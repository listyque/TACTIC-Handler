"""An unavailable local repository is a paused prerequisite, not a failed transfer."""
import io
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import QObject, Signal, QElapsedTimer
from PySide6.QtTest import QTest

from tests.qt_application import gui_test_application
from thlib.environment import env_mode
from thlib.ui.notifications import NotificationController
from thlib.ui.repository_sync import RepositorySyncController


class Response(io.BytesIO):
    headers = {"Content-Length": "3"}


class File:
    def __init__(self, root, name="preview.jpg"):
        self.root = Path(root)
        self.name = name

    def get_repo_path(self): return str(self.root)
    def get_full_abs_path(self): return str(self.root / "images" / self.name)
    def get_full_web_path(self): return "http://example.invalid/" + self.name
    def get_filename_with_ext(self): return self.name
    def get_file_size(self): return 3
    def get_md5(self): return ""
    def get_timestamp(self, obj=False): return ""
    def get_unique_id(self): return self.name
    def is_exists(self): return Path(self.get_full_abs_path()).is_file()
    def prepare_repo(self):
        path = Path(self.get_full_abs_path())
        path.parent.mkdir(parents=True, exist_ok=True)
        return str(path)


class Application(QObject):
    notification_changed = Signal(str)
    loading_changed = Signal()
    activity_log_changed = Signal()
    loading = False
    loading_message = ""
    activity_log = []

    def __init__(self, queue):
        super().__init__()
        self.repository_sync = queue


class RepositoryWaitingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def setUp(self):
        self.folder = TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.base = Path(self.folder.name)
        self.profile = patch.object(env_mode, "current_path", str(self.base / "profile"))
        self.profile.start()
        self.addCleanup(self.profile.stop)
        self.log = Mock()
        self.queue = RepositorySyncController(debug_log=self.log)
        self.addCleanup(self.queue.shutdown)
        self.application = Application(self.queue)
        self.notifications = NotificationController(self.application)
        self.failed = []
        self.complete = []
        self.queue.task_failed.connect(self.failed.append)
        self.queue.downloads_finished.connect(lambda: self.complete.append(True))

    def wait(self, condition):
        timer = QElapsedTimer()
        timer.start()
        while not condition() and timer.elapsed() < 2000:
            QTest.qWait(5)
        self.assertTrue(condition())

    def schedule(self, file, preview=True):
        return self.queue.schedule_file_object(file, auto_start=True, is_ui_preview=preview)

    def test_missing_repository_waits_without_download_errors_or_directory_creation(self):
        file = File(self.base / "missing")
        with patch("thlib.repository_download.UrllibTransport.open") as request:
            handle = self.schedule(file)
            self.wait(lambda: self.queue._active == 0)
            self.assertEqual(self.queue.status(handle.task_id), "waiting_repository")
            request.assert_not_called()
        self.assertFalse(file.root.exists())
        self.assertEqual(self.failed, [])
        self.assertEqual(self.notifications._history_records, [])
        self.assertFalse(any(call.args[0] == "ERROR" for call in self.log.log.call_args_list))

    def test_blank_and_relative_repository_roots_do_not_write_or_download(self):
        for root in ["", "relative/repo"]:
            with self.subTest(root=root), patch(
                "thlib.repository_download.UrllibTransport.open"
            ) as request:
                file = File(self.base / "missing", name=root.replace("/", "_") + "preview.jpg")
                file.get_repo_path = lambda: root
                handle = self.schedule(file)
                self.wait(lambda: self.queue._active == 0)
                self.assertEqual(self.queue.status(handle.task_id), "waiting_repository")
                request.assert_not_called()
                self.assertFalse(file.root.exists())
        self.assertEqual(self.notifications._history_records, [])

    def test_late_missing_root_result_does_not_pause_a_new_configuration(self):
        file = File(self.base / "missing")
        handle = self.schedule(file, preview=False)
        self.wait(lambda: self.queue._active == 0)
        previous_generation = self.queue._repository_generation
        self.queue._repository_generation += 1
        self.queue._unavailable_repositories.clear()
        old_root = str(file.root)
        file.root = self.base / "new"
        file.root.mkdir()
        with patch("thlib.repository_download.UrllibTransport.open", return_value=Response(b"img")):
            self.queue._repository_unavailable(handle.task_id, old_root, previous_generation)
            self.wait(handle.is_download_finished)
        self.assertNotIn(old_root, self.queue._unavailable_repositories)
        self.assertEqual(Path(file.get_full_abs_path()).read_bytes(), b"img")
        self.assertEqual(self.failed, [])

    def test_repeated_preview_requests_do_not_restart_workers_until_configuration_changes(self):
        file = File(self.base / "missing")
        handle = self.schedule(file)
        self.wait(lambda: self.queue._active == 0)
        with patch.object(self.queue.pool, "start") as start:
            for _ in range(10):
                self.assertIs(self.schedule(file), handle)
                other = self.schedule(File(file.root, "other.jpg"))
                self.assertEqual(self.queue.status(other.task_id), "waiting_repository")
            start.assert_not_called()
        self.assertEqual(self.notifications._history_records, [])

    def test_configuration_change_releases_old_previews_and_uses_new_repository(self):
        file = File(self.base / "missing")
        previous = self.schedule(file)
        self.wait(lambda: self.queue._active == 0)
        file.root = self.base / "new"
        file.root.mkdir()
        self.queue.reload_configuration()
        self.assertNotIn(previous.task_id, self.queue._tasks)
        with patch("thlib.repository_download.UrllibTransport.open", return_value=Response(b"img")) as request:
            current = self.schedule(file)
            self.wait(lambda: self.queue._active == 0)
            request.assert_called_once()
        self.assertEqual(Path(file.get_full_abs_path()).read_bytes(), b"img")
        self.assertEqual(self.failed, [])
        self.assertFalse((self.base / "missing").exists())

    def test_explicit_sync_waits_then_resumes_the_same_handle_with_new_paths(self):
        file = File(self.base / "missing")
        handle = self.schedule(file, preview=False)
        self.wait(lambda: self.queue._active == 0)
        self.assertEqual(self.queue.status(handle.task_id), "waiting_repository")
        self.assertEqual(self.complete, [])
        self.assertFalse(self.queue.is_all_downloads_done())
        self.assertEqual(self.notifications._history_records, [])
        file.root = self.base / "new"
        file.root.mkdir()
        with patch("thlib.repository_download.UrllibTransport.open", return_value=Response(b"img")):
            self.queue.reload_configuration()
            self.wait(handle.is_download_finished)
        self.assertEqual(self.queue.status(handle.task_id), "finished")
        self.assertEqual(self.queue.model.record(handle.task_id)["localPath"], file.get_full_abs_path())
        self.assertEqual(Path(file.get_full_abs_path()).read_bytes(), b"img")
        self.assertEqual(self.failed, [])
        self.assertEqual(len(self.complete), 1)

    def test_waiting_transfer_can_be_cancelled_without_resuming_on_configuration_change(self):
        file = File(self.base / "missing")
        handle = self.schedule(file, preview=False)
        self.wait(lambda: self.queue._active == 0)
        self.queue.cancel_task(handle.task_id)
        self.assertEqual(self.queue.status(handle.task_id), "cancelled")
        with patch.object(self.queue.pool, "start") as start:
            self.queue.reload_configuration()
            start.assert_not_called()

    def test_configuration_bridge_clears_waiting_previews_before_refresh(self):
        from thlib.ui.application_composition import ConfigurationBridge
        file = File(self.base / "missing")
        previous = self.schedule(file)
        self.wait(lambda: self.queue._active == 0)
        file.root = self.base / "new"
        file.root.mkdir()
        refreshed = []
        controller = SimpleNamespace(
            repository_sync=self.queue,
            refresh_checkin_defaults=lambda: refreshed.append(self.schedule(file)),
        )
        delivery = SimpleNamespace(checkin_out=Mock(), commit_queue=Mock(), drop_plate=Mock())
        bridge = ConfigurationBridge(SimpleNamespace(controller=controller), None, None, delivery)
        with patch("thlib.repository_download.UrllibTransport.open", return_value=Response(b"img")):
            bridge.reload_repository_configuration()
            self.wait(lambda: self.queue._active == 0)
        self.assertNotEqual(refreshed[0].task_id, previous.task_id)
        self.assertEqual(Path(file.get_full_abs_path()).read_bytes(), b"img")
        self.assertEqual(self.failed, [])

    def test_http_failure_with_an_available_repository_is_still_reported(self):
        file = File(self.base)
        with patch("thlib.repository_download.UrllibTransport.open", side_effect=OSError("network unavailable")), patch(
            "thlib.repository_download.time.sleep"
        ):
            handle = self.schedule(file)
            self.wait(lambda: self.queue._active == 0)
        self.assertEqual(self.failed, [handle.task_id])
        self.assertTrue(any(row["kind"] == "error" for row in self.notifications._history_records))
        self.assertTrue(any(call.args[0] == "ERROR" for call in self.log.log.call_args_list))


if __name__ == "__main__":
    unittest.main()

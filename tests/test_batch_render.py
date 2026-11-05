"""Run locally: python -m unittest discover -s side_tools/batch_scheduler -p test*.py."""

import json
import os
import sys
import tempfile
import threading
import time
import unittest
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import StringIO
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch
from urllib.error import HTTPError
from urllib.request import urlopen

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Material"
os.environ["QT_QUICK_BACKEND"] = "software"
if os.name == "nt":
    os.environ["QT_QPA_FONTDIR"] = str(Path(os.environ["WINDIR"]) / "Fonts")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import (
    Property,
    QObject,
    QPoint,
    QPointF,
    Qt,
    QUrl,
    qInstallMessageHandler,
)
from PySide6.QtGui import QFontDatabase, QGuiApplication, QWheelEvent
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression
from PySide6.QtQuick import (
    QQuickItem,  # noqa: F401 - registers Qt Quick pointer converters
)
from PySide6.QtTest import QSignalSpy, QTest

from plugins.batch_render import controller as batch
from plugins.batch_render import execution, settings, catalog_controller, web_control, preparation, render
from plugins.batch_render import domain as domain
from plugins.batch_render import window as batch_ui
from plugins.batch_render.web import BatchWebServer, WEB_HTML
from tactic_handler_api.operations import Executor
from thlib.environment import env_mode

ROOT = Path(__file__).resolve().parents[1]


def episode(identity="ep", shots=2):
    return {
        "id": identity,
        "episodeKey": identity,
        "title": identity,
        "test": True,
        "state": "waiting",
        "stage": "Waiting",
        "error": "",
        "elapsed": 0.0,
        "expanded": True,
        "prepared": False,
        "preparationErrors": [],
        "origin": "manual",
        "jobs": [
            {
                "id": f"{identity}-{i}",
                "shotKey": f"{identity}/shot{i}",
                "title": f"Shot {i}",
                "start": 1,
                "end": 5,
                "state": "waiting",
                "stage": "Waiting",
                "error": "",
                "progress": 0.0,
                "elapsed": 0.0,
                "renderElapsed": 0.0,
                "frame": "",
                "framesDone": 0,
                "attempt": 1,
                "scene": "",
                "logPath": "",
                "renderOutput": "",
                "renderFiles": [],
                "preparationErrors": [],
                "pid": "",
            }
            for i in range(shots)
        ],
    }


class Root(QObject):
    dark = Property(bool, lambda self: True, constant=True)
    applicationThemeStyleName = Property(str, lambda self: "default", constant=True)
    applicationThemeAccentColor = Property(str, lambda self: "#58b9e6", constant=True)
    applicationThemeBaseColor = Property(str, lambda self: "#202b32", constant=True)


class QueueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.name == "nt":
            import ctypes

            kernel32 = ctypes.windll.kernel32
            kernel32.SetErrorMode(kernel32.GetErrorMode() | 0x0001 | 0x0002 | 0x8000)
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        # Offscreen Windows does not discover system fonts automatically.
        if os.name == "nt":
            for name in ("segoeui.ttf", "segoeuib.ttf", "seguisb.ttf"):
                QFontDatabase.addApplicationFont(
                    str(Path(os.environ["WINDIR"]) / "Fonts" / name)
                )

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        old = env_mode.current_path
        env_mode.current_path = self.directory.name
        self.addCleanup(setattr, env_mode, "current_path", old)
        self.executor = Executor(4, 32)
        self.api = SimpleNamespace(submit=self.executor.submit)
        self.controller = batch.BatchDispatcherController(
            self.api, "test", offline=True, settings={}
        )
        self.addCleanup(self.finish)

    def finish(self):
        self.controller.shutdown()
        thread = threading.Thread(target=lambda: self.executor.close(wait=True))
        thread.start()
        thread.join(20)
        self.assertFalse(thread.is_alive(), "Worker did not stop")
        self.controller.deleteLater()
        self.app.processEvents()

    def until(self, predicate, seconds=4):
        deadline = time.monotonic() + seconds
        while not predicate() and time.monotonic() < deadline:
            self.app.processEvents()
            QTest.qWait(5)
        self.assertTrue(predicate(), self.controller.errorText)

    def visual(self, item, name):
        if item.objectName() == name:
            return item
        for child in item.childItems():
            found = self.visual(child, name)
            if found is not None:
                return found
        return None

    def test_two_episodes_run_once_and_remain_in_history(self):
        c = self.controller
        c._entries = [episode("one"), episode("two")]
        seen = []

        def render(job, _timeout, _cancel, _pause=None):
            seen.append(job["shotKey"])
            return {
                "exitCode": 0,
                "elapsed": 0.2,
                "cancelled": False,
                "timedOut": False,
            }

        with (
            patch.object(execution, "_prepare_episode", return_value={}),
            patch.object(
                execution, "_prepare_shot", return_value={"command": "test", "args": []}
            ),
            patch.object(execution, "_render_native", side_effect=render),
        ):
            c.startScheduler()
            self.until(lambda: all(row["state"] == "completed" for row in c._entries))
        self.assertEqual(seen, ["one/shot0", "one/shot1", "two/shot0", "two/shot1"])
        self.assertEqual(c.summary["completed"], 4)
        self.assertEqual(c.queue.rowCount(), 6)

    def test_web_server_is_embedded_and_token_protected(self):
        server = BatchWebServer(
            lambda request: {"type": request["type"]},
            host="127.0.0.1",
            require_token=True,
        )
        self.addCleanup(server.stop)
        url = server.start()
        self.assertIn("Диспетчер батч-рендера", WEB_HTML)
        with urlopen(url, timeout=2) as response:
            self.assertIn("Диспетчер батч-рендера", response.read().decode())
        with urlopen(url.split("/?", 1)[0], timeout=2) as response:
            self.assertIn("Нужна защищённая ссылка", response.read().decode())
        for name in ("solid", "regular", "material"):
            with urlopen(
                url.split("/?", 1)[0] + f"/assets/icons-{name}.ttf", timeout=2
            ) as response:
                self.assertEqual(response.read()[:4], b"\x00\x01\x00\x00")
        with self.assertRaises(HTTPError) as caught:
            urlopen(url.split("/?", 1)[0] + "/api/state", timeout=2)
        self.assertEqual(caught.exception.code, 403)
        caught.exception.close()

    def test_web_server_can_be_explicitly_open(self):
        server = BatchWebServer(
            lambda request: {"type": request["type"]}, host="127.0.0.1", require_token=False
        )
        self.addCleanup(server.stop)
        url = server.start()
        self.assertNotIn("token=", url)
        with urlopen(url + "api/state", timeout=2) as response:
            self.assertEqual(json.load(response), {"type": "state"})

    def test_web_server_proxies_remote_thumbnails(self):
        image = b"test-png"
        self.assertIn("if (url) url = `/api/thumb", WEB_HTML)

        class ImageHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(len(image)))
                self.end_headers()
                self.wfile.write(image)

            def log_message(self, _format, *_args):
                pass

        source = ThreadingHTTPServer(("127.0.0.1", 0), ImageHandler)
        source_thread = threading.Thread(target=source.serve_forever, daemon=True)
        source_thread.start()
        self.addCleanup(source.server_close)
        self.addCleanup(source.shutdown)

        preview_url = f"http://127.0.0.1:{source.server_port}/preview.png"
        server = BatchWebServer(lambda _request: preview_url, host="127.0.0.1", require_token=False)
        self.addCleanup(server.stop)
        with urlopen(server.start() + "api/thumb?identity=shot", timeout=2) as response:
            self.assertEqual(response.headers.get_content_type(), "image/png")
            self.assertEqual(response.read(), image)

    def test_web_requests_share_the_qt_queue_controller(self):
        entry = episode("web", 1)
        self.controller._entries = [entry]
        self.controller.setWebTheme(
            {"workspace": "#123456", "iconSet": "fontawesome-outline"}
        )
        result = []
        worker = threading.Thread(
            target=lambda: result.append(
                self.controller._web_dispatch(
                    {"type": "state", "selected": entry["jobs"][0]["id"]}
                )
            )
        )
        worker.start()
        self.until(lambda: not worker.is_alive())
        worker.join()
        self.assertEqual(result[0]["queue"][0]["episode"]["title"], "web")
        self.assertEqual(result[0]["selected"]["title"], "Shot 0")
        self.assertEqual(result[0]["theme"]["workspace"], "#123456")
        self.assertEqual(result[0]["theme"]["iconSet"], "fontawesome-outline")
        self.assertEqual(result[0]["settings"]["webPort"], 92)
        self.assertTrue(result[0]["settings"]["webSecurity"])
        self.assertTrue(result[0]["settings"]["webEnabled"])
        self.assertEqual(result[0]["settings"]["logCheckin"], "always")
        self.assertEqual(result[0]["queue"][0]["shots"][0]["frameSpec"], "1-5")
        self.assertIn('name="webPort"', WEB_HTML)
        self.assertIn('name="logCheckin"', WEB_HTML)
        self.assertIn('name="skipDependencyErrors"', WEB_HTML)
        self.assertIn('id="frames-dialog"', WEB_HTML)
        self.assertNotIn("prompt('Кадры", WEB_HTML)
        self.controller._web_action(
            {"action": "hold", "id": entry["jobs"][0]["id"]}
        )
        self.assertEqual(entry["jobs"][0]["state"], "held")

    def test_run_only_episode_ignores_queue_order_then_pauses(self):
        c = self.controller
        c._entries = [episode("first"), episode("chosen", 3), episode("last")]
        chosen = c._entries[1]
        chosen["state"] = "held"
        chosen["jobs"][0]["state"] = "held"
        chosen["jobs"][2]["state"] = "skipped"
        with (
            patch.object(execution, "_prepare_episode", return_value={}),
            patch.object(execution, "_prepare_shot", return_value={"command": "test"}),
            patch.object(
                execution,
                "_render_native",
                return_value={
                    "exitCode": 0,
                    "elapsed": 0.2,
                    "cancelled": False,
                    "timedOut": False,
                },
            ) as render,
        ):
            c.runOnly("chosen")
            self.until(lambda: chosen["state"] == "completed" and c.paused)
        self.assertEqual(
            [call.args[0]["shotKey"] for call in render.call_args_list],
            ["chosen/shot0", "chosen/shot1"],
        )
        self.assertEqual(c._entries[0]["state"], "waiting")
        self.assertEqual(c._entries[2]["state"], "waiting")

    def test_run_only_failed_shot_retries_and_saves_without_starting_siblings(self):
        c = self.controller
        c._entries = [episode("first"), episode("chosen", 3)]
        chosen = c._entries[1]
        chosen["test"] = False
        job = chosen["jobs"][1]
        job.update(state="failed", error="previous failure", logPath="previous.log")
        old_id = job["id"]
        with (
            patch.object(execution, "_prepare_episode", return_value={}) as prepare,
            patch.object(execution, "_prepare_shot", return_value={"command": "test"}),
            patch.object(
                execution,
                "_render_native",
                return_value={
                    "exitCode": 0,
                    "elapsed": 0.2,
                    "cancelled": False,
                    "timedOut": False,
                },
            ) as render,
            patch.object(execution, "_finalize_shot") as save,
            patch.object(execution, "_set_episode_task_status") as episode_status,
        ):
            c.runOnly(old_id)
            self.until(lambda: job["state"] == "completed" and c.paused)
        render.assert_called_once()
        save.assert_called_once()
        episode_status.assert_not_called()
        self.assertTrue(prepare.call_args.args[1]["singleShot"])
        self.assertNotEqual(job["id"], old_id)
        self.assertEqual(job["attempt"], 2)
        self.assertEqual(
            [row["state"] for row in chosen["jobs"]],
            ["waiting", "completed", "waiting"],
        )
        self.assertEqual(c._entries[0]["state"], "waiting")

    def test_run_only_preparation_failure_does_not_fail_other_shots(self):
        c = self.controller
        entry = episode()
        c._entries = [entry]
        with (
            patch.object(
                execution, "_prepare_episode", side_effect=OSError("cache unavailable")
            ),
            patch.object(execution, "_render_native") as render,
        ):
            c.runOnly("ep-1")
            self.until(lambda: entry["jobs"][1]["state"] == "failed" and c.paused)
        render.assert_not_called()
        self.assertEqual(entry["jobs"][0]["state"], "waiting")

    def test_run_only_rejects_busy_completed_and_unconfirmed_saves(self):
        c = self.controller
        c._entries = [episode()]
        job = c._entries[0]["jobs"][0]
        for blocked in ("busy", "completed", "saveFailed"):
            with self.subTest(blocked=blocked), patch.object(c, "_pump") as pump:
                job.update(
                    state="completed" if blocked == "completed" else "waiting",
                    saveFailed=blocked == "saveFailed",
                )
                c._stage_operation = object() if blocked == "busy" else None
                c.runOnly(job["id"])
                pump.assert_not_called()
                self.assertTrue(c.paused)
        c._stage_operation = None

    def test_pause_current_shot_then_resume_without_rerendering(self):
        c = self.controller
        c._entries = [episode()]
        entered, release = threading.Event(), threading.Event()
        seen = []

        def render(job, _timeout, _cancel, _pause=None):
            seen.append(job["id"])
            entered.set()
            if not release.wait(3):
                raise TimeoutError("test gate")
            return {
                "exitCode": 0,
                "elapsed": 0.2,
                "cancelled": False,
                "timedOut": False,
            }

        with (
            patch.object(execution, "_prepare_episode", return_value={}),
            patch.object(
                execution, "_prepare_shot", return_value={"command": "test", "args": []}
            ),
            patch.object(execution, "_render_native", side_effect=render),
        ):
            c.startScheduler()
            self.until(entered.is_set)
            c.stopScheduler()
            release.set()
            self.until(lambda: not c.running)
            self.assertEqual(len(seen), 1)
            self.assertEqual(c._entries[0]["jobs"][1]["state"], "waiting")
            c.startScheduler()
            self.until(lambda: c._entries[0]["state"] == "completed")
        self.assertEqual(len(seen), 2)

    def test_active_shot_pause_and_resume_reuses_hold_action(self):
        c = self.controller
        entry = episode()
        job = entry["jobs"][0]
        entry["state"] = job["state"] = "rendering"
        c._entries = [entry]
        c._active_entry, c._active_job = entry, job

        self.assertIn("hold", c._allowed_actions(entry))
        self.assertIn("hold", c._allowed_actions(entry, job))
        c.holdQueue(job["id"])
        self.assertTrue(c._render_pause.is_set())
        self.assertEqual((entry["state"], job["state"]), ("paused", "paused"))
        c.holdQueue(entry["id"])
        self.assertFalse(c._render_pause.is_set())
        self.assertEqual(
            (entry["state"], job["state"]), ("rendering", "rendering")
        )

    def test_pause_signal_is_a_temporary_file_for_maya(self):
        pause = threading.Event()
        path = Path(self.directory.name) / "paused"
        domain._sync_pause_file(pause, path)
        self.assertFalse(path.exists())
        pause.set()
        domain._sync_pause_file(pause, path)
        self.assertTrue(path.exists())
        pause.clear()
        domain._sync_pause_file(pause, path)
        self.assertFalse(path.exists())

    def test_stop_queue_cancels_active_episode_without_starting_next(self):
        c = self.controller
        first, second = episode("first", 1), episode("second", 1)
        c._entries = [first, second]
        entered = threading.Event()

        def prepare(_api, _entry, _config, cancel):
            entered.set()
            if not cancel.wait(3):
                raise TimeoutError("test cancellation")
            domain._check_cancel(cancel)

        with (
            patch.object(execution, "_prepare_episode", side_effect=prepare),
            patch.object(execution, "_render_native") as render,
        ):
            c.startScheduler()
            self.until(entered.is_set)
            c.interruptRender()
            self.until(lambda: first["state"] == "cancelled" and not c.running)

        self.assertTrue(c.paused)
        self.assertEqual(second["state"], "waiting")
        self.assertIsNone(c._active_entry)
        render.assert_not_called()

    def test_cancel_preparation_does_not_launch_renderer(self):
        c = self.controller
        c._entries = [episode()]
        entered = threading.Event()

        def prepare(_api, _entry, _config, cancel):
            entered.set()
            if not cancel.wait(3):
                raise TimeoutError("test cancellation")
            domain._check_cancel(cancel)

        with (
            patch.object(execution, "_prepare_episode", side_effect=prepare),
            patch.object(execution, "_render_native") as render,
        ):
            c.startScheduler()
            self.until(entered.is_set)
            c.cancelQueue("ep")
            self.until(lambda: c._entries[0]["state"] == "cancelled")
            render.assert_not_called()

    def test_removing_active_episode_cancels_then_removes_it(self):
        c = self.controller
        entry = episode()
        entry["result"] = "cancelled"
        c._entries = [entry]
        c._active_entry = entry
        c._stage_operation = object()

        self.assertTrue(c.removeEpisode(entry["id"]))
        self.assertTrue(c._cancel.is_set())
        self.assertEqual(c._pending_removal, entry["id"])

        c._entry_saved(None)

        self.assertEqual(c._entries, [])
        self.assertEqual(c._pending_removal, "")

    def test_cancel_only_active_shot_continues_siblings(self):
        c = self.controller
        c._entries = [episode()]
        entered = threading.Event()

        def render(job, _timeout, cancel, _pause=None):
            if job["id"] == "ep-0":
                entered.set()
                if not cancel.wait(3):
                    raise TimeoutError("test cancellation")
            return {
                "exitCode": 0,
                "elapsed": 0.2,
                "cancelled": cancel.is_set(),
                "timedOut": False,
            }

        with (
            patch.object(execution, "_prepare_episode", return_value={}),
            patch.object(
                execution, "_prepare_shot", return_value={"command": "test", "args": []}
            ),
            patch.object(execution, "_render_native", side_effect=render),
        ):
            c.startScheduler()
            self.until(entered.is_set)
            c.cancelQueue("ep-0")
            self.until(lambda: c._entries[0]["state"] in batch._TERMINAL)
        self.assertEqual(
            [j["state"] for j in c._entries[0]["jobs"]], ["cancelled", "completed"]
        )

    def test_exit_one_is_failure_not_user_cancellation(self):
        c = self.controller
        c._entries = [episode(shots=1)]
        with (
            patch.object(execution, "_prepare_episode", return_value={}),
            patch.object(execution, "_prepare_shot", return_value={"command": "test"}),
            patch.object(
                execution,
                "_render_native",
                return_value={
                    "exitCode": 1,
                    "elapsed": 0.2,
                    "cancelled": False,
                    "timedOut": False,
                },
            ),
        ):
            c.startScheduler()
            self.until(lambda: c._entries[0]["state"] == "failed")
        self.assertEqual(c._entries[0]["jobs"][0]["exitCode"], 1)

    def test_held_shot_is_not_reported_completed(self):
        c = self.controller
        c._entries = [episode(shots=1)]
        c._entries[0]["jobs"][0]["state"] = "held"
        c.startScheduler()
        self.assertEqual(c._entries[0]["state"], "held")
        self.assertEqual(c.summary["completed"], 0)
        self.assertEqual(c.statusText, "Waiting · held jobs remain")

    def test_failed_shot_retry_preserves_success_and_hold_blocks_resume(self):
        c = self.controller
        entry = episode()
        entry.update(state="failed", prepared=True)
        entry["jobs"][0].update(state="completed", renderElapsed=2.0)
        entry["jobs"][1].update(state="failed", error="Renderer failed")
        c._entries = [entry]
        c.retryQueue("ep")
        self.assertEqual(entry["jobs"][0]["attempt"], 1)
        self.assertEqual(entry["jobs"][1]["attempt"], 2)
        c._active_entry = entry
        c.holdQueue("ep")
        c.startScheduler()
        self.assertIsNone(c._active_entry)
        self.assertEqual(entry["state"], "held")
        seen = []
        with (
            patch.object(execution, "_prepare_episode", return_value={}),
            patch.object(execution, "_prepare_shot", return_value={"command": "test"}),
            patch.object(
                execution,
                "_render_native",
                side_effect=lambda job, *_: (
                    seen.append(job["shotKey"])
                    or {
                        "exitCode": 0,
                        "elapsed": 1.0,
                        "cancelled": False,
                        "timedOut": False,
                    }
                ),
            ),
        ):
            c.holdQueue("ep")
            self.until(lambda: entry["state"] == "completed")
        self.assertEqual(seen, ["ep/shot1"])

    def test_preparation_failure_saves_episode_failure_without_launching(self):
        c = self.controller
        c._config["log_checkin"] = "never"
        entry = episode(shots=1)
        entry["test"] = False
        c._entries = [entry]
        self.api.sobject = Mock(return_value="episode object")
        with (
            patch.object(
                execution, "_prepare_episode", side_effect=OSError("Cache cannot be read")
            ),
            patch.object(execution, "_render_native") as render,
            patch.object(execution, "_set_episode_task_status") as save,
        ):
            c.startScheduler()
            self.until(lambda: entry["state"] == "failed")
            render.assert_not_called()
            save.assert_called_once_with(
                "episode object", "render", c._config["failed_status"]
            )
        self.assertIn("Cache cannot be read", entry["error"])

    def test_unconfirmed_server_save_pauses_and_is_not_retried(self):
        c = self.controller
        entry = episode()
        entry["test"] = False
        c._entries = [entry]
        with (
            patch.object(execution, "_prepare_episode", return_value={}),
            patch.object(execution, "_prepare_shot", return_value={"command": "test"}),
            patch.object(
                execution,
                "_render_native",
                return_value={
                    "exitCode": 0,
                    "elapsed": 1.0,
                    "cancelled": False,
                    "timedOut": False,
                },
            ) as render,
            patch.object(
                execution,
                "_finalize_shot",
                side_effect=OSError("Connection lost while saving"),
            ),
        ):
            c.startScheduler()
            self.until(lambda: entry["jobs"][0].get("saveFailed"))
            self.assertTrue(c.paused)
            self.assertEqual(entry["jobs"][0]["state"], "failed")
            self.assertEqual(entry["jobs"][1]["state"], "waiting")
            c.retryQueue(entry["jobs"][0]["id"])
            self.assertIn("not confirmed", c.errorText)
            self.assertEqual(render.call_count, 1)

    def test_discovery_errors_are_visible_and_polls_do_not_duplicate(self):
        c = self.controller
        c.episodes.replace([{"searchKey": "ep", "title": "Episode"}])
        bad = [{"searchKey": "shot", "title": "Shot", "start": 20, "end": 1}]
        with patch.object(catalog_controller, "_discover_queue", return_value=bad):
            c.renderEpisode(0, False)
            c.renderEpisode(0, False)
            self.until(lambda: c._entries[0]["state"] == "failed")
        self.assertEqual(len(c._entries), 1)
        self.assertIn("Invalid frame range", c.errorText)
        c._watch_server = True
        row = {"searchKey": "ep", "title": "Episode", "code": "EP", "subtitle": "", "renderStatus": "Подготовлен"}

        def payload(queued):
            return {
                "episodes": [dict(row)],
                "queuedEpisodes": [dict(row)] if queued else [],
                "filters": [],
            }

        with patch.object(c, "_enqueue") as enqueue:
            c._episodes_ready(c._generation, payload(True))
            c._episodes_ready(c._generation, payload(True))
            enqueue.assert_not_called()
            with patch.object(c, "_persist") as persist:
                c._episodes_ready(c._generation, payload(False))
                persist.assert_called_once()
            server_row = payload(True)["queuedEpisodes"][0]
            c._episodes_ready(
                c._generation,
                {
                    "episodes": [dict(row)],
                    "queuedEpisodes": [server_row],
                    "filters": [],
                },
            )
            enqueue.assert_called_once_with(
                "ep", False, origin="server", episode=server_row
            )

    def test_queue_model_progress_updates_do_not_reset_or_reinsert_rows(self):
        import statistics

        c = self.controller
        c._entries = [episode(str(i), 10) for i in range(100)]
        c._publish_queue()
        reset, inserted, removed = [], [], []
        c.queue.modelReset.connect(lambda: reset.append(True))
        c.queue.rowsInserted.connect(lambda *_: inserted.append(True))
        c.queue.rowsRemoved.connect(lambda *_: removed.append(True))
        samples = []
        for index in range(5):
            c._entries[0]["jobs"][0]["progress"] = index / 10
            started = time.perf_counter()
            c._publish_queue()
            samples.append((time.perf_counter() - started) * 1000)
        self.assertEqual(c.queue.rowCount(), 1100)
        self.assertEqual((reset, inserted, removed), ([], [], []))
        if os.environ.get("BATCH_PROFILE"):
            print(
                f"1000 shots: median model update {statistics.median(samples):.1f} ms"
            )

    def test_saved_queue_roundtrip_never_restarts_interrupted_renderer(self):
        import hashlib

        from thlib.ui.server_address import normalize_tactic_server_url

        c = self.controller
        endpoint = normalize_tactic_server_url("https://tactic.invalid")
        c._scope = hashlib.sha256(endpoint.encode()).hexdigest()[:16] + "/test"
        entry = episode()
        entry["jobs"][0].update(state="completed")
        entry["jobs"][1].update(state="rendering", pid=12345)
        entry["state"] = "rendering"
        c._entries, c._offline = [entry], False
        c._persist()
        self.until(lambda: not c._saving)
        c._ready = False
        c._entries = []
        with (
            patch("thlib.environment.env_server.get_server", return_value=endpoint),
            patch.object(c, "refresh"),
            patch.object(execution, "_render_native") as render,
        ):
            c.initialize()
            self.until(lambda: c.ready)
            restored = c._entries[0]
            self.assertEqual(restored["state"], "held")
            self.assertEqual(
                [j["state"] for j in restored["jobs"]], ["completed", "failed"]
            )
            self.assertEqual(restored["jobs"][1]["pid"], "")
            self.assertTrue(c.paused)
            c.startScheduler()
            self.until(lambda: restored["state"] == "failed")
            render.assert_not_called()
        self.until(lambda: not c._saving)

    def test_cache_extraction_direct_and_child_alembic_and_unsafe_archive(self):
        import zipfile

        root = Path(self.directory.name)
        archive = root / "cache.zip"
        with zipfile.ZipFile(archive, "w") as zipped:
            zipped.writestr("characters/cache.abc", b"cache")
        file = Mock()
        file.get_ext.return_value = "zip"
        file.get_repo_path.return_value = str(root)
        direct, parent, child = Mock(), Mock(), Mock()
        direct.get_value.return_value = "cache/abc"
        direct.get_search_key.return_value = "direct"
        direct.related.return_value = []
        parent.get_value.return_value = "character"
        parent.related.return_value = [child, direct]
        child.get_search_key.return_value = "child"
        ep = Mock()
        ep.related.return_value = [direct, parent]
        api = Mock()
        api.sobject.return_value = ep
        api.files.ensure_local.return_value = archive
        config = batch.BATCH_DISPATCHER_CONFIG["project_config"]
        with (
            patch.object(preparation, "_repository_preset", return_value={}),
            patch.object(preparation, "_main_file", return_value=file),
        ):
            domain._prepare_episode(api, episode(), config, threading.Event())
        self.assertEqual(api.files.ensure_local.call_count, 2)
        self.assertEqual(
            (root / "cache/alembic/characters/cache.abc").read_bytes(), b"cache"
        )
        parent.related.assert_called_once_with(
            search_type="dolly3d/assets",
            filters=[("assets_category_code", "cache/abc")],
        )
        with zipfile.ZipFile(archive, "w") as zipped:
            zipped.writestr("../outside.txt", "invalid")
        with self.assertRaisesRegex(ValueError, "Unsafe cache"):
            domain._safe_extract(archive, root / "extracted")
        self.assertFalse((root / "outside.txt").exists())

    def test_frame_zero_and_fractional_values(self):
        self.assertEqual(domain._frame_number(0, 1, "shot"), 0)
        self.assertEqual(domain._frame_number(None, 1, "shot"), 1)
        for value in ("invalid", 1.5, float("nan"), float("inf")):
            with self.assertRaisesRegex(ValueError, "Invalid frame"):
                domain._frame_number(value, 1, "shot")

    def test_custom_frame_spec_is_preserved_and_counted(self):
        expected = [(1, 20), (50, 50), (66, 66), (68, 68), (70, 150)]
        self.assertEqual(
            domain._parse_frame_spec("1-20, 50,66,68, 70-150", 1, 150), expected
        )
        self.assertEqual(domain._parse_frame_spec("8-10, 1-4, 4-8", 1, 10), [(1, 10)])
        for value in ("", "1,,2", "20-10", "0-20", "1-151"):
            with self.assertRaises(ValueError):
                domain._parse_frame_spec(value, 1, 150)
        entry = episode(shots=1)
        entry["test"] = False
        job = entry["jobs"][0]
        job["end"] = 150
        self.controller._entries = [entry]
        self.assertTrue(
            self.controller.setFrameSpec(job["id"], "1-20, 50,66,68, 70-150")
        )
        self.assertEqual(job["frameRanges"], [list(pair) for pair in expected])
        self.assertEqual(job["frameSpec"], "1-20, 50,66,68, 70-150")
        self.assertEqual(self.controller.queue.get(1)["frames"], "0/104")
        self.assertEqual(
            self.controller.queue.get(1)["subtitle"],
            "Кадры: 1-20, 50,66,68, 70-150 · попытка 1",
        )

    def test_window_state_is_saved_without_losing_normal_geometry(self):
        self.controller._offline = False
        normal = {
            "x": 40,
            "y": 30,
            "width": 1200,
            "height": 700,
            "maximized": False,
            "episodeWidth": 320,
            "detailHeight": 210,
            "logPanelVisible": False,
            "detailPage": "details",
            "episodeStatuses": ["Проверен"],
        }
        with (
            patch("thlib.environment.env_write_config", return_value=True) as write,
            patch.object(settings, "current_screens", return_value=([], "")),
            patch.object(settings, "screen_for_window_rect", return_value=None),
        ):
            self.controller.saveWindowState(normal)
            self.until(lambda: not self.controller._operations)
            self.controller.saveWindowState({
                **normal,
                "x": 0,
                "y": 0,
                "width": 1920,
                "height": 1080,
                "maximized": True,
                "episodeStatuses": ["Готов"],
            })
            self.until(lambda: not self.controller._operations)

        saved = write.call_args_list[-1].args[0]
        self.assertEqual((saved["x"], saved["y"]), (40, 30))
        self.assertEqual((saved["width"], saved["height"]), (1200, 700))
        self.assertTrue(saved["maximized"])
        self.assertEqual(saved["episodeWidth"], 320)
        self.assertEqual(saved["detailHeight"], 210)
        self.assertFalse(saved["logPanelVisible"])
        self.assertEqual(saved["episodeStatuses"], ["Готов"])
        self.assertEqual(write.call_args_list[-1].kwargs, {
            "filename": "ui_batch_dispatcher_window",
            "unique_id": "test",
            "long_abs_path": True,
        })
        with (
            patch.object(self.controller, "refresh"),
            patch.object(settings, "current_screens", return_value=([], "")),
        ):
            self.controller._state_loaded(({}, normal, {}, "scope"))
        self.assertEqual(
            (self.controller.windowState["width"], self.controller.windowState["height"]),
            (1200, 700),
        )
        self.assertEqual(self.controller.windowState["episodeWidth"], 320)
        self.assertEqual(self.controller.windowState["detailHeight"], 210)
        self.assertFalse(self.controller.windowState["logPanelVisible"])
        self.assertEqual(self.controller.visibleEpisodeStatuses, ["Проверен"])

    def test_remove_episode_only_removes_its_local_queue_history(self):
        c = self.controller
        first, second = episode("first"), episode("second")
        c._entries = [first, second]
        c._server_seen.add(first["episodeKey"])
        c._events = [
            (first["id"], first["jobs"][0]["id"], "first log"),
            (second["id"], second["jobs"][0]["id"], "second log"),
        ]
        c.selectQueue(first["jobs"][0]["id"])
        with patch.object(c, "_persist") as persist:
            self.assertFalse(c.removeEpisode(first["jobs"][0]["id"]))
            self.assertTrue(c.removeEpisode(first["id"]))
            persist.assert_called_once()
        self.assertEqual(c._entries, [second])
        self.assertEqual(c.selectedDetail, {})
        self.assertEqual(c.queue.rowCount(), 3)
        self.assertEqual(
            c._events, [(second["id"], second["jobs"][0]["id"], "second log")]
        )
        self.assertIn(first["episodeKey"], c._server_seen)

    def test_catalog_selection_works_without_a_queue_entry(self):
        c = self.controller
        c.episodes.replace([
            {"searchKey": "episode-a", "selected": False},
            {"searchKey": "episode-b", "selected": False},
        ])

        c.selectEpisode(1)

        self.assertFalse(c.episodes.get(0)["selected"])
        self.assertTrue(c.episodes.get(1)["selected"])
        self.assertEqual(c._selected_episode, "episode-b")
        self.assertEqual(c.selectedDetail, {})

    def test_new_queue_entry_stays_collapsed(self):
        c = self.controller
        c.episodes.replace([{
            "searchKey": "episode-a",
            "title": "Episode A",
            "selected": False,
        }])

        with patch.object(c, "_discover_entry"):
            c.renderEpisode(0)

        self.assertEqual(len(c._entries), 1)
        self.assertFalse(c._entries[0]["expanded"])
        self.assertEqual(c.episodes.rowCount(), 0)
        c._remove_entries(c._entries[:])
        self.assertEqual(c.episodes.rowCount(), 1)
        self.assertEqual(c.episodes.get(0)["searchKey"], "episode-a")

    def test_queue_rows_move_by_target_and_while_a_sibling_renders(self):
        c = self.controller
        first, second, third = (
            episode("first", 3),
            episode("second"),
            episode("third"),
        )
        c._entries = [first, second, third]

        c.moveQueueTo(first["id"], third["jobs"][0]["id"])
        self.assertEqual(
            [entry["id"] for entry in c._entries],
            ["second", "third", "first"],
        )
        c.moveQueue(first["id"], -1000)
        self.assertEqual(c._entries[0], first)

        first.update(state="rendering")
        first["jobs"][0].update(state="rendering")
        c._active_entry = first
        c._active_job = first["jobs"][0]
        c.moveQueueTo(first["jobs"][2]["id"], first["jobs"][1]["id"])
        self.assertEqual(
            [job["id"] for job in first["jobs"]],
            ["first-0", "first-2", "first-1"],
        )

    def test_auto_clear_is_off_by_default_and_removes_finished_entries(self):
        c = self.controller
        completed = episode("completed")
        completed.update(state="completed")
        cancelled = episode("cancelled")
        cancelled.update(state="cancelled")
        failed = episode("failed")
        failed.update(state="failed")
        c._entries = [completed, cancelled, failed]

        self.assertFalse(c.autoClearFinished)
        c.setAutoClearFinished(True)

        self.assertTrue(c.autoClearFinished)
        self.assertEqual(c._entries, [failed])

        fresh = episode("fresh")
        fresh["result"] = "completed"
        c._entries.append(fresh)
        c._active_entry = fresh
        c._entry_saved(None)
        self.assertEqual(c._entries, [failed])

    def test_verified_episode_filter_is_off_until_enabled(self):
        c = self.controller
        c.episodes.replace(
            [
                {
                    "searchKey": "ready",
                    "renderStatus": "Подготовлен",
                    "statusChoices": [],
                },
                {
                    "searchKey": "verified",
                    "renderStatus": "Проверен",
                    "statusChoices": [],
                },
            ]
        )
        filters = {row["value"]: row for row in c.episode_filters.records()}

        self.assertTrue(filters["Подготовлен"]["active"])
        self.assertFalse(filters["Проверен"]["active"])
        self.assertNotIn("Проверен", c.visibleEpisodeStatuses)

        with patch.object(c, "refresh") as refresh:
            c.toggleEpisodeStatusFilter("Проверен")

        self.assertIn("Проверен", c.visibleEpisodeStatuses)
        refresh.assert_not_called()

    def test_episode_query_keeps_taskless_unknown_and_latest_blank_status(self):
        api = Mock()
        project = api.project.return_value
        episodes, tasks = Mock(), Mock()
        project.stype.side_effect = lambda code: tasks if code == 'sthpw/task' else episodes
        def task(code, status):
            value = Mock()
            value.get_value.side_effect = {'search_code':code, 'status':status}.get
            return value
        tasks.query.return_value.items = [task('EP1', 'Подготовлен'), task('EP1', ''),
                                          task('EP2', 'Custom'), task('ORPHAN', 'Проверен')]
        rows = []
        for code in ('EP1', 'EP2', 'EP3'):
            row = Mock()
            row.get_code.return_value = code
            row.get_search_key.return_value = code
            row.get_value.side_effect = {'name':code}.get
            row.snapshots.return_value = []
            rows.append(row)
        episodes.query.return_value.items = rows
        result = domain._query_episodes(api, 'test', self.controller._config)
        self.assertEqual([row['renderStatus'] for row in result['episodes']], ['', 'Custom', ''])
        counts = {row['value']: row['count'] for row in result['filters']}
        self.assertEqual(counts[''],2)
        self.assertEqual(counts['Custom'],1)
        self.assertEqual(counts['Проверен'],0)
        self.assertFalse(any(item[0] == 'status' for item in tasks.query.call_args.kwargs['filters']))
        episodes.query.assert_called_once_with(order_by=['name'], include_snapshots=True, limit=1000)
        for row in rows:
            row.tasks.assert_not_called()
            row.snapshots.assert_called_once_with(prefetched=True)

    def test_query_follows_pages(self):
        stype = Mock()
        second = SimpleNamespace(items=['last'],has_more=False)
        first = SimpleNamespace(items=list(range(1000)),has_more=True,next=lambda:second)
        stype.query.return_value = first
        self.assertEqual(len(list(domain._query_all(stype))),1001)

    def test_refresh_requested_during_load_is_coalesced(self):
        c=self.controller
        c._offline=False
        c._busy=True
        c.refresh()
        c.refresh()
        self.assertTrue(c._refresh_pending)
        with patch.object(c,'refresh') as refresh:
            c._busy=False
            c._finish_refresh()
            refresh.assert_called_once_with()
        self.assertFalse(c._refresh_pending)

    def test_filters_apply_latest_clicks_while_refresh_is_in_flight(self):
        c = self.controller
        records = [dict(title=code, searchKey=code, code=code, subtitle='', renderStatus=status)
                   for code,status in [('EP1','Подготовлен'),('EP2','Custom'),('EP3','')]]
        c._busy = True
        c._replace_episode_filters([dict(value=status,title=status,count=1,statusAccent='')
                                   for status in ('Подготовлен','Custom','')])
        c._catalog = records
        with patch.object(c,'refresh') as refresh:
            c.toggleEpisodeStatusFilter('Custom')
            c._episodes_ready(c._generation,dict(episodes=records,queuedEpisodes=[],filters=c.episode_filters.records()))
            self.assertEqual([row['code'] for row in c.episodes.records()],['EP1','EP3'])
            c.setEpisodeSearch('ep3')
            self.assertEqual([row['code'] for row in c.episodes.records()],['EP3'])
            c.toggleEpisodeStatusFilter('')
            self.assertEqual(c.episodes.rowCount(),0)
            refresh.assert_not_called()

    def test_disconnected_frame_ranges_use_one_process_and_structured_events(self):
        job = episode(shots=1)["jobs"][0]
        events = [
            'TH_BATCH_EVENT {"type":"started"}',
            'TH_BATCH_EVENT {"type":"frame","frame":1}',
            'TH_BATCH_EVENT {"type":"range_completed","start":1,"end":2}',
            'TH_BATCH_EVENT {"type":"frame","frame":5}',
            'TH_BATCH_EVENT {"type":"completed"}',
        ]
        script = "; ".join(f"print({event!r}, flush=True)" for event in events)
        script += "; import time; time.sleep(30)"
        job.update(
            frameSpec="1-2, 5",
            frameRanges=[[1, 2], [5, 5]],
            logPath=str(Path(self.directory.name) / "ranges.log"),
            args=[sys.executable, "-u", "-c", script],
        )
        progress = []
        with patch.object(render, "report_progress", side_effect=progress.append):
            result = domain._render_native(job, 0, threading.Event())
        self.assertEqual(
            result["exitCode"], 0, Path(job["logPath"]).read_text()
        )
        self.assertTrue(any(value.get("framesDone") == 3 for value in progress))
        log = Path(job["logPath"]).read_text()
        self.assertEqual(log.count("Command:"), 1)
        self.assertIn(events[-1], log)

    def test_maya_runner_opens_scene_once_and_preserves_post_frame_hook(self):
        cmds, mel = Mock(), Mock()
        cmds.getAttr.side_effect = lambda name: (
            "existingPostFrame()"
            if name == "defaultRenderGlobals.postRenderMel"
            else "mayaSoftware"
            if name == "defaultRenderGlobals.currentRenderer"
            else 4
        )
        maya = ModuleType("maya")
        maya.cmds, maya.mel = cmds, mel
        source = domain._maya_runner_source(
            "scene.ma", "output", "renderCam", [(1, 2), (5, 5)]
        )
        with patch.dict(sys.modules, {"maya": maya}), redirect_stdout(StringIO()):
            exec(source, {})

        cmds.file.assert_called_once_with(
            "scene.ma", open=True, force=True, prompt=False
        )
        renders = [
            call
            for call in mel.eval.call_args_list
            if "mayaBatchRenderProcedure" in call.args[0]
        ]
        self.assertEqual(len(renders), 2)
        post_hook = next(
            call.args[1]
            for call in cmds.setAttr.call_args_list
            if call.args[0] == "defaultRenderGlobals.postRenderMel"
        )
        self.assertTrue(post_hook.startswith("existingPostFrame();"))
        self.assertIn("TH_BATCH_EVENT", post_hook)
        self.assertIn("os.path.exists", post_hook)
        self.assertIn("cmds.renderSettings", post_hook)
        callback = json.loads(post_hook.split("python(", 1)[1][:-1])
        compile(callback, "postRenderMel", "exec")
        frame = Path(self.directory.name) / "frame.0001.png"
        frame.write_bytes(b"frame")
        cmds.currentTime.return_value = 1
        cmds.renderSettings.return_value = [str(frame)]
        output = StringIO()
        with patch.dict(sys.modules, {"maya": maya}), redirect_stdout(output):
            exec(callback, {})
        event = json.loads(output.getvalue().split("TH_BATCH_EVENT ", 1)[1])
        self.assertEqual(event["files"], [str(frame)])
        cmds.renderSettings.assert_called_with(
            genericFrameImageName="0001", fullPath=True
        )

    def test_maya_runner_uses_redshift_post_frame_hook(self):
        cmds, mel = Mock(), Mock()
        cmds.getAttr.side_effect = lambda name: (
            "redshift"
            if name == "defaultRenderGlobals.currentRenderer"
            else "existingRedshiftHook()"
            if name == "redshiftOptions.postRenderFrameMel"
            else 4
        )
        maya = ModuleType("maya")
        maya.cmds, maya.mel = cmds, mel
        source = domain._maya_runner_source("scene.ma", "output", "", [(1, 1)])

        with patch.dict(sys.modules, {"maya": maya}), redirect_stdout(StringIO()):
            exec(source, {})

        post_hook = next(
            call.args[1]
            for call in cmds.setAttr.call_args_list
            if call.args[0] == "redshiftOptions.postRenderFrameMel"
        )
        self.assertTrue(post_hook.startswith("existingRedshiftHook();"))
        self.assertIn("TH_BATCH_EVENT", post_hook)

    def test_rendered_flag_excludes_shots_but_test_render_includes_first_frame(self):
        c = self.controller
        shot = Mock()
        values = {"name": "Shot", "start_frame": 0, "end_frame": 100, "rendered": True}
        shot.get_value.side_effect = values.get
        shot.snapshots.return_value = []
        shot.get_search_key.return_value = "shot"
        shot.get_code.return_value = "SHOT001"
        shot.get_info.return_value = values
        ep = Mock()
        ep.related.return_value = [shot]
        payload = domain._query_shots(ep, c._config)
        self.assertTrue(payload[0]["excluded"])
        self.assertEqual((payload[0]["start"], payload[0]["end"]), (0, 100))
        c.episodes.replace([{"searchKey": "ep", "title": "Episode"}])
        with (
            patch.object(catalog_controller, "_discover_queue", return_value=payload),
            patch.object(execution, "_prepare_episode", return_value={}),
            patch.object(execution, "_prepare_shot", return_value={"command": "test"}),
            patch.object(
                execution,
                "_render_native",
                return_value={
                    "exitCode": 0,
                    "elapsed": 1.0,
                    "cancelled": False,
                    "timedOut": False,
                },
            ) as render,
            patch.object(execution, "_finalize_shot") as save_shot,
            patch.object(execution, "_set_episode_task_status") as save_episode,
        ):
            c.renderEpisode(0, True)
            self.until(lambda: c._entries[0]["state"] == "waiting")
            c.startScheduler()
            self.until(lambda: c._entries[0]["state"] == "completed")
            job = render.call_args.args[0]
            self.assertEqual((job["start"], job["end"]), (1, 1))
            save_shot.assert_not_called()
            save_episode.assert_not_called()

    def test_queue_test_render_targets_episode_or_one_shot(self):
        entry = episode(shots=2)
        entry["test"] = False
        self.controller._entries = [entry]

        self.controller.testQueue(entry["jobs"][1]["id"])
        shot_test = self.controller._entries[-1]
        self.assertTrue(shot_test["test"])
        self.assertEqual(len(shot_test["jobs"]), 1)
        self.assertEqual(
            shot_test["jobs"][0]["shotKey"], entry["jobs"][1]["shotKey"]
        )
        self.assertEqual(
            (shot_test["jobs"][0]["start"], shot_test["jobs"][0]["end"]),
            (1, 1),
        )

        self.controller.testQueue(entry["id"])
        self.assertEqual(len(self.controller._entries[-1]["jobs"]), 2)

    def test_render_log_is_checked_into_episode_context_and_kept_locally(self):
        entry = episode(shots=1)
        job = entry["jobs"][0]
        job.update(
            result="completed", logPath=str(Path(self.directory.name) / "render.log")
        )
        Path(job["logPath"]).touch()
        api, shot, ep = Mock(), Mock(), Mock()
        api.sobject.side_effect = lambda key: ep if key == entry["episodeKey"] else shot
        shot.get_project.return_value.get_code.return_value = "test"
        api.repositories.list.return_value = [{"value": ["", "", "", "repo", True]}]
        domain._finalize_shot(api, entry, job, self.controller._config)
        shot.set_value.assert_called_once_with("rendered", True)
        shot.commit.assert_called_once()
        queue = api.commit_queue.return_value
        self.assertIs(queue.add.call_args.args[0], ep)
        self.assertEqual(queue.add.call_args.kwargs["context"], "render/Shot 0")
        self.assertFalse(queue.add.call_args.kwargs["generate_previews"])
        queue.add.return_value.commit.assert_called_once()
        self.assertTrue(Path(job["logPath"]).is_file())

    def test_log_checkin_modes_and_preparation_errors(self):
        log_path = Path(self.directory.name) / "render.log"
        log_path.touch()
        for mode, result, expected in (
            ("always", "completed", True),
            ("failed", "completed", False),
            ("failed", "failed", True),
            ("never", "failed", False),
        ):
            with self.subTest(mode=mode, result=result):
                entry = episode(shots=1)
                job = entry["jobs"][0]
                job.update(result=result, logPath=str(log_path))
                api, shot, parent = Mock(), Mock(), Mock()
                api.sobject.side_effect = (
                    lambda key: parent if key == entry["episodeKey"] else shot
                )
                parent.get_project.return_value.get_code.return_value = "test"
                api.repositories.list.return_value = [
                    {"value": ["", "", "", "repo", True]}
                ]
                config = dict(self.controller._config, log_checkin=mode)
                domain._finalize_shot(api, entry, job, config)
                self.assertEqual(api.commit_queue.called, expected)

        entry = episode(shots=1)
        entry["preparationErrors"] = ["Dependency unavailable"]
        api, parent = Mock(), Mock()
        api.sobject.return_value = parent
        parent.get_project.return_value.get_code.return_value = "test"
        api.repositories.list.return_value = [{"value": ["", "", "", "repo", True]}]
        path = domain._finalize_preparation_log(
            api, entry, dict(self.controller._config, log_checkin="failed")
        )
        self.assertIn("Dependency unavailable", Path(path).read_text(encoding="utf-8"))
        self.assertEqual(
            api.commit_queue.return_value.add.call_args.kwargs["context"],
            "render/preparation",
        )

    def test_dependency_download_error_can_be_skipped(self):
        file = Mock()
        file.get_filename_with_ext.return_value = "missing.abc"
        api = Mock()
        api.files.ensure_local.side_effect = OSError("offline")
        errors = []
        self.assertIsNone(domain._download_dependency(api, file, True, errors))
        self.assertIn("missing.abc", errors[0])
        with self.assertRaises(OSError):
            domain._download_dependency(api, file, False, [])
        api.files.ensure_local.side_effect = InterruptedError("cancelled")
        with self.assertRaises(InterruptedError):
            domain._download_dependency(api, file, True, [])

    def test_disabled_web_server_is_not_started(self):
        self.controller._config["web_enabled"] = False
        with patch.object(web_control, "BatchWebServer") as server:
            self.controller._restart_web_server()
        server.assert_not_called()
        self.assertEqual(self.controller.webUrl, "")

    def test_new_render_settings_are_persisted(self):
        self.controller.saveSettings(
            "Render.exe", "D:/renders", "", False, 0,
            "failed", True, 17, False, 93, True,
        )
        self.until(lambda: self.controller.settings["logCheckin"] == "failed")
        settings = self.controller.settings
        self.assertTrue(settings["skipDependencyErrors"])
        self.assertEqual(settings["pollInterval"], 17)
        self.assertFalse(settings["webEnabled"])
        self.assertEqual(settings["webPort"], 93)
        self.assertTrue(settings["webSecurity"])

    def test_final_progress_survives_worker_completion_before_qt_delivery(self):
        gate = threading.Event()
        values, done = [], []

        def worker():
            if not gate.wait(3):
                raise TimeoutError("test gate")
            render.report_progress({"text": "last renderer line"})
            return "finished"

        operation = self.controller._submit(worker, done.append, progress=values.append)
        gate.set()
        deadline = time.monotonic() + 3
        while not operation.done and time.monotonic() < deadline:
            time.sleep(0.005)  # Deliberately withhold Qt delivery until worker exits.
        self.until(lambda: bool(done))
        self.assertEqual(values, [{"text": "last renderer line"}])

    def test_discovery_has_one_worker_even_when_many_episodes_are_added(self):
        c = self.controller
        gate, entered = threading.Event(), threading.Event()
        active = 0
        maximum = 0

        def discover(*_args):
            nonlocal active, maximum
            active += 1
            maximum = max(maximum, active)
            entered.set()
            if not gate.wait(3):
                raise TimeoutError("test gate")
            active -= 1
            return [
                {
                    "searchKey": "shot",
                    "title": "shot",
                    "start": 1,
                    "end": 1,
                    "excluded": False,
                    "scenePath": "",
                }
            ]

        with patch.object(catalog_controller, "_discover_queue", side_effect=discover):
            for i in range(70):
                c._enqueue(str(i), True)
            self.until(entered.is_set)
            gate.set()
            self.until(lambda: all(e["state"] == "waiting" for e in c._entries))
        self.assertEqual(maximum, 1)
        self.assertEqual(c.errorText, "")

    def test_singleton_show_reuses_existing_dispatcher(self):
        window = Mock()
        with patch.object(
            batch_ui,
            "_RUNTIME_WINDOWS",
            [{"window": window, "controller": self.controller}],
        ):
            self.assertIs(batch_ui.show(), window)
            self.assertIs(batch_ui.show(), window)
        self.assertEqual(window.showNormal.call_count, 2)

    def test_close_restores_handler_and_registered_script_editor_window(self):
        window, handler, application = Mock(), Mock(), Mock()
        entry = {
            "window": window,
            "controller": Mock(),
            "component": Mock(),
            "application": application,
            "hidden_windows": [handler],
            "hidden_window_ids": ["script_editor"],
        }
        with patch.object(batch_ui, "_RUNTIME_WINDOWS", [entry]):
            batch_ui._dispose_window(window)
            batch_ui._dispose_window(window)
        entry["controller"].shutdown.assert_called_once()
        handler.show.assert_called_once()
        application.window_model.show_window.assert_called_once_with("script_editor")

    def test_snapshot_selection_uses_native_version_and_file_contracts(self):
        from thlib.tactic_classes import Snapshot

        def snapshot(version, process="publish"):
            value = Mock(spec=Snapshot)
            value.get_info.return_value = {"process": process}
            value.get_version.return_value = version
            value.is_versionless.return_value = version == -1
            value.get_files_objects.return_value = []
            return value

        old, latest, versionless, unrelated = (
            snapshot(1),
            snapshot(2),
            snapshot(-1),
            snapshot(3, "cache"),
        )
        self.assertEqual(
            domain._preferred_snapshots([old, latest, unrelated], "publish"), [latest]
        )
        self.assertEqual(
            domain._preferred_snapshots([old, latest, versionless], "publish"),
            [versionless],
        )
        self.assertEqual(
            domain._preferred_snapshots([old, latest], "publish", True), [old, latest]
        )
        file = Mock()
        file.get_type.return_value = "main"
        versionless.get_files_objects.return_value = [file]
        self.assertIs(domain._main_file([versionless], "publish"), file)

    def test_unchecked_queue_shot_is_not_launched(self):
        c = self.controller
        entry = episode()
        c._entries = [entry]
        c.toggleIncluded(entry["jobs"][0]["id"])
        with (
            patch.object(execution, "_prepare_episode", return_value={}),
            patch.object(execution, "_prepare_shot", return_value={"command": "test"}),
            patch.object(
                execution,
                "_render_native",
                return_value={
                    "exitCode": 0,
                    "elapsed": 0.2,
                    "cancelled": False,
                    "timedOut": False,
                },
            ) as render,
        ):
            c.startScheduler()
            self.until(lambda: entry["state"] == "completed")
        render.assert_called_once()
        self.assertEqual(
            render.call_args.args[0]["shotKey"], entry["jobs"][1]["shotKey"]
        )
        self.assertEqual(entry["jobs"][0]["state"], "skipped")
        self.assertEqual(c.summary["completed"], 1)

    def test_repository_shot_cache_scene_and_render_arguments(self):
        import zipfile

        root = Path(self.directory.name)
        archive = root / "cache.zip"
        scene_path = root / "published_scene.mb"
        scene_path.touch()
        with zipfile.ZipFile(archive, "w") as zipped:
            zipped.writestr("simulation/cache.mc", "cache")
        cache, scene, api = Mock(), Mock(), Mock()
        api.sobject.return_value.snapshots.return_value = []
        cache.get_repo_path.return_value = str(root)
        scene.get_ext.return_value = "mb"
        scene.get_filename_with_ext.return_value = scene_path.name
        api.files.ensure_local.side_effect = lambda file, **_: (
            archive if file is cache else scene_path
        )
        render_executable = root / "Render.exe"
        maya_batch = root / "mayabatch.exe"
        render_executable.touch()
        maya_batch.touch()
        config = dict(
            self.controller._config,
            maya_render_executable=str(render_executable),
            output_directory=str(root / "output"),
            camera="renderCam",
        )
        entry = episode(shots=1)
        with patch.object(preparation, "_main_file", side_effect=[cache, scene]):
            prepared = domain._prepare_shot(
                api, entry, entry["jobs"][0], config, threading.Event()
            )
        self.assertEqual(prepared["mayaBatch"], str(maya_batch))
        self.assertEqual(prepared["camera"], "renderCam")
        self.assertNotIn("args", prepared)
        self.assertIn("Frames: 1-5", prepared["command"])
        extracted = (
            root / config["cache_path"] / "ep" / "Shot 0" / "simulation/cache.mc"
        )
        self.assertEqual(extracted.read_text(), "cache")

    def test_real_process_stdout_stderr_pid_and_missing_executable(self):
        job = episode(shots=1)["jobs"][0]
        job.update(
            logPath=str(Path(self.directory.name) / "render.log"),
            args=[
                sys.executable,
                "-u",
                "-c",
                "import sys; print('Rendering frame 1'); print('100% done'); print('error detail', file=sys.stderr)",
            ],
        )
        result = domain._render_native(job, 0, threading.Event())
        self.assertEqual(result["exitCode"], 0)
        log = Path(job["logPath"]).read_text()
        self.assertIn("Rendering frame 1", log)
        self.assertIn("error detail", log)
        job["args"] = [str(Path(self.directory.name) / "missing.exe")]
        with self.assertRaises(FileNotFoundError):
            domain._render_native(job, 0, threading.Event())

    @unittest.skipUnless(os.name == "nt", "Maya CER is Windows-specific")
    def test_maya_batch_replaces_crash_report_dialog(self):
        process = Mock(returncode=0)
        process.poll.return_value = 0
        with patch.object(render.subprocess, "Popen") as popen:
            popen.return_value.__enter__.return_value = process
            domain._run_render_command(
                [r"C:\Maya\bin\mayabatch.exe"],
                [(1, 1)],
                Mock(),
                StringIO(),
                threading.Event(),
                0,
                time.monotonic(),
                False,
                threading.Event(),
                None,
            )

        environment = popen.call_args.kwargs["env"]
        self.assertEqual(environment["MAYA_DEBUG_ENABLE_CRASH_REPORTING"], "1")
        self.assertIn(r"C:\Maya\bin\mayapy.exe", environment["MAYA_USER_CER_APP"])
        self.assertIn("scheduler_cer.py", environment["MAYA_USER_CER_APP"])

    def test_real_silent_process_cancellation(self):
        job = episode(shots=1)["jobs"][0]
        job.update(
            logPath=str(Path(self.directory.name) / "silent.log"),
            args=[sys.executable, "-c", "import time; time.sleep(30)"],
        )
        cancel, started = threading.Event(), threading.Event()
        operation = self.executor.submit(domain._render_native, job, 0, cancel)
        progress = []
        operation.on_progress(lambda value: (progress.append(value), started.set()))
        self.until(started.is_set)
        self.assertGreater(progress[-1]["pid"], 0)
        cancel.set()
        self.until(lambda: operation.done, seconds=20)
        self.assertTrue(operation.result()["cancelled"])

    def test_maya_final_error_stops_hung_launcher_and_marks_shot_failed(self):
        entry = episode(shots=1)
        job = entry["jobs"][0]
        marker = "Error: file: render.tmp line 34: Scene test.ma failed to render."
        event = "TH_BATCH_EVENT " + json.dumps(
            {"type": "failed", "error": marker}
        )
        job.update(
            logPath=str(Path(self.directory.name) / "failure.log"),
            args=[
                sys.executable,
                "-u",
                "-c",
                f"import time; print({event!r}, flush=True); time.sleep(30)",
            ],
        )
        result = domain._render_native(job, 0, threading.Event())
        self.assertEqual(result["error"], marker)
        self.assertLess(result["elapsed"], 5)
        self.assertFalse(result["cancelled"])
        self.assertIn(marker, Path(job["logPath"]).read_text())
        c = self.controller
        c._entries = [entry]
        c._active_entry, c._active_job = entry, job
        # Failure output wins even when the wrapper reports successful exit.
        result["exitCode"] = 0
        c._render_done(result)
        self.assertEqual(job["state"], "failed")
        self.assertEqual(job["error"], marker)

    def test_maya_completion_stops_hung_launcher_and_retains_rendered_frames(self):
        entry = episode(shots=1)
        job = entry["jobs"][0]
        output = Path(self.directory.name) / "render"
        output.mkdir()
        frame = output / "shot.0005.png"
        frame_event = "TH_BATCH_EVENT " + json.dumps(
            {"type": "frame", "frame": 5, "files": [str(frame)]}
        )
        marker = 'TH_BATCH_EVENT {"type":"completed"}'
        job.update(
            output=str(output),
            logPath=str(Path(self.directory.name) / "completed.log"),
            args=[
                sys.executable,
                "-u",
                "-c",
                (
                    "from pathlib import Path; import time; "
                    f"Path({str(frame)!r}).write_bytes(b'frame'); time.sleep(.5); "
                    f"print({frame_event!r}, flush=True); "
                    f"print({marker!r}, flush=True); time.sleep(30)"
                ),
            ],
        )
        progress_events = []
        operation = self.executor.submit(
            domain._render_native, job, 0, threading.Event()
        )
        operation.on_progress(progress_events.append)
        self.until(lambda: operation.done, seconds=15)
        result = operation.result()
        self.assertEqual(result["exitCode"], 0)
        self.assertLess(result["elapsed"], 8)
        tracker = domain.RenderProgress(1, 5)
        tracker.feed(Path(job["logPath"]).read_text())
        self.assertTrue(tracker.wrapper_completed)
        progress = next(
            event for event in reversed(progress_events) if event.get("renderFiles")
        )
        self.assertEqual(progress["renderOutput"], str(frame.parent))
        self.assertEqual(progress["renderFiles"], [str(frame)])
        self.controller._entries = [entry]
        self.controller._selected_queue = job["id"]
        self.controller._update_job_progress(job, progress)
        self.assertEqual(self.controller.renderPreviews[0]["path"], str(frame))
        with patch.object(settings.QDesktopServices, "openUrl") as opener:
            self.controller.showDestination()
        self.assertEqual(
            Path(opener.call_args.args[0].toLocalFile()),
            Path(self.controller._config["output_directory"]),
        )
        with patch.object(settings.QDesktopServices, "openUrl") as opener:
            self.controller.showQueueDestination(entry["id"])
        self.assertEqual(Path(opener.call_args.args[0].toLocalFile()), frame.parent)

    def test_render_preview_comes_from_completed_maya_frame(self):
        frames = [Path(self.directory.name) / f"frame.{i}.png" for i in range(1, 21)]
        events = "\n".join(
            "TH_BATCH_EVENT "
            + json.dumps({"type": "frame", "frame": i, "files": [str(frame)]})
            for i, frame in enumerate(frames, 1)
        )
        progress = domain.RenderProgress(1, 20).feed(events)
        self.assertEqual(progress["renderFiles"], list(map(str, frames)))
        self.assertEqual(progress["renderOutput"], str(frames[-1].parent))

    def test_warnings_are_not_final_errors_and_unterminated_failure_is_retained(self):
        tracker = domain.RenderProgress(1, 10)
        tracker.feed(
            "Warning: missing reference\nError: line 1: Error reading file.\nRendering frame 1"
        )
        tracker.feed("debug globals: {'EVENT_PREFIX': 'TH_BATCH_EVENT '}")
        self.assertEqual(tracker.error, "")
        self.assertIsNone(tracker.frame)
        job = episode(shots=1)["jobs"][0]
        marker = "Error: Scene sample.ma failed to render."
        event = "TH_BATCH_EVENT " + json.dumps(
            {"type": "failed", "error": marker}
        )
        job.update(
            logPath=str(Path(self.directory.name) / "tail.log"),
            args=[
                sys.executable,
                "-u",
                "-c",
                f"import sys; sys.stdout.write({event!r})",
            ],
        )
        result = domain._render_native(job, 0, threading.Event())
        self.assertEqual(result["error"], marker)
        self.assertEqual(result["exitCode"], 0)

    def test_real_process_timeout_is_failure_and_stops_child_tree(self):
        import ctypes

        job = episode(shots=1)["jobs"][0]
        child_pid_path = Path(self.directory.name) / "child_pid.txt"
        script = (
            "import subprocess,sys,time,pathlib; "
            "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); "
            f"pathlib.Path({str(child_pid_path)!r}).write_text(str(child.pid)); "
            "time.sleep(30)"
        )
        job.update(
            logPath=str(Path(self.directory.name) / "timeout.log"),
            args=[sys.executable, "-u", "-c", script],
        )
        cancel = threading.Event()
        operation = self.executor.submit(domain._render_native, job, 0.01, cancel)
        self.until(child_pid_path.exists)
        child_pid = int(child_pid_path.read_text())
        process_handle = None
        if os.name == "nt":
            kernel32 = ctypes.windll.kernel32
            kernel32.OpenProcess.restype = ctypes.c_void_p
            kernel32.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
            kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
            process_handle = kernel32.OpenProcess(0x00100000, False, child_pid)
            self.assertTrue(process_handle)
        try:
            self.until(lambda: operation.done, seconds=20)
            result = operation.result()
            self.assertTrue(result["timedOut"])
            self.assertFalse(result["cancelled"])
            self.assertNotEqual(result["exitCode"], 0)
            if process_handle:
                self.assertEqual(kernel32.WaitForSingleObject(process_handle, 0), 0)
        finally:
            cancel.set()
            if process_handle:
                kernel32.CloseHandle(process_handle)

    def test_queue_checkboxes_skip_without_counting_and_preserve_finished_work(self):
        c = self.controller
        entry = episode(shots=3)
        c._entries = [entry]
        first, second, third = entry["jobs"]
        with patch.object(c, "_persist") as persist:
            c.toggleIncluded(first["id"])
            self.assertEqual(first["state"], "skipped")
            self.assertEqual(c.queue.get(0)["progress"], 0)
            self.assertEqual(c.queue.get(0)["frames"], "0/10")
            self.assertEqual(c.queue.get(1)["progress"], 0)
            persist.assert_called_once()
        third.update(state="rendering")
        c.toggleIncluded(third["id"])
        self.assertEqual(third["state"], "rendering")
        third.update(state="completed", framesDone=5)
        c.toggleIncluded(third["id"])
        self.assertEqual(third["state"], "completed")
        second.update(state="completed", framesDone=5)
        entry["state"] = "completed"
        c.toggleIncluded(first["id"])
        self.assertEqual(entry["state"], "waiting")
        self.assertEqual(first["state"], "waiting")
        self.assertEqual(third["attempt"], 1)
        entry["state"] = "saving"
        c.toggleIncluded(first["id"])
        self.assertEqual(first["state"], "waiting")
        entry["state"] = "waiting"
        c.toggleIncluded(first["id"])
        entry["saveFailed"] = True
        c.toggleIncluded(first["id"])
        self.assertEqual(first["state"], "skipped")

    @unittest.skipUnless(os.name == "nt", "Windows taskkill fallback")
    def test_taskkill_failure_uses_process_kill_and_waits(self):
        process = Mock(pid=123, poll=Mock(return_value=None))
        with patch.object(render.subprocess, "run", return_value=SimpleNamespace(returncode=1)):
            domain._stop_process_tree(process)
        process.kill.assert_called_once_with()
        process.wait.assert_called_once_with(timeout=5)
        process.kill.side_effect = PermissionError("Cannot stop renderer")
        with patch.object(render.subprocess, "run", return_value=SimpleNamespace(returncode=1)):
            with self.assertRaisesRegex(PermissionError, "Cannot stop renderer"):
                domain._stop_process_tree(process)

    def test_frame_progress_and_unknown_eta(self):
        p = domain.RenderProgress(10, 12)
        self.assertEqual(p.feed("25% done")["progress"], 0)
        first = p.feed('TH_BATCH_EVENT {"type":"frame","frame":10}')
        self.assertAlmostEqual(first["progress"], 1 / 3)
        second = p.feed('TH_BATCH_EVENT {"type":"frame","frame":11}')
        self.assertEqual(second["framesDone"], 2)
        self.assertIsNone(self.controller._job_eta(episode()["jobs"][0]))

    def test_qml_filters_real_model_and_keeps_house_controls_in_both_languages(self):
        from PySide6.QtCore import Signal, QEvent, QCoreApplication
        from thlib.ui.icon_font import fontawesome_assets
        import thlib.ui.source_editor
        class Locale(QObject):
            changed = Signal()
            code = 'en'
            current_language = Property(str, lambda self:self.code, notify=changed)
        c = self.controller
        locale = Locale()
        messages = []
        previous = qInstallMessageHandler(lambda kind,ctx,text: messages.append(text)
            if not ('does not support raise' in text and QGuiApplication.platformName() == 'offscreen') else None)
        engine = QQmlEngine()
        engine.rootContext().setContextProperty('localizationController',locale)
        solid, solid_font, regular, regular_font = fontawesome_assets(ROOT)
        for key,value in dict(fontAwesomeSolidGlyphs=solid,fontAwesomeSolidFontFamily=solid_font,
                              fontAwesomeRegularGlyphs=regular,fontAwesomeRegularFontFamily=regular_font).items():
            engine.rootContext().setContextProperty(key,value)
        parent = Root()
        component,window = batch_ui._create_window(engine,ROOT,parent,c)
        QQmlEngine.setObjectOwnership(window,QQmlEngine.ObjectOwnership.CppOwnership)
        records = [dict(title=f'Episode {i}',searchKey=f'catalog-{i}',code=f'EP{i}',subtitle='Description',
                        previewUrl='',renderStatus='Custom' if i == 1 else 'Подготовлен',
                        statusColor='#ffffff',statusChoices=[],queued=False,selected=False) for i in range(30)]
        c._catalog = records
        c._replace_episode_filters([dict(value=status,title=status,count=1,statusAccent='')
                                   for status in ('Подготовлен','Custom')])
        c._filter_episodes()
        c._entries = [episode('queued',2)]
        c._publish_queue()
        window.show()
        def click(item):
            QTest.mouseClick(window,Qt.MouseButton.LeftButton,pos=item.mapToScene(
                QPointF(item.width()/2,item.height()/2)).toPoint())
        try:
            for language in ('en','ru'):
                locale.code=language
                locale.changed.emit()
                for width,height in ((1440,920),(950,650)):
                    window.resize(width,height)
                    self.app.processEvents()
                    self.until(lambda:window.findChild(QObject,'batchEpisodeSearch') is not None)
                    search=window.findChild(QObject,'batchEpisodeSearch')
                    search.setProperty('text','episode 17')
                    self.until(lambda:c.episodes.rowCount()==1)
                    self.assertEqual(c.episodes.get(0)['code'],'EP17')
                    self.until(lambda:self.visual(window.contentItem(),'batchEpisodeRow_0') is not None)
                    row=self.visual(window.contentItem(),'batchEpisodeRow_0')
                    self.until(lambda:0 <= row.mapToScene(QPointF(10,10)).y() < window.height())
                    click(row)
                    self.assertEqual(c._selected_episode,'catalog-17')
                    c._selected_episode=''
                    device=QTest.createTouchDevice()
                    QTest.qWait(200)
                    self.until(lambda:self.visual(window.contentItem(),'batchEpisodeRow_0') is not None)
                    row=self.visual(window.contentItem(),'batchEpisodeRow_0')
                    point=row.mapToScene(QPointF(100,30)).toPoint()
                    QTest.touchEvent(window,device).press(0,point,window).commit()
                    QTest.touchEvent(window,device).release(0,point,window).commit()
                    self.until(lambda:c._selected_episode=='catalog-17')
                    search.setProperty('text','')
                    self.until(lambda:c.episodes.rowCount()==30)
                    filter_button=self.visual(window.contentItem(),'batchEpisodeFilterButton')
                    click(filter_button)
                    popup=window.findChild(QObject,'batchEpisodeFilterMenu')
                    self.until(lambda:popup.property('visible'))
                    # The real popup command reaches the same local filter owner.
                    popup.triggered.emit('status:Custom')
                    self.until(lambda:c.episodes.rowCount()==29)
                    popup.close()
                    self.until(lambda:not popup.property("visible"))
                    window.requestActivate()
                    c.toggleEpisodeStatusFilter('Custom')
                    self.assertEqual(c.episodes.rowCount(),30)
                    summary=window.findChild(QObject,'batchSummaryBar')
                    self.assertEqual(summary.height(),62)
                    start=window.findChild(QObject,'batchStartQueue')
                    self.assertEqual(start.property('text'),'Запустить очередь' if language=='ru' else 'Start queue')
                    with patch.object(c,'_pump'):
                        start.forceActiveFocus()
                        QTest.qWait(200)
                        self.assertTrue(start.property("activeFocus"),f"focus {language} {width}")
                        QTest.keyClick(window,Qt.Key.Key_Space)
                        self.until(lambda:not c.paused)
                        c.stopScheduler()
                    c._busy=True
                    c.stateChanged.emit()
                    self.assertEqual(c.episodes.rowCount(),30)
                    self.assertTrue(filter_button.isEnabled())
                    c._busy=False
                    c.stateChanged.emit()
            if os.environ.get('BATCH_SCREENSHOT'):
                window.resize(1440,920)
                QTest.qWait(50)
                window.grabWindow().save(os.environ['BATCH_SCREENSHOT'])
            self.assertFalse(messages,'\n'.join(messages))
        finally:
            window.hide()
            window.deleteLater()
            component.deleteLater()
            QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
            engine.deleteLater()
            self.app.processEvents()
            qInstallMessageHandler(previous)

    def test_http_health_validation_and_release_port(self):
        from urllib.request import Request
        from urllib.parse import urlsplit
        requests=[]
        server=BatchWebServer(lambda request: requests.append(request) or {'ok':True},host='127.0.0.1')
        self.addCleanup(server.stop)
        url=server.start()
        self.assertTrue(server.alive)
        origin=urlsplit(url)
        base=f'http://{origin.netloc}'
        headers={'X-Batch-Token':server.token,'Content-Type':'application/json','Origin':base}
        with urlopen(Request(base+'/api/health',headers=headers),timeout=2) as response:
            self.assertEqual(json.load(response)['status'],'ok')
        request=Request(base+'/api/action',json.dumps({'type':'state','action':'refresh'}).encode(),headers)
        with urlopen(request,timeout=2) as response:
            self.assertTrue(json.load(response)['ok'])
        self.assertEqual(requests[-1]['type'],'action')
        for payload, extra, status in [([],{},400),({}, {},400),({'action':'refresh'},{'Origin':'http://other.invalid'},403)]:
            with self.assertRaises(HTTPError) as caught:
                urlopen(Request(base+'/api/action',json.dumps(payload).encode(),dict(headers,**extra)),timeout=2)
            self.assertEqual(caught.exception.code,status)
            caught.exception.close()
        occupied=BatchWebServer(lambda request:{},host='127.0.0.1',port=server.port)
        self.addCleanup(occupied.stop)
        with self.assertRaises(OSError): occupied.start()
        self.assertFalse(occupied.alive)
        server.stop()
        self.assertFalse(server.alive)
        server.start()
        self.assertTrue(server.alive)

    def test_shutdown_releases_pending_web_request_without_waiting_for_timeout(self):
        result=[]
        def request():
            try:self.controller._web_dispatch({'type':'state'})
            except RuntimeError as error:result.append(str(error))
        worker=threading.Thread(target=request)
        worker.start()
        deadline=time.monotonic()+2
        while not self.controller._web_pending and time.monotonic()<deadline:
            threading.Event().wait(.001)
        self.controller.shutdown()
        worker.join(1)
        self.assertFalse(worker.is_alive())
        self.assertEqual(result,['Batch Render is closing'])

    def descendants(self, item):
        for child in item.childItems():
            yield child
            yield from self.descendants(child)


if __name__ == "__main__":
    unittest.main()

"""Table checkout exercises real native File paths, transfer workers and shared controls."""

import io
import threading
import time
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtTest import QTest
import tests.test_frame_table as frames
from thlib.ui.repository_sync import RepositorySyncController
from thlib.ui.table.file_checkout import SnapshotCheckoutController
from thlib.ui.workspace_models.windows import FloatingWindowModel


class Response(io.BytesIO):
    headers = {"Content-Length": "6"}


class TableCheckoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = frames.gui_test_application()

    create = frames.FrameTableTests.create
    item = frames.FrameTableTests.item
    click = frames.FrameTableTests.click

    def close(self, window, view, engine, warnings, owners):
        frames.FrameTableTests.close(self, window, view, engine, warnings, owners)
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def setUp(self):
        from thlib import tactic_classes as tc
        from thlib.environment import env_mode

        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.enterContext(patch.object(env_mode, "current_path", str(self.root)))
        self.enterContext(
            patch.object(
                tc.env_tactic,
                "get_base_dir",
                side_effect=lambda name: {
                    "value": ["assets" if name == "web" else str(self.root), "", "", "", True]
                },
            )
        )
        self.enterContext(
            patch.object(tc.env_server, "get_server", return_value="https://example.invalid")
        )
        self.enterContext(
            patch.object(tc.env_server, "is_team_local_repository", return_value=False)
        )
        self.enterContext(
            patch.object(
                RepositorySyncController, "verify_repository_md5_enabled", return_value=False
            )
        )
        self.enterContext(
            patch.object(RepositorySyncController, "auto_clean_enabled", return_value=False)
        )
        self.server = Mock()
        self.enterContext(patch.object(tc, "server_start", return_value=self.server))
        self.data = dict(
            code="S7",
            version=7,
            context="publish/reference",
            repo="base",
            project_code="cg",
            snapshot="<snapshot/>",
            __search_key__="sthpw/snapshot?code=S7",
            __search_type__="sthpw/snapshot",
            __files__=[
                dict(
                    code=code,
                    type=kind,
                    file_name=name,
                    relative_dir="cg/asset #1/100%",
                    st_size=6,
                    metadata={},
                    timestamp="2000-01-01 00:00:00",
                    __search_key__="sthpw/file?code=" + code,
                )
                for code, kind, name in [
                    ("F1", "main", "scene.ma"),
                    ("F2", "reference", "reference #100%.txt"),
                ]
            ],
        )
        self.execute = self.enterContext(
            patch.object(
                tc, "execute_procedure_serverside", side_effect=lambda *a, **kw: deepcopy(self.data)
            )
        )
        self.http = self.enterContext(
            patch(
                "thlib.repository_download.UrllibTransport.open",
                side_effect=lambda *a, **kw: Response(b"remote"),
            )
        )
        self.queue = RepositorySyncController()
        self.addCleanup(self.queue.shutdown)
        self.application = SimpleNamespace(
            repository_sync=self.queue,
            window_model=Mock(),
            debug_log=None,
            refresh_snapshot_browser=Mock(),
        )
        self.owner = SnapshotCheckoutController(self.application)
        self.addCleanup(self.owner.shutdown)

    def wait(self, predicate):
        deadline = time.monotonic() + 3
        while not predicate() and time.monotonic() < deadline:
            QTest.qWait(5)
        self.assertTrue(predicate(), self.owner.model)

    def prepare(self):
        self.owner.open("sthpw/snapshot?code=S7", "cg")
        self.wait(lambda: self.owner.model["ready"] or bool(self.owner.model["error"]))
        self.assertEqual(self.owner.model["error"], "")

    def test_open_reads_metadata_without_stating_every_local_file(self):
        from thlib import tactic_classes as tc

        for code, filename in [("F3", "\ue000.txt"), ("F4", "\U00010000.txt")]:
            self.data["__files__"].append(
                dict(self.data["__files__"][1], code=code, file_name=filename)
            )
        self.data["__files__"][2].update(st_size=None, type=None)
        self.data["__files__"].reverse()

        with (
            patch.object(
                tc.File,
                "is_exists",
                side_effect=AssertionError("Opening must not stat local files"),
            ),
            patch.object(
                tc.File,
                "is_local_current",
                side_effect=AssertionError("Opening must not stat local files"),
            ),
        ):
            self.prepare()
        self.assertEqual(
            [row["token"] for row in self.owner.files.records()], ["F1", "F2", "F4", "F3"]
        )
        self.assertEqual(self.owner.files.records()[-1]["bytes"], 0)
        self.assertEqual(self.owner.files.records()[-1]["fileType"], "")

    def test_narrow_russian_footer_keeps_both_labels_visible(self):
        self.prepare()
        self.owner._state["busy"] = True
        self.owner._rebuild()
        window, view = self.create(
            "features/table/SnapshotCheckoutView.qml",
            dict(owner=self.owner),
            width=360,
            height=560,
            context=dict(localizationController=dict(current_language="ru")),
        )
        close = self.item(view, "snapshotCheckoutClose")
        submit = self.item(view, "snapshotCheckoutDownload")
        self.assertLess(
            close.mapToScene(frames.QPointF()).y() + close.height(),
            submit.mapToScene(frames.QPointF()).y(),
        )
        for control, text in ((close, "Закрыть"), (submit, "Отменить передачу")):
            labels = [
                item
                for item in frames._visual_items(control)
                if item.metaObject().indexOfProperty("elide") >= 0 and item.property("text") == text
            ]
            self.assertTrue(labels, text)
            self.assertTrue(all(item.width() >= item.implicitWidth() - 1 for item in labels), text)

    def test_house_progress_uses_accent_independent_of_qt_style(self):
        from PySide6.QtCore import QUrl
        from PySide6.QtQml import QQmlComponent, QQmlEngine

        engine = QQmlEngine()
        self.addCleanup(engine.deleteLater)
        component = QQmlComponent(engine)
        component.setData(b"import QtQuick.Controls as Base; Base.ProgressBar {}", QUrl())
        preload = component.create()
        self.assertIsNotNone(preload, component.errors())
        preload.setParent(engine)
        window, view = self.create(
            "controls/feedback/ProgressBar.qml", dict(value=0.4), width=200, height=6
        )
        action = view.property("theme").property("action")
        self.assertEqual(view.property("contentItem").property("color"), action)
        background = view.property("background").property("color")
        self.assertAlmostEqual(background.alphaF(), 0.25, delta=0.005)
        self.assertEqual(window.grabWindow().pixelColor(20, 3), action)

    def test_first_click_selects_exact_file_and_transfers_its_native_path(self):
        self.prepare()
        self.assertEqual(self.execute.call_args.kwargs["project"], "cg")
        self.assertIs(self.execute.call_args.kwargs["server"], self.server)
        self.assertEqual(self.owner.model["version"], 7)
        window, view = self.create(
            "features/table/SnapshotCheckoutView.qml", dict(owner=self.owner), width=760, height=560
        )
        self.assertTrue(self.item(view, "snapshotCheckoutDownload").property("highlighted"))
        self.click(window, self.item(view, "snapshotCheckoutFile_F2"))
        self.assertEqual(self.owner._selected, "F2")
        selection = self.item(view, "snapshotCheckoutFile_F2").property("background")
        self.assertEqual(
            selection.property("selectedColor"),
            selection.property("theme").property("contentSelection"),
        )
        target = self.root / "cg/asset #1/100%/reference #100%.txt"
        self.click(window, self.item(view, "snapshotCheckoutDownload"))
        self.wait(lambda: target.is_file() and not self.owner.busy)
        self.assertEqual(target.read_bytes(), b"remote")
        self.assertIn(
            "/asset%20%231/100%25/reference%20%23100%25.txt", self.http.call_args.args[0].full_url
        )
        self.assertTrue(self.owner.files.records()[1]["selected"])
        self.application.refresh_snapshot_browser.assert_called_once_with()

    def test_conflict_needs_explicit_overwrite_and_cancel_keeps_local_bytes(self):
        target = self.root / "cg/asset #1/100%/scene.ma"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"local original")
        self.prepare()
        window, view = self.create(
            "features/table/SnapshotCheckoutView.qml", dict(owner=self.owner), width=760, height=560
        )
        self.click(window, self.item(view, "snapshotCheckoutDownload"))
        self.wait(lambda: self.owner.model["conflict"])
        self.http.assert_not_called()
        self.click(window, self.item(view, "confirmationReject"))
        self.assertFalse(self.owner.model["conflict"])
        self.assertEqual(target.read_bytes(), b"local original")
        self.click(window, self.item(view, "snapshotCheckoutDownload"))
        self.wait(lambda: self.owner.model["conflict"])
        self.click(window, self.item(view, "confirmationAccept"))
        self.wait(lambda: not self.owner.busy)
        self.assertEqual(target.read_bytes(), b"remote")

    def test_empty_snapshot_disables_transfer_and_context_window_never_restores_open(self):
        self.data["__files__"] = []
        self.prepare()
        window, view = self.create(
            "features/table/SnapshotCheckoutView.qml", dict(owner=self.owner), width=360, height=560
        )
        self.assertFalse(self.item(view, "snapshotCheckoutDownload").isEnabled())
        self.assertIsNotNone(self.item(view, "snapshotCheckoutFilesScrollBar"))
        windows = FloatingWindowModel({})
        state = next(row for row in windows._windows if row.window_id == "snapshot_checkout")
        self.assertTrue(state.blocking)
        self.assertEqual((state.width, state.height), (760, 560))
        self.assertIn("snapshot_checkout", windows._context_required_windows)

    def test_cancel_during_local_stat_invalidates_its_late_result(self):
        self.prepare()
        window, view = self.create(
            "features/table/SnapshotCheckoutView.qml", dict(owner=self.owner), width=760, height=560
        )
        entered, release = threading.Event(), threading.Event()

        def stat():
            entered.set()
            if not release.wait(3):
                raise TimeoutError("Test stat was not released")
            return False

        with patch.object(self.owner._files["F1"], "is_exists", side_effect=stat):
            self.click(window, self.item(view, "snapshotCheckoutDownload"))
            self.wait(entered.is_set)
            self.assertTrue(self.owner.busy)
            self.click(window, self.item(view, "snapshotCheckoutDownload"))
            self.assertFalse(self.owner.busy)
            release.set()
            self.wait(lambda: not self.owner._workers)
        self.http.assert_not_called()
        self.assertFalse(self.owner.model["conflict"])
        self.assertEqual(self.owner.model["message"], "Download cancelled")

    def test_close_during_http_transfer_cancels_without_publishing_file(self):
        entered, release = threading.Event(), threading.Event()

        class BlockedResponse(Response):
            def read(self, *args):
                entered.set()
                if not release.wait(3):
                    raise TimeoutError("Test HTTP read was not released")
                return super().read(*args)

        self.http.side_effect = lambda *args, **kwargs: BlockedResponse(b"remote")
        self.prepare()
        window, view = self.create(
            "features/table/SnapshotCheckoutView.qml", dict(owner=self.owner), width=760, height=560
        )
        self.click(window, self.item(view, "snapshotCheckoutDownload"))
        self.wait(entered.is_set)
        task_id = self.owner._task_id
        self.click(window, self.item(view, "snapshotCheckoutClose"))
        self.assertFalse(self.owner.isOpen)
        release.set()
        self.wait(lambda: self.queue.model.record(task_id).get("status") == "cancelled")
        self.assertFalse((self.root / "cg/asset #1/100%/scene.ma").exists())
        self.assertFalse(list(self.root.rglob("*.part")))
        self.assertEqual(self.owner.files.rowCount(), 0)
        self.application.refresh_snapshot_browser.assert_not_called()

    def test_late_read_cannot_reopen_a_closed_scope(self):
        entered, release = threading.Event(), threading.Event()

        def read(*args, **kwargs):
            entered.set()
            if not release.wait(3):
                raise TimeoutError("Test read was not released")
            return deepcopy(self.data)

        self.execute.side_effect = read
        self.owner.open("sthpw/snapshot?code=S7", "cg")
        self.wait(entered.is_set)
        self.owner.shutdown()
        release.set()
        self.wait(lambda: not self.owner._workers)
        self.assertFalse(self.owner.isOpen)
        self.assertEqual(self.owner.files.rowCount(), 0)
        self.assertFalse(self.owner.model["ready"])


if __name__ == "__main__":
    unittest.main()

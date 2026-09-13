"""Exercise the existing Qt queue owner through the public API gateway."""

from concurrent.futures import Future, ThreadPoolExecutor
import os
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEventLoop, QObject, QThread, QTimer, Signal, Slot
from PySide6.QtQuick import QQuickWindow
from tests.qt_application import gui_test_application
from thlib.ui.api_bridge import DesktopQueue
from thlib.ui.commit_queue import CommitQueueController
from tactic_handler_api import (
    BlockingCallError, HandlerAPI, Operation, QueueFull, UIUnavailable,
)


class Dispatch(QObject):
    requested = Signal(object)
    finished = Signal()

    def __init__(self):
        super().__init__()
        self.requested.connect(self.execute)

    @Slot(object)
    def execute(self, request):
        callback, args, future = request
        try:
            future.set_result(callback(*args))
        except Exception as error:
            future.set_exception(error)

    def call(self, callback, *args):
        result = Future()
        self.requested.emit((callback, args, result))
        return result.result(timeout=3)


class CheckinExecutor(QObject):
    preparationChanged = Signal()
    operationFinished = Signal(bool, str)
    operationResult = Signal(object)
    preparedValidationFinished = Signal(str, bool, dict, str)
    operationBusy = False
    operationState = ""
    operationStage = ""
    operationProgress = 0.0
    operationError = ""

    def __init__(self):
        super().__init__()
        self.calls = []
        self.finish = None

    def validate_prepared_operation(self, request_id, payload):
        self.preparedValidationFinished.emit(request_id, True, {}, "")

    def start_prepared_operation(self, payload):
        self.calls.append(payload)
        self.operationState = "running"
        self.operationBusy = True
        if self.finish:
            QTimer.singleShot(0, self.finish)
        return True


class DesktopApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.source = Path(self.directory.name) / "source.txt"
        self.source.write_text("source", encoding="utf-8")
        for name in ("env_read_config", "env_write_config"):
            patcher = patch(
                "thlib.ui.commit_queue." + name,
                side_effect=(
                    lambda *args, **kwargs: (
                        [] if kwargs.get("filename") == "pending" else {}
                    )
                ),
            )
            patcher.start()
            self.addCleanup(patcher.stop)
        self.queue = CommitQueueController()
        self.executor = CheckinExecutor()
        self.queue.attach_executor(self.executor)
        self.dispatch = Dispatch()
        self.gateway = DesktopQueue(self.queue, self.dispatch.call)
        self.addCleanup(self.gateway.close)

    def payload(self, context="publish"):
        return {
            "searchKey": "types/object?project=demo&code=O1",
            "context": context,
            "process": context.split("/", 1)[0],
            "repository": "repo",
            "files": [{"path": str(self.source)}],
            "filesDict": [("source", {"t": ["file"], "e": ["txt"]})],
        }

    def worker_call(self, callback):
        loop = QEventLoop()
        self.dispatch.finished.connect(loop.quit)
        deadline = QTimer()
        deadline.setSingleShot(True)
        deadline.timeout.connect(loop.quit)
        with ThreadPoolExecutor(1) as pool:
            future = pool.submit(callback)
            future.add_done_callback(lambda _future: self.dispatch.finished.emit())
            deadline.start(3000)
            if not future.done():
                loop.exec()
            deadline.stop()
            self.dispatch.finished.disconnect(loop.quit)
            if not future.done():
                self.gateway.close()
                raise TimeoutError("Desktop API did not finish")
            return future.result()

    def ui_api(self):
        from thlib.ui.handler_server_controller import HandlerServerController

        calls = []

        def record(command, value=""):
            self.assertEqual(QThread.currentThread(), self.app.thread())
            if value == "missing":
                raise ValueError("Unknown project")
            calls.append((command, value))

        application = SimpleNamespace(
            select_project=lambda code: record("project", code),
            open_search_key=lambda key: record("sobject", key),
            window_model=SimpleNamespace(show_window=lambda key: record("window", key)),
            dock_model=SimpleNamespace(show_panel=lambda key: record("dock", key)),
        )
        controller = HandlerServerController(self.directory.name, None)
        controller.attach_application(application, None)
        self.addCleanup(controller.deleteLater)
        self.addCleanup(controller.shutdown)
        window = QQuickWindow()
        self.addCleanup(window.deleteLater)
        self.addCleanup(window.close)
        controller.showWindowRequested.connect(window.show)
        api = HandlerAPI(
            None, None, ui=controller._tactic_service._ui_api,
            max_workers=1, max_pending=2,
        )
        self.addCleanup(lambda: api.close(wait=False))
        return api, calls, window

    def test_ui_show_is_safe_on_gui_thread_and_uses_existing_dispatcher(self):
        api, calls, window = self.ui_api()
        ui = api.ui
        operation = ui.show()
        self.assertIsInstance(operation, Operation)
        self.assertIs(self.worker_call(lambda: operation.wait(3)), ui)
        self.app.processEvents()
        self.assertTrue(window.isVisible())
        self.assertEqual(calls, [])
        self.assertFalse(hasattr(ui, "application"))

    def test_ui_handles_dispatch_navigation_and_panel_as_one_operation(self):
        api, calls, _window = self.ui_api()
        key = "types/object?project=demo&code=O1"
        commands = [
            (api.ui.project("demo"), [("project", "demo")]),
            (api.ui.sobject(key), [("sobject", key)]),
            (api.ui.window("commit_queue"), [("window", "commit_queue")]),
            (api.ui.dock("tasks"), [("dock", "tasks")]),
            (api.ui.project("demo").commit_queue(),
             [("project", "demo"), ("window", "commit_queue")]),
            (api.ui.sobject(key).notes(), [("sobject", key), ("dock", "notes")]),
            (api.ui.sobject(key).commit_queue(),
             [("sobject", key), ("window", "commit_queue")]),
        ]
        self.assertEqual(calls, [])
        for handle, expected in commands:
            with self.subTest(handle=type(handle).__name__):
                operation = handle.show()
                self.assertIsInstance(operation, Operation)
                self.assertIs(self.worker_call(lambda: operation.wait(3)), handle)
                self.assertEqual(calls, expected)
                calls.clear()

    def test_fast_save_uses_the_selected_dcc_checkin_pipeline(self):
        from thlib.ui.tactic_rpc import UICommands

        key = "types/object?project=demo&code=O1"
        source = SimpleNamespace(
            get_search_key=lambda: key,
            get_code=lambda: "O1",
            get_title=lambda: "Object 1",
        )
        checkin = SimpleNamespace(start_dcc_scene_checkin=Mock(return_value=True))
        application = SimpleNamespace(
            _resolve_search_key=lambda value: (
                {"project": "demo"}, source
            ) if value == key else (None, None),
        )
        shown = []
        commands = UICommands(
            application,
            self.dispatch.call,
            shown.append,
            checkin,
        )
        api = HandlerAPI(None, None, ui=commands)
        self.addCleanup(lambda: api.close(wait=False))

        operation = api.ui.checkin_from_dcc(
            key, "publish", "Fast Save", "nuke", "nuke-42"
        )
        self.worker_call(lambda: operation.wait(3))

        target, payload, capability = (
            checkin.start_dcc_scene_checkin.call_args.args
        )
        self.assertEqual(target["searchKey"], key)
        self.assertEqual(target["context"], "publish")
        self.assertEqual(target["description"], "Fast Save")
        self.assertEqual(payload["client_id"], "nuke-42")
        self.assertEqual(payload["application_type"], "nuke")
        self.assertTrue(payload["generate_previews"])
        self.assertTrue(payload["update_versionless"])
        self.assertEqual(capability, "prepare_checkin")
        self.assertEqual(shown, [{}])

    def test_file_checkin_keeps_the_controller_checkin_settings(self):
        from thlib.ui.tactic_rpc import UICommands

        key = "types/object?project=demo&code=O1"
        source = SimpleNamespace(
            get_search_key=lambda: key,
            get_code=lambda: "O1",
            get_title=lambda: "Object 1",
        )
        checkin = SimpleNamespace(prepare_external_checkin=Mock())
        application = SimpleNamespace(
            _resolve_search_key=lambda value: (
                ({"project": "demo"}, source)
                if value == key else (None, None)
            ),
        )
        shown = []
        commands = UICommands(
            application, self.dispatch.call, shown.append, checkin
        )
        api = HandlerAPI(None, None, ui=commands)
        self.addCleanup(lambda: api.close(wait=False))

        operation = api.ui.checkin_files(
            key, "publish", "Texture check-in", [str(self.source)]
        )
        self.worker_call(lambda: operation.wait(3))

        checkin.prepare_external_checkin.assert_called_once_with(
            search_key=key,
            source=source,
            project_code="demo",
            title="Object 1",
            code="O1",
            context="publish",
            description="Texture check-in",
            paths=[str(self.source)],
            file_types=["main"],
            queue_before_naming=True,
        )
        self.assertEqual(shown, [{}])

    def test_ui_show_inside_data_worker_does_not_resubmit_or_deadlock(self):
        api, calls, _window = self.ui_api()
        handle = api.ui.window("commit_queue")
        operation = api.submit(lambda: handle.show().result())
        self.assertIs(self.worker_call(lambda: operation.wait(3)), handle)
        self.assertEqual(calls, [("window", "commit_queue")])

    def test_ui_errors_and_cancellation_use_the_operation_contract(self):
        api, calls, _window = self.ui_api()
        operation = api.ui.project("missing").commit_queue().show()
        with self.assertRaisesRegex(ValueError, "Unknown project"):
            self.worker_call(lambda: operation.wait(3))
        self.assertEqual(operation.state, "failed")
        self.assertEqual(calls, [])
        entered, release = threading.Event(), threading.Event()
        self.addCleanup(release.set)

        def occupy_worker():
            entered.set()
            if not release.wait(3):
                raise TimeoutError("Test worker was not released")

        busy = api.submit(occupy_worker)
        self.assertTrue(entered.wait(3))
        pending = api.ui.window("commit_queue").show()
        with self.assertRaises(QueueFull):
            api.ui.dock("notes").show()
        with self.assertRaises(BlockingCallError):
            pending.wait(3)
        self.assertTrue(pending.cancel())
        release.set()
        self.worker_call(lambda: busy.wait(3))
        self.assertEqual(pending.state, "cancelled")
        self.assertEqual(calls, [])
        api.close(wait=False)
        with self.assertRaisesRegex(RuntimeError, "closed"):
            api.ui.show()

    def test_headless_ui_failure_is_an_operation_not_a_gui_thread_error(self):
        api = HandlerAPI(None, None)
        self.addCleanup(lambda: api.close(wait=False))
        operation = api.ui.show()
        self.assertIsInstance(operation, Operation)
        with self.assertRaises(UIUnavailable):
            self.worker_call(lambda: operation.wait(3))

    def test_description_changes_exact_item_despite_bulk_selection(self):
        first = self.gateway.add(self.payload(), "First")
        second = self.gateway.add(self.payload("model"), "Second")
        self.queue.set_apply_to_checked(True)
        self.worker_call(
            lambda: self.gateway.update(first, {"description": "Only first"})
        )
        self.assertEqual(self.queue.count, 2)
        self.assertEqual(self.queue.operation(first)["description"], "Only first")
        self.assertFalse(self.queue.operation(second).get("description"))
        with self.assertRaisesRegex(ValueError, "already in the queue"):
            self.gateway.add(self.payload(), "Duplicate")

    def test_commit_uses_visible_queue_and_keeps_result_after_auto_clean(self):
        self.queue._auto_clean = True
        identity = self.gateway.add(self.payload(), "Object")
        result = {"__search_key__": "sthpw/snapshot?code=S1", "code": "S1"}

        def finish():
            self.executor.operationResult.emit(result)
            self.executor.operationBusy = False
            self.executor.operationState = "completed"
            self.executor.operationFinished.emit(True, "")

        self.executor.finish = finish
        self.assertEqual(
            self.worker_call(lambda: self.gateway.commit(identity)), result
        )
        self.assertEqual(len(self.executor.calls), 1)
        self.assertEqual(self.queue.count, 0)
        self.assertEqual(self.gateway.get(identity)["state"], "finished")
        self.assertEqual(
            self.worker_call(lambda: self.gateway.commit(identity)), result
        )
        self.assertEqual(len(self.executor.calls), 1)
        self.assertFalse(self.gateway._scheduled)

    def test_shutdown_unblocks_pending_caller_and_ui_wait_is_rejected(self):
        api = HandlerAPI(None, None)
        try:
            with self.assertRaises(BlockingCallError):
                api.close()
            self.assertFalse(api._closed)
        finally:
            api.close(wait=False)
        identity = self.gateway.add(self.payload(), "Object")
        with self.assertRaises(BlockingCallError):
            self.gateway.commit(identity)
        self.executor.finish = self.gateway.close
        with self.assertRaisesRegex(RuntimeError, "shutting down"):
            self.worker_call(lambda: self.gateway.commit(identity))

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

from PySide6.QtCore import QCoreApplication, QEvent, QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from thlib.ui.workspace_models.records import RecordListModel
from thlib.ui.ui_performance import UiPerformanceMonitor
from thlib.ui.controllers.tab_switch_performance import SearchTabSwitchMonitor
from tests.test_tasks_controller import FakeApplication, FakeTask
from thlib.ui.tasks import TasksController
from thlib.ui.localization import CatalogTranslator
from thlib.environment import env_mode
from tests.profile_ui_responsiveness import frame

QML = Path(__file__).resolve().parents[1] / "thlib/ui/qml"


class UiResponsivenessTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def setUp(self):
        temporary = TemporaryDirectory(prefix="tactic-responsiveness-")
        self.addCleanup(temporary.cleanup)
        redirect = patch.object(env_mode, "current_path", temporary.name)
        redirect.start()
        self.addCleanup(redirect.stop)

    def test_task_selection_does_not_rebuild_projections(self):
        application = FakeApplication()
        controller = TasksController(application)
        application.workspace_state._task_sobjects = [
            FakeTask(code=f"TASK{i}") for i in range(300)
        ]
        controller.use_current_object()
        with patch.object(controller, "_rebuild_advanced_models") as rebuild:
            controller.activate_advanced_task("TASK10", 0)
            controller.toggle_advanced_checked("TASK20")
        rebuild.assert_not_called()
        selected = [r for r in controller.table_model.records() if r["selected"]]
        self.assertEqual([r["taskCode"] for r in selected], ["TASK10"])

    def test_prepend_preserves_existing_row_identity_without_role_changes(self):
        model = RecordListModel(("id", "text"), identity_role="id")
        rows = [{"id": str(i), "text": str(i)} for i in range(300)]
        model.replace(rows)
        changes, insertions = [], []
        model.dataChanged.connect(lambda *args: changes.append(args))
        model.rowsInserted.connect(lambda _, first, last: insertions.append((first, last)))
        model.replace([{"id": "new", "text": "New"}] + rows)
        self.assertEqual(changes, [])
        self.assertEqual(insertions, [(0, 0)])
        self.assertEqual(model.get(1), rows[0])

    def test_reopening_notes_reuses_history_only_for_the_same_task(self):
        from tests.test_notes_qml import _Application, _SObject
        from thlib.ui.communication import CommunicationController

        application = _Application()
        key = "test/assets?code=ASSET1"
        application.workspace_state._selected_sobject = _SObject({"code": "ASSET1"}, key)
        controller = CommunicationController(application)
        controller._selected_object = {"searchKey": key}
        controller._selected_task_code = "TASK1"
        controller._loaded_task_context = (key, controller._process, "TASK1")
        controller._sync_selection_presentation = Mock()
        controller._use_workspace_history = Mock(return_value=False)
        controller._refresh_process_counts = Mock()
        controller._refresh_pending_task_context = Mock()
        controller.refresh = Mock()
        controller.set_visible(True)
        controller.refresh.assert_not_called()
        controller.set_visible(False)
        controller._selected_task_code = "TASK2"
        controller.set_visible(True)
        controller.refresh.assert_called_once_with()
        controller.shutdown()

    def test_keyed_reconciliation_updates_only_the_edited_row(self):
        model = RecordListModel(("id", "text"), identity_role="id")
        model.replace([{"id": "a", "text": "A"}, {"id": "b", "text": "B"}])
        changes = []
        model.dataChanged.connect(lambda first, last, _: changes.append((first.row(), last.row())))
        model.replace([{"id": "x", "text": "X"}, {"id": "a", "text": "A"}, {"id": "b", "text": "Edited"}])
        self.assertEqual(changes, [(2, 2)])

    def test_diagnostics_are_bounded_and_do_not_publish_while_hidden(self):
        monitor = UiPerformanceMonitor()
        for _ in range(300):
            monitor.end_operation(monitor._begin("Tasks"))
        self.assertEqual(monitor.model.count(), 0)
        monitor.set_visible(True)
        self.assertEqual(monitor.model.count(), 250)
        monitor.shutdown()

    def test_ui_measurements_are_disabled_by_default(self):
        monitor = UiPerformanceMonitor()
        self.addCleanup(monitor.shutdown)

        self.assertFalse(monitor.recording)
        with monitor.measure("Tasks: select row"):
            pass
        self.assertEqual(monitor.begin_operation("Search tab: Assets"), 0)
        self.assertEqual(list(monitor._samples), [])
        self.assertEqual(monitor._pending, {})

    def test_other_window_frame_cannot_finish_an_input_measurement(self):
        monitor = UiPerformanceMonitor()
        with patch("thlib.ui.ui_performance.time.perf_counter", return_value=1.):
            token = monitor._begin("Pointer", "Tasks", 123)
        monitor._pending[token]["handlerMs"] = 4
        monitor._frame(456, 1.01)
        self.assertIn(token, monitor._pending)
        monitor._frame(123, 1.02)
        self.assertNotIn(token, monitor._pending)
        self.assertAlmostEqual(monitor._samples[0]["frameMs"], 20)
        monitor.shutdown()

    def test_background_publication_does_not_claim_the_focused_window_frame(self):
        monitor = UiPerformanceMonitor()
        self.addCleanup(monitor.shutdown)
        monitor.set_recording(True)
        with monitor.measure("Notes: publish history"):
            pass
        self.assertEqual(monitor._samples[0]["status"], "Controller work")
        self.assertEqual(monitor._samples[0]["window"], "")
        self.assertEqual(monitor._samples[0]["readyMs"], -1)

    def test_missing_frame_is_not_reported_as_success(self):
        monitor = UiPerformanceMonitor()
        with patch("thlib.ui.ui_performance.time.perf_counter", return_value=1.):
            monitor._begin("Pointer", "Hidden", 1)
        with patch("thlib.ui.ui_performance.time.perf_counter", return_value=7.):
            monitor._expire()
        self.assertEqual(monitor._samples[0]["status"], "No frame")
        self.assertEqual(monitor._samples[0]["frameMs"], -1)
        monitor.shutdown()

    def test_frame_already_in_flight_cannot_count_as_input_feedback(self):
        monitor = UiPerformanceMonitor()
        self.addCleanup(monitor.shutdown)
        with patch("thlib.ui.ui_performance.time.perf_counter", return_value=1.):
            token = monitor._begin("Pointer", "Tasks", 123)
        monitor._pending[token]["handlerMs"] = 4
        monitor._frame(123, 1.02, .99)
        self.assertIn(token, monitor._pending)
        monitor._frame(123, 1.03, 1.01)
        self.assertAlmostEqual(monitor._samples[0]["frameMs"], 30)

    def test_ready_frame_must_be_synchronized_after_operation_commit(self):
        monitor = UiPerformanceMonitor()
        self.addCleanup(monitor.shutdown)
        with patch("thlib.ui.ui_performance.time.perf_counter", return_value=1.):
            token = monitor._begin("Switch", "Search", 123)
        monitor._pending[token].update(operation=True, handlerMs=-1)
        monitor._frame(123, 1.01, 1.005)
        self.assertAlmostEqual(monitor._pending[token]["frameMs"], 10)
        with patch("thlib.ui.ui_performance.time.perf_counter", return_value=1.1):
            monitor.end_operation(token)
        monitor._frame(123, 1.12, 1.09)
        self.assertIn(token, monitor._pending)
        monitor._frame(123, 1.13, 1.11)
        self.assertAlmostEqual(monitor._samples[0]["readyMs"], 130)

    def test_deferred_navigation_waits_for_a_new_feedback_frame(self):
        monitor = UiPerformanceMonitor()
        self.addCleanup(monitor.shutdown)
        calls = []
        monitor._feedback_callbacks[123] = [(1., lambda: calls.append("navigate"))]
        monitor._frame(123, 1.02, .99)
        self.app.processEvents()
        self.assertEqual(calls, [])
        monitor._frame(123, 1.03, 1.01)
        self.app.processEvents()
        self.assertEqual(calls, ["navigate"])

    def test_pausing_measurements_does_not_leave_navigation_switching(self):
        monitor = UiPerformanceMonitor()
        self.addCleanup(monitor.shutdown)
        switch = SearchTabSwitchMonitor(performance=monitor)
        self.assertFalse(switch.recording)
        monitor.set_recording(True)
        self.assertTrue(switch.recording)
        monitor.set_recording(False)
        serial = switch.begin("Assets")
        switch.commit(serial, {"rows": 20})
        self.assertFalse(switch.switching)
        self.assertNotIn("firstFrameMs", switch.metrics)
        self.assertFalse(switch._timeout.isActive())

    def test_diagnostic_window_real_input_layout_and_copy(self):
        translator = CatalogTranslator(QML.parent / "translations/ru.json")
        self.app.installTranslator(translator)
        self.addCleanup(self.app.removeTranslator, translator)
        monitor = UiPerformanceMonitor()
        self.addCleanup(monitor.shutdown)
        engine = QQmlEngine()
        warnings = []
        engine.warnings.connect(lambda errors: warnings.extend(e.toString() for e in errors))
        engine.rootContext().setContextProperty("uiPerformance", monitor)
        engine.rootContext().setContextProperty("uiPerformanceModel", monitor.model)
        theme_component = QQmlComponent(engine, QUrl.fromLocalFile(str(QML / "Theme.qml")))
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(engine, QUrl.fromLocalFile(str(QML / "UiPerformanceView.qml")))
        view = component.createWithInitialProperties({"theme": theme})
        self.assertIsNotNone(view, [e.toString() for e in component.errors()])
        window = QQuickWindow()
        window.setTitle("Diagnostic test")
        view.setParentItem(window.contentItem())
        window.show()
        try:
            for _ in range(20):
                serial = monitor._begin("Tasks: select row")
                monitor.set_details(serial, {"rows": 300, "phase": "selection"})
                monitor.end_operation(serial)
            monitor.set_visible(True)
            for width, height in ((720, 520), (1280, 800)):
                def resize():
                    window.resize(width, height)
                    view.setSize(window.size())
                frame(window, resize)
                history = view.findChild(QQuickItem, "uiPerformanceSamples")
                self.assertGreater(history.height(), 80)
                self.assertGreater(history.property("contentHeight"), history.height())
                for name in ("pauseUiMeasurements", "copyUiMeasurements", "clearUiMeasurements", "uiMeasurementDetails"):
                    item = view.findChild(QQuickItem, name)
                    self.assertIsNotNone(item, name)
                    bottom = item.mapToItem(view, QPointF(item.width(), item.height()))
                    self.assertLessEqual(bottom.x(), width)
                    self.assertLessEqual(bottom.y(), height)
                self.assertFalse(window.grabWindow().isNull())

            monitor.install()
            pause = view.findChild(QQuickItem, "pauseUiMeasurements")
            self.assertEqual(pause.property("text"), "Продолжить замеры")
            point = pause.mapToScene(QPointF(pause.width() / 2, pause.height() / 2)).toPoint()
            frame(window, lambda: QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, point))
            self.assertTrue(monitor.recording)
            history_point = history.mapToScene(QPointF(24, 24)).toPoint()
            frame(
                window,
                lambda: QTest.mouseClick(
                    window, Qt.LeftButton, Qt.NoModifier, history_point,
                ),
            )
            pause.forceActiveFocus()
            frame(window, lambda: QTest.keyClick(window, Qt.Key_Space))
            self.assertFalse(monitor.recording)
            samples = [s for s in monitor._samples if s["window"] == "Diagnostic test"]
            self.assertTrue(any(s["status"] == "Frame presented" and s["frameMs"] >= 0 for s in samples))
            copy = view.findChild(QQuickItem, "copyUiMeasurements")
            point = copy.mapToScene(QPointF(copy.width() / 2, copy.height() / 2)).toPoint()
            frame(window, lambda: QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, point))
            self.assertTrue(json.loads(self.app.clipboard().text()))
            self.assertEqual(warnings, [])
        finally:
            monitor.shutdown()
            window.close()
            view.setParentItem(None)
            view.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

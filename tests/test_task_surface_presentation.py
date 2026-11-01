"""Exercise real async task surfaces without readiness/visibility feedback."""
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Material")

import tests.test_tasks_controller as fixture
from tests.qt_application import gui_test_application
from PySide6.QtCore import QCoreApplication, QEvent, QPointF, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow
from thlib.environment import env_mode
from thlib.ui.tasks import TasksController
from thlib.ui.workspace_models.records import RecordListModel


class TaskSurfacePresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def test_loaded_rows_reveal_and_survive_surface_switches(self):
        with TemporaryDirectory() as settings, patch.object(env_mode, "current_path", settings):
            application = fixture.FakeApplication()
            controller = TasksController(application)
            controller.open_workspace()
            self.assertGreater(controller.advancedVisibleCount, 0)
            code = controller.table_model._records[0]["taskCode"]
            controller.stage_advanced_value(code, "description", "Retain this draft")
            engine = QQmlEngine()
            warnings = []
            engine.warnings.connect(lambda errors: warnings.extend(error.toString() for error in errors))
            qml = Path(__file__).parents[1] / "thlib/ui/qml"
            engine.addImportPath(str(qml))
            users = RecordListModel(("login", "displayName", "initials", "avatarUrl"))
            for name, value in {
                "tasksController": controller,
                "advancedTaskModel": controller.advanced_model,
                "advancedTaskTableModel": controller.table_model,
                "taskGanttModel": controller.gantt_model,
                "userListModel": users,
            }.items():
                engine.rootContext().setContextProperty(name, value)
            theme_component = QQmlComponent(engine, QUrl.fromLocalFile(str(qml / "Theme.qml")))
            theme = theme_component.createWithInitialProperties({"dark": True})
            component = QQmlComponent(engine, QUrl.fromLocalFile(str(qml / "TasksWorkspaceView.qml")))
            view = component.createWithInitialProperties({"theme": theme, "embedded": True})
            self.assertIsNotNone(view, str(component.errors()))
            window = QQuickWindow()
            view.setParentItem(window.contentItem())
            window.resize(900, 560)
            view.setSize(window.size())
            waiter = fixture.TasksQmlTests()
            try:
                window.show()
                # visual_find unwraps loaded items; inspect the Loader itself here.
                loader = view.findChild(fixture.QObject, "taskWorkspaceSurfaceLoader")
                waiter.wait_for(lambda: loader.property("firstBatchReady") and loader.isVisible())
                table = loader.property("item")
                self.assertTrue(table.property("initialPresentationReady"))
                rows = fixture.TasksQmlTests.visual_find(table, "taskBrowserList")
                self.assertGreater(rows.property("liveDelegateCount"), 0)
                gantt_button = fixture.TasksQmlTests.visual_find(view, "taskBrowserViewSwitcher_gantt")
                self.assertIsNotNone(gantt_button)
                point = gantt_button.mapToScene(QPointF(gantt_button.width() / 2, gantt_button.height() / 2))
                fixture.QTest.mouseClick(window, Qt.LeftButton, pos=point.toPoint())
                waiter.wait_for(lambda: controller.viewMode == "gantt")
                gantt = view.findChild(fixture.QObject, "taskWorkspaceGanttSurfaceLoader")
                waiter.wait_for(lambda: gantt.property("item") is not None and gantt.isEnabled())
                gantt_button.forceActiveFocus(Qt.TabFocusReason)
                fixture.QTest.keyClick(window, Qt.Key_Left)
                waiter.wait_for(lambda: controller.viewMode == "list")
                waiter.wait_for(lambda: loader.isVisible() and loader.isEnabled())
                self.assertEqual(loader.property("item"), table)
                self.assertTrue(table.property("initialPresentationReady"))
                self.assertEqual(controller.advancedDirtyCount, 1)
                self.assertEqual(controller.table_model._records[0]["description"], "Retain this draft")
                for width in (520, 1280):
                    window.resize(width, 560)
                    view.setSize(window.size())
                    waiter.wait_for(lambda: rows.width() > 0 and loader.isVisible())
                    self.assertLessEqual(rows.width(), view.width())
                controller._advanced_busy = True
                controller.advancedChanged.emit()
                self.assertFalse(loader.property("firstBatchReady"))
                controller._advanced_busy = False
                controller.advancedChanged.emit()
                waiter.wait_for(lambda: loader.property("firstBatchReady") and loader.isVisible())
                self.assertEqual(warnings, [])
            finally:
                window.close()
                view.setParentItem(None)
                view.deleteLater()
                window.deleteLater()
                QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
                controller.shutdown()

"""Production Frame scheduling through native input and the real draft owner."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
from PySide6.QtCore import QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QWheelEvent
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
from tests.qt_application import gui_test_application
from tests.profile_ui_responsiveness import frame
from tests import test_tasks_controller as fixtures
from thlib.environment import env_mode
from thlib.ui.tasks import TasksController
from thlib.ui.icon_font import qml_icon_bindings

QML = Path(__file__).resolve().parents[1] / "thlib/ui/qml"


class FrameScheduleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def setUp(self):
        isolated = TemporaryDirectory(prefix="frame-schedule-")
        self.addCleanup(isolated.cleanup)
        redirect = patch.object(env_mode, "current_path", isolated.name)
        redirect.start()
        self.addCleanup(redirect.stop)
        self.application = fixtures.FakeApplication()
        self.application.workspace_state._task_sobjects = [
            fixtures.FakeTask(
                code="TASK0001",
                id=1,
                bid_start_date="2026-08-03 09:13:00",
                bid_end_date="2026-08-05 17:20:00",
            ),
            fixtures.FakeTask(
                code="TASK0002",
                id=2,
                depend_id=1,
                bid_start_date="2026-08-06 10:15:00",
                bid_end_date="2026-08-08 18:20:00",
            ),
        ]
        self.controller = TasksController(self.application)
        self.controller._progress_column = lambda: "progress"
        self.controller.open_workspace()
        self.controller.set_view_mode("gantt")
        self.addCleanup(self.controller.shutdown)
        self.engine = QQmlEngine()
        self.warnings = []
        self.engine.warnings.connect(
            lambda errors: self.warnings.extend(error.toString() for error in errors)
        )
        for name, value in dict(
            qml_icon_bindings(QML.parents[2], self.app),
            tasksController=self.controller,
            taskGanttModel=self.controller.gantt_model,
            taskCalendarModel=self.controller.calendar_model,
        ).items():
            self.engine.rootContext().setContextProperty(name, value)
        self.theme_component = QQmlComponent(
            self.engine, QUrl.fromLocalFile(str(QML / "Theme.qml"))
        )
        self.theme = self.theme_component.createWithInitialProperties(
            {"dark": True, "popupAnimationsEnabled": False}
        )
        self.window = QQuickWindow()
        self.window.resize(1000, 540)
        self.window.show()
        self.addCleanup(self.window.close)

    def show(self, name):
        self.component = QQmlComponent(self.engine, QUrl.fromLocalFile(str(QML / name)))
        self.view = self.component.createWithInitialProperties(
            {"theme": self.theme, "width": 1000, "height": 540}
        )
        self.assertIsNotNone(
            self.view, [error.toString() for error in self.component.errors()]
        )
        self.view.setParentItem(self.window.contentItem())
        self.addCleanup(self.view.deleteLater)
        for _ in range(3):
            frame(self.window)
        return self.view

    def find(self, name):
        item = fixtures.TasksQmlTests.visual_find(self.view, name)
        self.assertIsNotNone(item, name)
        return item

    def click(self, item):
        point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2)).toPoint()
        QTest.mouseClick(self.window, Qt.LeftButton, pos=point)
        frame(self.window)

    def enter(self, item, text):
        self.click(item)
        QTest.keyClick(self.window, Qt.Key_A, Qt.ControlModifier)
        for character in text:
            QTest.keyClick(self.window, character)
        frame(self.window)

    def test_form_stages_dates_and_progress_as_one_undo_preserving_other_drafts(self):
        self.controller.stage_advanced_value(
            "TASK0001", "description", "Keep this draft"
        )
        self.show("TaskGanttView.qml")
        self.click(self.find("ganttTaskEdit"))
        self.enter(self.find("ganttEditorDuration"), "5")
        self.enter(self.find("ganttEditorProgress"), "75")
        self.assertEqual(
            self.controller._advanced_drafts["TASK0001"],
            {"description": "Keep this draft"},
        )
        QTest.keyClick(self.window, Qt.Key_Return)
        frame(self.window)
        draft = self.controller._advanced_drafts["TASK0001"]
        self.assertEqual(draft["progress"], "75")
        self.assertTrue(
            self.controller.gantt_model.get(0)["start"].endswith("09:13:00")
        )
        self.assertTrue(draft["end"].endswith("17:20:00"))
        self.assertEqual(len(self.controller._gantt_undo), 1)
        self.click(self.find("ganttUndo"))
        self.assertEqual(
            self.controller._advanced_drafts["TASK0001"],
            {"description": "Keep this draft"},
        )
        self.assertFalse(self.warnings, self.warnings)

    def test_escape_cancels_actual_resize_before_release(self):
        self.show("TaskGanttView.qml")
        grip = self.find("ganttEndGrip")
        point = grip.mapToScene(QPointF(grip.width() / 2, grip.height() / 2)).toPoint()
        QTest.mouseMove(self.window, point)
        QTest.mousePress(self.window, Qt.LeftButton, pos=point)
        QTest.mouseMove(self.window, point + QPoint(32, 0))
        frame(self.window)
        self.assertFalse(self.controller._advanced_drafts)
        QTest.keyClick(self.window, Qt.Key_Escape)
        QTest.mouseRelease(self.window, Qt.LeftButton, pos=point + QPoint(32, 0))
        frame(self.window)
        self.assertFalse(self.controller._advanced_drafts)
        self.assertFalse(self.controller._gantt_undo)
        self.assertFalse(self.warnings, self.warnings)

    def test_dependency_uses_real_ids_and_disappears_with_collapsed_rows(self):
        self.controller.set_group_mode("process")
        self.show("TaskGanttView.qml")
        self.assertTrue(self.find("ganttDependencyVerticalTASK0002").isVisible())
        key = self.controller.gantt_model.get(0)["groupKey"]
        self.controller.toggle_group_collapsed(key)
        frame(self.window)
        item = fixtures.TasksQmlTests.visual_find(
            self.view, "ganttDependencyVerticalTASK0002"
        )
        self.assertTrue(item is None or not item.isVisible())
        self.assertFalse(self.warnings, self.warnings)

    def test_calendar_day_and_month_use_the_existing_owner(self):
        self.controller.set_calendar_visible(True)
        self.show("TaskCalendarView.qml")
        self.assertEqual(self.controller.calendar_model.count(), 42)
        selected = self.find("calendarDayAction").property("text")
        self.click(self.find("calendarDayAction"))
        self.assertEqual(self.controller.selectedDay, selected)
        previous = (self.controller._calendar_year, self.controller._calendar_month)
        self.click(self.find("calendarNext"))
        self.assertNotEqual(
            previous, (self.controller._calendar_year, self.controller._calendar_month)
        )
        self.assertEqual(self.controller.selectedDay, "")
        self.click(self.find("calendarAgenda"))
        self.assertTrue(self.view.property("agenda"))
        self.assertFalse(self.warnings, self.warnings)

    def test_noop_schedule_keeps_the_redo_branch(self):
        self.controller.stage_gantt_progress("TASK0001", 75)
        self.controller.undo_gantt_change()
        undo = list(self.controller._gantt_undo)
        redo = list(self.controller._gantt_redo)
        self.assertFalse(self.controller.stage_gantt_progress("TASK0001", 40))
        self.assertEqual(self.controller._gantt_undo, undo)
        self.assertEqual(self.controller._gantt_redo, redo)
        self.controller.redo_gantt_change()
        self.assertEqual(self.controller._advanced_drafts["TASK0001"]["progress"], "75")

    def test_stale_form_cannot_stage_into_a_different_parent(self):
        self.show("TaskGanttView.qml")
        self.click(self.find("ganttTaskEdit"))
        self.enter(self.find("ganttEditorDuration"), "5")
        self.controller._advanced_raw[0]["parentKey"] = "project/other?code=OTHER"
        self.controller._rebuild_advanced_models()
        frame(self.window)
        self.click(self.find("ganttEditorApply"))
        self.assertFalse(self.controller._advanced_drafts)
        self.assertIn("changed", self.find("ganttEditorError").property("text"))
        self.assertFalse(self.warnings, self.warnings)

    def test_group_timeline_band_collapses_through_real_input(self):
        self.controller.set_group_mode("process")
        self.show("TaskGanttView.qml")
        toggle = self.find("ganttGroupToggle")
        position = toggle.mapToScene(QPointF(500, toggle.height() / 2)).toPoint()
        QTest.mouseClick(self.window, Qt.LeftButton, pos=position)
        frame(self.window)
        self.assertTrue(self.controller._collapsed_groups)
        QTest.mouseClick(self.window, Qt.LeftButton, pos=position)
        frame(self.window)
        self.assertFalse(self.controller._collapsed_groups)
        self.assertFalse(self.warnings, self.warnings)

    def test_five_hundred_rows_remain_virtualized_through_real_wheel_input(self):
        tasks = [
            fixtures.FakeTask(
                code="TASK" + str(index),
                id=index + 1,
                bid_start_date="2026-08-03 09:00:00",
                bid_end_date="2026-08-05 18:00:00",
            )
            for index in range(500)
        ]
        self.controller._advanced_raw = self.controller._task_records(tasks)
        self.controller._advanced_tasks = {
            task.get_info()["code"]: task for task in tasks
        }
        self.controller._rebuild_advanced_models()
        self.show("TaskGanttView.qml")
        self.assertEqual(self.controller.gantt_model.count(), 500)
        area = self.find("ganttTaskList")

        def delegates():
            items = [area]
            for item in items:
                items.extend(item.childItems())
            return [
                item
                for item in items
                if item.metaObject().indexOfProperty("ganttStartDay") >= 0
            ]

        self.assertLess(len(delegates()), 60)
        position = QPointF(80, 240)
        QTest.mouseMove(self.window, position.toPoint())
        event = QWheelEvent(
            position,
            QPointF(self.window.mapToGlobal(position.toPoint())),
            QPoint(),
            QPoint(0, -12000),
            Qt.NoButton,
            Qt.NoModifier,
            Qt.NoScrollPhase,
            False,
        )
        self.app.sendEvent(self.window, event)
        for _ in range(8):
            frame(self.window)
        self.assertGreater(area.property("contentY"), 0)
        self.assertLess(len(delegates()), 60)
        self.assertFalse(self.warnings, self.warnings)


if __name__ == "__main__":
    unittest.main()

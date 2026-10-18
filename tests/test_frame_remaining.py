"""Real input, retained hosts, list scale and icon validation for B14."""

import unittest
from unittest.mock import Mock

from PySide6.QtCore import QPointF, QTimer, Qt
from PySide6.QtTest import QSignalSpy, QTest
from tests.frame_remaining_fixture import Surface
from tests.profile_ui_responsiveness import frame
from tests.test_work_hours import _entry


def items(root):
    pending = [root]
    while pending:
        item = pending.pop()
        yield item
        pending.extend(item.childItems())


class FrameRemainingTests(unittest.TestCase):
    def open_surface(self, screen, width=900):
        surface = Surface(screen, width)
        self.addCleanup(surface.close)
        return surface

    def item(self, surface, name):
        return next(
            item
            for item in items(surface.window.contentItem())
            if item.objectName() == name
        )

    def click(self, surface, item):
        QTest.mouseClick(
            surface.window,
            Qt.LeftButton,
            pos=item.mapToScene(QPointF(item.width() / 2, item.height() / 2)).toPoint(),
        )
        frame(surface.window)

    def fill(self, surface, item, value):
        self.click(surface, item)
        QTest.keyClick(surface.window, Qt.Key_A, Qt.ControlModifier)
        for char in value:
            QTest.keyClick(surface.window, char)
        frame(surface.window)

    def test_hour_editor_input_reaches_original_work_hour_mutation(self):
        surface = self.open_surface("hourDialog")
        entry = _entry("hour-1", 2.5)
        entry.update_entry = Mock(return_value={})
        surface.controller._entries_by_task = {"TASK0001": [entry]}

        def mutate(operation, refresh):
            def finish():
                operation()
                surface.controller.entrySaved.emit()

            QTimer.singleShot(0, finish)

        surface.controller._mutate = mutate
        hours = self.item(surface, "workHourDuration")
        self.fill(surface, hours, "25")
        self.assertFalse(self.item(surface, "workHourApprove").property("enabled"))
        self.fill(surface, hours, "2.75")
        self.fill(
            surface, self.item(surface, "workHourDescription"), "Review completed"
        )
        approve = self.item(surface, "workHourApprove")
        self.assertTrue(approve.property("enabled"))
        self.click(surface, approve)
        entry.update_entry.assert_called_once_with(
            day="2026-10-14",
            category="regular",
            straight_time=2.75,
            description="Review completed",
            login="robin",
            approve=True,
        )
        self.assertFalse(surface.view.property("opened"))
        self.assertEqual(surface.warnings, [])

    def test_timesheet_real_selection_keeps_the_controller_owner(self):
        surface = self.open_surface("timesheet")
        selection = self.item(surface, "timesheetEntrySelect")
        self.click(surface, selection)
        self.assertEqual(surface.controller.selectedCount, 1)
        self.assertTrue(self.item(surface, "timesheetBulk-approve").isVisible())
        self.click(surface, self.item(surface, "timesheetBulk-clear"))
        self.assertEqual(surface.controller.selectedCount, 0)
        self.assertEqual(surface.warnings, [])

    def test_report_navigation_and_large_collection_stay_virtualized(self):
        surface = self.open_surface("reports")
        self.click(surface, self.item(surface, "workReport-approval"))
        self.assertEqual(surface.controller.selectedReport, "approval")
        surface.controller.report_values.replace(
            [
                dict(
                    label=f"Person {index:04d}",
                    value=index,
                    valueLabel=f"{index} h",
                    share=0.4,
                    secondary="",
                    accent="",
                )
                for index in range(1500)
            ]
        )
        surface.controller.stateChanged.emit()
        frame(surface.window)
        labels = [
            item
            for item in items(surface.view)
            if item.objectName() == "workReportValueLabel"
        ]
        self.assertLess(len(labels), 80)
        viewport = self.item(surface, "workReportValues")
        viewport.setProperty(
            "contentY", viewport.property("contentHeight") - viewport.height()
        )
        frame(surface.window)
        self.assertTrue(
            any(
                item.objectName() == "workReportValueLabel"
                and item.property("text") == "Person 1499"
                for item in items(surface.view)
            )
        )
        surface.view.setWidth(430)
        surface.window.resize(430, 650)
        frame(surface.window)
        choice = self.item(surface, "workReportChoice")
        self.assertTrue(choice.isVisible())
        surface.controller._permissions["viewCosts"] = False
        surface.controller.stateChanged.emit()
        frame(surface.window)
        options = choice.property("model")
        if hasattr(options, "toVariant"):
            options = options.toVariant()
        self.assertNotIn("labor_cost", [option["value"] for option in options])
        self.assertEqual(surface.warnings, [])

    def test_action_press_precedes_activation(self):
        surface = self.open_surface("format")
        meta = surface.view.metaObject()
        index = meta.indexOfSignal("event(QVariant,QVariant)")
        self.assertGreaterEqual(index, 0)
        observed = QSignalSpy(surface.view, meta.method(index))
        self.click(surface, self.item(surface, "knowledgeTextStyle"))
        actions = [
            observed.at(index)[0].toVariant() for index in range(observed.count())
        ]
        self.assertEqual(
            [action.get("pressed", False) for action in actions], [True, False]
        )

    def test_retained_knowledge_view_survives_reopen_and_scope_updates(self):
        surface = self.open_surface("reader")
        loader = self.item(surface, "knowledgeArticleLoader")
        original = loader.property("item")
        for cycle in range(48):
            surface.window.hide()
            surface.controller._document["title"] = f"Page {cycle}"
            surface.controller.stateChanged.emit()
            surface.window.show()
            frame(surface.window)
            self.assertIs(loader.property("item"), original)
            self.assertEqual(
                self.item(surface, "knowledgeViewerTitle").property("text"),
                f"Page {cycle}",
            )
        self.assertEqual(surface.warnings, [])


if __name__ == "__main__":
    unittest.main()

"""Real native pointer/touch input for the shared vertical section rail."""

import unittest
from contextlib import contextmanager

from PySide6.QtCore import QCoreApplication, QEvent, QObject, QPoint, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

import tests.test_section_tab_rail as fixture
from thlib.ui.workspace_models.sections import SectionTab


class FrameSectionInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture.SectionTabRailQmlTests.setUpClass()

    @contextmanager
    def scene(self):
        source = fixture.SectionTabRailQmlTests()
        engine, theme, model, component, rail, window = source._create_rail()
        warnings = []
        engine.warnings.connect(
            lambda errors: warnings.extend(error.toString() for error in errors)
        )
        selected, closed, reordered = [], [], []
        rail.selected.connect(selected.append)
        rail.closed.connect(closed.append)
        rail.reordered.connect(lambda first, last: reordered.append((first, last)))
        model.replace(
            [
                SectionTab(
                    str(index), "Section " + str(index), "#6f9fc1", index == 0, "assets"
                )
                for index in range(3)
            ]
        )
        neutral = QQuickItem(window.contentItem())
        neutral.forceActiveFocus()
        window.requestActivate()
        QTest.mouseMove(window, QPoint(850, 450))
        QTest.qWait(400)
        try:
            yield window, rail, selected, closed, reordered
            self.assertEqual(warnings, [])
        finally:
            window.close()
            window.deleteLater()
            engine.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def test_first_mouse_and_touch_select_exactly_once(self):
        with self.scene() as (window, rail, selected, closed, reordered):
            QTest.mouseClick(window, Qt.LeftButton, pos=QPoint(20, 28))
            self.assertEqual(selected, ["0"])
            device = QTest.createTouchDevice()
            point = QPoint(20, 73)
            QTest.touchEvent(window, device).press(0, point, window).commit()
            QTest.qWait(30)
            QTest.touchEvent(window, device).release(0, point, window).commit()
            QTest.qWait(40)
            self.assertEqual(selected, ["0", "1"])
            self.assertEqual(closed, [])
            self.assertEqual(reordered, [])

    def test_long_touch_opens_menu_without_selection(self):
        with self.scene() as (window, rail, selected, closed, reordered):
            device = QTest.createTouchDevice()
            point = QPoint(20, 73)
            QTest.touchEvent(window, device).press(0, point, window).commit()
            QTest.qWait(550)
            QTest.touchEvent(window, device).release(0, point, window).commit()
            QTest.qWait(80)
            menu = rail.findChild(QObject, "sectionTabActionsMenu")
            self.assertTrue(menu.property("opened"))
            self.assertEqual(selected, [])
            menu.close()

    def test_drag_to_middle_and_escape_cancel(self):
        with self.scene() as (window, rail, selected, closed, reordered):

            def drag_to(y):
                QTest.mouseMove(window, QPoint(20, 28))
                QTest.qWait(150)
                QTest.mousePress(window, Qt.LeftButton, pos=QPoint(90, 28))
                QTest.mouseMove(window, QPoint(90, 45), 30)
                QTest.mouseMove(window, QPoint(90, y), 30)
                QTest.qWait(40)

            drag_to(79)
            QTest.mouseRelease(window, Qt.LeftButton, pos=QPoint(90, 79))
            QTest.qWait(50)
            self.assertEqual(reordered, [(0, 1)])
            self.assertEqual(selected, [])
            drag_to(125)
            QTest.keyClick(window, Qt.Key_Escape)
            QTest.mouseRelease(window, Qt.LeftButton, pos=QPoint(90, 125))
            QTest.qWait(40)
            self.assertEqual(reordered, [(0, 1)])

    def test_context_actions_keep_selection_and_boundaries(self):
        with self.scene() as (window, rail, selected, closed, reordered):
            QTest.mouseClick(window, Qt.RightButton, pos=QPoint(20, 28))
            # Wait for the real popup's opened state, including at fractional DPI.
            menu = rail.findChild(QObject, "sectionTabActionsMenu")
            for _ in range(20):
                if menu.property("opened"):
                    break
                QTest.qWait(20)
            self.assertIsNotNone(menu)
            self.assertTrue(menu.property("opened"))
            actions = menu.property("actions")
            if hasattr(actions, "toVariant"):
                actions = actions.toVariant()
            actions = [action for action in actions if action.get("command")]
            self.assertFalse(actions[0]["enabled"])
            self.assertTrue(actions[1]["enabled"])
            self.assertEqual(selected, [])
            menu.close()
            QTest.qWait(200)
            window.requestActivate()
            QTest.qWait(30)
            source = fixture.SectionTabRailQmlTests._visual_children(
                rail, "sectionTabDelegate"
            )[0]
            source.forceActiveFocus()
            QTest.keyClick(window, Qt.Key_F10, Qt.ShiftModifier)
            for _ in range(20):
                if menu.property("opened"):
                    break
                QTest.qWait(20)
            self.assertTrue(menu.property("opened"))
            content = menu.property("contentItem")
            targets = fixture.SectionTabRailQmlTests._visual_children(
                content, "actionMenuPrimaryTarget"
            )
            target = next(
                item
                for item in targets
                if item.parentItem().property("modelData").toVariant().get("command")
                == "down"
            )
            QTest.qWait(20)
            self.assertTrue(target.hasActiveFocus())
            QTest.keyClick(target.window(), Qt.Key_Return)
            for _ in range(20):
                if reordered:
                    break
                QTest.qWait(20)
            self.assertEqual(reordered, [(0, 1)])
            self.assertEqual(selected, [])
            menu.close()


if __name__ == "__main__":
    unittest.main()

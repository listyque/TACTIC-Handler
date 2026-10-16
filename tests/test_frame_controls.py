"""Real house controls through the portable control catalog; no server or settings."""

import json
from pathlib import Path
import unittest

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    Qt,
    QUrl,
    QCoreApplication,
    QEvent,
    QPoint,
    QObject,
)
from PySide6.QtGui import QFont, QKeyEvent
from PySide6.QtQml import QQmlEngine, QQmlComponent, QQmlExpression
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
from thlib.ui.icon_font import qml_icon_bindings
from tests.qt_application import gui_test_application
from tests.profile_ui_responsiveness import frame
from tests import test_sidebar_editor_qml as sidebar_fixture

ROOT = Path(__file__).resolve().parents[1]


class Cells(QAbstractTableModel):
    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else 50

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else 3

    def roleNames(self):
        return {int(Qt.UserRole + 1): b"cell"}

    def data(self, index, role=Qt.DisplayRole):
        return {} if index.isValid() and role == Qt.UserRole + 1 else None


class FrameControlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()
        cls.app.setFont(QFont("Segoe UI", 10))
        QQuickWindow.setTextRenderType(QQuickWindow.NativeTextRendering)
        cls.icons = qml_icon_bindings(ROOT, cls.app)

    def setUp(self):
        self.engine = QQmlEngine()
        self.warnings = []
        self.engine.warnings.connect(
            lambda errors: self.warnings.extend(error.toString() for error in errors)
        )
        self.cells = Cells()
        context = self.engine.rootContext()
        context.setContextProperty("controlCells", self.cells)
        for name, value in self.icons.items():
            context.setContextProperty(name, value)
        self.component = QQmlComponent(
            self.engine,
            QUrl.fromLocalFile(str(ROOT / "tests/fixtures/FrameControlsHarness.qml")),
        )
        self.assertTrue(
            self.component.isReady(),
            [error.toString() for error in self.component.errors()],
        )
        self.window = self.component.create()
        self.assertIsNotNone(
            self.window, [error.toString() for error in self.component.errors()]
        )
        self.addCleanup(self.close)
        frame(self.window)

    def close(self):
        self.window.close()
        self.window.deleteLater()
        self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def evaluate(self, expression):
        call = QQmlExpression(self.engine.rootContext(), self.window, expression)
        result, undefined = call.evaluate()
        self.assertFalse(call.hasError(), call.error().toString())
        return result.toVariant() if hasattr(result, "toVariant") else result

    def item(self, name):
        return next(
            item
            for item in sidebar_fixture.SidebarEditorQmlTests.descendants(
                self.window.contentItem()
            )
            if item.objectName() == name
        )

    def scroll(self, offset):
        item = self.item("catalogScroll")
        item.setProperty(
            "contentY",
            min(offset, max(0, item.property("contentHeight") - item.height())),
        )
        frame(self.window)

    def model(self):
        return json.loads(self.evaluate("JSON.stringify(model)"))

    def test_all_controls_load_in_each_theme_language_state_and_width(self):
        for style in ("md3", "material5", "fluent"):
            self.window.setProperty("styleName", style)
            for dark in (True, False):
                self.window.setProperty("dark", dark)
                for language in ("en", "ru"):
                    self.window.setProperty("language", language)
                    for width in (900, 360):
                        self.window.resize(width, 900)
                        for state in (
                            "idle",
                            "disabled",
                            "readonly",
                            "error",
                            "loading",
                            "long",
                        ):
                            self.window.setProperty("status", state)
                            frame(self.window)
                            self.assertEqual(
                                self.item("field").property("enabled"),
                                state not in ("disabled", "loading"),
                            )
                            self.assertEqual(
                                self.item("field").property("font").pixelSize(), 13
                            )
                            self.assertEqual(
                                self.item("field").property("errorState"),
                                state == "error",
                            )
                            self.assertEqual(
                                self.warnings,
                                [],
                                (style, dark, language, width, state, self.warnings),
                            )

    def test_area_text_has_one_padding_and_reserves_the_scrollbar(self):
        area = self.item("area")
        editor = next(
            item
            for item in sidebar_fixture.SidebarEditorQmlTests.descendants(area)
            if "TextArea" in item.metaObject().className()
        )
        self.assertEqual(editor.mapToItem(area, 0, 0).y(), 0)
        self.assertEqual(editor.width(), area.width() - 12)
        self.assertEqual(editor.property("topPadding"), 10)
        self.window.setProperty("status", "error")
        frame(self.window)
        self.assertEqual(
            QQmlExpression(
                self.engine.rootContext(), area, "background.border.color.toString()"
            ).evaluate()[0],
            editor.property("theme").property("error").name(),
        )
        self.assertEqual(self.warnings, [])

    def test_button_hover_is_enabled_and_uses_the_shared_state(self):
        button = self.item("button")
        self.assertTrue(button.property("hoverEnabled"))
        QTest.mouseMove(self.window, QPoint(890, 890))
        QTest.mouseMove(
            self.window, button.mapToScene(button.boundingRect().center()).toPoint()
        )
        frame(self.window)
        self.assertTrue(button.property("hovered"))
        self.assertEqual(
            button.property("background").property("color"),
            button.property("theme").property("rowHover"),
        )
        self.assertEqual(self.warnings, [])

    def test_pointer_keyboard_and_disabled_actions(self):
        button = self.item("button")
        point = button.mapToScene(button.boundingRect().center()).toPoint()
        QTest.mouseClick(self.window, Qt.LeftButton, pos=point)
        frame(self.window)
        self.assertEqual(self.model()["events"][-1]["type"], "save")
        button.forceActiveFocus(Qt.TabFocusReason)
        QTest.keyClick(self.window, Qt.Key_Space)
        frame(self.window)
        self.assertEqual(len(self.model()["events"]), 2)
        self.window.setProperty("status", "disabled")
        frame(self.window)
        QTest.mouseClick(self.window, Qt.LeftButton, pos=point)
        frame(self.window)
        self.assertEqual(len(self.model()["events"]), 2)

    def test_native_calendar_rejects_rollover_and_trailing_input(self):
        for value in (
            "2023-02-29",
            "2024-02-30",
            "2024-13-01",
            "2024-02-29garbage",
            "2024-02-29T24:00",
        ):
            call = QQmlExpression(
                self.engine.rootContext(),
                self.item("date"),
                "parseValue(" + json.dumps(value) + ")===null",
            )
            result, _ = call.evaluate()
            self.assertFalse(call.hasError(), call.error().toString())
            self.assertTrue(result, value)
        self.assertEqual(self.warnings, [])

    def test_native_date_keeps_early_years_and_accepts_server_precision(self):
        date = self.item("date")
        for source in ("0099-02-28T13:14", "2024-02-29T13:14:15.123456+03:00"):
            expression = QQmlExpression(
                self.engine.rootContext(),
                date,
                "formattedValue(parseValue("
                + json.dumps(source)
                + ")).slice(0,10) === "
                + json.dumps(source[:10]),
            )
            result, _ = expression.evaluate()
            self.assertFalse(expression.hasError(), expression.error().toString())
            self.assertTrue(result, source)
        self.assertEqual(self.warnings, [])

    def test_mixed_checkbox_has_a_visible_mixed_mark(self):
        item = self.item("check")
        self.assertEqual(item.property("checkState"), Qt.PartiallyChecked)
        QTest.mouseClick(
            self.window,
            Qt.LeftButton,
            pos=item.mapToScene(item.boundingRect().center()).toPoint(),
        )
        frame(self.window)
        self.assertFalse(self.model()["mixed"])
        self.assertTrue(self.model()["checked"])
        self.assertEqual(self.model()["events"], [{"type": "checked", "value": True}])
        self.assertEqual(self.warnings, [])

    def test_searchable_user_choice_commits_from_the_native_popup_keyboard(self):
        chooser = self.item("user")
        point = chooser.mapToScene(chooser.boundingRect().center()).toPoint()
        QTest.mouseClick(self.window, Qt.LeftButton, pos=point)
        frame(self.window)
        expression = QQmlExpression(
            self.engine.rootContext(), chooser, "popup.contentItem"
        )
        content, _ = expression.evaluate()
        self.assertFalse(expression.hasError(), expression.error().toString())
        popup_window = content.window()
        self.assertTrue(popup_window.isVisible())
        popup_window.requestActivate()
        frame(popup_window)
        # Offscreen Popup.Window has no OS text-input route; use its real focused editor.
        target = popup_window.activeFocusItem()
        self.assertEqual(target.objectName(), "userComboBoxSearchField")
        for char in "test":
            for event_type in (QEvent.KeyPress, QEvent.KeyRelease):
                QCoreApplication.sendEvent(
                    target,
                    QKeyEvent(event_type, ord(char.upper()), Qt.NoModifier, char),
                )
        frame(popup_window)
        QTest.keyClick(popup_window, Qt.Key_Down)
        QTest.keyClick(popup_window, Qt.Key_Return)
        frame(self.window)
        self.assertEqual(self.model()["user"], "test")
        self.assertEqual(self.model()["events"][-1], {"type": "user", "value": "test"})
        self.assertFalse(popup_window.isVisible())
        self.assertEqual(self.warnings, [])

    def test_calendar_keyboard_crosses_leap_month_and_commits_once(self):
        calendar_button = self.item("dateFieldCalendarButton")
        point = calendar_button.mapToScene(
            calendar_button.boundingRect().center()
        ).toPoint()
        QTest.mouseClick(self.window, Qt.LeftButton, pos=point)
        frame(self.window)
        self.native_windows = self.app.allWindows()
        windows = [
            window
            for window in self.native_windows
            if window is not self.window
            and window.isVisible()
            and window.transientParent() is self.window
        ]
        self.assertEqual(len(windows), 1)
        popup_window = windows[0]
        content = popup_window.contentItem()
        day = next(
            item
            for item in sidebar_fixture.SidebarEditorQmlTests.descendants(content)
            if item.property("dayNumber") == 29
        )
        day.forceActiveFocus(Qt.TabFocusReason)
        QTest.keyClick(popup_window, Qt.Key_Right)
        frame(popup_window)
        self.assertEqual(popup_window.activeFocusItem().property("dayNumber"), 1)
        self.assertEqual(self.model()["date"], "2024-02-29T13:14")
        QTest.keyClick(popup_window, Qt.Key_Return)
        frame(self.window)
        self.assertEqual(self.model()["date"], "2024-03-01T13:14")
        self.assertEqual(
            [
                event
                for event in self.model()["events"]
                if event["type"] == "dateCommit"
            ],
            [{"type": "dateCommit", "value": "2024-03-01T13:14"}],
        )
        self.assertFalse(popup_window.isVisible())
        self.assertEqual(self.warnings, [])

    def test_composite_controls_expose_their_actual_keyboard_focus_target(self):
        for name in ("field", "date", "user", "color", "icon"):
            self.assertTrue(self.evaluate("focus(" + json.dumps(name) + ")"), name)
            frame(self.window)
            active = self.window.activeFocusItem()
            self.assertIsNotNone(active, name)
            control = self.item(name)
            while active and active is not control:
                active = active.parentItem()
            self.assertIs(active, control, name)
        self.assertEqual(self.warnings, [])

    def test_disabling_a_picker_owner_closes_its_native_window(self):
        for name in ("dateFieldCalendarButton", "user", "icon"):
            self.window.setProperty("status", "idle")
            frame(self.window)
            button = self.item(name)
            self.assertTrue(button.isEnabled(), name)
            QTest.mouseClick(
                self.window,
                Qt.LeftButton,
                pos=button.mapToScene(button.boundingRect().center()).toPoint(),
            )
            frame(self.window)
            for _ in range(20):
                self.native_windows = self.app.allWindows()
                popups = [
                    window
                    for window in self.native_windows
                    if window is not self.window and window.isVisible()
                ]
                if popups:
                    break
                QTest.qWait(20)
            self.assertEqual(len(popups), 1, name)
            self.window.setProperty("status", "disabled")
            frame(self.window)
            self.assertFalse(any(window.isVisible() for window in popups), name)
        self.assertEqual(self.warnings, [])

    def test_icon_library_keyboard_enters_grid_navigates_and_commits(self):
        self.assertTrue(self.evaluate('focus("icon")'))
        QTest.keyClick(self.window, Qt.Key_Space)
        frame(self.window)
        self.native_windows = self.app.allWindows()
        popup = next(
            window
            for window in self.native_windows
            if window is not self.window and window.isVisible()
        )
        QTest.keyClick(popup, Qt.Key_Down)
        frame(popup)
        self.assertEqual(popup.activeFocusItem().objectName(), "iconLibraryItem_0")
        QTest.keyClick(popup, Qt.Key_Right)
        frame(popup)
        self.assertEqual(popup.activeFocusItem().objectName(), "iconLibraryItem_1")
        label = popup.activeFocusItem().property("modelData")
        QTest.keyClick(popup, Qt.Key_Space)
        frame(self.window)
        self.assertEqual(self.model()["icon"], "material-design:" + label)
        self.assertFalse(popup.isVisible())
        self.assertEqual(self.warnings, [])

    def test_compact_icon_picker_accepts_keyboard_activation(self):
        self.assertTrue(self.evaluate('focus("icon")'))
        QTest.keyClick(self.window, Qt.Key_Space)
        frame(self.window)
        self.native_windows = self.app.allWindows()
        popups = [
            window
            for window in self.native_windows
            if window is not self.window and window.isVisible()
        ]
        self.assertEqual(len(popups), 1)
        QTest.keyClick(popups[0], Qt.Key_Escape)
        frame(self.window)
        self.assertFalse(popups[0].isVisible())
        self.assertEqual(self.warnings, [])


if __name__ == "__main__":
    unittest.main()

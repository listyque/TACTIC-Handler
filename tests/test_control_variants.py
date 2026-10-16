"""Real input into standalone reusable controls, without an application session."""

import json
from pathlib import Path
import unittest

from PySide6.QtCore import QCoreApplication, QEvent, QObject, QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QFont, QKeyEvent
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest

from tests.qt_application import gui_test_application
from tests.test_frame_controls import Cells
from tests import test_sidebar_editor_qml as sidebar_fixture
from thlib.ui.emoji import EmojiCatalog
from thlib.ui.icon_font import qml_icon_bindings
from thlib.ui.source_editor import SourceEditorService
from thlib.ui.workspace_models.records import RecordListModel

ROOT = Path(__file__).resolve().parents[1]


class ControlVariantsTests(unittest.TestCase):
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
        self.editor = SourceEditorService()
        self.emoji = EmojiCatalog(ROOT)
        roles = (
            "login",
            "displayName",
            "initials",
            "avatarUrl",
            "avatarColor",
            "groups",
            "primaryGroup",
            "current",
            "retired",
        )
        self.users = RecordListModel(roles)
        context = self.engine.rootContext()
        for name, value in dict(
            self.icons,
            controlCells=self.cells,
            sourceEditor=self.editor,
            userListModel=self.users,
            emojiCatalog=self.emoji,
        ).items():
            context.setContextProperty(name, value)
        self.component = QQmlComponent(
            self.engine,
            QUrl.fromLocalFile(
                str(ROOT / "tests/fixtures/frame_controls/ControlVariantsHarness.qml")
            ),
        )
        self.assertTrue(
            self.component.isReady(),
            [error.toString() for error in self.component.errors()],
        )
        self.window = self.component.create()
        self.assertIsNotNone(
            self.window, [error.toString() for error in self.component.errors()]
        )
        self.users.replace(json.loads(self.evaluate("userRecordsJson()")))
        self.addCleanup(self.close)
        QTest.qWait(20)

    def close(self):
        self.window.close()
        self.window.deleteLater()
        self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def evaluate(self, source):
        expression = QQmlExpression(self.engine.rootContext(), self.window, source)
        result, _ = expression.evaluate()
        self.assertFalse(expression.hasError(), expression.error().toString())
        return result.toVariant() if hasattr(result, "toVariant") else result

    def configure(self, name, state="idle"):
        QTest.keyClick(self.window, Qt.Key_Escape)
        self.warnings.clear()
        self.evaluate(f"configure({json.dumps(name)}, {json.dumps(state)})")
        QTest.qWait(20)
        self.assertFalse(
            [
                warning
                for warning in self.warnings
                if not (name == "preview-broken" and "missing-example.png" in warning)
            ],
            self.warnings,
        )

    def model(self):
        return json.loads(self.evaluate("modelJson()"))

    def item(self, name):
        return next(
            item
            for item in sidebar_fixture.SidebarEditorQmlTests.descendants(
                self.window.contentItem()
            )
            if item.objectName() == name
        )

    def click(self, item, x=None, y=None):
        point = item.mapToScene(
            QPointF(
                item.width() / 2 if x is None else x,
                item.height() / 2 if y is None else y,
            )
        ).toPoint()
        QTest.mouseClick(self.window, Qt.LeftButton, pos=point)
        QTest.qWait(20)

    def edit(self, item, text):
        item.forceActiveFocus()
        QTest.keyClick(self.window, Qt.Key_A, Qt.ControlModifier)
        for character in text:
            QTest.keyClick(self.window, character)
        QTest.keyClick(self.window, Qt.Key_Return)
        QTest.qWait(20)

    def test_segment_keys_skip_disabled_options_and_keep_one_tab_stop(self):
        self.configure("segments-disabled-option")
        self.item("segmentedButtonSegment_model").forceActiveFocus()
        QTest.keyClick(self.window, Qt.Key_Right)
        self.assertEqual(self.model()["value"], "publish")
        QTest.keyClick(self.window, Qt.Key_Right)
        self.assertEqual(self.model()["value"], "model")
        QTest.keyClick(self.window, Qt.Key_End)
        self.assertEqual(self.model()["value"], "publish")
        QTest.keyClick(self.window, Qt.Key_Home)
        self.assertEqual(self.model()["value"], "model")
        self.assertEqual(len(self.model()["events"]), 4)
        self.assertFalse(self.item("segmentedButtonSegment_rig").property("enabled"))

    def test_spin_keyboard_text_limits_and_readonly(self):
        self.configure("integer")
        field = self.item("spinBoxTextInput")
        field.forceActiveFocus()
        QTest.keyClick(self.window, Qt.Key_Up)
        self.assertEqual(self.model()["value"], 6)
        self.edit(field, "9")
        self.assertEqual(self.model()["value"], 9)
        self.assertEqual(len(self.model()["events"]), 2)
        QTest.keyClick(self.window, Qt.Key_Up)
        QTest.keyClick(self.window, Qt.Key_Up)
        self.assertEqual(self.model()["value"], 10)
        self.assertEqual(len(self.model()["events"]), 3)
        self.window.setProperty("status", "readonly")
        QTest.keyClick(self.window, Qt.Key_Down)
        self.assertEqual(self.model()["value"], 10)
        self.assertTrue(field.property("readOnly"))

    def test_slider_drag_and_disabled(self):
        self.configure("slider-step")
        slider = self.item("exampleControl")
        self.click(slider, slider.width() * 0.8)
        self.assertGreater(self.model()["value"], 50)
        self.assertEqual(self.model()["value"] % 5, 0)
        before = self.model()
        self.window.setProperty("status", "disabled")
        self.click(slider, slider.width() * 0.2)
        self.assertEqual(self.model(), before)
        self.configure("slider-fixed")
        self.click(self.item("exampleControl"))
        self.assertEqual(self.model()["value"], 5)

    def test_search_suggestions_keyboard_accept_clear_and_dismiss(self):
        self.configure("search-suggestions")
        field = self.item("exampleControl")
        field.forceActiveFocus()
        QTest.qWait(30)
        self.assertTrue(field.property("popupOpen"))
        QTest.keyClick(self.window, Qt.Key_Down)
        QTest.keyClick(self.window, Qt.Key_Return)
        self.assertEqual(self.model()["value"], "Robot Arm")
        self.assertEqual(len(self.model()["events"]), 1)
        self.assertFalse(field.property("popupOpen"))
        self.click(self.item("searchFieldClear"))
        self.assertEqual(self.model()["value"], "")
        QTest.keyClick(self.window, Qt.Key_Escape)
        self.assertEqual(self.model()["events"][-1]["type"], "dismiss")

    def test_retry_and_preview_buttons_activate_from_keyboard(self):
        self.configure("error-retry")
        buttons = [
            item
            for item in sidebar_fixture.SidebarEditorQmlTests.descendants(
                self.item("exampleControl")
            )
            if item.property("text") == "Retry" and item.property("enabled") is not None
        ]
        self.assertTrue(buttons)
        buttons[0].forceActiveFocus()
        QTest.keyClick(self.window, Qt.Key_Space)
        self.assertEqual(self.model()["events"][-1]["type"], "retry")

    def test_live_disabled_search_closes_its_popup_without_an_action(self):
        self.configure("search-suggestions")
        self.item("exampleControl").forceActiveFocus()
        QTest.qWait(30)
        self.assertTrue(self.item("exampleControl").property("popupOpen"))
        before = self.model()
        self.window.setProperty("status", "disabled")
        QTest.qWait(20)
        self.assertFalse(self.item("exampleControl").property("popupOpen"))
        QTest.keyClick(self.window, Qt.Key_Return)
        self.assertEqual(self.model(), before)

    def test_every_example_can_be_destroyed_and_recreated_without_warnings(self):
        examples = json.loads(self.evaluate("examplesJson()"))
        for state in ("idle", "disabled", "readonly"):
            for example in examples:
                self.configure(example["id"], state)
                unexpected = [
                    warning
                    for warning in self.warnings
                    if not (
                        example["id"] == "preview-broken"
                        and "missing-example.png" in warning
                    )
                ]
                self.assertFalse(unexpected, (example["id"], state, unexpected))

    def test_spin_keeps_external_value_binding_after_mouse_and_text_edits(self):
        self.configure("integer")
        spin = self.item("exampleControl")
        self.click(spin, spin.width() - 17)
        self.assertEqual(self.model()["value"], 6)
        self.assertEqual(len(self.model()["events"]), 1)
        self.evaluate("model = Object.assign({}, model, {value:2})")
        self.assertEqual(spin.property("realValue"), 2)
        self.edit(self.item("spinBoxTextInput"), "7")
        self.assertEqual(self.model()["value"], 7)
        self.evaluate("model = Object.assign({}, model, {value:3})")
        self.assertEqual(spin.property("realValue"), 3)
        self.assertEqual(self.item("spinBoxTextInput").property("text"), "3")

    def test_decimal_language_changes_without_losing_the_numeric_value(self):
        self.configure("decimal")
        self.edit(self.item("spinBoxTextInput"), "2.5")
        self.assertEqual(self.model()["value"], 2.5)
        self.window.setProperty("language", "ru")
        self.assertEqual(self.item("spinBoxTextInput").property("text"), "2,5")
        self.assertEqual(self.model()["value"], 2.5)
        self.edit(self.item("spinBoxTextInput"), "1,25")
        self.assertEqual(self.model()["value"], 1.25)

    def test_disclosure_preview_and_preset_are_keyboard_actions(self):
        self.configure("button-disclosure")
        self.item("exampleControl").forceActiveFocus()
        QTest.keyClick(self.window, Qt.Key_Space)
        self.assertEqual(self.model()["value"], True)
        self.configure("button-preview")
        self.item("previewNavigationAction").forceActiveFocus()
        QTest.keyClick(self.window, Qt.Key_Return)
        QTest.qWait(20)
        self.assertEqual(len(self.model()["events"]), 1)
        self.configure("accent-presets")
        choices = [
            item
            for item in sidebar_fixture.SidebarEditorQmlTests.descendants(
                self.item("exampleControl")
            )
            if item.property("_pendingActivationKey") is not None
        ]
        self.assertEqual(len(choices), 2)
        choices[1].forceActiveFocus()
        QTest.keyClick(self.window, Qt.Key_Space)
        QTest.qWait(20)
        self.assertEqual(self.model()["value"], "green")

    def test_repeated_key_release_does_not_repeat_an_action(self):
        self.configure("button-preview")
        action = self.item("previewNavigationAction")
        action.forceActiveFocus()
        QTest.keyPress(self.window, Qt.Key_Space)
        for _ in range(3):
            QCoreApplication.sendEvent(
                self.window,
                QKeyEvent(QEvent.KeyRelease, Qt.Key_Space, Qt.NoModifier, " ", True, 1),
            )
            QCoreApplication.sendEvent(
                self.window,
                QKeyEvent(QEvent.KeyPress, Qt.Key_Space, Qt.NoModifier, " ", True, 1),
            )
            QTest.qWait(20)
        QTest.keyRelease(self.window, Qt.Key_Space)
        QTest.qWait(20)
        self.assertEqual(len(self.model()["events"]), 1)

    def test_disclosure_ignores_repeated_releases_of_one_space_press(self):
        self.configure("button-disclosure")
        action = self.item("exampleControl")
        action.forceActiveFocus()
        QTest.keyPress(self.window, Qt.Key_Space)
        for _ in range(3):
            QCoreApplication.sendEvent(
                self.window,
                QKeyEvent(QEvent.KeyRelease, Qt.Key_Space, Qt.NoModifier, " ", True, 1),
            )
            QCoreApplication.sendEvent(
                self.window,
                QKeyEvent(QEvent.KeyPress, Qt.Key_Space, Qt.NoModifier, " ", True, 1),
            )
            QTest.qWait(20)
        QTest.keyRelease(self.window, Qt.Key_Space)
        self.assertEqual(len(self.model()["events"]), 1)

    def test_choices_skip_disabled_options_for_keyboard_input(self):
        self.configure("choice-disabled-option")
        combo = self.item("sample")
        combo.forceActiveFocus()
        QTest.keyClick(self.window, Qt.Key_Down)
        self.assertEqual(self.model()["value"], "publish")
        self.assertEqual(len(self.model()["events"]), 1)
        QTest.keyClick(self.window, Qt.Key_Up)
        self.assertEqual(self.model()["value"], "model")

    def test_packed_choice_widths_include_the_hidden_sizing_labels(self):
        self.configure("packed-choices")
        chips = [
            item
            for item in sidebar_fixture.SidebarEditorQmlTests.descendants(
                self.window.contentItem()
            )
            if item.objectName() == "quickFilterOption"
        ]
        self.assertGreater(len(chips), 5)
        self.assertLess(len(chips), 80, "Only visible rows own controls")
        self.assertTrue(
            all(chip.width() > 90 for chip in chips), [chip.width() for chip in chips]
        )
        self.click(chips[1])
        self.assertEqual(self.model()["value"], "1")
        self.window.setWidth(900)
        QTest.qWait(30)
        self.assertEqual(self.model()["value"], "1")

    def test_dates_display_the_fixture_value_and_preserve_early_years(self):
        self.configure("date")
        self.assertEqual(self.item("sample").property("text"), "2024-02-29")
        self.assertEqual(
            self.item("sample").property("presentationText"), "29 February 2024"
        )
        self.configure("date-early-year")
        self.window.setProperty("language", "ru")
        self.assertEqual(
            self.item("sample").property("presentationText"), "1 января 0099"
        )
        self.configure("date-invalid")
        self.assertFalse(self.item("sample").property("acceptableInput"))
        self.configure("date-empty")
        self.assertEqual(
            self.item("dateFieldTextInput").property("placeholderText"), "YYYY-MM-DD"
        )

    def test_grid_draft_survives_resize_and_readonly_recreation(self):
        self.configure("table")
        field = self.item("cell_0_0")
        self.edit(field, "Edited cell")
        self.assertEqual(self.model()["cells"]["0:0"], "Edited cell")
        self.window.setWidth(900)
        QTest.qWait(30)
        self.assertEqual(self.item("cell_0_0").property("text"), "Edited cell")
        self.configure("table-readonly")
        self.assertTrue(self.item("cell_0_0").property("readOnly"))

    def test_graph_selection_and_move_publish_to_the_common_model(self):
        self.configure("graph")
        node = self.item("graphNode_a")
        self.click(node)
        self.assertEqual(self.model()["graphSelected"], ["a"])
        point = node.mapToScene(node.boundingRect().center()).toPoint()
        QTest.mousePress(self.window, Qt.LeftButton, pos=point)
        QTest.mouseMove(self.window, point + QPoint(30, 20), delay=30)
        QTest.mouseRelease(self.window, Qt.LeftButton, pos=point + QPoint(30, 20))
        QTest.qWait(30)
        self.assertTrue(
            any(
                position["identity"] == "a" and position["nodeX"] != 20
                for position in self.model()["graphPositions"]
            )
        )

    def test_splitter_keyboard_changes_the_common_value(self):
        self.configure("splitter-vertical")
        self.item("sample").forceActiveFocus()
        QTest.keyClick(self.window, Qt.Key_Right)
        self.assertGreater(self.model()["value"], 50)


if __name__ == "__main__":
    unittest.main()

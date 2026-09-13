"""Exercise popup motion through real controls, including Qt style transitions."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Material")

from PySide6.QtCore import QEvent, QObject, QPoint, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication

from thlib.environment import env_mode, env_write_config
from thlib.ui.controller import ApplicationController


QML = Path(__file__).resolve().parents[1] / "thlib/ui/qml"


class PopupAnimationPreferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.engine = QQmlEngine()
        self.warnings = []
        self.engine.warnings.connect(lambda warnings: self.warnings.extend(
            warning.toString() for warning in warnings
        ))
        self.component = QQmlComponent(self.engine)
        self.component.setData(b'''import QtQuick
import QtQuick.Controls
import QtQuick.Window
import "." as App
import "controls" as Controls
Window {
    id: window
    width: 720; height: 540; visible: true
    property string popupKind: "menu"
    property var preferencesController: null
    property var testedPopup: popupKind === "menu" ? menu
        : popupKind === "combo" ? combo.popup
        : popupKind === "projects" ? projects : panel
    App.Theme {
        id: theme; objectName: "testTheme"; dark: true
        popupAnimationsEnabled: window.preferencesController
            ? window.preferencesController.popup_animations_enabled : true
    }
    Controls.Button {
        x: 20; y: 20; width: 140; height: 40
        theme: theme; text: "Open"
        onClicked: window.testedPopup.open()
    }
    MouseArea {
        x: 400; y: 20; width: 140; height: 40
        acceptedButtons: Qt.RightButton
        onClicked: mouse => menu.openAt(this, mouse.x, mouse.y)
    }
    App.ActionMenu {
        id: menu; parent: window.contentItem; theme: theme
        x: 20; y: 70
        actions: [{"title": "Open", "command": "open"}]
    }
    Controls.Popup {
        id: panel; parent: window.contentItem; theme: theme
        x: 20; y: 70; width: 240; height: 160
        usePopupWindow: false; modal: true; dim: true
    }
    Controls.ComboBox {
        id: combo; x: 200; y: 20; theme: theme
        model: ["First", "Second"]
    }
    App.ProjectChooser {
        id: projects; theme: theme
        model: ({groups: [], visibleCount: 0, totalCount: 0,
            retiredCount: 0, templateCount: 0, builtinCount: 0,
            showRetired: false, showTemplates: false, showBuiltins: false})
    }
    Controls.ToolTip {
        objectName: "motionTooltip"
        theme: theme; text: "Hint"; delay: 0; timeout: -1
    }
}
''', QUrl.fromLocalFile(str(QML / "_PopupMotionTest.qml")))
        self.window = self.component.create()
        self.assertIsNotNone(self.window, "\n".join(
            error.toString() for error in self.component.errors()
        ))
        self.addCleanup(self.dispose)
        self.assertTrue(QTest.qWaitForWindowExposed(self.window))
        self.theme = self.window.findChild(QObject, "testTheme")

    def dispose(self):
        self.window.close()
        self.window.deleteLater()
        self.app.sendPostedEvents(None, QEvent.DeferredDelete)
        self.engine.deleteLater()
        self.app.sendPostedEvents(None, QEvent.DeferredDelete)
        self.assertEqual(self.warnings, [])

    def test_popups_open_and_close_without_transitions_when_disabled(self):
        self.theme.setProperty("popupAnimationsEnabled", False)
        for kind in ("menu", "panel", "combo", "projects"):
            with self.subTest(kind=kind):
                self.window.setProperty("popupKind", kind)
                popup = self.window.property("testedPopup")
                opened = QSignalSpy(popup.opened)
                closed = QSignalSpy(popup.closed)
                QTest.mouseClick(self.window, Qt.LeftButton, pos=QPoint(70, 40))
                self.assertEqual(opened.count(), 1, kind)
                self.assertEqual(popup.property("opacity"), 1)
                self.assertAlmostEqual(popup.property("scale"), 1)
                popup.close()
                self.assertEqual(closed.count(), 1, kind)
                self.assertFalse(popup.property("visible"))

    def test_reenabling_restores_motion_and_process_menu_stays_instant(self):
        self.theme.setProperty("popupAnimationsEnabled", False)
        self.theme.setProperty("popupAnimationsEnabled", True)
        popup = self.window.property("testedPopup")
        opened = QSignalSpy(popup.opened)
        closed = QSignalSpy(popup.closed)
        QTest.mouseClick(self.window, Qt.LeftButton, pos=QPoint(70, 40))
        self.assertEqual(opened.count(), 0)
        self.assertTrue(opened.wait(1000))
        popup.close()
        self.assertEqual(closed.count(), 0)
        self.assertTrue(closed.wait(1000))
        self.theme.setProperty("popupAnimationsEnabled", False)
        QTest.mouseClick(self.window, Qt.LeftButton, pos=QPoint(70, 40))
        self.assertEqual(opened.count(), 2)
        self.assertEqual(popup.property("opacity"), 1)
        self.assertAlmostEqual(popup.property("scale"), 1)
        popup.close()
        self.assertEqual(closed.count(), 2)
        self.theme.setProperty("popupAnimationsEnabled", True)
        popup.setProperty("processPickerStyle", True)
        QTest.mouseClick(self.window, Qt.LeftButton, pos=QPoint(70, 40))
        self.assertEqual(opened.count(), 3)
        popup.close()
        self.assertEqual(closed.count(), 3)

    def test_tooltip_uses_popup_preference_not_content_fades(self):
        self.theme.setProperty("popupAnimationsEnabled", False)
        self.assertTrue(self.theme.property("fadeAnimationsEnabled"))
        loader = self.window.findChild(QObject, "motionTooltip")
        loader.setProperty("visible", True)
        tooltip = loader.property("item")
        opened = QSignalSpy(tooltip.opened)
        closed = QSignalSpy(tooltip.closed)
        self.app.processEvents()
        self.assertEqual(opened.count(), 1)
        self.assertEqual(tooltip.property("opacity"), 1)
        tooltip.close()
        self.assertEqual(closed.count(), 1)

    def test_setting_round_trip_and_runtime_reads_do_not_touch_disk(self):
        with TemporaryDirectory() as directory, patch.object(
            env_mode, "current_path", directory,
        ):
            controller = ApplicationController()
            try:
                values = controller.configuration_appearance_values()
                self.assertTrue(values["popupAnimations"])
                values["popupAnimations"] = False
                changed = QSignalSpy(controller.animation_preferences_changed)
                controller.apply_appearance_configuration(values)
                self.assertEqual(changed.count(), 1)
                self.assertFalse(controller.popup_animations_enabled)
            finally:
                controller.shutdown()
            restored = ApplicationController()
            try:
                self.assertFalse(restored.popup_animations_enabled)
                self.assertTrue(restored.fade_animations_enabled)
                with patch("thlib.ui.controller.env_read_config") as read:
                    for _ in range(100):
                        self.assertFalse(restored.popup_animations_enabled)
                    read.assert_not_called()
            finally:
                restored.shutdown()

    def test_apply_updates_existing_right_click_menu_without_recreating_ui(self):
        with TemporaryDirectory() as directory, patch.object(
            env_mode, "current_path", directory,
        ):
            controller = ApplicationController()
            self.window.setProperty("preferencesController", controller)
            try:
                values = controller.configuration_appearance_values()
                values["popupAnimations"] = False
                controller.apply_appearance_configuration(values)
                self.assertFalse(self.theme.property("popupAnimationsEnabled"))
                popup = self.window.property("testedPopup")
                opened = QSignalSpy(popup.opened)
                QTest.mouseClick(self.window, Qt.RightButton, pos=QPoint(450, 40))
                self.assertEqual(opened.count(), 1)
                self.assertAlmostEqual(popup.property("opacity"), 1)
                self.assertAlmostEqual(popup.property("scale"), 1)
                closed = QSignalSpy(popup.closed)
                popup.close()
                self.assertEqual(closed.count(), 1)
            finally:
                self.window.setProperty("preferencesController", None)
                controller.shutdown()

    def test_unset_popup_preference_respects_disabled_fades_then_is_independent(self):
        with TemporaryDirectory() as directory, patch.object(
            env_mode, "current_path", directory,
        ):
            env_write_config(
                {"appearance/fadeAnimations": False},
                filename="ui_settings", unique_id="ui_main", long_abs_path=True,
            )
            controller = ApplicationController()
            try:
                self.assertFalse(controller.popup_animations_enabled)
                values = controller.configuration_appearance_values()
                values["popupAnimations"] = True
                controller.apply_appearance_configuration(values)
                self.assertTrue(controller.popup_animations_enabled)
                self.assertFalse(controller.fade_animations_enabled)
            finally:
                controller.shutdown()
            restored = ApplicationController()
            try:
                self.assertTrue(restored.popup_animations_enabled)
                self.assertFalse(restored.fade_animations_enabled)
            finally:
                restored.shutdown()


if __name__ == "__main__":
    unittest.main()

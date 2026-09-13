import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtTest import QTest


ROOT = Path(__file__).parents[1]
QML = ROOT / "thlib" / "ui" / "qml"


class TouchControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def test_activation_handler_delivers_one_tap_and_yields_to_touch_scroll(self):
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Window
import "controls" as Controls

Window {
    id: window
    width: 260
    height: 220
    visible: true
    property int activationCount: 0
    property alias scrollY: flick.contentY

    Flickable {
        id: flick
        anchors.fill: parent
        contentWidth: width
        contentHeight: 700
        boundsBehavior: Flickable.StopAtBounds

        Rectangle {
            x: 30
            y: 40
            width: 180
            height: 90
            color: "transparent"

            Controls.ActivationHandler {
                onActivated: window.activationCount += 1
            }
        }
    }
}
''',
            QUrl.fromLocalFile(str(QML / "_TouchActivationTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(40)
            device = QTest.createTouchDevice()
            tap_point = QPoint(100, 75)

            tap = QTest.touchEvent(owner, device, autoCommit=False)
            tap.press(0, tap_point, owner).commit()
            QTest.qWait(20)
            tap.release(0, tap_point, owner).commit()
            QTest.qWait(60)
            self.assertEqual(owner.property("activationCount"), 1)

            QTest.qWait(190)
            QTest.mouseClick(owner, Qt.RightButton, Qt.NoModifier, tap_point)
            self.assertEqual(owner.property("activationCount"), 1)

            QTest.qWait(190)
            QTest.mouseClick(owner, Qt.LeftButton, Qt.NoModifier, tap_point)
            self.assertEqual(owner.property("activationCount"), 2)

            QTest.qWait(190)
            drag = QTest.touchEvent(owner, device, autoCommit=False)
            drag.press(0, QPoint(100, 90), owner).commit()
            QTest.qWait(20)
            drag.move(0, QPoint(100, 55), owner).commit()
            QTest.qWait(20)
            drag.move(0, QPoint(100, 20), owner).commit()
            QTest.qWait(20)
            drag.release(0, QPoint(100, 20), owner).commit()
            QTest.qWait(120)
            self.assertEqual(owner.property("activationCount"), 2)
            self.assertGreater(owner.property("scrollY"), 0)
        finally:
            owner.close()
            owner.deleteLater()

    def test_dock_level_press_observer_does_not_consume_button_touch(self):
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Window
import "controls" as Controls

Window {
    id: window
    width: 260
    height: 180
    visible: true
    property int activationCount: 0

    Theme {
        id: theme
        dark: true
    }

    TapHandler {
        target: null
        acceptedButtons: Qt.AllButtons
        gesturePolicy: TapHandler.DragThreshold
    }

    Controls.Button {
        x: 40
        y: 50
        width: 180
        theme: theme
        text: "Open"
        onClicked: window.activationCount += 1
    }
}
''',
            QUrl.fromLocalFile(str(QML / "_DockTouchButtonTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(40)
            device = QTest.createTouchDevice()
            touch_point = QPoint(130, 70)
            tap = QTest.touchEvent(owner, device, autoCommit=False)
            tap.press(0, touch_point, owner).commit()
            QTest.qWait(20)
            tap.release(0, touch_point, owner).commit()
            QTest.qWait(60)
            self.assertEqual(owner.property("activationCount"), 1)
        finally:
            owner.close()
            owner.deleteLater()

    def test_common_action_controls_accept_authentic_touch_events(self):
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Window
import "controls" as Controls

Window {
    id: window
    width: 320
    height: 300
    visible: true
    property int buttonCount: 0
    property int iconCount: 0
    property int filledCount: 0
    readonly property bool comboOpened: combo.popup.opened
    property alias switchChecked: toggle.checked

    Theme {
        id: theme
        dark: true
        popupAnimationsEnabled: false
    }

    Controls.Button {
        x: 40
        y: 20
        width: 240
        theme: theme
        text: "Button"
        onClicked: window.buttonCount += 1
    }
    Controls.CompactIconButton {
        x: 40
        y: 75
        width: 44
        height: 44
        theme: theme
        iconName: "add"
        onClicked: window.iconCount += 1
    }
    Controls.FilledActionButton {
        x: 105
        y: 75
        width: 175
        theme: theme
        text: "Filled"
        onClicked: window.filledCount += 1
    }
    Controls.ComboBox {
        id: combo
        x: 40
        y: 140
        width: 240
        theme: theme
        model: ["One", "Two"]
    }
    Controls.Switch {
        id: toggle
        x: 40
        y: 205
        width: 240
        theme: theme
        text: "Toggle"
    }
}
''',
            QUrl.fromLocalFile(str(QML / "_CommonTouchControlsTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )

        def tap_at(device, point):
            tap = QTest.touchEvent(owner, device, autoCommit=False)
            tap.press(0, point, owner).commit()
            QTest.qWait(20)
            tap.release(0, point, owner).commit()
            QTest.qWait(60)

        try:
            QTest.qWait(40)
            device = QTest.createTouchDevice()
            tap_at(device, QPoint(160, 38))
            tap_at(device, QPoint(62, 97))
            tap_at(device, QPoint(190, 97))
            tap_at(device, QPoint(160, 225))
            tap_at(device, QPoint(160, 156))
            self.assertTrue(owner.property("comboOpened"))

            self.assertEqual(owner.property("buttonCount"), 1)
            self.assertEqual(owner.property("iconCount"), 1)
            self.assertEqual(owner.property("filledCount"), 1)
            self.assertTrue(owner.property("switchChecked"))
        finally:
            owner.close()
            owner.deleteLater()

    def test_touch_moves_between_neighbor_native_combo_popups(self):
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Window
import "controls" as Controls

Window {
    id: window
    width: 520
    height: 220
    visible: true
    readonly property bool firstOpened: first.popup.opened
    readonly property bool secondOpened: second.popup.opened

    Theme { id: theme; dark: true; popupAnimationsEnabled: false }
    Controls.ComboBox {
        id: first
        x: 40
        y: 40
        width: 180
        theme: theme
        model: ["One", "Two"]
    }
    Controls.ComboBox {
        id: second
        x: 280
        y: 40
        width: 180
        theme: theme
        model: ["Alpha", "Beta"]
    }
}
''',
            QUrl.fromLocalFile(str(QML / "_TouchNeighborComboTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )

        def tap_at(device, point):
            tap = QTest.touchEvent(owner, device, autoCommit=False)
            tap.press(0, point, owner).commit()
            QTest.qWait(20)
            tap.release(0, point, owner).commit()
            QTest.qWait(80)

        try:
            QTest.qWait(40)
            device = QTest.createTouchDevice()
            tap_at(device, QPoint(100, 55))
            self.assertTrue(owner.property("firstOpened"))
            QTest.qWait(520)
            popup_windows = [
                window
                for window in QGuiApplication.allWindows()
                if window is not owner
                and window.isVisible()
                and window.transientParent() is owner
            ]
            self.assertEqual(len(popup_windows), 1)
            popup_window = popup_windows[0]
            second_global = owner.mapToGlobal(QPoint(340, 55))
            second_in_popup = QPoint(
                second_global.x() - popup_window.x(),
                second_global.y() - popup_window.y(),
            )
            popup_tap = QTest.touchEvent(
                popup_window, device, autoCommit=False
            )
            popup_tap.press(0, second_in_popup, popup_window).commit()
            QTest.qWait(20)
            popup_tap.release(0, second_in_popup, popup_window).commit()
            QTest.qWait(80)
            self.assertFalse(owner.property("firstOpened"))

            tap_at(device, QPoint(340, 55))
            self.assertTrue(owner.property("secondOpened"))
        finally:
            owner.close()
            owner.deleteLater()

    def test_delayed_synthetic_mouse_press_does_not_close_touched_combo(self):
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Window
import "controls" as Controls

Window {
    id: window
    width: 420
    height: 220
    visible: true
    readonly property bool comboOpened: combo.popup.opened

    Theme { id: theme; dark: true; popupAnimationsEnabled: false }
    Controls.ComboBox {
        id: combo
        x: 40
        y: 40
        width: 220
        theme: theme
        model: ["One", "Two"]
    }
}
''',
            QUrl.fromLocalFile(str(QML / "_TouchComboOpenGuardTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(40)
            device = QTest.createTouchDevice()
            touch_point = QPoint(140, 56)
            tap = QTest.touchEvent(owner, device, autoCommit=False)
            tap.press(0, touch_point, owner).commit()
            QTest.qWait(20)
            tap.release(0, touch_point, owner).commit()
            QTest.qWait(40)
            self.assertTrue(owner.property("comboOpened"))

            # Real Windows touchscreens may synthesize a mouse click at the
            # original control after the authentic touch has already opened
            # its popup.
            QTest.mouseClick(
                owner, Qt.LeftButton, Qt.NoModifier, touch_point
            )
            QTest.qWait(40)
            self.assertTrue(owner.property("comboOpened"))

            QTest.qWait(500)
            QTest.mouseClick(
                owner, Qt.LeftButton, Qt.NoModifier, QPoint(380, 190)
            )
            QTest.qWait(60)
            self.assertFalse(owner.property("comboOpened"))
        finally:
            owner.close()
            owner.deleteLater()

    def test_touch_opens_action_menu_and_activates_its_item(self):
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Window
import "controls" as Controls

Window {
    id: window
    width: 360
    height: 240
    visible: true
    property string triggeredCommand: ""
    readonly property bool menuOpened: menu.opened

    Theme { id: theme; dark: true; popupAnimationsEnabled: false }
    Controls.CompactIconButton {
        id: menuButton
        x: 40
        y: 40
        width: 48
        height: 48
        theme: theme
        iconName: "more_vert"
        onClicked: menu.openBelow(menuButton)
    }
    ActionMenu {
        id: menu
        objectName: "touchActionMenu"
        parent: window.contentItem
        theme: theme
        actions: [
            {"title": "Open", "icon": "open_in_new", "command": "open"}
        ]
        onTriggered: command => window.triggeredCommand = command
    }
}
''',
            QUrl.fromLocalFile(str(QML / "_TouchActionMenuTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(50)
            device = QTest.createTouchDevice()
            opening_tap = QTest.touchEvent(
                owner, device, autoCommit=False
            )
            opening_tap.press(0, QPoint(64, 64), owner).commit()
            QTest.qWait(20)
            opening_tap.release(0, QPoint(64, 64), owner).commit()
            QTest.qWait(100)
            self.assertTrue(owner.property("menuOpened"))

            # Simulate a delayed synthesized click after the activation
            # handler's ordinary duplicate window has already elapsed.
            QTest.qWait(100)
            QTest.mouseClick(
                owner, Qt.LeftButton, Qt.NoModifier, QPoint(64, 64)
            )
            QTest.qWait(40)
            self.assertTrue(owner.property("menuOpened"))

            popup_window = next(
                window
                for window in QGuiApplication.allWindows()
                if window is not owner
                and window.isVisible()
                and window.transientParent() is owner
            )
            action_point = QPoint(
                popup_window.width() // 2,
                popup_window.height() // 2,
            )
            action_tap = QTest.touchEvent(
                popup_window, device, autoCommit=False
            )
            action_tap.press(0, action_point, popup_window).commit()
            QTest.qWait(20)
            action_tap.release(0, action_point, popup_window).commit()
            QTest.qWait(100)
            self.assertEqual(owner.property("triggeredCommand"), "open")
            self.assertFalse(owner.property("menuOpened"))
        finally:
            owner.close()
            owner.deleteLater()


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, QPoint, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtTest import QTest
import shiboken6


ROOT = Path(__file__).resolve().parents[1]
QML = ROOT / "thlib" / "ui" / "qml"


class SharedPopupKeyboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if QGuiApplication.instance() is None:
            QQuickStyle.setStyle("Basic")
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def setUp(self):
        self.engine = QQmlEngine()
        self.engine.addImportPath(str(QML))
        self.component = QQmlComponent(self.engine)
        self.component.setData(
            b'''import QtQuick
import QtQuick.Controls
import QtQuick.Window
import "controls" as Controls

Window {
    id: window
    width: 440
    height: 300
    visible: true
    property bool comboPopupVisible: combo.popup.visible
    property int comboIndex: combo.currentIndex
    property bool menuVisible: menu.visible
    property bool textMenuVisible: textMenu.visible
    property bool dockMenuVisible: dockMenu.visible
    property string triggeredCommand: ""
    property string editorCommand: ""

    function focusCombo() { combo.forceActiveFocus() }
    function openMenu() { menu.openBelow(menuAnchor) }
    function toggleMenu() { menu.toggleBelow(menuAnchor) }
    function openTextMenu() {
        textMenu.openAt(textMenuAnchor, 0, textMenuAnchor.height)
    }
    function openDockMenu() { dockMenu.openBelow(dockMenuAnchor) }

    Theme {
        id: theme
        dark: true
        fadeAnimationsEnabled: false
        popupAnimationsEnabled: false
    }
    Controls.ComboBox {
        id: combo
        objectName: "keyboardCombo"
        x: 36
        y: 30
        width: 190
        theme: theme
        model: ["One", "Two", "Three"]
    }
    Rectangle {
        id: menuAnchor
        x: 36
        y: 100
        width: 120
        height: 34
        color: "transparent"
    }
    Rectangle {
        id: textMenuAnchor
        x: 190
        y: 100
        width: 120
        height: 34
        color: "transparent"
    }
    Rectangle {
        id: dockMenuAnchor
        x: 330
        y: 100
        width: 70
        height: 34
        color: "transparent"
    }
    ActionMenu {
        id: menu
        objectName: "keyboardActionMenu"
        theme: theme
        actions: [
            {"title": "First", "command": "first"},
            {"title": "Second", "command": "second"},
            {"title": "Third", "command": "third"}
        ]
        onTriggered: command => window.triggeredCommand = command
    }
    Item {
        id: editorStub
        property int selectionStart: 0
        property int selectionEnd: 1
        property int cursorPosition: 0
        function cut() { window.editorCommand = "cut" }
        function copy() { window.editorCommand = "copy" }
        function paste() { window.editorCommand = "paste" }
        function selectAll() { window.editorCommand = "select_all" }
    }
    Controls.TextContextMenu {
        id: textMenu
        objectName: "keyboardTextMenu"
        theme: theme
        editor: editorStub
    }
    ListModel {
        id: dockPanels
        function toggle_panel(panelId) {
            window.triggeredCommand = "dock-" + panelId
        }
        ListElement {
            panelId: "snapshots"
            title: "Snapshots"
            kind: "snapshot"
            panelVisible: false
            closable: true
        }
        ListElement {
            panelId: "tasks"
            title: "Tasks"
            kind: "tasks"
            panelVisible: false
            closable: true
        }
    }
    DockMenu {
        id: dockMenu
        objectName: "keyboardDockMenu"
        theme: theme
        panelModel: dockPanels
    }
}
''',
            QUrl.fromLocalFile(str(QML / "_KeyboardPopupsTest.qml")),
        )
        self.owner = self.component.create()
        self.assertIsNotNone(
            self.owner,
            "\n".join(
                error.toString() for error in self.component.errors()
            ),
        )
        self.owner.requestActivate()
        QTest.qWait(20)

    def tearDown(self):
        if shiboken6.isValid(self.owner):
            self.owner.close()
            self.owner.deleteLater()
        self.engine.deleteLater()

    def transient_popup_window(self):
        windows = [
            window for window in QGuiApplication.allWindows()
            if window != self.owner
            and window.isVisible()
            and window.transientParent() == self.owner
        ]
        self.assertEqual(len(windows), 1)
        return windows[0]

    def test_combo_pointer_activation_toggles_the_same_popup(self):
        point = QPoint(100, 48)
        QTest.mouseClick(
            self.owner, Qt.LeftButton, Qt.NoModifier, point,
        )
        QTest.qWait(30)
        self.assertTrue(self.owner.property("comboPopupVisible"))

        QTest.mouseClick(
            self.owner, Qt.LeftButton, Qt.NoModifier, point,
        )
        QTest.qWait(30)
        self.assertFalse(self.owner.property("comboPopupVisible"))

    def test_combo_supports_arrows_enter_space_and_escape(self):
        self.owner.focusCombo()
        QTest.keyClick(self.owner, Qt.Key_Space)
        QTest.qWait(80)
        self.assertTrue(self.owner.property("comboPopupVisible"))

        options = self.owner.findChild(QQuickItem, "comboBoxPopupList")
        self.assertIsNotNone(options)
        popup_window = options.window()
        QTest.keyClick(popup_window, Qt.Key_Down)
        QTest.keyClick(popup_window, Qt.Key_Return)
        QTest.qWait(20)
        self.assertEqual(self.owner.property("comboIndex"), 1)
        self.assertFalse(self.owner.property("comboPopupVisible"))

        QTest.keyClick(self.owner, Qt.Key_Space)
        QTest.qWait(80)
        self.assertTrue(self.owner.property("comboPopupVisible"))
        QTest.keyClick(options.window(), Qt.Key_Escape)
        QTest.qWait(20)
        self.assertFalse(self.owner.property("comboPopupVisible"))

        QTest.keyClick(self.owner, Qt.Key_Enter)
        QTest.qWait(80)
        self.assertTrue(self.owner.property("comboPopupVisible"))
        QTest.keyClick(options.window(), Qt.Key_Escape)
        QTest.qWait(20)

        self.owner.focusCombo()
        QTest.keyClick(self.owner, Qt.Key_Down)
        self.assertEqual(self.owner.property("comboIndex"), 2)

    def test_action_menu_uses_arrows_space_escape_and_toggle(self):
        self.owner.openMenu()
        QTest.qWait(100)
        self.assertTrue(self.owner.property("menuVisible"))
        menu = self.owner.findChild(QObject, "keyboardActionMenu")
        popup_window = self.transient_popup_window()

        QTest.keyClick(popup_window, Qt.Key_Down)
        self.app.processEvents()
        QTest.keyClick(popup_window, Qt.Key_Space)
        QTest.qWait(40)
        self.assertEqual(self.owner.property("triggeredCommand"), "second")
        self.assertFalse(self.owner.property("menuVisible"))

        QTest.qWait(180)
        self.owner.toggleMenu()
        QTest.qWait(20)
        self.assertTrue(self.owner.property("menuVisible"))
        QTest.keyClick(self.transient_popup_window(), Qt.Key_Escape)
        QTest.qWait(20)
        self.assertFalse(self.owner.property("menuVisible"))

        QTest.qWait(180)
        self.owner.toggleMenu()
        QTest.qWait(20)
        self.assertTrue(self.owner.property("menuVisible"))
        self.owner.toggleMenu()
        QTest.qWait(20)
        self.assertFalse(self.owner.property("menuVisible"))

    def test_text_context_menu_uses_arrows_space_and_escape(self):
        self.owner.openTextMenu()
        QTest.qWait(80)
        self.assertTrue(self.owner.property("textMenuVisible"))

        popup_window = self.transient_popup_window()
        QTest.keyClick(popup_window, Qt.Key_Down)
        QTest.keyClick(popup_window, Qt.Key_Space)
        QTest.qWait(40)
        self.assertEqual(self.owner.property("editorCommand"), "copy")
        self.assertFalse(self.owner.property("textMenuVisible"))

        self.owner.openTextMenu()
        QTest.qWait(80)
        self.assertTrue(self.owner.property("textMenuVisible"))
        QTest.keyClick(self.transient_popup_window(), Qt.Key_Escape)
        QTest.qWait(20)
        self.assertFalse(self.owner.property("textMenuVisible"))

    def test_dock_menu_uses_arrows_space_and_escape(self):
        self.owner.openDockMenu()
        QTest.qWait(80)
        self.assertTrue(self.owner.property("dockMenuVisible"))

        popup_window = self.transient_popup_window()
        QTest.keyClick(popup_window, Qt.Key_Down)
        QTest.keyClick(popup_window, Qt.Key_Space)
        QTest.qWait(40)
        dock_menu = self.owner.findChild(QObject, "keyboardDockMenu")
        submenu = dock_menu.property("activeSubmenu")
        self.assertTrue(submenu.property("opened"))
        submenu_content = submenu.property("contentItem")
        submenu_window = submenu_content.window()
        QTest.keyClick(submenu_window, Qt.Key_Space)
        QTest.qWait(40)
        self.assertEqual(self.owner.property("triggeredCommand"), "dock-tasks")
        self.assertFalse(self.owner.property("dockMenuVisible"))

        QTest.qWait(180)
        self.owner.openDockMenu()
        QTest.qWait(80)
        self.assertTrue(self.owner.property("dockMenuVisible"))
        QTest.keyClick(self.transient_popup_window(), Qt.Key_Escape)
        QTest.qWait(20)
        self.assertFalse(self.owner.property("dockMenuVisible"))

if __name__ == "__main__":
    unittest.main()

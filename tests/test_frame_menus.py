"""Main-menu input uses native popup ownership and the portable row composition."""

import json
from pathlib import Path
import unittest
from PySide6.QtCore import QCoreApplication, QEvent, QObject, QPointF, Qt, QUrl
from PySide6.QtQml import QQmlEngine, QQmlComponent, QQmlExpression
from PySide6.QtTest import QTest
from tests.qt_application import gui_test_application
from tests.profile_ui_responsiveness import frame
import tests.test_sidebar_editor_qml as fixture
from thlib.ui.icon_font import qml_icon_bindings
from thlib.ui.menu_schema import MenuRegistry

ROOT = Path(__file__).resolve().parents[1]
QML = ROOT / "thlib/ui/qml"


class FrameMenuTests(unittest.TestCase):
    def setUp(self):
        self.app = gui_test_application()
        self.engine = QQmlEngine()
        self.warnings = []
        self.engine.warnings.connect(
            lambda errors: self.warnings.extend(error.toString() for error in errors)
        )
        self.registry = MenuRegistry()
        self.qt_objects = []
        for name, value in qml_icon_bindings(ROOT, self.app).items():
            self.engine.rootContext().setContextProperty(name, value)
        self.component = QQmlComponent(self.engine)
        self.component.setData(
            b"""import QtQuick
import QtQuick.Controls
import "controls" as Controls
import "tactic_frame/shell/main.menus.mjs" as MainMenus
Window {
    id: window
    visible: true; width: 900; height: 850
    property string command: ""
    property bool commandAfterClose: false
    property var sourceActions: []
    property var menuContext: ({platform:"native",canAdminister:true,unread:7,updateMode:"poll",pollInterval:30})
    Theme { id: uiTheme; dark:true; popupAnimationsEnabled:false; hoverAnimationsEnabled:false }
    ActionMenu {
        id: menu; objectName:"testMainMenu"; theme:uiTheme; frameComposition:true
        actions:MainMenus.compose(window.sourceActions,window.menuContext)
        onTriggered: value => { window.commandAfterClose = !menu.opened; window.command = value }
    }
    Controls.DockWorkspaceFooter { objectName:"testFooter"; theme:uiTheme; width:300; anchors.bottom:parent.bottom }
    function openMenu() { menu.openAt(window.contentItem,20,20,false) }
}""",
            QUrl.fromLocalFile(str(QML / "_FrameMenuTest.qml")),
        )
        self.assertTrue(
            self.component.isReady(), [e.toString() for e in self.component.errors()]
        )
        self.window = self.component.create()
        self.assertIsNotNone(self.window)
        self.window.requestActivate()
        frame(self.window)

    def evaluate(self, expression):
        expr = QQmlExpression(
            QQmlEngine.contextForObject(self.window), self.window, expression
        )
        value = expr.evaluate()
        self.assertFalse(expr.hasError(), expr.error().toString())
        value = value[0] if isinstance(value, tuple) else value
        if isinstance(value, QObject):
            self.qt_objects.append(value)
        return value.toVariant() if hasattr(value, "toVariant") else value

    def open(self, name):
        self.evaluate("menu.close()")
        frame(self.window)
        self.window.setProperty("sourceActions", self.registry.actions(name))
        self.window.openMenu()
        frame(self.window)

    def target(self, command):
        content = self.evaluate("menu.contentItem")
        return next(
            item
            for item in fixture.SidebarEditorQmlTests.descendants(content)
            if item.objectName() == "actionMenuPrimaryTarget"
            and item.parentItem().property("modelData").toVariant().get("command")
            == command
        )

    def tearDown(self):
        self.evaluate("menu.close()")
        frame(self.window)
        self.window.close()
        self.window.deleteLater()
        self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.assertEqual(self.warnings, [])

    def test_first_mouse_touch_and_keyboard_dispatch_after_popup_closes(self):
        for input_kind in ("mouse", "touch", "key"):
            self.window.setProperty("command", "")
            self.open("user")
            target = self.target("show_messages")
            point = target.mapToScene(
                QPointF(target.width() / 2, target.height() / 2)
            ).toPoint()
            if input_kind == "key":
                target.forceActiveFocus()
                QTest.keyClick(target.window(), Qt.Key_Return)
            elif input_kind == "touch":
                device = QTest.createTouchDevice()
                QTest.touchEvent(target.window(), device).press(
                    0, point, target.window()
                ).commit()
                QTest.touchEvent(target.window(), device).release(
                    0, point, target.window()
                ).commit()
            else:
                QTest.mouseClick(target.window(), Qt.LeftButton, pos=point)
            frame(self.window)
            self.assertEqual(
                self.window.property("command"), "show_messages", input_kind
            )
            self.assertTrue(self.window.property("commandAfterClose"))

    def test_runtime_registry_replace_extend_and_connection_state(self):
        self.registry.replace(
            "user",
            [
                {
                    "title": "Custom",
                    "command": "script_custom",
                    "translate": False,
                    "accent": "red",
                    "checked": True,
                    "initials": "X",
                    "avatarColor": "steelblue",
                }
            ],
        )
        self.registry.extend(
            "user", [{"title": "Disabled", "command": "disabled", "enabled": False}]
        )
        self.open("user")
        self.assertEqual(self.evaluate("menu.displayedActions[0].title"), "Custom")
        self.assertFalse(self.target("disabled").isEnabled())
        target = self.target("script_custom")
        target.forceActiveFocus()
        QTest.keyClick(target.window(), Qt.Key_Space)
        frame(self.window)
        self.assertEqual(self.window.property("command"), "script_custom")
        self.open("connection")
        self.assertTrue(
            self.target("updates_30")
            .parentItem()
            .property("modelData")
            .toVariant()["checked"]
        )
        self.evaluate(
            'window.menuContext = Object.assign({}, window.menuContext, {updateMode:"sse"})'
        )
        frame(self.window)
        self.assertFalse(
            any(
                row.get("command") == "updates_30"
                for row in self.evaluate("menu.displayedActions")
            )
        )
        self.assertTrue(
            self.target("update_mode_sse")
            .parentItem()
            .property("modelData")
            .toVariant()["checked"]
        )
        footer = self.window.findChild(QObject, "testFooter")
        self.assertEqual(footer.property("implicitHeight"), 58)
        self.assertEqual(footer.property("topLeftRadius"), 0)
        self.assertEqual(footer.property("bottomLeftRadius"), 11)
        self.window.setFlags(Qt.Dialog)
        frame(self.window)
        self.assertTrue(footer.property("nativeDialog"))
        self.assertEqual(footer.property("bottomLeftRadius"), 0)


if __name__ == "__main__":
    unittest.main()

"""Shell menu actions follow the active user's management authority."""

from tempfile import TemporaryDirectory
from types import SimpleNamespace
from pathlib import Path
import unittest
from unittest.mock import patch

from PySide6.QtCore import QObject, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest

from tests.qt_application import gui_test_application
from thlib.environment import env_mode, env_server
from thlib.ui.controller import ApplicationController
from thlib.ui.script_editor import ScriptEditorController


class ShellPermissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def setUp(self):
        directory = self.enterContext(TemporaryDirectory())
        self.enterContext(patch.object(env_mode, "current_path", directory))
        self.controller = ApplicationController()
        self.addCleanup(self.controller.shutdown)
        self.users = SimpleNamespace(canManageUsers=False)
        self.controller.attach_user_controller(self.users)

    def test_regular_user_cannot_open_hidden_tools_or_server_window(self):
        actions = {
            action.get("command")
            for action in self.controller.menu_actions("configuration")
        }
        self.assertTrue({
            "show_tools", "show_ui_performance", "show_handler_server"
        }.isdisjoint(actions))
        self.assertIn("show_update", actions)
        self.assertIn("open_script_editor", actions)
        self.assertEqual(self.controller.menu_actions("tools"), [])

        for command in (
            "show_tools", "show_ui_performance", "show_handler_server",
            "tool_columns_editor", "dcc_tool:show_viewer",
        ):
            self.controller.invoke(command)
        self.controller.open_window("handler_server")
        self.controller.open_window("ui_performance")
        self.controller.open_window("update")
        self.controller.open_window("columns_editor")

        for window_id in ("handler_server", "ui_performance", "columns_editor"):
            self.assertFalse(
                self.controller.window_model.is_window_visible(window_id)
            )
        self.assertTrue(
            self.controller.window_model.is_window_visible("update")
        )

    def test_supervisor_keeps_server_controls_without_tools_menu(self):
        self.users.canManageUsers = True
        with patch.object(env_server, 'get_ticket', return_value='test-ticket'):
            self.controller._set_server_state('online', 'Authenticated')
            actions = {
                action.get("command")
                for action in self.controller.menu_actions("configuration")
            }
        self.assertTrue({
            "show_administration", "show_ui_performance", "show_handler_server"
        }.issubset(actions))
        self.assertNotIn("show_tools", actions)
        self.assertEqual(self.controller.menu_actions("tools"), [])


class ScriptEditorReadOnlyQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def test_regular_user_cannot_type_in_code_editor(self):
        qml_dir = Path(__file__).resolve().parents[1] / "thlib/ui/qml"
        engine = QQmlEngine()
        engine.addImportPath(str(qml_dir))
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        self.assertIsNotNone(theme, theme_component.errors())
        with patch("thlib.ui.script_editor.env_read_config", return_value={}):
            controller = ScriptEditorController(
                None, None,
                users=SimpleNamespace(
                    canManageUsers=False,
                    stateChanged=SimpleNamespace(connect=lambda _callback: None),
                ),
            )
        context = engine.rootContext()
        context.setContextProperty("scriptEditorController", controller)
        context.setContextProperty("scriptEditorModel", controller.model)
        context.setContextProperty("scriptEditorTabModel", controller.tabs)
        context.setContextProperty("scriptTriggerController", QObject())
        context.setContextProperty("windowModel", QObject())
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(
                str(qml_dir / "ScriptEditorView.qml")
            ),
        )
        editor = component.createWithInitialProperties({
            "theme": theme,
        })
        self.assertIsNotNone(editor, component.errors())
        window = QQuickWindow()
        try:
            window.setWidth(700)
            window.setHeight(400)
            editor.setWidth(690)
            editor.setHeight(390)
            editor.setParentItem(window.contentItem())
            code_editor = editor.findChild(QObject, "scriptEditorCodeEditor")
            self.assertIsNotNone(code_editor)
            self.assertTrue(code_editor.property("readOnly"))
            code_editor.setProperty("text", "print('original')")
            source = editor.findChild(QObject, "scriptEditorSourceText")
            self.assertIsNotNone(source)
            self.assertTrue(source.property("readOnly"))
            window.show()
            source.forceActiveFocus()
            QTest.keyClick(window, Qt.Key_X)
            self.assertEqual(source.property("text"), "print('original')")
        finally:
            window.close()
            editor.setParentItem(None)
            editor.deleteLater()
            theme.deleteLater()
            window.deleteLater()

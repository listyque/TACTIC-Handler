"""MCP window uses real native controls and forgets access tokens on close."""
from copy import deepcopy
import time
import unittest
from unittest.mock import patch

from PySide6.QtCore import Signal, QPointF, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest

from tests.test_frame_script_tools import ScriptToolsTests, QML
from tests.test_agent_request import Application
from tests.profile_ui_responsiveness import frame
from thlib.environment import env_inst
from thlib.ui.agent_mcp import AgentMcpController
from thlib.ui.icon_font import qml_icon_bindings


class McpApplication(Application):
    project_changed = Signal(str, str)
    server_url = 'http://127.0.0.1:8081'


class Server:
    def __init__(self):
        self.last = None
        self.created = None

    def get_project(self):
        return 'one'

    def execute_cmd(self, command, values):
        self.last = deepcopy(values)
        if values['action'] == 'create':
            self.created = deepcopy(values)
            return dict(status='OK', info=dict(id='fixture', path='/mcp/fixture', token='test-only-token'))
        return dict(status='OK', info=dict(enabled=True, unlimited_lifetime=True,
            connections=[dict(id='persistent', title='Persistent fixture', expires=None, revoked=False, pending=False)], tools=[
            dict(name='agent_context', description='Captured context', readonly=True),
            dict(name='ts_dashboard_save', description='Save a dashboard', readonly=False)]))


class McpUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ScriptToolsTests.setUpClass()

    def test_native_window_input_scope_token_and_close(self):
        surface = ScriptToolsTests(); surface.setUp(); self.addCleanup(surface.doCleanups)
        for name, value in qml_icon_bindings(QML.parents[2], surface.engine).items():
            surface.engine.rootContext().setContextProperty(name, value)
        app = McpApplication(); controller = AgentMcpController(app, env_inst.server_pool)
        self.addCleanup(controller.reset)
        server = Server()
        context = dict(client='TH', project='one', page='assets', title='Assets', search_type='cg/asset', view='table', search_keys=[])
        with patch('thlib.tactic_classes.server_start', return_value=server):
            controller.open(context)
            def wait():
                deadline = time.monotonic() + 10
                while controller.model['busy'] and time.monotonic() < deadline: QTest.qWait(10)
                self.assertFalse(controller.model['busy'])
                self.assertFalse(controller.model['error'], controller.model)
            wait()
            view = surface.create(QML/'features/configuration/AgentMcpView.qml', dict(theme=surface.theme, controller=controller, width=800, height=650))
            window = QQuickWindow(); window.resize(800,650); surface.windows.append(window)
            view.setParentItem(window.contentItem()); window.show(); frame(window)
            self.assertEqual(surface.item(view, 'mcpTool_0').property('text'), 'agent_context')
            caption = surface.item(view, 'mcpToolName_0')
            self.assertEqual(caption.property('text'), 'agent_context')
            surface.click(window, caption)
            self.assertEqual(controller.model['selected'], ['agent_context'])
            QTest.keyClick(window, Qt.Key_Space); frame(window)
            self.assertEqual(controller.model['selected'], [])
            surface.click(window, surface.item(view, 'mcpAllTools')); frame(window)
            self.assertEqual(set(controller.model['selected']), {'agent_context', 'ts_dashboard_save'})
            surface.click(window, surface.item(view, 'mcpClearTools')); frame(window)
            self.assertEqual(controller.model['selected'], [])
            field = surface.item(view,'mcpTitle'); field.forceActiveFocus()
            for char in 'Tracker': QTest.keyClick(window,char)
            surface.click(window,surface.item(view,'mcpReadTools')); frame(window)
            self.assertEqual(controller.model['selected'],['agent_context'])
            surface.item(view, 'mcpLifetime').forceActiveFocus()
            QTest.keyClick(window, Qt.Key_Down)
            QTest.keyClick(window, Qt.Key_Down); frame(window)
            self.assertEqual(controller.model['minutes'], '0')
            surface.click(window,surface.item(view,'mcpCreate')); wait(); frame(window)
            self.assertEqual(server.created['minutes'], 0)
            self.assertFalse(controller.model['connections'][0]['expired'])
            self.assertIn('No expiration', surface.item(view, 'mcpExisting_0').property('text'))
            self.assertTrue(controller.model['unlimited_lifetime'])
            self.assertEqual(controller.model['title'],'Tracker')
            self.assertIn('/mcp/fixture',controller.model['issued'])
            scene=surface.item(view,'mcpCopyAgentLink')
            self.assertIsNotNone(scene)
            scroll=surface.item(view,'mcpScroll')
            scroll.setProperty('contentY',max(0,scene.mapToScene(QPointF(0,0)).y()-300))
            frame(window)
            surface.click(window,scene)
            self.assertEqual(QGuiApplication.clipboard().text(),'http://127.0.0.1:8081/mcp/fixture#access_token=test-only-token')
            for width in (320,800):
                window.resize(width,650); view.setWidth(width); frame(window)
                self.assertLessEqual(surface.item(view,'mcpCreate').x()+surface.item(view,'mcpCreate').width(),width)
            app.window_model.close_window('agent_mcp')
            self.assertEqual(controller.model['issued'],'')
            app.project_changed.emit('two','Two')
            self.assertFalse(controller.model['tools'])
            self.assertFalse(surface.warnings,surface.warnings)

"""Actual native provider editor: input, write-only key and preserved drafts."""
from copy import deepcopy
import os
from pathlib import Path
import time
import unittest
from unittest.mock import patch

from PySide6.QtCore import Qt
from PySide6.QtQuick import QQuickWindow
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtTest import QTest

from tests.test_frame_script_tools import ScriptToolsTests, QML
from tests.test_agent_request import Application
from tests.profile_ui_responsiveness import frame
from thlib.environment import env_inst
from thlib.ui.agent_providers import AgentProvidersController
from thlib.ui.icon_font import qml_icon_bindings


class Server:
    def __init__(self):
        self.state = dict(default='codex', revision='r1', profiles=[dict(id='codex', name='Codex', kind='codex', url='', enabled=True,
            default_model='', models=[], status='connected')], kinds=[dict(value='codex',label='Codex account',url=''),
            dict(value='local',label='Local model server',url='http://127.0.0.1:11434/v1')])
        self.last = None

    def execute_cmd(self, command, values):
        self.last = deepcopy(values)
        if values['action']=='save':
            row = {key:value for key,value in values['document'].items() if key not in ('secret','clear_secret','default')}
            row.update(id='local', has_secret=bool(values['document']['secret']), status='unchecked', models=[])
            self.state['profiles'].append(row)
            self.state['revision']='r2'
        return dict(status='OK',info=deepcopy(self.state))


class ProviderUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ScriptToolsTests.setUpClass()
        if os.name=='nt':
            for name in ('segoeui.ttf','segoeuib.ttf'):
                QFontDatabase.addApplicationFont(str(Path(os.environ['WINDIR'])/'Fonts'/name))
            ScriptToolsTests.app.setFont(QFont('Segoe UI'))

    def test_configuration_embeds_editor_without_opening_another_window(self):
        surface=ScriptToolsTests();surface.setUp();self.addCleanup(surface.doCleanups)
        for name,value in qml_icon_bindings(QML.parents[2],surface.engine).items():
            surface.engine.rootContext().setContextProperty(name,value)
        app=Application();controller=AgentProvidersController(app,env_inst.server_pool)
        self.addCleanup(controller.reset)
        server=Server()
        config=surface.inline('import QtQuick; QtObject { function page_schema(id) { return {}; } }', {})
        surface.engine.rootContext().setContextProperty('configurationController', config)
        surface.engine.rootContext().setContextProperty('agentProvidersController', controller)
        with patch('thlib.tactic_classes.server_start',return_value=server):
            view=surface.create(QML/'ConfigurationPage.qml',dict(theme=surface.theme,pageId='ai',width=1000,height=650))
            window=QQuickWindow();window.resize(1000,650);window.setColor(surface.theme.property('workspace'));surface.windows.append(window)
            view.setParentItem(window.contentItem());window.show();frame(window)
            end=time.monotonic()+10
            while controller.model['busy'] and time.monotonic()<end:QTest.qWait(10)
            frame(window)
            self.assertFalse(controller.model['busy'])
            self.assertTrue(surface.item(view,'agentProviderProfile').isVisible())
            if os.environ.get('TACTIC_PROVIDER_CAPTURE'):
                window.grabWindow().save(str(Path(os.environ['TACTIC_PROVIDER_CAPTURE'])/'native-embedded-providers.png'))
            self.assertFalse(app.window_model.is_window_visible('agent_providers'))
            server.state['profiles'][0]['status']='waiting'
            controller.request('state')
            end=time.monotonic()+10
            while controller.model['busy'] and time.monotonic()<end:QTest.qWait(10)
            self.assertTrue(controller._timer.isActive())
            controller.handle(dict(type='field',field='name',value='Kept draft'))
            view.setProperty('pageId','unknown');frame(window)
            self.assertFalse(controller._embedded_active)
            self.assertFalse(controller._timer.isActive())
            view.setProperty('pageId','ai');frame(window)
            self.assertEqual(controller.model['draft']['name'],'Kept draft')
            self.assertFalse(app.window_model.is_window_visible('agent_providers'))
            self.assertFalse(surface.warnings,surface.warnings)

    def test_embedded_editor_does_not_connect_without_administrator_access(self):
        app=Application();app.can_administer=False
        controller=AgentProvidersController(app,env_inst.server_pool)
        self.addCleanup(controller.reset)
        with patch('thlib.tactic_classes.server_start') as start:
            controller.set_embedded_active(True)
            start.assert_not_called()
        self.assertEqual(controller.model['error'],'Administrator access required')
        self.assertFalse(app.window_model.is_window_visible('agent_providers'))

    def test_native_edit_save_and_auth_reset(self):
        surface=ScriptToolsTests();surface.setUp();self.addCleanup(surface.doCleanups)
        for name,value in qml_icon_bindings(QML.parents[2],surface.engine).items():
            surface.engine.rootContext().setContextProperty(name,value)
        app=Application();controller=AgentProvidersController(app,env_inst.server_pool)
        self.addCleanup(controller.reset)
        server=Server()
        with patch('thlib.tactic_classes.server_start',return_value=server):
            controller.open()
            def wait():
                end=time.monotonic()+10
                while controller.model['busy'] and time.monotonic()<end:QTest.qWait(10)
                self.assertFalse(controller.model['busy']);self.assertFalse(controller.model['error'],controller.model)
            wait()
            view=surface.create(QML/'features/configuration/AgentProvidersView.qml',dict(theme=surface.theme,controller=controller,width=1000,height=650))
            window=QQuickWindow();window.resize(1000,650);window.setColor(surface.theme.property('workspace'));surface.windows.append(window)
            view.setParentItem(window.contentItem());window.show();frame(window)
            surface.click(window,surface.item(view,'agentProvider_new'))
            name=surface.item(view,'setting_name');name.forceActiveFocus()
            for char in 'Local fixture':QTest.keyClick(window,char)
            frame(window)
            self.assertEqual(controller.model['draft']['name'],'Local fixture')
            controller.handle(dict(type='field',field='kind',value='local'));frame(window)
            self.assertEqual(controller.model['draft']['url'],'http://127.0.0.1:11434/v1')
            key=surface.item(view,'setting_secret')
            echo=surface.inline('import QtQuick; QtObject { property var source; property bool hidden: source.echoMode === TextInput.Password }',dict(source=key))
            self.assertTrue(echo.property('hidden'))
            controller.handle(dict(type='field',field='secret',value='private-fixture'))
            app.window_model.close_window('agent_providers');controller.open();frame(window)
            self.assertEqual(controller.model['draft']['secret'],'private-fixture')
            surface.click(window,surface.item(view,'agentProviderSave'));wait();frame(window)
            self.assertEqual(server.last['document']['secret'],'private-fixture')
            self.assertEqual(controller.model['draft']['secret'],'')
            self.assertTrue(controller.model['profiles'][-1]['has_secret'])
            for width in (320,520,1000):
                window.resize(width,650);view.setWidth(width);frame(window)
                self.assertLessEqual(surface.item(view,'agentProviderCheck').x()+surface.item(view,'agentProviderCheck').width(),width)
                if os.environ.get('TACTIC_PROVIDER_CAPTURE'):
                    window.grabWindow().save(str(Path(os.environ['TACTIC_PROVIDER_CAPTURE'])/f'native-providers-{width}.png'))
            app.authentication_changed.emit()
            self.assertEqual(controller.model['profiles'],[])
            self.assertFalse(controller.model['draft'])
            self.assertFalse(surface.warnings,surface.warnings)

    def test_waiting_host_does_not_replace_an_untouched_new_connection(self):
        app = Application()
        controller = AgentProvidersController(app, env_inst.server_pool)
        self.addCleanup(controller.reset)
        server = Server()
        server.state['profiles'][0]['status'] = 'waiting'
        with patch('thlib.tactic_classes.server_start', return_value=server):
            controller.set_embedded_active(True)
            deadline = time.monotonic() + 5
            while controller.model['busy'] and time.monotonic() < deadline:
                QTest.qWait(10)
            self.assertTrue(controller._timer.isActive())
            controller.handle(dict(type='new'))
            self.assertEqual(controller.model['selected'], '')
            controller._timer.timeout.emit()
            while controller.model['busy'] and time.monotonic() < deadline:
                QTest.qWait(10)
            self.assertEqual(controller.model['selected'], '')
            self.assertEqual(controller.model['draft']['name'], '')
            controller.set_embedded_active(False)
            controller.set_embedded_active(True)
            while controller.model['busy'] and time.monotonic() < deadline:
                QTest.qWait(10)
            self.assertEqual(controller.model['selected'], '')
            controller.handle(dict(type='select', value='codex'))
            self.assertTrue(controller._timer.isActive())

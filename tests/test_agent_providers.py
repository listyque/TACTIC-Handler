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

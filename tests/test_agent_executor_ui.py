"""Actual native connection buttons in chat and provider settings."""
import time
import unittest
from copy import deepcopy
from unittest.mock import patch

from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
from tests import test_agent_request as requests
from tests import test_agent_providers as providers
from tests import test_frame_script_tools as frames
from tests.profile_ui_responsiveness import frame
from thlib.environment import env_inst
from thlib.ui.agent_request import AgentRequestController
from thlib.ui.agent_providers import AgentProvidersController


class Server(requests.Server):
    def __init__(self):
        super().__init__()
        self.executor = dict(state='stopped', managed=False, error='', target='', targets=[dict(id='server', kind='server', label='TACTIC server', state='stopped')])
        self.settings = providers.Server()
        self.controls = []

    def execute_cmd(self, command, values):
        if command.endswith('AgentExecutorCmd'):
            self.controls.append(deepcopy(values))
            self.executor = dict(state='connected' if values['action'] == 'start' else 'stopped', managed=True, error='', target='server')
            self.executor['targets'] = [dict(id='server', kind='server', label='TACTIC server', state=self.executor['state'])]
            return dict(status='OK', info=self.executor)
        reply = (self.settings if command.endswith('AgentProviderCmd') else super()).execute_cmd(command, values)
        if values['action'] == 'state':
            reply['info']['executor'] = dict(self.executor)
            if 'hosts' in reply['info'] and self.executor['state'] == 'stopped':
                reply['info']['hosts'] = []
        return reply


class ExecutorUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        frames.ScriptToolsTests.setUpClass()

    def test_connect_disconnect_from_both_native_surfaces(self):
        for kind in ('chat', 'providers'):
            with self.subTest(kind=kind):
                surface = frames.ScriptToolsTests()
                surface.setUp()
                self.addCleanup(surface.doCleanups)
                app, server = requests.Application(), Server()
                owner = (AgentRequestController if kind == 'chat' else AgentProvidersController)(app, env_inst.server_pool)
                self.addCleanup(owner.reset)
                with patch('thlib.tactic_classes.server_start', return_value=server):
                    owner.open()
                    def wait():
                        deadline = time.monotonic() + 8
                        while owner.model['busy'] and time.monotonic() < deadline:
                            QTest.qWait(10)
                        self.assertFalse(owner.model['busy'])
                        self.assertFalse(owner.model['error'], owner.model['error'])
                    wait()
                    filename = 'features/scripts/AgentRequestView.qml' if kind == 'chat' else 'features/configuration/AgentProvidersView.qml'
                    view = surface.create(frames.QML / filename, dict(theme=surface.theme, controller=owner, width=1000, height=650))
                    window = QQuickWindow()
                    window.resize(1000, 650)
                    surface.windows.append(window)
                    view.setParentItem(window.contentItem())
                    window.show()
                    frame(window)
                    owner.handle('executorTarget', 'server') if kind == 'chat' else owner.handle(dict(type='executorTarget', value='server'))
                    surface.click(window, surface.item(view, 'agentExecutorControl'))
                    wait()
                    self.assertEqual(owner.model['executor']['state'], 'connected')
                    surface.click(window, surface.item(view, 'agentExecutorControl'))
                    wait()
                    self.assertEqual(owner.model['executor']['state'], 'stopped')
                    self.assertEqual(server.controls, [dict(action='start', project_code='one', target='server'), dict(action='stop', project_code='one', target='server')])
                    self.assertFalse(surface.warnings, surface.warnings)

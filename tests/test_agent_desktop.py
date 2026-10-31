"""Companion registration alone never starts an executor or installs packages."""
import unittest
from threading import Thread
from unittest.mock import patch, Mock
from uuid import uuid4
from xmlrpc.server import SimpleXMLRPCRequestHandler, SimpleXMLRPCServer

from PySide6.QtTest import QTest
from tests import test_agent_request as requests
from tests import test_frame_script_tools as frames
from thlib.environment import env_inst
from thlib.ui.agent_desktop import AgentDesktopController


class Desktop(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        frames.ScriptToolsTests.setUpClass()

    def test_legacy_server_stops_polling_until_the_session_changes(self):
        app = requests.Application()
        app.authentication_required = False
        local, server = Mock(), Mock()
        local.reports.return_value = {}
        server.class_exists.return_value = False
        server.execute_cmd.side_effect = AssertionError('Legacy command must not execute')
        with patch('thlib.environment.env_server.get_ticket', return_value='fixture-ticket'), \
             patch('thlib.environment.env_server.get_server', return_value='http://127.0.0.1:9'), \
             patch('thlib.environment.env_server.get_user', return_value='alice'), \
             patch('thlib.tactic_classes.server_start', return_value=server), \
             patch('thlib.ui.agent_desktop.LocalAgents', return_value=local):
            owner = AgentDesktopController(app, env_inst.server_pool)
            self.addCleanup(owner.close)
            for _ in range(200):
                if not owner.worker:
                    break
                QTest.qWait(10)
            self.assertIsNone(owner.worker)
            self.assertFalse(owner.timer.isActive())
            owner.sync()
            owner.poll()
            self.assertIsNone(owner.worker)
            server.class_exists.assert_called_once_with(
                'tactic.ui.panel.agent_executor_cmd.AgentExecutorCmd')
            server.execute_cmd.assert_not_called()
            local.start.assert_not_called()
            local.close.assert_not_called()
            old_generation = owner.generation
            owner.close()
            owner.sync()
            for _ in range(200):
                if not owner.worker:
                    break
                QTest.qWait(10)
            self.assertEqual(server.class_exists.call_count, 2)
            owner.done(dict(generation=old_generation, available=True))
            self.assertFalse(owner.timer.isActive())

    def test_offline_probe_is_retried_and_poll_failure_keeps_known_support(self):
        server = Mock()
        server.class_exists.side_effect = [OSError('offline'), True]
        values = dict(acks=[])
        first = AgentDesktopController.load(server, values, 1)
        self.assertIsNone(first.get('available'))
        server.execute_cmd.side_effect = OSError('offline')
        second = AgentDesktopController.load(server, values, 1, first.get('available'))
        self.assertTrue(second['available'])
        server.execute_cmd.side_effect = None
        server.execute_cmd.return_value = dict(status='OK', info=dict(commands=[]))
        third = AgentDesktopController.load(server, values, 1, second['available'])
        self.assertEqual(third['info'], dict(commands=[]))
        self.assertEqual(server.class_exists.call_count, 2)

    def test_optional_commands_over_native_xmlrpc_transport(self):
        from thlib.proxy import UrllibTransport
        from thlib.side.client.tactic_client_lib.tactic_server_stub import TacticServerStub
        from tests.test_script_triggers import ScriptTriggerTests

        calls = []
        available = False

        def class_exists(ticket, command):
            calls.append(command)
            return available

        class Handler(SimpleXMLRPCRequestHandler):
            rpc_paths = ('/tactic/default/Api/',)

        def execute_cmd(*args):
            self.assertTrue(available, 'Legacy command must not execute')
            return dict(status='OK', info=dict(commands=[]))

        with SimpleXMLRPCServer(('127.0.0.1', 0), requestHandler=Handler, logRequests=False) as rpc:
            rpc.register_function(class_exists)
            rpc.register_function(execute_cmd)
            rpc.register_function(lambda *args: [], 'query')
            thread = Thread(target=rpc.serve_forever, kwargs=dict(poll_interval=0.01))
            thread.start()
            try:
                with patch('thlib.environment.env_server.get_proxy', return_value={}), \
                     patch('thlib.environment.env_server.get_timeout', return_value=2):
                    server = TacticServerStub(setup=False)
                    server.transport = UrllibTransport()
                    server.set_server('http://127.0.0.1:%s' % rpc.server_address[1])
                    server.set_ticket('fixture-ticket')
                    result = AgentDesktopController.load(server, dict(acks=[]), 1)
                    self.assertFalse(result['available'])
                    hooks = ScriptTriggerTests()
                    hooks.setUp()
                    self.addCleanup(hooks.controller.shutdown)
                    hooks.controller._project_code = 'demo'
                    hooks.controller._run_server = lambda operation, handler: handler(operation())
                    with patch('thlib.tactic_classes.server_start', return_value=server):
                        hooks.controller.refresh()
                    self.assertTrue(hooks.controller.canManage)
                    self.assertFalse(hooks.controller.error)
                    self.assertEqual(calls, [
                        'tactic.ui.panel.agent_executor_cmd.AgentExecutorCmd',
                        'tactic.ui.panel.handler_automation_cmd.HandlerAutomationCmd',
                    ])
                    available = True
                    result = AgentDesktopController.load(server, dict(acks=[]), 2)
                    self.assertTrue(result['available'])
                    self.assertEqual(result['info'], dict(commands=[]))
            finally:
                rpc.shutdown()
                thread.join(timeout=2)

    def test_registration_deduplication_logout_and_stale_reply(self):
        app = requests.Application()
        app.authentication_required = False
        local = Mock()
        local.reports.return_value = {}
        server = Mock()
        server.execute_cmd.return_value = dict(status='OK', info=dict(commands=[]))
        with patch('thlib.environment.env_server.get_ticket', return_value='fixture-ticket'), \
             patch('thlib.environment.env_server.get_server', return_value='http://127.0.0.1:9'), \
             patch('thlib.environment.env_server.get_user', return_value='alice'), \
             patch('thlib.tactic_classes.server_start', return_value=server), \
             patch('thlib.ui.agent_desktop.LocalAgents', return_value=local):
            owner = AgentDesktopController(app, env_inst.server_pool)
            self.addCleanup(owner.close)
            deadline = 2000
            while owner.worker and deadline:
                QTest.qWait(10)
                deadline -= 10
            self.assertIsNone(owner.worker)
            local.start.assert_not_called()
            self.assertEqual(server.execute_cmd.call_args.args[1]['reports'], {})
            self.assertNotIn('fixture-ticket', str(server.execute_cmd.call_args))
            operation = dict(operation=str(uuid4()), action='start', project='one')
            reply = dict(generation=owner.generation, info=dict(commands=[operation]), acks=[])
            owner.done(reply)
            owner.done(reply)
            local.start.assert_called_once_with('one', operation['operation'], 'http://127.0.0.1:9', 'fixture-ticket')
            owner.stop_local('one', dict(action='stop', target=owner.device))
            local.stop.assert_called_once_with('one')
            app.signing_out.emit()
            local.close.assert_called_once()
            owner.done(reply)
            self.assertEqual(local.start.call_count, 1)
            self.assertFalse(owner.timer.isActive())

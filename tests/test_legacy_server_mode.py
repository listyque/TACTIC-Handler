"""Session detection hides Stream services without disabling legacy workflows."""
from io import BytesIO
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError

from tests import test_administration_access as access_fixture
from thlib import tactic_classes as tc, server_cache
from thlib.environment import env_inst
from thlib.ui.agent_desktop import AgentDesktopController
from thlib.ui.agent_mcp import AgentMcpController
from thlib.ui.agent_providers import AgentProvidersController
from thlib.ui.agent_request import AgentRequestController
from thlib.ui.configuration_server import ServerControlEditor
from thlib.ui.configuration_database_resources import DatabaseResourcesEditor
from thlib.ui.system_info import SystemInfoController


class LegacyServerModeTests(unittest.TestCase):
    def setUp(self):
        fixture = access_fixture.AdministrationAccessTests()
        fixture.setUpClass()
        fixture.setUp()
        self.enterContext(patch.object(env_inst, 'exit_pools'))
        self.addCleanup(fixture.doCleanups)
        self.application = fixture.application
        self.admin = fixture.admin
        self.enterContext(patch.object(env_inst, 'server_api', None))
        self.identity = ('http://tactic.test', 'supervisor', 'test-ticket')
        self.application._server_state = 'online'
        self.application._administration_identity = self.identity[:2]

    def test_detection_is_bound_to_server_login_and_ticket(self):
        app = self.application
        self.assertEqual(app.server_api, 'unknown')
        self.assertFalse(app.is_stream_server)
        env_inst.server_api = (*self.identity, 'stream')
        self.assertTrue(app.is_stream_server)
        for index in range(3):
            changed = list(self.identity)
            changed[index] = 'other'
            env_inst.server_api = (*changed, 'stream')
            self.assertEqual(app.server_api, 'unknown')
        env_inst.server_api = (*self.identity, 'legacy')
        self.assertEqual(app.server_api, 'legacy')
        self.assertTrue(app.can_manage_tools)

    def test_authoritative_bootstrap_publishes_mode_and_cache_cannot_enable_it(self):
        payload = dict(projects=[], logins=[], server_api='stream')
        with patch.object(tc, 'execute_procedure_serverside', return_value=payload), \
                patch.object(server_cache, 'token', return_value=None), \
                patch.object(env_inst, 'projects'), patch.object(env_inst, 'logins'):
            tc.get_all_projects_and_logins(force=True)
        self.assertTrue(self.application.is_stream_server)
        payload['server_api'] = 'unsupported'
        with patch.object(tc, 'execute_procedure_serverside', return_value=payload), \
                patch.object(server_cache, 'token', return_value=None), \
                patch.object(env_inst, 'projects'), patch.object(env_inst, 'logins'):
            tc.get_all_projects_and_logins(force=True)
        self.assertEqual(self.application.server_api, 'unknown')
        payload['server_api'] = 'stream'
        env_inst.server_api = None
        with patch.object(server_cache, 'read_entry', return_value=payload), \
                patch.object(tc.env_mode, 'get_mode', return_value='standalone'), \
                patch.object(env_inst, 'projects'), patch.object(env_inst, 'logins'):
            tc.get_all_projects_and_logins(cache_only=True)
        self.assertEqual(self.application.server_api, 'unknown')

    def test_legacy_menus_and_direct_entry_points_never_contact_stream(self):
        app = self.application
        env_inst.server_api = (*self.identity, 'legacy')
        commands = {row.get('command') for row in app.menu_actions('configuration')}
        self.assertNotIn('open_agent_request', commands)
        self.assertNotIn('show_system_info', commands)
        self.assertIn('open_script_editor', commands)
        self.assertIn('show_administration', commands)
        pool = Mock(is_stopped=False)
        with patch.object(tc, 'server_start') as server, \
                patch.object(env_inst, 'server_pool', pool):
            chat = AgentRequestController(app, pool)
            providers = AgentProvidersController(app, pool)
            mcp = AgentMcpController(app, pool)
            desktop = AgentDesktopController(app, pool)
            info = SystemInfoController(app, pool)
            backend = ServerControlEditor(app)
            resources = DatabaseResourcesEditor(app)
            for owner, close in ((chat, chat.reset), (providers, providers.reset),
                                 (mcp, mcp.reset), (desktop, desktop.close),
                                 (info, info.reset), (backend, backend.shutdown), (resources, resources.shutdown)):
                self.addCleanup(close)
            chat.open(dict(project='one'))
            providers.open()
            mcp.open(dict(project='one'))
            info.open()
            backend.open()
            resources.open()
            self.assertFalse(backend.managementAvailable)
            app.invoke('open_agent_providers')
            app.open_window('agent_request')
            server.assert_not_called()
            pool.add_task.assert_not_called()
            self.assertFalse(desktop.timer.isActive())
            for window in ('agent_request', 'agent_providers', 'agent_mcp', 'system_info'):
                self.assertFalse(app.window_model.is_window_visible(window))

    def test_stream_layout_entry_points_do_not_send_legacy_requests(self):
        app, admin = self.application, self.admin
        pool = Mock(is_stopped=False)
        with patch.object(tc, 'server_start') as server, \
                patch.object(env_inst, 'server_pool', pool):
            for mode in ('legacy', 'unknown'):
                env_inst.server_api = (*self.identity, mode)
                admin.select_section('dashboards')
                admin.select_section('layouts')
                admin.open_page_layout('review')
                admin.open_page_card('demo/asset', 'cards')
                admin.open_layout_editor()
                admin.dashboardEditor.activate('demo')
                admin.dashboardEditor.load_source('demo/asset')
                admin.dashboardEditor._document = {'name': 'review'}
                admin.dashboardEditor._preview()
                admin.layoutEditor.activate('demo')
                self.assertEqual(admin.section, 'groups')
                self.assertFalse(admin.streamAvailable)
                server.assert_not_called()
                pool.add_task.assert_not_called()

    def test_stream_layout_session_loss_cancels_queued_requests(self):
        app, admin = self.application, self.admin
        pool = Mock(is_stopped=False)
        env_inst.server_api = (*self.identity, 'stream')
        admin._project = 'demo'
        with patch.object(env_inst, 'server_pool', pool), \
                patch.object(tc, 'execute_procedure_serverside') as execute:
            admin.select_section('dashboards')
            self.assertTrue(admin.streamAvailable)
            self.assertEqual(admin.section, 'dashboards')
            operation = pool.add_task.call_args.args[0]
            env_inst.server_api = (*self.identity, 'legacy')
            app.authentication_changed.emit()
            self.assertEqual(admin.section, 'groups')
            self.assertEqual(admin.dashboardEditor.document, {})
            with self.assertRaises(PermissionError):
                operation()
            execute.assert_not_called()

    def test_stream_plugin_manager_never_sends_legacy_commands_or_uploads(self):
        from PySide6.QtCore import QUrl
        admin = self.admin
        pool = Mock(is_stopped=False)
        with patch.object(tc, 'server_start') as server, \
                patch.object(env_inst, 'server_pool', pool):
            for mode in ('legacy', 'unknown'):
                env_inst.server_api = (*self.identity, mode)
                admin.select_section('plugins')
                editor = admin.pluginsEditor
                editor.activate('demo')
                editor.perform('install', {'upload_path': 'fixture.zip'})
                editor.save()
                editor.upload(QUrl.fromLocalFile('C:/fixture.zip'), True)
                self.assertEqual(admin.section, 'groups')
                self.assertFalse(editor.writeUncertain)
                with self.assertRaises(PermissionError):
                    editor._execute_request(dict(action='install', upload_path='fixture.zip'), 'demo', {})
                server.assert_not_called()
                pool.add_task.assert_not_called()

    def test_stream_plugin_manager_session_loss_blocks_queued_upload(self):
        admin = self.admin
        pool = Mock(is_stopped=False)
        env_inst.server_api = (*self.identity, 'stream')
        admin._project = 'demo'
        with patch.object(env_inst, 'server_pool', pool), \
                patch.object(tc, 'server_start') as server:
            with patch.object(admin.pluginsEditor, 'activate') as activate:
                admin.select_section('plugins')
                activate.assert_called_once_with('demo')
            editor = admin.pluginsEditor
            editor.reset('demo')
            editor.perform('install', {'upload_path': 'fixture.zip'})
            operation = pool.add_task.call_args.args[0]
            env_inst.server_api = (*self.identity, 'legacy')
            self.application.authentication_changed.emit()
            self.assertEqual(admin.section, 'groups')
            self.assertEqual(editor.document, {})
            with self.assertRaises(PermissionError):
                operation()
            server.assert_not_called()

    def test_backend_non_json_errors_keep_http_status_and_restart_correlation(self):
        app = self.application
        env_inst.server_api = (*self.identity, 'stream')
        backend = ServerControlEditor(app)
        self.addCleanup(backend.shutdown)
        server = Mock(login_ticket='fixture-ticket')
        server.get_server_name.return_value = 'http://fixture.invalid'
        for body in (b'', b'<html>not found</html>', b'[]', b'null'):
            for action in ('load', 'save', 'restart', 'runtime'):
                with self.subTest(body=body, action=action):
                    error = HTTPError('http://fixture.invalid', 404, 'Not Found', {}, BytesIO(body))
                    server.transport.open.side_effect = error
                    args = dict(action=action, expected_revision='r1', document={'workers':'3'},
                                instance_id='old', request_id='request')
                    with patch.object(tc, 'server_start', return_value=server):
                        if action in ('load', 'save'):
                            with self.assertRaisesRegex(RuntimeError, 'HTTP 404: Not Found'):
                                backend._execute_request(args, 'admin', {})
                        else:
                            result = backend._execute_request(args, 'admin', {})
                            self.assertEqual(result['metadata']['runtime'], dict(
                                restart_id='request', restart_error='HTTP 404: Not Found'))
                    self.assertTrue(error.closed)

    def test_native_configuration_hides_stream_pages_and_restores_them(self):
        from tests.frame_configuration_fixture import Surface
        from tests.frame_support_fixture import variant

        surface = Surface('configuration')
        self.addCleanup(surface.close)
        def entries():
            return {row['id'] for row in variant(surface.view.property('entries'))}
        self.assertIn('ai', entries())
        surface.application.setProperty('server_api', 'unknown')
        surface.application.setProperty('is_stream_server', False)
        surface.settle()
        self.assertNotIn('ai', entries())
        self.assertNotIn('database_resources', entries())
        self.assertIn('server', entries())
        surface.case.config.select_page('ai')
        surface.settle()
        self.assertEqual(surface.case.config.current_page, 'ai')
        surface.application.setProperty('server_api', 'legacy')
        surface.settle()
        self.assertEqual(surface.case.config.current_page, 'server')
        surface.application.setProperty('server_api', 'stream')
        surface.application.setProperty('is_stream_server', True)
        surface.settle()
        self.assertIn('ai', entries())
        self.assertFalse(surface.warnings, surface.warnings)

    def test_legacy_uses_polling_without_overwriting_saved_sse_preference(self):
        from tests.test_server_updates import _Application
        from thlib.ui.server_updates import ServerUpdateService

        app = _Application()
        app.is_stream_server = False
        app._settings['network/serverUpdateMode'] = 'sse'
        service = ServerUpdateService(app)
        self.addCleanup(service.stop)
        with patch.object(env_inst, 'server_pool', Mock(is_stopped=False)), \
                patch.object(service, '_start_stream') as stream:
            service.start()
        stream.assert_not_called()
        self.assertEqual(service.update_mode, 'poll')
        self.assertEqual(app._settings['network/serverUpdateMode'], 'sse')
        app.is_stream_server = True
        self.assertEqual(service.update_mode, 'sse')

    def test_native_script_toolbar_keeps_triggers_and_hides_agent_drafts(self):
        from tests.frame_scripts_fixture import Surface
        from tests.profile_ui_responsiveness import frame

        surface = Surface('editor')
        self.addCleanup(surface.dispose)
        with self.assertRaises(AssertionError):
            surface.item(surface.view, 'script_drafts')
        self.assertIsNotNone(surface.item(surface.view, 'script_triggers'))
        surface.controller._application = SimpleNamespace(is_stream_server=True)
        surface.controller.agentDrafts.changed.emit()
        frame(surface.window)
        self.assertIsNotNone(surface.item(surface.view, 'script_drafts'))
        self.assertFalse(surface.warnings, surface.warnings)

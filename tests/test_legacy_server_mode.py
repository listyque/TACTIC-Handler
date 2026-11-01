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
            chat._server = Mock()
            chat._start_files(['fixture.txt'])
            chat._download('fixture')
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

    def test_table_views_custom_urls_and_stream_layout_actions_are_blocked(self):
        from thlib.ui.table.views import TableViewsController
        from thlib.ui.table.services import TableServicesController
        from thlib.ui.custom_urls import open_custom_url
        app = self.application
        pool = Mock(is_stopped=False)
        views = TableViewsController(app, pool)
        services = TableServicesController(app)
        self.addCleanup(services.shutdown)
        app._table_services = services
        for mode in ('legacy', 'unknown'):
            env_inst.server_api = (*self.identity, mode)
            with patch.object(tc, 'server_start') as server:
                views.open(Mock(busy=False, dirty=False))
                views.run(dict(action='read'))
                result = views.load(dict(project='demo'), dict(action='read'), 0)
                self.assertIn('error', result)
                self.assertFalse(open_custom_url(app, 'http://tactic.test/projects/demo/review'))
                owner = services.customLayout
                owner.request_filter_suggestions({}, 'request')
                owner.select_detail()
                owner.save_form('form', {})
                owner.print_report()
                owner.open_result(dict(streamRequired=True), 'Stream page', 'page')
                server.assert_not_called()
                pool.add_task.assert_not_called()
            self.assertFalse(app.window_model.is_window_visible('table_views'))

    def test_legacy_checkin_never_submits_polls_or_cancels_stream_batches(self):
        from thlib.ui.commit_queue import CommitQueueController
        queue = CommitQueueController()
        self.addCleanup(queue.shutdown)
        queue._server_queue = True
        batch = dict(batch_id='retained', project='demo', server=self.identity[0],
                     user=self.identity[1], operations=[], submitted=True)
        queue._server_batches = {'retained': batch}
        pool = Mock(is_stopped=False)
        for mode in ('legacy', 'unknown'):
            env_inst.server_api = (*self.identity, mode)
            with patch.object(env_inst, 'server_pool', pool), \
                    patch.object(env_inst, 'commit_pool', pool), \
                    patch('thlib.server_checkin_queue.request') as request, \
                    patch('thlib.server_checkin_queue.submit_batches') as submit:
                queue._server_api_changed()
                self.assertFalse(queue.serverQueueAvailable)
                self.assertFalse(queue.serverQueue)
                self.assertFalse(queue.busy)
                queue.set_server_queue(True)
                queue._start_server_ids([])
                queue._send_server_batches([batch])
                queue._poll_server_queue()
                queue._cancel_server_batches()
                with self.assertRaises(InterruptedError):
                    queue._server_request(self.identity[0], self.identity[2], 'demo', 'updates', {})
                with self.assertRaises(InterruptedError):
                    queue._submit_server_batches(self.identity[0], self.identity[2], [batch])
                self.assertFalse(queue._server_timer.isActive())
                self.assertEqual(queue._server_batches, {'retained': batch})
                request.assert_not_called()
                submit.assert_not_called()
                pool.add_task.assert_not_called()

    def test_legacy_checkin_uses_local_executor_without_replaying_remote_jobs(self):
        from thlib.ui.commit_queue import CommitQueueController
        queue = CommitQueueController()
        self.addCleanup(queue.shutdown)
        env_inst.server_api = (*self.identity, 'legacy')
        queue._server_queue = True
        queue._executor = Mock()
        reference = dict(state='error', batch_id='server-batch')
        queue._operations = {'local': {}, 'remote': {'_serverQueue': reference}}
        queue.model._records = [
            dict(operationId=key, status='Prepared', canCommit=True)
            for key in ('local', 'remote')
        ]
        with patch.object(queue, '_start_next') as local, \
                patch.object(queue, '_start_server_ids') as remote:
            queue._start_ids(['local', 'remote'])
            self.assertEqual(queue._batch_ids, ['local'])
            local.assert_called_once_with()
            remote.assert_not_called()
            self.assertEqual(queue._operations['remote']['_serverQueue'], reference)

    def test_native_queue_switch_tracks_confirmed_api(self):
        from pathlib import Path
        from PySide6.QtCore import QObject, Property, QUrl
        from PySide6.QtQml import QQmlComponent, QQmlEngine
        from PySide6.QtQuick import QQuickWindow
        from tests.test_columns_table_view import _visual_items
        from tests.profile_ui_responsiveness import frame
        from thlib.ui.commit_queue import CommitQueueController

        class Host(QObject):
            @Property(bool, constant=True)
            def clipboardHasImage(self):
                return False

        queue = CommitQueueController()
        self.addCleanup(queue.shutdown)
        engine = QQmlEngine()
        warnings = []
        engine.warnings.connect(lambda errors: warnings.extend(error.toString() for error in errors))
        host = Host()
        context = engine.rootContext()
        context.setContextProperty('commitQueueController', queue)
        context.setContextProperty('commitQueueModel', queue.model)
        context.setContextProperty('screenshotController', host)
        root = Path(__file__).resolve().parents[1] / 'thlib/ui/qml'
        theme_component = QQmlComponent(engine, QUrl.fromLocalFile(str(root / 'Theme.qml')))
        theme = theme_component.createWithInitialProperties(dict(dark=True))
        component = QQmlComponent(engine, QUrl.fromLocalFile(str(root / 'CommitQueueView.qml')))
        view = component.createWithInitialProperties(dict(theme=theme, width=720, height=760))
        self.assertIsNotNone(view, [error.toString() for error in component.errors()])
        window = QQuickWindow()
        view.setParentItem(window.contentItem())
        window.resize(720, 760)
        window.show()
        try:
            for mode in ('unknown', 'legacy', 'stream', 'legacy'):
                env_inst.server_api = (*self.identity, mode)
                queue._server_api_changed()
                frame(window)
                switches = [item for item in _visual_items(view)
                            if item.objectName() == 'commitQueueServerSwitch' and item.isVisible()]
                self.assertEqual(bool(switches), mode == 'stream')
            self.assertEqual(warnings, [])
        finally:
            window.close()
            view.setParentItem(None)
            view.deleteLater()
            engine.collectGarbage()

    def test_legacy_search_skips_stream_item_metadata_and_cached_layouts(self):
        from thlib.ui.controllers.search_runtime import SearchRuntimeMixin
        env_inst.server_api = (*self.identity, 'legacy')
        value = ({'A': Mock()}, dict(itemLayout={'requiresStream': True}))
        with patch.object(server_cache, 'token', return_value=None), \
                patch.object(server_cache, 'read_entry', return_value=None), \
                patch.object(tc, 'get_snapshots_updates_list', return_value=[]), \
                patch.object(tc, 'get_sobjects', return_value=value), \
                patch.object(tc, 'server_start') as server, \
                patch.object(SearchRuntimeMixin, '_search_stype', return_value=Mock()), \
                patch.object(SearchRuntimeMixin, '_resolve_category_labels'):
            objects, info, _stype = SearchRuntimeMixin._query_sobjects(
                'demo/asset', 'demo', (), [], 50, 0, item_view='cards_example')
            self.assertEqual(objects, list(value[0].values()))
            self.assertNotIn('itemLayout', info)
            server.assert_not_called()

    def test_api_change_stops_sse_without_overwriting_saved_preference(self):
        from thlib.ui.server_updates import ServerUpdateService
        app = self.application
        app._settings['network/serverUpdateMode'] = 'sse'
        service = ServerUpdateService(app)
        self.addCleanup(service.stop)
        stream = Mock()
        service._stream, service._running, service._busy = stream, True, True
        service._session = self.identity
        env_inst.server_api = (*self.identity, 'legacy')
        with patch.object(env_inst, 'logins', {'supervisor': object()}), \
                patch.object(service, 'poll') as poll:
            service.sync_authentication()
            stream.cancel.assert_called_once_with()
            self.assertIsNone(service._stream)
            self.assertEqual(service.update_mode, 'poll')
            self.assertEqual(service._update_mode, 'sse')
            poll.assert_called_once_with()

    def test_file_workspace_drops_stream_state_on_api_change(self):
        from thlib.ui.file_workspace import FileWorkspaceController
        app = self.application
        env_inst.server_api = (*self.identity, 'legacy')
        owner = FileWorkspaceController(app)
        self.addCleanup(owner.shutdown)
        owner._enabled = True
        with patch.object(owner, '_start_read') as read, \
                patch.object(tc, 'server_start') as server:
            owner.action('refresh', {})
            read.assert_not_called()
            server.assert_not_called()
            app.authentication_changed.emit()
            self.assertFalse(owner.enabled)

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

"""Native session authority, admin entry points and diagnostic modal ownership."""

import json
import os
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('QT_QUICK_BACKEND', 'software')

from PySide6.QtGui import QGuiApplication

from thlib.environment import env_inst, env_mode, env_server
from thlib.ui.administration import AdministrationController
from thlib.ui.user import UserController
from thlib.ui.controller import ApplicationController
from thlib.ui.sidebar_editor import SidebarEditorController
from thlib.ui.workspace_models.windows import FloatingWindowModel


class AdministrationAccessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def setUp(self):
        directory = self.enterContext(TemporaryDirectory())
        self.enterContext(patch.object(env_mode, 'current_path', directory))
        self.enterContext(patch.object(env_server, 'get_server', return_value='http://tactic.test'))
        self.login_name = self.enterContext(patch.object(env_server, 'get_user', return_value='supervisor'))
        self.enterContext(patch.object(env_server, 'get_ticket', return_value='test-ticket'))
        self.application = ApplicationController()
        self.addCleanup(self.application.shutdown)
        self.users = UserController(self.application)
        self.enterContext(patch.object(type(self.users), 'canManageUsers', return_value=True,
                                       new_callable=unittest.mock.PropertyMock))
        self.admin = AdministrationController(self.application, self.users)
        self.addCleanup(self.admin.shutdown)
        self.sidebar = SidebarEditorController(self.application, self.users)
        self.enterContext(patch.object(self.admin, 'reload'))
        self.rpc = self.enterContext(patch('thlib.tactic_classes.execute_procedure_serverside'))

    def bootstrap(self, *, native_admin):
        project = SimpleNamespace(
            get_code=lambda: 'demo', get_title=lambda: 'Demo',
            get_info=lambda: {}, is_template=lambda: False, is_builtin=lambda: False,
        )
        login = SimpleNamespace(
            get_display_name=lambda: 'Administrator',
            get_info=lambda: {'__is_admin__': native_admin},
        )
        with patch('thlib.tactic_classes.get_server_updates', return_value={}), patch.object(
                env_inst, 'logins', {self.login_name.return_value: login}), patch.object(
                self.application, '_load_projects', return_value=[project]), patch.object(
                self.application, '_prepare_project_selection',
                return_value=('demo', 'Demo', [], project)):
            result = self.application._bootstrap_server_task('demo')
        self.application._bootstrap_request_id = 'current-request'
        with patch.object(self.application, '_apply_selected_project'), patch.object(
                self.application.project_model, 'replace'), patch.object(
                self.application, '_write_search_cache_config'):
            self.application._async_bootstrap_result((*result, 'current-request'))

    def test_supervisor_is_not_admin_and_cannot_open_any_admin_entry_point(self):
        self.bootstrap(native_admin=False)
        self.assertFalse(self.application.can_administer)
        self.assertFalse(self.admin.canManage)
        self.assertTrue(self.sidebar.canEdit)
        self.assertFalse(self.sidebar.canManageGroups)
        self.assertNotIn('show_administration', [
            action.get('command') for action in self.application.menu_actions('configuration')])
        self.application._registry.invoke('show_administration')
        self.sidebar.open_group_manager()
        self.admin.select_project('demo')
        self.admin.select_section('schema')
        self.admin.schemaEditor.activate('demo')
        self.application.window_model.show_window('administration')
        self.assertFalse(self.application.window_model.is_window_visible('administration'))
        self.assertFalse(self.admin.schemaEditor.busy)
        self.rpc.assert_not_called()

    def test_native_admin_flag_not_login_or_group_label_controls_access(self):
        self.bootstrap(native_admin=True)
        self.assertTrue(self.application.can_administer)
        self.assertIn('show_administration', [
            action.get('command') for action in self.application.menu_actions('configuration')])
        self.admin.open()
        self.assertTrue(self.application.window_model.is_window_visible('administration'))
        self.login_name.return_value = 'admin'
        self.assertFalse(self.application.can_administer)
        self.bootstrap(native_admin=False)
        self.assertFalse(self.application.can_administer)

    def test_access_loss_closes_admin_and_cancels_pending_editors(self):
        self.bootstrap(native_admin=True)
        self.admin.open()
        worker = Mock()
        self.admin.schemaEditor._worker = worker
        self.admin.schemaEditor._document = {'xml': '<schema/>'}
        self.application._set_server_state('authentication', 'Sign in')
        self.assertFalse(self.admin.canManage)
        self.assertFalse(self.application.window_model.is_window_visible('administration'))
        worker.cancel.assert_called_once()
        self.assertEqual(self.admin.schemaEditor.document, {})
        self.application._set_server_state('online', 'Ping succeeded')
        self.assertFalse(self.application.can_administer)

    def test_cached_login_metadata_does_not_grant_admin_access(self):
        login = SimpleNamespace(get_info=lambda: {'__is_admin__': True})
        with patch.object(env_inst, 'logins', {'supervisor': login}):
            self.application._set_server_state('online', 'Restored')
            self.assertFalse(self.application.can_administer)


class AdministrationBootstrapQueryTests(unittest.TestCase):
    def test_authority_is_only_attached_to_the_authenticated_native_login(self):
        from thlib import tactic_query

        class Login:
            def __init__(self, name):
                self.name = name

            def get_data(self):
                return {'code': self.name, 'login': self.name}

        class Search:
            def __init__(self, stype):
                self.stype = stype

            def add_filters(self, *_args, **_kwargs):
                pass

            def add_relationship_filters(self, *_args, **_kwargs):
                pass

            def add_op_filters(self, *_args):
                pass

            def get_sobjects(self):
                return [Login('operator'), Login('admin')] if self.stype == 'sthpw/login' else []

        native_admin = Mock(return_value=True)
        modules = {
            'pyasm': SimpleNamespace(),
            'pyasm.search': SimpleNamespace(Search=Search, SearchKey=SimpleNamespace(
                get_by_sobjects=lambda rows, **_: [row.name for row in rows])),
            'pyasm.biz': SimpleNamespace(
                Project=SimpleNamespace(get_user_projects=lambda: []),
                Snapshot=SimpleNamespace(get_files_dict_by_snapshots=lambda _: {})),
            'pyasm.common': SimpleNamespace(Environment=SimpleNamespace(get_security=lambda: SimpleNamespace(
                get_user_name=lambda: 'operator', is_admin=native_admin))),
        }
        with patch.dict('sys.modules', modules):
            for allowed in (True, False):
                native_admin.return_value = allowed
                result = json.loads(tactic_query.get_projects_and_logins(current_login='admin'))
                self.assertEqual([row['__is_admin__'] for row in result['logins']], [allowed, False])


class DiagnosticWindowOwnershipTests(unittest.TestCase):
    def test_error_nests_under_topmost_modal_and_keeps_parent_on_repeated_errors(self):
        model = FloatingWindowModel({})
        model.show_window('sidebar_editor')
        model.show_child_window('administration', 'sidebar_editor')
        model.show_window('error')
        self.assertEqual(model._parent_windows['error'], 'administration')
        model.show_window('error')
        self.assertEqual(model._parent_windows['error'], 'administration')
        model.close_window('error')
        model.show_window('debug_log')
        self.assertEqual(model._parent_windows['debug_log'], 'administration')
        model.show_window('help')
        self.assertEqual(model._parent_windows['help'], 'administration')
        model.close_window('administration')
        model.show_window('error')
        self.assertEqual(model._parent_windows['error'], 'sidebar_editor')
        model.close_window('sidebar_editor')
        model.show_window('error')
        self.assertNotIn('error', model._parent_windows)


if __name__ == '__main__':
    unittest.main()

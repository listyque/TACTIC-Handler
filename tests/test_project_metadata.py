"""Native project hydration must not depend on a production workflow."""

from concurrent.futures import ThreadPoolExecutor
import json
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from thlib import server_cache, tactic_classes as tc
from thlib.environment import env_inst, env_mode, env_server
from thlib.ui.controller import ApplicationController
from thlib.ui.models import NavigationModel
from tests.qt_application import gui_test_application


def metadata(*, schema='', pipelines=(), with_types=True, with_views=True):
    return {
        'schema': [{'schema': schema}] if schema else [],
        'pipelines': list(pipelines),
        'stypes': [{
            'code': 'sthpw/login', 'title': 'Users', 'color': '#123456',
            'table_name': 'login', 'column_info': {'login': {'data_type': 'text'}},
        }] if with_types else [],
        'views': [{
            'search_type': 'SideBarWdg', 'view': 'definition',
            'config': '<config><definition><element name="users" title="Users">'
                      '<display class="LinkWdg"/><search_type>sthpw/login</search_type>'
                      '</element></definition></config>',
        }, {
            'search_type': 'SideBarWdg', 'view': 'tactic_handler',
            'config': '<config><tactic_handler><element name="users"/>'
                      '</tactic_handler></config>',
        }] if with_views else [],
    }


class ProjectMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def setUp(self):
        directory = self.enterContext(TemporaryDirectory())
        self.enterContext(patch.object(env_mode, 'current_path', directory))
        self.enterContext(patch.object(env_mode, 'get_mode', return_value='api_server'))
        self.enterContext(patch.object(env_inst, 'projects', {}))
        self.enterContext(patch.object(env_inst, 'logins', {}))
        self.enterContext(patch.object(env_inst, 'current_project', None))
        self.rpc = self.enterContext(patch.object(tc, 'execute_procedure_serverside'))

    @staticmethod
    def project(code):
        return tc.Project({'code': code, 'name': code, 'type': ''})

    def load(self, project, payload):
        self.rpc.return_value = json.dumps(payload)
        return project.query_search_types(force=True)

    def test_views_exist_before_metadata_loading_without_an_implicit_rpc(self):
        project = self.project('sthpw')
        views = project.get_config_views()
        self.assertIsInstance(views, tc.ViewsConfig)
        self.assertIs(views.project, project)
        self.assertEqual(views.get_view('SideBarWdg'), [])
        self.assertFalse(views.has_definition())
        self.rpc.assert_not_called()

    def test_catalog_and_sidebar_load_without_schema_or_pipelines(self):
        for code in ('admin', 'sthpw', 'demo'):
            with self.subTest(project=code):
                project = self.project(code)
                env_inst.projects[code] = project
                types = self.load(project, metadata())
                self.assertEqual(list(types), ['sthpw/login'])
                self.assertIs(types['sthpw/login'].project, project)
                self.assertEqual(project.get_workflow().get_all_pipelines(), {})
                login = SimpleNamespace(check_security=lambda **_: 'allow')
                entries = NavigationModel.build_project_entries(project, login)
                self.assertEqual([entry.key for entry in entries], ['sthpw/login@users'])
                self.assertEqual(entries[0].title, 'Users')

    def test_sthpw_preserves_native_schema_and_pipelines(self):
        project = self.project('sthpw')
        schema = (
            '<schema><search_type name="sthpw/login"/>'
            '<search_type name="sthpw/login_in_group"/>'
            '<connect from="sthpw/login_in_group" to="sthpw/login" '
            'relationship="code"/></schema>'
        )
        pipeline = {'code': 'accounts', 'search_type': 'sthpw/login',
                    'pipeline': '<pipeline><process name="review"/></pipeline>',
                    'stypes_processes': []}
        types = self.load(project, metadata(schema=schema, pipelines=[pipeline]))
        self.assertIsNotNone(types['sthpw/login'].get_schema())
        self.assertEqual(types['sthpw/login'].get_schema().children[0]['from'],
                         'sthpw/login_in_group')
        self.assertEqual(list(types['sthpw/login'].get_pipeline()), ['accounts'])
        self.assertEqual(list(project.get_workflow().get_all_pipelines()), ['sthpw/login'])

    def test_schema_without_pipelines_is_not_discarded(self):
        project = self.project('demo')
        types = self.load(project, metadata(
            schema='<schema><search_type name="sthpw/login"/></schema>',
        ))
        self.assertIsNotNone(types['sthpw/login'].get_schema())
        self.assertIsNone(types['sthpw/login'].get_pipeline())
        self.assertTrue(project.get_config_views().has_definition())

    def test_pipelines_are_bound_by_search_type_without_a_schema_node(self):
        project = self.project('demo')
        pipeline = {'code': 'accounts', 'search_type': 'sthpw/login'}
        types = self.load(project, metadata(pipelines=[pipeline]))
        self.assertEqual(list(types['sthpw/login'].get_pipeline()), ['accounts'])

    def test_empty_catalog_is_loaded_once_and_refresh_replaces_old_metadata(self):
        project = self.project('demo')
        self.load(project, metadata())
        empty = self.load(project, metadata(with_types=False, with_views=False))
        self.assertEqual(empty, {})
        self.assertIs(project.get_stypes(), empty)
        self.assertIs(project.get_stypes(), empty)
        self.assertFalse(project.get_config_views().has_definition())
        self.assertEqual(self.rpc.call_count, 2)

    def test_cached_metadata_without_workflow_is_hydrated_without_network(self):
        project = self.project('admin')
        with (
            patch.object(env_mode, 'get_mode', return_value='standalone'),
            patch.object(server_cache, 'read_entry', return_value=json.dumps(metadata())),
        ):
            types = project.query_search_types(cache_only=True)
        self.assertEqual(list(types), ['sthpw/login'])
        self.assertTrue(project.get_config_views().has_definition())
        self.rpc.assert_not_called()

    def test_transport_error_remains_visible_and_does_not_replace_loaded_metadata(self):
        project = self.project('sthpw')
        types = self.load(project, metadata())
        views = project.get_config_views()
        self.rpc.side_effect = RuntimeError('server metadata unavailable')
        with self.assertRaisesRegex(RuntimeError, 'server metadata unavailable'):
            project.query_search_types(force=True)
        self.assertIs(project.get_stypes(), types)
        self.assertIs(project.get_config_views(), views)

    def test_builtin_project_selection_publishes_hydrated_models_on_gui_thread(self):
        self.enterContext(patch.object(env_inst, 'exit_pools'))
        self.enterContext(patch.object(env_server, 'get_server_presets', return_value={}))
        controller = ApplicationController()
        self.addCleanup(controller.shutdown)
        changed = Mock()
        controller.project_changed.connect(changed)
        for code in ('admin', 'sthpw'):
            with self.subTest(project=code):
                project = self.project(code)
                env_inst.projects[code] = project
                self.rpc.return_value = json.dumps(metadata(with_views=False))
                with ThreadPoolExecutor(max_workers=1) as pool:
                    prepared = pool.submit(
                        controller._prepare_project_selection, code, code,
                    ).result(timeout=5)
                controller._apply_selected_project(*prepared)
                self.assertEqual(controller._current_project_code, code)
                self.assertIs(controller.workspace_state._project, project)
                self.assertEqual(controller.workspace_state.search_type_model.records(),
                                 [{'label': 'sthpw/login'}])
                self.assertEqual(controller.navigation_model.rowCount(), 0)
                changed.assert_called_with(code, code)
        self.assertEqual(self.rpc.call_count, 2)


if __name__ == '__main__':
    unittest.main()

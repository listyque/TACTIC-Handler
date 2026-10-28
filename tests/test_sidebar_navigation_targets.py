"""Sidebar element names are identities, not implicit Search Types."""

from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from thlib import tactic_classes as tc
from thlib.environment import cfg_controls, env_inst, env_mode, env_server
from thlib.ui.controller import ApplicationController
from thlib.ui.models import NavigationModel
from tests.qt_application import gui_test_application


UNCONFIGURED_KEY = 'Column_Manager@Column_Manager'
SEARCH_KEY = 'config/naming@naming'


def sidebar_project(*, with_search=True, handler_view=False, display_options=''):
    # This is the actual shape of the reported admin sidebar entry. It has no
    # search_type, widget_key or class_name; its name must never become a query.
    unconfigured = (
        '<element name="Column_Manager" title="Column Manager">'
        '<display class="LinkWdg"/></element>'
    )
    search = (
        '<element name="naming" title="Naming"><display class="LinkWdg">' + display_options + '</display>'
        '<search_type>config/naming</search_type></element>'
    ) if with_search else ''
    project = tc.Project({'code': 'admin', 'name': 'Admin', 'type': ''})
    project.get_all_search_types([], [], '', [{
        'search_type': 'SideBarWdg', 'view': 'definition',
        'config': '<config><definition>' + unconfigured + search + '</definition></config>',
    }, {
        'search_type': 'SideBarWdg',
        'view': 'tactic_handler' if handler_view else 'project_view',
        'config': '<config><view>' + unconfigured + search + '</view></config>',
    }])
    return project


def sidebar_entries(project):
    return NavigationModel.build_project_entries(
        project, SimpleNamespace(check_security=lambda **_: 'allow'),
    )


class SidebarNavigationTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def setUp(self):
        directory = self.enterContext(TemporaryDirectory())
        self.enterContext(patch.object(env_mode, 'current_path', directory))
        self.enterContext(patch.object(env_inst, 'projects', {}))
        self.enterContext(patch.object(env_inst, 'logins', {}))
        self.enterContext(patch.object(env_inst, 'current_project', None))
        self.enterContext(patch.object(env_inst, 'exit_pools'))
        self.enterContext(patch.object(env_server, 'get_server_presets', return_value={}))
        self.enterContext(patch.object(cfg_controls, 'get_checkin_out_projects', return_value={}))
        self.enterContext(patch.object(cfg_controls, 'set_checkin_out_projects'))
        self.rpc = self.enterContext(patch.object(
            tc, 'execute_procedure_serverside',
            side_effect=AssertionError('Opening a sidebar must not issue this RPC'),
        ))
        self.controller = ApplicationController()
        self.addCleanup(self.controller.shutdown)
        self.enterContext(patch.object(
            self.controller._performance, 'after_feedback', side_effect=lambda callback: callback(),
        ))
        self.shown_targets = []
        self.enterContext(patch.object(
            self.controller, '_show_or_load_tab',
            side_effect=lambda _tab: self.shown_targets.append(
                self.controller._current_section().search_type),
        ))

    def tearDown(self):
        self.app.processEvents()

    def test_both_sidebar_views_keep_unconfigured_link_unavailable(self):
        for handler_view in (False, True):
            with self.subTest(handler_view=handler_view):
                entries = sidebar_entries(sidebar_project(handler_view=handler_view))
                self.assertEqual([entry.key for entry in entries], [UNCONFIGURED_KEY, SEARCH_KEY])
                self.assertFalse(entries[0].available)
                self.assertEqual(entries[0].search_type, '')
                self.assertTrue(entries[1].available)
                self.assertEqual(entries[1].search_type, 'config/naming')
        self.rpc.assert_not_called()

    def test_legacy_view_panel_defaults_to_table_and_keeps_explicit_modes(self):
        for handler, options, expected in (
            (False, '<widget_key>view_panel</widget_key>', 'table'),
            (False, '', 'table'),
            (False, '<view_mode>continious</view_mode>', 'continious'),
            (False, '<widget_key>tile_layout</widget_key>', 'tiles'),
            (True, '<widget_key>view_panel</widget_key>', ''),
        ):
            with self.subTest(handler=handler, options=options):
                project = sidebar_project(handler_view=handler, display_options=options)
                entry = next(row for row in sidebar_entries(project) if row.key == SEARCH_KEY)
                self.assertEqual(entry.view_mode, expected)

    def test_custom_layout_sidebar_keeps_its_view_and_opens_the_native_owner(self):
        project=sidebar_project(with_search=False)
        entry='<element name="planner" title="Planner"><display class="LinkWdg"><widget_key>custom_layout</widget_key><view>planner_layout</view></display></element>'
        configs=project.get_config_views().config_dict
        configs[0]['config']='<config><definition>'+entry+'</definition></config>'
        configs[1]['config']='<config><project_view>'+entry+'</project_view></config>'
        configs.append(dict(search_type='CustomLayoutWdg',view='planner_layout',config='<config><planner_layout><html><element name="table"><display class="tactic.ui.panel.ViewPanelWdg"><search_type>config/naming</search_type><view>table</view></display></element></html></planner_layout></config>'))
        entries=sidebar_entries(project)
        self.assertEqual(len(entries),1)
        self.assertEqual((entries[0].search_type,entries[0].layout_view,entries[0].table_view),('config/naming','planner_layout','table'))
        self.controller.navigation_model.replace(entries)
        self.controller._table_services=SimpleNamespace(customLayout=Mock(),workspaceLayout=Mock())
        self.controller.select_navigation(entries[0].key,entries[0].title,entries[0].command)
        tab=self.controller._current_tab()
        self.assertEqual(tab.layout_view,'planner_layout')
        from thlib.ui.controllers.navigation import NavigationMixin
        sections_changed = []
        self.controller.section_state_changed.connect(lambda: sections_changed.append(True))
        NavigationMixin._show_or_load_tab(self.controller,tab)
        self.assertEqual(sections_changed, [True], 'Main workspace visibility must be notified when a custom page opens')
        self.controller._table_services.workspaceLayout.open_view.assert_called_once_with('planner_layout','Planner',tab.tab_id,search_key='')
        self.controller._table_services.customLayout.open_view.assert_not_called()

    def test_configured_empty_handler_sidebar_does_not_show_web_sidebar(self):
        project = sidebar_project()
        project.get_config_views().config_dict.append({
            "search_type": "SideBarWdg",
            "view": "tactic_handler",
            "config": "<config/>",
            "login": "",
        })

        self.assertEqual(sidebar_entries(project), [])

    def test_project_without_sidebar_lists_its_native_search_types(self):
        for code in ('cafe', 'admin', 'sthpw'):
            for config in (
                [],
                [{'search_type': 'cafe/item', 'view': 'definition', 'config': '<config/>'}],
                [{'search_type': 'SideBarWdg', 'view': 'project_view',
                  'config': '<config><project_view><element name="_home" title="Examples"/></project_view></config>'}],
            ):
                with self.subTest(project=code, config=config):
                    project = tc.Project({'code': code, 'name': 'Cafe', 'type': 'cafe'})
                    project.get_all_search_types([], [], '', config)
                    stype = Mock()
                    stype.get_info.return_value = {'title': 'Menu items'}
                    stype.get_stype_color.return_value = '#778899'
                    project.stypes = {'cafe/item': stype}
                    entries = sidebar_entries(project)
                    self.assertEqual([entry.search_type for entry in entries], ['cafe/item'])
                    self.assertEqual(entries[0].title, 'Menu items')
                    self.assertEqual(entries[0].command, 'open_sidebar_item')
                    self.controller.navigation_model.replace(entries)
                    self.controller._current_project_code = code
                    self.controller.select_navigation(entries[0].key, entries[0].title, entries[0].command)
                    self.assertEqual(self.shown_targets[-1], 'cafe/item')
                    self.controller._sessions.clear()
        self.rpc.assert_not_called()

    def test_file_project_keeps_object_tabs_and_filters_managed_file_tables(self):
        from thlib.ui.file_workspace import FileWorkspaceController

        project = sidebar_project()
        project.info.update(code='files', type='file_project')
        env_inst.projects['files'] = project
        workspace = FileWorkspaceController(self.controller)
        self.addCleanup(workspace.shutdown)
        saved = {'files': {'stypes_list': [SEARCH_KEY, 'file_project/depot@file_project/depot'],
                           'active_stype': SEARCH_KEY}}
        with (patch.object(env_inst, 'get_current_login_object', return_value=SimpleNamespace(check_security=lambda **kwargs:'allow')),
              patch.object(project, 'query_search_types', return_value=True) as metadata,
              patch.object(cfg_controls, 'get_checkin_out_projects', return_value=saved),
              patch.object(workspace, 'action') as action,
              patch.object(self.controller, 'open_window')):
            prepared = self.controller._prepare_project_selection('files', 'Files')
            self.controller._apply_cached_project_shell(*prepared)
            self.assertTrue(workspace.enabled)
            action.assert_not_called()
            self.controller._apply_selected_project(*prepared)
            action.assert_called_once_with('refresh', {})
            self.assertEqual(list(self.controller._sessions), [SEARCH_KEY])
            self.assertEqual(self.shown_targets, ['config/naming'])
            metadata.assert_called_once()
        self.rpc.assert_not_called()

    def test_file_project_administrator_sees_managed_search_types_with_empty_sidebar(self):
        project = tc.Project({'code':'files','type':'file_project'})
        types = [{'code':'file_project/'+name,'search_type':'file_project/'+name,'title':name.title(),'table_name':name,'color':'','__record_read__':{'command':'native.reader','available':True}}
                 for name in ('depot','stream','workspace','change','page','blob','chunk','version','checkout','sync')]
        project.get_all_search_types(types, [], '', [{'search_type':'SideBarWdg','view':'tactic_handler',
                                                     'config':'<config><tactic_handler/></config>'}])
        login = SimpleNamespace(get_info=lambda:{'__is_admin__':True}, check_security=lambda **_:'allow')
        entries = NavigationModel.build_project_entries(project, login)
        env_inst.projects['files'] = project
        self.controller._current_project_code = 'files'
        self.assertEqual(len(entries),10)
        self.assertEqual(entries[0].search_type,'file_project/depot')
        self.controller.navigation_model.replace(entries)
        self.controller.select_navigation(entries[0].key, entries[0].title, entries[0].command)
        self.assertEqual(self.shown_targets,['file_project/depot'])
        self.rpc.assert_not_called()

    def test_file_project_mode_is_ready_when_controller_starts_after_cached_project(self):
        from thlib.ui.file_workspace import FileWorkspaceController
        env_inst.projects['files'] = tc.Project({'code':'files','type':'file_project'})
        self.controller._current_project_code = 'files'
        workspace = FileWorkspaceController(self.controller)
        self.addCleanup(workspace.shutdown)
        self.assertTrue(workspace.enabled)
        self.controller.open_window('commit_queue')
        self.assertTrue(self.controller.dock_model.is_panel_presented('commit_queue'))
        self.assertFalse(self.controller.window_model.is_window_visible('commit_queue'))

    def test_direct_entry_cannot_infer_search_type_from_sidebar_name(self):
        entries = sidebar_entries(sidebar_project())
        self.controller.navigation_model.replace(entries)
        with self.assertRaisesRegex(ValueError, 'Search Type'):
            self.controller._create_section(UNCONFIGURED_KEY, 'Column Manager')
        self.assertEqual(self.controller._sessions, {})
        self.rpc.assert_not_called()

    def test_deactivation_clears_workspace_but_keeps_project_catalog_and_login(self):
        project = sidebar_project()
        env_inst.projects['admin'] = project
        self.controller._apply_selected_project('admin', 'Admin', sidebar_entries(project), project)
        self.controller.select_navigation(SEARCH_KEY, 'Naming', 'open_sidebar_item')
        self.controller._project_request_id = 'late-project-request'
        self.controller.deactivate_project()
        self.assertEqual(self.controller.current_project_code, '')
        self.assertEqual(self.controller.current_project_title, '')
        self.assertIsNone(env_inst.current_project)
        self.assertIs(env_inst.projects['admin'], project)
        self.assertEqual(self.controller.navigation_model.rowCount(), 0)
        self.assertEqual(self.controller._sessions, {})
        self.assertEqual(self.controller._settings['server/currentProject'], '')
        self.assertEqual(self.controller._project_request_id, '')
        self.assertIsNone(self.controller.workspace_state._project)
        self.controller._async_project_result(('admin', 'Admin', sidebar_entries(project), project, 'late-project-request'))
        self.assertEqual(self.controller.current_project_code, '')
        self.rpc.assert_not_called()

    def test_unavailable_and_stale_clicks_do_not_create_or_activate_searches(self):
        self.controller.navigation_model.replace(sidebar_entries(sidebar_project()))
        notify = Mock()
        self.controller.notification_changed.connect(notify)
        for key in (UNCONFIGURED_KEY, 'removed@removed'):
            self.controller.select_navigation(key, 'Column Manager', 'open_sidebar_item')
            self.app.processEvents()
            self.assertEqual(self.controller._sessions, {})
            self.assertEqual(self.shown_targets, [])
        self.assertEqual(notify.call_count, 2)
        self.rpc.assert_not_called()

    def test_project_open_and_cache_restore_skip_unconfigured_saved_tabs(self):
        for cached in (False, True):
            for with_search in (False, True):
                with self.subTest(cached=cached, with_search=with_search):
                    project = sidebar_project(with_search=with_search)
                    env_inst.projects['admin'] = project
                    entries = sidebar_entries(project)
                    saved = {
                        'admin': {'stypes_list': [UNCONFIGURED_KEY],
                                  'active_stype': UNCONFIGURED_KEY},
                    }
                    self.controller._search_cache['admin'] = {'sections': [{
                        'entry_key': UNCONFIGURED_KEY, 'tabs': [{
                            'tab_id': 'old-tab', 'quick_filter_personalized': False,
                        }],
                    }]}
                    with patch.object(cfg_controls, 'get_checkin_out_projects', return_value=saved):
                        apply = (self.controller._apply_cached_project_shell if cached
                                 else self.controller._apply_selected_project)
                        apply('admin', 'Admin', entries, project)
                        self.app.processEvents()
                    self.assertEqual(self.controller._current_project_code, 'admin')
                    self.assertEqual(list(self.controller._sessions), [])
                    self.assertNotIn('Column_Manager', self.shown_targets)
        self.rpc.assert_not_called()

    def test_empty_project_workspace_stays_empty_until_sidebar_selection(self):
        project = sidebar_project()
        env_inst.projects['admin'] = project
        entries = sidebar_entries(project)
        for apply in (
            self.controller._apply_cached_project_shell,
            self.controller._apply_selected_project,
        ):
            with self.subTest(apply=apply.__name__):
                self.controller._current_page_title = 'Naming / Last search'
                apply('admin', 'Admin', entries, project)
                self.app.processEvents()
                self.assertEqual(self.controller.current_section_key, '')
                self.assertEqual(self.controller.current_page_title, '')
                self.assertEqual(self.controller.section_model.rowCount(), 0)
                self.assertEqual(self.shown_targets, [])

        self.controller.select_navigation(SEARCH_KEY, 'Naming', 'open_sidebar_item')
        self.controller._current_page_key = SEARCH_KEY
        self.controller._current_page_title = 'Naming / Last search'
        self.controller.close_section(SEARCH_KEY)
        self.app.processEvents()
        self.assertEqual(self.controller.current_section_key, '')
        self.assertEqual(self.controller.section_model.rowCount(), 0)
        self.assertEqual(self.controller.current_page_title, '')

    def test_configured_sidebar_click_keeps_explicit_search_target(self):
        self.controller.navigation_model.replace(sidebar_entries(sidebar_project()))
        self.controller.select_navigation(SEARCH_KEY, 'Naming', 'open_sidebar_item')
        self.app.processEvents()
        self.assertEqual(self.controller._current_section().search_type, 'config/naming')
        self.assertEqual(self.shown_targets, ['config/naming'])
        self.rpc.assert_not_called()

    def test_direct_search_navigation_without_sidebar_entry_is_unchanged(self):
        section = self.controller._create_section('config/naming', 'Naming')
        self.assertEqual(section.search_type, 'config/naming')
        self.rpc.assert_not_called()

    def test_direct_search_keeps_the_matching_sidebar_initial_mode(self):
        self.controller.navigation_model.replace(sidebar_entries(sidebar_project(display_options='<widget_key>view_panel</widget_key>')))
        section = self.controller._create_section('config/naming', 'Naming')
        self.assertEqual(section.tabs[0].view_mode, 'table')


if __name__ == '__main__':
    unittest.main()

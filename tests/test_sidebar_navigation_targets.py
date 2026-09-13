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


def sidebar_project(*, with_search=True, handler_view=False):
    # This is the actual shape of the reported admin sidebar entry. It has no
    # search_type, widget_key or class_name; its name must never become a query.
    unconfigured = (
        '<element name="Column_Manager" title="Column Manager">'
        '<display class="LinkWdg"/></element>'
    )
    search = (
        '<element name="naming" title="Naming"><display class="LinkWdg"/>'
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

    def test_direct_entry_cannot_infer_search_type_from_sidebar_name(self):
        entries = sidebar_entries(sidebar_project())
        self.controller.navigation_model.replace(entries)
        with self.assertRaisesRegex(ValueError, 'Search Type'):
            self.controller._create_section(UNCONFIGURED_KEY, 'Column Manager')
        self.assertEqual(self.controller._sessions, {})
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
                    self.assertEqual(list(self.controller._sessions),
                                     [SEARCH_KEY] if with_search else [])
                    self.assertNotIn('Column_Manager', self.shown_targets)
        self.rpc.assert_not_called()

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


if __name__ == '__main__':
    unittest.main()

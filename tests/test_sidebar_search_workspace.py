"""Sidebar actions reuse actual Search tab and Quick Filter editor ownership."""

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PySide6.QtCore import QCoreApplication, QEvent

from thlib.ui.models import NavigationEntry
from thlib.ui.quick_filter_editor import QuickFilterEditorController
from thlib.ui.sidebar_editor import SidebarEditorController
from tests import test_process_menu_latency as workspace
from tests.test_quick_filters import _Stype


class SidebarSearchWorkspaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        workspace.ProcessMenuLatencyTests.setUpClass()

    def setUp(self):
        self.fixture = workspace.ProcessMenuLatencyTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.application = self.fixture.controller
        self.users = SimpleNamespace(canManageUsers=True)
        self.entry = NavigationEntry(
            key="demo/asset@my_tasks", title="My tasks", glyph="tasks", group="Project",
            search_type="demo/asset", command="open_sidebar_item",
            search_view="link_search:ready:demo/asset",
            filter_records=({
                "column": "category", "relation": "is", "value": "props",
                "enabled": True,
            },),
        )
        self.application.navigation_model.replace([self.entry])
        self.sidebar = SidebarEditorController(self.application, self.users)
        self.sidebar._loaded(("demo", "Demo", object(), [{
            "code": "CONFIG1", "search_type": "SideBarWdg", "view": "definition",
            "config": """<config><element name="my_tasks" title="My tasks">
                <display class="LinkWdg"/><search_type>demo/asset</search_type>
                <search_view>link_search:ready:demo/asset</search_view>
                </element></config>""",
        }]))
        self.sidebar.select_entry(0)
        self.filters = QuickFilterEditorController(self.application, self.users)
        self.filters._loaded[("demo", "demo/asset", self.entry.key)] = {}
        stype = _Stype()
        stype.get_code = lambda: "demo/asset"
        self.application._active_stype = lambda: stype
        self.enterContext(patch.object(self.application, "request_quick_filter_data"))
        self.enterContext(patch.object(self.application, "_show_or_load_tab"))
        self.enterContext(patch.object(self.application, "_load_tab"))
        self.enterContext(
            patch.object(self.application, "_request_sidebar_presets")
        )

    def tearDown(self):
        # Flush queued model and deferred-deletion work while this test still
        # owns the mocked query boundary.
        QCoreApplication.processEvents()
        self.filters.deleteLater()
        self.sidebar.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def test_quick_filters_wait_for_exact_custom_sidebar_scope(self):
        previous = self.application._current_section()
        self.sidebar.open_search()
        self.assertEqual(self.application.current_section_key, self.entry.key)
        self.assertFalse(self.filters._session_open)
        self.assertEqual(self.sidebar.previewSurfaces.rowCount(), 1)
        self.application.window_model.show_window("quick_filter_editor")
        self.assertTrue(self.filters._session_open)
        self.assertEqual(self.filters._context_key, ("demo", "demo/asset", self.entry.key))
        tab = self.application._current_tab()
        self.assertTrue(any(record.get("column") == "category" and record.get("value") == "props"
                            for record in tab.filter_records), tab.filter_records)
        self.assertIs(self.application._sessions["demo/asset"], previous)
        self.fixture.rpc.assert_not_called()

    def test_preview_reuses_query_and_retains_tab_work_on_reopen(self):
        self.sidebar.open_search()
        tab = self.application._current_tab()
        tab.quick_filters = {"column:category": {"props"}}
        self.sidebar.open_search()
        self.assertIs(self.application._current_tab(), tab)
        self.assertEqual(tab.quick_filters, {"column:category": {"props"}})
        self.assertFalse(self.filters._session_open)
        self.assertEqual(len(self.application._current_section().tabs), 1)
        self.fixture.rpc.assert_not_called()

    def test_closing_modal_restores_previous_section_without_discarding_query(self):
        previous = self.application.current_section_key
        self.sidebar.open_search()
        tab = self.application._current_tab()
        tab.quick_filters = {"column:category": {"props"}}
        self.application.window_model.close_window("sidebar_search_preview")
        self.assertEqual(self.application.current_section_key, previous)
        self.assertIsNone(self.sidebar.previewSurfaces.sourceModel())
        self.assertEqual(tab.quick_filters, {"column:category": {"props"}})

    def test_unsaved_changes_cannot_open_a_different_saved_definition(self):
        self.sidebar.update_selected("name", "another_search")
        self.assertFalse(self.sidebar.canOpenSearch)
        self.sidebar.open_search()
        self.assertEqual(self.application.current_section_key, "demo/asset")

    def test_project_change_cancels_pending_editor_open(self):
        self.sidebar.open_search()
        self.application._current_project_code = "other"
        self.sidebar._finish_search_open()
        self.assertIsNone(self.sidebar._pending_search_open)
        self.assertFalse(self.filters._session_open)

    def test_workspace_action_is_a_real_qml_slot(self):
        self.assertGreaterEqual(self.sidebar.metaObject().indexOfMethod("open_search()"), 0)

    def test_modal_uses_stype_preset_library_without_changing_quick_filter_scope(self):
        from thlib.ui.filter_editor import FilterEditorController
        state = self.application.workspace_state
        editor = FilterEditorController(
            state.filter_model.records, state.filter_column_model.records,
            self.application.search_filter_relations, self.application.notify,
            self.application.has_active_search_tab, self.application.filter_editor_context,
            self.application.stage_filter_editor_records,
        )
        self.enterContext(patch.object(editor, 'load_presets'))
        self.sidebar.attach_filter_editor(editor)
        self.sidebar.open_search()
        self.assertEqual(editor._current_context()['preset_scope'], '')
        self.assertEqual(editor._current_context()['preset_namespace'], 'demo/asset')
        self.assertEqual(self.application._current_section().entry_key, self.entry.key)
        self.assertEqual(self.application._current_section().search_view, self.entry.search_view)
        self.application.window_model.close_window('sidebar_search_preview')
        self.assertFalse(editor._search_type_library)

    def test_stale_project_cannot_open_same_named_search_in_another_project(self):
        self.application._current_project_code = "other"
        self.sidebar.open_search()
        self.assertIn("project changed", self.sidebar.error)


if __name__ == "__main__":
    unittest.main()

"""Personal filter layout uses actual Search tab ownership and persistence."""

from copy import deepcopy
import unittest
from unittest.mock import patch

from tests import test_process_menu_latency as workspace
from tests.test_quick_filters import _Stype
from thlib.ui.controllers.types import SearchTabSession, SectionSession
from thlib.ui.quick_filters import QuickFilterCatalog


class QuickFilterPersonalLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        workspace.ProcessMenuLatencyTests.setUpClass()

    def setUp(self):
        self.fixture = workspace.ProcessMenuLatencyTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.controller = self.fixture.controller
        self.tab = self.controller._current_tab()
        stype = _Stype()
        stype.get_code = lambda: "demo/asset"
        self.tab.stype = stype
        self.controller._active_stype = lambda: stype
        facets = QuickFilterCatalog.discover_facets(stype, [
            {"category": "props", "priority": "low", "duration": 1},
            {"category": "characters", "priority": "high", "duration": 2},
        ])
        key = self.controller._quick_filter_catalog_cache_key("demo", "demo/asset")
        self.controller._quick_filter_runtime.context_key = key
        self.controller._quick_filter_runtime.records = facets
        self.controller._quick_filters.set_configuration("demo/asset", {
            "groups": [
                {"key": "column:priority", "enabled": False},
                {"key": "column:category", "options": ["props"]},
            ], "defaultSelections": {},
        })
        self.query = self.enterContext(patch.object(self.controller, "_load_tab"))

    def test_local_save_is_scoped_clamped_and_restored_with_the_tab(self):
        other = SearchTabSession(tab_id="other", title="Other")
        section = self.controller._current_section()
        section.tabs.append(other)
        standard = self.controller._quick_filters.configuration("demo/asset")
        with patch("thlib.tactic_classes.server_start") as server:
            self.controller.save_quick_filter_layout(self.tab.tab_id, {
                "groups": [
                    {"key": "column:priority", "enabled": True},
                    {"key": "column:category", "options": ["props", "characters"]},
                    {"key": "column:duration", "enabled": False},
                ],
                "defaultSelections": {
                    "column:priority": ["high"], "column:duration": ["1"],
                    "column:category": ["props", "characters"],
                },
            })
            server.assert_not_called()
        self.query.assert_called_once()
        self.assertEqual(self.tab.quick_filters, {"column:category": {"props"}})
        self.assertEqual(other.quick_filters, {})
        self.assertEqual(other.quick_filter_layout, [])
        self.assertEqual(self.controller._quick_filters.configuration("demo/asset"), standard)
        groups = self.controller.quick_filter_editor_context(shared=False)["groups"]
        by_key = {group["key"]: group for group in groups}
        self.assertNotIn("column:priority", by_key)
        self.assertEqual([option["key"] for option in by_key["column:category"]["options"]], ["props"])
        self.assertFalse(by_key["column:duration"]["enabled"])
        self.controller._write_search_cache()
        cached = self.controller._load_search_cache("demo")[section.entry_key]
        restored = SectionSession(entry_key=section.entry_key, title="Assets", accent="", search_type="demo/asset")
        self.controller._restore_section_tabs(restored, deepcopy(cached))
        self.assertEqual(restored.tabs[0].quick_filter_layout, self.tab.quick_filter_layout)
        self.assertEqual(restored.tabs[0].quick_filters, self.tab.quick_filters)
        self.assertEqual(restored.tabs[1].quick_filter_layout, [])

    def test_save_rejects_a_different_tab_and_restore_clears_only_local_layout(self):
        with self.assertRaisesRegex(ValueError, "search tab changed"):
            self.controller.save_quick_filter_layout("stale", {"groups": [], "defaultSelections": {}})
        self.controller.save_quick_filter_layout(self.tab.tab_id, {
            "groups": [{"key": "column:duration", "enabled": False}],
            "defaultSelections": {},
        })
        self.assertTrue(self.tab.quick_filter_layout)
        self.controller.reset_quick_filters_to_standard()
        self.assertEqual(self.tab.quick_filter_layout, [])
        groups = self.controller.quick_filter_editor_context(shared=False)["groups"]
        self.assertNotIn("column:priority", {group["key"] for group in groups})

    def test_shared_policy_is_scoped_to_sidebar_identity_not_search_type(self):
        other_tab = SearchTabSession(tab_id="custom-runtime-id", title="My Tasks", stype=self.tab.stype)
        other = SectionSession(
            entry_key="demo/asset@my_tasks", search_type="demo/asset",
            title="My Tasks", accent="", tabs=[other_tab], current_tab_id=other_tab.tab_id,
        )
        self.controller._sessions[other.entry_key] = other
        self.controller.apply_quick_filter_configuration(other.entry_key, {
            "groups": [{"key": "column:category", "enabled": False}],
            "defaultSelections": {"column:duration": ["1"]},
        })
        self.assertEqual(other_tab.quick_filters, {"column:duration": {"1"}})
        self.assertEqual(self.tab.quick_filters, {})
        self.assertIn("column:category", {group["key"] for group in self.controller.quick_filter_groups})
        self.controller._current_section_key = other.entry_key
        self.assertEqual(self.controller.quick_filter_editor_context()["scope_key"], other.entry_key)
        self.assertNotIn("column:category", {group["key"] for group in self.controller.quick_filter_groups})
        self.controller.reset_quick_filters_to_standard()
        self.assertEqual(other_tab.quick_filters, {"column:duration": {"1"}})
        self.assertEqual(self.tab.quick_filters, {})


if __name__ == "__main__":
    unittest.main()

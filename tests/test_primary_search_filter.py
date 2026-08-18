from __future__ import annotations

from types import SimpleNamespace
import unittest

from modern_ui.controllers.advanced_search import AdvancedSearchMixin
from modern_ui.controllers.search_suggestions import SearchSuggestionsMixin
from modern_ui.controllers.types import SearchTabSession, SectionSession


class _Model:
    def __init__(self, records=()):
        self._records = [dict(record) for record in records]

    def replace(self, records):
        self._records = [dict(record) for record in records]

    def clear(self):
        self._records.clear()


class _PrimarySearchHarness(AdvancedSearchMixin, SearchSuggestionsMixin):
    def __init__(self, records):
        self.tab = SearchTabSession(
            tab_id="assets:tab",
            title="My Assets",
            search_text="",
            filter_records=[dict(record) for record in records],
        )
        self.section = SectionSession(
            entry_key="assets",
            title="My Assets",
            accent="",
            search_type="demo/asset",
            tabs=[self.tab],
            current_tab_id=self.tab.tab_id,
        )
        self.workspace_state = SimpleNamespace(
            filter_model=_Model(records),
            search_suggestion_model=_Model(),
        )
        self._skey_worker = None
        self._skey_request_id = ""
        self._suggestion_worker = None
        self._pending_suggestion_value = None
        self._suggestion_request_id = ""
        self.loaded = False

    def _current_tab(self):
        return self.tab

    def _current_section(self):
        return self.section

    def _capture_current_tree_state(self):
        pass

    def _sync_search_tabs(self, clear_suggestions=True):
        pass

    def _load_tab(self, tab, append=False):
        self.loaded = tab is self.tab and not append


class PrimarySearchFilterTests(unittest.TestCase):
    @staticmethod
    def _preset_records():
        return [
            {
                "column": "name",
                "relation": "EQI",
                "value": "",
                "rowEnabled": True,
                "operator": "begin",
                "isDefault": True,
            },
            {
                "column": "_expression",
                "relation": "expression",
                "value": "@SOBJECT(sthpw/task['assigned', '$LOGIN'])",
                "rowEnabled": True,
                "operator": "and",
                "isDefault": False,
            },
        ]

    def test_main_search_updates_name_and_preserves_preset_scope(self):
        controller = _PrimarySearchHarness(self._preset_records())

        controller.search("chair")

        self.assertTrue(controller.loaded)
        self.assertEqual(controller.tab.title, "chair")
        self.assertEqual(controller.tab.search_text, "chair")
        self.assertEqual(len(controller.tab.filter_records), 2)
        self.assertEqual(controller.tab.filter_records[0]["column"], "name")
        self.assertEqual(controller.tab.filter_records[0]["value"], "chair")
        self.assertEqual(
            controller.tab.filter_records[1]["value"],
            "@SOBJECT(sthpw/task['assigned', '$LOGIN'])",
        )
        self.assertIn(
            ("_expression", "expression", "@SOBJECT(sthpw/task['assigned', '$LOGIN'])"),
            controller.tab.extra_filters,
        )

    def test_missing_primary_row_is_inserted_before_existing_scope(self):
        expression = self._preset_records()[1]
        controller = _PrimarySearchHarness([expression])

        controller.search("tree")

        self.assertEqual(len(controller.tab.filter_records), 2)
        self.assertEqual(controller.tab.filter_records[0]["column"], "name")
        self.assertEqual(controller.tab.filter_records[0]["value"], "tree")
        self.assertEqual(controller.tab.filter_records[1]["column"], "_expression")
        self.assertEqual(controller.tab.filter_records[1]["operator"], "and")


if __name__ == "__main__":
    unittest.main()

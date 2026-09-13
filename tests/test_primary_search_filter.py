from __future__ import annotations

from types import SimpleNamespace
import unittest

from thlib.ui.controllers.advanced_search import AdvancedSearchMixin
from thlib.ui.controllers.search_suggestions import SearchSuggestionsMixin
from thlib.ui.controllers.types import SearchTabSession, SectionSession
from thlib.ui.search_suggestion_data import search_suggestion_spec
from thlib.ui.search_contract import create_search_tab, set_primary_name


class _Model:
    def __init__(self, records=()):
        self._records = [dict(record) for record in records]

    def replace(self, records):
        self._records = [dict(record) for record in records]

    def clear(self):
        self._records.clear()


class _PrimarySearchHarness(AdvancedSearchMixin, SearchSuggestionsMixin):
    def __init__(self, records, columns=None):
        self.stype = None if columns is None else SimpleNamespace(
            get_columns_info=lambda: {column: {} for column in columns},
        )
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
        self._page_size = 25
        self._default_view_mode = "continious"
        self.section_state_changed = SimpleNamespace(emit=lambda: None)
        self.loaded = False
        self.loaded_tab = None

    def _current_tab(self):
        return self.tab

    def _active_stype(self):
        return self.stype

    def _current_section(self):
        return self.section

    def _capture_current_tree_state(self, persist_tree=False):
        pass

    def _capture_current_workspace_layout(self):
        pass

    def _sync_search_tabs(self, clear_suggestions=True):
        pass

    def _load_tab(self, tab, append=False):
        self.loaded_tab = tab
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

    def test_enter_uses_the_suggestion_fields_and_preserves_other_conditions(self):
        controller = _PrimarySearchHarness(
            self._preset_records(), ["name", "code", "keywords", "description"],
        )
        controller.search("chair")
        _title, _columns, suggestions = search_suggestion_spec(controller.stype, "chair")
        expected = [part for part in suggestions if isinstance(part, tuple)]
        records = controller.tab.filter_records
        self.assertEqual([
            (row["column"], row["relation"], row["value"]) for row in records[:3]
        ], expected)
        self.assertEqual([row["operator"] for row in records], ["begin", "or", "or", "and"])
        self.assertEqual(records[-1]["value"], self._preset_records()[-1]["value"])

    def test_repeated_enter_and_clear_replace_the_complete_primary_group(self):
        controller = _PrimarySearchHarness(
            self._preset_records(), ["name", "keywords", "description"],
        )
        controller.search("chair")
        controller.search("tree")
        self.assertEqual(len(controller.tab.filter_records), 4)
        self.assertEqual([row["value"] for row in controller.tab.filter_records[:3]], ["tree"] * 3)
        controller.search("")
        self.assertEqual(len(controller.tab.filter_records), 2)
        self.assertEqual(controller.tab.extra_filters, [(
            "_expression", "expression", "@SOBJECT(sthpw/task['assigned', '$LOGIN'])",
        )])

    def test_title_and_code_fallbacks_only_query_available_fields(self):
        for columns, expected in [
            (["title", "description"], ["title", "description"]),
            (["code"], ["code"]),
        ]:
            with self.subTest(columns=columns):
                controller = _PrimarySearchHarness(self._preset_records(), columns)
                controller.search("needle")
                self.assertEqual(
                    [r["column"] for r in controller.tab.filter_records[:-1]], expected,
                )

    def test_accepting_one_suggestion_replaces_broad_search_with_exact_title(self):
        controller = _PrimarySearchHarness(
            self._preset_records(), ["title", "keywords", "description"],
        )
        controller.search("chair")
        controller._suggestion_column = "title"
        controller.workspace_state.search_suggestion_model.replace([{
            "title": "Red Chair", "values": {"title": "Red Chair"},
        }])
        controller.accept_search_suggestion(0)
        self.assertEqual(len(controller.tab.filter_records), 2)
        self.assertEqual(controller.tab.extra_filters[:2], ["begin", ("title", "=", "Red Chair")])

    def test_middle_click_opens_suggestion_in_an_independent_tab(self):
        controller = _PrimarySearchHarness(self._preset_records())
        controller.workspace_state.search_suggestion_model.replace([{
            "title": "Red Chair", "code": "ASSET001",
            "values": {"name": "Red Chair"},
        }])

        controller.open_search_suggestion_in_new_tab(0)

        self.assertEqual(len(controller.section.tabs), 2)
        opened = controller.section.tabs[-1]
        self.assertIs(controller.loaded_tab, opened)
        self.assertEqual(controller.section.current_tab_id, opened.tab_id)
        self.assertEqual(opened.tab_kind, "user")
        self.assertEqual(opened.title, "Red Chair")
        self.assertEqual(opened.extra_filters, [("code", "=", "ASSET001")])

    def test_new_tab_from_saved_search_clears_the_whole_primary_group(self):
        from thlib.tactic_classes import pack_tactic_search_view
        from thlib.ui.search_presets import records_from_config

        controller = _PrimarySearchHarness(
            self._preset_records(), ["name", "keywords", "description"],
        )
        controller.search("chair")
        packed = pack_tactic_search_view([
            (row["rowEnabled"], (row["column"], row["relation"], row["value"]), row["operator"])
            for row in controller.tab.filter_records
        ])
        restored = records_from_config(f"<config><filter><values>{packed}</values></filter></config>")
        tab = create_search_tab(
            "assets", "Preset", tab_kind="preset", limit=25,
            view_mode="continious", records=restored, ensure_name_row=True,
        )
        self.assertEqual([row["column"] for row in tab.filter_records], ["name", "_expression"])

    def test_independent_keyword_constraint_is_not_removed(self):
        records = self._preset_records() + [{
            "column": "keywords", "relation": "like", "value": "%approved%",
            "rowEnabled": True, "operator": "and",
        }]
        result = set_primary_name(records, "chair", columns=["name", "keywords", "description"])
        result = set_primary_name(result, "table", columns=["name", "keywords", "description"])
        self.assertEqual(result[-1]["value"], "%approved%")
        self.assertEqual(result[-1]["relation"], "like")
        self.assertEqual(len(result), 5)


if __name__ == "__main__":
    unittest.main()

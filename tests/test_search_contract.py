from __future__ import annotations

import unittest

from modern_ui.search_contract import (
    create_search_tab,
    filters_from_records,
    records_from_filters,
    set_primary_name,
)
from modern_ui.workspace_models.state_project_state import ProjectStateMixin


class _RecordModel:
    def __init__(self):
        self.records = []

    def replace(self, records):
        self.records = [dict(record) for record in records]


class _ProjectState(ProjectStateMixin):
    def __init__(self):
        self.columns_model = _RecordModel()
        self.filter_column_model = _RecordModel()
        self.filter_relation_model = _RecordModel()


class _SearchType:
    _columns = {
        "name": {"data_type": "varchar"},
        "title": {"data_type": "varchar"},
        "code": {"data_type": "varchar"},
    }

    def get_columns_info(self):
        return self._columns

    def get_column_data_type(self, column):
        return self._columns[column]["data_type"]


class SearchContractTests(unittest.TestCase):
    def test_primary_search_preserves_the_sidebar_or_preset_scope(self):
        records = records_from_filters([
            ("_expression", "in", "@SOBJECT(sthpw/task['assigned', '$LOGIN'])"),
        ])

        records = set_primary_name(records, "chair")

        self.assertEqual(records[0]["column"], "name")
        self.assertEqual(records[0]["value"], "chair")
        self.assertEqual(records[1]["column"], "_expression")
        self.assertIn(
            ("_expression", "in", "@SOBJECT(sthpw/task['assigned', '$LOGIN'])"),
            filters_from_records(records),
        )

    def test_all_entry_points_create_the_same_runtime_contract(self):
        source_filters = [("status", "=", "Ready")]

        related = create_search_tab(
            "demo/assets@direct",
            "Related",
            tab_kind="related",
            limit=25,
            view_mode="continious",
            filters=source_filters,
        )
        preset = create_search_tab(
            "demo/assets@sidebar",
            "Preset",
            tab_kind="preset",
            limit=25,
            view_mode="continious",
            records=records_from_filters(source_filters),
        )

        self.assertEqual(related.filter_records, preset.filter_records)
        self.assertEqual(related.extra_filters, preset.extra_filters)

    def test_user_tab_has_primary_name_card_immediately(self):
        tab = create_search_tab(
            "demo/assets@sidebar",
            "New Search",
            tab_kind="user",
            limit=25,
            view_mode="continious",
            ensure_name_row=True,
        )

        self.assertEqual(len(tab.filter_records), 1)
        self.assertEqual(tab.filter_records[0]["column"], "name")
        self.assertEqual(tab.filter_records[0]["relation"], "EQI")
        self.assertEqual(tab.extra_filters, [])

    def test_advanced_search_columns_keep_native_tactic_schema_order(self):
        state = _ProjectState()

        state.load_stype(_SearchType())

        self.assertEqual(
            [record["value"] for record in state.filter_column_model.records],
            ["name", "title", "code", "_expression"],
        )


if __name__ == "__main__":
    unittest.main()

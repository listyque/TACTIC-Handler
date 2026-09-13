from types import SimpleNamespace
import unittest

from thlib.ui.controllers.advanced_search import AdvancedSearchMixin
from thlib.ui.controllers.view_state import ViewStateMixin
from thlib.ui.controllers.types import SearchTabSession
from thlib.ui.quick_filters import QuickFilterCatalog
from thlib.ui.search_contract import default_name_record, filters_from_records
from thlib.ui.tel_filters import (
    CURRENT_LOGIN_FILTER,
    compile_task_filter_tel,
    generated_quick_filter_records,
    generated_task_filter_record,
    is_generated_quick_filter,
    quick_selection_from_records,
)
from thlib.ui.workspace_models.records import RecordListModel


class _Signal:
    def emit(self, *args):
        pass


class _FilterModel:
    def __init__(self):
        self.records = []

    def replace(self, records):
        self.records = [dict(record) for record in records]


class _ViewStateHarness(ViewStateMixin):
    def __init__(self, tab, facets=None):
        self.tab = tab
        self.tab.quick_filter_layout = []
        self._login_name = "artist"
        self._card_path = []
        self._pending_card_focus_id = ""
        self._quick_filters = QuickFilterCatalog()
        self.workspace_state = SimpleNamespace(filter_model=_FilterModel())
        self.quick_filters_changed = _Signal()
        self.section_state_changed = _Signal()
        self.load_calls = []
        self._sessions = {
            "demo/assets": SimpleNamespace(
                search_type="demo/asset", entry_key="demo/asset", tabs=[tab]
            )
        }
        self.facets = list(facets or [])

    def _current_tab(self):
        return self.tab

    def _current_section(self):
        return SimpleNamespace(search_type="demo/asset", entry_key="demo/asset")

    def _active_stype(self):
        return None

    def _active_quick_filter_facets(self):
        return self.facets

    @staticmethod
    def _default_search_filter_record(value=""):
        return default_name_record(value)

    @staticmethod
    def _filter_records_from_filters(filters):
        return []

    @staticmethod
    def _filters_from_records(records):
        return filters_from_records(records)

    def _capture_current_tree_state(self, persist_tree=False):
        pass

    def _save_search_cache(self):
        pass

    def _load_tab(self, tab, append=False):
        self.load_calls.append((tab, append))

    def _notify(self, message):
        self.notification = message


class _AdvancedSearchHarness(AdvancedSearchMixin):
    def __init__(self, tab, records):
        self.tab = tab
        model = RecordListModel((
            "column", "relation", "value", "rowEnabled", "operator",
            "isDefault", "generatedFilterKind", "generatedFilterState",
        ))
        model.replace(records)
        self.workspace_state = SimpleNamespace(filter_model=model)
        self.quick_filters_changed = _Signal()
        self._applying_tag_filters = False
        self.load_calls = []

    def _current_tab(self):
        return self.tab

    def _save_search_cache(self):
        pass

    def _capture_current_tree_state(self, persist_tree=False):
        pass

    def _load_tab(self, tab, append=False):
        self.load_calls.append((tab, append))


class QuickFilterRecordTests(unittest.TestCase):
    def test_my_tasks_matches_the_exact_legacy_expression(self):
        self.assertEqual(
            compile_task_filter_tel({
                "assigned": {CURRENT_LOGIN_FILTER},
            }),
            "@SOBJECT(sthpw/task['assigned', '$LOGIN'])",
        )

    def test_all_task_facets_compile_inside_one_relationship(self):
        expression = compile_task_filter_tel({
            "assigned": {"reviewer", CURRENT_LOGIN_FILTER},
            "process": {"storyboard"},
            "status": {"In Progress", "Assigned"},
        }, current_login="artist")
        self.assertEqual(
            expression,
            "@SOBJECT(sthpw/task"
            "['assigned', 'in', 'artist|reviewer']"
            "['process', 'storyboard']"
            "['status', 'in', 'Assigned|In Progress'])",
        )

    def test_direct_and_task_facets_round_trip_from_advanced_search(self):
        records = generated_quick_filter_records(
            {
                "column:category": {"props", "characters"},
                "assigned": {"reviewer"},
                "status": {"Assigned"},
            },
            [{
                "key": "column:category",
                "column": "category",
                "title": "Category",
            }],
        )

        self.assertEqual(len(records), 2)
        direct = next(record for record in records if record["column"] == "category")
        self.assertEqual(direct["relation"], "in")
        self.assertEqual(direct["value"], "characters|props")
        self.assertTrue(all(is_generated_quick_filter(record) for record in records))
        self.assertEqual(
            quick_selection_from_records(records),
            {
                "column:category": {"characters", "props"},
                "assigned": {"reviewer"},
                "status": {"Assigned"},
            },
        )

    def test_applying_direct_quick_filter_reloads_server_from_first_page(self):
        tab = SearchTabSession(
            tab_id="quick-filter", title="Quick Filter",
            filter_records=[default_name_record()],
            extra_filters=[],
            quick_filters={"column:category": {"props"}},
            quick_filter_tasks={},
            sobjects=[],
            stype=None,
            offset=75,
            next_offset=100,
            exhausted=True,
            duplicate_pages=2,
            loaded=True,
            workspace_roots=[object()],
        )
        controller = _ViewStateHarness(tab)

        controller._apply_quick_filters(tab)

        generated = [
            record for record in tab.filter_records
            if is_generated_quick_filter(record)
        ]
        self.assertEqual(len(generated), 1)
        self.assertIn(("category", "=", "props"), tab.extra_filters)
        self.assertEqual((tab.offset, tab.next_offset), (0, 0))
        self.assertFalse(tab.loaded)
        self.assertEqual(tab.workspace_roots, [])
        self.assertEqual(controller.load_calls, [(tab, False)])

    def test_clear_quick_filters_removes_all_generated_rows(self):
        generated = generated_quick_filter_records(
            {
                "column:category": {"props"},
                "assigned": {CURRENT_LOGIN_FILTER},
            },
            [{
                "key": "column:category",
                "column": "category",
                "title": "Category",
            }],
        )
        records = [default_name_record(), *generated]
        tab = SearchTabSession(
            tab_id="quick-filter", title="Quick Filter",
            filter_records=records,
            extra_filters=filters_from_records(records),
            quick_filters={
                "column:category": {"props"},
                "assigned": {CURRENT_LOGIN_FILTER},
            },
            quick_filter_tasks={},
            sobjects=[],
            stype=None,
            offset=75,
            next_offset=100,
            exhausted=True,
            duplicate_pages=2,
            loaded=True,
            workspace_roots=[object()],
        )
        controller = _ViewStateHarness(tab)

        controller.clear_quick_filters()

        self.assertEqual(tab.quick_filters, {})
        self.assertFalse(any(
            is_generated_quick_filter(record) for record in tab.filter_records
        ))
        self.assertEqual(controller.load_calls, [(tab, False)])

    def test_generated_card_can_become_an_ordinary_filter(self):
        generated = generated_task_filter_record({
            "assigned": {CURRENT_LOGIN_FILTER},
        })
        records = [default_name_record(), generated]
        tab = SearchTabSession(
            tab_id="advanced-search", title="Advanced Search",
            filter_records=list(records),
            extra_filters=filters_from_records(records),
            quick_filters={
                "assigned": {CURRENT_LOGIN_FILTER},
                "column:category": {"asset"},
            },
        )
        controller = _AdvancedSearchHarness(tab, records)

        controller.detach_generated_search_filter(1)

        detached = tab.filter_records[1]
        self.assertEqual(detached["generatedFilterKind"], "")
        self.assertEqual(detached["generatedFilterState"], {})
        self.assertEqual(detached["column"], "_expression")
        self.assertIn(
            ("_expression", "in", detached["value"]), tab.extra_filters
        )
        self.assertNotIn("assigned", tab.quick_filters)
        self.assertEqual(tab.quick_filters["column:category"], {"asset"})

    def test_advanced_search_apply_restores_direct_quick_filter_chips(self):
        generated = generated_quick_filter_records(
            {"column:category": {"props"}},
            [{
                "key": "column:category",
                "column": "category",
                "title": "Category",
            }],
        )[0]
        records = [default_name_record(), generated]
        tab = SearchTabSession(
            tab_id="advanced-search", title="Advanced Search",
            filter_records=list(records),
            extra_filters=[],
            quick_filters={},
            selected_tags=set(),
            tag_column="",
            offset=50,
            next_offset=75,
            exhausted=True,
            duplicate_pages=2,
            loaded=True,
            workspace_roots=[object()],
        )
        controller = _AdvancedSearchHarness(tab, records)

        controller.apply_search_filters()

        self.assertEqual(
            tab.quick_filters, {"column:category": {"props"}}
        )
        self.assertIn(("category", "=", "props"), tab.extra_filters)
        self.assertEqual(controller.load_calls, [(tab, False)])

    @staticmethod
    def _session_tab(*, personalized=False, selected=None):
        return SearchTabSession(
            tab_id="demo:base",
            title="Assets",
            tab_kind="base",
            filter_records=[default_name_record()],
            quick_filters={
                key: set(values) for key, values in (selected or {}).items()
            },
            quick_filter_personalized=personalized,
        )

    @staticmethod
    def _category_facet():
        return {
            "key": "column:category",
            "column": "category",
            "title": "Category",
            "source": "column",
            "accent": "#607d8b",
            "options": [
                {"key": "props", "title": "Props", "count": 3},
                {"key": "characters", "title": "Characters", "count": 2},
            ],
        }

    def test_server_standard_applies_to_unpersonalized_normal_tab(self):
        tab = self._session_tab()
        controller = _ViewStateHarness(tab, [self._category_facet()])

        controller.apply_quick_filter_configuration("demo/asset", {
            "groups": [],
            "defaultSelections": {"column:category": ["props"]},
        })

        self.assertEqual(tab.quick_filters, {"column:category": {"props"}})
        self.assertFalse(tab.quick_filter_personalized)
        self.assertTrue(any(
            is_generated_quick_filter(record) for record in tab.filter_records
        ))
        self.assertEqual(controller.load_calls, [(tab, False)])

    def test_explicit_empty_local_state_is_not_replaced_by_standard(self):
        tab = self._session_tab(personalized=True)
        controller = _ViewStateHarness(tab, [self._category_facet()])

        controller.apply_quick_filter_configuration("demo/asset", {
            "groups": [],
            "defaultSelections": {"column:category": ["props"]},
        })

        self.assertEqual(tab.quick_filters, {})
        self.assertEqual(controller.load_calls, [])

    def test_shared_hidden_group_prunes_a_personalized_selection(self):
        tab = self._session_tab(
            personalized=True,
            selected={"column:category": {"props"}},
        )
        tab.filter_records.extend(generated_quick_filter_records(
            tab.quick_filters, [self._category_facet()]
        ))
        tab.extra_filters = filters_from_records(tab.filter_records)
        controller = _ViewStateHarness(tab, [self._category_facet()])

        controller.apply_quick_filter_configuration("demo/asset", {
            "groups": [{
                "key": "column:category",
                "enabled": False,
            }],
            "defaultSelections": {},
        })

        self.assertEqual(tab.quick_filters, {})
        self.assertFalse(any(
            is_generated_quick_filter(record) for record in tab.filter_records
        ))
        self.assertEqual(controller.load_calls, [(tab, False)])

    def test_restore_standard_releases_local_override(self):
        tab = self._session_tab(personalized=True)
        controller = _ViewStateHarness(tab, [self._category_facet()])
        controller._quick_filters.set_configuration("demo/asset", {
            "groups": [],
            "defaultSelections": {"column:category": ["props"]},
        })

        controller.reset_quick_filters_to_standard()

        self.assertFalse(tab.quick_filter_personalized)
        self.assertEqual(tab.quick_filters, {"column:category": {"props"}})
        self.assertEqual(controller.load_calls, [(tab, False)])

    def test_explicit_preset_cannot_mix_in_the_server_starting_state(self):
        tab = self._session_tab(personalized=True)
        tab.tab_kind = "preset"
        controller = _ViewStateHarness(tab, [self._category_facet()])
        controller._quick_filters.set_configuration("demo/asset", {
            "groups": [],
            "defaultSelections": {"column:category": ["props"]},
        })

        controller.reset_quick_filters_to_standard()

        self.assertTrue(tab.quick_filter_personalized)
        self.assertEqual(tab.quick_filters, {})
        self.assertEqual(controller.load_calls, [])


if __name__ == "__main__":
    unittest.main()

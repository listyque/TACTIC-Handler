from collections import OrderedDict
import unittest
from unittest.mock import MagicMock, patch

from thlib.ui.controllers.view_state import ViewStateMixin
from thlib.ui.quick_filters import QuickFilterCatalog, QuickFilterRuntime


class _TaskPipeline:
    def __init__(self):
        self.pipeline = OrderedDict((
            ("Assigned", {"color": "#8a6d3b"}),
            ("In Progress", {"color": "#3f7fc4"}),
        ))


class _Workflow:
    def get_by_pipeline_code(self, search_type, code):
        if search_type == "sthpw/task" and code == "demo/story_task":
            return _TaskPipeline()
        return None

    def get_by_process_node_type(self, search_type, node_type):
        return None


class _Pipeline:
    pipeline = OrderedDict((
        ("storyboard", {"name": "storyboard"}),
        ("publish", {"name": "publish"}),
    ))

    def get_all_pipeline_names(self):
        return list(self.pipeline)

    def get_all_pipeline_process(self):
        return [
            {"process": "storyboard"},
            {"process": "publish"},
        ]

    def get_info(self):
        return {
            "code": "demo/episode",
            "name": "Asset production",
            "color": "#5267a8",
        }

    def get_process_info(self, process):
        return {"label": process.title(), "type": "manual"}

    def get_pipeline_process(self, process):
        if process == "storyboard":
            return {
                "color": "#b54f3e",
                "workflow": {
                    "properties": {"task_pipeline": "demo/story_task"},
                },
            }
        return {"color": "#28a96b"}


class _Project:
    def get_code(self):
        return "demo"


class _Stype:
    def get_code(self):
        return "demo/assets"

    def get_project(self):
        return _Project()

    def get_pipeline(self):
        return {"demo/episode": _Pipeline()}

    def get_workflow(self):
        return _Workflow()

    def get_columns_info(self):
        return OrderedDict((
            ("name", {"data_type": "varchar"}),
            ("description", {"data_type": "text"}),
            ("category", {"data_type": "varchar", "title": "Category"}),
            ("pipeline_code", {"data_type": "varchar"}),
            ("priority", {
                "data_type": "varchar",
                "choices": {"low": "Low priority", "high": "High priority"},
            }),
            ("duration", {"data_type": "integer"}),
            ("timestamp", {"data_type": "timestamp"}),
        ))


class _Record:
    def __init__(self, code, **values):
        self.info = {"code": code, **values}

    def get_code(self):
        return self.info["code"]

    def get_info(self):
        return dict(self.info)

    def get_pipeline_code(self):
        return self.info.get("pipeline_code", "demo/episode")


class _Signal:
    def __init__(self):
        self.emissions = 0

    def emit(self, *args):
        self.emissions += 1


class _CachedFacetHarness(ViewStateMixin):
    def __init__(self, records):
        self.stype = _Stype()
        self.tab = type("Tab", (), {"stype": self.stype})()
        self._current_project_code = "demo"
        self._quick_filters = QuickFilterCatalog()
        self._quick_filter_runtime = QuickFilterRuntime()
        cache_key = self._quick_filter_catalog_cache_key(
            "demo", "demo/assets"
        )
        self._quick_filter_runtime.cache[cache_key] = {
            "loadedAt": 1.0,
            "records": records,
            "facetColumns": QuickFilterCatalog.facet_columns(self.stype),
        }
        self.quick_filters_changed = _Signal()

    def _current_tab(self):
        return self.tab

    def _current_section(self):
        return type("Section", (), {"search_type": "demo/assets"})()

    def _active_stype(self):
        return self.stype


class QuickFilterCatalogTests(unittest.TestCase):
    def setUp(self):
        self.catalog = QuickFilterCatalog()
        self.asset_a = _Record(
            "ASSET0001", category="characters",
            pipeline_code="demo/episode", priority="high", duration=40,
        )
        self.asset_b = _Record(
            "ASSET0002", category="props",
            pipeline_code="demo/other", priority="low", duration=80,
        )
        self.tasks = {
            "ASSET0001": [_Record(
                "TASK0001", process="storyboard", status="Assigned",
                assigned="artist",
            )],
            "ASSET0002": [_Record(
                "TASK0002", process="publish", status="In Progress",
                assigned="reviewer",
            )],
        }

    def test_facets_come_from_schema_and_actual_sobjects(self):
        groups = self.catalog.discover_facets(
            _Stype(), [self.asset_a, self.asset_b]
        )
        by_key = {group["key"]: group for group in groups}

        self.assertEqual(
            set(by_key),
            {
                "column:category",
                "column:pipeline_code",
                "column:priority",
                "column:duration",
            },
        )
        self.assertEqual(
            {option["key"] for option in by_key["column:category"]["options"]},
            {"characters", "props"},
        )
        self.assertEqual(
            {
                option["key"]: option["title"]
                for option in by_key["column:priority"]["options"]
            },
            {"high": "High priority", "low": "Low priority"},
        )

    def test_text_fields_include_duration_and_single_storyboard_value(self):
        stype = _Stype()
        stype.get_columns_info = lambda: {
            "duration": {"data_type": "text"},
            "storyboard": {"data_type": "text"},
            "description": {"data_type": "text"},
        }
        groups = self.catalog.discover_facets(stype, [
            {"duration": "1 Minute", "storyboard": "(No Storyboard)"},
            {"duration": "2 Minutes", "storyboard": None},
            {"duration": "2 Minutes", "storyboard": "(No Storyboard)"},
        ])
        by_key = {group["key"]: group for group in groups}
        self.assertEqual(set(by_key), {"column:duration", "column:storyboard"})
        self.assertEqual(
            [(option["key"], option["count"])
             for option in by_key["column:duration"]["options"]],
            [("1 Minute", 1), ("2 Minutes", 2)],
        )
        self.assertEqual(
            [(option["title"], option["count"])
             for option in by_key["column:storyboard"]["options"]],
            [("(No Storyboard)", 2)],
        )

    def test_numeric_zero_and_false_metadata_options_are_preserved(self):
        stype = _Stype()
        stype.get_columns_info = lambda: {
            "duration": {"data_type": "integer"},
            "flag": {"data_type": "boolean", "choices": [False, True]},
            "rating": {"data_type": "integer", "choices": [
                {"value": 0, "title": "Unrated"},
                {"value": 1, "title": "Rated"},
            ]},
        }
        groups = self.catalog.discover_facets(stype, [
            {"duration": 0, "flag": False, "rating": 0},
            {"duration": 2, "flag": True, "rating": 1},
        ])
        by_key = {group["key"]: group for group in groups}
        self.assertEqual(
            [option["key"] for option in by_key["column:duration"]["options"]],
            ["0", "2"],
        )
        self.assertEqual(
            [(option["key"], option["count"])
             for option in by_key["column:flag"]["options"]],
            [("False", 1), ("True", 1)],
        )
        self.assertIn(
            ("0", "Unrated", 1),
            [(option["key"], option["title"], option["count"])
             for option in by_key["column:rating"]["options"]],
        )

    def test_high_cardinality_discovered_column_is_not_a_quick_filter(self):
        rows = [
            {"category": f"value-{index}", "pipeline_code": "asset"}
            for index in range(self.catalog.MAX_DISCOVERED_OPTIONS + 1)
        ]
        groups = self.catalog.discover_facets(_Stype(), rows)
        self.assertNotIn("column:category", {
            group["key"] for group in groups
        })

    def test_task_facets_use_workflow_and_task_data(self):
        direct = self.catalog.discover_facets(
            _Stype(), [self.asset_a, self.asset_b]
        )
        groups = self.catalog.groups(
            "demo/assets", _Stype(), [self.asset_a, self.asset_b], {},
            self.tasks, "artist", direct,
        )
        by_key = {group["key"]: group for group in groups}

        processes = {
            option["key"]: option for option in by_key["process"]["options"]
        }
        statuses = {
            option["key"]: option for option in by_key["status"]["options"]
        }
        self.assertEqual(processes["storyboard"]["accent"], "#b54f3e")
        self.assertEqual(statuses["Assigned"]["accent"], "#8a6d3b")
        self.assertTrue(by_key["assigned"]["userPicker"])

    def test_configuration_targets_discovered_group_keys(self):
        facets = self.catalog.discover_facets(
            _Stype(), [self.asset_a, self.asset_b]
        )
        self.catalog.set_configuration("demo/assets", {
            "groups": [
                {
                    "key": "column:priority",
                    "enabled": True,
                    "options": ["high"],
                },
                {"key": "column:category", "enabled": False},
            ],
            "defaultSelections": {},
        })

        groups = self.catalog.groups(
            "demo/assets", _Stype(), [self.asset_a, self.asset_b], {},
            {}, "artist", facets,
        )
        by_key = {group["key"]: group for group in groups}
        self.assertNotIn("column:category", by_key)
        self.assertEqual(
            [option["key"] for option in by_key["column:priority"]["options"]],
            ["high"],
        )

    def test_whole_search_type_query_is_unfiltered_and_paged(self):
        columns = QuickFilterCatalog.facet_columns(_Stype())
        pages = [
            [
                {"category": "characters", "pipeline_code": "asset"},
                {"category": "props", "pipeline_code": "asset"},
            ],
            [{"category": "sets", "pipeline_code": "shot"}],
        ]
        with patch(
            "thlib.tactic_classes.server_query", side_effect=pages
        ) as query:
            groups = ViewStateMixin._query_quick_filter_catalog(
                "demo", "demo/assets", columns, page_size=2
            )

        self.assertEqual(query.call_count, 2)
        for call in query.call_args_list:
            self.assertEqual(call.kwargs["filters"], [])
            self.assertEqual(call.kwargs["order_bys"], [])
        category = next(
            group for group in groups if group["key"] == "column:category"
        )
        self.assertEqual(
            {option["key"] for option in category["options"]},
            {"characters", "props", "sets"},
        )

    def test_fresh_search_type_facet_cache_skips_server_work(self):
        cached = [{
            "key": "column:category",
            "column": "category",
            "title": "Category",
            "source": "column",
            "accent": "#607d8b",
            "options": [{"key": "props", "title": "props", "count": 7}],
        }]
        harness = _CachedFacetHarness(cached)

        harness._request_quick_filter_catalog(False)

        self.assertEqual(harness._quick_filter_runtime.records, cached)
        self.assertFalse(harness._quick_filter_runtime.loading)
        self.assertEqual(harness._quick_filter_runtime.workers, {})
        self.assertEqual(harness.quick_filters_changed.emissions, 1)

    def test_persistent_catalog_checks_its_schema_and_refresh_bypasses_it(self):
        for cache_state in ("missing_schema", "changed_schema", "current", "refresh"):
            with self.subTest(cache_state=cache_state):
                harness = _CachedFacetHarness([])
                key = harness._quick_filter_catalog_cache_key("demo", "demo/assets")
                columns = QuickFilterCatalog.facet_columns(harness.stype)
                cached = {"records": [{"key": "cached"}]}
                if cache_state != "missing_schema":
                    cached["facetColumns"] = columns[:-1] if cache_state == "changed_schema" else columns
                # A stale hot projection must not hide the schema mismatch.
                harness._quick_filter_runtime.cache[key] = cached
                if cache_state == "current":
                    harness._quick_filter_runtime.cache.clear()
                pool = MagicMock(is_stopped=False)
                fresh = [{"key": "fresh"}]
                with (
                    patch("thlib.environment.env_inst.server_pool", pool),
                    patch("thlib.server_cache.token", return_value="token"),
                    patch("thlib.server_cache.read_entry", return_value=cached) as read,
                    patch("thlib.server_cache.write_entry") as write,
                    patch.object(harness, "_query_quick_filter_catalog", return_value=fresh) as query,
                ):
                    harness._request_quick_filter_catalog(cache_state == "refresh")
                    callback = pool.add_task.call_args.args[0]
                    payload, = callback()
                    harness._quick_filter_catalog_result((payload, (key,)))
                expected = cached["records"] if cache_state == "current" else fresh
                self.assertEqual(harness._quick_filter_runtime.records, expected)
                self.assertEqual(query.call_count, 0 if cache_state == "current" else 1)
                self.assertEqual(read.call_count, 0 if cache_state == "refresh" else 1)
                self.assertEqual(write.call_count, query.call_count)
                self.assertEqual(harness._quick_filter_runtime.cache[key]["facetColumns"], columns)

    def test_shared_policy_sanitizes_local_and_standard_selections(self):
        self.catalog.set_configuration("demo/assets", {
            "groups": [
                {"key": "process", "enabled": False},
                {
                    "key": "column:category",
                    "enabled": True,
                    "options": ["props"],
                },
            ],
            "defaultSelections": {
                "process": ["render"],
                "column:category": ["props", "characters"],
                "status": ["Ready"],
            },
        })

        self.assertEqual(
            self.catalog.default_selections("demo/assets"),
            {
                "column:category": {"props"},
                "status": {"Ready"},
            },
        )
        self.assertEqual(
            self.catalog.sanitize_selection("demo/assets", {
                "process": {"render"},
                "column:category": {"characters", "props"},
            }),
            {"column:category": {"props"}},
        )

    def test_local_layout_cannot_restore_shared_hidden_groups_or_values(self):
        self.catalog.set_configuration("demo/assets", {
            "groups": [
                {"key": "column:category", "enabled": False},
                {"key": "column:priority", "options": ["low"]},
            ], "defaultSelections": {},
        })
        groups = self.catalog.editor_groups(
            "demo/assets", _Stype(), [self.asset_a, self.asset_b],
            include_hidden=False, local_groups=[
                {"key": "column:category", "enabled": True},
                {"key": "column:priority", "options": ["high", "low"]},
            ],
        )
        by_key = {group["key"]: group for group in groups}
        self.assertNotIn("column:category", by_key)
        self.assertEqual([option["key"] for option in by_key["column:priority"]["options"]], ["low"])

    def test_versioned_configuration_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "fields: version"):
            self.catalog.set_configuration("demo/assets", {
                "version": 2,
                "groups": [{"key": "status", "enabled": True}],
                "defaultSelections": {},
            })

    def test_restored_direct_selection_compiles_before_facet_catalog_loads(self):
        groups = self.catalog.groups(
            "demo/assets", _Stype(), [],
            {"column:category": {"props"}},
            {}, "artist", [],
        )

        category = next(
            group for group in groups
            if group["key"] == "column:category"
        )
        self.assertEqual(category["column"], "category")
        self.assertTrue(category["options"][0]["selected"])


if __name__ == "__main__":
    unittest.main()

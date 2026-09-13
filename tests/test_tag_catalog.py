from __future__ import annotations

import time
import unittest
from unittest.mock import patch

from thlib.ui.controllers.view_state import ViewStateMixin


class _Signal:
    def __init__(self):
        self.emissions = 0
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)

    def emit(self, value=None):
        self.emissions += 1
        for callback in list(self.callbacks):
            callback(value)


class _DeferredWorker:
    def __init__(self, operation):
        self.operation = operation
        self.result = _Signal()
        self.error = _Signal()
        self.metadata = None
        self.started = False

    def add_result_data(self, metadata):
        self.metadata = metadata

    def get_result_data(self):
        return self.metadata

    def start(self):
        self.started = True


class _DeferredPool:
    is_stopped = False

    def __init__(self):
        self.worker = None

    def add_task(self, operation):
        self.worker = _DeferredWorker(operation)
        return self.worker


class _Project:
    def get_code(self):
        return "demo"


class _SearchType:
    def get_columns_info(self):
        return {"keywords": {"type": "text"}}

    def get_project(self):
        return _Project()

    def get_code(self):
        return "demo/asset"


class _Tab:
    def __init__(self):
        self.tag_column = ""


class _Section:
    search_type = "demo/asset"


class _CachedCatalogHarness(ViewStateMixin):
    def __init__(self, records):
        self.tab = _Tab()
        self._tag_catalog_cache = {
            self._tag_catalog_cache_key(
                "demo", "demo/asset", "keywords"
            ): {
                "loadedAt": time.time(),
                "records": records,
            }
        }
        self._tag_context_key = ""
        self._tag_workers = {}
        self._tag_records = []
        self._tag_loading = False
        self._tag_error = ""
        self._current_project_code = "demo"
        self.tag_cloud_changed = _Signal()

    def _current_tab(self):
        return self.tab

    def _current_section(self):
        return _Section()

    def _active_stype(self):
        return _SearchType()


class TagCatalogTests(unittest.TestCase):
    def test_query_pages_whole_search_type_without_active_filters(self):
        pages = [
            [
                {"keywords": "Alpha, Beta"},
                {"keywords": "alpha"},
            ],
            [{"keywords": "Gamma"}],
        ]
        with patch(
            "thlib.tactic_classes.server_query",
            side_effect=pages,
        ) as query:
            records = ViewStateMixin._query_tag_catalog(
                "demo",
                "demo/asset",
                "keywords",
                page_size=2,
            )

        self.assertEqual(
            [(row["tag"], row["count"]) for row in records],
            [("Alpha", 2), ("Beta", 1), ("Gamma", 1)],
        )
        self.assertEqual(query.call_count, 2)
        for call in query.call_args_list:
            self.assertEqual(call.kwargs["filters"], [])
            self.assertEqual(call.kwargs["columns"], ["keywords"])
            self.assertEqual(call.kwargs["order_bys"], [])
        self.assertEqual(
            [call.kwargs["offset"] for call in query.call_args_list],
            [0, 2],
        )

    def test_fresh_project_search_type_cache_skips_server_work(self):
        cached = [{
            "tag": "FromEntireType",
            "count": 7,
            "weight": 1.0,
            "column": "keywords",
        }]
        harness = _CachedCatalogHarness(cached)

        harness.request_tag_cloud(False)

        self.assertEqual(harness._tag_records, cached)
        self.assertFalse(harness._tag_loading)
        self.assertEqual(harness._tag_workers, {})
        self.assertEqual(harness.tab.tag_column, "keywords")
        self.assertEqual(harness.tag_cloud_changed.emissions, 1)

    def test_forced_reload_only_schedules_server_query(self):
        from thlib.environment import env_inst

        harness = _CachedCatalogHarness([])
        pool = _DeferredPool()
        with (
            patch.object(env_inst, "server_pool", pool),
            patch.object(
                harness,
                "_query_tag_catalog",
                return_value=[],
            ) as query,
        ):
            harness.request_tag_cloud(True)

        self.assertIsNotNone(pool.worker)
        self.assertTrue(pool.worker.started)
        query.assert_not_called()
        self.assertEqual(
            pool.worker.metadata[0],
            harness._tag_context_key,
        )

    def test_result_is_cached_even_after_context_changes(self):
        harness = _CachedCatalogHarness([])
        cache_key = harness._tag_catalog_cache_key(
            "demo", "demo/asset", "keywords"
        )
        harness._tag_context_key = "another-context"
        harness._write_tag_catalog_cache = lambda: None

        harness._tag_cloud_result(([{"tag": "New"}], (cache_key, "keywords")))

        self.assertEqual(
            harness._tag_catalog_cache[cache_key]["records"],
            [{"tag": "New"}],
        )
        self.assertEqual(harness._tag_records, [])


if __name__ == "__main__":
    unittest.main()

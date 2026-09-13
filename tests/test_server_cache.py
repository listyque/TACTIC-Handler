from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from thlib import server_cache
from thlib.ui.cache_controller import ServerCacheController
from thlib.ui.controller import ApplicationController
from thlib.ui.controllers.search_runtime import SearchRuntimeMixin
from thlib.ui.controllers.types import SearchTabSession, SectionSession


class ServerCacheTests(unittest.TestCase):
    def setUp(self):
        self.documents = {}
        self.identity = ["https://tactic.example", "listy", "project"]

        def read_config(filename="settings", unique_id="", **_kwargs):
            value = self.documents.get((unique_id, filename))
            if isinstance(value, dict):
                return dict(value)
            return value

        def write_config(
                value=None, filename="settings", unique_id="", remove=False,
                **_kwargs):
            if remove and not filename:
                prefix = unique_id.rstrip("/") + "/"
                self.documents = {
                    key: document
                    for key, document in self.documents.items()
                    if key[0] != unique_id and not key[0].startswith(prefix)
                }
                return
            if remove:
                self.documents.pop((unique_id, filename), None)
                return
            self.documents[(unique_id, filename)] = value

        self.patches = (
            patch.object(
                server_cache, "_environment_api",
                return_value=(read_config, write_config),
            ),
            patch.object(
                server_cache, "_identity",
                side_effect=lambda project="": (
                    self.identity[0], self.identity[1], project,
                ),
            ),
        )
        for current in self.patches:
            current.start()

    def tearDown(self):
        for current in reversed(self.patches):
            current.stop()

    def test_entry_is_scoped_by_server_login_and_project(self):
        self.assertTrue(server_cache.write_entry(
            "search", "assets", {"codes": ["A"]}, "project"
        ))
        self.assertEqual(
            server_cache.read_entry("search", "assets", "project"),
            {"codes": ["A"]},
        )
        self.identity[1] = "admin"
        self.assertIsNone(
            server_cache.read_entry("search", "assets", "project")
        )

    def test_cache_uses_readable_scope_and_one_document_per_domain(self):
        server_cache.write_entry(
            "reference", "project-catalog", {"codes": ["DEMO"]}, "project"
        )

        data_documents = [
            key for key in self.documents
            if key[0].startswith("cache/server_data/")
            and key[1] != "control"
        ]
        self.assertEqual(len(data_documents), 1)
        unique_id, filename = data_documents[0]
        self.assertIn("project__listy__tactic.example", unique_id)
        self.assertEqual(filename, "reference")

    def test_domain_preference_disables_reads_and_writes(self):
        values = dict(server_cache.DEFAULT_CACHE_PREFERENCES)
        values["messages"] = False
        server_cache.update_preferences(values)
        self.assertFalse(server_cache.write_entry(
            "messages", "chat", {"messages": []}, "sthpw"
        ))
        self.assertIsNone(
            server_cache.read_entry("messages", "chat", "sthpw")
        )

    def test_preferences_with_unexpected_fields_are_not_adopted(self):
        self.documents[("ui_conf", "data_cache")] = {
            "enabled": {"messages": False},
            "obsolete": True,
        }

        self.assertTrue(server_cache.preferences()["messages"])

    def test_incompatible_domain_document_is_replaced_not_migrated(self):
        cache_token = server_cache.token("search", "project")
        unique_id, filename = server_cache._domain_path(
            cache_token.scope, cache_token.domain
        )
        self.documents[(unique_id, filename)] = {
            "obsoleteSchemaVersion": 99,
            "domain": "search",
            "scope": cache_token.scope,
            "entries": {
                server_cache._entry_digest("old"): {
                    "key": "old", "value": [1],
                },
            },
        }

        self.assertIsNone(
            server_cache.read_entry("search", "old", "project")
        )
        self.assertTrue(server_cache.write_entry(
            "search", "current", [2], "project"
        ))

        document = self.documents[(unique_id, filename)]
        self.assertNotIn("obsoleteSchemaVersion", document)
        self.assertEqual(set(document), {"domain", "scope", "entries"})
        self.assertEqual(len(document["entries"]), 1)
        self.assertEqual(
            next(iter(document["entries"].values()))["key"], "current"
        )

    def test_domain_invalidation_rejects_previous_entries(self):
        server_cache.write_entry("tasks", "mine", [1], "project")
        server_cache.invalidate_domains(("tasks",), "project")
        self.assertIsNone(
            server_cache.read_entry("tasks", "mine", "project")
        )

    def test_stale_projection_survives_revision_but_not_cache_clear(self):
        calendar = {
            "completeHistory": True,
            "dayCounts": {"2026-08-20": 4, "2026-07-18": 9},
        }
        server_cache.write_entry(
            "activity", "calendar:all", calendar, "project"
        )
        server_cache.invalidate_domains(("activity",), "project")

        self.assertIsNone(server_cache.read_entry(
            "activity", "calendar:all", "project"
        ))
        self.assertEqual(
            server_cache.read_stale_entry(
                "activity", "calendar:all", "project"
            ),
            calendar,
        )

        server_cache.clear_all()
        self.assertIsNone(server_cache.read_stale_entry(
            "activity", "calendar:all", "project"
        ))

    def test_clear_generation_rejects_late_worker_write(self):
        token = server_cache.token("notes", "project")
        server_cache.clear_all()
        self.assertFalse(server_cache.write_entry(
            "notes", "asset", {"notes": []}, "project",
            expected_token=token,
        ))

    def test_change_batch_invalidates_mapped_domains(self):
        server_cache.write_entry("tasks", "all", [1], "project")
        server_cache.write_entry("search", "assets", [1], "project")
        changed = server_cache.apply_change_batch([{
            "searchType": "sthpw/task",
            "projectCode": "project",
        }])
        self.assertIn("tasks", changed["project"])
        self.assertIsNone(
            server_cache.read_entry("tasks", "all", "project")
        )
        self.assertIsNone(
            server_cache.read_entry("search", "assets", "project")
        )

    def test_clear_removes_change_cursor(self):
        server_cache.write_cursor("server_changes", "2026-08-25", "project")
        self.assertEqual(
            server_cache.read_cursor("server_changes", "project"),
            "2026-08-25",
        )
        server_cache.clear_all()
        self.assertEqual(
            server_cache.read_cursor("server_changes", "project"), ""
        )

    def test_clear_removes_cache_documents_without_empty_placeholders(self):
        server_cache.write_entry("reference", "catalog", [1], "project")
        server_cache.write_entry("search", "assets", [2], "project")
        self.documents[(
            "cache/server_data/unknown_old_scope", "reference_07",
        )] = {}

        server_cache.clear_all()

        data_documents = [
            (key, value) for key, value in self.documents.items()
            if key[0].startswith("cache/server_data/")
            and key != ("cache/server_data", "control")
        ]
        self.assertEqual(data_documents, [])

    def test_preference_change_emits_only_changed_domains(self):
        controller = ServerCacheController()
        invalidations = []
        controller.invalidated.connect(invalidations.append)

        values = dict(server_cache.DEFAULT_CACHE_PREFERENCES)
        values["search"] = False
        controller.apply_configuration(values)

        self.assertEqual(invalidations, [{
            "preferences": True,
            "domains": ["search"],
        }])

    def test_hard_reset_keeps_hot_search_tabs_loaded_without_blanking_rows(self):
        tab = SearchTabSession("tab", "Assets", loaded=True)
        tab.sobjects = [object()]
        tab.selected_node_id = "asset-one"
        tab.selected_node_ids = ["asset-one", "asset-two"]
        worker = SimpleNamespace(cancelled=False)
        worker.cancel = lambda: setattr(worker, "cancelled", True)
        emitted = []
        quick_filter_invalidations = []
        dummy = SimpleNamespace(
            _current_project_code="project",
            _tag_catalog_cache={"tag": {}},
            _tag_context_key="context",
            _search_workers={"tab": worker},
            _pending_search_loads={"tab": object()},
            _sessions={
                "assets": SectionSession(
                    "assets", "Assets", "", "prod/asset", tabs=[tab]
                )
            },
            _active_request_id="request",
            _quick_filter_runtime=SimpleNamespace(
                invalidate=lambda: quick_filter_invalidations.append(True)
            ),
            _set_loading=lambda *_args: None,
            search_state_changed=SimpleNamespace(
                emit=lambda: emitted.append("search")
            ),
            tag_cloud_changed=SimpleNamespace(
                emit=lambda: emitted.append("tags")
            ),
            quick_filters_changed=SimpleNamespace(
                emit=lambda: emitted.append("quick-filters")
            ),
        )

        ApplicationController.apply_cache_invalidation(dummy, {"all": True})

        self.assertTrue(tab.loaded)
        self.assertEqual(len(tab.sobjects), 1)
        self.assertEqual(tab.selected_node_id, "asset-one")
        self.assertEqual(
            tab.selected_node_ids, ["asset-one", "asset-two"]
        )
        self.assertTrue(worker.cancelled)
        self.assertEqual(dummy._pending_search_loads, {})
        self.assertEqual(dummy._tag_catalog_cache, {})
        self.assertEqual(quick_filter_invalidations, [True])
        self.assertEqual(emitted, ["search", "tags", "quick-filters"])

    def test_search_rehydrates_cache_and_explicit_refresh_bypasses_it(self):
        import thlib.tactic_classes as tc
        from thlib.environment import env_inst

        native = object()
        hydrated = (OrderedDict((("ASSET001", native),)), {"total": 1})
        raw = {"sobjects_list": [{"code": "ASSET001"}]}
        with (
            patch.object(tc, "get_snapshots_updates_list", return_value=[]),
            patch.object(
                tc, "get_sobjects", return_value=(hydrated, raw)
            ) as query,
            patch.object(
                tc, "hydrate_sobjects_payload", return_value=hydrated
            ) as hydrate,
            patch.object(env_inst, "get_stype_by_code", return_value=None),
        ):
            first = SearchRuntimeMixin._query_sobjects(
                "sthpw/task", "project", (), [], 25, 0
            )
            second = SearchRuntimeMixin._query_sobjects(
                "sthpw/task", "project", (), [], 25, 0
            )
            forced = SearchRuntimeMixin._query_sobjects(
                "sthpw/task", "project", (), [], 25, 0,
                bypass_cache=True,
            )

        self.assertEqual(query.call_count, 2)
        hydrate.assert_called_once()
        self.assertFalse(first[1]["cacheHit"])
        self.assertTrue(second[1]["cacheHit"])
        self.assertFalse(forced[1]["cacheHit"])

    def test_saved_projection_queries_every_page_through_the_cache_path(self):
        from thlib.environment import env_inst

        def page_query(
            _search_type, _project, _base, _extra, _limit, offset,
            _sort_mode,
        ):
            records = [
                SimpleNamespace(
                    get_search_key=lambda value=offset + index:
                        f"demo/asset?code=ASSET{value:03d}"
                )
                for index in range(2)
            ]
            return records, {"cacheHit": True}, None

        with (
            patch.object(
                SearchRuntimeMixin,
                "_query_sobjects",
                side_effect=page_query,
            ) as query,
            patch.object(env_inst, "get_project_by_code", return_value=None),
        ):
            records, info, stype = (
                SearchRuntimeMixin._query_saved_projection(
                    "demo/asset", "project", (), [], 25,
                    [0, 25, 50], "name_asc", 75, 180, False,
                )
            )

        self.assertEqual(len(records), 6)
        self.assertEqual(
            [call.args[5] for call in query.call_args_list],
            [0, 25, 50],
        )
        self.assertTrue(info["cachedProjection"])
        self.assertEqual(info["pageOffsets"], [0, 25, 50])
        self.assertEqual(info["nextOffset"], 75)
        self.assertEqual(info["savedTotal"], 180)
        self.assertIsNone(stype)

    def test_search_cache_identity_includes_search_type(self):
        assets = SearchRuntimeMixin._search_cache_key(
            "demo/asset", (), [], 25, 0, "name_asc"
        )
        shots = SearchRuntimeMixin._search_cache_key(
            "demo/shot", (), [], 25, 0, "name_asc"
        )

        self.assertNotEqual(assets, shots)


class ServerCacheFileTests(unittest.TestCase):
    def setUp(self):
        from thlib import environment

        self.directory = Path(self.enterContext(TemporaryDirectory()))
        for current in (
            patch.object(
                environment.env_mode, "current_path", str(self.directory),
            ),
            patch.object(
                environment.env_server, "get_cur_srv_preset",
                return_value="test-preset",
            ),
            patch.object(
                environment.env_mode, "get_mode", return_value="standalone",
            ),
            patch.object(
                server_cache, "_identity",
                side_effect=lambda project="": (
                    "https://tactic.example", "tester", project,
                ),
            ),
        ):
            self.enterContext(current)

    def test_concurrent_cache_writes_keep_each_entry(self):
        token = server_cache.token("tasks", "project")
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(
                    server_cache.write_entry,
                    "tasks", f"scope-{index}", {"index": index}, "project",
                    expected_token=token,
                )
                for index in range(24)
            ]
            results = [future.result(timeout=10) for future in futures]

        self.assertEqual(results, [True] * 24)
        for index in range(24):
            cached = server_cache.read_entry(
                "tasks", f"scope-{index}", "project",
            )
            self.assertEqual(cached, {"index": index})
        self.assertEqual(len(list(self.directory.rglob("tasks.json"))), 1)
        self.assertEqual(list(self.directory.rglob("*.tmp")), [])

    @unittest.skipUnless(sys.platform == "win32", "Windows file sharing")
    def test_task_refresh_with_windows_reader_does_not_repeat_query(self):
        from thlib import environment
        import thlib.tactic_classes as tc
        from thlib.ui.task_workspace import TaskWorkspaceStore

        project = SimpleNamespace(info={"code": "project"})
        tasks = [
            tc.Task({"code": f"TASK{index}", "process": "publish"}, project)
            for index in range(9)
        ]
        with patch.object(
            environment.env_inst, "get_project_by_code", return_value=project,
        ), patch.object(
            tc, "get_task_workspace_page",
            side_effect=[
                {"tasks": [task], "parents": [], "total": 1}
                for task in tasks
            ],
        ) as query, ThreadPoolExecutor(max_workers=1) as executor:
            def load_scope(bypass_cache=False):
                return executor.submit(
                    TaskWorkspaceStore.load_scope,
                    "project", "", "project", None, "", [],
                    bypass_cache=bypass_cache,
                ).result(timeout=10)

            load_scope()
            path, = self.directory.rglob("tasks.json")
            for task in tasks[1:]:
                with path.open(encoding="utf-8") as reader, patch.object(
                    environment.time, "sleep",
                    side_effect=lambda _delay: reader.close(),
                ) as sleep:
                    result = load_scope(bypass_cache=True)

                sleep.assert_called_once()
                self.assertIs(result["tasks"][0], task)
                self.assertFalse(result["page"]["cacheHit"])
            cached = load_scope()

        self.assertEqual(query.call_count, 9)
        self.assertTrue(cached["page"]["cacheHit"])
        self.assertEqual(cached["tasks"][0].get_code(), "TASK8")
        self.assertEqual(list(self.directory.rglob("*.tmp")), [])


if __name__ == "__main__":
    unittest.main()

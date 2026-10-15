from __future__ import annotations

import json
import sys
import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, call, patch

from thlib import tactic_classes as tc
from thlib import tactic_query as tq
from thlib import global_functions as gf
from thlib import environment
from thlib import server_cache


class CompatibleUpdateTests(unittest.TestCase):
    def test_failed_forced_catalog_refresh_preserves_existing_cache(self):
        with (
            patch.object(tc.env_mode, "get_mode", return_value="standalone"),
            patch.object(server_cache, "invalidate_domains") as invalidate,
            patch.object(server_cache, "token", return_value=None),
            patch.object(
                tc, "execute_procedure_serverside",
                side_effect=ConnectionError("server unavailable"),
            ),
        ):
            with self.assertRaises(ConnectionError):
                tc.get_all_projects_and_logins(force=True)
        invalidate.assert_not_called()

    def test_late_reference_request_does_not_restore_old_user_catalogs(self):
        identity = {"user": "old-user"}
        previous_projects = {"new": object()}
        previous_logins = {"new": object()}

        def finish_old_request(*_args, **_kwargs):
            identity["user"] = "new-user"
            return {"projects": [], "logins": []}

        with (
            patch.object(tc.env_server, "get_server", return_value="server"),
            patch.object(tc.env_server, "get_user", side_effect=lambda: identity["user"]),
            patch.object(tc.env_server, "get_ticket", return_value="ticket"),
            patch.object(tc.env_inst, "get_current_login", return_value="old-user"),
            patch.object(tc.env_inst, "projects", previous_projects),
            patch.object(tc.env_inst, "logins", previous_logins),
            patch.object(server_cache, "invalidate_domains"),
            patch.object(server_cache, "token", return_value=None),
            patch.object(tc, "execute_procedure_serverside", side_effect=finish_old_request),
        ):
            tc.get_all_projects_and_logins(force=True)
            self.assertIs(tc.env_inst.projects, previous_projects)
            self.assertIs(tc.env_inst.logins, previous_logins)

    def test_explicit_authentication_does_not_publish_unverified_ticket(self):
        server = Mock()
        server.get_ticket.return_value = "new-ticket"

        with (
            patch.object(tc, "TacticServerStub", return_value=server),
            patch.object(tc.env_server, "get_proxy", return_value={"enabled": False}),
            patch.object(tc.env_server, "get_ticket", return_value="old-ticket"),
            patch.object(tc.env_server, "set_ticket") as set_ticket,
        ):
            tc.server_auth(
                "server", project="sthpw", login="artist",
                password="password", get_ticket=True,
            )

        server.set_ticket.assert_called_once_with("new-ticket")
        set_ticket.assert_not_called()

    def test_signed_out_session_does_not_request_ticket_with_empty_password(self):
        server = Mock()

        with (
            patch.object(tc, "TacticServerStub", return_value=server),
            patch.object(tc.env_server, "get_proxy", return_value={"enabled": False}),
            patch.object(tc.env_server, "get_ticket", return_value=None),
        ):
            with self.assertRaisesRegex(PermissionError, "signed out"):
                tc.server_start()

        server.get_ticket.assert_not_called()

    def test_code_and_id_search_keys_are_sent_in_separate_requests(self):
        server = Mock()
        server.update_multiple.side_effect = [
            [{"__search_key__": "sthpw/task?code=TASK001"}],
            [{"__search_key__": "sthpw/task?id=17"}],
        ]
        data = {
            "sthpw/task?code=TASK001": {"status": "Ready"},
            "sthpw/task?code=TASK002": {"status": "Ready"},
            "sthpw/task?id=17": {"status": "Ready"},
        }

        result = tc.update_multiple_compatible(server, data, triggers=True)

        self.assertEqual(server.update_multiple.call_args_list, [
            call(data={
                "sthpw/task?code=TASK001": {"status": "Ready"},
                "sthpw/task?code=TASK002": {"status": "Ready"},
            }, triggers=True),
            call(data={
                "sthpw/task?id=17": {"status": "Ready"},
            }, triggers=True),
        ])
        server.update.assert_not_called()
        self.assertEqual(result, [
            {"__search_key__": "sthpw/task?code=TASK001"},
            {"__search_key__": "sthpw/task?id=17"},
        ])


class CustomScriptMirrorTests(unittest.TestCase):
    def test_nested_title_is_a_nested_script_path(self):
        script = {
            "folder": "batch",
            "title": "old/scheduler_classes",
            "language": "local_python",
        }
        with TemporaryDirectory() as directory, patch.object(
            environment.env_mode, "get_current_path", return_value=directory
        ):
            path = tc._custom_script_local_path(script, "demo")

        self.assertEqual(
            Path(path),
            Path(directory)
            / "custom_scripts/demo/batch/old/scheduler_classes.py",
        )
        self.assertEqual(
            tc.normalize_custom_script_path("batch", "old/scheduler_classes"),
            ("batch/old", "scheduler_classes"),
        )

    def test_nested_title_is_downloaded_into_the_nested_folder(self):
        values = {
            "folder": "batch",
            "title": "old/scheduler_classes",
            "language": "local_python",
            "script": "value = 1\n",
            "timestamp": None,
        }
        script = Mock(
            info=values,
            get_value=Mock(side_effect=values.get),
        )
        server = Mock()
        server.build_search_type.return_value = "config/custom_script?project=demo"

        with (
            TemporaryDirectory() as directory,
            patch.object(
                environment.env_mode, "get_current_path", return_value=directory
            ),
            patch.object(tc, "server_start", return_value=server),
            patch.object(
                tc, "get_sobjects", return_value=({"SCRIPT": script}, {})
            ),
        ):
            tc.get_custom_scripts(store_locally=True, project="demo")
            path = (
                Path(directory)
                / "custom_scripts/demo/batch/old/scheduler_classes.py"
            )
            self.assertEqual(path.read_text(encoding="utf-8"), "value = 1\n")

    def test_server_timestamp_controls_local_script_rewrites(self):
        with TemporaryDirectory() as directory, patch.object(
            environment.env_mode, "get_current_path", return_value=directory
        ):
            environment.env_write_file(
                "print('current')\n", "batch", "runner.py", "demo",
                "2023-11-14 22:13:20",
            )
            script_path = Path(directory) / "custom_scripts/demo/batch/runner.py"
            unchanged_timestamp = script_path.stat().st_mtime_ns

            environment.env_write_file(
                "print('must not replace')\n", "batch", "runner.py", "demo",
                "2023-11-14 22:13:20",
            )
            self.assertEqual(script_path.stat().st_mtime_ns, unchanged_timestamp)
            self.assertEqual(
                script_path.read_text(encoding="utf-8"),
                "print('current')\n",
            )

            environment.env_write_file(
                "print('updated')\n", "batch", "runner.py", "demo",
                "2023-11-14 22:13:21",
            )
            self.assertEqual(
                script_path.read_text(encoding="utf-8"),
                "print('updated')\n",
            )

    def test_script_manifest_avoids_unchanged_source_download(self):
        manifest = [{
            "code": "CUSTOM_SCRIPT00001",
            "folder": "batch",
            "title": "runner",
            "language": "local_python",
            "timestamp": "2023-11-14 22:13:20",
        }]
        server = Mock()
        server.build_search_type.return_value = (
            "config/custom_script?project=demo"
        )
        server.query.return_value = manifest

        with TemporaryDirectory() as directory:
            with (
                patch.object(
                    environment.env_mode, "get_current_path",
                    return_value=directory,
                ),
                patch.object(tc, "server_start", return_value=server),
                patch.object(tc, "get_custom_scripts") as download,
            ):
                environment.env_write_file(
                    "print('current')\n", "batch", "runner.py", "demo",
                    manifest[0]["timestamp"],
                )

                self.assertEqual(
                    tc.sync_custom_scripts("demo"), (None, False)
                )
                download.assert_not_called()

                manifest[0]["timestamp"] = "2023-11-14 22:13:21"
                download.return_value = {"CUSTOM_SCRIPT00001": object()}
                scripts, changed = tc.sync_custom_scripts("demo")

        self.assertTrue(changed)
        self.assertEqual(scripts, {"CUSTOM_SCRIPT00001": download.return_value[
            "CUSTOM_SCRIPT00001"
        ]})
        download.assert_called_once_with(store_locally=True, project="demo")
        server.query.assert_called_with(
            "config/custom_script?project=demo",
            columns=["code", "folder", "title", "language", "timestamp"],
            order_bys=["folder", "title"],
        )

    def test_full_server_sync_prunes_only_obsolete_script_files(self):
        scripts = [{
            "folder": "batch", "title": "keep",
            "language": "local_python",
        }]
        with TemporaryDirectory() as directory, patch.object(
            environment.env_mode, "get_current_path", return_value=directory
        ):
            root = Path(directory) / "custom_scripts/demo/batch"
            root.mkdir(parents=True)
            keep = root / "keep.py"
            obsolete = root / "obsolete.py"
            package = root / "__init__.py"
            unrelated = root / "notes.txt"
            for path in (keep, obsolete, package, unrelated):
                path.write_text("value", encoding="utf-8")

            tc._prune_custom_script_mirror(scripts, "demo")

            self.assertTrue(keep.exists())
            self.assertFalse(obsolete.exists())
            self.assertTrue(package.exists())
            self.assertTrue(unrelated.exists())


class FileWebPathTests(unittest.TestCase):
    def test_https_server_address_is_not_prefixed_with_http(self):
        file_object = tc.File({
            "metadata": {},
            "relative_dir": "demo/articles",
            "file_name": "guide.png",
            "st_size": 1,
            "type": "main",
            "base_type": "file",
        })
        with (
            patch.object(
                tc.env_server, "get_server",
                return_value="https://tactic.example.test",
            ),
            patch.object(
                tc.env_tactic, "get_base_dir",
                return_value={"value": ["assets"]},
            ),
        ):
            self.assertEqual(
                file_object.get_full_web_path(),
                "https://tactic.example.test/assets/"
                "demo/articles/guide.png",
            )


class SObjectDeleteTests(unittest.TestCase):
    def setUp(self):
        self.sobject = tc.SObject({"__search_key__": "sthpw/note?code=NOTE0001"})

    def test_delete_has_no_dependency_list_by_default(self):
        with patch.object(tc, "execute_procedure_serverside", return_value=True) as execute:
            self.assertTrue(self.sobject.delete_sobject())

        self.assertIsNone(execute.call_args.args[1]["list_dependencies"])

    def test_explicit_dependencies_are_preserved(self):
        with patch.object(tc, "execute_procedure_serverside", return_value=True) as execute:
            self.sobject.delete_sobject(list_dependencies=["sthpw/file"])

        self.assertEqual(
            execute.call_args.args[1]["list_dependencies"],
            {"related_types": ["sthpw/file"]},
        )


class NoteMutationTests(unittest.TestCase):
    def test_task_note_uses_explicit_parent_project(self):
        server = Mock()
        server.insert.return_value = {"code": "NOTE001"}
        with patch.object(tc, "server_start", return_value=server) as start:
            result = tc.add_note(
                "sthpw/task?code=TASK001", "model", "model", "Ready",
                "artist", project_code="demo",
            )

        start.assert_called_once_with(project="demo")
        server.insert.assert_called_once_with(
            "sthpw/note", {
                "process": "model", "context": "model",
                "note": "Ready", "login": "artist",
            }, parent_key="sthpw/task?code=TASK001", triggers=True,
        )
        self.assertEqual(result, {"code": "NOTE001"})

    def test_empty_insert_result_is_not_reported_as_a_sent_note(self):
        server = Mock()
        server.insert.return_value = None
        with patch.object(tc, "server_start", return_value=server):
            with self.assertRaisesRegex(RuntimeError, "did not create"):
                tc.add_note(
                    "sthpw/task?code=TASK001", "model", "model", "Ready",
                    "artist", project_code="demo",
                )


class LoginMembershipTests(unittest.TestCase):
    def test_login_constructor_builds_reverse_group_membership(self):
        group = tc.LoginGroup({
            "login_group": "artists",
            "code": "GROUP_ARTISTS",
            "project_code": "demo",
            "access_rules": "",
        })

        login = tc.Login(
            {"login": "artist", "code": "artist", "project_code": "demo"},
            [group],
            [{"login": "artist", "login_group": "artists"}],
        )

        self.assertEqual(login.get_login_groups(), [group])
        self.assertEqual(group.get_logins(), [login])


class ServerCountQueryTests(unittest.TestCase):
    def test_relation_count_uses_unique_related_objects(self):
        class Record:
            def __init__(self, code):
                self.code = code

        class Search:
            def __init__(self, _search_type):
                pass

            @staticmethod
            def get_by_search_key(_search_key):
                return object()

            @staticmethod
            def eval(_expression):
                return [Record("TEXTURE001"), Record("TEXTURE001"),
                        Record("TEXTURE002")]

        search_module = ModuleType("pyasm.search")
        search_module.Search = Search
        search_module.SearchKey = type("SearchKey", (), {
            "get_by_sobject": staticmethod(
                lambda record, use_id=False: record.code
            ),
        })
        pyasm_module = ModuleType("pyasm")
        pyasm_module.search = search_module
        fake_server = type("Server", (), {
            "split_search_key": staticmethod(
                lambda _key: ("demo/asset", "ASSET001")
            ),
        })()

        with patch.dict(sys.modules, {
            "pyasm": pyasm_module,
            "pyasm.search": search_module,
        }), patch.object(tq, "server", fake_server, create=True):
            result = tq.get_notes_and_stypes_counts(
                [],
                "demo/asset?project=demo&code=ASSET001",
                [{
                    "key": "demo/texture_in_asset",
                    "searchType": "demo/texture",
                    "expression": "@SOBJECT(demo/texture)",
                }],
            )

        self.assertEqual(result["stypes"], {
            "demo/texture_in_asset": 2,
        })

    def test_process_counts_use_one_query_per_table(self):
        searched = []

        class Record:
            def __init__(self, process, code=""):
                self.process = process
                self.code = code

            def get_value(self, name):
                return {
                    "process": self.process,
                    "code": self.code,
                    "project_code": "demo",
                }.get(name)

            def get_data(self):
                return {
                    "process": self.process,
                    "code": self.code,
                    "project_code": "demo",
                }

        table_records = {
            "sthpw/note": [Record("model"), Record("model")],
            "sthpw/task": [
                Record("model", "TASK001"),
                Record("render", "TASK002"),
            ],
        }

        class Search:
            def __init__(self, search_type):
                self.search_type = search_type
                self.filters = []
                searched.append(self)

            def get_by_search_key(self, _search_key):
                class ParentRecord:
                    @staticmethod
                    def get_value(name):
                        raise AssertionError(
                            "Parent Search Type must not be queried for " + name
                        )

                return ParentRecord()

            def add_op_filters(self, filters):
                self.filters = list(filters)

            def add_filter(self, name, value):
                self.filters.append((name, value))

            def add_filters(self, name, values):
                self.filters.append((name, values))

            def get_sobjects(self):
                if self.search_type == "sthpw/note" and any(
                        name == "search_code" and isinstance(value, list)
                        for name, value in self.filters):
                    return []
                return list(table_records.get(self.search_type, []))

            def add_relationship_filter(self, _sobject):
                pass

            def get_count(self, _fast):
                return {"demo/shot": 3}.get(self.search_type, -1)

        search_module = ModuleType("pyasm.search")
        search_module.Search = Search
        search_module.SearchKey = type("SearchKey", (), {
            "get_by_sobject": staticmethod(
                lambda record, use_id=False: "sthpw/task?code=" + record.code
            ),
        })
        pyasm_module = ModuleType("pyasm")
        pyasm_module.search = search_module
        fake_server = type("Server", (), {
            "split_search_key": staticmethod(
                lambda _key: ("demo/asset", "ASSET001")
            ),
        })()

        with patch.dict(sys.modules, {
            "pyasm": pyasm_module,
            "pyasm.search": search_module,
        }), patch.object(tq, "server", fake_server, create=True):
            result = tq.get_notes_and_stypes_counts(
                ["model", "render", "model"],
                "demo/asset?project=demo&code=ASSET001",
                ["demo/shot", "demo/missing"],
            )

        self.assertEqual(result["notes"], {"model": 2, "render": 0})
        self.assertEqual(result["tasks"], {"model": 1, "render": 1})
        self.assertEqual(
            result["stypes"], {"demo/shot": 3, "demo/missing": 0}
        )
        table_queries = [
            search for search in searched
            if search.search_type in ("sthpw/note", "sthpw/task")
        ]
        self.assertEqual(len(table_queries), 2)
        aggregate_queries = [
            search for search in table_queries
            if search.filters and search.filters[0] == (
                "process", ["model", "render"]
            )
        ]
        self.assertEqual(len(aggregate_queries), 2)
        for search in aggregate_queries:
            self.assertEqual(search.filters[0], (
                "process", ["model", "render"]
            ))
        self.assertEqual(
            result["taskDetails"]["model"][0]["code"], "TASK001"
        )


class DuplicateSObjectQueryTests(unittest.TestCase):
    def test_duplicate_does_not_copy_related_objects(self):
        class Source:
            @staticmethod
            def get_project_code():
                return "demo"

            @staticmethod
            def get_base_search_type():
                return "demo/asset"

            @staticmethod
            def get_data():
                return {
                    "code": "ASSET001",
                    "id": 1,
                    "name": "Original",
                    "description": "Keep me",
                }

            @staticmethod
            def get_related_sobjects(_search_type):
                raise AssertionError("Related objects must not be duplicated")

        source = Source()

        class ServerBackend:
            @staticmethod
            def _get_sobjects(_search_keys):
                return [source]

        inserted = []
        fake_server = type("Server", (), {
            "server": ServerBackend(),
            "set_project": staticmethod(lambda _project: None),
            "insert": staticmethod(
                lambda search_type, data: inserted.append(
                    (search_type, dict(data))
                ) or {
                    "__search_key__": "demo/asset?code=ASSET002",
                    "code": "ASSET002",
                }
            ),
        })()

        with patch.object(tq, "server", fake_server, create=True):
            result = json.loads(tq.duplicate_sobjects(
                ["demo/asset?code=ASSET001"],
                {
                    "new_name": "Duplicate",
                    "related_search_type": ["sthpw/note"],
                },
            ))

        self.assertEqual(result["code"], "ASSET002")
        self.assertEqual(inserted, [(
            "demo/asset",
            {"name": "Duplicate", "description": "Keep me"},
        )])


class CustomScriptExecutionTests(unittest.TestCase):
    def test_existing_local_file_skips_tactic_script_refresh(self):
        project = Mock()
        editor = Mock()
        editor.execute_source_code.return_value = "executed"

        with TemporaryDirectory() as directory:
            script = Path(directory) / "batch_dispatcher_runner.py"
            script.write_text(
                "batch_dispatcher_window = batch_dispatcher.show()\n",
                encoding="utf-8",
            )
            with (
                patch.object(tc.env_inst, "set_current_project") as select,
                patch.object(
                    tc.env_inst, "get_project_by_code",
                    return_value=project,
                ),
                patch.object(tc.env_inst, "ui_script_editor", editor),
                patch.object(tc, "get_custom_scripts") as refresh,
            ):
                result = tc.execute_custom_script(
                    str(script), project="test"
                )

        self.assertEqual(result, "executed")
        select.assert_called_once_with("test")
        project.get_stypes.assert_called_once_with()
        refresh.assert_not_called()
        editor.execute_source_code.assert_called_once_with(
            "batch_dispatcher_window = batch_dispatcher.show()\n"
        )


class ServerProcedureTests(unittest.TestCase):
    def test_sobjects_without_code_load_snapshots_by_search_id(self):
        record = Mock()
        record.get_id.return_value = 17
        record.get_search_type.return_value = "sthpw/transaction_state"
        searches = []

        class Search:
            def __init__(self, search_type):
                self.search_type = search_type
                self.filters = []
                searches.append(self)

            def add_op(self, *_args):
                pass

            def add_filter(self, name, value):
                self.filters.append((name, value))

            def add_filters(self, name, values):
                self.filters.append((name, list(values)))

            def add_relationship_filters(self, *_args, **_kwargs):
                raise AssertionError("code-less objects cannot use this relationship")

            def get_sobjects(self):
                return [record] if self.search_type == "sthpw/transaction_state" else []

        search_module = ModuleType("pyasm.search")
        search_module.Search = Search
        search_module.SearchKey = Mock()
        search_module.SearchType = SimpleNamespace()
        biz_module = ModuleType("pyasm.biz")
        biz_module.Snapshot = Mock()
        biz_module.Snapshot.get_files_dict_by_snapshots.return_value = {}
        biz_module.Schema = Mock()
        fake_server = Mock()
        fake_server.server._get_sobjects_dict.return_value = [{"id": 17}]

        for get_all_snapshots in (False, True):
            with (
                self.subTest(get_all_snapshots=get_all_snapshots),
                patch.dict(sys.modules, {
                    "pyasm.search": search_module,
                    "pyasm.biz": biz_module,
                }),
                patch.object(tq, "server", fake_server, create=True),
            ):
                result = json.loads(tq.query_sobjects(
                    "sthpw/transaction_state", project_code="sthpw",
                    include_info=False, include_snapshots=True,
                    get_all_snapshots=get_all_snapshots,
                    compressed_return=False,
                ))
                self.assertEqual(result["sobjects_list"][0]["__snapshots__"], [])
                self.assertEqual(searches[-1].filters, [
                    ("search_type", "sthpw/transaction_state"),
                    ("search_id", [17]),
                ])

    def test_application_python_does_not_use_removed_ast_minifier(self):
        source = "# keep server procedure layout\nvalue = 1\n"

        self.assertEqual(gf.minify_code(source), source)

    def test_tasks_and_notes_script_calls_the_complete_function_name(self):
        code = tq.prepare_serverside_script(
            tq.get_tasks_and_notes,
            {
                "search_code": "ASSET0001",
                "project_code": "test",
                "process": "publish",
                "include_all_tasks": True,
            },
            shrink=False,
            catch_traceback=False,
        )["code"]

        self.assertIn("\nreturn get_tasks_and_notes(", code)
        self.assertNotIn("\nreturn get_tasks_and_note(", code)
        self.assertIn("include_all_tasks=True", code)
        self.assertIn("notes_count_by_process", code)
        self.assertIn("task['__notes_count__']", code)

    def test_task_workspace_counts_contextual_notes_by_task_parent(self):
        class Record:
            def __init__(self, **values):
                self.values = dict(values)

            def get_data(self):
                return dict(self.values)

            def get_value(self, name):
                return self.values.get(name)

        tasks = [
            Record(
                code="TASK001", search_type="demo/asset",
                search_code="ASSET001", process="model", context="model",
                project_code="demo", timestamp="2026-08-01 10:00:00",
            ),
            Record(
                code="TASK002", search_type="demo/asset",
                search_code="ASSET001", process="model", context="review",
                project_code="demo", timestamp="2026-08-01 11:00:00",
            ),
        ]
        root_notes = [
            Record(
                code="NOTE_ROOT_{}".format(index),
                search_type="demo/asset", search_code="ASSET001",
                process="model",
            )
            for index in range(4)
        ]
        task_notes = [Record(
            code="NOTE_TASK", search_type="sthpw/task?project=demo",
            search_code="TASK002", process="model",
        )]

        class Search:
            def __init__(self, search_type):
                self.search_type = search_type
                self.filters = []

            def add_op_filters(self, filters):
                self.filters.extend(filters or [])

            def add_filter(self, name, value):
                self.filters.append((name, value))

            def add_filters(self, name, values):
                self.filters.append((name, list(values)))

            def add_order_by(self, _value):
                pass

            def set_limit(self, _value):
                pass

            def set_offset(self, _value):
                pass

            def get_count(self):
                return len(tasks)

            def get_sobjects(self):
                if self.search_type == "sthpw/task":
                    return list(tasks)
                if self.search_type == "sthpw/note":
                    search_codes = next((
                        values for name, values in self.filters
                        if name == "search_code"
                    ), [])
                    if "ASSET001" in search_codes:
                        return list(root_notes)
                    if "TASK002" in search_codes:
                        return list(task_notes)
                return []

        search_module = ModuleType("pyasm.search")
        search_module.Search = Search
        pyasm_module = ModuleType("pyasm")
        pyasm_module.search = search_module
        fake_server = type("Server", (), {
            "set_project": staticmethod(lambda _project: None),
            "server": type("Stub", (), {
                "_get_sobjects_dict": staticmethod(
                    lambda records: [record.get_data() for record in records]
                ),
            })(),
        })()

        with patch.dict(sys.modules, {
            "pyasm": pyasm_module,
            "pyasm.search": search_module,
        }), patch.object(tq, "server", fake_server, create=True):
            payload = json.loads(tq.query_task_workspace_page(
                [], [], "demo", limit=500, offset=0,
            ))

        by_code = {item["code"]: item for item in payload["tasks"]}
        self.assertTrue(by_code["TASK001"]["__primary_note_branch__"])
        self.assertEqual(by_code["TASK001"]["__notes_count__"], 4)
        self.assertFalse(by_code["TASK002"]["__primary_note_branch__"])
        self.assertEqual(by_code["TASK002"]["__notes_count__"], 1)

    def test_task_note_with_qualified_parent_type_reloads_after_send(self):
        class Record:
            def __init__(self, **values):
                self.values = dict(values)

            def get_data(self):
                return dict(self.values)

            def get_value(self, name):
                return self.values.get(name)

            def get_connections(self, context=None):
                return []

        tasks = [
            Record(
                code="TASK001", search_code="ASSET001", process="model",
                context="model", project_code="demo",
                timestamp="2026-08-01 10:00:00",
            ),
            Record(
                code="TASK002", search_code="ASSET001", process="model",
                context="review", project_code="demo",
                timestamp="2026-08-01 11:00:00",
            ),
        ]
        root_notes = [
            Record(
                code="NOTE_ROOT_{}".format(index),
                search_type="demo/asset", search_code="ASSET001",
                process="model",
            )
            for index in range(4)
        ]
        task_note = Record(
            code="NOTE_TASK", search_type="sthpw/task?project=demo",
            search_code="TASK002", process="model",
        )

        class Search:
            def __init__(self, search_type):
                self.search_type = search_type
                self.filters = []

            def add_filter(self, name, value):
                self.filters.append((name, value))

            def add_filters(self, name, values):
                self.filters.append((name, list(values)))

            def add_order_by(self, *_args, **_kwargs):
                pass

            def get_sobject(self):
                return tasks[0]

            def get_sobjects(self):
                if self.search_type == "sthpw/task":
                    return list(tasks)
                if self.search_type == "sthpw/status_log":
                    return []
                if self.search_type == "sthpw/note":
                    search_code = next((
                        value for name, value in self.filters
                        if name == "search_code"
                    ), None)
                    if search_code == "ASSET001":
                        return list(root_notes)
                    if isinstance(search_code, list):
                        return [task_note]
                return []

        search_module = ModuleType("pyasm.search")
        search_module.Search = Search
        search_module.SearchKey = type("SearchKey", (), {
            "get_by_sobjects": staticmethod(lambda records, use_id=False: [
                "{}?code={}".format(
                    record.get_value("search_type") or "sthpw/task",
                    record.get_value("code"),
                )
                for record in records
            ]),
            "get_by_sobject": staticmethod(
                lambda record, use_id=False: "sthpw/note?code="
                + str(record.get_value("code") or "")
            ),
        })
        biz_module = ModuleType("pyasm.biz")
        biz_module.Snapshot = type("Snapshot", (), {
            "get_by_sobjects": staticmethod(lambda _records: []),
            "get_files_dict_by_snapshots": staticmethod(lambda _records: {}),
        })
        pyasm_module = ModuleType("pyasm")
        pyasm_module.search = search_module
        pyasm_module.biz = biz_module
        fake_server = type("Server", (), {
            "set_project": staticmethod(lambda _project: None),
            "server": type("Stub", (), {
                "_get_sobject_dict": staticmethod(
                    lambda record: record.get_data()
                ),
            })(),
        })()

        with patch.dict(sys.modules, {
            "pyasm": pyasm_module,
            "pyasm.search": search_module,
            "pyasm.biz": biz_module,
        }), patch.object(tq, "server", fake_server, create=True):
            payload = json.loads(tq.get_tasks_and_notes(
                "ASSET001", "demo", process="model",
            ))

        self.assertIn("NOTE_TASK", {
            item["code"] for item in payload["notes"]
        })
        by_code = {item["code"]: item for item in payload["tasks"]}
        self.assertEqual(by_code["TASK001"]["__notes_count__"], 4)
        self.assertEqual(by_code["TASK002"]["__notes_count__"], 1)

    def test_combined_tasks_and_notes_populates_native_task_counts(self):
        payload = {
            "tasks": [
                {
                    "__search_key__": (
                        "skey://sthpw/task?project=test&code=TASK0001"
                    ),
                    "code": "TASK0001",
                    "process": "model",
                    "search_code": "ASSET0001",
                    "project_code": "test",
                    "__notes_count__": 4,
                }
            ],
            "notes": [],
        }
        parent = Mock()
        parent.get_code.return_value = "ASSET0001"
        parent.get_project.return_value.get_code.return_value = "test"
        with patch.object(
                tc, "execute_procedure_serverside", return_value=payload
        ), patch.object(tc.env_inst, "projects", {"test": object()}):
            tasks, notes = tc.get_tasks_and_notes(
                sobject=parent,
                process="publish",
                include_all_tasks=True,
            )

        self.assertEqual(notes, {})
        self.assertEqual(tasks["TASK0001"].get_notes_count("model"), 4)
        parent.set_notes_count.assert_called_once_with("model", 4)

    def test_batched_progress_query_compiles_for_server(self):
        code = tq.prepare_serverside_script(
            tq.query_sobjects,
            {
                "search_type": "demo/asset",
                "project_code": "demo",
                "include_progress": True,
            },
            shrink=False,
            catch_traceback=False,
        )["code"]

        compile(
            "def execute():\n" + textwrap.indent(code, "    "),
            "<query-sobjects-progress>", "exec",
        )

    def test_progress_query_reads_sqlite_and_postgres_workflow_json(self):
        episode = Mock()
        episode.get_search_key.return_value = "first_project/episode?code=EP001"
        episode.get_value.return_value = "first_project/episode"
        episode.get_base_search_type.return_value = "first_project/episode"
        episode.get_project_code.return_value = "first_project"
        related = Mock()
        related.get_search_key.return_value = "first_project/shot?code=SHOT001"
        related.get_related_sobjects.return_value = []
        episode.get_related_sobjects.return_value = [related]

        pipeline_process = Mock()
        pipeline_process.get_attribute.return_value = "PROC001"
        pipeline = Mock()
        pipeline.get_value.return_value = "first_project/episode"
        pipeline.get_process_names.return_value = ["progress"]
        pipeline.get_process.return_value = pipeline_process

        search_module = ModuleType("pyasm.search")
        biz_module = ModuleType("pyasm.biz")
        search_module.SearchKey = Mock()
        search_module.SearchType = SimpleNamespace()
        biz_module.Snapshot = Mock()
        biz_module.Schema = Mock()
        fake_server = Mock()
        fake_server.split_search_key.return_value = (
            "first_project/episode", "first_project"
        )
        fake_server.server._get_sobjects_dict.return_value = [{"code": "EP001"}]

        for workflow, related_to_episode in (
            ({"search_type": "first_project/shot"}, True),
            ('{"search_type": "first_project/shot"}', True),
            ({"search_type": "first_project/shot"}, False),
        ):
            with self.subTest(
                workflow_type=type(workflow).__name__,
                related_to_episode=related_to_episode,
            ):
                biz_module.Schema.get.return_value.get_relationship.return_value = (
                    related_to_episode
                )
                episode.get_related_sobjects.reset_mock()
                process = Mock()
                process.get_value.side_effect = lambda name: (
                    "PROC001" if name == "code" else workflow
                )
                process.get_json_value.side_effect = lambda name, default=None: (
                    json.loads(workflow) if isinstance(workflow, str)
                    else workflow
                )

                class Search:
                    def __init__(self, search_type):
                        self.search_type = search_type

                    def __getattr__(self, name):
                        return lambda *_args, **_kwargs: None

                    def get_sobjects(self):
                        return {
                            "first_project/episode": [episode],
                            "sthpw/pipeline": [pipeline],
                            "config/process": [process],
                        }.get(self.search_type, [])

                search_module.Search = Search
                with patch.dict(sys.modules, {
                    "pyasm.search": search_module,
                    "pyasm.biz": biz_module,
                }), patch.object(tq, "server", fake_server, create=True):
                    result = json.loads(tq.query_sobjects(
                        "first_project/episode",
                        project_code="first_project",
                        limit=1,
                        include_info=False,
                        include_snapshots=False,
                        include_progress=True,
                        compressed_return=False,
                    ))

                self.assertEqual(
                    result["sobjects_list"][0]["__progress__"],
                    {"progress": {"tc": 1, "ac": 0}}
                    if related_to_episode else {},
                )
                if not related_to_episode:
                    episode.get_related_sobjects.assert_not_called()
                process.get_json_value.assert_called_with("workflow", {})

    def test_sobject_payload_retains_counts_for_every_process(self):
        payload = {
            "sobjects_list": [{
                "__search_key__": (
                    "skey://demo/asset?project=demo&code=ASSET001"
                ),
                "__search_type__": "demo/asset",
                "code": "ASSET001",
                "name": "Asset 1",
                "__notes_count__": 5,
                "__tasks_count__": 6,
                "__notes_count_by_process__": {
                    "publish": 1,
                    "model": 4,
                },
                "__tasks_count_by_process__": {
                    "publish": 2,
                    "rig": 4,
                },
                "__task_details_by_process__": {
                    "publish": [{
                        "code": "TASK001", "process": "publish",
                        "assigned": "artist", "status": "Ready",
                        "__primary_note_branch__": True,
                        "__notes_count__": 1,
                    }],
                },
            }],
            "total_sobjects_count": 1,
            "total_sobjects_query_count": 1,
            "limit": 25,
            "offset": 0,
        }
        with patch.object(tc.env_inst, "projects", {"demo": Mock()}):
            sobjects, _info = tc.hydrate_sobjects_payload(
                payload,
                "demo",
                include_snapshots=False,
            )

        sobject = next(iter(sobjects.values()))
        self.assertEqual(
            sobject.get_notes_count(),
            {"publish": 1, "model": 4},
        )
        self.assertEqual(sobject.get_tasks_count("publish"), 2)
        self.assertEqual(sobject.get_tasks_count("rig"), 4)
        self.assertEqual(sobject.get_tasks_count("__total__"), 6)
        self.assertEqual(
            sobject.get_task_summaries("publish")[0]["assigned"],
            "artist",
        )

    def test_sobject_query_exports_process_count_maps(self):
        code = tq.prepare_serverside_script(
            tq.query_sobjects,
            {
                "search_type": "demo/asset",
                "project_code": "demo",
                "include_info": True,
            },
            shrink=False,
            catch_traceback=False,
        )["code"]

        self.assertIn("__notes_count_by_process__", code)
        self.assertIn("__tasks_count_by_process__", code)
        self.assertIn("__task_details_by_process__", code)
        self.assertIn("('sthpw/note', notes_count_by_key", code)
        self.assertIn("('sthpw/task', tasks_count_by_key", code)
        compile(
            "def execute():\n" + textwrap.indent(code, "    "),
            "<query-sobjects-process-counts>",
            "exec",
        )

    def test_server_script_source_survives_stale_runtime_line_numbers(self):
        with patch.object(
                tq.inspect, "getsourcelines",
                return_value=(["conversation_metadata = {}\n",
                               "conversation_metadata =\n"], 1)):
            code = tq.prepare_serverside_script(
                tq.query_server_updates,
                {
                    "message_after": "",
                    "activity_after": "",
                    "project_code": "test",
                },
                shrink=False,
                catch_traceback=False,
            )["code"]

        self.assertIn("def query_server_updates(", code)
        self.assertIn("return query_server_updates(", code)
        compile(
            "def execute():\n" + textwrap.indent(code, "    "),
            "<server-updates>", "exec",
        )

    def test_user_profile_mutation_compiles_for_server(self):
        code = tq.prepare_serverside_script(
            tq.mutate_user_profile,
            {
                "login": "artist",
                "values": {"display_name": "Artist Name"},
                "password": "",
                "groups": ["artists"],
            },
            shrink=False,
            catch_traceback=False,
        )["code"]

        compile(
            "def execute():\n" + textwrap.indent(code, "    "),
            "<user-profile>",
            "exec",
        )

    def test_presence_heartbeat_compiles_for_server(self):
        code = tq.prepare_serverside_script(
            tq.heartbeat_user_presence,
            {"ttl_seconds": 90},
            shrink=False,
            catch_traceback=False,
        )["code"]

        self.assertIn("category = 'online_status'", code)
        self.assertNotIn("client_type", code)
        compile(
            "def execute():\n" + textwrap.indent(code, "    "),
            "<presence-heartbeat>",
            "exec",
        )

    def test_batched_queries_compile_for_server(self):
        procedures = (
            (
                tq.query_server_updates,
                {
                    "message_after": "", "activity_after": "",
                    "project_code": "test", "include_presence": True,
                    "presence_ttl": 360,
                },
            ),
            (
                tq.query_task_workspace_page,
                {
                    "filters": [("project_code", "test")],
                    "order_bys": ["timestamp desc"],
                    "project_code": "test", "limit": 100, "offset": 0,
                },
            ),
            (
                tq.query_user_profile_data,
                {
                    "login": "artist", "project_code": "test",
                    "activity_limit": 12,
                },
            ),
            (
                tq.get_notes_with_attachments,
                {"note_codes": ["NOTE0001"], "project_code": "test"},
            ),
            (
                tq.query_table_layout,
                {
                    "search_type": "demo/asset",
                    "search_keys": ["demo/asset?code=ASSET001"],
                    "view": "table", "project_code": "demo",
                },
            ),
        )
        for function, kwargs in procedures:
            with self.subTest(function=function.__name__):
                code = tq.prepare_serverside_script(
                    function, kwargs, shrink=False, catch_traceback=False,
                )["code"]
                compile(
                    "def execute():\n" + textwrap.indent(code, "    "),
                    "<{0}>".format(function.__name__), "exec",
                )

    def test_user_profile_wrapper_uses_sthpw_security_procedure(self):
        with patch.object(
                tc, "execute_procedure_serverside", return_value={}) as execute:
            tc.mutate_user_profile(
                "artist", values={"department": "Animation"},
                groups=["artists"],
            )

        self.assertIs(execute.call_args.args[0], tq.mutate_user_profile)
        self.assertEqual(execute.call_args.kwargs["project"], "sthpw")
        self.assertEqual(
            execute.call_args.args[1]["values"],
            {"department": "Animation"},
        )


class ChatHistoryTests(unittest.TestCase):
    def test_sqlite_chat_send_and_forward_commit_missing_message_logs(self):
        server = Mock()
        server.get_login.return_value = "artist"
        server.split_search_key.return_value = ("sthpw/message_log", "LOGSRC")

        def log_record(code, message_code):
            values = {
                "code": code, "message_code": message_code,
                "message": "Hello", "status": "sent",
                "timestamp": "2026-09-24 12:00:00", "metadata": {},
            }
            record = Mock()
            record.get_code.side_effect = lambda: values["code"]
            record.get_id.return_value = 1
            record.get_value.side_effect = lambda key, **_kwargs: values.get(key)
            record.set_value.side_effect = lambda key, value: values.__setitem__(key, value)
            record.get_data.side_effect = lambda: dict(values)
            return record

        source = log_record("LOGSRC", "CHAT001")
        old_target = log_record("LOGOLD", "CHAT002")
        created = [log_record("LOGSEND", "CHAT001"),
                   log_record("LOGFORWARD", "CHAT002")]
        members = [
            SimpleNamespace(get_value=lambda key, code=code: {
                "login": "artist", "message_code": code,
            }.get(key))
            for code in ("CHAT001", "CHAT002")
        ]
        destination = Mock()
        destination.get_code.return_value = "CHAT002"
        destination.get_value.return_value = {}

        class FakeSearch:
            get_by_search_key = staticmethod(lambda _key: source)

            def __init__(self, search_type):
                self.search_type = search_type
                self.codes = None

            def add_filter(self, field, value, **_kwargs):
                if field == "message_code":
                    self.codes = {value}

            def add_filters(self, field, values, **_kwargs):
                if field == "message_code":
                    self.codes = set(values)

            def add_order_by(self, *_args, **_kwargs):
                pass

            def set_limit(self, _limit):
                pass

            def get_database_impl(self):
                return SimpleNamespace(get_database_type=lambda: "Sqlite")

            def get_sobjects(self):
                if self.search_type == "sthpw/subscription":
                    return [item for item in members
                            if self.codes is None or item.get_value("message_code") in self.codes]
                if self.search_type == "sthpw/message":
                    return [destination]
                if self.search_type == "sthpw/message_log":
                    return [old_target]
                return []

            def get_sobject(self):
                return source if self.search_type == "sthpw/message_log" else None

        search_module = ModuleType("pyasm.search")
        search_module.Search = FakeSearch
        search_module.SearchType = SimpleNamespace(create=Mock(side_effect=created))
        search_module.SearchKey = SimpleNamespace(
            get_by_sobject=lambda item, use_id=False:
                "sthpw/message_log?code=" + item.get_code()
        )
        pyasm_module = ModuleType("pyasm")
        pyasm_module.__path__ = []
        with (
            patch.dict(sys.modules, {
                "pyasm": pyasm_module, "pyasm.search": search_module,
            }),
            patch.object(tq, "server", server, create=True),
        ):
            sent = json.loads(tq.send_chat_message("CHAT001", "Hello"))
            forwarded = json.loads(tq.forward_chat_messages(
                ["sthpw/message_log?code=LOGSRC"], ["CHAT002"]
            ))

        self.assertEqual(sent["message"]["code"], "LOGSEND")
        self.assertEqual(forwarded["forwarded"], 1)
        self.assertEqual(search_module.SearchType.create.call_count, 2)
        self.assertEqual(
            [entry.kwargs["log_history"] for entry in server.log_message.call_args_list],
            [False, False],
        )
        self.assertEqual([item.commit.call_args.kwargs for item in created],
                         [{"triggers": False}, {"triggers": False}])

    def test_chat_history_keeps_older_logs_without_codes(self):
        class OldLog:
            code = None

            def get_code(self):
                return self.code

            def get_id(self):
                return 19

            def get_value(self, key, **_kwargs):
                return {
                    "message": "вкап", "login": "admin", "metadata": {},
                    "message_code": "CHAT001", "timestamp": "2026-09-22 12:00:00",
                }.get(key)

            def get_data(self):
                return {"message": "вкап", "login": "admin", "code": self.code}

            def set_value(self, key, value):
                setattr(self, key, value)

        old_log = OldLog()

        class FakeSearch:
            def __init__(self, search_type):
                self.search_type = search_type

            def add_filter(self, *_args, **_kwargs):
                pass

            def add_filters(self, *_args, **_kwargs):
                pass

            def add_order_by(self, *_args, **_kwargs):
                pass

            def set_limit(self, _limit):
                pass

            def get_sobjects(self):
                if self.search_type == "sthpw/message_log":
                    return [old_log]
                return []

            def get_sobject(self):
                return object() if self.search_type == "sthpw/subscription" else None

        search_module = ModuleType("pyasm.search")
        search_module.Search = FakeSearch
        search_module.SearchKey = SimpleNamespace(
            get_by_sobject=lambda item, use_id=False:
            "sthpw/message_log?id=19" if use_id else
            f"sthpw/message_log?code={item.get_code()}"
        )
        biz_module = ModuleType("pyasm.biz")
        biz_module.Snapshot = SimpleNamespace(
            get_files_dict_by_snapshots=lambda _snapshots: {}
        )
        pyasm_module = ModuleType("pyasm")
        pyasm_module.__path__ = []
        server = Mock()
        server.get_login.return_value = "artist"
        with (
            patch.dict(sys.modules, {
                "pyasm": pyasm_module, "pyasm.search": search_module,
                "pyasm.biz": biz_module,
            }),
            patch.object(tq, "server", server, create=True),
        ):
            history = json.loads(tq.query_chat_history("CHAT001"))

        self.assertEqual(history["messages"][0]["message"], "вкап")
        self.assertEqual(old_log.get_code(), "MESSAGE_LOG00019")

    def test_chat_history_attachment_can_be_opened_as_snapshot(self):
        class Row:
            def __init__(self, search_type, code, record_id=0, **values):
                self.search_type = search_type
                self.code = code
                self.record_id = record_id
                self.values = values

            def get_code(self):
                return self.code

            def get_id(self):
                return self.record_id

            def get_value(self, key, **_kwargs):
                return self.values.get(key)

            def get_data(self):
                return {"code": self.code, **self.values}

        member = Row("sthpw/subscription", "MEMBER", login="artist")
        log = Row(
            "sthpw/message_log", "LOG001", record_id=3, login="artist",
            message_code="CHAT001", message="", metadata={},
        )
        connection = Row(
            "sthpw/connection", "CON001", src_search_type="sthpw/snapshot",
            src_search_id=37, dst_search_id=3,
        )
        snapshot = Row("sthpw/snapshot", "SNAP001", record_id=37)
        file_row = Row(
            "sthpw/file", "FILE001", type="main", base_type="file",
            file_name="image.png", st_size=4, relative_dir="attachment/chat",
        )
        rows = {
            "sthpw/subscription": [member],
            "sthpw/message_log": [log],
            "sthpw/connection": [connection],
            "sthpw/snapshot": [snapshot],
        }

        class FakeSearch:
            def __init__(self, search_type):
                self.search_type = search_type

            def add_filter(self, *_args, **_kwargs):
                pass

            def add_filters(self, *_args, **_kwargs):
                pass

            def add_order_by(self, *_args, **_kwargs):
                pass

            def set_limit(self, _limit):
                pass

            def get_sobjects(self):
                return rows.get(self.search_type, [])

            def get_sobject(self):
                return next(iter(self.get_sobjects()), None)

        search_module = ModuleType("pyasm.search")
        search_module.Search = FakeSearch
        search_module.SearchKey = SimpleNamespace(
            get_by_sobject=lambda item, use_id=False:
            f"{item.search_type}?code={item.code}"
        )
        biz_module = ModuleType("pyasm.biz")
        biz_module.Snapshot = SimpleNamespace(
            get_files_dict_by_snapshots=lambda _snapshots: {"SNAP001": [file_row]}
        )
        pyasm_module = ModuleType("pyasm")
        pyasm_module.__path__ = []
        server = Mock()
        server.get_login.return_value = "artist"
        with (
            patch.dict(sys.modules, {
                "pyasm": pyasm_module, "pyasm.search": search_module,
                "pyasm.biz": biz_module,
            }),
            patch.object(tq, "server", server, create=True),
        ):
            history = json.loads(tq.query_chat_history("CHAT001"))
            authorization = json.loads(tq.authorize_chat_attachment(
                "CHAT001", "SNAP001"
            ))

        attachment = history["messages"][0]["__attachments__"][0]
        self.assertTrue(authorization["allowed"])
        wrapped = tc.Snapshot(attachment)
        self.assertEqual(wrapped.get_code(), "SNAP001")
        self.assertEqual(
            wrapped.get_files_objects()[0].get_filename_with_ext(), "image.png"
        )

    def test_chat_attachment_is_validated_and_connected_to_newest_log(self):
        snapshot_present = {"value": False}
        server = Mock()
        server.get_login.return_value = "artist"
        server.split_search_key.return_value = ("sthpw/snapshot", "SNAP001")
        member = SimpleNamespace(get_value=lambda key: "artist")
        snapshot = SimpleNamespace(get_value=lambda key: {
            "search_type": "sthpw/message", "search_code": "CHAT001",
        }.get(key))

        def log_record(code, record_id):
            return SimpleNamespace(
                get_code=lambda: code,
                get_id=lambda: record_id,
                get_value=lambda key: "2026-09-22 12:00:00",
                get_data=lambda: {"code": code},
            )

        old_log = log_record("LOG001", 1)
        new_log = log_record("LOG002", 2)

        class FakeSearch:
            def __init__(self, search_type):
                self.search_type = search_type
                self.order = ""

            def add_filter(self, *_args):
                pass

            def add_order_by(self, field, direction="asc"):
                self.order = field

            def set_limit(self, _limit):
                pass

            def get_database_impl(self):
                return SimpleNamespace(get_database_type=lambda: "Postgres")

            def get_sobjects(self):
                return [member] if self.search_type == "sthpw/subscription" else []

            def get_sobject(self):
                if self.search_type == "sthpw/snapshot":
                    return snapshot if snapshot_present["value"] else None
                if self.search_type == "sthpw/message_log":
                    return new_log if self.order == "id" else old_log
                return None

        search_module = ModuleType("pyasm.search")
        search_module.Search = FakeSearch
        search_module.SearchKey = SimpleNamespace(
            get_by_sobject=lambda item, use_id=False:
                "sthpw/message_log?code=" + item.get_code()
        )
        pyasm_module = ModuleType("pyasm")
        pyasm_module.__path__ = []
        with (
            patch.dict(sys.modules, {
                "pyasm": pyasm_module, "pyasm.search": search_module,
            }),
            patch.object(tq, "server", server, create=True),
        ):
            with self.assertRaisesRegex(ValueError, "attachment.*not found"):
                tq.send_chat_message(
                    "CHAT001", "Picture", ["sthpw/snapshot?code=SNAP001"]
                )
            server.log_message.assert_not_called()

            snapshot_present["value"] = True
            server.connect_sobjects.return_value = None
            with self.assertRaisesRegex(RuntimeError, "attach.*message"):
                tq.send_chat_message(
                    "CHAT001", "Picture", ["sthpw/snapshot?code=SNAP001"]
                )
            self.assertTrue(any(
                call.args[1] == {"status": "deleted"}
                for call in server.update.call_args_list
            ))
            server.connect_sobjects.reset_mock()
            server.connect_sobjects.return_value = {"code": "CON001"}
            result = json.loads(tq.send_chat_message(
                "CHAT001", "Picture", ["sthpw/snapshot?code=SNAP001"]
            ))

        self.assertEqual(result["message"]["code"], "LOG002")
        self.assertTrue(server.log_message.call_args.kwargs["log_history"])
        server.connect_sobjects.assert_called_once_with(
            "sthpw/snapshot?code=SNAP001",
            "sthpw/message_log?code=LOG002",
            context="chat_attachment",
        )

    def test_send_chat_message_preserves_reply_target(self):
        with patch.object(
                tc, "execute_procedure_serverside", return_value={}) as execute:
            tc.send_chat_message(
                "CHAT001", "Reply", reply_to="sthpw/message_log?code=LOG001"
            )

        self.assertEqual(
            execute.call_args.args[1]["reply_to"],
            "sthpw/message_log?code=LOG001",
        )

    def test_forward_chat_messages_preserves_sources_and_targets(self):
        with patch.object(
                tc, "execute_procedure_serverside", return_value={}) as execute:
            tc.forward_chat_messages(
                ["sthpw/message_log?code=LOG001"], ["CHAT002", "CHAT003"]
            )

        self.assertIs(execute.call_args.args[0], tq.forward_chat_messages)
        self.assertEqual(execute.call_args.args[1], {
            "message_log_keys": ["sthpw/message_log?code=LOG001"],
            "target_message_codes": ["CHAT002", "CHAT003"],
        })

    def test_conversation_query_with_mentions_compiles_for_server(self):
        code = tq.prepare_serverside_script(
            tq.query_chat_conversations,
            {},
            shrink=False,
            catch_traceback=False,
        )["code"]

        compile(
            "def execute():\n" + textwrap.indent(code, "    "),
            "<chat-conversations>",
            "exec",
        )

    def test_forward_messages_compiles_for_server(self):
        code = tq.prepare_serverside_script(
            tq.forward_chat_messages,
            {
                "message_log_keys": ["sthpw/message_log?code=LOG001"],
                "target_message_codes": ["CHAT002"],
            },
            shrink=False,
            catch_traceback=False,
        )["code"]

        compile(
            "def execute():\n" + textwrap.indent(code, "    "),
            "<forward-chat-messages>",
            "exec",
        )
        self.assertIn("for item in log_search.get_sobjects():", code)
        self.assertNotIn("message_log = next((", code)

    def test_unpin_uses_existing_pin_metadata_operation(self):
        with patch.object(
                tc, "execute_procedure_serverside", return_value={}) as execute:
            tc.unpin_chat_message("LOG001")

        self.assertIs(execute.call_args.args[0], tq.pin_chat_message)
        self.assertEqual(execute.call_args.args[1], {
            "message_log_code": "LOG001",
            "unpin": True,
        })

    def test_server_script_escapes_string_arguments(self):
        code = tq.prepare_serverside_script(
            tq.send_chat_message,
            {
                "message_code": "CHAT'001",
                "message": "It's ready\nC:\\scene\\shot.ma",
                "attachment_keys": [],
            },
            shrink=False,
            catch_traceback=False,
        )["code"]

        compile("def execute():\n" + textwrap.indent(code, "    "), "<chat>", "exec")

    def test_new_message_logs_receive_codes_before_skey_generation(self):
        code = tq.prepare_serverside_script(
            tq.send_chat_message,
            {
                "message_code": "CHAT001",
                "message": "Hello",
                "attachment_keys": [],
            },
            shrink=False,
            catch_traceback=False,
        )["code"]

        self.assertIn("MESSAGE_LOG{0:05d}", code)
        self.assertLess(
            code.index("update_message_log(message_log, metadata_values)"),
            code.index(
                "message_log_key = SearchKey.get_by_sobject("
                "message_log, use_id=False)"
            ),
        )
        self.assertIn("update_message_log(reply_target)", code)
        self.assertNotIn("The replied message has no code", code)

    def test_chat_metadata_uses_native_columns(self):
        functions = (
            tq.query_chat_conversations,
            tq.create_chat_conversation,
            tq.update_chat_conversation,
            tq.edit_chat_message,
            tq.pin_chat_message,
            tq.query_chat_history,
            tq.send_chat_message,
            tq.forward_chat_messages,
        )
        source = "\n".join(
            tq.prepare_serverside_script(
                function, {}, shrink=False, catch_traceback=False,
            )["code"]
            for function in functions
        )

        self.assertNotIn("CHAT_META_", source)
        self.assertNotIn("CHAT_LOG_META_", source)
        self.assertNotIn("chat_message_metadata", source)
        self.assertIn("get_value('metadata')", source)
        self.assertNotIn("'metadata': json.dumps", source)
        self.assertNotIn("values['metadata'] = json.dumps", source)

    def test_search_text_uses_existing_chat_history_contract(self):
        with patch.object(
                tc, "execute_procedure_serverside", return_value={}) as execute:
            tc.get_chat_history(
                "CHAT001", limit=31, offset=10, search_text="render ready"
            )

        self.assertEqual(execute.call_args.args[1], {
            "message_code": "CHAT001",
            "limit": 31,
            "offset": 10,
            "search_text": "render ready",
        })

    def test_history_assigns_codes_before_generating_display_search_keys(self):
        code = tq.prepare_serverside_script(
            tq.query_chat_history,
            {
                "message_code": "CHAT001",
                "limit": 31,
                "offset": 0,
                "search_text": "",
            },
            shrink=False,
            catch_traceback=False,
        )["code"]

        self.assertLess(
            code.index("message_log.set_value('code', code)"),
            code.index("data['__search_key__'] = SearchKey.get_by_sobject("),
        )
        self.assertNotIn("info.get(\"id\")", code)

    def test_chat_delivery_receipts_compile_and_replace_in_progress_status(self):
        functions = (
            tq.create_chat_conversation,
            tq.send_chat_message,
            tq.forward_chat_messages,
            tq.query_chat_history,
            tq.mark_chat_read,
            tq.query_server_updates,
        )
        source = "\n".join(
            tq.prepare_serverside_script(
                function, {}, shrink=False, catch_traceback=False,
            )["code"]
            for function in functions
        )

        for function in functions:
            code = tq.prepare_serverside_script(
                function, {}, shrink=False, catch_traceback=False,
            )["code"]
            compile(
                "def execute():\n" + textwrap.indent(code, "    "),
                "<chat-delivery>",
                "exec",
            )

        self.assertNotIn("in_progress", source)
        self.assertIn("status='sent'", source)
        self.assertIn("'deliveredAt': ''", source)
        self.assertIn("'readAt': ''", source)
        self.assertIn("'project_code': 'sthpw'", source)
        self.assertIn("server.update_multiple(data=receipt_updates, triggers=True)", source)


if __name__ == "__main__":
    unittest.main()

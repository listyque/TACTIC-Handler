from __future__ import annotations

import json
import sys
import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from unittest.mock import Mock, patch

from thlib import tactic_classes as tc
from thlib import tactic_query as tq
from thlib import global_functions as gf
from thlib import environment


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
            (
                tq.save_widget_config,
                {
                    "search_type": "demo/asset", "view": "definition",
                    "element_xml": '<element name="name"/>',
                    "project_code": "demo",
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

    def test_history_requires_codes_before_generating_search_keys(self):
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

        self.assertNotIn("use_id=True", code)
        self.assertLess(
            code.index("history = [item for item in history if item.get_code()]"),
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

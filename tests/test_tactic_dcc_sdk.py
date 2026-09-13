"""Unified domain API through real ThinClient/HandlerServer transport."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import importlib.util
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from handler_server.client import ThinClient
from handler_server.registry import CommandRegistry
from handler_server.server import HandlerServer
from tactic_handler_api import HandlerAPI, from_client, DirtyObject, Operation
from tactic_handler_api import remote, wire
from tactic_handler_api.contract import METHODS, PROPERTIES
from thlib.ui.tactic_rpc import HandlerApiService


class TacticDccSdkTests(unittest.TestCase):
    def setUp(self):
        from thlib import tactic_classes as tc, global_functions as gf

        self.server = HandlerServer(token="sdk-test-token")
        port = self.server.start()
        registry = CommandRegistry()
        self.service = HandlerApiService(
            gui_dispatch=lambda callback, *args: callback(*args)
        )
        self.ui_calls = []
        application = SimpleNamespace(
            select_project=lambda code: self.ui_calls.append(("project", code)),
            open_search_key=lambda key: self.ui_calls.append(("sobject", key)),
            dock_model=SimpleNamespace(
                show_panel=lambda key: self.ui_calls.append(("dock", key))
            ),
            window_model=SimpleNamespace(
                show_window=lambda key: self.ui_calls.append(("window", key))
            ),
        )
        self.service.attach_application(application, None)
        self.service.register(registry)
        self.registry = registry
        self.operator = ThinClient(
            "127.0.0.1",
            port,
            "sdk-test-token",
            "tactic_handler",
            registry=registry,
            client_id="sdk-operator",
        )
        self.dcc = ThinClient(
            "127.0.0.1", port, "sdk-test-token", "maya", client_id="sdk-maya"
        )
        self.operator.start()
        self.dcc.start()
        self.assertTrue(self.operator.wait_connected(3))
        self.assertTrue(self.dcc.wait_connected(3))
        self.project = tc.Project({"code": "demo"})
        stype = tc.SType(
            {"code": "types/object", "column_info": {"code": {}}}, project=self.project
        )
        self.project.stypes = {"types/object": stype}
        self.data = {
            "__search_key__": "types/object?project=demo&code=O1",
            "code": "O1",
            "description": "before",
        }
        self.tactic = Mock()

        def update(key, data, **options):
            self.data.update(data)
            return deepcopy(self.data)

        self.tactic.update.side_effect = update
        self.core = SimpleNamespace(
            get_sobjects=Mock(
                side_effect=lambda *args, **kwargs: (
                    {"O1": tc.SObject(deepcopy(self.data), self.project)},
                    {"total_sobjects_query_count": 1},
                )
            ),
            SObject=tc.SObject,
            Snapshot=tc.Snapshot,
            server_start=lambda **kwargs: self.tactic,
            edit_multiple_instance_sobjects=Mock(),
        )
        self.runtime = HandlerAPI(
            self.core,
            SimpleNamespace(projects={"demo": self.project}),
            files=gf,
            ui=self.service._ui_api,
            repositories=lambda: [],
        )
        self.service._api_runtime = self.runtime
        patcher = patch.object(tc, "server_start", return_value=self.tactic)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.api = from_client(self.dcc, timeout=3)
        self.worker = ThreadPoolExecutor(1)

    def tearDown(self):
        self.worker.submit(self.api.close).result(5)
        self.worker.shutdown()
        self.service.close_api()
        self.dcc.stop()
        self.operator.stop()
        self.server.stop()

    def run_api(self, callback):
        return self.worker.submit(callback).result(5)

    def test_project_query_and_staged_commit_without_legacy_bridge(self):
        def query():
            result = self.api.project("demo").stype("types/object").query(limit=1)
            self.assertEqual(result._type_name, "SearchResult")
            self.assertEqual(result.total, 1)
            self.assertFalse(result.has_more)
            calls = self.core.get_sobjects.call_count
            empty = result.next()
            self.assertEqual(empty._type_name, "SearchResult")
            self.assertEqual(empty.items, ())
            self.assertEqual(self.core.get_sobjects.call_count, calls)
            return result.items[0]

        obj = self.run_api(query)
        self.assertEqual(type(obj).__name__, "SObject")
        obj.set_value("description", "after")
        self.assertEqual(obj.get_value("description"), "after")
        self.tactic.update.assert_not_called()
        self.assertIs(self.run_api(obj.commit), obj)
        self.assertEqual(self.data["description"], "after")
        self.tactic.update.assert_called_once()
        self.assertEqual(obj.changes(), {})
        self.assertIs(self.api._client, self.dcc)

    def test_nonblocking_close_drains_work_then_releases_remote_handles(self):
        entered, release = threading.Event(), threading.Event()

        def work():
            entered.set()
            if not release.wait(3):
                raise TimeoutError("test gate")
            return self.api.project("demo").get_code()

        operation = self.api.submit(work)
        try:
            self.assertTrue(entered.wait(3))
            self.api.close(wait=False)
            release.set()
            self.assertEqual(self.run_api(lambda: operation.wait(3)), "demo")
            self.run_api(self.api.close)
            self.assertEqual(self.service._sessions, {})
        finally:
            release.set()

    def test_nested_metadata_and_dependency_objects_cross_transport(self):
        from thlib import tactic_classes as tc

        process = {"code": "PROC1", "process": "review", "pipeline_code": "main"}
        self.project.get_all_search_types(
            [{"code": "types/object", "column_info": {"code": {}}}],
            [
                {
                    "code": "main", "search_type": "types/object",
                    "pipeline": '<pipeline><process name="review" type="manual" '
                                'label="Review" task_pipeline="approval"/></pipeline>',
                    "stypes_processes": [process],
                },
                {
                    "code": "approval", "search_type": "sthpw/task",
                    "parent_process": "PROC1",
                    "pipeline": '<pipeline><process name="Ready" type="manual"/></pipeline>',
                    "stypes_processes": [],
                },
            ],
            '<schema><search_type name="types/object"/>'
            '<connect from="types/child" to="types/object" relationship="code"/></schema>',
            [],
        )
        dependency_key = "sthpw/note?project=demo&code=N1"
        raw_dependencies = {"sthpw/note": [[{
            "__search_key__": dependency_key, "code": "N1", "note": "Review me",
        }]]}
        self.core.get_all_dependency = tc.get_all_dependency

        def inspect():
            project = self.api.project("demo")
            workflow = project.workflow()
            main = workflow.get_all_pipelines()["types/object"]["main"]
            self.assertEqual(main.get_pipeline_process("review"), process)
            self.assertEqual(main.get_all_pipeline_names(), ["review"])
            self.assertEqual(main.get_process_info("review")["task_pipeline"], "approval")
            task_pipeline = workflow.get_child_pipeline_by_process_code(main, "review")
            self.assertEqual(task_pipeline.get_all_pipeline_names(), ["Ready"])
            self.assertEqual(
                project.stype("types/object").pipelines()[0].get_info()["code"], "main"
            )
            schema = project.stype("types/object").schema()
            self.assertEqual(schema.get_info()["name"], "types/object")
            self.assertEqual(schema.get_parents(), [])
            self.assertEqual(
                schema.get_child("types/child", "types/object"), schema.get_children()[0]
            )
            dependencies = self.api.sobject(self.data["__search_key__"]).dependencies()
            note = dependencies["sthpw/note"][dependency_key]
            self.assertEqual(note.get_value("note"), "Review me")
            self.assertEqual(note.get_search_key(), dependency_key)
            with self.assertRaises(AttributeError):
                note.commit()

        with (
            patch.object(tc.env_inst, "projects", {"demo": self.project}),
            patch.object(tc, "execute_procedure_serverside", return_value=raw_dependencies),
        ):
            self.run_api(inspect)

    def test_commit_error_preserves_local_changes_and_refresh_contract(self):
        obj = self.run_api(lambda: self.api.sobject(self.data["__search_key__"]))
        obj.set_value("description", "pending")
        self.tactic.update.side_effect = OSError("reply lost")
        with self.assertRaisesRegex(OSError, "reply lost") as raised:
            self.run_api(obj.commit)
        self.assertTrue(raised.exception.__notes__)
        self.assertEqual(obj.changes(), {"description": "pending"})
        with self.assertRaises(DirtyObject):
            self.run_api(obj.refresh)
        obj.discard_changes()
        self.run_api(obj.refresh)
        self.assertEqual(obj.get_value("description"), "before")

    def test_remote_error_keeps_traceback_on_maya_python_without_add_note(self):
        class LegacyOSError(OSError):
            add_note = None

        obj = self.run_api(lambda: self.api.sobject(self.data["__search_key__"]))
        obj.set_value("description", "pending")
        self.tactic.update.side_effect = OSError("reply lost")
        with patch.object(remote, "OSError", LegacyOSError, create=True):
            with self.assertRaisesRegex(
                LegacyOSError, "Remote traceback"
            ) as raised:
                self.run_api(obj.commit)
        self.assertIn("reply lost", str(raised.exception))
        self.assertIn("Traceback", str(raised.exception))

    def test_ui_handles_and_native_files_use_only_domain_commands(self):
        self.assertEqual(self.ui_calls, [])
        target = self.api.ui.sobject(self.data["__search_key__"]).notes()
        operation = target.show()
        self.assertIsInstance(operation, Operation)
        self.assertIs(self.run_api(lambda: operation.wait(3)), target)
        self.assertEqual(
            self.ui_calls, [("sobject", self.data["__search_key__"]), ("dock", "notes")]
        )
        files = self.run_api(lambda: self.api.files.match(["scene.ma"]))
        self.assertEqual(self.run_api(files[0].get_file_ext), "ma")
        with self.assertRaises(AttributeError):
            files[0].delete_everything()

    def test_removed_api_modules_and_commands_are_absent(self):
        for module in ("environment", "tactic_classes", "global_functions", "maya_functions", "session"):
            self.assertIsNone(importlib.util.find_spec("tactic_handler_dcc." + module))
        self.assertEqual(
            self.registry.capabilities(),
            ["handler.call", "handler.close", "handler.release"],
        )
        with self.assertRaises(RuntimeError):
            self.dcc.request(
                "@tactic_handler",
                "tactic.module_getattr",
                {"module": "thlib.environment", "name": "env_inst"},
                timeout=3,
            )
        for member in ("_core", "module", "environment", "server_start"):
            with self.assertRaises(PermissionError):
                self.run_api(lambda: self.api._invoke("root", member))

    def test_handles_are_session_scoped_and_released(self):
        obj = self.run_api(lambda: self.api.sobject(self.data["__search_key__"]))
        other = from_client(self.dcc, timeout=3)
        try:
            with self.assertRaises(ReferenceError):
                self.run_api(lambda: other._invoke(obj._handle, "get_info"))
            self.run_api(obj.release)
            with self.assertRaises(ReferenceError):
                self.run_api(obj.get_project)
        finally:
            self.run_api(other.close)
        self.run_api(self.api.close)
        self.assertEqual(self.service._sessions, {})

    def test_plain_mapping_cannot_be_mistaken_for_object_reference(self):
        value = {"kind": "ref", "id": "root", "nested": (1, 2)}
        encoded = wire.encode(value, lambda obj: self.fail("not a reference"))
        restored = wire.decode(encoded, lambda obj: self.fail("not a reference"))
        self.assertEqual(restored, value)

    def test_domain_contract_names_real_methods_and_properties(self):
        import inspect
        from thlib import tactic_classes, global_functions
        from tactic_handler_api import api, objects, files, checkin, definitions
        from thlib.ui import tactic_rpc

        modules = (api, objects, files, checkin, definitions, tactic_rpc)
        instances = {
            "QueueItem": checkin.QueueItem(SimpleNamespace(_api=None), "Q1"),
            "DefinitionElement": definitions.DefinitionElement(None, "field"),
        }
        missing = object()
        for name, methods in METHODS.items():
            if name.startswith("Native"):
                native_name = name.removeprefix("Native")
                cls = getattr(tactic_classes, native_name, None) or getattr(
                    global_functions, native_name
                )
            else:
                cls = next(
                    getattr(module, name) for module in modules if hasattr(module, name)
                )
            for member in methods:
                with self.subTest(type=name, member=member):
                    self.assertTrue(callable(inspect.getattr_static(cls, member)))
            for member in PROPERTIES.get(name, ()):
                with self.subTest(type=name, property=member):
                    self.assertTrue(
                        member in getattr(cls, "__dataclass_fields__", {})
                        or inspect.getattr_static(
                            instances.get(name, cls), member, missing
                        )
                        is not missing
                    )

    def test_remote_create_preserves_pipeline_and_parent_relationship(self):
        key = "types/object?project=demo&code=O2"
        self.core.insert_sobjects = Mock(
            side_effect=lambda stype, project, values, **kwargs: {
                **values,
                "code": "O2",
                "__search_key__": key,
            }
        )

        def create():
            parent = self.api.sobject(self.data["__search_key__"])
            child = (
                self.api.project("demo")
                .stype("types/object")
                .new(
                    {"name": "Child", "pipeline_code": "chosen_pipeline"},
                    parent=parent,
                    relation="types/instance",
                    direction="child",
                )
            )
            child.set_value("description", "Local change")
            return child.commit(triggers=False)

        obj = self.run_api(create)
        self.assertEqual(obj.get_search_key(), key)
        self.assertEqual(obj.get_value("pipeline_code"), "chosen_pipeline")
        self.assertEqual(obj.get_value("description"), "Local change")
        self.assertEqual(
            self.core.insert_sobjects.call_args.kwargs,
            {
                "parent_key": self.data["__search_key__"],
                "instance_type": "types/instance",
                "instance_path": "child",
                "triggers": False,
            },
        )

    def test_remote_link_uses_the_existing_instance_relation(self):
        def link():
            parent = self.api.sobject(self.data["__search_key__"])
            child = self.api.sobject(self.data["__search_key__"])
            parent.link(child, relation="types/instance")

        self.run_api(link)

        self.core.edit_multiple_instance_sobjects.assert_called_once_with(
            "demo",
            insert_search_keys=[self.data["__search_key__"]],
            parent_key=self.data["__search_key__"],
            instance_type="types/instance",
            path=None,
        )

    def test_remote_definition_edits_exact_record_without_changing_expressions(self):
        row = {
            "code": "W1",
            "view": "edit",
            "search_type": "types/object",
            "login": "alice",
            "__search_key__": "config/widget_config?project=demo&code=W1",
            "config": '<config><!--keep--><edit><element name="category"><display class="SelectWdg"><values_expr>@GET(types/category.code)</values_expr></display></element></edit></config>',
        }
        self.tactic.query.return_value = [deepcopy(row)]
        self.tactic.update.side_effect = lambda key, values, **kwargs: {**row, **values}

        def edit():
            definition = (
                self.api.project("demo").stype("types/object").definitions.get("W1")
            )
            definition.element("category").set_option(
                "display", "empty", "-- Select --"
            )
            definition.commit()
            return definition.xml, definition.login

        xml, login = self.run_api(edit)
        self.assertIn("<!--keep-->", xml)
        self.assertIn("@GET(types/category.code)", xml)
        self.assertIn("<empty>-- Select --</empty>", xml)
        self.assertEqual(login, "alice")
        self.assertEqual(self.tactic.update.call_args.args[0], row["__search_key__"])
        self.assertEqual(set(self.tactic.update.call_args.args[1]), {"config"})

    def test_checkin_hydrates_snapshot_through_domain_queue(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.txt"
            source.write_text("data", encoding="utf-8")
            self.runtime._repositories = lambda: [
                {"name": "repo", "value": [directory, "", "", "repo", True]}
            ]
            result = {
                "__search_key__": "sthpw/snapshot?code=S1",
                "code": "S1",
                "version": 1,
            }
            self.tactic.query_snapshots.side_effect = lambda **kwargs: [
                {**result, "__files__": [], "snapshot": "<snapshot/>"}
            ]
            with patch(
                "thlib.checkin_operation.execute_checkin_payload", return_value=result
            ) as checkin:

                def submit():
                    queue = self.api.commit_queue("demo")
                    item = queue.add(
                        self.data["__search_key__"],
                        context="publish",
                        files=[source],
                        repository="repo",
                        generate_previews=False,
                    )
                    item.set_description("From DCC")
                    snapshot = item.commit()
                    self.assertEqual(snapshot.get_code(), "S1")
                    self.assertEqual(snapshot.get_files_objects(), [])
                    self.assertEqual(item.state, "finished")
                    item.commit()

                self.run_api(submit)
                checkin.assert_called_once()
                self.assertEqual(checkin.call_args.args[0]["description"], "From DCC")

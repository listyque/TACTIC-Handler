import sys
from types import ModuleType
import unittest
from unittest.mock import Mock, patch
from xmlrpc.client import Fault

import thlib.tactic_classes as tc
import thlib.tactic_query as tq


class TacticCoreContractTests(unittest.TestCase):
    class _GatewayError(RuntimeError):
        def __init__(self, status):
            self.code = status
            super().__init__("HTTP Error {0}: Proxy Error".format(status))

    @staticmethod
    def _gateway_error(status=502):
        return TacticCoreContractTests._GatewayError(status)

    def test_read_only_procedure_retries_temporary_gateway_failures(self):
        server = Mock()
        server.execute_python_script.side_effect = [
            self._gateway_error(),
            self._gateway_error(503),
            {"info": {"spt_ret_val": '{"records": []}'}},
        ]

        def procedure():
            return None

        with patch.object(tc.tq, "prepare_serverside_script", return_value={}), \
                patch("thlib.request_retry.time.sleep") as sleep:
            result = tc._execute_read_only_procedure_serverside(
                procedure, {}, project="demo", server=server
            )

        self.assertEqual(result, {"records": []})
        self.assertEqual(server.execute_python_script.call_count, 3)
        self.assertEqual(
            [call.args[0] for call in sleep.call_args_list],
            [0.35, 0.9],
        )

    def test_read_only_procedure_exposes_final_gateway_failure(self):
        server = Mock()
        server.execute_python_script.side_effect = self._gateway_error(504)

        def procedure():
            return None

        with patch.object(tc.tq, "prepare_serverside_script", return_value={}), \
                patch("thlib.request_retry.time.sleep"):
            with self.assertRaises(self._GatewayError) as raised:
                tc._execute_read_only_procedure_serverside(
                    procedure, {}, project="demo", server=server
                )

        self.assertEqual(raised.exception.code, 504)
        self.assertEqual(server.execute_python_script.call_count, 3)

    def test_read_only_procedure_retries_tactic_sudo_context_fault(self):
        server = Mock()
        server.execute_python_script.side_effect = [
            Fault(1, "('count of sudo: ', 0)"),
            {"info": {"spt_ret_val": '{"records": []}'}},
        ]

        def procedure():
            return None

        with patch.object(tc.tq, "prepare_serverside_script", return_value={}), \
                patch("thlib.request_retry.time.sleep") as sleep:
            result = tc._execute_read_only_procedure_serverside(
                procedure, {}, project="demo", server=server
            )

        self.assertEqual(result, {"records": []})
        self.assertEqual(server.execute_python_script.call_count, 2)
        sleep.assert_called_once_with(0.35)

    def test_sobject_query_uses_the_read_only_retry_boundary(self):
        payload = {"sobjects_list": []}
        with patch.object(
                tc, "_execute_read_only_procedure_serverside",
                return_value=payload,
        ) as execute, patch.object(
                tc, "execute_procedure_serverside",
                side_effect=AssertionError("unsafe raw query boundary"),
        ), patch.object(
                tc, "hydrate_sobjects_payload", return_value=(object(), {})
        ):
            tc.get_sobjects(
                "demo/asset", project_code="demo", return_payload=True
            )

        execute.assert_called_once()
        self.assertIs(execute.call_args.args[0], tq.query_sobjects)

    def test_mutating_procedure_does_not_retry_gateway_failure(self):
        server = Mock()
        server.execute_python_script.side_effect = self._gateway_error()

        def procedure():
            return None

        with patch.object(tc.tq, "prepare_serverside_script", return_value={}):
            with self.assertRaises(self._GatewayError):
                tc.execute_procedure_serverside(
                    procedure, {}, project="demo", server=server
                )

        server.execute_python_script.assert_called_once()

    def test_server_traceback_raises_structured_error(self):
        server = Mock()
        server.execute_python_script.return_value = {
            "info": "Traceback (most recent call last):\nValueError: broken"
        }

        def procedure():
            return None

        with patch.object(tc.tq, "prepare_serverside_script", return_value={}), \
                patch.object(tc.dl, "exception"):
            with self.assertRaises(tc.TacticProcedureError) as raised:
                tc.execute_procedure_serverside(
                    procedure, {}, project="demo", server=server
                )

        self.assertEqual(raised.exception.procedure, "procedure")
        self.assertEqual(raised.exception.project, "demo")
        self.assertIn("ValueError: broken", raised.exception.server_traceback)

    def test_search_type_relationship_uses_search_code(self):
        schema = Mock()
        schema.get_child.return_value = {
            "relationship": "search_type",
            "from": "sthpw/note",
            "to": "demo/asset",
        }
        child_stype = Mock()
        child_stype.get_code.return_value = "sthpw/note"
        parent_stype = Mock()
        parent_stype.get_code.return_value = "demo/asset"
        parent_stype.get_schema.return_value = schema
        sobject = tc.SObject({"code": "ASSET0001"})

        expression = sobject.get_related_sobjects_tel_string(
            child_stype=child_stype,
            parent_stype=parent_stype,
            path="child",
        )

        self.assertEqual(
            expression,
            "@SOBJECT(sthpw/note['search_code', 'ASSET0001'])",
        )

    def test_code_relationship_uses_declared_columns_in_both_directions(self):
        relation = {
            "relationship": "code",
            "from": "demo/shot",
            "to": "demo/episode",
            "from_col": "episode_code",
            "to_col": "code",
        }
        schema = Mock()
        schema.get_child.return_value = relation
        schema.get_parent.return_value = relation
        child_stype = Mock()
        child_stype.get_code.return_value = "demo/shot"
        child_stype.get_schema.return_value = schema
        parent_stype = Mock()
        parent_stype.get_code.return_value = "demo/episode"
        parent_stype.get_schema.return_value = schema

        parent = tc.SObject({"code": "EPISODE0001"})
        child = tc.SObject({"code": "SHOT0001", "episode_code": "EPISODE0001"})

        self.assertEqual(
            parent.get_related_sobjects_tel_string(
                child_stype, parent_stype, path="child"
            ),
            "@SOBJECT(demo/shot['episode_code', 'EPISODE0001'])",
        )
        self.assertEqual(
            child.get_related_sobjects_tel_string(
                child_stype, parent_stype, path="parent"
            ),
            "@SOBJECT(demo/episode['code', 'EPISODE0001'])",
        )

    def test_instance_relationship_uses_instance_foreign_keys(self):
        relation = {
            "relationship": "instance",
            "instance_type": "demo/shot_in_sequence",
            "from": "demo/shot",
            "to": "demo/sequence",
        }
        instance_relation = {
            "from": "demo/shot_in_sequence",
            "to": "demo/shot",
            "from_col": "shot_code",
            "to_col": "sequence_code",
        }
        schema = Mock()
        schema.get_child.return_value = relation
        instance_schema = Mock()
        instance_schema.get_child_instance.return_value = instance_relation
        child_stype = Mock()
        child_stype.get_code.return_value = "demo/shot"
        parent_stype = Mock()
        parent_stype.get_code.return_value = "demo/sequence"
        parent_stype.get_schema.return_value = schema
        parent = tc.SObject({"code": "SEQUENCE0001"})
        parent.get_schema = Mock(return_value=instance_schema)

        expression = parent.get_related_sobjects_tel_string(
            child_stype, parent_stype, path="child"
        )

        self.assertEqual(
            expression,
            "@SOBJECT(demo/shot_in_sequence['sequence_code', "
            "'SEQUENCE0001'].demo/shot)",
        )

    def test_related_insert_uses_native_instance_path(self):
        server = Mock()
        server.insert.return_value = {
            "__search_key__": "demo/asset?code=CHILD"
        }
        server.split_search_key.side_effect = [
            ("demo/asset", "CHILD"),
            ("demo/asset", "PARENT"),
        ]
        parent = object()
        child = object()
        server.query.side_effect = [[parent], [child]]
        instance = Mock()
        search_type = Mock()
        search_type.create.return_value = instance
        pyasm = ModuleType("pyasm")
        pyasm_search = ModuleType("pyasm.search")
        pyasm_search.SearchType = search_type
        pyasm.search = pyasm_search

        with patch.dict(
            sys.modules,
            {"pyasm": pyasm, "pyasm.search": pyasm_search},
        ), patch.object(tq, "server", server, create=True):
            result = tq.insert_sobjects(
                "demo/asset",
                "demo",
                {"name": "Child"},
                parent_key="demo/asset?code=PARENT",
                instance_type="demo/asset_in_asset",
                instance_path="child_asset",
            )

        self.assertEqual(result, server.insert.return_value)
        instance.add_related_connection.assert_called_once_with(
            child, parent, src_path="child_asset"
        )
        instance.commit.assert_called_once_with()

    def test_related_batch_insert_uses_native_multiple_and_instance_path(self):
        server = Mock()
        inserted = [
            {"__search_key__": "demo/asset?code=CHILD001"},
            {"__search_key__": "demo/asset?code=CHILD002"},
        ]
        server.insert_multiple.return_value = inserted
        server.split_search_key.side_effect = [
            ("demo/asset", "CHILD001"),
            ("demo/asset", "PARENT"),
            ("demo/asset", "CHILD002"),
            ("demo/asset", "PARENT"),
        ]
        parent = object()
        children = [object(), object()]
        server.query.side_effect = [
            [parent], [children[0]], [parent], [children[1]],
        ]
        instances = [Mock(), Mock()]
        search_type = Mock()
        search_type.create.side_effect = instances
        pyasm = ModuleType("pyasm")
        pyasm_search = ModuleType("pyasm.search")
        pyasm_search.SearchType = search_type
        pyasm.search = pyasm_search
        values = [{"name": "Child 1"}, {"name": "Child 2"}]

        with patch.dict(
            sys.modules,
            {"pyasm": pyasm, "pyasm.search": pyasm_search},
        ), patch.object(tq, "server", server, create=True):
            result = tq.insert_sobjects(
                "demo/asset",
                "demo",
                values,
                parent_key="demo/asset?code=PARENT",
                instance_type="demo/asset_in_asset",
                instance_path="child_asset",
            )

        self.assertEqual(result, inserted)
        server.insert_multiple.assert_called_once_with(
            "demo/asset", values, [{}, {}],
            "demo/asset?code=PARENT", False, True,
        )
        for instance, child in zip(instances, children):
            instance.add_related_connection.assert_called_once_with(
                child, parent, src_path="child_asset"
            )
            instance.commit.assert_called_once_with()

    def test_batch_insert_rejects_an_incomplete_server_result(self):
        server = Mock()
        server.insert_multiple.return_value = [
            {"__search_key__": "demo/shot?code=SHOT001"}
        ]
        pyasm = ModuleType("pyasm")
        pyasm_search = ModuleType("pyasm.search")
        pyasm_search.SearchType = Mock()
        pyasm.search = pyasm_search

        with patch.dict(
            sys.modules,
            {"pyasm": pyasm, "pyasm.search": pyasm_search},
        ), patch.object(tq, "server", server, create=True):
            with self.assertRaisesRegex(RuntimeError, "every batch-created"):
                tq.insert_sobjects(
                    "demo/shot",
                    "demo",
                    [{"name": "shot_001"}, {"name": "shot_002"}],
                )

    def test_existing_instance_relation_is_not_inserted_again(self):
        server = Mock()
        server.split_search_key.side_effect = [
            ("demo/texture", "TEXTURE0001"),
            ("demo/asset", "ASSET0001"),
        ]
        parent = object()
        child = object()
        server.query.side_effect = [[parent], [child]]

        existing = Mock()
        existing.get_search_key.return_value = (
            "demo/texture_in_asset?code=REL0001"
        )
        search = Mock()
        search.eval.side_effect = [[existing], [existing]]
        search_type = Mock()
        pyasm = ModuleType("pyasm")
        pyasm_search = ModuleType("pyasm.search")
        pyasm_search.Search = search
        pyasm_search.SearchType = search_type
        pyasm.search = pyasm_search

        with patch.dict(
            sys.modules,
            {"pyasm": pyasm, "pyasm.search": pyasm_search},
        ), patch.object(tq, "server", server, create=True):
            result = tq.edit_multiple_instance_sobjects(
                "demo",
                insert_search_keys=[
                    "demo/texture?project=demo&code=TEXTURE0001"
                ],
                parent_key="demo/asset?project=demo&code=ASSET0001",
                instance_type="demo/texture_in_asset",
            )

        self.assertEqual(result, "ok")
        search_type.create.assert_not_called()
        self.assertEqual(
            [call.args[0] for call in search.eval.call_args_list],
            [
                "@SOBJECT(demo/texture_in_asset)",
                "@SOBJECT(demo/texture_in_asset)",
            ],
        )

    def test_workflow_indexes_child_pipeline_by_parent_process(self):
        workflow = tc.Workflow([
            {
                "code": "asset",
                "search_type": "demo/asset",
                "stypes_processes": [{
                    "process": "model",
                    "code": "PROCESS0001",
                }],
            },
            {
                "code": "model_tasks",
                "search_type": "sthpw/task",
                "parent_process": "PROCESS0001",
                "stypes_processes": [],
            },
        ])
        parent = workflow.get_by_pipeline_code("demo/asset", "asset")

        child = workflow.get_child_pipeline_by_process_code(parent, "model")

        self.assertEqual(child.get_info()["code"], "model_tasks")


if __name__ == "__main__":
    unittest.main()

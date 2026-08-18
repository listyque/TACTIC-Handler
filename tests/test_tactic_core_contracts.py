import unittest
from unittest.mock import Mock, patch

import thlib.tactic_classes as tc


class TacticCoreContractTests(unittest.TestCase):
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

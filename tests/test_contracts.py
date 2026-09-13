from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path
import textwrap
import unittest
# Import before thlib extends sys.path with its Python 2 compatibility bundle.
from unittest import mock as _stdlib_mock

from thlib import tactic_classes as tc
from thlib import tactic_query as tq

from tests.support.build_contract_manifest import ROOT, build_manifest


CONTRACTS = ROOT / "tests" / "contracts"


class ServerProcedureContractTests(unittest.TestCase):
    def test_every_core_server_procedure_used_by_thlib_compiles(self):
        source_path = ROOT / "thlib" / "tactic_classes.py"
        tree = ast.parse(source_path.read_text(encoding="utf-8-sig"))
        names = set()
        for node in ast.walk(tree):
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "execute_procedure_serverside"
                and node.args
                and isinstance(node.args[0], ast.Attribute)
                and isinstance(node.args[0].value, ast.Name)
                and node.args[0].value.id == "tq"
            ):
                continue
            names.add(node.args[0].attr)
        names = sorted(names)
        self.assertGreater(len(names), 20)
        for name in names:
            with self.subTest(procedure=name):
                function = getattr(tq, name)
                code = tq.prepare_serverside_script(
                    function, {}, shrink=False, catch_traceback=False,
                )["code"]
                compile(
                    "def execute():\n" + textwrap.indent(code, "    "),
                    f"<{name}>", "exec",
                )

    def test_identity_procedures_generate_code_skeys(self):
        procedures = (
            tq.query_server_updates,
            tq.query_task_workspace_page,
            tq.query_user_profile_data,
            tq.query_chat_conversations,
            tq.send_chat_message,
            tq.get_notes_with_attachments,
        )
        for function in procedures:
            with self.subTest(procedure=function.__name__):
                source = inspect.getsource(function)
                self.assertNotIn("use_id=True", source)
                self.assertNotIn("?id=", source)

    def test_server_update_shape_is_stable(self):
        contracts = json.loads(
            (CONTRACTS / "data_shapes.json").read_text(encoding="utf-8")
        )
        procedures = {
            "serverUpdates": tq.query_server_updates,
            "taskPage": tq.query_task_workspace_page,
            "userProfile": tq.query_user_profile_data,
        }
        for contract, function in procedures.items():
            source = inspect.getsource(function)
            for key in contracts[contract]:
                with self.subTest(contract=contract, key=key):
                    self.assertIn(repr(key), source)

    def test_user_profile_uses_scoped_hours_without_a_second_activity_source(self):
        source = inspect.getsource(tq.query_user_profile_data)

        self.assertNotIn("sthpw/message_log", source)
        self.assertNotIn("sthpw/status_log", source)
        self.assertNotIn("sthpw/snapshot", source)
        self.assertNotIn("sthpw/note", source)
        self.assertNotIn("'activity':", source)
        self.assertNotIn("'tasks':", source)
        self.assertNotIn("'taskTotal':", source)
        self.assertIn("'viewWorkHours'", source)
        self.assertIn("week_start.isoformat(), op='>='", source)
        self.assertIn("entry.get_value('over_time')", source)
        self.assertIn("week_end.isoformat(), op='<='", source)


class NativeObjectContractTests(unittest.TestCase):
    def test_domain_objects_remain_native_sobjects(self):
        for object_type in (tc.File, tc.Snapshot, tc.Task):
            with self.subTest(object_type=object_type.__name__):
                self.assertTrue(issubclass(object_type, tc.SObject))

    def test_native_file_repository_and_preview_api_is_available(self):
        required = {
            "prepare_repo", "get_icon_preview", "get_file_size",
            "is_local_current",
            "get_filename_with_ext", "get_repo_path", "get_abs_path",
        }
        self.assertTrue(required.issubset(set(dir(tc.File))))

    def test_metadata_contracts_use_code_identity(self):
        contracts = json.loads(
            (CONTRACTS / "metadata_schemas.json").read_text(encoding="utf-8")
        )
        self.assertEqual(contracts["message"]["identity"], "code")
        self.assertEqual(contracts["note"]["identity"], "code")
        self.assertNotIn("id", contracts["message"]["allowed"])
        self.assertNotIn("id", contracts["note"]["allowed"])


class PublicApiContractTests(unittest.TestCase):
    def test_public_thlib_api_contains_the_reviewed_baseline(self):
        baseline = json.loads(
            (CONTRACTS / "thlib_public_api.json").read_text(encoding="utf-8")
        )
        current = build_manifest()
        for module, records in baseline.items():
            self.assertIn(module, current)
            for name, contract in records.items():
                with self.subTest(module=module, name=name):
                    self.assertIn(name, current[module])
                    actual = current[module][name]
                    self.assertEqual(actual["kind"], contract["kind"])
                    if contract["kind"] == "function":
                        self._assert_signature_compatible(contract, actual)
                    else:
                        for method, signature in contract["methods"].items():
                            self.assertIn(method, actual["methods"])
                            self._assert_signature_compatible(
                                signature, actual["methods"][method]
                            )

    def _assert_signature_compatible(self, baseline, current):
        expected = baseline["positional"]
        self.assertEqual(current["positional"][:len(expected)], expected)
        self.assertEqual(current["required"][:len(baseline["required"])],
                         baseline["required"])
        if baseline["vararg"]:
            self.assertEqual(current["vararg"], baseline["vararg"])
        if baseline["kwarg"]:
            self.assertEqual(current["kwarg"], baseline["kwarg"])


if __name__ == "__main__":
    unittest.main()

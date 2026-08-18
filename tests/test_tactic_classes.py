from __future__ import annotations

import unittest
import textwrap
from unittest.mock import patch

from thlib import tactic_classes as tc
from thlib import tactic_query as tq
from thlib import global_functions as gf


class SObjectDeleteTests(unittest.TestCase):
    def setUp(self):
        self.sobject = tc.SObject({"__search_key__": "sthpw/note?code=NOTE0001"})

    def test_delete_without_confirmation_has_no_dependency_list(self):
        with patch.object(tc, "execute_procedure_serverside", return_value=True) as execute:
            self.assertTrue(self.sobject.delete_sobject(confirm=False))

        self.assertIsNone(execute.call_args.args[1]["list_dependencies"])

    def test_explicit_dependencies_are_preserved(self):
        with patch.object(tc, "execute_procedure_serverside", return_value=True) as execute:
            self.sobject.delete_sobject(list_dependencies=["sthpw/file"])

        self.assertEqual(
            execute.call_args.args[1]["list_dependencies"],
            {"related_types": ["sthpw/file"]},
        )


class ServerProcedureTests(unittest.TestCase):
    def test_modern_python_does_not_use_the_legacy_ast_minifier(self):
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

    def test_batched_modern_queries_compile_for_server(self):
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

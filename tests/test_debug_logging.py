from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest
from unittest.mock import patch
from xmlrpc.client import Fault

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from thlib.ui.debug_logging import DebugLogController
from thlib.ui.handler_server_controller import HandlerServerController
from thlib.ui.request_metrics import request_metrics
from thlib.request_retry import defer_transient_error_reporting


class DebugLoggingModeTests(unittest.TestCase):
    def setUp(self):
        read_patcher = patch(
            "thlib.ui.debug_logging.env_read_config", return_value={}
        )
        write_patcher = patch("thlib.ui.debug_logging.env_write_config")
        read_patcher.start()
        write_patcher.start()
        self.addCleanup(read_patcher.stop)
        self.addCleanup(write_patcher.stop)

    def test_default_mode_keeps_only_error_and_critical(self):
        with TemporaryDirectory() as directory:
            controller = DebugLogController(Path(directory))
            controller.log("INFO", "progress detail")
            controller.log("API", "server request")
            controller.log("EXCEPTION", "handled exception")
            controller.log("ERROR", "download failed")
            controller.log("CRITICAL", "database unavailable")

            self.assertEqual(
                [record["level"] for record in controller._live_entries],
                ["ERROR", "CRITICAL"],
            )
            controller.shutdown()
            records = controller._read_session_records(controller._json_log)
            messages = [record["message"] for record in records]
            self.assertIn("download failed", messages)
            self.assertIn("database unavailable", messages)
            self.assertNotIn("progress detail", messages)
            self.assertNotIn("server request", messages)
            self.assertNotIn("handled exception", messages)
            self.assertFalse(list(Path(directory, "log").glob("*.log")))

    def test_individual_recording_levels_are_persisted_and_applied(self):
        with TemporaryDirectory() as directory:
            controller = DebugLogController(Path(directory))
            controller.set_recording_levels(["INFO", "WARNING"])
            controller.log("INFO", "progress detail")
            controller.log("WARNING", "slow request")
            controller.log("ERROR", "not selected")

            self.assertEqual(
                controller.recording_levels, ["INFO", "WARNING"]
            )
            self.assertEqual(
                [record["level"] for record in controller._live_entries],
                ["INFO", "WARNING"],
            )
            stored = json.loads(
                controller._settings.get("debugLog/enabledLevels", "[]")
            )
            self.assertEqual(stored, ["INFO", "WARNING"])
            controller.shutdown()

    def test_all_recording_levels_can_be_enabled_explicitly(self):
        with TemporaryDirectory() as directory:
            controller = DebugLogController(Path(directory))
            controller.set_recording_levels([
                "LOG", "INFO", "WARNING", "MISSING", "EXCEPTION",
                "ERROR", "CRITICAL", "API",
            ])
            controller.log("INFO", "progress detail")

            self.assertEqual(controller._live_entries[-1]["level"], "INFO")
            controller.shutdown()

    def test_set_server_success_is_silent_but_failure_is_recorded(self):
        class FakeServer:
            project_code = "sthpw"

        with TemporaryDirectory() as directory:
            request_metrics.reset()
            self.addCleanup(request_metrics.reset)
            controller = DebugLogController(Path(directory))
            controller.set_recording_levels(["API", "EXCEPTION"])

            def successful_set_server(server, server_name):
                server.server_name = server_name

            wrapped_success = controller._server_wrapper(
                "set_server", successful_set_server
            )
            wrapped_success(FakeServer(), "https://example.invalid")
            self.assertEqual(controller._live_entries, [])
            self.assertNotIn(
                "xmlrpc.set_server", request_metrics.snapshot()
            )

            def failing_set_server(server, server_name):
                raise ValueError("Invalid server address")

            wrapped_failure = controller._server_wrapper(
                "set_server", failing_set_server
            )
            with self.assertRaisesRegex(ValueError, "Invalid server address"):
                wrapped_failure(FakeServer(), "not a server")

            self.assertEqual(len(controller._live_entries), 1)
            failure = controller._live_entries[0]
            self.assertEqual(failure["level"], "EXCEPTION")
            self.assertEqual(failure["group"], "server/set_server")
            self.assertIn(".set_server(", failure["command"])
            self.assertIn("ValueError", failure["stacktrace"])
            controller.shutdown()

    def test_intermediate_gateway_retry_does_not_open_error_surface(self):
        class GatewayError(RuntimeError):
            code = 502

        class FakeServer:
            project_code = "sthpw"

        def temporary_failure(server):
            raise GatewayError("HTTP Error 502: Proxy Error")

        with TemporaryDirectory() as directory:
            controller = DebugLogController(Path(directory))
            controller.set_recording_levels(["EXCEPTION"])
            wrapped = controller._server_wrapper(
                "execute_python_script", temporary_failure
            )

            with defer_transient_error_reporting():
                with self.assertRaises(GatewayError):
                    wrapped(FakeServer())

            self.assertFalse(controller.error_visible)
            self.assertEqual(controller._live_entries, [])
            controller.shutdown()

    def test_intermediate_sudo_retry_does_not_open_error_surface(self):
        class FakeServer:
            project_code = "sthpw"

        def temporary_failure(server):
            raise Fault(1, "('count of sudo: ', 0)")

        with TemporaryDirectory() as directory:
            controller = DebugLogController(Path(directory))
            controller.set_recording_levels(["EXCEPTION"])
            wrapped = controller._server_wrapper(
                "execute_python_script", temporary_failure
            )

            with defer_transient_error_reporting():
                with self.assertRaises(Fault):
                    wrapped(FakeServer())

            self.assertFalse(controller.error_visible)
            self.assertEqual(controller._live_entries, [])
            controller.shutdown()

    def test_error_classification_uses_exception_and_stacktrace_details(self):
        class PreviewGenerationFailure(Exception):
            pass

        self.assertEqual(
            DebugLogController.classify_error(TypeError("bad argument")),
            "type_error",
        )
        self.assertEqual(
            DebugLogController.classify_error(
                RuntimeError("remote failure"),
                "xmlrpc.client.Fault: do_query error: SELECT invalid",
            ),
            "database_query_error",
        )
        self.assertEqual(
            DebugLogController.classify_error(
                "worker failed",
                "Traceback (most recent call last):\nFileNotFoundError: scene.ma",
            ),
            "file_not_found_error",
        )
        custom_error = PreviewGenerationFailure("preview failed")
        self.assertEqual(
            DebugLogController.exception_kind(custom_error),
            "PreviewGenerationFailure",
        )
        self.assertEqual(
            DebugLogController._humanize_exception_kind(
                type(custom_error).__name__
            ),
            "Preview Generation Failure",
        )
        with TemporaryDirectory() as directory:
            controller = DebugLogController(Path(directory))
            controller.raise_error(custom_error)
            self.assertEqual(controller.error_type, "unknown_error")
            self.assertEqual(controller.error_kind, "PreviewGenerationFailure")
            self.assertEqual(controller.error_title, "Preview Generation Failure")
            controller.shutdown()

    def test_nested_url_timeout_is_classified_with_complete_diagnostics(self):
        from urllib.error import URLError

        error = URLError(TimeoutError("Удалённый компьютер не ответил"))
        self.assertEqual(
            DebugLogController.classify_error(error),
            "connection_timeout",
        )
        refused = URLError(ConnectionRefusedError("Соединение отклонено"))
        self.assertEqual(
            DebugLogController.classify_error(refused),
            "connection_refused",
        )
        with TemporaryDirectory() as directory:
            controller = DebugLogController(Path(directory))
            controller.set_recording_levels(["EXCEPTION"])
            stacktrace = (
                "Traceback (most recent call last):\n"
                "TimeoutError: [WinError 10060] remote host did not respond\n"
                "urllib.error.URLError: <urlopen error [WinError 10060]>"
            )
            controller.raise_error(
                error,
                stacktrace=stacktrace,
                group="server/execute_python_script",
            )

            self.assertEqual(controller.error_type, "connection_timeout")
            self.assertEqual(controller.error_message, str(error))
            event = controller._live_entries[-1]
            self.assertEqual(event["message"], str(error))
            self.assertEqual(event["stacktrace"], stacktrace)
            controller.shutdown()

    def test_native_admin_denial_is_not_misclassified_as_a_protocol_error(self):
        from xmlrpc.client import Fault
        for message in ('TACTIC administrator access is required',
                        'Only a TACTIC administrator can change access rules'):
            error = Fault(1, message)
            self.assertEqual(DebugLogController.classify_error(
                error, 'xmlrpc.client.Fault: ' + str(error)), 'permission_error')

    def test_deleted_project_database_is_reported_as_unavailable(self):
        from xmlrpc.client import Fault

        error = Fault(1, 'This database [complex] does not exist')
        self.assertEqual(
            DebugLogController.classify_error(
                error, 'xmlrpc.client.Fault: ' + str(error)),
            'no_project_error',
        )

    def test_error_stacktrace_copy_keeps_the_complete_trace(self):
        stacktrace = "Traceback\n" + "complete diagnostic line\n" * 400
        with TemporaryDirectory() as directory:
            controller = DebugLogController(Path(directory))
            controller._error_stacktrace = stacktrace
            with patch("thlib.ui.debug_logging.QGuiApplication") as application:
                self.assertTrue(controller.copy_error_stacktrace())
                application.clipboard.return_value.setText.assert_called_once_with(
                    stacktrace
                )
            controller.shutdown()

    def test_session_jsonl_uses_compact_disk_keys_and_restores_ui_roles(self):
        with TemporaryDirectory() as directory:
            controller = DebugLogController(Path(directory))
            controller.set_recording_levels(["ERROR"])
            controller.log(
                "ERROR", "Compact failure", group="network/request",
                source="Runtime", command="tc.query()", line=27,
                module="requests.py", function="send",
                details="Readable details",
            )
            controller.shutdown()

            lines = controller._json_log.read_text(
                encoding="utf-8"
            ).splitlines()
            self.assertEqual(json.loads(lines[0]), {"v": 1})
            stored = json.loads(lines[1])
            self.assertEqual(stored["m"], "Compact failure")
            self.assertEqual(stored["g"], "network/request")
            self.assertNotIn("message", stored)
            self.assertNotIn("timestamp", stored)
            self.assertNotIn("selected", stored)

            restored = controller._read_session_records(
                controller._json_log
            )[0]
            self.assertEqual(restored["message"], "Compact failure")
            self.assertEqual(restored["group"], "network/request")
            self.assertEqual(restored["command"], "tc.query()")
            self.assertEqual(restored["line"], 27)
            self.assertFalse(restored["selected"])

    def test_session_reader_requires_current_schema_header(self):
        with TemporaryDirectory() as directory:
            path = Path(directory, "session_invalid.jsonl")
            path.write_text(
                json.dumps({"m": "Header is required"}) + "\n",
                encoding="utf-8",
            )
            controller = DebugLogController(Path(directory))

            with self.assertRaisesRegex(ValueError, "Unsupported"):
                controller._read_session_records(path)

            controller.refresh_session_history()
            self.assertEqual(controller.sessions_model.rowCount(), 0)
            controller.shutdown()

    def test_runtime_command_and_session_fields_are_not_truncated(self):
        class FakeServer:
            project_code = "demo"

        def execute_python_script(
            self, script_body, options, session_token
        ):
            return None

        script_body = "print('diagnostic')\n" * 400
        leaf = "deep-value-" * 700
        options = {"leaf": leaf}
        for depth in range(12):
            options = {f"level_{depth}": options}

        with TemporaryDirectory() as directory:
            controller = DebugLogController(Path(directory))
            controller.set_recording_levels(["API"])
            command = controller._runtime_command(
                FakeServer(),
                "execute_python_script",
                execute_python_script,
                (script_body, options, "do-not-log-this-token"),
                {},
            )
            message = "message-" * 900
            stacktrace = "stacktrace-" * 900
            details = "details-" * 900
            controller.log(
                "API",
                message,
                group="server/execute_python_script",
                command=command,
                stacktrace=stacktrace,
                details=details,
            )
            controller.shutdown()

            restored = controller._read_session_records(
                controller._json_log
            )[0]

        self.assertIn(f"script_body={script_body!r}", command)
        self.assertIn(leaf, command)
        self.assertNotIn("do-not-log-this-token", command)
        self.assertIn("<redacted>", command)
        self.assertNotIn("<truncated", command)
        self.assertNotIn("<depth limit>", command)
        self.assertEqual(restored["message"], message)
        self.assertEqual(restored["command"], command)
        self.assertEqual(restored["stacktrace"], stacktrace)
        self.assertEqual(restored["details"], details)

    def test_handler_server_payload_details_are_complete_and_redacted(self):
        text = "handler-result-" * 500
        nested = {"leaf": "complete"}
        for depth in range(12):
            nested = {f"level_{depth}": nested}
        payload = {
            "text": text,
            "items": list(range(250)),
            "nested": nested,
            "session_token": "do-not-log-this-token",
        }

        detail = HandlerServerController._payload_detail(payload)
        restored = json.loads(detail)

        self.assertEqual(restored["text"], text)
        self.assertEqual(restored["items"], list(range(250)))
        cursor = restored["nested"]
        for depth in reversed(range(12)):
            cursor = cursor[f"level_{depth}"]
        self.assertEqual(cursor, {"leaf": "complete"})
        self.assertEqual(restored["session_token"], "<redacted>")
        self.assertNotIn("do-not-log-this-token", detail)
        self.assertNotIn("truncated", detail.lower())
        self.assertNotIn("depth limit", detail.lower())


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.qt_application import gui_test_application
from thlib.ui.handler_server_controller import HandlerServerController


class DebugLogStub:
    def __init__(self):
        self.entries = []

    def raise_error(self, *args, **kwargs):
        return None

    def log(self, level, message, **kwargs):
        self.entries.append({
            "level": level, "message": message, **kwargs,
        })


class HandlerServerControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def setUp(self):
        self.discovery_directory = tempfile.TemporaryDirectory()
        self.previous_discovery_directory = os.environ.get(
            "TACTIC_HANDLER_DISCOVERY_DIR"
        )
        os.environ["TACTIC_HANDLER_DISCOVERY_DIR"] = (
            self.discovery_directory.name
        )
        self.debug_log = DebugLogStub()
        self.controller = HandlerServerController(
            Path(__file__).resolve().parents[1], self.debug_log
        )

    def tearDown(self):
        self.controller.shutdown()
        if self.previous_discovery_directory is None:
            os.environ.pop("TACTIC_HANDLER_DISCOVERY_DIR", None)
        else:
            os.environ["TACTIC_HANDLER_DISCOVERY_DIR"] = (
                self.previous_discovery_directory
            )
        self.discovery_directory.cleanup()

    def _wait(self, predicate, timeout=8.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.app.processEvents()
            if predicate():
                return
            time.sleep(0.02)
        self.fail("Timed out waiting for Handler Server controller state")

    def test_server_demo_and_command(self):
        self.controller.start_server()
        self._wait(lambda: self.controller.state == "running")
        self.controller.start_demo()
        self._wait(lambda: self.controller.clients.count() == 1)
        self.controller.select_client(0)
        self.assertEqual(self.controller.selectedApplicationType, "maya")
        self.assertEqual(self.controller.activeEnvironment, "maya")
        self.assertTrue(self.controller.has_dcc_capability("open"))
        self.assertTrue(any(
            action.get("checked")
            for action in self.controller.clientMenuActions
            if action.get("command") == "dcc_client:demo-maya"
        ))
        request_id = self.controller.send_command(
            "ping", '{"value": 7, "session_token": "do-not-log"}', 2
        )
        self.assertTrue(request_id)
        self._wait(lambda: any(
            record.get("requestId") == request_id
            and record.get("status") == "completed"
            for record in self.controller.results._records
        ))
        command_logs = [
            entry for entry in self.debug_log.entries
            if entry.get("group") == "handler_server/command"
        ]
        self.assertTrue(command_logs)
        self.assertFalse(any(
            "do-not-log" in str(entry) for entry in command_logs
        ))
        self.assertTrue(any(
            "<redacted>" in str(entry.get("details") or "")
            for entry in command_logs
        ))
        request_id = self.controller.send_active_command(
            "get_current_scene", {}, 2
        )
        self.assertTrue(request_id)
        self._wait(lambda: any(
            record.get("requestId") == request_id
            and record.get("status") == "completed"
            for record in self.controller.results._records
        ))
        self.controller.stop_server()
        self._wait(lambda: self.controller.state == "stopped")
        self.app.processEvents()
        self.assertFalse(any(
            "Cannot read property" in str(record.get("summary") or "")
            or "Cannot read property" in str(record.get("detail") or "")
            for record in self.controller.results._records
        ))

    def test_unexpected_exit_does_not_wait_and_finishes_pending_commands(self):
        class ClientStub:
            def __init__(self):
                self.stop_calls = []

            def stop(self, wait=True):
                self.stop_calls.append(wait)
                if wait:
                    raise AssertionError("GUI teardown must not join client threads")

        client = ClientStub()
        self.controller._client = client
        self.controller._pending = {
            "request-1": {
                "target": "maya-1",
                "action": "open_scene",
                "startedAt": time.monotonic(),
            },
        }
        completions = []
        self.controller.commandFinished.connect(
            lambda *values: completions.append(values)
        )

        self.controller._server_finished(1, None)

        self.assertEqual(client.stop_calls, [False])
        self.assertIsNone(self.controller._client)
        self.assertEqual(self.controller._pending, {})
        self.assertEqual(len(completions), 1)
        self.assertEqual(completions[0][0], "request-1")
        self.assertFalse(completions[0][1])
        self.assertIn("exited with code 1", completions[0][3])
        self.assertIn("exited with code 1", self.controller.error)

        self.controller._handle_response({
            "type": "result", "request_id": "request-1",
            "success": True, "payload": {},
        })
        self.assertEqual(len(completions), 1)

    def test_command_can_target_the_maya_client_stored_by_commit_queue(self):
        class ClientStub:
            connected = True

            def __init__(self):
                self.commands = []

            def send_command(self, target, action, payload, timeout):
                self.commands.append((target, action, payload, timeout))
                return "request-1"

            @staticmethod
            def stop(wait=True):
                return None

            @staticmethod
            def shutdown_server():
                return None

        client = ClientStub()
        self.controller._client = client
        self.controller.clients.replace([
            {
                "clientId": "maya-1",
                "applicationType": "maya",
                "processId": 1,
                "capabilities": [
                    "prepare_checkin", "focus_application", "open_scene",
                ],
                "capabilityText": "prepare_checkin, focus_application, open_scene",
                "selected": True,
            },
            {
                "clientId": "maya-2",
                "applicationType": "maya",
                "processId": 2,
                "capabilities": [
                    "prepare_checkin", "focus_application", "open_scene",
                ],
                "capabilityText": "prepare_checkin, focus_application, open_scene",
                "selected": False,
            },
        ])
        self.controller._selected_client = "maya-1"
        self.controller._dcc_preferences = lambda _application: {
            "focus_after_open": False,
            "focus_after_save": True,
        }

        with patch.object(
            self.controller, "_allow_client_foreground"
        ) as allow_foreground:
            request_id = self.controller.send_client_command(
                "maya-2", "prepare_checkin", {"path": "scene.ma"}, 120.0
            )

        self.assertEqual(request_id, "request-1")
        self.assertEqual(client.commands[0][0], "maya-2")
        self.assertEqual(client.commands[0][1], "prepare_checkin")
        self.assertTrue(client.commands[0][2]["focus_application"])
        allow_foreground.assert_called_once_with(2)

        with patch.object(
            self.controller, "_allow_client_foreground"
        ) as allow_foreground:
            self.controller.send_client_command(
                "maya-2", "open_scene", {"path": "scene.ma"}, 120.0
            )

        self.assertEqual(client.commands[1][1], "open_scene")
        self.assertFalse(client.commands[1][2]["focus_application"])
        allow_foreground.assert_not_called()

        self.controller._dcc_preferences = lambda _application: {
            "focus_after_open": True,
            "focus_after_save": False,
        }
        with patch.object(
            self.controller, "_allow_client_foreground"
        ) as allow_foreground:
            self.controller.send_client_command(
                "maya-2", "open_scene", {"path": "scene.ma"}, 120.0
            )

        self.assertEqual(client.commands[2][1], "focus_application")
        self.assertEqual(client.commands[3][1], "open_scene")
        self.assertFalse(client.commands[3][2]["focus_application"])
        allow_foreground.assert_called_once_with(2)

        with patch.object(
            self.controller, "_allow_client_foreground"
        ) as allow_foreground:
            self.controller.send_client_command(
                "maya-2", "prepare_checkin", {"path": "scene.ma"}, 120.0
            )

        self.assertFalse(client.commands[4][2]["focus_application"])
        allow_foreground.assert_not_called()

    def test_client_menu_loads_maya_version_and_current_scene(self):
        class ClientStub:
            connected = True

            def __init__(self):
                self.commands = []

            def send_command(self, target, action, payload, timeout):
                request_id = f"request-{len(self.commands) + 1}"
                self.commands.append((target, action, payload, timeout))
                return request_id

            @staticmethod
            def stop(wait=True):
                return None

            @staticmethod
            def shutdown_server():
                return None

        client = ClientStub()
        self.controller._client = client
        self.controller.clients.replace([{
            "clientId": "maya-23328",
            "applicationType": "maya",
            "processId": 23328,
            "capabilities": ["get_application_info", "get_current_scene"],
            "capabilityText": "get_application_info, get_current_scene",
            "applicationVersion": "",
            "sceneName": "",
            "selected": True,
        }])
        self.controller._selected_client = "maya-23328"

        self.controller.refresh_client_details()

        self.assertEqual(
            [command[1] for command in client.commands],
            ["get_application_info", "get_current_scene"],
        )
        self.controller._handle_response({
            "type": "result", "request_id": "request-1", "success": True,
            "payload": {"version": "2026"},
        })
        self.controller._handle_response({
            "type": "result", "request_id": "request-2", "success": True,
            "payload": {"path": "D:/work/scenes/asset_model_v003.ma"},
        })

        action = next(
            item for item in self.controller.clientMenuActions
            if item.get("command") == "dcc_client:maya-23328"
        )
        self.assertEqual(action["title"], "Maya 2026")
        self.assertEqual(action["status"], "asset_model_v003.ma · PID 23328")
        self.assertNotIn("maya-23328", action["status"])
        self.assertEqual(
            self.controller.selectedClientLabel,
            "Maya 2026 · asset_model_v003.ma · PID 23328",
        )

        self.controller.refresh_client_details()
        self.assertEqual(
            [command[1] for command in client.commands],
            ["get_application_info", "get_current_scene", "get_current_scene"],
        )

        self.controller._handle_response({
            "type": "result", "request_id": "request-3", "success": True,
            "payload": {"path": ""},
        })
        self.assertEqual(
            next(
                item for item in self.controller.clientMenuActions
                if item.get("command") == "dcc_client:maya-23328"
            )["status"],
            "Untitled · PID 23328",
        )

    def test_custom_script_notification_identifies_what_ran(self):
        notifications = []
        self.controller.clientActionReported.connect(
            lambda *values: notifications.append(values)
        )

        self.controller._handle_client_event({
            "client_id": "maya-37260",
            "action": "custom_script",
            "status": "completed",
            "payload": {
                "path": "tools/runners/textures_checkin_runner",
                "project": "niki_friends",
            },
        })

        self.assertEqual(notifications[0][0], "complete")
        self.assertEqual(notifications[0][1], "Custom script completed")
        self.assertIn(
            "Script: tools/runners/textures_checkin_runner",
            notifications[0][2],
        )
        self.assertIn("Project: niki_friends", notifications[0][2])
        self.assertIn("Client: maya-37260", notifications[0][2])


if __name__ == "__main__":
    unittest.main()

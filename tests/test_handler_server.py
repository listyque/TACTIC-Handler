from __future__ import annotations

import queue
import tempfile
import threading
import time
import unittest
from pathlib import Path

from handler_server.client import ThinClient
from handler_server.demo_adapter import DemoDocumentAdapter
from handler_server.demo_maya_adapter import DemoMayaAdapter
from handler_server.server import HandlerServer
from handler_server.protocol import ProtocolError, encode_message, message
from handler_server.registry import CommandRegistry


class HandlerServerTests(unittest.TestCase):
    def setUp(self):
        self.token = "test-session-token"
        self.server = HandlerServer(token=self.token)
        self.port = self.server.start()
        self.events = queue.Queue()
        operator_registry = CommandRegistry()
        operator_registry.register(
            "show_handler_window", lambda _payload: {"accepted": True}
        )
        self.operator = ThinClient(
            "127.0.0.1", self.port, self.token, "operator",
            registry=operator_registry, client_id="test-operator",
            on_event=self.events.put,
        )
        adapter = DemoDocumentAdapter()
        self.demo_events = queue.Queue()
        self.demo = ThinClient(
            "127.0.0.1", self.port, self.token, "demo",
            registry=adapter.registry(), client_id="test-demo",
            on_event=self.demo_events.put,
        )
        self.operator.start()
        self.demo.start()
        self.assertTrue(self.operator.wait_connected(3.0))
        self.assertTrue(self.demo.wait_connected(3.0))
        self._wait_for_client("test-demo")

    def tearDown(self):
        self.operator.stop()
        self.demo.stop()
        self.server.stop()

    def _wait_for_client(self, client_id, timeout=3.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if any(
                client["client_id"] == client_id
                for client in self.server.clients
            ):
                return
            time.sleep(0.02)
        self.fail(f"Client did not connect: {client_id}")

    def _response(self, request_id, timeout=3.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                event = self.events.get(timeout=0.1)
            except queue.Empty:
                continue
            if event.get("request_id") == request_id and event["type"] in {
                "result", "error",
            }:
                return event
        self.fail(f"No response for request: {request_id}")

    def test_ping_and_application_info(self):
        request_id = self.operator.send_command(
            "test-demo", "ping", {"value": 7}, timeout=2
        )
        response = self._response(request_id)
        self.assertTrue(response["success"])
        self.assertEqual(response["payload"]["echo"], {"value": 7})

        request_id = self.operator.send_command(
            "test-demo", "get_application_info", {}, timeout=2
        )
        response = self._response(request_id)
        self.assertEqual(
            response["payload"]["application"], "thin-client-demo"
        )

    def test_dcc_commands_are_executed_serially(self):
        lock = threading.Lock()
        state = {"active": 0, "peak": 0}

        def serialized(payload):
            with lock:
                state["active"] += 1
                state["peak"] = max(state["peak"], state["active"])
            try:
                time.sleep(0.08)
                return {"value": payload.get("value")}
            finally:
                with lock:
                    state["active"] -= 1

        self.demo.registry.register("serialized", serialized)
        first = self.operator.send_command(
            "test-demo", "serialized", {"value": 1}, timeout=2
        )
        second = self.operator.send_command(
            "test-demo", "serialized", {"value": 2}, timeout=2
        )
        self.assertEqual(1, self._response(first)["payload"]["value"])
        self.assertEqual(2, self._response(second)["payload"]["value"])
        self.assertEqual(1, state["peak"])

    def test_connected_client_refreshes_capabilities_without_reconnecting(self):
        self.demo.registry.register(
            "added_after_start", lambda _payload: {"updated": True}
        )

        self.demo.refresh_capabilities()

        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            record = next(
                (
                    item for item in self.server.clients
                    if item["client_id"] == "test-demo"
                ),
                {},
            )
            if "added_after_start" in record.get("capabilities", []):
                break
            time.sleep(0.02)
        else:
            self.fail("Updated capabilities were not advertised")

        response = self.operator.request(
            "test-demo", "added_after_start", {}, timeout=2
        )
        self.assertTrue(response["updated"])

    def test_open_save_and_current_file(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.txt"
            target = Path(directory) / "saved.txt"
            source.write_text("source", encoding="utf-8")
            request_id = self.operator.send_command(
                "test-demo", "open_file", {"path": str(source)}, timeout=2
            )
            self.assertTrue(self._response(request_id)["success"])
            request_id = self.operator.send_command(
                "test-demo", "save_current_file",
                {"path": str(target), "content": "saved"}, timeout=2,
            )
            self.assertTrue(self._response(request_id)["success"])
            self.assertEqual(target.read_text(encoding="utf-8"), "saved")
            request_id = self.operator.send_command(
                "test-demo", "get_current_file", {}, timeout=2
            )
            response = self._response(request_id)
            self.assertEqual(Path(response["payload"]["path"]), target)

    def test_error_timeout_and_reconnect(self):
        request_id = self.operator.send_command(
            "test-demo", "fail", {"message": "expected"}, timeout=2
        )
        response = self._response(request_id)
        self.assertEqual(response["type"], "error")
        self.assertIn("expected", response["message"])

        request_id = self.operator.send_command(
            "test-demo", "sleep", {"seconds": 0.5}, timeout=0.1
        )
        response = self._response(request_id)
        self.assertEqual(response["code"], "timeout")

        self.operator.disconnect_client("test-demo")
        deadline = time.monotonic() + 4.0
        disconnected = False
        while time.monotonic() < deadline:
            try:
                event = self.events.get(timeout=0.05)
                disconnected = disconnected or (
                    event.get("type") == "client_disconnected"
                    and event.get("client_id") == "test-demo"
                )
            except queue.Empty:
                pass
            clients = [client["client_id"] for client in self.server.clients]
            if disconnected and "test-demo" in clients and self.demo.connected:
                return
        self.fail("Demo client did not reconnect")

    def test_protocol_limits_and_bad_token(self):
        with self.assertRaises(ProtocolError):
            encode_message(message("heartbeat", value="x" * (1024 * 1024)))
        with self.assertRaisesRegex(ProtocolError, "Capabilities must be"):
            message("capabilities", capabilities="not-a-list")
        events = queue.Queue()
        bad_client = ThinClient(
            "127.0.0.1", self.port, "wrong-token", "demo",
            client_id="bad-client", reconnect=False, on_event=events.put,
        )
        bad_client.start()
        self.assertFalse(bad_client.wait_connected(0.5))
        bad_client.stop()
        self.assertNotIn(
            "bad-client", [client["client_id"] for client in self.server.clients]
        )

    def test_client_stop_is_not_reported_as_connection_error(self):
        events = queue.Queue()
        client = ThinClient(
            "127.0.0.1", self.port, self.token, "demo",
            client_id="stopped-client", reconnect=False,
            on_event=events.put,
        )
        client.start()
        self.assertTrue(client.wait_connected(3.0))
        client.stop()
        captured = []
        while not events.empty():
            captured.append(events.get_nowait())
        self.assertFalse(any(
            event.get("type") == "error"
            and event.get("code") == "connection_error"
            for event in captured
        ))

    def test_demo_maya_exposes_only_registered_actions(self):
        adapter = DemoMayaAdapter()
        registry = adapter.registry()
        self.assertIn("save_current_scene", registry.capabilities())
        self.assertIn("prepare_checkin", registry.capabilities())
        self.assertIn("prepare_scene", registry.capabilities())
        self.assertNotIn("exec", registry.capabilities())
        saved = registry.execute("save_current_scene", {
            "project_code": "demo", "search_key": "demo/asset?code=CAR",
            "process": "model", "context": "model/main",
        })
        self.assertTrue(Path(saved["path"]).is_file())
        self.assertTrue(saved["prepared"]["ready"])
        self.assertEqual(saved["target"]["project_code"], "demo")
        self.assertEqual(saved["target"]["process"], "model")

        prepared = registry.execute("prepare_checkin", {
            "project_code": "demo", "search_key": "demo/asset?code=CAR",
            "process": "model", "context": "model/main",
            "generate_previews": True,
        })
        self.assertTrue(Path(prepared["files"][0]["path"]).is_file())
        self.assertEqual(prepared["files"][0]["role"], "main")
        self.assertTrue(Path(prepared["previews"][0]["path"]).is_file())
        self.assertEqual(prepared["previews"][0]["type"], "playblast")

    def test_dcc_client_event_reaches_operator(self):
        self.demo.publish_event(
            "save_current_scene", "completed", {"path": "demo_scene.ma"}
        )
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            try:
                event = self.events.get(timeout=0.1)
            except queue.Empty:
                continue
            if event.get("type") != "client_event":
                continue
            self.assertEqual(event["client_id"], "test-demo")
            self.assertEqual(event["action"], "save_current_scene")
            self.assertEqual(event["payload"]["path"], "demo_scene.ma")
            return
        self.fail("Operator did not receive the DCC client event")

    def test_dcc_client_can_restore_operator_window(self):
        request_id = self.demo.send_command(
            "@operator", "show_handler_window", {}, timeout=2
        )
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            try:
                event = self.demo_events.get(timeout=0.1)
            except queue.Empty:
                continue
            if event.get("request_id") != request_id:
                continue
            self.assertEqual(event["type"], "result")
            self.assertTrue(event["payload"]["accepted"])
            return
        self.fail("DCC client did not receive the window restore result")

    def test_operator_can_request_server_shutdown(self):
        self.operator.shutdown_server()
        self.assertTrue(self.server.shutdown_requested.wait(2.0))


if __name__ == "__main__":
    unittest.main()

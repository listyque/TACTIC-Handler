from __future__ import annotations

import time
import unittest
from pathlib import Path

from PySide6.QtCore import QCoreApplication

from modern_ui.handler_server_controller import HandlerServerController


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
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def setUp(self):
        self.debug_log = DebugLogStub()
        self.controller = HandlerServerController(
            Path(__file__).resolve().parents[1], self.debug_log
        )

    def tearDown(self):
        self.controller.shutdown()

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


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import os
import tempfile
import time
import unittest

from handler_server.client import ThinClient
from handler_server.discovery import (
    available_sessions, publish_session, remove_session,
)
from handler_server.server import HandlerServer


class HandlerServerDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.previous_directory = os.environ.get(
            "TACTIC_HANDLER_DISCOVERY_DIR"
        )
        os.environ["TACTIC_HANDLER_DISCOVERY_DIR"] = self.directory.name
        self.server = HandlerServer(token="discovery-test-token")
        self.server.start()
        self.discovery_path = publish_session(
            self.server.host, self.server.port, self.server.token
        )
        self.clients = []

    def tearDown(self):
        for client in self.clients:
            client.stop()
        self.server.stop()
        remove_session(self.discovery_path)
        if self.previous_directory is None:
            os.environ.pop("TACTIC_HANDLER_DISCOVERY_DIR", None)
        else:
            os.environ["TACTIC_HANDLER_DISCOVERY_DIR"] = (
                self.previous_directory
            )
        self.directory.cleanup()

    def _client(self):
        client = ThinClient.local("maya")
        self.clients.append(client)
        client.start()
        self.assertTrue(client.wait_connected(3.0))
        return client

    def test_clients_discover_session_without_connection_parameters(self):
        first = self._client()
        second = self._client()
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline and len(self.server.clients) < 2:
            time.sleep(0.02)
        connected = {record["client_id"] for record in self.server.clients}
        self.assertIn(first.client_id, connected)
        self.assertIn(second.client_id, connected)
        self.assertNotEqual(first.client_id, second.client_id)
        self.assertEqual(first.port, self.server.port)

    def test_discovery_record_contains_current_local_server(self):
        records = available_sessions()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["host"], "127.0.0.1")
        self.assertEqual(records[0]["port"], self.server.port)
        self.assertEqual(records[0]["token"], self.server.token)


if __name__ == "__main__":
    unittest.main()

"""A real dropped-in DCC plugin can be disabled without importing its adapter."""

import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from tactic_handler_dcc import connectors
from handler_server.client import ThinClient
from handler_server.server import HandlerServer


class DccPluginTests(unittest.TestCase):
    def tearDown(self):
        connectors.configure_plugins()
        sys.modules.pop("tactic_handler_dcc.connectors.testdcc", None)
        sys.modules.pop("tactic_handler_dcc.connectors.brokendcc", None)

    def test_drop_in_plugin_metadata_toggle_and_import_isolation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "testdcc.py").write_text(
                "DCC_MANIFEST = {'application':'testdcc', 'title':'Test DCC', "
                "'ui':{'configuration':{'title':'Test DCC'}}}\n", encoding="utf-8")
            (path / "testdcc.plugin.json").write_text(json.dumps({"title": "Test DCC"}))
            with patch.object(connectors, "__path__", [directory]):
                importlib.invalidate_caches()
                connectors.configure_plugins(["testdcc"])
                self.assertEqual(connectors.plugin_catalog()[0]["title"], "Test DCC")
                self.assertEqual(connectors.dcc_manifests(), ())
                self.assertNotIn("tactic_handler_dcc.connectors.testdcc", sys.modules)
                self.assertEqual(connectors.disabled_applications(), ("testdcc",))
                connectors.configure_plugins()
                self.assertEqual(connectors.dcc_configuration_pages()[0]["id"], "dcc.testdcc")
                self.assertEqual(connectors.disabled_applications(), ())

    def test_broken_plugin_reports_error_without_removing_healthy_plugins(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "brokendcc.py").write_text("raise RuntimeError('broken adapter')\n")
            original = list(connectors.__path__)
            with patch.object(connectors, "__path__", [directory, *original]), \
                    self.assertLogs(connectors.__name__, level="ERROR"):
                manifests = connectors.dcc_manifests()
                self.assertTrue(any(row["application"] == "maya" for row in manifests))
                row = next(row for row in connectors.plugin_catalog() if row["id"] == "brokendcc")
                self.assertIn("broken adapter", row["error"])

    def test_disabled_native_client_is_rejected_but_handler_operator_connects(self):
        server = HandlerServer(token="test-disabled-dcc", disabled_applications=["maya"])
        server.start()
        maya = ThinClient(server.host, server.port, server.token, "maya", reconnect=False)
        operator = ThinClient(server.host, server.port, server.token, "tactic_handler", reconnect=False)
        try:
            maya.start()
            maya._thread.join(timeout=3)
            self.assertFalse(maya.connected)
            self.assertIn("disabled", maya._last_connection_error)
            operator.start()
            self.assertTrue(operator.wait_connected(3))
            self.assertEqual([client["application_type"] for client in server.clients], ["tactic_handler"])
        finally:
            maya.stop()
            operator.stop()
            server.stop()


if __name__ == "__main__":
    unittest.main()

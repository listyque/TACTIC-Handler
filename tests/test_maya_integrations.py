"""Real filesystem boundaries for the Configuration-owned Maya integration."""

import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import Mock, patch

from tactic_handler_dcc import maya_integration as integration
from handler_server.client import ThinClient
from handler_server.discovery import current_session, publish_session, remove_session
from handler_server.server import HandlerServer


class MayaIntegrationFilesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="maya integration Кириллица ")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.profile = self.directory / "maya" / "2023"
        self.root = self.directory / "TH folder"
        self.root.mkdir()
        (self.root / "launch.pyw").touch()

    def test_install_update_remove_preserve_existing_startup_and_legacy_shelves(self):
        startup = self.profile / "scripts/userSetup.py"
        startup.parent.mkdir(parents=True)
        startup.write_bytes(b"# legacy startup\r\n")
        legacy = self.profile / "prefs/shelves/shelf_Niki_And_Friends.mel"
        legacy.parent.mkdir(parents=True)
        legacy.write_bytes(b"legacy shelf")
        for _ in range(2):
            integration.install(self.profile, self.root)
            state = integration.integration_state(self.profile)
            self.assertEqual(state["status"], "Installed")
            self.assertEqual(state["handlerRoot"], str(self.root.resolve()))
        receipt = integration._receipt(self.profile)
        module = self.profile / "modules/TACTIC_Stream.mod"
        relative = module.read_text().split("1.0 ", 1)[1].strip()
        self.assertEqual((module.parent / relative).resolve(), self.profile / "tactic_stream_payload")
        for name in receipt["files"]:
            self.assertTrue((self.profile / name).is_file())
        integration.remove(self.profile)
        self.assertEqual(integration.integration_state(self.profile)["status"], "Not installed")
        self.assertEqual(startup.read_bytes(), b"# legacy startup\r\n")
        self.assertEqual(legacy.read_bytes(), b"legacy shelf")

    def test_modified_or_foreign_integration_is_never_overwritten_or_removed(self):
        integration.install(self.profile, self.root)
        script = self.profile / "tactic_stream_payload/scripts/userSetup.py"
        script.write_text("user customization", encoding="utf-8")
        self.assertEqual(integration.integration_state(self.profile)["status"], "Modified files")
        for action in (lambda: integration.install(self.profile, self.root),
                       lambda: integration.remove(self.profile)):
            with self.assertRaisesRegex(ValueError, "[Mm]odified"):
                action()
        self.assertEqual(script.read_text(), "user customization")

    def test_receipt_cannot_redirect_deletion_outside_owned_files(self):
        integration.install(self.profile, self.root)
        receipt_path = self.profile / "tactic_stream_payload/integration.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["files"]["../keep.txt"] = "attacker"
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "inventory"):
            integration.remove(self.profile)

    def test_maya_shelf_serialization_is_owned_but_added_mel_logic_is_preserved(self):
        integration.install(self.profile, self.root)
        shelf = self.profile / "prefs/shelves/shelf_TACTIC_Stream.mel"
        generated = shelf.read_text(encoding="utf-8")
        shelf.write_text(generated.replace('shelfButton ', 'global string $gBuffStr;\n shelfButton -width 35 '),
                         encoding="utf-8")
        self.assertEqual(integration.integration_state(self.profile)["status"], "Installed")
        shelf.write_text(shelf.read_text().replace("\n}", '\n print("custom");\n}'), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Modified"):
            integration.remove(self.profile)
        self.assertIn('print("custom")', shelf.read_text())

    def test_detects_installed_running_profiles_and_existing_integrations(self):
        integration.install(self.profile, self.root)
        (self.profile.parent / "2024").mkdir()
        rows = integration.discover(
            app_directory=self.profile.parent,
            executables=[Path("C:/Autodesk/Maya2022/bin/maya.exe")],
            processes=[{"ExecutablePath": "E:/Custom/Maya2023/bin/maya.exe", "ProcessId": 777}],
        )
        by_version = {row["version"]: row for row in rows}
        self.assertEqual(set(by_version), {"2022", "2023", "2024"})
        self.assertEqual(by_version["2023"]["pids"], [777])
        self.assertEqual(by_version["2023"]["status"], "Installed")

    def test_rejects_python2_profile_and_foreign_shelf(self):
        with self.assertRaisesRegex(ValueError, "Python 3"):
            integration.install(self.profile.parent / "2020", self.root)
        shelf = self.profile / "prefs/shelves/shelf_TACTIC_Stream.mel"
        shelf.parent.mkdir(parents=True)
        shelf.write_text("foreign", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            integration.install(self.profile, self.root)

    def test_custom_registered_location_keeps_its_version_for_running_processes(self):
        rows = integration.discover(
            app_directory=self.profile.parent,
            executables=[{"version": "2023", "executable": "D:/DCC/Maya/bin/maya.exe"}],
            processes=[{"ExecutablePath": "D:/DCC/Maya/bin/maya.exe", "ProcessId": 777}],
        )
        self.assertEqual(rows[0]["version"], "2023")
        self.assertEqual(rows[0]["pids"], [777])

    def test_partial_install_rolls_back_existing_bytes(self):
        integration.install(self.profile, self.root)
        paths = [self.profile / name for name in integration._receipt(self.profile)["files"]]
        before = {path: path.read_bytes() for path in paths}
        original = integration.os.replace
        calls = []

        def fail_once(source, destination):
            calls.append(destination)
            if len(calls) == 2:
                raise OSError("disk full")
            original(source, destination)

        with patch.object(integration.os, "replace", side_effect=fail_once):
            with self.assertRaisesRegex(OSError, "disk full"):
                integration.install(self.profile, self.root)
        self.assertEqual(before, {path: path.read_bytes() for path in paths})

    def test_autostart_does_not_launch_handler_or_change_foreign_modules(self):
        integration.install(self.profile, self.root)
        script = self.profile / "tactic_stream_payload/scripts/tactic_stream_maya.py"
        spec = importlib.util.spec_from_file_location("test_maya_bootstrap", script)
        bootstrap = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bootstrap)
        native = ModuleType("maya")
        native.cmds = Mock()
        foreign = ModuleType("custom_scripts")
        foreign.__file__ = str(self.directory / "other/custom_scripts/__init__.py")
        with patch.dict(sys.modules, {"maya": native, "custom_scripts": foreign}), \
                patch.object(bootstrap.subprocess, "Popen") as launch:
            self.assertIsNone(bootstrap.connect())
            launch.assert_not_called()
            self.assertIs(sys.modules["custom_scripts"], foreign)
            self.assertIn("restart Maya", native.cmds.warning.call_args.args[0])


class PinnedHandlerDiscoveryTests(unittest.TestCase):
    def test_pins_real_transport_to_installation_and_keeps_old_records_valid(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.dict(os.environ, {"TACTIC_HANDLER_DISCOVERY_DIR": directory}):
            selected = HandlerServer(token="selected-local-test")
            other = HandlerServer(token="other-local-test")
            selected.start()
            other.start()
            root = Path(directory) / "TH selected"
            path = publish_session(selected.host, selected.port, selected.token, handler_root=root)
            self.addCleanup(remove_session, path)
            other_path = Path(directory) / "session-other.json"
            record = json.loads(path.read_text(encoding="utf-8"))
            record.update(port=other.port, token=other.token, handler_root=str(Path(directory) / "other"),
                          started_at=record["started_at"] + 100)
            other_path.write_text(json.dumps(record), encoding="utf-8")
            client = ThinClient.local("maya", handler_root=root)
            try:
                client.start()
                self.assertTrue(client.wait_connected(3))
                self.assertEqual(client.port, selected.port)
                self.assertEqual(current_session()["port"], other.port)
                self.assertIsNone(current_session(handler_root=Path(directory) / "absent"))
                record.pop("handler_root")
                other_path.write_text(json.dumps(record), encoding="utf-8")
                self.assertEqual(current_session()["port"], other.port)
                self.assertEqual(current_session(handler_root=root)["port"], selected.port)
            finally:
                client.stop()
                selected.stop()
                other.stop()


if __name__ == "__main__":
    unittest.main()

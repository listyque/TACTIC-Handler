from __future__ import annotations

import json
import os
from pathlib import Path
import unittest
from unittest import mock

import launch


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "tests" / "contracts" / "release_acceptance.json"


class ReleaseReadinessContractTests(unittest.TestCase):
    def test_common_launcher_defaults_to_modern_and_keeps_explicit_legacy(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            selected, forwarded = launch._selected_ui(["launch.py"])
        self.assertEqual(selected, "qml")
        self.assertEqual(forwarded, ["launch.py"])
        selected, forwarded = launch._selected_ui(
            ["launch.py", "--ui", "legacy", "--example"]
        )
        self.assertEqual(selected, "legacy")
        self.assertEqual(forwarded, ["launch.py", "--example"])

    def test_automated_gate_commands_resolve_inside_repository(self):
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        identifiers = [item["id"] for item in contract["automated"]]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertIn("isolated-regression", identifiers)
        self.assertIn("legacy-smoke", identifiers)
        self.assertIn("foreign-cwd-entrypoints", identifiers)
        for check in contract["automated"]:
            command = check["command"]
            self.assertIsInstance(command, list)
            self.assertTrue(command)
            target = command[0]
            if target == "-m":
                continue
            self.assertTrue((ROOT / target).is_file(), target)

    def test_environment_dependent_checks_remain_explicitly_manual(self):
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        manual = {item["id"]: item for item in contract["manual"]}
        expected = {
            "live-session-navigation",
            "live-mutations",
            "repository-checkin",
            "windows-lifecycle",
            "maya-dcc",
            "visual-acceptance",
        }
        self.assertEqual(set(manual), expected)
        self.assertTrue(all(item["required"] for item in manual.values()))
        self.assertTrue(all(item["environment"] for item in manual.values()))

    def test_release_documentation_and_runners_are_present(self):
        for path in (
            ROOT / "docs" / "release_readiness.md",
            ROOT / "tests" / "run_release_gate.py",
            ROOT / "tests" / "run_entrypoint_smoke.py",
        ):
            self.assertTrue(path.is_file(), str(path))


if __name__ == "__main__":
    unittest.main()

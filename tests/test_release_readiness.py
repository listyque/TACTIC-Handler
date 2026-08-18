from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import launch
from tests import run_release_gate


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
            "live-server-procedures",
            "live-mutations",
            "repository-checkin",
            "windows-lifecycle",
            "clean-environment-install",
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
            ROOT / "tests" / "run_clean_environment_smoke.py",
            ROOT / "tests" / "run_live_server_procedure_smoke.py",
            ROOT / "tests" / "record_release_acceptance.py",
        ):
            self.assertTrue(path.is_file(), str(path))

    def test_runtime_dependencies_are_pinned_and_direct(self):
        requirements = (ROOT / "requirements-modern.txt").read_text(
            encoding="utf-8"
        )
        dependencies = [
            line.strip() for line in requirements.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertEqual(["PySide6==6.11.1"], dependencies)

    def test_manual_results_require_status_identity_time_and_evidence(self):
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        complete = {
            "schemaVersion": 1,
            "checks": {
                item["id"]: {
                    "status": "passed",
                    "tester": "release tester",
                    "testedAt": "2026-08-11T12:00:00+00:00",
                    "evidence": "recorded scenario output",
                }
                for item in contract["manual"] if item.get("required")
            },
        }
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "acceptance.json"
            path.write_text(json.dumps(complete), encoding="utf-8")
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                self.assertEqual(0, run_release_gate._manual_check(contract, path))
            complete["checks"]["repository-checkin"]["evidence"] = ""
            path.write_text(json.dumps(complete), encoding="utf-8")
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                self.assertEqual(1, run_release_gate._manual_check(contract, path))


if __name__ == "__main__":
    unittest.main()

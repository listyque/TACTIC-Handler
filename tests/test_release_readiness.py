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
from tests import run_isolated_suite, run_release_gate


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "tests" / "contracts" / "release_acceptance.json"


class ReleaseReadinessContractTests(unittest.TestCase):
    def test_common_launcher_has_only_the_application_entrypoint(self):
        source = (ROOT / "launch.py").read_text(encoding="utf-8")
        self.assertIn("from thlib.ui.application import main as start", source)
        self.assertNotIn("main_standalone", source)
        self.assertNotIn("TACTIC_HANDLER_UI", source)

    def test_automated_gate_commands_resolve_inside_repository(self):
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        identifiers = [item["id"] for item in contract["automated"]]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertIn("python-lint", identifiers)
        self.assertIn("qml-lint", identifiers)
        self.assertIn("isolated-regression", identifiers)
        self.assertNotIn("legacy-smoke", identifiers)
        self.assertIn("foreign-cwd-entrypoints", identifiers)
        for check in contract["automated"]:
            command = check["command"]
            self.assertIsInstance(command, list)
            self.assertTrue(command)
            target = command[0]
            if target == "-m":
                continue
            self.assertTrue((ROOT / target).is_file(), target)

        isolated = next(
            item for item in contract["automated"]
            if item["id"] == "isolated-regression"
        )
        self.assertEqual(
            ["tests/run_isolated_suite.py", "--exclude", "test_qml_lint"],
            isolated["command"],
        )

    def test_isolated_runner_can_exclude_an_explicit_module(self):
        self.assertEqual(
            [],
            run_isolated_suite.test_modules(
                "test_qml_lint.py", excluded=["tests.test_qml_lint"]
            ),
        )

    def test_activity_feed_loading_does_not_rediscover_imported_test_cases(self):
        from tests import test_activity_feed_loading

        suite = unittest.defaultTestLoader.loadTestsFromModule(
            test_activity_feed_loading
        )
        modules = {
            test.__class__.__module__
            for group in suite
            for test in group
        }
        self.assertEqual({"tests.test_activity_feed_loading"}, modules)

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
        requirements = (ROOT / "requirements.txt").read_text(
            encoding="utf-8"
        )
        dependencies = [
            line.strip() for line in requirements.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertEqual(["PySide6==6.11.1"], dependencies)

    def test_development_linter_is_pinned(self):
        requirements = (ROOT / "requirements-dev.txt").read_text(
            encoding="utf-8"
        )
        dependencies = [
            line.strip() for line in requirements.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertEqual(["-r requirements.txt", "ruff==0.16.5"], dependencies)

    def test_manual_results_require_status_identity_time_and_evidence(self):
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        complete = {
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

from __future__ import annotations

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from thlib.ui.workspace_models.windows import FloatingWindowModel
from tests.support.async_scenarios import MemorySettings
from tests.support.vertical_workflows import (
    ROOT, load_vertical_manifest, missing_modules,
)


class VerticalWorkflowManifestTests(unittest.TestCase):
    def setUp(self):
        self.payload = load_vertical_manifest()
        self.manifest = self.payload["verticals"]

    def test_every_vertical_has_contract_controller_qml_and_live_layers(self):
        self.assertEqual(len(self.manifest), 6)
        for name, record in self.manifest.items():
            with self.subTest(vertical=name):
                self.assertTrue(record["modules"])
                self.assertTrue(record["qml"])
                self.assertTrue(record["windows"])
                self.assertTrue(record["liveChecks"])

    def test_shared_contract_and_qml_smoke_layers_are_always_run(self):
        self.assertEqual(self.payload["sharedModules"], [
            "tests.test_contracts",
            "tests.test_qml_smoke_harness",
            "tests.test_vertical_workflows",
        ])

    def test_all_referenced_test_modules_and_qml_components_exist(self):
        self.assertEqual(missing_modules(), [])
        qml_root = ROOT / "thlib" / "ui" / "qml"
        for name, record in self.manifest.items():
            for component in record["qml"]:
                with self.subTest(vertical=name, component=component):
                    self.assertTrue((qml_root / component).is_file())

    def test_every_standalone_window_uses_the_single_window_registry(self):
        model = FloatingWindowModel(MemorySettings())
        registered = {window.window_id for window in model._windows}
        for name, record in self.manifest.items():
            with self.subTest(vertical=name):
                self.assertTrue(set(record["windows"]).issubset(registered))

    def test_live_checks_are_declared_once_per_vertical(self):
        for name, record in self.manifest.items():
            checks = list(record["liveChecks"])
            with self.subTest(vertical=name):
                self.assertEqual(len(checks), len(set(checks)))
                self.assertTrue(all(str(check).strip() for check in checks))

    def test_live_runner_rejects_implicit_or_production_targets(self):
        from tests.run_live_vertical_checks import _require_live_target

        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "TACTIC_RUN_LIVE_VERTICALS"):
                _require_live_target()
        with patch.dict("os.environ", {
            "TACTIC_RUN_LIVE_VERTICALS": "1",
            "TACTIC_TEST_PROJECT_CODE": "production",
        }, clear=True):
            with self.assertRaises(Exception):
                _require_live_target()

    def test_live_runner_accepts_only_explicit_read_only_test_target(self):
        from tests.run_live_vertical_checks import _require_live_target

        with patch.dict("os.environ", {
            "TACTIC_RUN_LIVE_VERTICALS": "1",
            "TACTIC_TEST_PROJECT_CODE": "th_test_verticals",
            "TACTIC_TEST_SEARCH_TYPE": "th_test_verticals/asset",
        }, clear=True):
            self.assertEqual(
                _require_live_target(),
                ("th_test_verticals", "th_test_verticals/asset"),
            )

    def test_live_navigation_check_consumes_native_search_page_shape(self):
        from tests import run_live_vertical_checks as live

        tactic = SimpleNamespace(
            get_sobjects=lambda *_args, **_kwargs: (
                {"skey://demo/asset?code=A1": object()},
                {"total_sobjects_count": 7},
            ),
        )
        with (
            patch.object(
                live, "_require_live_target",
                return_value=("th_test_verticals", "demo/asset"),
            ),
            patch.object(live, "_bootstrap", return_value=(tactic, object())),
        ):
            result = live.run("navigation_search")

        self.assertEqual(result["records"], 1)
        self.assertEqual(result["total"], 7)


if __name__ == "__main__":
    unittest.main()

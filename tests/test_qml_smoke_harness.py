from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class QmlSmokeHarnessTests(unittest.TestCase):
    def test_all_registered_windows_load_reopen_and_shutdown_offline(self):
        environment = os.environ.copy()
        environment.update({
            "QT_QPA_PLATFORM": "offscreen",
            "QSG_RHI_BACKEND": "software",
            "TACTIC_QML_SMOKE_WINDOWS": "1",
            "TACTIC_QML_SMOKE_OFFLINE": "1",
        })
        with tempfile.TemporaryDirectory(prefix="tactic-qml-smoke-") as temp:
            environment["TACTIC_QML_TEST_SETTINGS_DIR"] = temp
            completed = subprocess.run(
                [sys.executable, str(ROOT / "main_qml.py")],
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )

        diagnostic = "\n".join((completed.stdout, completed.stderr))
        self.assertEqual(completed.returncode, 0, diagnostic)
        self.assertNotIn("QML startup failed", diagnostic)
        self.assertNotIn("QML window smoke warnings", diagnostic)
        self.assertNotIn("Binding loop detected", diagnostic)
        self.assertNotIn("Required property", diagnostic)
        self.assertNotIn("ReferenceError", diagnostic)

    def test_smoke_mode_isolated_from_network_and_user_settings(self):
        source = (ROOT / "main_qml.py").read_text(encoding="utf-8")
        self.assertIn("TACTIC_QML_SMOKE_OFFLINE", source)
        self.assertIn("TACTIC_QML_TEST_SETTINGS_DIR", source)
        guarded_startup = source[source.index("if not smoke_offline:"):]
        self.assertIn("controller.bootstrap_server", guarded_startup)
        self.assertIn("handler_server_controller.start_server", guarded_startup)
        self.assertIn("server_update_service.start", guarded_startup)


if __name__ == "__main__":
    unittest.main()

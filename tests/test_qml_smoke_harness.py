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
            "QT_QUICK_BACKEND": "software",
            "TACTIC_QML_SMOKE_WINDOWS": "1",
            "TACTIC_QML_SMOKE_OFFLINE": "1",
        })
        existing_session_logs = set((ROOT / "log").glob("session_*.jsonl"))
        with tempfile.TemporaryDirectory(prefix="tactic-qml-smoke-") as temp:
            environment["TACTIC_QML_TEST_SETTINGS_DIR"] = temp
            environment["XDG_CACHE_HOME"] = str(Path(temp) / "cache")
            environment["XDG_CONFIG_HOME"] = str(Path(temp) / "config")
            if os.name == "nt":
                environment["LOCALAPPDATA"] = temp
                environment["APPDATA"] = temp
                environment["QT_QPA_FONTDIR"] = str(
                    Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
                )
            completed = subprocess.run(
                [sys.executable, "-m", "thlib.ui.application"],
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            isolated_settings = list(
                (Path(temp) / "settings").rglob("ui_settings.json")
            )
            self.assertTrue(isolated_settings)

        self.assertEqual(
            set((ROOT / "log").glob("session_*.jsonl")),
            existing_session_logs,
            "QML smoke wrote diagnostic files into the production log",
        )

        diagnostic = "\n".join((completed.stdout, completed.stderr))
        self.assertEqual(completed.returncode, 0, diagnostic)
        self.assertNotIn("QML startup failed", diagnostic)
        self.assertNotIn("QML window smoke warnings", diagnostic)
        self.assertNotIn("Cannot find font directory", diagnostic)
        self.assertNotIn("Binding loop detected", diagnostic)
        self.assertNotIn("Required property", diagnostic)
        self.assertNotIn("ReferenceError", diagnostic)
        self.assertNotIn("TypeError", diagnostic)
        self.assertNotIn("delayed function evaluation", diagnostic)
        self.assertNotIn("QQmlVMEMetaObject: Internal error", diagnostic)
        self.assertNotIn(
            "QUnifiedTimer::stopAnimationDriver",
            diagnostic,
        )
        self.assertNotIn(
            "Both point size and pixel size set",
            diagnostic,
        )
        self.assertNotIn(
            "Injection of parameters into signal handlers is deprecated",
            diagnostic,
        )

    def test_smoke_mode_isolated_from_network_and_user_settings(self):
        source = (ROOT / "thlib/ui/application.py").read_text(encoding="utf-8")
        self.assertIn("TACTIC_QML_SMOKE_OFFLINE", source)
        self.assertIn("TACTIC_QML_TEST_SETTINGS_DIR", source)
        self.assertIn(
            "diagnostics_root=settings_path if test_settings_dir else PROJECT_ROOT",
            source,
        )
        guarded_startup = source[source.index("if not smoke_offline:"):]
        self.assertIn("controller.bootstrap_server", guarded_startup)
        self.assertIn("runtime.handler_server.start_server", guarded_startup)
        self.assertIn(
            "runtime.server_updates.sync_authentication", guarded_startup
        )
        self.assertIn("Qt.ConnectionType.SingleShotConnection", guarded_startup)
        self.assertNotIn(
            "frameSwapped.disconnect(start_after_first_frame)", guarded_startup
        )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings

from modern_ui.debug_logging import DebugLogController


class DebugLoggingModeTests(unittest.TestCase):
    def setUp(self):
        self.settings = QSettings("TACTIC-Handler", "modern-qml")
        self.previous_levels = self.settings.value(
            "debugLog/enabledLevels", None
        )
        self.settings.remove("debugLog/enabledLevels")
        self.settings.sync()

    def tearDown(self):
        if self.previous_levels is None:
            self.settings.remove("debugLog/enabledLevels")
        else:
            self.settings.setValue(
                "debugLog/enabledLevels", self.previous_levels
            )
        self.settings.sync()

    def test_default_mode_keeps_only_error_and_critical(self):
        with TemporaryDirectory() as directory:
            controller = DebugLogController(Path(directory))
            controller.log("INFO", "progress detail")
            controller.log("API", "server request")
            controller.log("EXCEPTION", "handled exception")
            controller.log("ERROR", "download failed")
            controller.log("CRITICAL", "database unavailable")

            self.assertEqual(
                [record["level"] for record in controller._live_entries],
                ["ERROR", "CRITICAL"],
            )
            controller.shutdown()
            text_log = controller._text_log.read_text(encoding="utf-8")
            self.assertIn("download failed", text_log)
            self.assertIn("database unavailable", text_log)
            self.assertNotIn("progress detail", text_log)
            self.assertNotIn("server request", text_log)
            self.assertNotIn("handled exception", text_log)

    def test_individual_recording_levels_are_persisted_and_applied(self):
        with TemporaryDirectory() as directory:
            controller = DebugLogController(Path(directory))
            controller.set_recording_levels(["INFO", "WARNING"])
            controller.log("INFO", "progress detail")
            controller.log("WARNING", "slow request")
            controller.log("ERROR", "not selected")

            self.assertEqual(
                controller.recording_levels, ["INFO", "WARNING"]
            )
            self.assertEqual(
                [record["level"] for record in controller._live_entries],
                ["INFO", "WARNING"],
            )
            stored = json.loads(self.settings.value(
                "debugLog/enabledLevels", "[]"
            ))
            self.assertEqual(stored, ["INFO", "WARNING"])
            controller.shutdown()

    def test_all_recording_levels_can_be_enabled_explicitly(self):
        with TemporaryDirectory() as directory:
            controller = DebugLogController(Path(directory))
            controller.set_recording_levels([
                "LOG", "INFO", "WARNING", "MISSING", "EXCEPTION",
                "ERROR", "CRITICAL", "API",
            ])
            controller.log("INFO", "progress detail")

            self.assertEqual(controller._live_entries[-1]["level"], "INFO")
            controller.shutdown()


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

from PySide6.QtCore import QCoreApplication

from tests.qt_application import gui_test_application
from thlib.ui.single_instance import (
    SingleInstanceGuard,
    instance_server_name,
)


class SingleInstanceGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = gui_test_application()

    @staticmethod
    def _name() -> str:
        return f"TacticHandlerTest-{uuid.uuid4().hex}"

    def test_second_owner_is_rejected_and_activates_primary(self):
        name = self._name()
        primary = SingleInstanceGuard(name)
        self.addCleanup(primary.close)
        activations = []
        primary.set_activation_handler(lambda: activations.append("shown"))
        self.assertTrue(primary.start())

        secondary = SingleInstanceGuard(name)
        self.addCleanup(secondary.close)
        self.assertFalse(secondary.start())
        QCoreApplication.processEvents()

        self.assertEqual(activations, ["shown"])
        self.assertTrue(primary.is_primary)
        self.assertFalse(secondary.is_primary)

    def test_early_activation_is_replayed_after_window_is_attached(self):
        name = self._name()
        primary = SingleInstanceGuard(name)
        self.addCleanup(primary.close)
        self.assertTrue(primary.start())
        secondary = SingleInstanceGuard(name)
        self.addCleanup(secondary.close)

        self.assertFalse(secondary.start())
        QCoreApplication.processEvents()
        activations = []
        primary.set_activation_handler(lambda: activations.append("shown"))

        self.assertEqual(activations, ["shown"])

    def test_normal_shutdown_releases_ownership(self):
        name = self._name()
        primary = SingleInstanceGuard(name)
        self.assertTrue(primary.start())
        primary.close()

        replacement = SingleInstanceGuard(name)
        self.addCleanup(replacement.close)
        self.assertTrue(replacement.start())

    def test_separate_process_cannot_acquire_owned_name(self):
        name = self._name()
        primary = SingleInstanceGuard(name)
        self.addCleanup(primary.close)
        activations = []
        primary.set_activation_handler(lambda: activations.append("shown"))
        self.assertTrue(primary.start())
        script = (
            "from PySide6.QtCore import QCoreApplication; "
            "from thlib.ui.single_instance import SingleInstanceGuard; "
            "import sys; app = QCoreApplication([]); "
            "guard = SingleInstanceGuard(sys.argv[1]); "
            "print('primary' if guard.start() else 'secondary', flush=True); "
            "guard.close()"
        )

        completed = subprocess.run(
            [sys.executable, "-c", script, name],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        QCoreApplication.processEvents()

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), "secondary")
        self.assertEqual(activations, ["shown"])

    def test_isolated_test_settings_get_a_deterministic_private_name(self):
        with tempfile.TemporaryDirectory() as directory:
            first = instance_server_name("TacticHandler_Client", directory)
            second = instance_server_name(
                "TacticHandler_Client",
                str(Path(directory) / "."),
            )

        self.assertEqual(first, second)
        self.assertNotEqual(first, "TacticHandler_Client")

    def test_entrypoint_acquires_guard_before_starting_runtime_work(self):
        source = Path("thlib/ui/application.py").read_text(encoding="utf-8")
        guard_at = source.index("single_instance.start()")
        pools_at = source.index("env_inst.start_pools()")
        runtime_at = source.index("build_application_runtime(")

        self.assertLess(guard_at, pools_at)
        self.assertLess(guard_at, runtime_at)


if __name__ == "__main__":
    unittest.main()

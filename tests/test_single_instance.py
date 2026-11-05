from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
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

    def _entrypoint_name(self, profile, *, test_profile="", entrypoint="client"):
        environment = dict(os.environ, QT_QPA_PLATFORM="offscreen",
                           QT_QUICK_BACKEND="software",
                           QT_QPA_FONTDIR=str(Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"),
                           TACTIC_HANDLER_SETTINGS_DIR=str(profile),
                           TACTIC_QML_TEST_SETTINGS_DIR=str(test_profile))
        script = """
import json, sys
from unittest.mock import patch
names = []
class ProbeGuard:
    def __init__(self, name, parent): names.append(name)
    def start(self): return False
if sys.argv[1] in ('setup', 'builder'):
    from thlib.ui import setup_wizard
    with patch('thlib.ui.single_instance.SingleInstanceGuard', ProbeGuard), patch.object(setup_wizard.QMessageBox, 'information'):
        setup_wizard.main(builder=sys.argv[1] == "builder")
else:
    from thlib.ui import application
    with patch.object(application, 'SingleInstanceGuard', ProbeGuard):
        application.main()
print(json.dumps(names))
"""
        result = subprocess.run(
            [sys.executable, "-B", "-c", script, entrypoint],
            cwd=Path(__file__).resolve().parents[1], env=environment,
            capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout.splitlines()[-1])[0]

    def test_portable_settings_do_not_create_another_desktop_instance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = self._entrypoint_name(root / 'first-build')
            second = self._entrypoint_name(root / 'second-build')
            self.assertEqual(first, second)
            self.assertEqual(first, 'TacticHandler_Client')
            self.assertEqual(self._entrypoint_name(root / 'setup', entrypoint='setup'), first)
            builder = self._entrypoint_name(root / 'builder', entrypoint='builder')
            self.assertEqual(builder, instance_server_name('TacticHandler_SetupBuilder', str(root / 'builder')))
            self.assertNotEqual(builder, first)
            isolated = self._entrypoint_name(root / 'first-build', test_profile=root / 'test')
            self.assertNotEqual(isolated, first)
            self.assertEqual(isolated, self._entrypoint_name(root / 'second-build', test_profile=root / 'test'))

    def test_ownership_does_not_expire_by_age(self):
        guard = SingleInstanceGuard(self._name())
        self.addCleanup(guard.close)
        self.assertEqual(guard._lock.staleLockTime(), 0)

    def test_crashed_owner_does_not_block_a_new_process(self):
        name = self._name()
        script = (
            "from PySide6.QtCore import QCoreApplication; "
            "from thlib.ui.single_instance import SingleInstanceGuard; "
            "import sys; app = QCoreApplication([]); "
            "guard = SingleInstanceGuard(sys.argv[1]); "
            "assert guard.start(); print('ready', flush=True); sys.stdin.read()"
        )
        process = subprocess.Popen(
            [sys.executable, '-B', '-c', script, name],
            cwd=Path(__file__).resolve().parents[1],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True,
        )
        with ThreadPoolExecutor(max_workers=1) as reader:
            try:
                ready = reader.submit(process.stdout.readline)
                self.assertEqual(ready.result(timeout=10).strip(), 'ready')
            finally:
                process.kill()
                process.communicate(timeout=10)
        replacement = SingleInstanceGuard(name)
        self.addCleanup(replacement.close)
        self.assertTrue(replacement.start())

    def test_entrypoint_acquires_guard_before_starting_runtime_work(self):
        source = Path("thlib/ui/application.py").read_text(encoding="utf-8")
        guard_at = source.index("single_instance.start()")
        pools_at = source.index("env_inst.start_pools()")
        runtime_at = source.index("build_application_runtime(")

        self.assertLess(guard_at, pools_at)
        self.assertLess(guard_at, runtime_at)


if __name__ == "__main__":
    unittest.main()

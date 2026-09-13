"""Test setup rejects a non-GUI Qt process before any window is constructed."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch


class QtTestApplicationTests(unittest.TestCase):
    def run_isolated(self, code):
        environment = dict(os.environ, QT_QPA_PLATFORM='offscreen',
                           QT_QUICK_BACKEND='software')
        result = subprocess.run(
            [sys.executable, '-X', 'faulthandler', '-c', code],
            cwd=Path(__file__).resolve().parents[1], env=environment,
            capture_output=True, text=True, timeout=20, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_existing_core_application_is_rejected_without_native_crash(self):
        self.run_isolated('''
from PySide6.QtCore import QCoreApplication
from tests.qt_application import gui_test_application
app = QCoreApplication([])
try:
    gui_test_application()
except RuntimeError as error:
    assert 'earlier fixture created QCoreApplication' in str(error)
else:
    raise AssertionError('A non-GUI application must be rejected before QML')
''')

    @unittest.skipUnless(os.name == 'nt', 'Windows process error mode')
    def test_gui_fixture_disables_native_crash_dialogs_for_tests(self):
        import ctypes

        from tests.qt_application import (
            WINDOWS_TEST_ERROR_MODE,
            gui_test_application,
        )

        application = gui_test_application()
        self.assertIsNotNone(application)
        self.assertEqual(
            int(ctypes.windll.kernel32.GetErrorMode())
            & WINDOWS_TEST_ERROR_MODE,
            WINDOWS_TEST_ERROR_MODE,
        )

    def test_shared_suite_fixtures_do_not_create_core_only_applications(self):
        root = Path(__file__).resolve().parent
        offenders = []
        forbidden = (
            'QCoreApplication.instance() or QCoreApplication(',
            'QtCore.QCoreApplication.instance() or '
            'QtCore.QCoreApplication(',
        )
        for path in root.glob('test_*.py'):
            if path == Path(__file__):
                continue
            source = path.read_text(encoding='utf-8')
            if any(pattern in source for pattern in forbidden):
                offenders.append(path.name)
        self.assertEqual(offenders, [])

    def test_controller_fixture_can_run_before_gui_fixture(self):
        self.run_isolated('''
from PySide6.QtGui import QGuiApplication
from tests.test_administration_documents import AdministrationLifecycleTests
from tests.test_theme_controls import ThemeControlTests
AdministrationLifecycleTests.setUpClass()
ThemeControlTests.setUpClass()
assert isinstance(ThemeControlTests.app, QGuiApplication)
assert ThemeControlTests.app is AdministrationLifecycleTests.app
''')

    def test_activity_controller_fixture_can_precede_real_qml_view(self):
        self.run_isolated('''
from PySide6.QtGui import QGuiApplication
from tests.test_topbar_activity import TopBarActivityTests
from tests.test_activity_feed_qml import ActivityFeedQmlTests
TopBarActivityTests.setUpClass()
ActivityFeedQmlTests.setUpClass()
assert isinstance(TopBarActivityTests.app, QGuiApplication)
assert ActivityFeedQmlTests.app is TopBarActivityTests.app
case = ActivityFeedQmlTests(
    'test_feed_reflows_without_losing_search_calendar_or_refresh'
)
case.test_feed_reflows_without_losing_search_calendar_or_refresh()
''')

    def test_ui_hang_dump_keeps_all_python_thread_stacks(self):
        from thlib.ui.hang_diagnostics import UiHangWatchdog
        from tests.qt_application import gui_test_application

        gui_test_application()
        with tempfile.TemporaryDirectory() as temporary:
            watchdog = UiHangWatchdog(Path(temporary))
            with patch.object(
                watchdog, "_write_windows_minidump", return_value=None
            ):
                trace_path, dump_path = watchdog._write_dump(16.25)

            report = trace_path.read_text(encoding="utf-8")
            self.assertIsNone(dump_path)
            self.assertIn("TACTIC-Handler UI hang", report)
            self.assertIn("blocked_seconds=16.250", report)
            self.assertIn("test_ui_hang_dump", report)

    def test_ui_hang_watchdog_detects_a_blocked_event_loop(self):
        from thlib.ui.hang_diagnostics import UiHangWatchdog
        from tests.qt_application import gui_test_application

        gui_test_application()
        reported = threading.Event()
        trace_path = Path("ui_hang.txt")
        watchdog = UiHangWatchdog(Path.cwd(), timeout_seconds=1.0)
        with patch.object(
            watchdog,
            "_write_dump",
            return_value=(trace_path, None),
        ), patch.object(
            watchdog,
            "_terminate_after_hang",
            side_effect=lambda *_paths: reported.set(),
        ) as terminate:
            watchdog.start()
            try:
                self.assertTrue(reported.wait(2.0))
            finally:
                watchdog.stop()
        terminate.assert_called_once_with(trace_path, None)

    def test_ui_hang_watchdog_detaches_notice_before_forced_exit(self):
        from thlib.ui.hang_diagnostics import UiHangWatchdog

        watchdog = UiHangWatchdog(Path.cwd())
        with patch("thlib.ui.hang_diagnostics.sys.platform", "win32"), \
                patch("thlib.ui.hang_diagnostics.subprocess.Popen") as popen, \
                patch("thlib.ui.hang_diagnostics.os._exit") as forced_exit:
            watchdog._terminate_after_hang(
                Path("ui_hang.txt"), Path("ui_hang.dmp")
            )

        self.assertIn("ui_hang.dmp", popen.call_args.args[0][-2])
        forced_exit.assert_called_once_with(70)

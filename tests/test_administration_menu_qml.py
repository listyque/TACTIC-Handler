"""The actual application menu must update after asynchronous authentication."""

import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROBE = r'''
import traceback
from unittest.mock import patch

from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication
from thlib.environment import env_server
from thlib.ui import application

runtime = None
failures = []
original_build = application.build_application_runtime

def inspect_menu():
    try:
        window = next(w for w in QGuiApplication.allWindows()
                      if w.isVisible() and w.title() == 'TACTIC-Handler')
        controller = runtime.controller

        def has_admin():
            actions = window.property('configMenuActions')
            return any(row.get('command') == 'show_administration' for row in actions)

        assert not has_admin(), 'Administration visible before authentication'
        with patch.object(env_server, 'get_ticket', return_value='test-ticket'):
            controller._administration_identity = (controller.server_url, controller.server_user)
            controller._set_server_state('online', 'Test authenticated session')
            assert controller.can_administer, 'Native admin session was not published'
            assert has_admin(), 'Administration did not appear after signing in as admin'
            controller._set_server_state('authentication', 'Test signed out')
            assert not has_admin(), 'Administration remained visible after signing out'
            controller._set_server_state('online', 'Test supervisor session')
            assert not has_admin(), 'Supervisor received an administration menu entry'
    except Exception:
        failures.append(traceback.format_exc())
    finally:
        QGuiApplication.instance().quit()

def build(*args, **kwargs):
    global runtime
    runtime = original_build(*args, **kwargs)
    QTimer.singleShot(0, inspect_menu)
    return runtime

application.build_application_runtime = build
result = application.main()
if failures:
    print('\n'.join(failures), flush=True)
    raise SystemExit(1)
assert result == 0, result
print('ADMIN_MENU_OK', flush=True)
'''


class AdministrationMenuQmlTests(unittest.TestCase):
    def test_real_main_menu_updates_after_authentication_and_revocation(self):
        with TemporaryDirectory(prefix='handler-admin-menu-') as directory:
            environment = os.environ.copy()
            environment.update({
                'QT_QPA_PLATFORM': 'offscreen', 'QT_QUICK_BACKEND': 'software',
                'TACTIC_QML_SMOKE_OFFLINE': '1', 'TACTIC_QML_SMOKE_WINDOWS': '0',
                'TACTIC_QML_TEST_SETTINGS_DIR': directory,
                'APPDATA': directory, 'LOCALAPPDATA': directory,
                'QT_QPA_FONTDIR': str(Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts'),
            })
            completed = subprocess.run(
                [sys.executable, '-c', PROBE], cwd=ROOT, env=environment,
                capture_output=True, text=True, timeout=35, check=False,
            )
        diagnostic = completed.stdout + completed.stderr
        self.assertEqual(completed.returncode, 0, diagnostic)
        self.assertIn('ADMIN_MENU_OK', diagnostic)
        for warning in ('ReferenceError', 'Binding loop', 'TypeError:', 'Traceback'):
            self.assertNotIn(warning, diagnostic)


if __name__ == '__main__':
    unittest.main()

"""Bound the real editor suite's input and QML destruction lifecycle."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class EditorWindowsLifecycleTests(unittest.TestCase):
    def test_repeated_editor_input_and_teardown_finish_offscreen(self):
        environment = os.environ.copy()
        environment.update({
            'QT_QPA_PLATFORM': 'offscreen',
            'QT_QUICK_BACKEND': 'software',
        })
        environment.pop('QSG_RENDER_LOOP', None)
        with tempfile.TemporaryDirectory(prefix='editor-lifecycle-') as directory:
            environment.update(TMP=directory, TEMP=directory)
            completed = subprocess.run(
                [sys.executable, '-m', 'unittest', '-v',
                 'tests.test_editor_windows_qml.EditorWindowQmlTests'],
                cwd=ROOT, env=environment, capture_output=True, text=True,
                timeout=45, check=False,
            )
        self.assertEqual(
            completed.returncode, 0, (completed.stdout or '') + (completed.stderr or ''),
        )

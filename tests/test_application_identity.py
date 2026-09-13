"""Real launcher, Windows process identity and Qt/native window icons."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]

PROBE = r'''
import ctypes
from ctypes import wintypes
import json
import runpy
import sys

from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication
from thlib.ui import application

shell = ctypes.WinDLL("shell32")
get_id = shell.GetCurrentProcessExplicitAppUserModelID
get_id.argtypes = (ctypes.POINTER(ctypes.c_wchar_p),)
get_id.restype = ctypes.c_long
free = ctypes.OleDLL("ole32").CoTaskMemFree
free.argtypes = (ctypes.c_void_p,)
free.restype = None
observed = {}

def read_identity():
    value = ctypes.c_wchar_p()
    result = get_id(ctypes.byref(value))
    try:
        return {"hresult": result, "id": value.value}
    finally:
        if value:
            free(value)

def inspect_window():
    app = QGuiApplication.instance()
    window = next(w for w in app.topLevelWindows()
                  if w.isVisible() and w.title() == "TACTIC-Handler")
    observed["windowIconMatches"] = (
        window.icon().cacheKey() == app.windowIcon().cacheKey()
    )
    observed["iconSizes"] = [s.width() for s in app.windowIcon().availableSizes()]
    observed["windowIconNull"] = window.icon().isNull()
    if app.platformName() == "windows":
        send = ctypes.WinDLL("user32").SendMessageW
        send.argtypes = (wintypes.HWND, wintypes.UINT,
                         wintypes.WPARAM, wintypes.LPARAM)
        send.restype = ctypes.c_void_p
        observed["nativeIcons"] = [bool(send(int(window.winId()), 0x007F, kind, 0))
                                   for kind in (0, 1)]

original_build = application.build_application_runtime

def build(*args, **kwargs):
    observed["beforeWindows"] = read_identity()
    observed["windowCountAtBuild"] = len(QGuiApplication.allWindows())
    runtime = original_build(*args, **kwargs)
    QTimer.singleShot(0, inspect_window)
    return runtime

application.build_application_runtime = build
try:
    runpy.run_path(sys.argv[1], run_name="__main__")
except SystemExit as result:
    observed["exitCode"] = result.code
print("TASKBAR_PROBE=" + json.dumps(observed), flush=True)
'''


@unittest.skipUnless(sys.platform == "win32", "Windows taskbar contract")
class ApplicationIdentityTests(unittest.TestCase):
    def test_launchers_set_handler_identity_and_inherit_application_icon(self):
        for launcher in ("launch.py", "launch.pyw"):
            with self.subTest(launcher=launcher), tempfile.TemporaryDirectory(
                prefix="handler-taskbar-test-"
            ) as directory:
                environment = os.environ.copy()
                environment.setdefault("QT_QPA_PLATFORM", "offscreen")
                environment.setdefault("QT_QUICK_BACKEND", "software")
                environment.update({
                    "TACTIC_QML_SMOKE_OFFLINE": "1",
                    "TACTIC_QML_SMOKE_WINDOWS": "0",
                    "TACTIC_QML_SMOKE_EXIT_MS": "400",
                    "TACTIC_QML_TEST_SETTINGS_DIR": directory,
                    "LOCALAPPDATA": directory,
                    "APPDATA": directory,
                    "QT_QPA_FONTDIR": str(
                        Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
                    ),
                })
                completed = subprocess.run(
                    [sys.executable, "-c", PROBE, str(ROOT / launcher)],
                    cwd=ROOT,
                    env=environment,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )
                diagnostics = completed.stdout + completed.stderr
                self.assertEqual(completed.returncode, 0, diagnostics)
                line = next((line for line in completed.stdout.splitlines()
                             if line.startswith("TASKBAR_PROBE=")), "")
                self.assertTrue(line, diagnostics)
                observed = json.loads(line.split("=", 1)[1])
                self.assertEqual(observed["exitCode"], 0, diagnostics)
                self.assertEqual(observed["beforeWindows"], {
                    "hresult": 0, "id": "TACTIC.Handler.Desktop",
                })
                self.assertEqual(observed["windowCountAtBuild"], 0)
                self.assertFalse(observed["windowIconNull"])
                self.assertTrue(observed["windowIconMatches"])
                self.assertIn(16, observed["iconSizes"])
                self.assertIn(32, observed["iconSizes"])
                if environment["QT_QPA_PLATFORM"] == "windows":
                    self.assertEqual(observed["nativeIcons"], [True, True])
                self.assertNotIn("Traceback", diagnostics)
                self.assertNotIn("Binding loop", diagnostics)
                self.assertNotIn("ReferenceError", diagnostics)


if __name__ == "__main__":
    unittest.main()

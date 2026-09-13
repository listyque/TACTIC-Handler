"""GUI-capable Qt application shared by controller and QML test fixtures."""

import ctypes
import os

from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QGuiApplication


WINDOWS_TEST_ERROR_MODE = 0x0001 | 0x0002 | 0x8000


def suppress_windows_test_error_dialogs() -> None:
    """Keep a native test crash observable without blocking on a modal box."""
    if os.name != "nt":
        return
    kernel32 = ctypes.windll.kernel32
    current_mode = int(kernel32.GetErrorMode())
    kernel32.SetErrorMode(current_mode | WINDOWS_TEST_ERROR_MODE)


def gui_test_application() -> QGuiApplication:
    suppress_windows_test_error_dialogs()
    application = QCoreApplication.instance()
    if application is not None:
        if not isinstance(application, QGuiApplication):
            raise RuntimeError(
                'QML tests require QGuiApplication, but an earlier fixture '
                'created QCoreApplication. Use gui_test_application() in that '
                'fixture or run GUI tests in a separate process.'
            )
        return application
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    os.environ.setdefault('QT_QUICK_BACKEND', 'software')
    return QGuiApplication([])

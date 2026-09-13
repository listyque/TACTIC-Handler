"""Native window-frame appearance kept in sync with the QML theme."""

from __future__ import annotations

import sys

from PySide6.QtCore import QObject, Slot
from PySide6.QtGui import QColor


class WindowAppearanceController(QObject):
    _IMMERSIVE_DARK_MODE = 20
    _IMMERSIVE_DARK_MODE_OLD = 19
    _CAPTION_COLOR = 35
    _TEXT_COLOR = 36

    @staticmethod
    def _colorref(value: QColor) -> int:
        color = QColor(value)
        return (
            color.red()
            | (color.green() << 8)
            | (color.blue() << 16)
        )

    @Slot(QObject, bool, QColor, QColor, result=bool)
    def apply(self, window, dark, caption_color, text_color):
        if sys.platform != "win32" or window is None:
            return False
        try:
            import ctypes

            hwnd = int(window.winId())
            if not hwnd:
                return False
            dwm = ctypes.windll.dwmapi.DwmSetWindowAttribute
            dwm.argtypes = (
                ctypes.c_void_p,
                ctypes.c_uint,
                ctypes.c_void_p,
                ctypes.c_uint,
            )
            dwm.restype = ctypes.c_long
            native_handle = ctypes.c_void_p(hwnd)
            mode = ctypes.c_int(1 if dark else 0)
            result = dwm(
                native_handle,
                self._IMMERSIVE_DARK_MODE,
                ctypes.byref(mode),
                ctypes.sizeof(mode),
            )
            if result:
                dwm(
                    native_handle,
                    self._IMMERSIVE_DARK_MODE_OLD,
                    ctypes.byref(mode),
                    ctypes.sizeof(mode),
                )

            caption = ctypes.c_uint(self._colorref(caption_color))
            text = ctypes.c_uint(self._colorref(text_color))
            dwm(
                native_handle,
                self._CAPTION_COLOR,
                ctypes.byref(caption),
                ctypes.sizeof(caption),
            )
            dwm(
                native_handle,
                self._TEXT_COLOR,
                ctypes.byref(text),
                ctypes.sizeof(text),
            )
            return True
        except (AttributeError, OSError, TypeError, ValueError):
            return False

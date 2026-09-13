from __future__ import annotations

import unittest

from PySide6.QtGui import QColor

from thlib.ui.window_appearance import WindowAppearanceController


class WindowAppearanceTests(unittest.TestCase):
    def test_qcolor_is_encoded_as_windows_colorref(self):
        self.assertEqual(
            WindowAppearanceController._colorref(QColor("#123456")),
            0x563412,
        )

    def test_non_window_target_is_ignored(self):
        controller = WindowAppearanceController()
        self.assertFalse(
            controller.apply(
                None, False, QColor("#eeeeee"), QColor("#111111")
            )
        )


if __name__ == "__main__":
    unittest.main()

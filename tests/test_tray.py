from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

from thlib.ui.tray import TrayController


class FakeNotifications:
    def __init__(self):
        self.messages = []

    def notify(self, message):
        self.messages.append(str(message))


class TrayControllerTests(unittest.TestCase):
    def setUp(self):
        tray_patcher = patch("thlib.ui.tray.QSystemTrayIcon")
        menu_patcher = patch("thlib.ui.tray.QMenu")
        action_patcher = patch("thlib.ui.tray.QAction")
        self.tray_class = tray_patcher.start()
        self.menu_class = menu_patcher.start()
        self.action_class = action_patcher.start()
        self.addCleanup(tray_patcher.stop)
        self.addCleanup(menu_patcher.stop)
        self.addCleanup(action_patcher.stop)
        self.tray_class.isSystemTrayAvailable.return_value = True
        self.action_class.side_effect = [MagicMock(), MagicMock()]

    def make_controller(self, close_to_tray=True):
        controller = TrayController(
            Path("missing-test-icon.ico"),
            lambda: close_to_tray,
        )
        window = MagicMock()
        notifications = FakeNotifications()
        controller.attach_window(window)
        controller.attach_notifications(notifications)
        return (
            controller, window, self.tray_class.return_value, notifications,
        )

    def test_main_close_hides_to_tray_by_default(self):
        controller, window, tray_icon, notifications = self.make_controller(
            True
        )

        self.assertFalse(controller.handle_close())
        window.hide.assert_called_once_with()
        tray_icon.showMessage.assert_not_called()
        self.assertEqual(len(notifications.messages), 1)
        self.assertIn("TACTIC Handler", notifications.messages[0])

        self.assertFalse(controller.handle_close())
        self.assertEqual(len(notifications.messages), 1)
        tray_icon.showMessage.assert_not_called()

    @patch("thlib.ui.tray.QApplication.quit")
    def test_disabled_close_to_tray_exits_completely(self, quit_application):
        controller, window, _tray_icon, _notifications = self.make_controller(
            False
        )

        self.assertTrue(controller.handle_close())
        quit_application.assert_called_once_with()
        window.hide.assert_not_called()

    def test_tray_does_not_own_message_or_activity_notifications(self):
        controller, _window, tray_icon, _notifications = self.make_controller(
            True
        )

        self.assertFalse(hasattr(controller, "attach_messages"))
        self.assertFalse(hasattr(controller, "attach_activity"))
        self.assertFalse(hasattr(controller, "_message_clicked"))
        tray_icon.showMessage.assert_not_called()


if __name__ == "__main__":
    unittest.main()

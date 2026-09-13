from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QCoreApplication, QObject, Slot
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon


class TrayController(QObject):
    def __init__(
        self,
        icon_path,
        close_to_tray: Callable[[], bool] | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._window = None
        self._notifications = None
        self._close_to_tray = close_to_tray or (lambda: True)
        self._quitting = False
        self._close_notice_shown = False
        self._tray = QSystemTrayIcon(self)
        icon = QIcon(str(icon_path))
        if not icon.isNull():
            self._tray.setIcon(icon)
        self._menu = QMenu()
        self._show_action = QAction(self._menu)
        self._show_action.triggered.connect(self.show_window)
        self._menu.addAction(self._show_action)
        self._menu.addSeparator()
        self._exit_action = QAction(self._menu)
        self._exit_action.triggered.connect(self.quit_application)
        self._menu.addAction(self._exit_action)
        self._tray.setContextMenu(self._menu)
        self._tray.activated.connect(self._activated)
        self.retranslate()
        if QSystemTrayIcon.isSystemTrayAvailable():
            self._tray.show()

    @staticmethod
    def _translate(text: str) -> str:
        return QCoreApplication.translate("TrayController", text)

    @Slot()
    def retranslate(self) -> None:
        self._tray.setToolTip("TACTIC Handler")
        self._show_action.setText(self._translate("Show TACTIC Handler"))
        self._exit_action.setText(self._translate("Exit"))

    def attach_window(self, window):
        self._window = window

    def attach_notifications(self, notifications) -> None:
        self._notifications = notifications

    @Slot(result=bool)
    def handle_close(self):
        if self._quitting:
            return True
        if not self._close_to_tray():
            self.quit_application()
            return True
        if QSystemTrayIcon.isSystemTrayAvailable():
            self._window.hide()
            if not self._close_notice_shown:
                if self._notifications is not None:
                    self._notifications.notify(self._translate(
                        "TACTIC Handler is still running. Use the tray "
                        "icon to restore the window or exit the application."
                    ))
                self._close_notice_shown = True
            return False
        if self._window:
            self._window.showMinimized()
            return False
        return True

    @Slot()
    def show_window(self):
        if not self._window:
            return
        self._window.showNormal()
        self._window.raise_()
        self._window.requestActivate()

    @Slot()
    def quit_application(self):
        self._quitting = True
        QApplication.quit()

    @Slot(QSystemTrayIcon.ActivationReason)
    def _activated(self, reason):
        if reason in {
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        }:
            self.show_window()

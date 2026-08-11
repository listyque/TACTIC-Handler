from __future__ import annotations

from PySide6.QtCore import QObject, Slot
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon


class TrayController(QObject):
    def __init__(self, icon_path, parent=None):
        super().__init__(parent)
        self._window = None
        self._tray = QSystemTrayIcon(self)
        icon = QIcon(str(icon_path))
        if not icon.isNull():
            self._tray.setIcon(icon)
        self._tray.setToolTip("TACTIC Handler")
        menu = QMenu()
        show_action = QAction("Show TACTIC Handler", menu)
        show_action.triggered.connect(self.show_window)
        menu.addAction(show_action)
        menu.addSeparator()
        exit_action = QAction("Exit", menu)
        exit_action.triggered.connect(self.quit_application)
        menu.addAction(exit_action)
        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._activated)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self._tray.show()

    def attach_window(self, window):
        self._window = window

    @Slot(bool)
    def handle_close(self, has_dcc_clients):
        if has_dcc_clients and QSystemTrayIcon.isSystemTrayAvailable():
            self._window.hide()
            self._tray.showMessage(
                "TACTIC Handler is still running",
                "A DCC client is connected. Use the tray icon to restore the window.",
                QSystemTrayIcon.MessageIcon.Information,
                2500,
            )
            return
        if has_dcc_clients:
            self._window.showMinimized()
            return
        self.quit_application()

    @Slot()
    def show_window(self):
        if not self._window:
            return
        self._window.showNormal()
        self._window.raise_()
        self._window.requestActivate()

    @Slot()
    def quit_application(self):
        QApplication.quit()

    @Slot(QSystemTrayIcon.ActivationReason)
    def _activated(self, reason):
        if reason in {
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        }:
            self.show_window()

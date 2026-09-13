from __future__ import annotations

import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")

from PySide6.QtCore import QObject, Property, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from thlib.ui.localization import CatalogTranslator
from thlib.ui.workspace_models.records import RecordListModel


ROOT = Path(__file__).resolve().parents[1]
QML = ROOT / "thlib" / "ui" / "qml"


class _LoginController(QObject):
    authenticationChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._authentication_error = (
            "Enter your TACTIC login and password to generate a ticket."
        )
        self._dialog_visible = True

    @Property(bool, notify=authenticationChanged)
    def authentication_dialog_visible(self) -> bool:
        return self._dialog_visible

    @Property(bool, notify=authenticationChanged)
    def authentication_busy(self) -> bool:
        return False

    @Property(str, notify=authenticationChanged)
    def authentication_error(self) -> str:
        return self._authentication_error

    @Property(str, notify=authenticationChanged)
    def login_name(self) -> str:
        return ""

    @Property(str, notify=authenticationChanged)
    def server_url(self) -> str:
        return "http://tactic.example"

    def set_error(self, message: str) -> None:
        self._authentication_error = message
        self.authenticationChanged.emit()

    @Slot()
    def cancel_authentication(self) -> None:
        self._dialog_visible = False
        self.authenticationChanged.emit()

    @Slot(str, str)
    def authenticate(self, _login: str, _password: str) -> None:
        pass


class _NotificationController(QObject):
    @Slot(int)
    def dismiss(self, _index: int) -> None:
        pass

    @Slot(int)
    def activate(self, _index: int) -> None:
        pass


class LoginLocalizationQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def test_login_dialog_translates_runtime_authentication_messages(self):
        translator = CatalogTranslator(
            QML.parent / "translations" / "ru.json"
        )
        self.app.installTranslator(translator)
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        controller = _LoginController()
        engine.rootContext().setContextProperty("appController", controller)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        owner = QQuickWindow()
        owner.resize(720, 520)
        owner.show()
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "LoginDialog.qml"))
        )
        dialog = component.createWithInitialProperties({
            "ownerWindow": owner,
            "theme": theme,
        })
        self.assertIsNotNone(
            dialog,
            "\n".join(error.toString() for error in component.errors()),
        )

        try:
            QTest.qWait(30)
            message = dialog.findChild(QObject, "loginAuthenticationMessage")
            self.assertIsNotNone(message)
            expected_messages = {
                "Enter your TACTIC login and password to generate a ticket.":
                    "Введите логин и пароль TACTIC, чтобы создать тикет.",
                "Your TACTIC session has expired. Generate a new ticket.":
                    "Сессия TACTIC истекла. Создайте новый тикет.",
                "Enter both login and password.":
                    "Введите логин и пароль.",
                "Incorrect login or password.":
                    "Неверный логин или пароль.",
                "The TACTIC server did not respond in time.":
                    "Сервер TACTIC не ответил вовремя.",
                "Cannot connect to the configured TACTIC server.":
                    "Не удалось подключиться к настроенному серверу TACTIC.",
                "TACTIC did not issue an authentication ticket.":
                    "TACTIC не выдал тикет аутентификации.",
                "TACTIC did not accept the generated ticket.":
                    "TACTIC не принял созданный тикет.",
            }
            for source, expected in expected_messages.items():
                with self.subTest(source=source):
                    controller.set_error(source)
                    QTest.qWait(2)
                    self.assertEqual(message.property("text"), expected)
        finally:
            controller.cancel_authentication()
            dialog.close()
            owner.close()
            dialog.deleteLater()
            owner.deleteLater()
            theme.deleteLater()
            controller.deleteLater()
            engine.deleteLater()
            self.app.processEvents()
            self.app.removeTranslator(translator)

    def test_signed_out_notification_translates_controller_message(self):
        translator = CatalogTranslator(
            QML.parent / "translations" / "ru.json"
        )
        self.app.installTranslator(translator)
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        model = RecordListModel((
            "kind", "message", "detail", "progress", "dismissible",
            "action", "actionData", "sourceType", "sourceTitle",
            "previewUrl", "avatarText", "avatarColor", "sourceIcon",
        ), [{
            "kind": "error",
            "message": "Select an existing server preset",
            "detail": "",
            "progress": 0.0,
            "dismissible": True,
            "action": "",
            "actionData": "",
            "sourceType": "",
            "sourceTitle": "",
            "previewUrl": "",
            "avatarText": "",
            "avatarColor": "",
            "sourceIcon": "",
        }])
        controller = _NotificationController()
        context = engine.rootContext()
        context.setContextProperty("notificationModel", model)
        context.setContextProperty("notificationController", controller)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "NotificationStack.qml"))
        )
        stack = component.createWithInitialProperties({
            "theme": theme,
            "controller": controller,
            "notifications": model,
        })
        self.assertIsNotNone(
            stack,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.resize(440, 220)
        stack.setParentItem(window.contentItem())
        stack.setWidth(390)
        stack.setHeight(200)
        window.show()

        try:
            QTest.qWait(20)
            pending = list(stack.childItems())
            message = None
            while pending:
                item = pending.pop()
                pending.extend(item.childItems())
                if (
                    isinstance(item, QQuickItem)
                    and item.objectName() == "notificationMessage"
                ):
                    message = item
                    break
            self.assertIsNotNone(message)
            self.assertEqual(
                message.property("text"),
                "Выберите существующий пресет сервера",
            )
        finally:
            window.close()
            stack.setParentItem(None)
            stack.deleteLater()
            window.deleteLater()
            theme.deleteLater()
            controller.deleteLater()
            model.deleteLater()
            engine.deleteLater()
            self.app.processEvents()
            self.app.removeTranslator(translator)


if __name__ == "__main__":
    unittest.main()

"""Real native input through the production communication presenters."""

from pathlib import Path
import os

os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
import unittest
from unittest.mock import Mock

from PySide6.QtCore import QCoreApplication, QEvent, QPointF, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtGui import QAccessible
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QSignalSpy, QTest
from tests.qt_application import gui_test_application
from tests.profile_ui_responsiveness import frame
from tests.frame_messages_fixture import Fixture, Locale
from thlib.ui.icon_font import qml_icon_bindings

QML = Path(__file__).resolve().parents[1] / "thlib/ui/qml"


class FrameMessagesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def setUp(self):
        self.fixture = Fixture()
        self.engine = QQmlEngine()
        self.engine.addImportPath(str(QML))
        self.warnings = []
        self.engine.warnings.connect(
            lambda errors: self.warnings.extend(error.toString() for error in errors)
        )
        self.locale = Locale("en")
        for name, value in dict(
            qml_icon_bindings(QML.parents[2], self.app),
            **self.fixture.context(),
            localizationController=self.locale,
        ).items():
            self.engine.rootContext().setContextProperty(name, value)
        self.theme_component = QQmlComponent(
            self.engine, QUrl.fromLocalFile(str(QML / "Theme.qml"))
        )
        self.theme = self.theme_component.createWithInitialProperties(
            dict(
                dark=True,
                clickAnimationsEnabled=False,
                hoverAnimationsEnabled=False,
                popupAnimationsEnabled=False,
                fadeAnimationsEnabled=False,
            )
        )
        self.window = QQuickWindow()
        self.window.resize(1000, 620)
        self.view = None

    def create(self, name, **properties):
        self.component = QQmlComponent(self.engine, QUrl.fromLocalFile(str(QML / name)))
        self.view = self.component.createWithInitialProperties(
            dict(theme=self.theme, parent=self.window.contentItem(), **properties)
        )
        self.assertIsNotNone(
            self.view, "\n".join(error.toString() for error in self.component.errors())
        )
        self.view.setParent(self.window)
        self.window.show()
        self.settle()
        return self.view

    def settle(self):
        for _ in range(3):
            frame(self.window)

    def items(self, name):
        found = []
        pending = [self.window.contentItem()]
        while pending:
            item = pending.pop()
            if item.objectName() == name and item.isVisible():
                found.append(item)
            pending.extend(item.childItems())
        return found

    def click(self, item):
        QTest.mouseClick(
            self.window,
            Qt.LeftButton,
            pos=item.mapToScene(QPointF(item.width() / 2, item.height() / 2)).toPoint(),
        )
        self.settle()

    def tearDown(self):
        self.window.close()
        if self.view:
            self.view.deleteLater()
        self.window.deleteLater()
        self.theme.deleteLater()
        self.fixture.close()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.assertFalse(self.warnings, "\n".join(self.warnings))

    def test_composer_profile_and_metadata_use_real_input(self):
        self.fixture.controller.send = Mock(return_value=True)
        self.create("MessagesView.qml", width=1000, height=620)
        composer = self.items("messageComposerTextArea")[0]
        self.click(composer)
        for character in "Review draft":
            QTest.keyClick(self.window, character)
        self.settle()
        self.assertEqual(self.fixture.controller.draftText, "Review draft")
        QTest.keyClick(self.window, Qt.Key_Return, Qt.ControlModifier)
        for character in "Second line":
            QTest.keyClick(self.window, character)
        self.settle()
        self.assertEqual(self.fixture.controller.draftText, "Review draft\nSecond line")
        QTest.keyClick(self.window, Qt.Key_Return)
        self.settle()
        self.fixture.controller.send.assert_called_once_with(
            "Review draft\nSecond line"
        )
        self.click(self.items("messageSender")[0])
        self.assertIn(self.fixture.profiles.opened, ("admin", "artist"))
        delivery = self.items("messageDelivery")[0]
        delivery.forceActiveFocus()
        self.settle()
        self.assertTrue(delivery.hasActiveFocus())
        accessible = QAccessible.queryAccessibleInterface(delivery)
        self.assertIsNotNone(accessible)
        self.assertEqual(accessible.text(QAccessible.Name), "Read by 1 of 1")
        self.assertTrue(self.items("messageTimeLabel"))

    def test_message_menu_remains_usable_during_selection(self):
        view = self.create("MessagesView.qml", width=1000, height=620)
        self.fixture.controller.toggle_forward_selection("MSG001")
        self.settle()
        button = self.items("messageActionsButton")[0]
        point = button.mapToScene(
            QPointF(button.width() / 2, button.height() / 2)
        ).toPoint()
        QTest.mouseMove(self.window, point)
        self.settle()
        self.click(button)
        self.assertIn(view.property("actionMessageId"), ("MSG001", "MSG002", "MSG003"))
        self.assertEqual(self.fixture.controller.forwardSelectionCount, 1)
        QTest.keyClick(self.window, Qt.Key_Escape)
        self.settle()
        body = self.items("messageBodyText")[0]
        self.click(body)
        self.assertEqual(self.fixture.controller.forwardSelectionCount, 2)

    def test_picker_accepts_first_click_and_form_enter(self):
        form = self.create(
            "features/messages/MessageForm.qml",
            width=408,
            mode="create",
            availableBodyHeight=508,
        )
        form.selectionChanged.connect(
            lambda logins: form.setProperty(
                "selectedLogins",
                logins.toVariant() if hasattr(logins, "toVariant") else logins,
            )
        )
        self.click(self.items("userPickerAction_artist")[0])
        value = form.property("selectedLogins")
        value = value.toVariant() if hasattr(value, "toVariant") else value
        self.assertEqual(value, ["artist"])
        self.click(self.items("userPickerAction_reviewer")[0])
        title = self.items("messageGroupTitle")[0]
        self.click(title)
        for character in "Lighting review":
            QTest.keyClick(self.window, character)
        submitted = QSignalSpy(form.submitted)
        QTest.keyClick(self.window, Qt.Key_Return)
        self.settle()
        self.assertEqual(submitted.count(), 1)
        self.assertEqual(form.property("text"), "Lighting review")
        self.assertEqual(len(self.items("messageFormSubmit")), 1)

    def test_confirmation_measures_its_live_description(self):
        view=self.create("features/messages/MessageForm.qml",width=380,mode="clear")
        self.assertGreater(view.property("descriptionHeight"),18)
        self.assertLess(view.property("descriptionHeight"),72)
        submitted=QSignalSpy(view.submitted)
        self.click(self.items("messageFormSubmit")[0])
        self.assertEqual(submitted.count(),1)

    def test_forward_reference_measures_multiple_lines_and_opens(self):
        view = self.create(
            "MessageForwardPreview.qml",
            width=260,
            sender="Administrator",
            body="Thank you! I will review it now.",
            attachmentCount=2,
        )
        self.assertGreater(view.property("implicitHeight"), 62)
        accepted = QSignalSpy(view.activated)
        self.click(self.items("messageReferenceOpen")[0])
        self.assertEqual(accepted.count(), 1)
        self.window.setWidth(380)
        view.setWidth(200)
        self.settle()
        self.assertGreater(view.property("implicitHeight"), 62)


if __name__ == "__main__":
    unittest.main()

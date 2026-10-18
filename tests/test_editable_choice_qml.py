"""Editable house ComboBox accepts native text and Enter once."""

import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

from PySide6.QtCore import QCoreApplication, QEvent, QPointF, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest
from tests.profile_ui_responsiveness import frame

QML = Path(__file__).resolve().parents[1] / "thlib/ui/qml"


class EditableChoiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def test_pointer_focus_accepts_custom_mapping_and_enter_once(self):
        engine = QQmlEngine()
        warnings = []
        engine.warnings.connect(lambda errors: warnings.extend(str(e) for e in errors))
        component = QQmlComponent(engine)
        component.setData(
            b"""
import QtQuick
import QtQuick.Window
import "." as App
import "controls" as Controls
Window {
    width: 400; height: 180; visible: true
    property int acceptedCount: 0
    App.Theme { id: theme; dark: true }
    Controls.ComboBox {
        id: choice; objectName: "editableChoice"; theme: theme; x: 20; y: 20; width: 300
        editable: true; model: ["publish", "render"]
        onAccepted: acceptedCount++
    }
}
""",
            QUrl.fromLocalFile(str(QML / "_EditableChoiceTest.qml")),
        )
        window = component.create()
        self.assertIsNotNone(window, str(component.errors()))
        try:
            window.requestActivate()
            frame(window)
            choice = window.findChild(QQuickItem, "editableChoice")
            center = choice.mapToScene(QPointF(50, choice.height() / 2))
            frame(
                window,
                lambda: QTest.mouseClick(window, Qt.LeftButton, pos=center.toPoint()),
            )
            QTest.keyClick(window, Qt.Key_A, Qt.ControlModifier)
            for char in "custom":
                QTest.keyClick(window, Qt.Key(ord(char.upper())))
            frame(window)
            self.assertEqual(choice.property("editText"), "custom")
            QTest.keyClick(window, Qt.Key_Return)
            frame(window)
            self.assertEqual(window.property("acceptedCount"), 1)
            self.assertEqual(choice.property("currentIndex"), 0)
            QTest.keyClick(window, Qt.Key_Down)
            frame(window)
            popup = self.app.focusWindow() or window
            QTest.keyClick(popup, Qt.Key_Down)
            QTest.keyClick(popup, Qt.Key_Return)
            frame(window)
            self.assertEqual(choice.property("currentIndex"), 1)
            self.assertEqual(choice.property("editText"), "render")

            self.assertEqual(warnings, [])
        finally:
            window.close()
            window.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
            engine.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


if __name__ == "__main__":
    unittest.main()

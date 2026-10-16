"""The update offer uses the real QML button and window route."""

import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")

from PySide6.QtCore import QObject, QPointF, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest


QML = Path(__file__).resolve().parents[1] / "thlib" / "ui" / "qml"


class Controller(QObject):
    updateAvailable = Signal(str)

    def __init__(self):
        super().__init__()
        self.installs = 0

    @Slot()
    def install_selected(self):
        self.installs += 1


class Windows(QObject):
    def __init__(self):
        super().__init__()
        self.opened = []

    @Slot(str)
    def show_window(self, window_id):
        self.opened.append(window_id)


class UpdatePromptQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def test_offer_install_button_opens_progress_window(self):
        engine = QQmlEngine()
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "UpdatePrompt.qml"))
        )
        controller, windows = Controller(), Windows()
        prompt = component.createWithInitialProperties({
            "theme": theme, "controller": controller, "windows": windows,
        })
        self.assertIsNotNone(
            prompt, "\n".join(error.toString() for error in component.errors())
        )
        window = QQuickWindow()
        window.resize(460, 400)
        prompt.setParentItem(window.contentItem())
        prompt.setWidth(460)
        prompt.setHeight(400)
        window.show()
        try:
            for count, width in enumerate((460, 900), start=1):
                window.resize(width, 400)
                prompt.setWidth(width)
                controller.updateAvailable.emit("0.5.1.0")
                QTest.qWait(350)
                dialog = prompt.findChild(QObject, "availableUpdateDialog")
                self.assertIsNotNone(dialog)
                self.assertTrue(dialog.property("visible"))
                from tests import test_sidebar_editor_qml as sidebar_fixture
                button = next((item for item in sidebar_fixture.SidebarEditorQmlTests.descendants(window.contentItem())
                               if item.objectName() == "installUpdateButton"), None)
                self.assertIsNotNone(button)
                point = button.mapToScene(QPointF(
                    button.width() / 2, button.height() / 2,
                )).toPoint()
                self.assertTrue(button.isVisible())
                self.assertLess(point.x(), width)
                QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=point)
                self.app.processEvents()
                self.assertEqual(controller.installs, count)
                self.assertEqual(windows.opened, ["update"] * count)
        finally:
            window.close()
            prompt.deleteLater()
            theme.deleteLater()
            engine.deleteLater()


if __name__ == "__main__":
    unittest.main()

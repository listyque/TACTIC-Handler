import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
from PySide6.QtCore import QObject, QPointF, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlEngine, QQmlComponent
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
from tests.profile_ui_responsiveness import frame
from tests.frame_files_fixture import Fixture

QML = Path(__file__).resolve().parents[1] / "thlib/ui/qml"


def visual(item, name):
    if item.objectName() == name:
        return item
    for child in item.childItems():
        result = visual(child, name)
        if result is not None:
            return result


class FrameDropPlateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def test_native_filter_checks_context_menu_and_queue_handoff(self):
        with Fixture() as fixture:
            engine = QQmlEngine()
            warnings = []
            engine.warnings.connect(
                lambda errors: warnings.extend(str(error) for error in errors)
            )
            for name, value in fixture.context().items():
                engine.rootContext().setContextProperty(name, value)
            theme_component = QQmlComponent(
                engine, QUrl.fromLocalFile(str(QML / "Theme.qml"))
            )
            theme = theme_component.createWithInitialProperties(
                {"dark": True, "popupAnimationsEnabled": False}
            )
            component = QQmlComponent(
                engine, QUrl.fromLocalFile(str(QML / "DropPlateView.qml"))
            )
            view = component.createWithInitialProperties({"theme": theme})
            self.assertIsNotNone(
                view, "\n".join(str(error) for error in component.errors())
            )
            window = QQuickWindow()
            view.setParentItem(window.contentItem())
            window.resize(1000, 700)
            view.setWidth(1000)
            view.setHeight(700)
            window.show()

            def click(name, button=Qt.LeftButton):
                item = visual(window.contentItem(), name)
                self.assertIsNotNone(item, name)
                QTest.mouseClick(
                    window,
                    button,
                    pos=item.mapToScene(
                        QPointF(item.width() / 2, item.height() / 2)
                    ).toPoint(),
                )
                frame(window)

            try:
                for width in (390, 640, 1000):
                    window.resize(width, 700)
                    view.setWidth(width)
                    frame(window)
                    for name in (
                        "dropPlateFilter",
                        "dropPlateQueue",
                        "dropPlateContext",
                    ):
                        item = visual(view, name)
                        point = item.mapToScene(QPointF())
                        self.assertGreaterEqual(point.x(), 0)
                        self.assertGreaterEqual(point.y(), 0)
                        self.assertLessEqual(point.x() + item.width(), width)
                        self.assertLessEqual(point.y() + item.height(), 700)
                self.assertEqual(warnings, [])
                self.assertIsNotNone(visual(view, "dropPlateGroup_0"))
                click("dropPlateCheck_0")
                self.assertFalse(fixture.drop.model.get(0)["checked"])
                click("dropPlateCheck_0")
                self.assertTrue(fixture.drop.model.get(0)["checked"])
                field = visual(view, "dropPlateFilter")
                click("dropPlateFilter")
                for char in "diffuse":
                    QTest.keyClick(window, Qt.Key(ord(char.upper())))
                frame(window)
                self.assertIsNone(visual(view, "dropPlateGroup_0"))
                self.assertIsNotNone(visual(view, "dropPlateGroup_1"))
                QTest.keyClick(window, Qt.Key_A, Qt.ControlModifier)
                QTest.keyClick(window, Qt.Key_Backspace)
                frame(window)
                click("dropPlateGroup_0", Qt.RightButton)
                menu = view.findChild(QObject, "dropPlateFileMenu")
                self.assertIsNotNone(menu)
                self.assertTrue(menu.property("opened"))
                self.assertEqual(view.property("contextGroupId"), "0")
                QTest.keyClick(self.app.focusWindow() or window, Qt.Key_Escape)
                frame(window)
                self.assertFalse(menu.property("opened"))
                click("dropPlateContext")
                QTest.keyClick(window, Qt.Key_A, Qt.ControlModifier)
                for char in "custom":
                    QTest.keyClick(window, Qt.Key(ord(char.upper())))
                frame(window)
                self.assertEqual(fixture.checkin.context, "custom")
                click("dropPlateQueue")
                self.assertEqual(fixture.drop.count, 1)
                self.assertEqual(len(fixture.queue.payloads), 1)
                self.assertEqual(fixture.queue.payloads[0][0]["context"], "custom")
                self.assertEqual(
                    fixture.queue.payloads[0][0]["dropPlateGroupIds"], ["0"]
                )
                fixture.drop.model.replace(
                    [
                        dict(
                            fixture.data["groups"][0],
                            groupId=str(index),
                            title=f"file_{index}.exr",
                        )
                        for index in range(1000)
                    ]
                )
                frame(window)
                lst = visual(view, "dropPlateGroups")
                self.assertLess(len(lst.property("contentItem").childItems()), 50)
                self.assertEqual(warnings, [])
            finally:
                window.close()
                view.deleteLater()
                window.deleteLater()
                theme.deleteLater()
                self.app.sendPostedEvents()
                self.app.processEvents()


if __name__ == "__main__":
    unittest.main()

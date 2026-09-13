from pathlib import Path
import unittest

from PySide6.QtCore import QObject, QPoint, QPointF, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from thlib.ui.localization import CatalogTranslator


ROOT = Path(__file__).resolve().parents[1]


class _CheckinDialogController(QObject):
    checkinFilesRequested = Signal()
    revisionCheckinConfirmationRequested = Signal()
    multiFileCheckinModeRequested = Signal(int)

    def __init__(self):
        super().__init__()
        self.multi_file_choices = []

    @Slot("QVariantList")
    def submit_checkin_files(self, _values):
        pass

    @Slot(bool)
    def resolve_revision_checkin(self, _accepted):
        pass

    @Slot(str)
    def resolve_multi_file_checkin(self, mode):
        self.multi_file_choices.append(mode)


class ItemCheckinDialogsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def setUp(self):
        qml_dir = ROOT / "thlib" / "ui" / "qml"
        self.translator = CatalogTranslator(
            qml_dir.parent / "translations" / "ru.json"
        )
        self.app.installTranslator(self.translator)
        self.engine = QQmlEngine()
        self.controller = _CheckinDialogController()
        theme_component = QQmlComponent(
            self.engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        self.theme = theme_component.createWithInitialProperties({"dark": True})
        self.component = QQmlComponent(
            self.engine,
            QUrl.fromLocalFile(str(qml_dir / "ItemCheckinDialogs.qml")),
        )
        self.dialogs = self.component.createWithInitialProperties({
            "theme": self.theme,
            "applicationController": self.controller,
        })
        self.assertIsNotNone(
            self.dialogs,
            "\n".join(error.toString() for error in self.component.errors()),
        )
        self.window = QQuickWindow()
        self.window.resize(560, 280)
        self.dialogs.setParentItem(self.window.contentItem())
        self.dialogs.setWidth(560)
        self.dialogs.setHeight(280)
        self.window.show()
        QTest.qWait(30)

    def tearDown(self):
        self.window.close()
        self.dialogs.deleteLater()
        self.window.deleteLater()
        self.app.processEvents()
        self.app.removeTranslator(self.translator)

    def _click(self, object_name):
        button = self.dialogs.findChild(QQuickItem, object_name)
        self.assertIsNotNone(button)
        center = button.mapToScene(QPointF(
            button.width() / 2, button.height() / 2
        ))
        QTest.mouseClick(
            self.window,
            Qt.LeftButton,
            Qt.NoModifier,
            QPoint(round(center.x()), round(center.y())),
        )
        QTest.qWait(20)

    def test_multiple_file_question_routes_all_three_choices(self):
        dialog = self.dialogs.findChild(QObject, "multiFileCheckinDialog")
        self.assertIsNotNone(dialog)

        self.controller.multiFileCheckinModeRequested.emit(3)
        QTest.qWait(20)
        self.assertTrue(dialog.property("opened"))
        self.assertEqual(dialog.property("fileCount"), 3)
        self._click("multiFileCheckinGroupButton")
        self.assertEqual(self.controller.multi_file_choices, ["group"])

        self.controller.multiFileCheckinModeRequested.emit(2)
        QTest.qWait(20)
        self._click("multiFileCheckinSeparateButton")
        self.assertEqual(
            self.controller.multi_file_choices, ["group", "individual"]
        )

        self.controller.multiFileCheckinModeRequested.emit(4)
        QTest.qWait(20)
        self._click("multiFileCheckinCancelButton")
        self.assertEqual(
            self.controller.multi_file_choices,
            ["group", "individual", "cancel"],
        )

    def test_question_stays_inside_narrow_and_wide_windows(self):
        dialog = self.dialogs.findChild(QObject, "multiFileCheckinDialog")
        for width in (360, 720):
            with self.subTest(width=width):
                self.window.resize(width, 280)
                self.dialogs.setWidth(width)
                self.app.processEvents()
                self.controller.multiFileCheckinModeRequested.emit(12)
                QTest.qWait(20)
                self.assertLessEqual(dialog.property("width"), width - 32)
                for object_name in (
                    "multiFileCheckinGroupButton",
                    "multiFileCheckinSeparateButton",
                    "multiFileCheckinCancelButton",
                ):
                    button = self.dialogs.findChild(QQuickItem, object_name)
                    top_left = button.mapToScene(QPointF(0, 0))
                    bottom_right = button.mapToScene(QPointF(
                        button.width(), button.height()
                    ))
                    self.assertGreaterEqual(top_left.x(), 0)
                    self.assertLessEqual(bottom_right.x(), width)
                self._click("multiFileCheckinCancelButton")


if __name__ == "__main__":
    unittest.main()

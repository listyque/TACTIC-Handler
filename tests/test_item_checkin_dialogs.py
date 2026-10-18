from pathlib import Path
import unittest

from PySide6.QtCore import QObject, QPoint, QPointF, Qt, QUrl, Signal, Slot, QEvent, Property
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from thlib.ui.localization import CatalogTranslator


ROOT = Path(__file__).resolve().parents[1]
QML = ROOT / "thlib/ui/qml"


def visual(item, name):
    if item.objectName() == name:
        return item
    for child in item.childItems():
        result = visual(child, name)
        if result is not None:
            return result


class _Locale(QObject):
    @Property(str, constant=True)
    def current_language(self):
        return "ru"


class _CheckinDialogController(QObject):
    checkinFilesRequested = Signal()
    revisionCheckinConfirmationRequested = Signal()
    multiFileCheckinModeRequested = Signal(int)

    def __init__(self):
        super().__init__()
        self.multi_file_choices = []
        self.revision_choices = []

    @Slot("QVariantList")
    def submit_checkin_files(self, _values):
        pass

    @Slot(bool)
    def resolve_revision_checkin(self, accepted):
        self.revision_choices.append(accepted)

    @Slot(str)
    def resolve_multi_file_checkin(self, mode):
        self.multi_file_choices.append(mode)


class ItemCheckinDialogsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def setUp(self):
        qml_dir = QML
        self.translator = CatalogTranslator(
            ROOT / "thlib/ui/translations/ru.json"
        )
        self.app.installTranslator(self.translator)
        self.engine = QQmlEngine()
        self.warnings = []
        self.engine.warnings.connect(lambda errors: self.warnings.extend(str(error) for error in errors))
        self.locale = _Locale()
        self.locale.setParent(self.engine)
        self.engine.rootContext().setContextProperty("localizationController", self.locale)
        self.controller = _CheckinDialogController()
        self.controller.setParent(self.engine)
        theme_component = QQmlComponent(
            self.engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        self.theme = theme_component.createWithInitialProperties({"dark": True})
        self.theme.setParent(self.engine)
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
        try:
            self.assertEqual(self.warnings, [])
        finally:
            self.window.close()
            for value in (self.dialogs, self.window, self.theme, self.engine):
                value.deleteLater()
            self.app.sendPostedEvents(None, QEvent.DeferredDelete)
            self.app.processEvents()
            self.app.removeTranslator(self.translator)

    def _click(self, object_name):
        button = visual(self.window.contentItem(), object_name)
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

    def test_revision_confirmation_requires_a_choice(self):
        self.controller.revisionCheckinConfirmationRequested.emit()
        QTest.qWait(20)
        dialog = self.dialogs.findChild(QObject, "revisionCheckinDialog")
        self.assertTrue(dialog.property("opened"))
        QTest.keyClick(self.window, Qt.Key_Escape)
        self.assertTrue(dialog.property("opened"))
        self._click("revisionCheckinCancel")
        self.assertEqual(self.controller.revision_choices, [False])
        self.controller.revisionCheckinConfirmationRequested.emit()
        QTest.qWait(20)
        self._click("revisionCheckinAccept")
        self.assertEqual(self.controller.revision_choices, [False, True])

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
                    button = visual(self.window.contentItem(), object_name)
                    top_left = button.mapToScene(QPointF(0, 0))
                    bottom_right = button.mapToScene(QPointF(
                        button.width(), button.height()
                    ))
                    self.assertGreaterEqual(top_left.x(), 0)
                    self.assertLessEqual(bottom_right.x(), width)
                self._click("multiFileCheckinCancelButton")


if __name__ == "__main__":
    unittest.main()

import json
import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
from PySide6.QtCore import QPointF, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlEngine, QQmlComponent
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
from tests.test_ingest_files import _Application
from tests.profile_ui_responsiveness import frame
from thlib.ui.ingest import IngestFilesController

QML = Path(__file__).resolve().parents[1] / "thlib/ui/qml"


def visual(item, name):
    if item.objectName() == name:
        return item
    for child in item.childItems():
        result = visual(child, name)
        if result is not None:
            return result


class FrameIngestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def test_native_owner_actions_inputs_conflicts_and_virtualization(self):
        application = _Application()
        controller = IngestFilesController(application)
        controller._target_search_type = "cg/shot"
        controller._replace_rules(
            [
                {
                    "code": "saved",
                    "__search_key__": "config/ingest_rule?code=saved",
                    "title": "Saved rule",
                    "data": json.dumps({"process": "render"}),
                }
            ]
        )
        controller.files.replace(
            [
                {
                    "path": str(index),
                    "title": f"file_{index}.exr",
                    "extension": "exr",
                    "status": "Ready",
                    "error": "Example error" if index == 1 else "",
                }
                for index in range(1000)
            ]
        )
        engine = QQmlEngine()
        warnings = []
        engine.warnings.connect(
            lambda errors: warnings.extend(str(error) for error in errors)
        )
        for key, value in {
            "ingestFilesController": controller,
            "ingestFileModel": controller.files,
            "ingestRuleModel": controller.rules,
            "windowModel": application.window_model,
        }.items():
            engine.rootContext().setContextProperty(key, value)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "IngestFilesView.qml"))
        )
        view = component.createWithInitialProperties({"theme": theme})
        self.assertIsNotNone(
            view, "\n".join(str(error) for error in component.errors())
        )
        window = QQuickWindow()
        view.setParentItem(window.contentItem())
        window.show()

        def click(name):
            item = visual(window.contentItem(), name)
            self.assertIsNotNone(item, name)
            QTest.mouseClick(
                window,
                Qt.LeftButton,
                pos=item.mapToScene(
                    QPointF(item.width() / 2, item.height() / 2)
                ).toPoint(),
            )
            frame(window)

        try:
            for width, height in ((1000, 700), (680, 760), (390, 700)):
                window.resize(width, height)
                view.setWidth(width)
                view.setHeight(height)
                frame(window)
                left, right = (
                    visual(view, "ingestFilesPanel"),
                    visual(view, "ingestRulePanel"),
                )
                self.assertIsNotNone(left)
                self.assertIsNotNone(right)
                for item in (left, right):
                    point = item.mapToScene(QPointF(0, 0))
                    self.assertGreaterEqual(point.x(), 0)
                    self.assertLessEqual(point.x() + item.width(), width)
                    self.assertLessEqual(point.y() + item.height(), height - 58)
            window.resize(1000, 700)
            view.setWidth(1000)
            view.setHeight(700)
            frame(window)
            lst = visual(view, "ingestFilesList")
            self.assertLess(len(lst.property("contentItem").childItems()), 100)
            self.assertEqual(visual(view, "ingestFile_1").height(), 62)
            click("ingestRule_saved")
            self.assertEqual(controller.options["process"], "render")
            click("ingestAdvanced")
            field = visual(view, "ingestOption_filter")
            QTest.mouseClick(
                window,
                Qt.LeftButton,
                pos=field.mapToScene(QPointF(15, field.height() / 2)).toPoint(),
            )
            for char in ".exr":
                QTest.keyClick(window, Qt.Key(ord(char.upper())))
            frame(window)
            self.assertEqual(controller.options["filter"], ".exr")
            click("ingestFileRemove_0")
            self.assertEqual(controller.fileCount, 999)
            controller._generation = 1
            controller._preflight.pending = {
                "generation": 1,
                "job": {"paths": ["file.exr"], "options": {}},
                "conflicts": [{"path": "file.exr", "name": "file"}],
                "existingByPath": {"file.exr": ["cg/shot?code=SHOT001"]},
                "canUpdate": True,
            }
            controller.stateChanged.emit()
            frame(window)
            click("ingestConflict_cancel")
            self.assertFalse(controller.conflictPending)
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

import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Material")

from PySide6.QtCore import QObject, Property, QUrl, Signal, Slot
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow

from thlib.ui.workspace_models.records import RecordListModel
from tests.qt_application import gui_test_application


ROOT = Path(__file__).resolve().parents[1]
QML = ROOT / "thlib/ui/qml"


class _PresetController(QObject):
    stateChanged = Signal()

    def __init__(self):
        super().__init__()
        self.records = RecordListModel((
            "code", "view", "title", "panelCount", "assignedCount",
            "valid", "error",
        ))
        self.records.replace([{
            "code": "CONFIG0001",
            "view": "workspace_layout@review",
            "title": "Review",
            "panelCount": 12,
            "assignedCount": 2,
            "valid": True,
            "error": "",
        }])

    @Property(QObject, constant=True)
    def model(self):
        return self.records

    @Property(bool, notify=stateChanged)
    def busy(self):
        return False

    @Property(bool, notify=stateChanged)
    def canManage(self):
        return True

    @Property(str, notify=stateChanged)
    def error(self):
        return ""

    @Slot()
    def refresh(self):
        pass

    @Slot(str, result=bool)
    def apply_preset(self, _view):
        return True

    @Slot(str)
    def update(self, _view):
        pass

    @Slot(str)
    def delete_preset(self, _view):
        pass

    @Slot(str)
    def save_as(self, _title):
        pass


class WorkspaceLayoutPresetQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def test_menu_section_creates_real_preset_actions_without_warnings(self):
        controller = _PresetController()
        engine = QQmlEngine()
        warnings = []
        engine.warnings.connect(
            lambda errors: warnings.extend(
                error.toString() for error in errors
            )
        )
        engine.rootContext().setContextProperty(
            "presetController", controller,
        )
        component = QQmlComponent(engine)
        component.setData(b'''
import QtQuick
import QtQuick.Controls
import "." as App
ApplicationWindow {
    width: 420
    height: 620
    visible: true
    App.Theme {
        id: theme
        dark: true
        clickAnimationsEnabled: false
        hoverAnimationsEnabled: false
        fadeAnimationsEnabled: false
        popupAnimationsEnabled: false
    }
    App.WorkspaceLayoutPresetMenuSection {
        width: 300
        theme: theme
        controller: presetController
    }
}
''', QUrl.fromLocalFile(str(QML / "_WorkspaceLayoutPresetTest.qml")))
        window = component.create()
        self.assertIsNotNone(
            window,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            self.app.processEvents()
            section = window.findChild(
                QObject, "workspaceLayoutPresetMenuSection",
            )
            save = window.findChild(
                QObject, "saveWorkspaceLayoutPreset",
            )
            self.assertIsNotNone(section)
            self.assertIsNotNone(save)
            self.assertTrue(save.property("visible"))
            self.assertGreater(section.property("height"), 100)
            self.assertEqual(warnings, [])
        finally:
            window.close()
            window.deleteLater()
            engine.deleteLater()
            self.app.processEvents()


if __name__ == "__main__":
    unittest.main()

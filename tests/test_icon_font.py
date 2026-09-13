import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, Property, QUrl, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine

from thlib.ui.icon_font import qml_icon_bindings


ROOT = Path(__file__).resolve().parents[1]
QML = ROOT / "thlib" / "ui" / "qml"


class _IconSettings(QObject):
    changed = Signal()

    @Property(str, notify=changed)
    def icon_set(self):
        return "automatic"


class IconFontCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.bindings = qml_icon_bindings(ROOT, cls.app)
        cls.catalog = cls.bindings["iconFontCatalog"]

    def test_complete_bundled_catalogs_are_available_to_pickers(self):
        self.assertEqual(len(self.catalog.search("material-design", "")), 7448)
        self.assertEqual(len(self.catalog.search("fluent-regular", "")), 2819)
        self.assertEqual(len(self.catalog.search("fluent-filled", "")), 2859)

    def test_search_and_resolution_use_normalized_names(self):
        matches = self.catalog.search("fluent-regular", "folder open")
        self.assertIn("folder-open", matches)
        icon = self.catalog.resolve("fluent-regular", "folder_open")
        self.assertTrue(icon["glyph"])
        self.assertTrue(icon["fontFamily"])

    def test_picker_sets_keep_tactic_and_local_fonts_distinct(self):
        values = [record["value"] for record in self.catalog.sets]
        self.assertEqual(values, [
            "fontawesome-solid",
            "fontawesome-outline",
            "material-design",
            "fluent-regular",
            "fluent-filled",
        ])

    def test_picker_qualifies_local_icons_but_keeps_tactic_names_plain(self):
        engine = QQmlEngine()
        engine.rootContext().setContextProperty(
            "appController", _IconSettings(engine)
        )
        for name, value in qml_icon_bindings(ROOT, engine).items():
            engine.rootContext().setContextProperty(name, value)
        component = QQmlComponent(engine)
        component.setData(b'''
import QtQuick
import "." as App
Item {
    width: 640; height: 480
    App.Theme { id: theme; dark: true }
    App.IconPickerButton {
        id: localPicker; objectName: "localPicker"; theme: theme
        Component.onCompleted: rebuildSets()
    }
    App.IconPickerButton {
        id: tacticPicker; objectName: "tacticPicker"; theme: theme
        tacticCompatibleOnly: true
        Component.onCompleted: rebuildSets()
    }
    property string localStored: localPicker.storedIconName("camera")
    property string tacticStored: tacticPicker.storedIconName("camera")
}
''', QUrl.fromLocalFile(str(QML / "_IconPickerTest.qml")))
        root = component.create()
        self.assertIsNotNone(
            root,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            self.app.processEvents()
            local_picker = root.findChild(QObject, "localPicker")
            tactic_picker = root.findChild(QObject, "tacticPicker")
            self.assertEqual(
                local_picker.property("activeSet"), "material-design"
            )
            self.assertEqual(
                root.property("localStored"), "material-design:camera"
            )
            self.assertEqual(
                tactic_picker.property("activeSet"), "fontawesome-solid"
            )
            self.assertEqual(root.property("tacticStored"), "camera")
        finally:
            root.deleteLater()
            engine.deleteLater()


if __name__ == "__main__":
    unittest.main()

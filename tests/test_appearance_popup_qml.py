import re
import unittest
from pathlib import Path
from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent


class AppearancePopupQmlContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main_source = Path("thlib/ui/qml/Main.qml").read_text(
            encoding="utf-8"
        )
        cls.popup_source = Path("thlib/ui/qml/AppearancePopup.qml").read_text(
            encoding="utf-8"
        )

    def test_appearance_button_in_main(self):
        self.assertIn("id: appearanceButton", self.main_source)
        self.assertIn('toolTip: qsTr("Appearance")', self.main_source)
        self.assertIn('iconName: "theme_mode"', self.main_source)
        self.assertIn("appearancePopup.toggleBelow(appearanceButton)", self.main_source)
        self.assertIn("window.closeTopBarPopups(appearancePopup)", self.main_source)
        self.assertIn("appearancePopup.opened", self.main_source)

    def test_appearance_popup_structure(self):
        self.assertIn("Controls.ScrollablePopup", self.popup_source)
        self.assertIn('objectName: "appearanceLanguageCombo"', self.popup_source)
        self.assertIn('objectName: "appearanceThemeStyleCombo"', self.popup_source)
        self.assertIn('objectName: "appearanceColorModeCombo"', self.popup_source)
        self.assertIn('objectName: "appearanceIconSetCombo"', self.popup_source)
        self.assertIn("set_language", self.popup_source)
        self.assertIn("set_theme_style", self.popup_source)
        self.assertIn("set_dark_theme", self.popup_source)
        self.assertIn("set_icon_set", self.popup_source)

    def test_no_color_literals_in_appearance_popup(self):
        color_literal = re.compile(r"#[0-9a-fA-F]{3,8}")
        matches = color_literal.findall(self.popup_source)
        self.assertEqual(matches, [])

    def test_appearance_popup_compiles(self):
        app = QGuiApplication.instance() or QGuiApplication([])
        engine = QQmlApplicationEngine()
        engine.addImportPath("thlib/ui/qml")
        comp = QQmlComponent(engine, QUrl.fromLocalFile("thlib/ui/qml/AppearancePopup.qml"))
        self.assertEqual(comp.status(), QQmlComponent.Status.Ready, [e.toString() for e in comp.errors()])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, Property, QUrl, Signal
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine

from thlib.ui.theme_catalog import (
    ACCENT_PRESETS,
    accent_color,
    base_color,
)
from thlib.ui.icon_font import (
    qml_icon_bindings,
)


class _IconSettings(QObject):
    icon_set_changed = Signal(str)

    def __init__(self, value):
        super().__init__()
        self._value = value

    @Property(str, notify=icon_set_changed)
    def icon_set(self):
        return self._value

    def set_value(self, value):
        self._value = value
        self.icon_set_changed.emit(value)


class ThemeQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = (
            QGuiApplication.instance() or QGuiApplication([])
        )
        cls.qml = Path(__file__).parents[1] / "thlib" / "ui" / "qml"

    def test_theme_uses_supplied_accent_for_all_primary_roles(self):
        engine = QQmlEngine()
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(self.qml / "Theme.qml"))
        )
        theme = component.createWithInitialProperties({
            "dark": True,
            "styleName": "fluent",
            "accentColor": QColor("#de786b"),
        })
        self.assertIsNotNone(
            theme,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            self.assertEqual(
                theme.property("action").name().lower(), "#de786b"
            )
            self.assertEqual(
                theme.property("primary").name().lower(), "#de786b"
            )
            self.assertNotEqual(
                theme.property("selected").name().lower(), "#de786b"
            )
        finally:
            theme.deleteLater()

    def test_palette_preset_supplies_base_and_accent_for_each_mode(self):
        self.assertEqual(accent_color("violet", True), "#b49ac8")
        self.assertEqual(base_color("violet", True), "#322d36")
        self.assertEqual(accent_color("steel", False), "#3d7599")
        self.assertEqual(base_color("steel", False), "#d4dce1")
        for preset in ACCENT_PRESETS:
            self.assertIn("lightBase", preset)
            self.assertIn("darkBase", preset)

    def test_theme_base_color_changes_all_surface_roles(self):
        engine = QQmlEngine()
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(self.qml / "Theme.qml"))
        )
        common = {
            "dark": True,
            "styleName": "md3",
            "accentColor": QColor("#78a6c4"),
        }
        steel = component.createWithInitialProperties({
            **common,
            "baseColor": QColor("#292d30"),
        })
        violet = component.createWithInitialProperties({
            **common,
            "baseColor": QColor("#322d36"),
        })
        self.assertIsNotNone(
            steel,
            "\n".join(error.toString() for error in component.errors()),
        )
        self.assertIsNotNone(
            violet,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            for role in (
                "workspace", "topBar", "toolBar", "panel",
                "panelRaised", "panelDeep", "row", "rowHover",
            ):
                self.assertNotEqual(
                    steel.property(role).name().lower(),
                    violet.property(role).name().lower(),
                    role,
                )
            self.assertEqual(
                steel.property("action").name().lower(), "#78a6c4"
            )
        finally:
            steel.deleteLater()
            violet.deleteLater()

    def test_animation_preferences_zero_only_their_runtime_tokens(self):
        engine = QQmlEngine()
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(self.qml / "Theme.qml"))
        )
        theme = component.createWithInitialProperties({
            "dark": True,
            "clickAnimationsEnabled": False,
            "hoverAnimationsEnabled": False,
            "fadeAnimationsEnabled": False,
            "popupAnimationsEnabled": False,
        })
        self.assertIsNotNone(
            theme,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            self.assertGreater(theme.property("baseMotionFast"), 0)
            for token in (
                "motionInstant", "motionFast", "motionMedium",
                "motionSlow", "motionExtended", "clickMotionInstant",
                "clickMotionFast", "clickMotionMedium",
                "clickMotionSlow", "clickMotionExtended",
                "hoverMotionFast", "hoverMotionMedium",
                "popupMotionFast", "popupMotionMedium", "popupMotionSlow",
            ):
                self.assertEqual(theme.property(token), 0, token)

            theme.setProperty("clickAnimationsEnabled", True)
            self.assertGreater(theme.property("clickMotionFast"), 0)
            self.assertEqual(theme.property("hoverMotionFast"), 0)
            self.assertEqual(theme.property("motionFast"), 0)
            self.assertEqual(theme.property("popupMotionFast"), 0)
            theme.setProperty("popupAnimationsEnabled", True)
            self.assertGreater(theme.property("popupMotionFast"), 0)
            self.assertEqual(theme.property("motionFast"), 0)
            self.assertEqual(theme.property("hoverMotionFast"), 0)
        finally:
            theme.deleteLater()

    def test_content_selection_text_uses_its_own_background_contrast(self):
        engine = QQmlEngine()
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(self.qml / "Theme.qml"))
        )
        themes = []
        try:
            for preset in ACCENT_PRESETS:
                for dark in (False, True):
                    theme = component.createWithInitialProperties({
                        "dark": dark,
                        "styleName": "md3",
                        "accentColor": QColor(
                            preset["dark" if dark else "light"]
                        ),
                        "baseColor": QColor(
                            preset["darkBase" if dark else "lightBase"]
                        ),
                    })
                    self.assertIsNotNone(
                        theme,
                        "\n".join(
                            error.toString() for error in component.errors()
                        ),
                    )
                    themes.append(theme)
                    background = theme.property("contentSelection")
                    luminance = (
                        background.redF() * 0.2126
                        + background.greenF() * 0.7152
                        + background.blueF() * 0.0722
                    )
                    expected = "#172027" if luminance > 0.56 else "#f6f8fa"
                    self.assertEqual(
                        theme.property("contentSelectionText").name().lower(),
                        expected,
                        f"{preset['value']} dark={dark}",
                    )
        finally:
            for theme in themes:
                theme.deleteLater()

    def test_accent_picker_wraps_all_presets_at_configuration_width(self):
        engine = QQmlEngine()
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(self.qml / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(
                self.qml / "controls" / "AccentPresetPicker.qml"
            )),
        )
        picker = component.createWithInitialProperties({
            "theme": theme,
            "model": [dict(record) for record in ACCENT_PRESETS],
            "currentValue": "violet",
            "darkPreview": True,
            "width": 360,
        })
        self.assertIsNotNone(
            picker,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            for _pass in range(4):
                self.application.processEvents()
            self.assertGreaterEqual(picker.property("implicitHeight"), 120)
            self.assertEqual(picker.property("currentValue"), "violet")
        finally:
            picker.deleteLater()
            theme.deleteLater()

    def test_material_icon_switches_between_bundled_font_sets(self):
        engine = QQmlEngine()
        project_root = Path(__file__).parents[1]
        bindings = qml_icon_bindings(project_root, engine)
        solid_family = bindings["fontAwesomeSolidFontFamily"]
        regular_family = bindings["fontAwesomeRegularFontFamily"]
        material_family = bindings["materialDesignIconFontFamily"]
        fluent_family = bindings["iconFontCatalog"].resolve(
            "fluent-regular", "settings"
        )["fontFamily"]
        settings = _IconSettings("material-design")
        context = engine.rootContext()
        context.setContextProperty("appController", settings)
        for name, value in bindings.items():
            context.setContextProperty(name, value)
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(
                self.qml / "controls" / "MaterialIcon.qml"
            )),
        )
        icon = component.createWithInitialProperties({
            "name": "settings",
            "size": 24,
            "color": "#ffffff",
        })
        self.assertIsNotNone(
            icon,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            self.application.processEvents()
            glyph = icon.findChild(QObject, "materialIconGlyph")
            self.assertIsNotNone(glyph)
            self.assertEqual(glyph.property("font").family(), material_family)
            self.assertTrue(glyph.property("text"))
            material_size = glyph.property("font").pixelSize()
            self.assertEqual(icon.property("implicitWidth"), 24)
            self.assertEqual(icon.property("implicitHeight"), 24)

            for icon_name in """
                account-circle account-tree add add-photo-alternate
                add_alarm add_task address-book bar_chart bolt book-open
                calendar cloud-upload-alt code commit_queue
                dashboard_customize description donut-small dynamic_feed
                edit edit_note emoji envelope error exclamation-circle
                filter_alt_off group-items hub info input language list-ul
                lock manage-accounts memory milestone mouse naming-editor
                notifications photo_library play-selection project-diagram
                push-pin route rule save schedule schema search sensors
                settings-suggest shapes stream sync_problem system-activity
                system_activity tags task tasks terminal times type
                ui-performance unlock-alt upload user users visibility
                workflow zoom-in zoom-out
            """.split():
                icon.setProperty("name", icon_name)
                self.application.processEvents()
                self.assertEqual(
                    glyph.property("font").family(),
                    material_family,
                    icon_name,
                )

            settings.set_value("automatic")
            for icon_name in (
                "terminal", "type", "play-selection", "save", "code",
            ):
                icon.setProperty("name", icon_name)
                self.application.processEvents()
                self.assertEqual(
                    glyph.property("font").family(),
                    material_family,
                    icon_name,
                )

            settings.set_value("fontawesome-solid")
            self.application.processEvents()
            self.assertEqual(glyph.property("font").family(), solid_family)
            self.assertTrue(glyph.property("text"))
            fontawesome_size = glyph.property("font").pixelSize()
            self.assertGreater(material_size, fontawesome_size)

            icon.setProperty("name", "emoji")
            settings.set_value("automatic")
            self.application.processEvents()
            self.assertEqual(glyph.property("font").family(), material_family)

            settings.set_value("fontawesome-outline")
            self.application.processEvents()
            self.assertEqual(glyph.property("font").family(), regular_family)

            settings.set_value("fluent-regular")
            self.application.processEvents()
            self.assertEqual(glyph.property("font").family(), fluent_family)
            fluent_size = glyph.property("font").pixelSize()
            self.assertGreater(fluent_size, fontawesome_size)

            settings.set_value("fluent-filled")
            self.application.processEvents()
            self.assertEqual(glyph.property("font").family(), fluent_family)

            settings.set_value("material-design")
            icon.setProperty("name", "unavailable")
            self.application.processEvents()
            self.assertEqual(glyph.property("font").family(), fluent_family)
            self.assertEqual(glyph.property("font").pixelSize(), fluent_size)

            settings.set_value("fontawesome-solid")
            icon.setProperty("name", "material-design:ab-testing")
            self.application.processEvents()
            self.assertEqual(glyph.property("font").family(), material_family)
            self.assertEqual(glyph.property("font").pixelSize(), material_size)
            self.assertEqual(icon.property("implicitWidth"), 24)
            self.assertEqual(icon.property("implicitHeight"), 24)

            icon.setProperty("name", "swap_horiz")
            self.application.processEvents()
            self.assertEqual(
                glyph.property("fontAwesomeName"), "exchange-alt"
            )
            self.assertNotEqual(
                glyph.property("resolvedName"), "exclamation-triangle"
            )
            self.assertTrue(glyph.property("text"))

            icon.setProperty("name", "book-open")
            self.application.processEvents()
            self.assertEqual(
                glyph.property("fontAwesomeName"), "book-open"
            )
            self.assertEqual(glyph.property("resolvedName"), "book-open")
            self.assertTrue(glyph.property("text"))

            icon.setProperty("name", "create-article")
            for icon_set, family in (
                ("fontawesome-solid", solid_family),
                ("fontawesome-outline", regular_family),
                ("material-design", material_family),
                ("fluent-regular", fluent_family),
                ("fluent-filled", fluent_family),
            ):
                settings.set_value(icon_set)
                self.application.processEvents()
                self.assertEqual(glyph.property("font").family(), family)
                self.assertTrue(glyph.property("text"))

            for icon_name in (
                "format-paragraph",
                "format-header-1",
                "format-header-2",
                "format-header-3",
                "format-header-4",
                "format-header-5",
                "format-header-6",
                "format-quote",
                "code-block",
                "small-text",
                "divider",
                "table-view",
                "checkbox-multiple-marked-outline",
                "attachments-editor",
            ):
                icon.setProperty("name", icon_name)
                for icon_set, family in (
                    ("material-design", material_family),
                    ("fluent-regular", fluent_family),
                    ("fluent-filled", fluent_family),
                ):
                    settings.set_value(icon_set)
                    self.application.processEvents()
                    self.assertEqual(glyph.property("font").family(), family)
                    self.assertTrue(glyph.property("text"))
        finally:
            icon.deleteLater()


if __name__ == "__main__":
    unittest.main()

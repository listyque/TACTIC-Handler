import json
from pathlib import Path
import unittest

from thlib.ui.theme_catalog import (
    ACCENT_PRESETS,
    DEFAULT_THEME_ACCENTS,
    ICON_SETS,
    THEME_STYLES,
    accent_color,
    normalize_icon_set,
    normalize_theme_accents,
    normalize_theme_style,
)


class ThemeCatalogTests(unittest.TestCase):
    def test_catalog_values_are_unique(self):
        values = [record["value"] for record in THEME_STYLES]
        self.assertEqual(len(values), len(set(values)))
        self.assertEqual(values[0], "md3")

    def test_unknown_style_falls_back_to_md3(self):
        self.assertEqual(normalize_theme_style("unknown"), "md3")
        self.assertEqual(normalize_theme_style(None), "md3")

    def test_supported_styles_are_preserved(self):
        for record in THEME_STYLES:
            self.assertEqual(
                normalize_theme_style(record["value"]), record["value"]
            )

    def test_nineteen_palette_presets_define_light_and_dark_colors(self):
        self.assertEqual(len(ACCENT_PRESETS), 19)
        values = [record["value"] for record in ACCENT_PRESETS]
        self.assertEqual(len(values), len(set(values)))
        for record in ACCENT_PRESETS:
            self.assertRegex(record["light"], r"^#[0-9a-f]{6}$")
            self.assertRegex(record["dark"], r"^#[0-9a-f]{6}$")
            self.assertNotEqual(record["light"], record["dark"])

    def test_neutral_palette_family_has_distinct_base_shades(self):
        neutral_ids = ("silver", "ash", "graphite", "charcoal")
        records = {
            record["value"]: record for record in ACCENT_PRESETS
            if record["value"] in neutral_ids
        }
        self.assertEqual(tuple(records), neutral_ids)
        self.assertEqual(
            len({record["lightBase"] for record in records.values()}), 4
        )
        self.assertEqual(
            len({record["darkBase"] for record in records.values()}), 4
        )

    def test_accents_are_normalized_per_style_and_color_mode(self):
        values = normalize_theme_accents({
            "md3": {"light": "coral", "dark": "cyan"},
            "fluent": {"light": "unknown", "dark": "rose"},
        })

        self.assertEqual(values["md3"], {
            "light": "coral", "dark": "cyan",
        })
        self.assertEqual(values["fluent"]["light"], "azure")
        self.assertEqual(values["fluent"]["dark"], "rose")
        self.assertEqual(
            values["material5"], DEFAULT_THEME_ACCENTS["material5"]
        )
        self.assertEqual(accent_color("coral", False), "#a4483c")
        self.assertEqual(accent_color("coral", True), "#de786b")

    def test_icon_set_catalog_is_normalized(self):
        values = [record["value"] for record in ICON_SETS]
        self.assertEqual(len(values), len(set(values)))
        self.assertIn("material-design", values)
        self.assertIn("fluent-regular", values)
        self.assertIn("fluent-filled", values)
        self.assertEqual(
            normalize_icon_set("fontawesome-solid"),
            "fontawesome-solid",
        )
        self.assertEqual(normalize_icon_set(None), "material-design")
        self.assertEqual(normalize_icon_set("unknown"), "material-design")

    def test_user_facing_catalog_labels_have_russian_translations(self):
        catalog = json.loads(
            (
                Path(__file__).parents[1]
                / "thlib" / "ui" / "translations" / "ru.json"
            ).read_text(encoding="utf-8")
        )
        messages = {
            record[field]
            for records in (ACCENT_PRESETS, ICON_SETS)
            for record in records
            for field in ("label", "description")
            if field in record
        }
        self.assertEqual(messages - catalog.keys(), set())


if __name__ == "__main__":
    unittest.main()

import unittest

from modern_ui.theme_catalog import THEME_STYLES, normalize_theme_style


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


if __name__ == "__main__":
    unittest.main()

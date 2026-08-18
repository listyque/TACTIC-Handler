from pathlib import Path
import ast
import json
import re
import unittest

from modern_ui.localization import CatalogTranslator, normalize_language
from modern_ui.configuration import ConfigurationController


class LocalizationTests(unittest.TestCase):
    _ROOT = Path(__file__).parents[1]

    def test_language_codes_are_normalized(self):
        self.assertEqual(normalize_language("ru_RU"), "ru")
        self.assertEqual(normalize_language("en-US"), "en")
        self.assertEqual(normalize_language("unknown"), "en")

    def test_configuration_keeps_normalized_language(self):
        values = ConfigurationController._normalize_global({
            "language": "ru_RU",
            "themeStyle": "md3",
        })
        self.assertEqual(values["language"], "ru")

    def test_russian_catalog_translates_and_falls_back(self):
        catalog = self._ROOT / "modern_ui" / "translations" / "ru.json"
        translator = CatalogTranslator(catalog)
        self.assertEqual(
            translator.translate("ModernUI", "Configuration"),
            "Конфигурация",
        )
        self.assertEqual(
            translator.translate("ModernUI", "Untranslated value"),
            "Untranslated value",
        )

    def test_project_search_type_names_are_not_translation_keys(self):
        catalog_path = (
            self._ROOT / "modern_ui" / "translations" / "ru.json"
        )
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        self.assertEqual(catalog["All"], "Все")
        self.assertNotIn("All Assets", catalog)
        self.assertNotIn("All Episodes", catalog)
        self.assertNotIn("All Scenes", catalog)
        self.assertNotIn("All Shots", catalog)
        self.assertNotIn("All Sequences", catalog)
        self.assertNotIn("Assets Category", catalog)
        self.assertNotIn("Tasks For: Reef", catalog)
        self.assertEqual(catalog["Task Manager"], "Диспетчер задач")

        dock_host = (
            self._ROOT / "modern_ui" / "qml" / "DockHost.qml"
        ).read_text(encoding="utf-8")
        self.assertIn('qsTr("Tasks for:")', dock_host)

        dock_menu = (
            self._ROOT / "modern_ui" / "qml" / "DockMenu.qml"
        ).read_text(encoding="utf-8")
        self.assertIn('panelRow.kind === "tasks"', dock_menu)
        self.assertIn('qsTr("Task Manager")', dock_menu)

        drawer_source = (
            self._ROOT / "modern_ui" / "qml" / "NavigationDrawer.qml"
        ).read_text(encoding="utf-8")
        sidebar_row_source = (
            self._ROOT / "modern_ui" / "qml" / "SidebarTreeRow.qml"
        ).read_text(encoding="utf-8")
        self.assertIn("SidebarTreeRow", drawer_source)
        self.assertIn("text: root.title", sidebar_row_source)
        self.assertNotIn("qsTr(root.title)", sidebar_row_source)

    def test_server_search_columns_are_not_translated(self):
        advanced_search = (
            self._ROOT / "modern_ui" / "qml" / "AdvancedSearchView.qml"
        ).read_text(encoding="utf-8")
        combo_box = (
            self._ROOT / "modern_ui" / "qml" / "controls"
            / "Md3ComboBox.qml"
        ).read_text(encoding="utf-8")

        self.assertRegex(
            advanced_search,
            r"model:\s*filterColumnModel[\s\S]{0,420}"
            r"translateDisplayText:\s*false",
        )
        self.assertIn(
            "text: control.translateDisplayText",
            combo_box,
        )
        self.assertIn(
            ": control.textAt(option.index)",
            combo_box,
        )

    def test_russian_catalog_is_valid_utf8_without_replacement_markers(self):
        catalog_path = (
            self._ROOT / "modern_ui" / "translations" / "ru.json"
        )
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        self.assertGreater(len(catalog), 650)
        for source, target in catalog.items():
            self.assertNotIn("??", target, source)
            self.assertNotIn("\ufffd", target, source)

    def test_literal_qml_messages_have_russian_catalog_entries(self):
        catalog_path = (
            self._ROOT / "modern_ui" / "translations" / "ru.json"
        )
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        pattern = re.compile(r'qsTr\(\s*"((?:\\.|[^"\\])*)"')
        messages = set()
        for path in (self._ROOT / "modern_ui" / "qml").rglob("*.qml"):
            messages.update(pattern.findall(path.read_text(encoding="utf-8")))
        technical_literals = {
            "@GET(snapshot.context) == publish",
            r"Loading more results\u2026",
            "PID ",
            "TACTIC-Handler",
            "http://server",
            "shot.001.exr",
            "{project.code}/{search_type.table_name}/{sobject.code}/versions",
            "{sobject.name}_v{version}.{ext}",
        }
        missing = {
            message for message in messages
            if message.strip()
            and any(character.isalpha() for character in message)
            and message not in catalog
            and message not in technical_literals
        }
        self.assertEqual(missing, set())

    def test_dynamic_menu_and_window_titles_have_russian_entries(self):
        catalog = json.loads(
            (self._ROOT / "modern_ui" / "translations" / "ru.json")
            .read_text(encoding="utf-8")
        )
        messages = set()

        menu_path = self._ROOT / "modern_ui" / "menu_schema.py"
        menu_tree = ast.parse(menu_path.read_text(encoding="utf-8"))
        for node in ast.walk(menu_tree):
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in {"action", "tool_action", "tool_header"}
            ):
                continue
            if (
                node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                messages.add(node.args[0].value)
            for keyword in node.keywords:
                if (
                    keyword.arg == "status"
                    and isinstance(keyword.value, ast.Constant)
                    and isinstance(keyword.value.value, str)
                ):
                    messages.add(keyword.value.value)

        item_actions_path = (
            self._ROOT / "modern_ui" / "controllers" / "item_actions.py"
        )
        item_actions_tree = ast.parse(
            item_actions_path.read_text(encoding="utf-8")
        )
        for node in ast.walk(item_actions_tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "item"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                messages.add(node.args[0].value)

        windows_path = (
            self._ROOT / "modern_ui" / "workspace_models" / "windows.py"
        )
        windows_tree = ast.parse(windows_path.read_text(encoding="utf-8"))
        for node in ast.walk(windows_tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "FloatingWindow"
                and len(node.args) > 1
                and isinstance(node.args[1], ast.Constant)
                and isinstance(node.args[1].value, str)
            ):
                messages.add(node.args[1].value)

        docks_path = (
            self._ROOT / "modern_ui" / "workspace_models" / "docks_records.py"
        )
        docks_tree = ast.parse(docks_path.read_text(encoding="utf-8"))
        for node in ast.walk(docks_tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "DockPanel"
                and len(node.args) > 1
                and isinstance(node.args[1], ast.Constant)
                and isinstance(node.args[1].value, str)
            ):
                messages.add(node.args[1].value)

        qml_menu_pattern = re.compile(
            r'["\']title["\']\s*:\s*(?:qsTr\()?\s*["\']([^"\']+)["\']'
        )
        for qml_path in (self._ROOT / "modern_ui" / "qml").rglob("*.qml"):
            messages.update(
                qml_menu_pattern.findall(qml_path.read_text(encoding="utf-8"))
            )

        self.assertEqual(
            {message for message in messages if message not in catalog},
            set(),
        )


if __name__ == "__main__":
    unittest.main()

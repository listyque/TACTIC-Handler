import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PySide6.QtCore import QObject, Property, Signal

from thlib.ui.help import HelpController
from thlib.ui.workspace_models.windows import FloatingWindowModel


ROOT = Path(__file__).resolve().parents[1]


class _Localization(QObject):
    languageChanged = Signal()

    def __init__(self, language="en"):
        super().__init__()
        self.language = language

    @Property(str, notify=languageChanged)
    def current_language(self):
        return self.language

    def use(self, language):
        self.language = language
        self.languageChanged.emit()


class HelpControllerTests(unittest.TestCase):
    def test_shipped_articles_are_complete_and_outside_ui_catalog(self):
        article_root = ROOT / "thlib" / "ui" / "help_articles"
        english = {path.name.removesuffix(".en.md") for path in article_root.glob("*.en.md")}
        russian = {path.name.removesuffix(".ru.md") for path in article_root.glob("*.ru.md")}
        self.assertEqual(english, russian)
        self.assertGreater(len(english), 40)

        localization = _Localization()
        controller = HelpController(article_root, localization)
        self.assertEqual(len(controller.topics), len(english))
        self.assertFalse(controller.error)
        localization.use("ru")
        self.assertEqual(len(controller.topics), len(russian))
        self.assertEqual(controller.article["title"], "Обзор")
        self.assertTrue(controller.article["summary"])
        self.assertFalse(controller.article["body"].lstrip().startswith(">"))

        configuration_topics = {
            "server_configuration",
            "repository_configuration",
            "configuration.projects",
            "configuration.checkin",
            "configuration.global",
            "appearance",
            "configuration.cache",
            "configuration.tasks",
            "configuration.maya",
            "commit_queue",
            "sidebar_editor",
        }
        self.assertTrue(configuration_topics.issubset({
            topic["id"] for topic in controller.topics
        }))

        dock_topics = {
            "dock.results", "dock.snapshot", "dock.tasks",
            "dock.description", "dock.notes", "dock.knowledge",
            "dock.task_calendar", "dock.timesheet", "dock.work_reports",
            "dock.cost_reports", "dock.drop_plate", "dock.advanced_search",
            "dock.repo_sync_queue", "dock.commit_queue",
            "dock.watch_folders", "dock.db_table",
        }
        self.assertTrue(dock_topics.issubset({
            topic["id"] for topic in controller.topics
        }))

        controller.select("dcc_clients")
        dcc_help = controller.article["body"]
        for section in (
            "## Подключение Maya",
            "## Выбор нужного клиента",
            "## Возможности Maya-клиента",
            "## Открытие, импорт и референс",
            "## Сохранение и чекин",
            "## Работа с TACTIC без зависания Maya",
            "## Триггеры DCC-скриптов",
            "## Диагностика",
            "## Добавление нового DCC",
        ):
            self.assertIn(section, dcc_help)
        for token in (
            "maya.startup", "get_current_scene", "prepare_checkin",
            "execute_custom_script", "TACTIC_SCRIPT_KWARGS",
            "th.submit", "BlockingCallError", "DCC_MANIFEST",
        ):
            self.assertIn(token, dcc_help)

        english_windows_help = (
            article_root / "windows.en.md"
        ).read_text(encoding="utf-8")
        for window in FloatingWindowModel._defaults():
            self.assertIn(window.title, english_windows_help)

        for topic_id, controls in {
            "server_configuration": (
                "Адрес сервера", "Проверить", "Создать тикет",
                "Проверка соединения", "Обновления сервера",
                "Пульс присутствия",
            ),
            "configuration.checkin": (
                "Доставка превью", "Метод Check-in", "Метод Check-out",
                "Проверять файлы по MD5", "Минимальная разрядность кадра",
            ),
            "configuration.cache": (
                "Кэшировать вкладки процессов", "Снапшоты и файлы",
                "Очистить все кэшированные серверные данные",
            ),
            "configuration.tasks": (
                "Начальная область задач", "Начальная сортировка",
                "Колонки таблицы задач",
            ),
            "commit_queue": (
                "Автоочистка", "Очистить очередь", "Отправить все",
                "Применять каждое изменение к отмеченным элементам",
            ),
            "sidebar_editor": (
                "Перезагрузить боковую панель", "Добавить ссылку",
                "Настроить поиск", "Применить XML",
            ),
        }.items():
            controller.select(topic_id)
            for control in controls:
                self.assertIn(control, controller.article["body"])

        controller.select("administration")
        administration_help = controller.article["body"]
        for section in (
            "## Разделы окна",
            "## Проект, доступ и черновики",
            "## Серч-тайпы",
            "## Схема проекта",
            "## Воркфлоу",
            "## Пользователи и группы",
            "## Права доступа",
            "## Сохранение, конфликты и ошибки",
        ):
            self.assertIn(section, administration_help)
        for control in (
            "Только текущий проект",
            "Скрыть типы config",
            "Зависимости процесса",
            "Показывать retired",
            "Наследовать правило",
        ):
            self.assertIn(control, administration_help)

        controller.select("script_triggers")
        trigger_help = controller.article["body"]
        for example in (
            "get_api", "th.sobject", "th.snapshot", "get_files_objects"
        ):
            self.assertIn(example, trigger_help)

        controller.select("search")
        search_help = controller.article["body"]
        for section in (
            "## Верхняя строка",
            "## Быстрые фильтры",
            "## Расширенный поиск",
            "## Многослойный поиск: практические схемы",
            "## `**Expression` и TEL",
            "## Сохранённые поиски",
            "## Нижняя панель результатов",
        ):
            self.assertIn(section, search_help)
        for example in (
            "@SOBJECT(sthpw/task['assigned', '$LOGIN'])",
            "@GET(.priority) == 3",
            "Match (slow)",
            "AND / OR",
        ):
            self.assertIn(example, search_help)

        english_search_help = (
            article_root / "search.en.md"
        ).read_text(encoding="utf-8")
        for control in (
            "Refresh current results",
            "Script shelf",
            "Quick filters",
            "Workspace panels",
            "Add new search tab",
            "Search filters and presets",
            "All search tabs",
            "Sort items",
            "Group items",
            "Change search results view",
            "Result actions",
            "Previous page",
            "Next page",
            "Sync current Search Type",
            "Update selected preset",
            "Save as new preset",
        ):
            self.assertIn(control, english_search_help)

        catalog = json.loads(
            (ROOT / "thlib" / "ui" / "translations" / "ru.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertNotIn(
            "Script triggers run saved scripts immediately before or after "
            "selected Handler and DCC actions.",
            catalog,
        )

    def test_articles_are_markdown_files_with_language_fallback_and_reload(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            english = root / "overview.en.md"
            english.write_text(
                "---\ngroup: Guide\nicon: help\norder: 1\n---\n"
                "# Overview\n\n> First summary line.\n"
                "> Second summary line.\n\n"
                "## Example\n\n```python\nprint('hello')\n```\n",
                encoding="utf-8",
            )
            (root / "overview.ru.md").write_text(
                "---\ngroup: Руководство\nicon: help\norder: 1\n---\n"
                "# Обзор\n\nТекст справки.\n",
                encoding="utf-8",
            )
            (root / "files.en.md").write_text(
                "# Files\n\nEnglish fallback.\n", encoding="utf-8"
            )
            localization = _Localization()
            controller = HelpController(root, localization)

            self.assertEqual(controller.article["title"], "Overview")
            self.assertEqual(
                controller.article["summary"],
                "First summary line.\nSecond summary line.",
            )
            self.assertNotIn("First summary line", controller.article["body"])
            self.assertIn("```python", controller.article["body"])
            localization.use("ru")
            self.assertEqual(controller.article["title"], "Обзор")
            self.assertEqual(
                [topic["title"] for topic in controller.topics],
                ["Обзор", "Files"],
            )

            controller.select("files")
            self.assertTrue(controller.article["filePath"].endswith("files.en.md"))
            (root / "files.en.md").write_text(
                "# Updated files\n\nEdited by a user.\n", encoding="utf-8"
            )
            controller.reload()
            self.assertEqual(controller.article["title"], "Updated files")

            with patch(
                "thlib.ui.help.QDesktopServices.openUrl", return_value=True
            ) as open_url:
                self.assertTrue(controller.open_current_file())
            self.assertEqual(
                Path(open_url.call_args.args[0].toLocalFile()).resolve(),
                (root / "files.en.md").resolve(),
            )


if __name__ == "__main__":
    unittest.main()

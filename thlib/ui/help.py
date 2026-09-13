"""File-backed product help for the QML application."""

from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import QObject, Property, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QTextCursor, QTextFormat


_ARTICLE_NAME = re.compile(r"^(?P<topic>.+)\.(?P<language>[a-z]{2})\.md$")


class HelpController(QObject):
    """Loads editable Markdown help articles for the selected UI language."""

    topicsChanged = Signal()
    articleChanged = Signal()
    errorChanged = Signal()

    def __init__(
        self,
        article_root: Path,
        localization,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._article_root = Path(article_root).resolve()
        self._localization = localization
        self._topics: list[dict] = []
        self._articles: dict[str, dict] = {}
        self._article: dict = {}
        self._selected_topic_id = "overview"
        self._error = ""
        localization.languageChanged.connect(self.reload)
        self.reload()

    @Property("QVariantList", notify=topicsChanged)
    def topics(self) -> list[dict]:
        return self._topics

    @Property("QVariantMap", notify=articleChanged)
    def article(self) -> dict:
        return self._article

    @Property(str, notify=articleChanged)
    def selected_topic_id(self) -> str:
        return self._selected_topic_id

    @Property(str, notify=errorChanged)
    def error(self) -> str:
        return self._error

    @Slot(str)
    def select(self, topic_id: str) -> None:
        topic_id = str(topic_id or "overview")
        article = self._articles.get(topic_id)
        if article is None or topic_id == self._selected_topic_id:
            return
        self._selected_topic_id = topic_id
        self._article = article
        self.articleChanged.emit()

    @Slot()
    def reload(self) -> None:
        try:
            articles = self._load_articles(
                str(self._localization.current_language or "en")
            )
            if not articles:
                raise ValueError(f"No help articles found in {self._article_root}")
        except (OSError, UnicodeError, ValueError) as error:
            self._set_error(str(error))
            return

        self._set_error("")
        self._articles = articles
        self._topics = [
            {
                key: article[key]
                for key in ("id", "group", "title", "icon", "searchText")
            }
            for article in articles.values()
        ]
        if self._selected_topic_id not in articles:
            self._selected_topic_id = (
                "overview" if "overview" in articles else next(iter(articles))
            )
        self._article = articles[self._selected_topic_id]
        self.topicsChanged.emit()
        self.articleChanged.emit()

    @Slot(result=bool)
    def open_current_file(self) -> bool:
        path = self._article.get("filePath")
        return bool(
            path and QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
        )

    @Slot(QObject)
    def format_document(self, text_document: QObject) -> None:
        document = text_document.textDocument()
        cursor = QTextCursor(document)
        cursor.beginEditBlock()
        block = document.begin()
        while block.isValid():
            block_format = block.blockFormat()
            next_block = block.next()
            in_code_block = block_format.hasProperty(
                QTextFormat.Property.BlockCodeFence
            )
            next_in_code_block = (
                next_block.isValid()
                and next_block.blockFormat().hasProperty(
                    QTextFormat.Property.BlockCodeFence
                )
            )
            block_format.setBottomMargin(
                0 if in_code_block and next_in_code_block else 8
            )
            cursor.setPosition(block.position())
            cursor.setBlockFormat(block_format)
            block = next_block
        cursor.endEditBlock()

    def _load_articles(self, language: str) -> dict[str, dict]:
        paths: dict[str, Path] = {}
        for path in self._article_root.glob("*.en.md"):
            paths[self._topic_id(path)] = path
        if language != "en":
            for path in self._article_root.glob(f"*.{language}.md"):
                paths[self._topic_id(path)] = path

        records = [
            self._read_article(topic_id, path)
            for topic_id, path in paths.items()
        ]
        records.sort(key=lambda record: (record["order"], record["title"].casefold()))
        return {record["id"]: record for record in records}

    @staticmethod
    def _topic_id(path: Path) -> str:
        match = _ARTICLE_NAME.fullmatch(path.name)
        if match is None:
            raise ValueError(f"Invalid help article filename: {path.name}")
        return match.group("topic")

    def _read_article(self, topic_id: str, path: Path) -> dict:
        text = path.read_text(encoding="utf-8")
        metadata, markdown = self._split_front_matter(path, text)
        lines = markdown.splitlines()
        title_index = next(
            (index for index, line in enumerate(lines) if line.startswith("# ")),
            None,
        )
        if title_index is None:
            raise ValueError(f"Help article has no title: {path}")
        title = lines.pop(title_index)[2:].strip()
        if not title:
            raise ValueError(f"Help article has an empty title: {path}")
        summary, lines = self._extract_summary(lines)
        body = "\n".join(lines).strip()
        plain_text = re.sub(
            r"[`#>*_|\[\]()]", " ", f"{summary}\n{body}"
        )
        return {
            "id": topic_id,
            "group": metadata.get("group", "Other"),
            "title": title,
            "icon": metadata.get("icon", "help"),
            "order": self._order(path, metadata.get("order", "1000")),
            "summary": summary,
            "body": body,
            "filePath": str(path),
            "fileUrl": QUrl.fromLocalFile(str(path)).toString(),
            "searchText": " ".join(plain_text.split()),
        }

    @staticmethod
    def _extract_summary(lines: list[str]) -> tuple[str, list[str]]:
        start = next(
            (index for index, line in enumerate(lines) if line.strip()),
            None,
        )
        if start is None or not lines[start].lstrip().startswith(">"):
            return "", lines

        end = start
        summary_lines = []
        while end < len(lines) and lines[end].lstrip().startswith(">"):
            summary_lines.append(lines[end].lstrip()[1:].lstrip())
            end += 1
        return "\n".join(summary_lines).strip(), lines[:start] + lines[end:]

    @staticmethod
    def _split_front_matter(path: Path, text: str) -> tuple[dict[str, str], str]:
        lines = text.splitlines()
        if not lines or lines[0].strip() != "---":
            return {}, text
        try:
            end = next(
                index for index, line in enumerate(lines[1:], start=1)
                if line.strip() == "---"
            )
        except StopIteration as error:
            raise ValueError(f"Unclosed help article metadata: {path}") from error
        metadata = {}
        for line in lines[1:end]:
            key, separator, value = line.partition(":")
            if not separator or not key.strip() or not value.strip():
                raise ValueError(
                    f"Invalid help article metadata in {path}: {line}"
                )
            metadata[key.strip()] = value.strip()
        return metadata, "\n".join(lines[end + 1 :])

    @staticmethod
    def _order(path: Path, value: str) -> int:
        try:
            return int(value)
        except ValueError as error:
            raise ValueError(
                f"Invalid help article order in {path}: {value}"
            ) from error

    def _set_error(self, value: str) -> None:
        if value == self._error:
            return
        self._error = value
        self.errorChanged.emit()

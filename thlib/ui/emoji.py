"""Unicode emoji catalog and bundled Noto Color Emoji registration."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    Property,
    Signal,
    Qt,
    Slot,
)
from PySide6.QtGui import QFontDatabase


_EMOJI_LINE = re.compile(
    r"^([0-9A-F ]+)\s*;\s*fully-qualified\s*"
    r"#\s*\S+\s+E[0-9.]+\s+(.+)$"
)
_REGISTERED_FONT_FAMILY = ""


@dataclass(frozen=True, slots=True)
class EmojiEntry:
    value: str
    name: str
    category: str


class EmojiCatalog(QAbstractListModel):
    """Filtered RGI emoji model backed by the bundled Unicode data file."""

    EmojiRole = Qt.UserRole + 1
    NameRole = Qt.UserRole + 2
    CategoryRole = Qt.UserRole + 3

    countChanged = Signal()

    _CATEGORY_SPECS = (
        ("Smileys & Emotion", "emoji"),
        ("People & Body", "person"),
        ("Component", "puzzle-piece"),
        ("Animals & Nature", "paw"),
        ("Food & Drink", "utensils"),
        ("Travel & Places", "car"),
        ("Activities", "futbol"),
        ("Objects", "lightbulb"),
        ("Symbols", "shapes"),
        ("Flags", "flag"),
    )

    def __init__(self, project_root: Path, parent=None) -> None:
        super().__init__(parent)
        side_root = Path(project_root) / "thlib" / "side"
        self._data_path = side_root / "unicode_emoji" / "emoji-test.txt"
        self._font_path = (
            side_root
            / "noto_emoji"
            / "NotoColorEmoji_WindowsCompatible.ttf"
        )
        self._font_family = self._register_font(self._font_path)
        self._entries: tuple[EmojiEntry, ...] | None = None
        self._visible_entries: tuple[EmojiEntry, ...] = ()
        self._category = self.defaultCategory
        self._query = ""

    @staticmethod
    def _register_font(path: Path) -> str:
        global _REGISTERED_FONT_FAMILY
        if _REGISTERED_FONT_FAMILY:
            return _REGISTERED_FONT_FAMILY
        if not path.is_file():
            raise FileNotFoundError(f"Bundled emoji font is missing: {path}")
        font_id = QFontDatabase.addApplicationFont(str(path))
        if font_id < 0:
            raise RuntimeError(f"Qt could not load the bundled emoji font: {path}")
        families = QFontDatabase.applicationFontFamilies(font_id)
        if not families:
            raise RuntimeError(f"Bundled emoji font declares no family: {path}")
        family = str(families[0])
        if family not in QFontDatabase.applicationEmojiFontFamilies():
            QFontDatabase.addApplicationEmojiFontFamily(family)
        _REGISTERED_FONT_FAMILY = family
        return family

    @Property(str, constant=True)
    def fontFamily(self) -> str:
        return self._font_family

    @Property(str, constant=True)
    def defaultCategory(self) -> str:
        return self._CATEGORY_SPECS[0][0]

    @Property("QVariantList", constant=True)
    def categories(self) -> list[dict[str, str]]:
        return [
            {"key": key, "icon": icon}
            for key, icon in self._CATEGORY_SPECS
        ]

    @Property(int, notify=countChanged)
    def count(self) -> int:
        return len(self._visible_entries)

    @Property(int, constant=True)
    def totalCount(self) -> int:
        return len(self._load_entries())

    def roleNames(self) -> dict[int, bytes]:
        return {
            self.EmojiRole: b"emoji",
            self.NameRole: b"emojiName",
            self.CategoryRole: b"emojiCategory",
        }

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._visible_entries)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < self.rowCount():
            return None
        entry = self._visible_entries[index.row()]
        if role in {Qt.DisplayRole, self.EmojiRole}:
            return entry.value
        if role == self.NameRole:
            return entry.name
        if role == self.CategoryRole:
            return entry.category
        return None

    def _load_entries(self) -> tuple[EmojiEntry, ...]:
        if self._entries is not None:
            return self._entries
        if not self._data_path.is_file():
            raise FileNotFoundError(
                f"Bundled Unicode emoji data is missing: {self._data_path}"
            )
        entries: list[EmojiEntry] = []
        category = ""
        with self._data_path.open("r", encoding="utf-8") as stream:
            for raw_line in stream:
                line = raw_line.strip()
                if line.startswith("# group:"):
                    category = line.partition(":")[2].strip()
                    continue
                match = _EMOJI_LINE.match(line)
                if not match or not category:
                    continue
                code_points, name = match.groups()
                value = "".join(
                    chr(int(code_point, 16))
                    for code_point in code_points.split()
                )
                entries.append(EmojiEntry(value, name.strip(), category))
        if not entries:
            raise ValueError(
                f"Bundled Unicode emoji data contains no RGI entries: "
                f"{self._data_path}"
            )
        self._entries = tuple(entries)
        return self._entries

    @Slot(str, str)
    def set_filter(self, category: str, query: str) -> None:
        category = str(category or self.defaultCategory)
        valid_categories = {key for key, _icon in self._CATEGORY_SPECS}
        if category not in valid_categories:
            category = self.defaultCategory
        query = str(query or "").strip().casefold()
        if category == self._category and query == self._query and self._entries:
            return
        entries: Iterable[EmojiEntry] = self._load_entries()
        if query:
            visible = tuple(
                entry
                for entry in entries
                if query in entry.name.casefold() or query in entry.value
            )
        else:
            visible = tuple(
                entry for entry in entries if entry.category == category
            )
        self.beginResetModel()
        self._category = category
        self._query = query
        self._visible_entries = visible
        self.endResetModel()
        self.countChanged.emit()

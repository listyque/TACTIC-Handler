"""Workspace presentation models."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path

from PySide6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    QObject,
    Property,
    Qt,
    QUrl,
    Signal,
    Slot,
)

@dataclass(slots=True)
class SectionTab:
    entry_key: str
    title: str
    accent: str
    current: bool = False
    glyph: str = "sidebar-link"

class SectionTabModel(QAbstractListModel):
    """Persistent narrow stype tabs from Ui_extendedLeftTabBarWidget."""

    KeyRole = Qt.UserRole + 1
    TitleRole = Qt.UserRole + 2
    AccentRole = Qt.UserRole + 3
    CurrentRole = Qt.UserRole + 4
    GlyphRole = Qt.UserRole + 5

    def __init__(self) -> None:
        super().__init__()
        self._items: list[SectionTab] = []

    def roleNames(self) -> dict[int, bytes]:
        return {
            self.KeyRole: b"entryKey",
            self.TitleRole: b"title",
            self.AccentRole: b"accent",
            self.CurrentRole: b"current",
            self.GlyphRole: b"glyph",
        }

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._items):
            return None
        item = self._items[index.row()]
        return {
            self.KeyRole: item.entry_key,
            self.TitleRole: item.title,
            self.AccentRole: item.accent,
            self.CurrentRole: item.current,
            self.GlyphRole: item.glyph,
        }.get(role)

    def replace(self, items: list[SectionTab]) -> None:
        items = list(items)
        same_rows = (
            len(self._items) == len(items)
            and all(
                current.entry_key == updated.entry_key
                for current, updated in zip(self._items, items)
            )
        )
        if same_rows:
            fields = (
                (self.TitleRole, "title"),
                (self.AccentRole, "accent"),
                (self.CurrentRole, "current"),
                (self.GlyphRole, "glyph"),
            )
            for row, (current, updated) in enumerate(
                zip(self._items, items)
            ):
                changed_roles = []
                for role, field_name in fields:
                    value = getattr(updated, field_name)
                    if getattr(current, field_name) == value:
                        continue
                    setattr(current, field_name, value)
                    changed_roles.append(role)
                if changed_roles:
                    index = self.index(row, 0)
                    self.dataChanged.emit(index, index, changed_roles)
            return

        self.beginResetModel()
        self._items = items
        self.endResetModel()

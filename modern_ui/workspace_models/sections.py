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
    QSettings,
    Qt,
    QUrl,
    Signal,
    Slot,
)

@dataclass(slots=True)
class SectionTab:
    entry_key: str
    title: str
    acronym: str
    accent: str
    current: bool = False

class SectionTabModel(QAbstractListModel):
    """Persistent narrow stype tabs from Ui_extendedLeftTabBarWidget."""

    KeyRole = Qt.UserRole + 1
    TitleRole = Qt.UserRole + 2
    AcronymRole = Qt.UserRole + 3
    AccentRole = Qt.UserRole + 4
    CurrentRole = Qt.UserRole + 5

    def __init__(self) -> None:
        super().__init__()
        self._items: list[SectionTab] = []

    def roleNames(self) -> dict[int, bytes]:
        return {
            self.KeyRole: b"entryKey",
            self.TitleRole: b"title",
            self.AcronymRole: b"acronym",
            self.AccentRole: b"accent",
            self.CurrentRole: b"current",
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
            self.AcronymRole: item.acronym,
            self.AccentRole: item.accent,
            self.CurrentRole: item.current,
        }.get(role)

    def replace(self, items: list[SectionTab]) -> None:
        self.beginResetModel()
        self._items = list(items)
        self.endResetModel()

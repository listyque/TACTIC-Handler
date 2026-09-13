"""Workspace state: detail editing."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, replace
from pathlib import Path

from PySide6.QtCore import QModelIndex, Qt, QUrl, Slot

from .records import RecordListModel
from .results import WorkspaceItemModel
from .watch_folders import _watch_folder_record


class DetailEditingMixin:
    def set_description_target(
        self,
        target,
        kind: str,
        title: str,
    ) -> None:
        info = {}
        target_key = ""
        if target is not None:
            try:
                info = (
                    target.get_snapshot()
                    if kind == "snapshot"
                    else target.get_info()
                ) or {}
            except (AttributeError, KeyError, TypeError):
                info = {}
            if kind in {"sobject", "snapshot"}:
                try:
                    target_key = str(target.get_search_key() or "")
                except (AttributeError, KeyError, TypeError):
                    target_key = ""

        self._description_target = target
        self._description_target_key = target_key
        self._description_target_kind = str(kind or "")
        self._description_target_title = str(title or "")
        self._description_error = ""
        self._description_saving = False

        value = str(info.get("description") or info.get("detail") or "")
        self._description_original = value
        if not self._description_pinned:
            self._description_editing = False
            if value != self._description:
                self._description = value
                self.description_changed.emit(value)
        self.description_editor_changed.emit()

    @Slot(str)
    def set_description(self, value: str) -> None:
        value = str(value or "")
        if value == self._description:
            return
        self._description = value
        self.description_changed.emit(value)
        self.description_editor_changed.emit()

    @Slot()
    def begin_description_edit(self) -> None:
        if self._description_saving or not self._description_target:
            return
        self._description_editing = True
        self._description_error = ""
        self.description_editor_changed.emit()

    @Slot()
    def cancel_description_edit(self) -> None:
        if self._description_saving:
            return
        self._description_editing = False
        if not self._description_pinned:
            self.set_description(self._description_original)
        self._description_error = ""
        self.description_editor_changed.emit()

    @Slot()
    def freeze_description(self) -> None:
        if not self._description_target:
            return
        self._description_pinned = True
        self._description_editing = False
        self._description_error = ""
        self.description_editor_changed.emit()

    @Slot()
    def unfreeze_description(self) -> None:
        if self._description_saving:
            return
        self._description_pinned = False
        self._description_editing = False
        self.set_description(self._description_original)
        self._description_error = ""
        self.description_editor_changed.emit()

    @Slot()
    def commit_description(self) -> None:
        if (
            self._description_saving
            or not self._description_target_key
            or self._description == self._description_original
        ):
            return
        self._description_saving = True
        self._description_editing = False
        self._description_error = ""
        self.description_editor_changed.emit()
        self.description_save_requested.emit(self._description)

    def description_save_succeeded(self, target_key: str, value: str) -> None:
        if target_key != self._description_target_key:
            return
        self._description_original = str(value or "")
        self._description_saving = False
        self._description_editing = False
        self._description_error = ""
        self.description_editor_changed.emit()

    def description_save_failed(self, target_key: str, message: str) -> None:
        if target_key != self._description_target_key:
            return
        self._description_saving = False
        self._description_editing = True
        self._description_error = str(message or "Unable to save description")
        self.description_editor_changed.emit()

    @Slot(str)
    def add_note(self, value: str) -> None:
        value = value.strip()
        if not value or not self._selected_sobject:
            return
        self.note_add_requested.emit(value)

    @Slot(int, str)
    def set_task_status(self, row: int, status: str) -> None:
        if not 0 <= row < len(self._task_sobjects):
            return
        self.task_status_requested.emit(row, status)

    @Slot(str)
    def save_description(self, value: str) -> None:
        self.set_description(value)
        self.commit_description()

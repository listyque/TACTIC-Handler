"""Workspace state: workspace tabs."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, replace
from pathlib import Path

from PySide6.QtCore import QModelIndex, Qt, QUrl, Slot

from .records import RecordListModel
from .results import WorkspaceItemModel
from .watch_folders import _watch_folder_record


class WorkspaceTabsMixin:
    @Slot(str)
    @Slot(str, str)
    def activate_tab(self, entry_key: str, title: str = "") -> None:
        """Raise an existing inner search tab."""
        entry_key = entry_key or "search"
        title = title or entry_key.replace("_", " ").title()
        if any(
            record.get("entryKey") == entry_key
            for record in self.tabs_model._records
        ):
            self.tab_activated.emit(entry_key, title)

    @Slot()
    def add_search_tab(self) -> None:
        self.tab_add_requested.emit()

    @Slot(int)
    def close_tab(self, row: int) -> None:
        self.tab_close_requested.emit(row)

    @Slot(int, int)
    def reorder_tab(self, source_row: int, target_row: int) -> None:
        if source_row != target_row:
            self.tab_reorder_requested.emit(source_row, target_row)

    @staticmethod
    def _set_stable_records(
        model: RecordListModel,
        records: list[dict],
        identity_role: str,
    ) -> None:
        existing = model._records
        same_rows = (
            len(existing) == len(records)
            and all(
                current.get(identity_role) == updated.get(identity_role)
                for current, updated in zip(existing, records)
            )
        )
        if not same_rows:
            model.replace(records)
            return

        changed_rows = []
        changed_roles = set()
        for row, (current, updated) in enumerate(zip(existing, records)):
            row_changed = False
            for role_name in model._roles:
                value = updated.get(role_name)
                if current.get(role_name) == value:
                    continue
                current[role_name] = value
                changed_roles.add(model._role_ids[role_name])
                row_changed = True
            if row_changed:
                changed_rows.append(row)

        if changed_rows:
            model.dataChanged.emit(
                model.index(min(changed_rows), 0),
                model.index(max(changed_rows), 0),
                list(changed_roles),
            )

    def set_tabs(self, records: list[dict]) -> None:
        self._set_stable_records(self.tabs_model, records, "entryKey")

    def set_result_surfaces(self, records: list[dict]) -> None:
        self._set_stable_records(
            self.result_surfaces_model,
            records,
            "surfaceKey",
        )

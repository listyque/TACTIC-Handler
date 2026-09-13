"""Workspace presentation models."""

from __future__ import annotations

import json
import time
from difflib import SequenceMatcher
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

class RecordListModel(QAbstractListModel):
    """Small role-based model shared by QML panels."""

    contentReplaced = Signal()

    def __init__(self, roles: tuple[str, ...], records: list[dict] | None = None, *, identity_role: str | None = None) -> None:
        super().__init__()
        self._roles = roles
        self._role_ids = {name: Qt.UserRole + index + 1 for index, name in enumerate(roles)}
        self._role_names_by_id = {
            role_id: name for name, role_id in self._role_ids.items()
        }
        self._records = list(records or [])
        self._identity_role = identity_role
        self._lookup_indexes = {}
        self.dataChanged.connect(self._invalidate_lookups)
        self.rowsInserted.connect(self._invalidate_lookups)
        self.rowsRemoved.connect(self._invalidate_lookups)
        self.modelReset.connect(self._invalidate_lookups)

    def _invalidate_lookups(self, *_args):
        self._lookup_indexes.clear()

    @Slot(str, str, result="QVariantMap")
    def lookup(self, role: str, value: str) -> dict:
        """Find a presentation record by identity, sharing the index across views."""
        if role not in self._role_ids:
            raise ValueError(f"Unknown model role: {role}")
        if role not in self._lookup_indexes:
            self._lookup_indexes[role] = {
                str(record.get(role) or ""): row
                for row, record in reversed(list(enumerate(self._records)))
            }
        row = self._lookup_indexes[role].get(value)
        return dict(self._records[row]) if row is not None else {}

    def roleNames(self) -> dict[int, bytes]:
        return {role_id: name.encode("utf-8") for name, role_id in self._role_ids.items()}

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._records)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._records):
            return None
        name = self._role_names_by_id.get(role)
        return self._records[index.row()].get(name) if name else None

    @Slot(int)
    def remove(self, row: int) -> None:
        if not 0 <= row < len(self._records):
            return
        self.beginRemoveRows(QModelIndex(), row, row)
        self._records.pop(row)
        self.endRemoveRows()

    @Slot()
    def clear(self) -> None:
        if not self._records:
            return
        self.beginRemoveRows(QModelIndex(), 0, len(self._records) - 1)
        self._records.clear()
        self.endRemoveRows()

    def replace(self, records) -> None:
        new_records = [dict(record) for record in records]
        identity_changed = False
        if self._identity_role:
            identity_changed = self._reconcile_identities(new_records)
        old_count = len(self._records)
        new_count = len(new_records)
        common_count = min(old_count, new_count)
        changed_rows = []

        for row in range(common_count):
            if self._records[row] == new_records[row]:
                continue
            changed_roles = [
                self._role_ids[name]
                for name in self._roles
                if self._records[row].get(name) != new_records[row].get(name)
            ]
            self._records[row] = new_records[row]
            if changed_roles:
                changed_rows.append((row, changed_roles))

        changed_ranges = []
        for row, roles in changed_rows:
            role_key = tuple(roles)
            if (
                changed_ranges
                and changed_ranges[-1][1] + 1 == row
                and changed_ranges[-1][2] == role_key
            ):
                changed_ranges[-1] = (
                    changed_ranges[-1][0], row, role_key
                )
            else:
                changed_ranges.append((row, row, role_key))
        for first_row, last_row, roles in changed_ranges:
            self.dataChanged.emit(
                self.index(first_row, 0),
                self.index(last_row, 0),
                list(roles),
            )

        structure_changed = False
        if new_count < old_count:
            self.beginRemoveRows(QModelIndex(), new_count, old_count - 1)
            del self._records[new_count:]
            self.endRemoveRows()
            structure_changed = True
        elif new_count > old_count:
            self.beginInsertRows(QModelIndex(), old_count, new_count - 1)
            self._records.extend(new_records[old_count:])
            self.endInsertRows()
            structure_changed = True
        if changed_rows or structure_changed or identity_changed:
            self.contentReplaced.emit()

    def _reconcile_identities(self, records: list[dict]) -> bool:
        """Insert/remove at their real positions; keep unchanged delegates alive."""
        key = self._identity_role
        old_keys = [record.get(key) for record in self._records]
        new_keys = [record.get(key) for record in records]
        if any(value in (None, "") for value in new_keys) or len(set(new_keys)) != len(new_keys):
            raise ValueError(f"{key} must be present and unique in a keyed list")
        if old_keys == new_keys:
            return False
        # Reverse edit order keeps the old indices valid. The common prepend
        # and append paths emit one insertion, not dataChanged for every row.
        edits = SequenceMatcher(None, old_keys, new_keys, autojunk=False).get_opcodes()
        for operation, start, end, new_start, new_end in reversed(edits):
            if operation == "equal":
                continue
            if end > start:
                self.beginRemoveRows(QModelIndex(), start, end - 1)
                del self._records[start:end]
                self.endRemoveRows()
            if new_end > new_start:
                self.beginInsertRows(QModelIndex(), start, start + new_end - new_start - 1)
                self._records[start:start] = records[new_start:new_end]
                self.endInsertRows()
        return True

    def reset_records(self, records) -> None:
        new_records = [dict(record) for record in records]
        if self._records == new_records:
            return
        self.beginResetModel()
        self._records = new_records
        self.endResetModel()
        self.contentReplaced.emit()

    def append_records(self, records: list[dict]) -> None:
        if not records:
            return
        first = len(self._records)
        self.beginInsertRows(QModelIndex(), first, first + len(records) - 1)
        self._records.extend(dict(record) for record in records)
        self.endInsertRows()
        self.contentReplaced.emit()

    @Slot(int, result="QVariantMap")
    def get(self, row: int) -> dict:
        if not 0 <= row < len(self._records):
            return {}
        return dict(self._records[row])

    @Slot(result=int)
    def count(self) -> int:
        return len(self._records)

    def records(self) -> list[dict]:
        """Return a detached snapshot for Python-side feature composition."""
        return [dict(record) for record in self._records]

    @Slot(int)
    def select_row(self, row: int) -> None:
        if "selected" not in self._roles or not 0 <= row < len(self._records):
            return
        changed = []
        for index, record in enumerate(self._records):
            selected = index == row
            if bool(record.get("selected")) != selected:
                record["selected"] = selected
                changed.append(index)
        for index in changed:
            model_index = self.index(index, 0)
            self.dataChanged.emit(
                model_index,
                model_index,
                [self._role_ids["selected"]],
            )

    @Slot(str)
    def append_named(self, title: str) -> None:
        row = len(self._records)
        record = {name: "" for name in self._roles}
        record.update({
            "title": title,
            "name": title,
            "checked": True,
            "rowEnabled": True,
            "watchEnabled": True,
        })
        self.beginInsertRows(QModelIndex(), row, row)
        self._records.append(record)
        self.endInsertRows()

    @Slot(int)
    def toggle_checked(self, row: int) -> None:
        if not 0 <= row < len(self._records):
            return
        role_name = next(
            (
                name for name in ("checked", "rowEnabled", "watchEnabled")
                if name in self._roles
            ),
            "checked",
        )
        current = bool(self._records[row].get(role_name, False))
        self._records[row][role_name] = not current
        model_index = self.index(row, 0)
        self.dataChanged.emit(model_index, model_index)

    @Slot(int, str)
    def set_status(self, row: int, status: str) -> None:
        if not 0 <= row < len(self._records):
            return
        self._records[row]["status"] = status
        model_index = self.index(row, 0)
        self.dataChanged.emit(model_index, model_index)

    @Slot(int, str, "QVariant")
    def set_value(self, row: int, role: str, value) -> None:
        if (
            not 0 <= row < len(self._records)
            or role not in self._role_ids
            or self._records[row].get(role) == value
        ):
            return
        self._records[row][role] = value
        model_index = self.index(row, 0)
        self.dataChanged.emit(
            model_index,
            model_index,
            [self._role_ids[role]],
        )

    def update_record(self, row: int, values) -> bool:
        if not 0 <= row < len(self._records):
            return False
        changed_roles = []
        record = self._records[row]
        for role, value in dict(values or {}).items():
            role_id = self._role_ids.get(role)
            if role_id is None or record.get(role) == value:
                continue
            record[role] = value
            changed_roles.append(role_id)
        if not changed_roles:
            return False
        model_index = self.index(row, 0)
        self.dataChanged.emit(model_index, model_index, changed_roles)
        return True

    def set_role_for_rows(self, rows, role: str, value) -> bool:
        """Update one role over sparse rows with contiguous notifications."""
        role_id = self._role_ids.get(role)
        if role_id is None:
            return False
        changed_rows = []
        for row in sorted({int(row) for row in rows}):
            if (
                    not 0 <= row < len(self._records)
                    or self._records[row].get(role) == value):
                continue
            self._records[row][role] = value
            changed_rows.append(row)
        if not changed_rows:
            return False
        first = previous = changed_rows[0]
        for row in changed_rows[1:] + [None]:
            if row is not None and row == previous + 1:
                previous = row
                continue
            self.dataChanged.emit(
                self.index(first, 0), self.index(previous, 0), [role_id]
            )
            if row is not None:
                first = previous = row
        return True

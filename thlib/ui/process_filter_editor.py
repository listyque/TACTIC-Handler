from __future__ import annotations

from PySide6.QtCore import QObject, Property, Signal, Slot

from .process_selection import (
    PROCESS_SELECTION_ROLES,
    build_process_selection_tree,
    resolve_process_selection_context,
)
from .workspace import RecordListModel


class ProcessFilterEditorController(QObject):
    """Process-filter editor using the original Handler data contract.

    The editor owns only the local tree-visibility preference. Search
    conditions and server-side Saved Searches remain in Advanced Search.
    """

    stateChanged = Signal()

    def __init__(self, context, apply_settings, notify, parent=None) -> None:
        super().__init__(parent)
        self._context = context
        self._apply_settings = apply_settings
        self._notify = notify
        self._context_key: tuple[str, str, str] = ("", "", "")
        self._title = ""
        self._original_ignore: dict = {}
        self.model = RecordListModel(PROCESS_SELECTION_ROLES)

    @staticmethod
    def _key(context: dict) -> tuple[str, str, str]:
        return (
            str(context.get("project_code") or ""),
            str(context.get("search_type") or ""),
            str(context.get("tab_name") or context.get("tab_id") or ""),
        )

    @staticmethod
    def _info(source) -> dict:
        return dict(getattr(source, "info", None) or {})

    def _settings_path(self, context: dict) -> str:
        return "ui_search/checkin_out/{}/{}/{}".format(
            context.get("project_type") or "",
            context.get("project_code") or "",
            context.get("tab_name") or context.get("tab_id") or "",
        )

    @Slot()
    def begin_session(self) -> None:
        context = dict(self._context() or {})
        stype, project = resolve_process_selection_context(context)
        context["stype"] = stype
        context["project"] = project
        self._context_key = self._key(context)
        info = self._info(stype)
        self._title = str(
            info.get("title") or info.get("name")
            or info.get("code") or context.get("search_type") or ""
        )
        if not stype or not project or not all(self._context_key[:2]):
            self.model.clear()
            self._original_ignore = {}
            self.stateChanged.emit()
            return

        records = self._build_records(stype, project)
        ignore = self._read_settings(context)
        self._apply_ignore(records, ignore)
        self.model.reset_records(records)
        self._original_ignore = self._ignore_dict()
        self.stateChanged.emit()

    def _build_records(self, stype, project) -> list[dict]:
        return build_process_selection_tree(
            stype,
            project,
            checked_kinds=frozenset({"builtin", "process", "child"}),
        )

    def _read_settings(self, context: dict) -> dict:
        from thlib.environment import env_read_config

        return dict(env_read_config(
            filename="process_ignore_dict",
            unique_id=self._settings_path(context),
            long_abs_path=True,
        ) or {})

    @staticmethod
    def _apply_ignore(records: list[dict], ignore: dict) -> None:
        children = set(ignore.get("children") or [])
        builtins = set(ignore.get("builtins") or [])
        processes = dict(ignore.get("processes") or {})
        for record in records:
            kind = record.get("kind")
            if kind == "child":
                record["checked"] = record.get("key") not in children
            elif kind == "builtin":
                record["checked"] = record.get("key") not in builtins
            elif kind == "process":
                record["checked"] = record.get("key") not in set(
                    processes.get(record.get("group")) or []
                )

    @Property(str, notify=stateChanged)
    def context_title(self) -> str:
        return self._title

    @Property(bool, notify=stateChanged)
    def valid_context(self) -> bool:
        return bool(self.model._records and all(self._context_key[:2]))

    @Property(bool, notify=stateChanged)
    def dirty(self) -> bool:
        return self._ignore_dict() != self._original_ignore

    @Slot(int, bool)
    def select_row(self, row: int, additive: bool) -> None:
        if not 0 <= row < len(self.model._records):
            return
        current = bool(self.model._records[row].get("selected"))
        changed = False
        for index, record in enumerate(self.model._records):
            selected = (not current) if index == row else (
                bool(record.get("selected")) if additive else False
            )
            changed = self.model.update_record(
                index, {"selected": selected}
            ) or changed
        if changed:
            self.stateChanged.emit()

    @Slot(int, bool)
    def set_checked(self, row: int, checked: bool) -> None:
        if not 0 <= row < len(self.model._records):
            return
        source = self.model._records[row]
        if not source.get("checkable"):
            return
        selected_rows = [
            index for index, record in enumerate(self.model._records)
            if record.get("selected") and record.get("checkable")
        ]
        rows = selected_rows if source.get("selected") and len(selected_rows) > 1 else [row]
        changed = self.model.set_role_for_rows(rows, "checked", bool(checked))
        if changed:
            self.stateChanged.emit()

    @Slot(int, bool)
    def toggle_expanded(self, row: int, recursive: bool = False) -> None:
        if not 0 <= row < len(self.model._records):
            return
        record = self.model._records[row]
        if not record.get("hasChildren"):
            return
        expanded = not bool(record.get("expanded"))
        self.model.set_value(row, "expanded", expanded)
        if recursive:
            node_id = str(record.get("nodeId") or "")
            descendants = {node_id}
            for index, item in enumerate(self.model._records):
                if item.get("parentId") in descendants:
                    descendants.add(str(item.get("nodeId") or ""))
                    if item.get("hasChildren"):
                        self.model.set_value(index, "expanded", expanded)
        self._update_visibility()

    def _update_visibility(self) -> None:
        by_id = {
            record.get("nodeId"): record for record in self.model._records
        }
        for index, record in enumerate(self.model._records):
            parent_id = record.get("parentId")
            visible = True
            while parent_id:
                parent = by_id.get(parent_id)
                if not parent:
                    break
                if not parent.get("expanded"):
                    visible = False
                    break
                parent_id = parent.get("parentId")
            self.model.set_value(index, "rowVisible", visible)
        self.stateChanged.emit()

    @Slot(str)
    def toggle_kind(self, kind: str) -> None:
        rows = [
            index for index, record in enumerate(self.model._records)
            if record.get("checkable")
            and (kind == "all" or record.get("kind") == kind)
        ]
        checked = any(
            not self.model._records[index].get("checked") for index in rows
        )
        if self.model.set_role_for_rows(rows, "checked", checked):
            self.stateChanged.emit()

    def _ignore_dict(self) -> dict:
        ignore = {
            "children": [],
            "processes": {},
            "builtins": [],
            "show_builtins": False,
        }
        for record in self.model._records:
            kind = record.get("kind")
            if kind == "process":
                ignore["processes"].setdefault(record.get("group"), [])
            if record.get("checked") or not record.get("checkable"):
                continue
            if kind == "child":
                ignore["children"].append(record.get("key"))
            elif kind == "builtin":
                ignore["builtins"].append(record.get("key"))
            elif kind == "process":
                ignore["processes"][record.get("group")].append(
                    record.get("key")
                )
        if not any((
            ignore["children"], ignore["builtins"],
            any(ignore["processes"].values()),
        )):
            return {}
        return ignore

    @Slot(result=bool)
    def save(self) -> bool:
        context = dict(self._context() or {})
        if self._key(context) != self._context_key or not self.valid_context:
            self._notify(
                "The active project or search tab changed. Reopen the editor."
            )
            return False
        ignore = self._ignore_dict()
        from thlib.environment import env_write_config

        env_write_config(
            ignore,
            filename="process_ignore_dict",
            unique_id=self._settings_path(context),
            long_abs_path=True,
        )
        self._original_ignore = dict(ignore)
        self._apply_settings(ignore)
        self.stateChanged.emit()
        return True

    @Slot()
    def cancel(self) -> None:
        records = [dict(record) for record in self.model._records]
        self._apply_ignore(records, self._original_ignore)
        for record in records:
            record["selected"] = False
        self.model.replace(records)
        self.stateChanged.emit()

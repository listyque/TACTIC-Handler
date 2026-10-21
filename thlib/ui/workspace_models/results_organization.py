"""Sorting and grouping for workspace result roots."""

from __future__ import annotations

import re

from PySide6.QtCore import QCoreApplication

from ..search_contract import parse_column_group_mode, parse_column_sort_mode
from .results_types import WorkspaceNode


class OrganizationMixin:
    _natural_parts = re.compile(r"(\d+)")

    @classmethod
    def _natural_key(cls, value) -> tuple:
        return tuple(
            int(part) if part.isdigit() else part.casefold()
            for part in cls._natural_parts.split(str(value or ""))
        )

    @staticmethod
    def _source_info(node: WorkspaceNode) -> dict:
        try:
            return dict(node.source.get_info() or {})
        except (AttributeError, TypeError, ValueError):
            return dict(node.values or {})

    def set_organization(
        self,
        sort_mode: str = "name_asc",
        group_mode: str = "none",
        task_process: str = "",
        task_records: dict | None = None,
        loaded_task_codes: set | None = None,
        task_statuses: list[dict] | None = None,
        rebuild: bool = True,
    ) -> None:
        self._sort_mode = sort_mode if (
            sort_mode in {
                "name_asc", "name_desc", "updated_desc", "updated_asc",
            } or parse_column_sort_mode(sort_mode)
        ) else "name_asc"
        self._group_mode = (
            group_mode if group_mode in {
                "none", "status", "pipeline", "task_status",
            } or parse_column_group_mode(group_mode) else "none"
        )
        self._task_group_process = str(task_process or "")
        self._task_group_records = {
            str(code): list(tasks or ())
            for code, tasks in (task_records or {}).items()
        }
        self._task_group_loaded_codes = {
            str(code) for code in (loaded_task_codes or set())
        }
        self._task_group_statuses = [
            dict(record) for record in (task_statuses or ())
        ]
        if rebuild and hasattr(self, "_roots"):
            self._rebuild_organized_rows()

    def _sorted_roots(self) -> list[WorkspaceNode]:
        roots = list(self._roots)
        column_sort = parse_column_sort_mode(self._sort_mode)
        if column_sort:
            column, descending = column_sort

            def key(node):
                return self._natural_key(self._source_info(node).get(column))
        elif self._sort_mode.startswith("updated_"):
            def key(node):
                info = self._source_info(node)
                return self._natural_key(
                    info.get("timestamp") or info.get("last_updated") or ""
                )
        else:
            def key(node):
                return self._natural_key(node.title or node.code)
        roots.sort(
            key=lambda node: (key(node), self._natural_key(node.code)),
            reverse=(
                column_sort[1]
                if column_sort else self._sort_mode.endswith("_desc")
            ),
        )
        return roots

    @staticmethod
    def _translated(text: str) -> str:
        return QCoreApplication.translate("WorkspaceResults", text)

    def _task_group_value(self, node: WorkspaceNode) -> tuple[str, str, int]:
        code = str(node.code or "")
        if code not in self._task_group_loaded_codes:
            return self._translated("Loading task status:"), node.accent, -1
        tasks = self._task_group_records.get(code, ())
        statuses = []
        has_task = False
        for task in tasks:
            try:
                info = dict(task.get_info() or {})
            except (AttributeError, TypeError, ValueError):
                info = dict(getattr(task, "info", {}) or {})
            if str(info.get("process") or "") != self._task_group_process:
                continue
            has_task = True
            status = str(info.get("status") or "")
            if status and status not in statuses:
                statuses.append(status)
        if not statuses:
            return (
                self._translated("No status" if has_task else "No task"),
                node.accent,
                9_999 if has_task else 10_000,
            )
        catalog = {
            str(record.get("key") or ""): (index, str(
                record.get("accent") or node.accent
            ))
            for index, record in enumerate(self._task_group_statuses)
        }
        status = min(
            statuses,
            key=lambda value: (
                catalog.get(value, (9_000, ""))[0],
                self._natural_key(value),
            ),
        )
        rank, accent = catalog.get(status, (9_000, node.accent))
        return status, accent, rank

    def _group_value(self, node: WorkspaceNode) -> tuple[str, str, int]:
        info = self._source_info(node)
        column = parse_column_group_mode(self._group_mode)
        if column:
            value = (node.values or {}).get(column)
            if value is None:
                value = info.get(column)
            if value is None and column == "code":
                value = node.code
            if value is None and column in {"name", "title"}:
                value = node.title
            if isinstance(value, (list, tuple, set)):
                value = ", ".join(str(item) for item in value)
            value = str(value or "")
            return (
                value or self._translated("No value"), node.accent,
                0 if value else 10_000,
            )
        if self._group_mode == "task_status":
            return self._task_group_value(node)
        if self._group_mode == "pipeline":
            value = str(info.get("pipeline_code") or "")
            return (
                value or self._translated("No pipeline"), node.accent,
                0 if value else 10_000,
            )
        value = str(info.get("status") or info.get("state") or "")
        return (
            value or self._translated("No status"), node.accent,
            0 if value else 10_000,
        )

    def _organized_groups(self) -> list[WorkspaceNode]:
        if self._group_mode == "none":
            return []
        buckets: dict[str, dict] = {}
        for root in self._sorted_roots():
            title, accent, rank = self._group_value(root)
            column = parse_column_group_mode(self._group_mode)
            parent = (root.values.get("__tableParentGroups") or {}).get(column)
            key = parent["groupKey"] if parent else title
            if parent:
                rank = 0
                title = parent.get("text") or self._translated(
                    "Parent unavailable" if parent.get("missingParentKey") else "No parent"
                )
            bucket = buckets.setdefault(key, {
                "title": title,
                "parent": parent,
                "accent": accent,
                "rank": rank,
                "children": [],
            })
            bucket["rank"] = min(bucket["rank"], rank)
            bucket["children"].append(root)
        def order(item):
            key, bucket = item
            is_parent = bool(bucket["parent"])
            # Match JavaScript's canonical-key ordering for parent groups.
            value = key.encode("utf-16-be", "surrogatepass") if is_parent else self._natural_key(key)
            return bucket["rank"], is_parent, value

        ordered = sorted(buckets.items(), key=order)
        previous = {
            group.values.get("groupKey", group.title): group.expanded
            for group in getattr(self, "_root_groups", ())
        }
        groups = []
        for index, (key, bucket) in enumerate(ordered):
            title = bucket["title"]
            children = bucket["children"]
            groups.append(WorkspaceNode(
                node_id=f"result-group:{self._group_mode}:{index}:{key}",
                node_type="group",
                search_key="",
                code="",
                title=title,
                subtitle=self._translated("{} items").format(len(children)),
                accent=bucket["accent"],
                expanded=previous.get(key, True),
                has_children=bool(children),
                loaded=True,
                child_count=len(children),
                children=children,
                values={"groupMode": self._group_mode, "groupKey": key, "parentGroup": bucket["parent"]},
            ))
        return groups

    def _rebuild_organized_rows(self, preserve_slots: bool = False) -> None:
        self._roots = self._sorted_roots()
        for group in getattr(self, "_root_groups", ()):
            self._nodes.pop(group.node_id, None)
        self._root_groups = self._organized_groups()
        for group in self._root_groups:
            self._nodes[group.node_id] = group
        self._replace_visible_items(
            self._project_visible_rows(self._flatten()),
            preserve_slots=preserve_slots,
        )

    def organized_flatten(self) -> list[WorkspaceNode] | None:
        if not getattr(self, "_root_groups", None):
            return None
        result = []

        def visit(node: WorkspaceNode) -> None:
            result.append(node)
            if node.expanded:
                for child in node.children:
                    visit(child)

        for group in self._root_groups:
            result.append(group)
            if group.expanded:
                for root in group.children:
                    visit(root)
        return result

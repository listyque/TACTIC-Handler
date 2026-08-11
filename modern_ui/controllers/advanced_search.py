"""Application controller: advanced search."""

from __future__ import annotations

from collections.abc import Callable
import json
import math
import re
import sys
import time
import traceback
import uuid

from PySide6.QtCore import (
    QDateTime,
    QObject,
    Property,
    QSettings,
    Qt,
    QTimer,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtGui import QGuiApplication, QImage

from ..menu_schema import MenuRegistry
from ..quick_filters import QuickFilterCatalog
from ..repository_sync import RepositorySyncController
from ..models import NavigationModel, ProjectModel
from ..workspace import (
    DockPanelModel,
    FloatingWindowModel,
    SectionTab,
    SectionTabModel,
    WorkspaceItemModel,
    WorkspaceState,
)
from .types import ActionRegistry, SearchTabSession, SectionSession

class AdvancedSearchMixin:
    @Slot()
    def add_search_filter(self) -> None:
        columns = self.workspace_state.filter_column_model._records
        column = ""
        if columns:
            preferred = next(
                (
                    record for record in columns
                    if record.get("value") == "name"
                ),
                columns[0],
            )
            column = str(preferred.get("value") or "")
        records = list(self.workspace_state.filter_model._records)
        is_default = not records
        relations = self.search_filter_relations(column)
        records.append({
            "column": column,
            "relation": (
                "EQI"
                if is_default
                else relations[0].get("value") if relations else "="
            ),
            "value": "",
            "rowEnabled": True,
            "operator": "begin" if is_default else "and",
            "isDefault": is_default,
        })
        self.workspace_state.filter_model.replace(records)

    @Slot()
    def clear_search_filters(self) -> None:
        self.workspace_state.filter_model.clear()
        self.add_search_filter()

    @Slot()
    def ensure_search_filter(self) -> None:
        if not self.workspace_state.filter_model._records:
            self.add_search_filter()

    @Slot(int, str)
    def set_search_filter_column(self, row: int, column: str) -> None:
        model = self.workspace_state.filter_model
        if not 0 <= row < len(model._records):
            return
        choices = self.search_filter_relations(column)
        model.set_value(row, "column", column)
        model.set_value(
            row,
            "relation",
            choices[0].get("value") if choices else "=",
        )

    @Slot(str, result="QVariantList")
    def search_filter_relations(self, column: str) -> list[dict]:
        import thlib.tactic_classes as tc

        stype = self._active_stype()
        column_type = "_expression" if column == "_expression" else "all"
        if stype and column != "_expression":
            try:
                column_type = stype.get_column_data_type(column) or "all"
            except (AttributeError, KeyError, TypeError):
                column_type = "all"
        return [
            {"label": str(label), "value": relation}
            for label, relation in tc.get_match_list_by_type(column_type)
        ]

    @Slot()
    def clear_advanced_filter_suggestions(self) -> None:
        self._pending_filter_suggestion = None
        if self._filter_suggestion_worker is not None:
            self._filter_suggestion_worker.cancel()
        self._filter_suggestion_request_id = ""
        self._filter_suggestion_row = -1
        self.workspace_state.advanced_filter_suggestion_model.clear()
        self.advanced_filter_suggestions_changed.emit()

    @Slot(int, str, str)
    def request_advanced_filter_suggestions(
        self,
        row: int,
        column: str,
        value: str,
    ) -> None:
        value = (value or "").strip()
        stype = self._active_stype()
        if not value or not stype or column == "_expression":
            self.clear_advanced_filter_suggestions()
            return
        columns_info = stype.get_columns_info() or {}
        if column not in columns_info:
            self.clear_advanced_filter_suggestions()
            return
        if self._filter_suggestion_worker is not None:
            self._pending_filter_suggestion = (row, column, value)
            self._filter_suggestion_worker.cancel()
            return
        self._pending_filter_suggestion = None
        from thlib.search_helpers import get_suggestion_filter
        from thlib.environment import env_inst
        import thlib.tactic_classes as tc

        columns = [column]
        for extra in ("keywords", "code", "description"):
            if extra in columns_info and extra not in columns:
                columns.append(extra)
        filters = get_suggestion_filter(column, value, columns)
        request_id = uuid.uuid4().hex
        self._filter_suggestion_request_id = request_id
        self._filter_suggestion_row = row
        self.advanced_filter_suggestions_changed.emit()
        project = stype.get_project()

        def query_suggestions():
            return tc.server_query(
                filters=filters,
                stype=stype.get_code(),
                columns=columns,
                project=project.get_code(),
                limit=20,
                offset=0,
            )

        try:
            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            worker = env_inst.server_pool.add_task(query_suggestions)
            if worker is None:
                raise RuntimeError("Server worker pool is not available")
            self._filter_suggestion_worker = worker
            worker.add_result_data((request_id, row, column, value))
            worker.result.connect(self._advanced_filter_suggestions_result)
            worker.error.connect(self._advanced_filter_suggestions_error)
            worker.settled.connect(
                self._advanced_filter_suggestion_worker_settled,
                Qt.ConnectionType.QueuedConnection,
            )
            worker.start()
        except Exception as error:
            self.clear_advanced_filter_suggestions()
            self._notify(str(error))

    @Slot(object)
    def _advanced_filter_suggestion_worker_settled(self, worker) -> None:
        if self._filter_suggestion_worker is worker:
            self._filter_suggestion_worker = None
        pending = self._pending_filter_suggestion
        self._pending_filter_suggestion = None
        if pending:
            QTimer.singleShot(
                0,
                lambda values=pending:
                    self.request_advanced_filter_suggestions(*values),
            )

    @Slot(object)
    def _advanced_filter_suggestions_result(self, result) -> None:
        records, metadata = result
        request_id, row, column, key = metadata
        if request_id != self._filter_suggestion_request_id:
            return
        self._filter_suggestion_worker = None
        suggestions = []
        seen = set()
        for record in records or []:
            title = record.get(column)
            if title in (None, ""):
                continue
            title = str(title)
            if title in seen:
                continue
            seen.add(title)
            keywords = str(record.get("keywords") or "")
            keyword = next(
                (
                    candidate
                    for candidate in keywords.replace(",", " ").split()
                    if key in candidate
                ),
                "",
            )
            suggestions.append({
                "title": title,
                "description": " ".join(
                    str(record.get("description") or "").splitlines()
                ),
                "keyword": keyword,
                "values": {column: title},
            })
        self._filter_suggestion_row = row
        self.workspace_state.advanced_filter_suggestion_model.replace(
            suggestions
        )
        self.advanced_filter_suggestions_changed.emit()

    @Slot(object)
    def _advanced_filter_suggestions_error(self, error) -> None:
        payload, worker = error
        metadata = worker.get_result_data() if worker else None
        if metadata and metadata[0] != self._filter_suggestion_request_id:
            return
        self._filter_suggestion_worker = None
        self._report_error_payload(
            payload,
            "server/advanced_filter_suggestions",
            worker,
        )
        self.clear_advanced_filter_suggestions()

    @Slot(int, int)
    def accept_advanced_filter_suggestion(
        self,
        filter_row: int,
        suggestion_row: int,
    ) -> None:
        filters = self.workspace_state.filter_model._records
        suggestions = (
            self.workspace_state.advanced_filter_suggestion_model._records
        )
        if (
            not 0 <= filter_row < len(filters)
            or not 0 <= suggestion_row < len(suggestions)
        ):
            return
        column = str(filters[filter_row].get("column") or "")
        suggestion = suggestions[suggestion_row]
        value = (
            (suggestion.get("values") or {}).get(column)
            or suggestion.get("title")
            or ""
        )
        self.workspace_state.filter_model.set_value(
            filter_row, "value", value
        )
        self.clear_advanced_filter_suggestions()

    @Slot(str)
    def set_search_tab_title(self, value: str) -> None:
        tab = self._current_tab()
        section = self._current_section()
        if not tab or not section:
            return
        title = value.strip() or section.title
        if tab.title == title:
            return
        pending_filters = [
            dict(record)
            for record in self.workspace_state.filter_model._records
        ]
        tab.title = title
        self._sync_search_tabs(clear_suggestions=False)
        self.workspace_state.filter_model.replace(pending_filters)

    @staticmethod
    def _filter_records_from_filters(filters) -> list[dict]:
        values = list(filters or [])
        tuples = [
            (index, value)
            for index, value in enumerate(values)
            if isinstance(value, tuple) and len(value) == 3
        ]
        records = []
        for row, (position, value) in enumerate(tuples):
            operator = "begin" if row == 0 else "and"
            if row > 0 and position + 1 < len(values):
                candidate = values[position + 1]
                if candidate in {"and", "or"}:
                    operator = candidate
            records.append({
                "column": str(value[0]),
                "relation": value[1],
                "value": value[2],
                "rowEnabled": True,
                "operator": operator,
                "isDefault": row == 0,
            })
        return records

    @staticmethod
    def _filters_from_records(records) -> list:
        active_records = []
        for record in records:
            column = str(record.get("column") or "")
            if not record.get("rowEnabled") or not column:
                continue
            value = record.get("value")
            relation = record.get("relation")
            if str(value or "").strip() == "" and relation is not None:
                continue
            active_records.append((
                record,
                (column, relation, value),
            ))
        filters = []
        for index, (record, filter_value) in enumerate(active_records):
            if index == 0:
                if len(active_records) > 1:
                    filters.append("begin")
                filters.append(filter_value)
                continue
            filters.append(filter_value)
            filters.append(
                "or" if record.get("operator") == "or" else "and"
            )
        return filters

    @Slot()
    def apply_search_filters(self) -> None:
        tab = self._current_tab()
        if not tab:
            return
        if not self._applying_tag_filters:
            tab.selected_tags.clear()
            tab.tag_column = ""
        filters = self._filters_from_records(
            self.workspace_state.filter_model._records
        )
        self._capture_current_tree_state()
        tab.extra_filters = filters
        tab.offset = 0
        tab.next_offset = 0
        tab.exhausted = False
        tab.duplicate_pages = 0
        tab.loaded = False
        tab.workspace_roots.clear()
        self._load_tab(tab, append=False)

    def apply_filter_editor_records(
        self,
        records: list[dict],
        title: str = "",
        process_ignore: dict | None = None,
    ) -> None:
        tab = self._current_tab()
        section = self._current_section()
        if not tab or not section:
            return
        tab.title = title.strip() or section.title
        tab.selected_tags.clear()
        tab.tag_column = ""
        tab.process_ignore = dict(process_ignore or {})
        self.workspace_model.set_process_ignore(tab.process_ignore)
        self.workspace_state.filter_model.replace([
            dict(record) for record in records
        ])
        self.apply_search_filters()

    def has_active_search_tab(self) -> bool:
        return self._current_tab() is not None

    def filter_editor_context(self) -> dict:
        tab = self._current_tab()
        section = self._current_section()
        stype = self._active_stype()
        if not tab or not section or not stype:
            return {}
        try:
            project = stype.get_project()
            project_type = project.get_type()
        except (AttributeError, KeyError, TypeError):
            project = None
            project_type = ""
        return {
            "project": project,
            "project_code": self._current_project_code,
            "project_type": project_type,
            "search_type": section.search_type,
            "tab_id": tab.tab_id,
            "tab_name": section.search_type.rsplit("/", 1)[-1],
            "tab_title": tab.title,
            "stype": stype,
        }

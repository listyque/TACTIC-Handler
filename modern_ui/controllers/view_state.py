"""Application controller: view state."""

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

class ViewStateMixin:
    def _set_server_state(self, state: str, message: str) -> None:
        self._server_state = state
        self._server_message = message
        self.server_state_changed.emit()

    def quick_filter_editor_context(self) -> dict:
        section = self._current_section()
        tab = self._current_tab()
        if not section or not tab:
            return {}
        return {
            "project_code": str(self._current_project_code or ""),
            "search_type": str(section.search_type or ""),
            "title": str(section.title or tab.title or ""),
            "groups": self._quick_filters.editor_groups(
                section.search_type,
                tab.stype or self._active_stype(),
                tab.sobjects,
                tab.quick_filter_tasks,
            ),
        }

    def apply_quick_filter_configuration(
            self, search_type: str, configuration: dict | None
    ) -> None:
        configuration = configuration or {}
        if self._quick_filters.configuration(search_type) == configuration:
            self.quick_filters_changed.emit()
            return
        self._quick_filters.set_configuration(search_type, configuration)
        settings = {
            str(group.get("key") or ""): group
            for group in configuration.get("groups", ())
            if isinstance(group, dict) and group.get("key")
        }
        for session in self._sessions.values():
            if session.search_type != search_type:
                continue
            for session_tab in session.tabs:
                for key in list(session_tab.quick_filters):
                    group = settings.get(key)
                    if group and group.get("enabled", True) is False:
                        session_tab.quick_filters.pop(key, None)
                        continue
                    options = group.get("options") if group else None
                    if isinstance(options, list):
                        session_tab.quick_filters[key].intersection_update(
                            str(value) for value in options
                        )
                        if not session_tab.quick_filters[key]:
                            session_tab.quick_filters.pop(key, None)
        section = self._current_section()
        tab = self._current_tab()
        if not section or not tab or section.search_type != search_type:
            self.quick_filters_changed.emit()
            return
        visible_groups = {
            group["key"]: {
                str(option["key"]) for option in group.get("options", ())
            }
            for group in self._quick_filters.groups(
                section.search_type,
                tab.stype or self._active_stype(),
                tab.sobjects,
                tab.quick_filters,
                tab.quick_filter_tasks,
            )
        }
        for key in list(tab.quick_filters):
            if key not in visible_groups:
                tab.quick_filters.pop(key, None)
                continue
            tab.quick_filters[key].intersection_update(visible_groups[key])
            if not tab.quick_filters[key]:
                tab.quick_filters.pop(key, None)
        self._apply_quick_filters(tab)

















    @Slot(str, str)
    def toggle_quick_filter(self, group_key: str, option_key: str) -> None:
        tab = self._current_tab()
        if not tab:
            return
        group_key = str(group_key or "")
        option_key = str(option_key or "")
        if not group_key:
            return
        if not option_key:
            tab.quick_filters.pop(group_key, None)
        else:
            selected = tab.quick_filters.setdefault(group_key, set())
            if option_key in selected:
                selected.remove(option_key)
            else:
                selected.add(option_key)
            if not selected:
                tab.quick_filters.pop(group_key, None)

        self._apply_quick_filters(tab)

    def _apply_quick_filters(self, tab) -> None:
        self._card_path.clear()
        self._pending_card_focus_id = ""
        visible_sobjects = self._visible_sobjects(tab)
        self.workspace_model.replace_sobjects(visible_sobjects, tab.stype)
        if tab.view_mode == "tiles":
            self.workspace_model.show_card_level()
        tab.workspace_roots = list(self.workspace_model._roots)

        if not self.workspace_model.node_for(tab.selected_node_id):
            tab.selected_node_id = ""
            tab.selected_node_ids.clear()
            tab.selection_anchor_id = ""
            tab.clear_details()
            self.workspace_state.clear_selection()
        self._set_result_state(tab)
        self.quick_filters_changed.emit()
        self.section_state_changed.emit()

    @Slot()
    def request_quick_filter_data(self) -> None:
        """Warm the per-tab task facet cache with one batched task query."""
        tab = self._current_tab()
        section = self._current_section()
        if (
                not tab or not section or not tab.sobjects
                or not self._quick_filters.requires_tasks(section.search_type)):
            return
        object_by_code = {}
        for sobject in tab.sobjects:
            try:
                code = str(sobject.get_code() or "")
            except AttributeError:
                code = str(
                    (getattr(sobject, "info", {}) or {}).get("code") or ""
                )
            if code:
                object_by_code[code] = sobject
        missing = set(object_by_code) - tab.quick_filter_task_codes
        fresh = (
            tab.quick_filter_task_loaded_at > 0
            and time.monotonic() - tab.quick_filter_task_loaded_at < 60.0
        )
        if fresh and not missing:
            return
        requested_codes = set(object_by_code) if not fresh else missing
        targets = [object_by_code[code] for code in requested_codes]
        if not targets:
            return
        previous = self._quick_filter_workers.pop(tab.tab_id, None)
        if previous is not None:
            try:
                previous.cancel()
            except (AttributeError, RuntimeError):
                pass
        request_id = uuid.uuid4().hex
        tab.quick_filter_task_request_id = request_id
        try:
            import thlib.tactic_classes as tc
            from thlib.environment import env_inst

            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()

            def query_tasks():
                return (
                    tc.SObject.get_multiple_tasks_sobjects(targets) or {},
                )

            worker = env_inst.server_pool.add_task(query_tasks)
            if worker is None:
                raise RuntimeError("Server worker pool is not available")
            self._quick_filter_workers[tab.tab_id] = worker
            worker.add_result_data((
                section.entry_key,
                tab.tab_id,
                request_id,
                tuple(requested_codes),
            ))
            worker.result.connect(
                self._quick_filter_tasks_ready,
                Qt.ConnectionType.QueuedConnection,
            )
            worker.error.connect(
                self._quick_filter_tasks_failed,
                Qt.ConnectionType.QueuedConnection,
            )
            worker.start()
        except Exception as error:
            self._quick_filter_tasks_failed(({
                "exception": error,
                "stacktrace": traceback.format_exc(),
            }, None))

    @Slot(object)
    def _quick_filter_tasks_ready(self, result) -> None:
        grouped, metadata = result
        section_key, tab_id, request_id, requested_codes = metadata
        tab = self._find_tab(section_key, tab_id)
        self._quick_filter_workers.pop(tab_id, None)
        if not tab or tab.quick_filter_task_request_id != request_id:
            return
        normalized = {}
        for code, tasks in (grouped or {}).items():
            normalized[str(code)] = list(tasks or ())
        for code in requested_codes:
            code = str(code)
            tab.quick_filter_tasks[code] = normalized.get(code, [])
            tab.quick_filter_task_codes.add(code)
        tab.quick_filter_task_loaded_at = time.monotonic()
        if tab is self._current_tab():
            active_task_filters = set(tab.quick_filters).intersection({
                "process", "status",
            })
            if active_task_filters:
                self._apply_quick_filters(tab)
            else:
                self.quick_filters_changed.emit()

    @Slot(object)
    def _quick_filter_tasks_failed(self, error) -> None:
        payload, worker = error
        metadata = worker.get_result_data() if worker else None
        if metadata:
            section_key, tab_id, request_id, _codes = metadata
            tab = self._find_tab(section_key, tab_id)
            if tab and tab.quick_filter_task_request_id == request_id:
                tab.quick_filter_task_request_id = ""
            self._quick_filter_workers.pop(tab_id, None)
        self._report_error_payload(
            payload,
            "search/quick_filters",
            worker=worker,
            command="load task facets",
        )





    def _records_without_tag_filters(self, tab) -> list[dict]:
        records = self._filter_records_from_filters(tab.extra_filters)
        if not tab.tag_column or not tab.selected_tags:
            return records
        generated_values = {
            f"%{tag}%" for tag in tab.selected_tags
        }
        return [
            record for record in records
            if not (
                record.get("column") == tab.tag_column
                and record.get("relation") == "like"
                and record.get("value") in generated_values
            )
        ]

    @Slot()
    def request_tag_cloud(self) -> None:
        tab = self._current_tab()
        section = self._current_section()
        stype = self._active_stype()
        if not tab or not section or not stype:
            return
        try:
            columns_info = stype.get_columns_info() or {}
        except (AttributeError, TypeError):
            columns_info = {}
        column = next(
            (
                name for name in ("keywords", "tags", "tag")
                if name in columns_info
            ),
            "",
        )
        if not column:
            self._tag_records = []
            self._tag_error = "This search type has no tag column."
            self._tag_loading = False
            self.tag_cloud_changed.emit()
            return
        request_id = uuid.uuid4().hex
        context = (
            self._current_project_code,
            section.entry_key,
            tab.tab_id,
            column,
        )
        self._tag_request_id = request_id
        self._tag_records = []
        self._tag_error = ""
        self._tag_loading = True
        self.tag_cloud_changed.emit()
        try:
            from thlib.environment import env_inst
            import thlib.tactic_classes as tc
            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            project = stype.get_project()
            filters = self._filters_from_records(
                self._records_without_tag_filters(tab)
            )
            tab.tag_column = column

            def query_tags():
                return (tc.server_query(
                    filters=filters,
                    stype=stype.get_code(),
                    columns=[column],
                    project=project.get_code(),
                    limit=2000,
                    offset=0,
                ),)

            worker = env_inst.server_pool.add_task(query_tags)
            worker.add_result_data((request_id, context))
            worker.result.connect(self._tag_cloud_result)
            worker.error.connect(self._tag_cloud_error)
            worker.start()
        except Exception as error:
            self._tag_loading = False
            self._tag_error = str(error)
            self.tag_cloud_changed.emit()
            self._notify(str(error))

    @Slot(object)
    def _tag_cloud_result(self, result) -> None:
        records, metadata = result
        request_id, context = metadata
        tab = self._current_tab()
        section = self._current_section()
        current = (
            self._current_project_code,
            section.entry_key if section else "",
            tab.tab_id if tab else "",
            context[3],
        )
        if request_id != self._tag_request_id or context != current:
            return
        counts: dict[str, int] = {}
        labels: dict[str, str] = {}
        column = context[3]
        for record in records or []:
            value = str(record.get(column) or "")
            for tag in re.split(r"[,;\s]+", value):
                tag = tag.strip()
                if not tag:
                    continue
                key = tag.casefold()
                counts[key] = counts.get(key, 0) + 1
                labels.setdefault(key, tag)
        maximum = max(counts.values(), default=1)
        self._tag_records = [
            {
                "tag": labels[key],
                "count": count,
                "weight": math.log1p(count) / math.log1p(maximum),
                "column": column,
            }
            for key, count in sorted(
                counts.items(),
                key=lambda item: (-item[1], labels[item[0]].casefold()),
            )
        ]
        self._tag_loading = False
        self._tag_error = "" if self._tag_records else "No tags found."
        self.tag_cloud_changed.emit()

    @Slot(object)
    def _tag_cloud_error(self, error) -> None:
        payload, worker = error
        metadata = worker.get_result_data() if worker else None
        if metadata and metadata[0] != self._tag_request_id:
            return
        self._report_error_payload(payload, "server/tag_cloud", worker)
        self._tag_loading = False
        self._tag_error = str(payload.get("exception") or error)
        self.tag_cloud_changed.emit()

    @Slot(str)
    def toggle_tag(self, value: str) -> None:
        tab = self._current_tab()
        if not tab:
            return
        base_records = self._records_without_tag_filters(tab)
        value = str(value or "")
        if not value:
            tab.selected_tags.clear()
        elif value in tab.selected_tags:
            tab.selected_tags.remove(value)
        else:
            tab.selected_tags.add(value)
        if not tab.tag_column:
            context_column = (
                self._tag_records[0].get("column")
                if self._tag_records else ""
            )
            tab.tag_column = str(context_column or "keywords")
        tag_records = [
            {
                "column": tab.tag_column,
                "relation": "like",
                "value": f"%{tag}%",
                "rowEnabled": True,
                "operator": (
                    "and" if index == 0 and base_records
                    else "begin" if index == 0
                    else "or"
                ),
                "isDefault": not base_records and index == 0,
                "dataType": "all",
            }
            for index, tag in enumerate(sorted(tab.selected_tags))
        ]
        records = base_records + tag_records
        if records:
            records[0]["operator"] = "begin"
            records[0]["isDefault"] = True
            for record in records[1:]:
                record["isDefault"] = False
        self.workspace_state.filter_model.replace(records)
        self._applying_tag_filters = True
        try:
            self.apply_search_filters()
        finally:
            self._applying_tag_filters = False
        self.tag_cloud_changed.emit()








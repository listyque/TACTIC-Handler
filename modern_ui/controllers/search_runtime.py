"""Application controller: search runtime."""

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

class SearchRuntimeMixin:
    @staticmethod
    def _query_sobjects(
        search_type: str,
        project_code: str,
        base_filters: tuple,
        extra_filters: list,
        limit: int,
        offset: int,
    ):
        import thlib.tactic_classes as tc
        from thlib.environment import env_inst

        kwargs = {
            "filters": list(base_filters) + list(extra_filters or []),
            "project_code": project_code,
            "limit": limit,
            "offset": offset,
        }
        try:
            result = tc.get_sobjects(
                search_type,
                check_snapshots_updates=tc.get_snapshots_updates_list(
                    search_type,
                    project_code,
                ),
                include_progress=True,
                include_total_count=False,
                **kwargs,
            )
        except Exception as error:
            message = str(error).lower()
            if not (
                "include_progress" in message
                or (
                    "unexpected" in message
                    and ("argument" in message or "keyword" in message)
                )
            ):
                raise
            result = tc.get_sobjects(search_type, **kwargs)
        if not result:
            return [], {}, None
        sobjects, info = result
        if search_type.startswith("sthpw"):
            stype = env_inst.get_stype_by_code(search_type)
        else:
            project = env_inst.get_project_by_code(project_code)
            stype = (
                project.get_stypes().get(search_type)
                if project else None
            )
        return list(sobjects.values()), info, stype

    def _set_loading(self, value: bool, message: str = "") -> None:
        changed = self._loading != value or (
            value and message and self._loading_message != message
        )
        self._loading = value
        self._loading_message = message if value else ""
        if message:
            if value:
                status = "START"
            elif "fail" in message.lower() or "error" in message.lower():
                status = "FAILED"
            else:
                status = "DONE"
            self._append_activity(f"{status} · {message}")
        if changed:
            self.loading_changed.emit()

    def _set_result_state(self, tab: SearchTabSession) -> None:
        section = self._current_section()
        self._result_count = (
            len(self._visible_sobjects(tab, section))
            if tab.quick_filters else tab.total
        )
        self._current_page_key = section.entry_key if section else ""
        self._current_page_title = f"{section.title} / {tab.title}" if section else tab.title
        self.result_count_changed.emit()
        self.paging_state_changed.emit()
        self.page_changed.emit(self._current_page_key, self._current_page_title)

    def _load_tab(self, tab: SearchTabSession, append: bool = False) -> None:
        section = self._current_section()
        if not section:
            return
        previous_worker = self._search_workers.get(tab.tab_id)
        if previous_worker is not None:
            self._pending_search_loads[tab.tab_id] = (tab, append)
            previous_worker.cancel()
            return
        request_signature = json.dumps(
            {
                "section": section.entry_key,
                "filters": tab.extra_filters,
                "offset": tab.next_offset if append else tab.offset,
                "append": append,
            },
            ensure_ascii=False,
            default=str,
            sort_keys=True,
        )
        if request_signature != tab.failure_signature:
            tab.failure_signature = request_signature
            tab.failure_count = 0
        if tab.failure_count >= 3:
            tab.error = "Retry limit reached for this search"
            self._set_loading(False, tab.error)
            self.search_state_changed.emit()
            return
        from thlib.environment import env_inst
        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        request_id = uuid.uuid4().hex
        tab.request_id = request_id
        tab.started_at = time.perf_counter()
        tab.loading = True
        tab.error = ""
        tab.cancelled = False
        self._active_request_id = request_id
        request_offset = tab.next_offset if append else tab.offset
        if not append:
            self._card_path.clear()
            self._pending_card_focus_id = ""
            tab.clear_details()
            tab.sobjects = []
            tab.quick_filter_tasks.clear()
            tab.quick_filter_task_codes.clear()
            tab.quick_filter_task_loaded_at = 0.0
            tab.quick_filter_task_request_id = ""
            tab.workspace_roots.clear()
            if tab is self._current_tab():
                self.workspace_model.clear()
                self.versions_model.clear()
                self.workspace_state.clear_selection()
        self._set_loading(
            True,
            f"{'Loading more' if append else 'Loading'} {section.title}",
        )
        worker = env_inst.server_pool.add_task(
            self._query_sobjects,
            section.search_type,
            self._current_project_code,
            section.base_filters,
            tab.extra_filters,
            limit=tab.limit,
            offset=request_offset,
        )
        if worker is None:
            tab.loading = False
            tab.error = "Server worker pool is not available"
            self._set_loading(False, tab.error)
            self.search_state_changed.emit()
            return
        self._search_workers[tab.tab_id] = worker
        worker.add_result_data((
            section.entry_key,
            tab.tab_id,
            append,
            request_id,
            request_offset,
        ))
        worker.result.connect(self._async_query_result)
        worker.error.connect(self._async_query_error)
        worker.settled.connect(
            self._search_worker_settled,
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()
        self.search_state_changed.emit()

    @Slot(object)
    def _search_worker_settled(self, worker) -> None:
        metadata = worker.get_result_data() if worker else None
        if not metadata or len(metadata) < 2:
            return
        section_key, tab_id = metadata[:2]
        if self._search_workers.get(tab_id) is worker:
            self._search_workers.pop(tab_id, None)
        pending = self._pending_search_loads.pop(tab_id, None)
        if pending:
            tab, append = pending
            section = self._sessions.get(section_key)
            if (
                not section
                or self._current_section_key != section_key
                or section.current_tab_id != tab_id
                or self._find_tab(section_key, tab_id) is not tab
            ):
                return
            QTimer.singleShot(
                0,
                lambda current=tab, more=append: self._load_tab(current, more),
            )

    def _find_tab(self, section_key: str, tab_id: str) -> SearchTabSession | None:
        section = self._sessions.get(section_key)
        if not section:
            return None
        return next((tab for tab in section.tabs if tab.tab_id == tab_id), None)

    @Slot(object)
    def _async_query_result(self, result) -> None:
        sobjects, info, stype, metadata = result
        section_key, tab_id, append, request_id, request_offset = metadata
        details_search_key = ""
        details_process = None
        details_snapshot_code = None
        tab = self._find_tab(section_key, tab_id)
        if not tab or tab.request_id != request_id:
            return
        self._search_workers.pop(tab_id, None)
        tab.loading = False
        tab.error = ""
        tab.cancelled = False
        tab.failure_count = 0
        previous_count = len(tab.sobjects)
        if append:
            known = {sobject.get_search_key() for sobject in tab.sobjects}
            tab.sobjects.extend(
                sobject for sobject in sobjects
                if sobject.get_search_key() not in known
            )
        else:
            tab.sobjects = list(sobjects)
        tab.stype = stype
        tab.loaded = True
        raw_count = len(sobjects)
        reported_total = int(
            (info or {}).get("total_sobjects_query_count") or 0
        )
        tab.total = max(reported_total, len(tab.sobjects))
        tab.next_offset = request_offset + raw_count
        tab.exhausted = (
            raw_count == 0
            or raw_count < tab.limit
            or (
                reported_total > 0
                and tab.next_offset >= reported_total
            )
        )
        added_count = len(tab.sobjects) - previous_count
        if append and added_count == 0:
            tab.duplicate_pages += 1
            if tab.duplicate_pages >= 2:
                tab.exhausted = True
        else:
            tab.duplicate_pages = 0
        is_current = (
            section_key == self._current_section_key
            and self._current_section()
            and self._current_section().current_tab_id == tab_id
        )
        if is_current:
            self.workspace_model.set_process_ignore(tab.process_ignore)
            visible_sobjects = self._visible_sobjects(
                tab,
                self._sessions.get(section_key),
            )
            if append and not tab.quick_filters:
                self.workspace_model.append_sobjects(sobjects, stype)
            else:
                self._versions_request_id = ""
                self.versions_model.clear()
                self.workspace_model.replace_sobjects(visible_sobjects, stype)
                if tab.view_mode == "tiles":
                    pending_restore, restored_selection = [], ""
                    self.workspace_model.show_card_level()
                else:
                    pending_restore, restored_selection = (
                        self.workspace_model.apply_tree_state(tab.tree_state)
                    )
                if restored_selection:
                    tab.selected_node_id = restored_selection
                    if not tab.selected_node_ids:
                        tab.selected_node_ids = [restored_selection]
                    if not tab.selection_anchor_id:
                        tab.selection_anchor_id = restored_selection
            tab.workspace_roots = list(self.workspace_model._roots)
            if not append:
                self.workspace_state.load_stype(stype)
                selected = self.workspace_model.node_for(tab.selected_node_id)
                if selected and selected.search_key:
                    details_search_key = selected.search_key
                    if tab.view_mode not in {"continious", "compact"}:
                        self._request_versions(selected.node_id)
                elif visible_sobjects and not tab.selected_node_id:
                    details_search_key = visible_sobjects[0].get_search_key()
                else:
                    self.workspace_state.clear_selection()
                if visible_sobjects and tab.pending_snapshot_code:
                    details_search_key = visible_sobjects[0].get_search_key()
                    details_process = tab.pending_snapshot_process or None
                    details_snapshot_code = tab.pending_snapshot_code
                    tab.pending_snapshot_code = ""
                    tab.pending_snapshot_process = ""
                elif details_search_key and tab.pending_detail_process:
                    details_process = tab.pending_detail_process
                    tab.pending_detail_process = ""
            self._set_result_state(tab)
            if not append:
                self.section_state_changed.emit()
            if not append and pending_restore:
                QTimer.singleShot(
                    0,
                    lambda ids=pending_restore: self._restore_tree_nodes(ids),
                )
        if request_id == self._active_request_id:
            self._set_loading(
                False,
                "Search results loaded · {}".format(
                    self._transaction_metrics(tab.started_at, (sobjects, info))
                ),
            )
        if details_search_key:
            self._load_sobject_details(
                details_search_key,
                process=details_process,
                snapshot_code=details_snapshot_code,
            )
        if self._server_state == "error":
            self._set_server_state("online", "Connected")
        self.search_state_changed.emit()
        self.quick_filters_changed.emit()
        if (
                is_current
                and set(tab.quick_filters).intersection({"process", "status"})):
            QTimer.singleShot(0, self.request_quick_filter_data)
        if (
            append
            and len(tab.sobjects) == previous_count
            and raw_count > 0
            and not tab.exhausted
        ):
            QTimer.singleShot(0, self.load_more)

    @Slot(object)
    def _async_query_error(self, error) -> None:
        payload, worker = error
        section_key, tab_id, append, request_id, _request_offset = (
            worker.get_result_data()
        )
        tab = self._find_tab(section_key, tab_id)
        if not tab or tab.request_id != request_id:
            return
        self._search_workers.pop(tab_id, None)
        self._report_error_payload(payload, "server/search", worker)
        tab.loading = False
        tab.error = str(payload.get("exception") or error)
        tab.cancelled = False
        tab.failure_count += 1
        if not append:
            tab.loaded = False
            tab.sobjects = []
            tab.total = 0
            tab.next_offset = 0
            tab.exhausted = False
            tab.workspace_roots.clear()
        if request_id == self._active_request_id:
            if not append:
                self.workspace_model.clear()
                self.versions_model.clear()
                self.workspace_state.clear_selection()
                self._result_count = 0
                self.result_count_changed.emit()
            self._set_loading(
                False,
                "Search failed · {} · {}".format(
                    self._transaction_metrics(
                        tab.started_at if tab else time.perf_counter()
                    ),
                    payload.get("exception") or error,
                ),
            )
            self._notify(str(payload.get("exception") or error))
            message = tab.error.lower()
            if any(token in message for token in (
                "connection refused",
                "connection reset",
                "timed out",
                "unreachable",
                "failed to establish",
            )):
                self._set_server_state("error", tab.error)
        self.paging_state_changed.emit()
        self.search_state_changed.emit()

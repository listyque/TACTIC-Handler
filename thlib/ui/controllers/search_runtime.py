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
    Qt,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtGui import QGuiApplication, QImage

from ..menu_schema import MenuRegistry
from ..quick_filters import QuickFilterCatalog
from ..repository_sync import RepositorySyncController
from ..search_contract import result_order_bys
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
    def _search_cache_key(
        search_type: str,
        base_filters: tuple,
        extra_filters: list,
        limit: int,
        offset: int,
        sort_mode: str,
    ) -> str:
        order_bys = result_order_bys(sort_mode)
        return json.dumps(
            {
                "searchType": search_type,
                "filters": list(base_filters) + list(extra_filters or []),
                "orderBys": order_bys,
                "limit": limit,
                "offset": offset,
                "snapshots": True,
                "progress": True,
            },
            ensure_ascii=False,
            default=str,
            separators=(",", ":"),
            sort_keys=True,
        )

    @staticmethod
    def _search_stype(search_type: str, project_code: str):
        from thlib.environment import env_inst

        if search_type.startswith("sthpw"):
            return env_inst.get_stype_by_code(search_type)
        project = env_inst.get_project_by_code(project_code)
        return project.get_stypes().get(search_type) if project else None

    @staticmethod
    def _query_sobjects(
        search_type: str,
        project_code: str,
        base_filters: tuple,
        extra_filters: list,
        limit: int,
        offset: int,
        sort_mode: str = "name_asc",
        bypass_cache: bool = False,
    ):
        import thlib.tactic_classes as tc
        from thlib import server_cache

        kwargs = {
            "filters": list(base_filters) + list(extra_filters or []),
            "project_code": project_code,
            "limit": limit,
            "offset": offset,
            "order_bys": result_order_bys(sort_mode),
        }
        cache_key = SearchRuntimeMixin._search_cache_key(
            search_type,
            base_filters,
            extra_filters,
            limit,
            offset,
            sort_mode,
        )
        if bypass_cache:
            server_cache.invalidate_domains(("search",), project_code)
        cache_token = server_cache.token("search", project_code)
        raw_payload = None
        if not bypass_cache:
            raw_payload = server_cache.read_entry(
                "search", cache_key, project_code,
            )
        if isinstance(raw_payload, dict):
            result = tc.hydrate_sobjects_payload(
                raw_payload,
                project_code,
                include_info=True,
                include_snapshots=True,
                include_progress=True,
            )
            cache_hit = True
        else:
            cache_hit = False
        try:
            if not cache_hit:
                fetched = tc.get_sobjects(
                    search_type,
                    check_snapshots_updates=tc.get_snapshots_updates_list(
                        search_type,
                        project_code,
                    ),
                    include_progress=True,
                    include_total_count=False,
                    return_payload=True,
                    **kwargs,
                )
                if (
                        isinstance(fetched, tuple)
                        and len(fetched) == 2
                        and isinstance(fetched[1], dict)
                        and "sobjects_list" in fetched[1]):
                    result, raw_payload = fetched
                else:
                    result = fetched
                    raw_payload = None
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
            raw_payload = None
        if (
                not cache_hit
                and isinstance(raw_payload, dict)
                and cache_token is not None):
            server_cache.write_entry(
                "search", cache_key, raw_payload, project_code,
                expected_token=cache_token,
            )
        if not result:
            return [], {"cacheHit": cache_hit}, None
        sobjects, info = result
        info = dict(info or {})
        info["cacheHit"] = cache_hit
        stype = SearchRuntimeMixin._search_stype(
            search_type, project_code
        )
        return list(sobjects.values()), info, stype

    @staticmethod
    def _query_saved_projection(
        search_type: str,
        project_code: str,
        base_filters: tuple,
        extra_filters: list,
        limit: int,
        page_offsets: list[int],
        sort_mode: str,
        next_offset: int,
        total: int,
        exhausted: bool,
    ):
        """Rebuild one saved tab through cache-first page queries."""
        sobjects = []
        known = set()
        stype = None
        cache_hits = []
        for offset in page_offsets:
            page, page_info, page_stype = SearchRuntimeMixin._query_sobjects(
                search_type,
                project_code,
                base_filters,
                extra_filters,
                limit,
                offset,
                sort_mode,
            )
            cache_hits.append(bool(page_info.get("cacheHit")))
            stype = stype or page_stype
            for sobject in page:
                identity = str(sobject.get_search_key() or "")
                if not identity or identity in known:
                    continue
                known.add(identity)
                sobjects.append(sobject)
        info = {
            "cacheHit": bool(cache_hits) and all(cache_hits),
            "cachedProjection": True,
            "pageOffsets": list(page_offsets),
            "nextOffset": max(0, int(next_offset or 0)),
            "savedTotal": max(0, int(total or 0)),
            "savedExhausted": bool(exhausted),
        }
        return (
            sobjects,
            info,
            stype or SearchRuntimeMixin._search_stype(
                search_type, project_code
            ),
        )

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
        self._result_count = tab.total
        self._current_page_key = section.entry_key if section else ""
        self._current_page_title = f"{section.title} / {tab.title}" if section else tab.title
        self.result_count_changed.emit()
        self.paging_state_changed.emit()
        self.page_changed.emit(self._current_page_key, self._current_page_title)

    def _restore_cached_tab(self, tab: SearchTabSession) -> None:
        section = self._current_section()
        if not section or not tab.loaded_page_offsets:
            self._load_tab(tab, append=False)
            return
        from thlib.environment import env_inst

        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        request_id = uuid.uuid4().hex
        metadata = (
            section.entry_key,
            tab.tab_id,
            False,
            request_id,
            tab.offset,
        )
        tab.request_id = request_id
        tab.started_at = time.perf_counter()
        tab.loading = True
        tab.loading_append = False
        tab.error = ""
        tab.cancelled = False
        self._active_request_id = request_id
        self._card_path.clear()
        self._pending_card_focus_id = ""
        if tab is self._current_tab():
            self.workspace_model.clear()
            self.versions_model.clear()
            self.workspace_state.clear_selection()
        self._set_loading(
            True,
            f"{self.tr('Restoring search session')}: {section.title}",
        )
        worker = env_inst.server_pool.add_task(
            self._query_saved_projection,
            section.search_type,
            self._current_project_code,
            section.base_filters,
            tab.extra_filters,
            tab.limit,
            list(tab.loaded_page_offsets),
            tab.sort_mode,
            tab.next_offset,
            tab.total,
            tab.exhausted,
        )
        if worker is None:
            tab.loading = False
            tab.loaded_page_offsets.clear()
            self._load_tab(tab, append=False)
            return
        self._search_workers[tab.tab_id] = worker
        worker.add_result_data(metadata)
        worker.result.connect(self._async_query_result)
        worker.error.connect(self._async_query_error)
        worker.settled.connect(
            self._search_worker_settled,
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()
        self.search_state_changed.emit()

    def _load_tab(
        self, tab: SearchTabSession, append: bool = False,
        bypass_cache: bool = False,
    ) -> None:
        section = self._section_for_tab(tab)
        if not section:
            return
        is_current = (
            section.entry_key == self._current_section_key
            and section.current_tab_id == tab.tab_id
            and self._find_tab(section.entry_key, tab.tab_id) is tab
        )
        previous_worker = self._search_workers.get(tab.tab_id)
        if previous_worker is not None:
            self._pending_search_loads[tab.tab_id] = (
                tab, append, bypass_cache
            )
            previous_worker.cancel()
            return
        request_signature = json.dumps(
            {
                "section": section.entry_key,
                "filters": tab.extra_filters,
                "offset": tab.next_offset if append else tab.offset,
                "append": append,
                "sort": tab.sort_mode,
            },
            ensure_ascii=False,
            default=str,
            sort_keys=True,
        )
        if request_signature != tab.failure_signature:
            tab.failure_signature = request_signature
            tab.failure_count = 0
        if tab.failure_count >= 3:
            tab.loading = False
            tab.loading_append = False
            tab.error = "Retry limit reached for this search"
            if is_current:
                if self._active_request_id == tab.request_id:
                    self._active_request_id = ""
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
        tab.loading_append = append
        if is_current:
            self._active_request_id = request_id
        request_offset = tab.next_offset if append else tab.offset
        if not append:
            if is_current:
                self._card_path.clear()
                self._pending_card_focus_id = ""
            tab.clear_details()
            tab.sobjects = []
            tab.quick_filter_tasks.clear()
            tab.quick_filter_task_codes.clear()
            tab.quick_filter_task_loaded_at = 0.0
            tab.quick_filter_task_request_id = ""
            tab.loaded_page_offsets.clear()
            tab.clear_result_projection()
            if is_current:
                self.workspace_model.clear()
                self.versions_model.clear()
                self.workspace_state.clear_selection()
        if is_current:
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
            sort_mode=tab.sort_mode,
            bypass_cache=bypass_cache,
        )
        if worker is None:
            tab.loading = False
            tab.loading_append = False
            tab.error = "Server worker pool is not available"
            if is_current:
                if self._active_request_id == request_id:
                    self._active_request_id = ""
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
        is_current = (
            self._current_section_key == section_key
            and self._current_section() is not None
            and self._current_section().current_tab_id == tab_id
        )
        request_id = metadata[3] if len(metadata) > 3 else ""
        if (
            request_id
            and self._active_request_id == request_id
            and not is_current
        ):
            self._active_request_id = ""
            self._set_loading(False)
        pending = self._pending_search_loads.pop(tab_id, None)
        if pending:
            tab, append, bypass_cache = pending
            section = self._sessions.get(section_key)
            if (
                not section
                or self._find_tab(section_key, tab_id) is not tab
            ):
                tab.loading = False
                tab.loading_append = False
                return
            self._load_tab(tab, append, bypass_cache)

    def _section_for_tab(
        self,
        tab: SearchTabSession,
    ) -> SectionSession | None:
        return next((
            section for section in self._sessions.values()
            if any(candidate is tab for candidate in section.tabs)
        ), None)

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
        info = dict(info or {})
        tab.loading = False
        tab.loading_append = False
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
            info.get("total_sobjects_query_count")
            or info.get("savedTotal")
            or 0
        )
        tab.total = max(reported_total, len(tab.sobjects))
        cached_projection = bool(info.get("cachedProjection"))
        if cached_projection:
            tab.next_offset = max(
                0, int(info.get("nextOffset") or raw_count)
            )
            tab.exhausted = bool(info.get("savedExhausted", False))
            tab.loaded_page_offsets = [
                max(0, int(value))
                for value in (info.get("pageOffsets") or [])
            ]
        else:
            tab.next_offset = request_offset + raw_count
            tab.exhausted = (
                raw_count == 0
                or raw_count < tab.limit
                or (
                    reported_total > 0
                    and tab.next_offset >= reported_total
                )
            )
            if append:
                if request_offset not in tab.loaded_page_offsets:
                    tab.loaded_page_offsets.append(request_offset)
            else:
                tab.loaded_page_offsets = [request_offset]
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
        result_model = self._ensure_tab_workspace_model(tab)
        result_model.set_process_ignore(tab.process_ignore)
        self._configure_result_organization(tab, model=result_model)
        visible_sobjects = self._visible_sobjects(
            tab,
            self._sessions.get(section_key),
        )
        pending_restore, restored_selection = [], ""
        if append:
            result_model.append_sobjects(sobjects, stype)
        else:
            result_model.replace_sobjects(visible_sobjects, stype)
            if tab.view_mode == "tiles":
                result_model.show_card_level()
            elif tab.view_mode == "table":
                result_model.show_table_rows()
            else:
                pending_restore, restored_selection = (
                    result_model.apply_tree_state(tab.tree_state)
                )
            if restored_selection:
                tab.selected_node_id = restored_selection
                if not tab.selected_node_ids:
                    tab.selected_node_ids = [restored_selection]
                if not tab.selection_anchor_id:
                    tab.selection_anchor_id = restored_selection
        if append and tab.view_mode == "table":
            result_model.show_table_rows()
        tab.workspace_roots = list(result_model._roots)
        tab.workspace_projection = result_model.capture_projection()
        if not append:
            # A background completion may populate a hidden retained surface.
            # Its saved Flickable coordinates are applied when it is first
            # raised instead of being lost merely because another tab won the
            # race to become current.
            tab.viewport_restore_pending = bool(pending_restore) or not is_current
        if is_current:
            if not append:
                self._versions_request_id = ""
                self.versions_model.clear()
            tab.card_path = list(self._card_path)
            if not append:
                self.workspace_state.load_stype(stype)
                selected = result_model.node_for(tab.selected_node_id)
                if selected and selected.search_key:
                    details_search_key = selected.search_key
                    if tab.view_mode not in {"continious", "compact", "table"}:
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
                if not tab.viewport_restore_pending:
                    self._restore_result_viewport(tab)
            if not append and pending_restore:
                self._restore_tree_nodes(pending_restore)
        if request_id == self._active_request_id:
            self._active_request_id = ""
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
        self._save_search_cache()
        self.search_state_changed.emit()
        self.quick_filters_changed.emit()
        if (
                is_current
                and (
                    tab.group_mode == "task_status"
                    or bool(tab.quick_filters))):
            self.request_quick_filter_data()
        if (
            append
            and is_current
            and len(tab.sobjects) == previous_count
            and raw_count > 0
            and not tab.exhausted
        ):
            self.load_more()

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
        tab.loading_append = False
        tab.error = str(payload.get("exception") or error)
        tab.cancelled = False
        tab.failure_count += 1
        if not append:
            tab.loaded = False
            tab.sobjects = []
            tab.total = 0
            tab.next_offset = 0
            tab.exhausted = False
            tab.clear_result_projection()
        is_current = (
            section_key == self._current_section_key
            and self._current_section() is not None
            and self._current_section().current_tab_id == tab_id
        )
        if request_id == self._active_request_id:
            self._active_request_id = ""
            if is_current and not append:
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

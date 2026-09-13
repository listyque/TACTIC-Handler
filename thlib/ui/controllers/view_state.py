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
    Qt,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtGui import QGuiApplication, QImage

from ..menu_schema import MenuRegistry
from ..quick_filters import QuickFilterCatalog
from ..repository_sync import RepositorySyncController
from ..search_contract import (
    is_result_sort_mode,
    normalize_records,
    parse_column_sort_mode,
)
from ..tel_filters import (
    generated_quick_filter_records,
    is_generated_quick_filter,
)
from ..models import NavigationModel, ProjectModel
from ..workspace import (
    DockPanelModel,
    FloatingWindowModel,
    SectionTab,
    SectionTabModel,
    WorkspaceItemModel,
    WorkspaceState,
)
from .types import (
    STANDARD_QUICK_FILTER_TAB_KINDS,
    ActionRegistry,
    SearchTabSession,
    SectionSession,
)

_TAG_CATALOG_CACHE_TTL = 600.0
_TAG_CATALOG_PAGE_SIZE = 1000
_QUICK_FILTER_CATALOG_PAGE_SIZE = 1000

class ViewStateMixin:
    def clear_quick_filter_configurations(self) -> None:
        self._quick_filters.clear_configurations()
        self.quick_filters_changed.emit()

    def _quick_filter_context(self, stype=None, section=None) -> tuple[str, str]:
        section = section or self._current_section()
        stype = stype or self._active_stype()
        if not section or not stype:
            return "", ""
        try:
            project = stype.get_project()
            project_code = str(
                (project.get_code() if project else "")
                or self._current_project_code
            )
            stype_code = str(stype.get_code() or section.search_type)
        except (AttributeError, TypeError):
            return "", ""
        return project_code, stype_code

    def _active_quick_filter_facets(self):
        context = self._quick_filter_context()
        if not all(context):
            return None
        cache_key = self._quick_filter_catalog_cache_key(*context)
        if cache_key != self._quick_filter_runtime.context_key:
            return None
        return self._quick_filter_runtime.records

    def _set_server_state(self, state: str, message: str) -> None:
        if state != "online":
            self._administration_identity = None
        self._server_state = state
        self._server_message = message
        self.server_state_changed.emit()

    def quick_filter_editor_context(
        self,
        include_groups: bool = True,
        shared: bool = True,
    ) -> dict:
        section = self._current_section()
        tab = self._current_tab()
        if not section or not tab:
            return {}
        context = {
            "tab_id": tab.tab_id,
            "project_code": str(self._current_project_code or ""),
            "search_type": str(section.search_type or ""),
            "scope_key": section.entry_key,
            "title": str(section.title or tab.title or ""),
            "selections": {
                str(key): sorted(str(value) for value in values)
                for key, values in tab.quick_filters.items()
            },
            "layout": tab.quick_filter_layout,
            "loading": self._quick_filter_runtime.loading,
            "error": self._quick_filter_runtime.error,
        }
        if include_groups:
            context["groups"] = self._quick_filters.editor_groups(
                section.entry_key,
                tab.stype or self._active_stype(),
                tab.sobjects,
                tab.quick_filter_tasks,
                self._active_quick_filter_facets(),
                include_hidden=shared,
                local_groups=tab.quick_filter_layout or None,
            )
        return context

    def save_quick_filter_layout(self, tab_id: str, configuration: dict) -> None:
        """Commit a personal editor draft to its tab, never to widget_config."""
        tab = self._current_tab()
        section = self._current_section()
        if not tab or not section or tab.tab_id != tab_id:
            raise ValueError(self.tr(
                "The search tab changed. Reopen the filter editor."
            ))
        configuration = QuickFilterCatalog.validate_configuration(configuration)
        # Start with server-permitted entries. A local payload cannot resurrect
        # hidden groups or options, even after a shared policy change.
        permitted = self._quick_filters.editor_groups(
            section.entry_key, tab.stype or self._active_stype(),
            tab.sobjects, tab.quick_filter_tasks,
            self._active_quick_filter_facets(),
            include_hidden=False,
        )
        groups = self._quick_filters.configured_groups(
            permitted, configuration, include_hidden=True,
        )
        layout = []
        for group in groups:
            record = {"key": group["key"], "enabled": group["enabled"]}
            options = group["options"]
            enabled = [option["key"] for option in options
                       if option.get("enabled", True)]
            if len(enabled) != len(options):
                record["options"] = enabled
            layout.append(record)
        tab.quick_filter_layout = layout
        tab.quick_filters = self._quick_filters.sanitize_selection(
            section.entry_key, configuration["defaultSelections"],
        )
        tab.quick_filter_personalized = True
        self._apply_quick_filters(tab)

    def apply_quick_filter_configuration(
            self, scope_key: str, configuration: dict | None
    ) -> None:
        configuration = configuration or {}
        self._quick_filters.set_configuration(scope_key, configuration)
        active_tab = self._current_tab()
        active_changed = False
        cache_changed = False
        for session in self._sessions.values():
            if session.entry_key != scope_key:
                continue
            for session_tab in session.tabs:
                uses_standard = (
                    session_tab.tab_kind
                    in STANDARD_QUICK_FILTER_TAB_KINDS
                )
                if (
                        uses_standard
                        and not session_tab.quick_filter_personalized):
                    desired = self._quick_filters.default_selections(
                        scope_key
                    )
                else:
                    desired = self._quick_filters.sanitize_selection(
                        scope_key, session_tab.quick_filters
                    )
                selection_changed = desired != session_tab.quick_filters
                if selection_changed:
                    session_tab.quick_filters = desired
                try:
                    server_filter_changed = self._sync_generated_quick_filters(
                        session_tab, scope_key=scope_key
                    )
                except ValueError as error:
                    self._notify(str(error))
                    continue
                cache_changed = (
                    cache_changed or selection_changed
                    or server_filter_changed
                )
                if server_filter_changed:
                    self._reset_tab_after_filter_change(session_tab)
                    active_changed = active_changed or session_tab is active_tab
        if cache_changed:
            self._save_search_cache()
        self.quick_filters_changed.emit()
        if cache_changed:
            self.section_state_changed.emit()
        if active_changed and active_tab is not None:
            self._load_tab(active_tab, append=False)

    @Slot(str, str)
    def toggle_quick_filter(self, group_key: str, option_key: str) -> None:
        tab = self._current_tab()
        if not tab:
            return
        group_key = str(group_key or "")
        option_key = str(option_key or "")
        if not group_key:
            return
        tab.quick_filter_personalized = True
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

    @Slot()
    def clear_quick_filters(self) -> None:
        tab = self._current_tab()
        if not tab:
            return
        tab.quick_filter_personalized = True
        tab.quick_filters.clear()
        self._apply_quick_filters(tab)

    @Slot()
    def reset_quick_filters_to_standard(self) -> None:
        tab = self._current_tab()
        section = self._current_section()
        if (
                not tab or not section
                or tab.tab_kind not in STANDARD_QUICK_FILTER_TAB_KINDS):
            return
        tab.quick_filter_personalized = False
        tab.quick_filter_layout = []
        tab.quick_filters = self._quick_filters.default_selections(
            section.entry_key
        )
        self._apply_quick_filters(tab)

    @Slot("QVariantList")
    def set_quick_filter_assignees(self, logins) -> None:
        tab = self._current_tab()
        if not tab:
            return
        tab.quick_filter_personalized = True
        values = {
            str(value) for value in (logins or ()) if str(value or "")
        }
        current_key = self._quick_filters.CURRENT_LOGIN_FILTER
        if current_key in tab.quick_filters.get("assigned", set()):
            values.add(current_key)
        if values:
            tab.quick_filters["assigned"] = values
        else:
            tab.quick_filters.pop("assigned", None)
        self._apply_quick_filters(tab)

    @Slot()
    def toggle_my_tasks_filter(self) -> None:
        self.toggle_quick_filter(
            "assigned", self._quick_filters.CURRENT_LOGIN_FILTER
        )

    def _configure_result_organization(
        self,
        tab,
        rebuild: bool = True,
        model=None,
    ) -> None:
        statuses = self._quick_filters.task_group_statuses(
            tab.stype,
            tab.sobjects,
            tab.quick_filter_tasks,
            tab.task_group_process,
        ) if tab.group_mode == "task_status" and tab.stype else []
        target_model = model if model is not None else self.workspace_model
        target_model.set_organization(
            tab.sort_mode,
            tab.group_mode,
            tab.task_group_process,
            tab.quick_filter_tasks,
            tab.quick_filter_task_codes,
            statuses,
            rebuild=rebuild,
        )

    @Slot(str)
    def set_result_sort_mode(self, mode: str) -> None:
        tab = self._current_tab()
        if not tab or not is_result_sort_mode(mode):
            return
        column_sort = parse_column_sort_mode(mode)
        if column_sort and (
            not tab.stype
            or column_sort[0] not in (tab.stype.get_columns_info() or {})
        ):
            return
        if tab.sort_mode == mode:
            return
        tab.sort_mode = mode
        tab.offset = 0
        tab.next_offset = 0
        tab.exhausted = False
        self._configure_result_organization(tab)
        if tab.view_mode == "table":
            self.workspace_model.show_table_rows()
        self._save_search_cache()
        self.results_view_changed.emit()
        self._load_tab(tab)

    @Slot(str)
    def set_result_group_mode(self, command: str) -> None:
        tab = self._current_tab()
        if not tab:
            return
        command = str(command or "")
        process = ""
        mode = command
        if command.startswith("task_status:"):
            mode = "task_status"
            process = command[len("task_status:"):]
            known = {
                str(record.get("key") or "")
                for record in self._quick_filters.task_group_processes(
                    tab.stype, tab.sobjects, tab.quick_filter_tasks
                )
            }
            if not process or process not in known:
                return
        if mode not in {"none", "status", "pipeline", "task_status"}:
            return
        if tab.group_mode == mode and tab.task_group_process == process:
            return
        tab.group_mode = mode
        tab.task_group_process = process
        if mode != "none" and tab.view_mode == "tiles":
            tab.view_mode = "continious"
            self._card_path.clear()
            self._pending_card_focus_id = ""
        self._configure_result_organization(tab)
        if tab.view_mode == "table":
            self.workspace_model.show_table_rows()
        tab.workspace_roots = list(self.workspace_model._roots)
        self._save_search_cache()
        self.results_view_changed.emit()
        self.section_state_changed.emit()
        if mode == "task_status":
            self.request_quick_filter_data()

    def _sync_generated_quick_filters(
            self, tab, *, scope_key: str = ""
    ) -> bool:
        """Mirror every Quick Filter into executable Advanced Search cards."""
        source_records = tab.filter_records or self._filter_records_from_filters(
            tab.extra_filters
        )
        existing = [dict(record) for record in source_records]
        previous = [
            (
                str(record.get("column") or ""),
                str(record.get("relation") or ""),
                str(record.get("value") or ""),
                record.get("generatedFilterState") or {},
            )
            for record in existing
            if is_generated_quick_filter(record)
        ]
        records = [
            record for record in existing
            if not is_generated_quick_filter(record)
        ]
        section = self._current_section()
        is_current = tab is self._current_tab()
        effective_scope = str(
            scope_key
            or (section.entry_key if is_current and section else "")
        )
        effective_stype = tab.stype or (
            self._active_stype() if is_current else None
        )
        tab.quick_filters = self._quick_filters.sanitize_selection(
            effective_scope, tab.quick_filters,
        )
        tab.quick_filters = self._quick_filters.sanitize_selection(
            effective_scope, tab.quick_filters,
            configuration={"groups": tab.quick_filter_layout},
        )
        groups = self._quick_filters.groups(
            effective_scope,
            effective_stype,
            tab.sobjects,
            tab.quick_filters,
            tab.quick_filter_tasks,
            self._login_name,
            self._active_quick_filter_facets() if is_current else None,
            local_groups=tab.quick_filter_layout,
        )
        records.extend(generated_quick_filter_records(
            tab.quick_filters,
            groups,
            self._login_name,
        ))
        if not records:
            records.append(self._default_search_filter_record())
        records = normalize_records(records)
        current = [
            (
                str(record.get("column") or ""),
                str(record.get("relation") or ""),
                str(record.get("value") or ""),
                record.get("generatedFilterState") or {},
            )
            for record in records
            if is_generated_quick_filter(record)
        ]
        tab.filter_records = [dict(record) for record in records]
        tab.extra_filters = self._filters_from_records(records)
        if tab is self._current_tab():
            self.workspace_state.filter_model.replace(records)
        return previous != current

    @staticmethod
    def _reset_tab_after_filter_change(tab) -> None:
        tab.offset = 0
        tab.next_offset = 0
        tab.exhausted = False
        tab.duplicate_pages = 0
        tab.loaded = False
        tab.clear_result_projection()

    def _apply_quick_filters(self, tab) -> None:
        self._card_path.clear()
        self._pending_card_focus_id = ""
        try:
            server_filter_changed = self._sync_generated_quick_filters(tab)
        except ValueError as error:
            self._notify(str(error))
            return
        if server_filter_changed:
            self._capture_current_tree_state(persist_tree=True)
            self._reset_tab_after_filter_change(tab)
            self._save_search_cache()
            self.quick_filters_changed.emit()
            self.section_state_changed.emit()
            self._load_tab(tab, append=False)
            return
        # The explicit empty state and the server-owned state can produce the
        # same TEL. Persist their provenance even when no query changed.
        self._save_search_cache()
        self.quick_filters_changed.emit()

    @staticmethod
    def _quick_filter_catalog_cache_key(
        project_code: str, stype_code: str
    ) -> str:
        return json.dumps(
            [project_code, stype_code],
            ensure_ascii=False,
            separators=(",", ":"),
        )

    @staticmethod
    def _query_quick_filter_catalog(
        project_code: str,
        stype_code: str,
        facet_columns: list[dict],
        page_size: int = _QUICK_FILTER_CATALOG_PAGE_SIZE,
    ) -> list[dict]:
        import thlib.tactic_classes as tc

        columns = [
            str(record.get("column") or "")
            for record in facet_columns
            if record.get("column")
        ]
        if not columns:
            return []
        rows = []
        offset = 0
        page_size = max(1, int(page_size))
        while True:
            batch = list(tc.server_query(
                filters=[],
                stype=stype_code,
                columns=columns,
                project=project_code,
                limit=page_size,
                offset=offset,
                order_bys=[],
            ) or [])
            rows.extend(record for record in batch if isinstance(record, dict))
            if len(batch) < page_size:
                break
            offset += page_size
        return QuickFilterCatalog.discover_facets(
            None, rows, facet_columns
        )

    def _cached_quick_filter_catalog(
        self, cache_key: str
    ) -> tuple[list[dict], bool]:
        entry = self._quick_filter_runtime.cache.get(cache_key)
        if not isinstance(entry, dict):
            return [], False
        records = entry.get("records")
        if not isinstance(records, list):
            return [], False
        return [
            dict(record) for record in records if isinstance(record, dict)
        ], True

    @Slot(bool)
    def request_quick_filter_data(self, force: bool = False) -> None:
        """Load whole-Search-Type facets and related task values."""
        self._request_quick_filter_catalog(bool(force))
        self._request_quick_filter_tasks()

    def _request_quick_filter_catalog(self, force: bool = False) -> None:
        tab = self._current_tab()
        section = self._current_section()
        stype = (tab.stype if tab else None) or self._active_stype()
        if not tab or not section or not stype:
            return
        project_code, stype_code = self._quick_filter_context(stype, section)
        if not project_code or not stype_code:
            return
        cache_key = self._quick_filter_catalog_cache_key(
            project_code, stype_code
        )
        runtime = self._quick_filter_runtime
        runtime.context_key = cache_key
        facet_columns = self._quick_filters.facet_columns(stype)
        if not facet_columns:
            runtime.records = []
            runtime.loading = False
            runtime.error = "No categorical fields found."
            self.quick_filters_changed.emit()
            return

        cached_records, cache_exists = self._cached_quick_filter_catalog(
            cache_key
        )
        cache_exists = cache_exists and (
            runtime.cache[cache_key].get("facetColumns") == facet_columns
        )
        if cache_exists:
            runtime.records = cached_records
            runtime.error = (
                "" if cached_records else "No filter values found."
            )
        else:
            runtime.records = []
            runtime.error = ""
        if cache_exists and not force:
            runtime.loading = False
            self.quick_filters_changed.emit()
            return
        if cache_key in runtime.workers:
            runtime.loading = True
            self.quick_filters_changed.emit()
            return

        runtime.loading = True
        self.quick_filters_changed.emit()
        try:
            from thlib.environment import env_inst

            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()

            def query_facets():
                from thlib import server_cache

                cache_token = server_cache.token("reference", project_code)
                cached = None if force else server_cache.read_entry(
                    "reference",
                    "quick-facets:" + cache_key,
                    project_code,
                )
                if isinstance(cached, dict) and isinstance(
                    cached.get("records"), list
                ) and cached.get("facetColumns") == facet_columns:
                    return ({
                        "records": list(cached["records"]),
                        "facetColumns": facet_columns,
                        "cacheHit": True,
                    },)
                records = self._query_quick_filter_catalog(
                    project_code,
                    stype_code,
                    facet_columns,
                )
                if cache_token is not None:
                    server_cache.write_entry(
                        "reference",
                        "quick-facets:" + cache_key,
                        {"records": records, "facetColumns": facet_columns},
                        project_code,
                        expected_token=cache_token,
                    )
                return ({
                    "records": records, "facetColumns": facet_columns,
                    "cacheHit": False,
                },)

            worker = env_inst.server_pool.add_task(query_facets)
            if worker is None:
                raise RuntimeError("Server worker pool is not available")
            runtime.workers[cache_key] = worker
            worker.add_result_data((cache_key,))
            worker.result.connect(self._quick_filter_catalog_result)
            worker.error.connect(self._quick_filter_catalog_error)
            worker.start()
        except Exception as error:
            runtime.workers.pop(cache_key, None)
            runtime.loading = False
            runtime.error = str(error)
            self.quick_filters_changed.emit()
            self._notify(str(error))

    @Slot(object)
    def _quick_filter_catalog_result(self, result) -> None:
        payload, metadata = result
        cache_key = metadata[0]
        runtime = self._quick_filter_runtime
        runtime.workers.pop(cache_key, None)
        facet_records = [
            dict(record) for record in payload["records"]
            if isinstance(record, dict)
        ]
        runtime.cache[cache_key] = {
            "loadedAt": time.time(),
            "records": facet_records,
            "facetColumns": payload.get("facetColumns"),
        }
        if cache_key != runtime.context_key:
            return
        runtime.records = facet_records
        runtime.loading = False
        runtime.error = (
            "" if facet_records else "No filter values found."
        )
        self.quick_filters_changed.emit()

    @Slot(object)
    def _quick_filter_catalog_error(self, error) -> None:
        payload, worker = error
        metadata = worker.get_result_data() if worker else None
        cache_key = metadata[0] if metadata else ""
        runtime = self._quick_filter_runtime
        if cache_key:
            runtime.workers.pop(cache_key, None)
        self._report_error_payload(
            payload, "server/quick_filter_catalog", worker
        )
        if cache_key != runtime.context_key:
            return
        runtime.loading = False
        message = str(payload.get("exception") or error)
        runtime.error = (
            "Could not refresh quick filters: " + message
            if runtime.records else message
        )
        self.quick_filters_changed.emit()

    def _request_quick_filter_tasks(self) -> None:
        """Warm the per-tab related-task facets with one batched query."""
        tab = self._current_tab()
        section = self._current_section()
        if not tab or not section or not tab.sobjects:
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
            if tab.group_mode == "task_status":
                self._configure_result_organization(tab)
                if tab.view_mode == "table":
                    self.workspace_model.show_table_rows()
                tab.workspace_roots = list(self.workspace_model._roots)
                self.section_state_changed.emit()
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
        records = (
            [dict(record) for record in tab.filter_records]
            if tab.filter_records
            else self._filter_records_from_filters(tab.extra_filters)
        )
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

    @staticmethod
    def _tag_catalog_cache_key(
        project_code: str,
        stype_code: str,
        column: str,
    ) -> str:
        return json.dumps(
            [project_code, stype_code, column],
            ensure_ascii=False,
            separators=(",", ":"),
        )

    @staticmethod
    def _query_tag_catalog(
        project_code: str,
        stype_code: str,
        column: str,
        page_size: int = _TAG_CATALOG_PAGE_SIZE,
    ) -> list[dict]:
        import thlib.tactic_classes as tc

        page_size = max(1, int(page_size))
        counts: dict[str, int] = {}
        labels: dict[str, str] = {}
        offset = 0
        while True:
            batch = list(tc.server_query(
                filters=[],
                stype=stype_code,
                columns=[column],
                project=project_code,
                limit=page_size,
                offset=offset,
                order_bys=[],
            ) or [])
            for record in batch:
                if not isinstance(record, dict):
                    continue
                value = str(record.get(column) or "")
                for tag in re.split(r"[,;\s]+", value):
                    tag = tag.strip()
                    if not tag:
                        continue
                    key = tag.casefold()
                    counts[key] = counts.get(key, 0) + 1
                    labels.setdefault(key, tag)
            if len(batch) < page_size:
                break
            offset += page_size

        maximum = max(counts.values(), default=1)
        return [
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

    def _cached_tag_catalog(
        self,
        cache_key: str,
    ) -> tuple[list[dict], float, bool]:
        entry = self._tag_catalog_cache.get(cache_key)
        if not isinstance(entry, dict):
            return [], 0.0, False
        records = entry.get("records")
        if not isinstance(records, list):
            return [], 0.0, False
        try:
            loaded_at = float(entry.get("loadedAt") or 0.0)
        except (TypeError, ValueError):
            return [], 0.0, False
        return (
            [dict(record) for record in records if isinstance(record, dict)],
            loaded_at,
            True,
        )

    @Slot(bool)
    def request_tag_cloud(self, force: bool = False) -> None:
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
        project = stype.get_project()
        project_code = str(
            (project.get_code() if project else "")
            or self._current_project_code
        )
        stype_code = str(stype.get_code() or section.search_type)
        cache_key = self._tag_catalog_cache_key(
            project_code,
            stype_code,
            column,
        )
        self._tag_context_key = cache_key
        tab.tag_column = column

        cached_records, _loaded_at, cache_exists = (
            self._cached_tag_catalog(cache_key)
        )
        if cache_exists:
            self._tag_records = cached_records
            self._tag_error = (
                "" if cached_records else "No tags found."
            )
        else:
            self._tag_records = []
            self._tag_error = ""
        if cache_exists and not force:
            self._tag_loading = False
            self.tag_cloud_changed.emit()
            return
        if cache_key in self._tag_workers:
            self._tag_loading = True
            self.tag_cloud_changed.emit()
            return

        self._tag_loading = True
        self.tag_cloud_changed.emit()
        try:
            from thlib.environment import env_inst
            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()

            def query_tags():
                from thlib import server_cache

                cache_token = server_cache.token(
                    "reference", project_code
                )
                cached = None if force else server_cache.read_entry(
                    "reference", "tags:" + cache_key, project_code,
                )
                if isinstance(cached, dict) and isinstance(
                        cached.get("records"), list):
                    return ({
                        "records": list(cached["records"]),
                        "cacheHit": True,
                    },)
                records = self._query_tag_catalog(
                    project_code,
                    stype_code,
                    column,
                )
                if cache_token is not None:
                    server_cache.write_entry(
                        "reference", "tags:" + cache_key,
                        {"records": records}, project_code,
                        expected_token=cache_token,
                    )
                return ({"records": records, "cacheHit": False},)

            worker = env_inst.server_pool.add_task(query_tags)
            if worker is None:
                raise RuntimeError("Server worker pool is not available")
            self._tag_workers[cache_key] = worker
            worker.add_result_data((cache_key, column))
            worker.result.connect(self._tag_cloud_result)
            worker.error.connect(self._tag_cloud_error)
            worker.start()
        except Exception as error:
            self._tag_workers.pop(cache_key, None)
            self._tag_loading = False
            self._tag_error = str(error)
            self.tag_cloud_changed.emit()
            self._notify(str(error))

    @Slot(object)
    def _tag_cloud_result(self, result) -> None:
        payload, metadata = result
        cache_key, _column = metadata
        self._tag_workers.pop(cache_key, None)
        records = (
            dict(payload or {}).get("records")
            if isinstance(payload, dict) else payload
        )
        tag_records = [
            dict(record)
            for record in records or []
            if isinstance(record, dict)
        ]
        self._tag_catalog_cache[cache_key] = {
            "loadedAt": time.time(),
            "records": tag_records,
        }
        if cache_key != self._tag_context_key:
            return
        self._tag_records = tag_records
        self._tag_loading = False
        self._tag_error = "" if self._tag_records else "No tags found."
        self.tag_cloud_changed.emit()

    @Slot(object)
    def _tag_cloud_error(self, error) -> None:
        payload, worker = error
        metadata = worker.get_result_data() if worker else None
        self._report_error_payload(payload, "server/tag_cloud", worker)
        cache_key = metadata[0] if metadata else ""
        if cache_key:
            self._tag_workers.pop(cache_key, None)
        if cache_key != self._tag_context_key:
            return
        self._tag_loading = False
        message = str(payload.get("exception") or error)
        self._tag_error = (
            "Could not refresh tags: " + message
            if self._tag_records else message
        )
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

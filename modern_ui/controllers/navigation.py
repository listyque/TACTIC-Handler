"""Application controller: navigation."""

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
from ..search_contract import (
    create_search_tab,
    filters_from_records,
    normalize_records,
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
from .types import ActionRegistry, SearchTabSession, SectionSession

class NavigationMixin:
    def _save_preferences(self) -> None:
        from thlib.environment import env_server
        env_server.save_defaults()
        self._settings.sync()
        self._notify("Preferences saved")

    def _opened_section_keys(self, project_code: str) -> list[str]:
        try:
            from thlib.environment import cfg_controls
            config = cfg_controls.get_checkin_out_projects() or {}
            return list((config.get(project_code) or {}).get("stypes_list") or [])
        except (AttributeError, TypeError):
            return []

    def _saved_active_section_key(self, project_code: str) -> str:
        try:
            from thlib.environment import cfg_controls
            config = cfg_controls.get_checkin_out_projects() or {}
            return str(
                (config.get(project_code) or {}).get("active_stype") or ""
            )
        except (AttributeError, TypeError):
            return ""

    def _save_opened_sections(self) -> None:
        if not self._current_project_code:
            return
        try:
            from thlib.environment import cfg_controls
            config = cfg_controls.get_checkin_out_projects() or {}
            project_config = dict(config.get(self._current_project_code) or {})
            project_config["stypes_list"] = list(self._sessions)
            project_config["active_stype"] = self._current_section_key
            config[self._current_project_code] = project_config
            cfg_controls.set_checkin_out_projects(config)
        except (AttributeError, TypeError):
            pass

    def _capture_current_tree_state(self) -> None:
        tab = self._current_tab()
        if not tab or not tab.loaded:
            return
        tab.workspace_roots = list(self.workspace_model._roots)
        tab.tree_state = self.workspace_model.collect_tree_state(
            tab.selected_node_id
        )

    def _search_cache_key(self, project_code: str) -> str:
        return f"search/treeCacheV1/{project_code}"

    def _search_cache_enabled(self) -> bool:
        return self._settings.value(
            "workspace/cacheProcessTabs", True, type=bool
        )

    def _save_search_cache(self) -> None:
        self._search_cache_save_timer.start()

    def _write_search_cache(self) -> None:
        if not self._current_project_code or not self._search_cache_enabled():
            return
        self._capture_current_tree_state()
        sections = []
        for section in self._sessions.values():
            sections.append({
                "entry_key": section.entry_key,
                "current_tab_id": section.current_tab_id,
                "tabs": [
                    {
                        "tab_id": tab.tab_id,
                        "title": tab.title,
                        "tab_kind": tab.tab_kind,
                        "navigation_target": tab.navigation_target,
                        "search_text": tab.search_text,
                        "filter_records": tab.filter_records,
                        "offset": tab.offset,
                        "limit": tab.limit,
                        "tree_state": tab.tree_state,
                        "selected_node_id": tab.selected_node_id,
                        "selected_node_ids": tab.selected_node_ids,
                        "selection_anchor_id": tab.selection_anchor_id,
                        "view_mode": tab.view_mode,
                        "splitter_ratio": tab.splitter_ratio,
                        "process_ignore": tab.process_ignore,
                        "selected_tags": sorted(tab.selected_tags),
                        "tag_column": tab.tag_column,
                    }
                    for tab in section.tabs
                ],
            })
        self._settings.setValue(
            self._search_cache_key(self._current_project_code),
            json.dumps({"sections": sections}, ensure_ascii=False, default=str),
        )

    def _load_search_cache(self, project_code: str) -> dict[str, dict]:
        if not self._search_cache_enabled():
            return {}
        raw = self._settings.value(
            self._search_cache_key(project_code),
            "",
            type=str,
        )
        if not raw:
            return {}
        try:
            payload = json.loads(raw)
            return {
                str(section.get("entry_key") or ""): section
                for section in payload.get("sections") or []
                if section.get("entry_key")
            }
        except (TypeError, ValueError):
            return {}

    def _restore_section_tabs(
        self,
        section: SectionSession,
        cached: dict,
    ) -> None:
        def restored_splitter_ratio(value) -> float:
            try:
                return max(0.25, min(0.75, float(value or 0.58)))
            except (TypeError, ValueError):
                return 0.58

        tabs: list[SearchTabSession] = []
        for record in cached.get("tabs") or []:
            filter_records = normalize_records(
                value
                for value in (record.get("filter_records") or [])
                if isinstance(value, dict)
            )
            if not filter_records:
                filter_records = [self._default_search_filter_record()]
            tabs.append(SearchTabSession(
                tab_id=str(record.get("tab_id") or (
                    f"{section.entry_key}:search:{uuid.uuid4().hex[:8]}"
                )),
                title=str(record.get("title") or section.title),
                tab_kind=str(record.get("tab_kind") or "search"),
                navigation_target=str(
                    record.get("navigation_target") or ""
                ),
                search_text=str(record.get("search_text") or ""),
                extra_filters=filters_from_records(filter_records),
                filter_records=filter_records,
                offset=(
                    0
                    if self._loading_mode == "infinite"
                    else max(0, int(record.get("offset") or 0))
                ),
                limit=max(20, min(
                    5000, int(record.get("limit") or self._page_size)
                )),
                tree_state=record.get("tree_state") or {},
                selected_node_id=str(record.get("selected_node_id") or ""),
                selected_node_ids=[
                    str(value)
                    for value in (record.get("selected_node_ids") or [])
                    if value
                ] or (
                    [str(record.get("selected_node_id"))]
                    if record.get("selected_node_id") else []
                ),
                selection_anchor_id=str(
                    record.get("selection_anchor_id")
                    or record.get("selected_node_id")
                    or ""
                ),
                view_mode=(
                    str(record.get("view_mode") or self._default_view_mode)
                    if str(record.get("view_mode") or self._default_view_mode) in {
                        "continious", "compact", "splitted_vertical",
                        "splitted_horizontal", "tiles"
                    } else self._default_view_mode
                ),
                splitter_ratio=restored_splitter_ratio(
                    record.get("splitter_ratio")
                ),
                process_ignore=dict(record.get("process_ignore") or {}),
                selected_tags={
                    str(value)
                    for value in (record.get("selected_tags") or [])
                    if value
                },
                tag_column=str(record.get("tag_column") or ""),
            ))
        if tabs:
            section.tabs = tabs
            current_id = str(cached.get("current_tab_id") or "")
            section.current_tab_id = (
                current_id
                if any(tab.tab_id == current_id for tab in tabs)
                else tabs[0].tab_id
            )

    @staticmethod
    def _acronym(title: str) -> str:
        import thlib.global_functions as gf
        return str(gf.gen_acronym(title, length=2) or "?").upper()

    @Slot(str, result=str)
    def get_acronym(self, title: str) -> str:
        return self._acronym(title)

    def _create_section(self, key: str, title: str, accent: str = "") -> SectionSession:
        existing = self._sessions.get(key)
        if existing:
            return existing
        entry = self.navigation_model.entry(key)
        search_type = (
            entry.search_type if entry and entry.search_type
            else key.partition("@")[0]
        )
        filter_records = [
            dict(record)
            for record in (entry.filter_records if entry else ())
        ]
        tab = create_search_tab(
            key,
            title,
            tab_kind="base",
            limit=self._page_size,
            view_mode=(
                entry.view_mode if entry and entry.view_mode
                else self._default_view_mode
            ),
            records=filter_records,
            ensure_name_row=True,
        )
        section = SectionSession(
            entry_key=key,
            title=title,
            accent=accent or "#607d8b",
            search_type=search_type,
            search_view=str(entry.search_view or "") if entry else "",
            # Sidebar Search View conditions belong to the visible Advanced
            # Search tab, as in Ui_tacticSidebarWidget.apply_search_filter().
            # Keeping them out of base_filters prevents a hidden second copy.
            base_filters=(),
            tabs=[tab],
            current_tab_id=tab.tab_id,
        )
        self._sessions[key] = section
        self._sync_section_model()
        self._save_opened_sections()
        return section

    def _cancel_section_searches(self, section: SectionSession) -> None:
        """Detach searches owned by tabs that are about to be rebuilt."""
        for tab in section.tabs:
            self._pending_search_loads.pop(tab.tab_id, None)
            worker = self._search_workers.get(tab.tab_id)
            if worker is not None:
                worker.cancel()
            quick_worker = self._quick_filter_workers.pop(tab.tab_id, None)
            if quick_worker is not None:
                quick_worker.cancel()

    def _reset_sidebar_section(
        self,
        key: str,
        title: str,
        accent: str = "",
    ) -> SectionSession:
        """Rebuild a sidebar search group from its server definition.

        This is the original Handler behavior: clicking a sidebar link clears
        that Search Type's result tabs and recreates the base Search View plus
        its saved searches.  Runtime/user tabs are deliberately discarded.
        """
        entry = self.navigation_model.entry(key)
        existing = self._sessions.get(key)
        # Legacy apply_search_filter() only rebuilt tabs when the sidebar
        # element actually declared a Search View. Plain Search Type links
        # simply raised their existing workspace.
        if existing is not None and not (entry and entry.search_view):
            return existing
        if existing is not None:
            self._cancel_section_searches(existing)
            del self._sessions[key]
        section = self._create_section(key, title, accent)
        if entry and entry.search_view:
            self._request_sidebar_presets(section)
        return section

    def _request_sidebar_presets(self, section: SectionSession) -> None:
        """Load legacy ``link_search`` tabs without blocking the QML thread."""
        if not self._current_project_code or not section.search_type:
            return
        previous = self._sidebar_preset_workers.get(section.entry_key)
        if previous is not None:
            previous.cancel()
        request_id = uuid.uuid4().hex
        self._sidebar_preset_requests[section.entry_key] = request_id
        # Ui_sidebarItemWidget.get_item_code() was passed into
        # Ui_checkInOutWidget as ``customized_name``. Saved searches therefore
        # belong to the complete ``search_type@sidebar_name`` key, not merely
        # to the Search Type tail (for example ``assets``).
        tab_name = self._sidebar_preset_tab_name(section)
        project_code = self._current_project_code
        search_type = section.search_type

        def query():
            from ..search_presets import query_search_presets

            return (
                section.entry_key,
                request_id,
                query_search_presets(
                    project_code,
                    search_type,
                    tab_name,
                ),
            )

        try:
            from thlib.environment import env_inst

            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            worker = env_inst.server_pool.add_task(query)
            if worker is None:
                return
            self._sidebar_preset_workers[section.entry_key] = worker
            worker.result.connect(self._sidebar_presets_ready)
            worker.error.connect(self._sidebar_presets_failed)
            worker.finished.connect(
                lambda key=section.entry_key, target=worker:
                self._release_sidebar_preset_worker(key, target)
            )
            worker.start()
        except Exception:
            if self.debug_log:
                self.debug_log.log(
                    "ERROR",
                    traceback.format_exc(),
                    group="server/search-presets",
                    source="NavigationMixin",
                    caller=2,
                )

    @staticmethod
    def _sidebar_preset_tab_name(section: SectionSession) -> str:
        return section.entry_key

    def _release_sidebar_preset_worker(self, key: str, worker) -> None:
        if self._sidebar_preset_workers.get(key) is worker:
            self._sidebar_preset_workers.pop(key, None)

    @Slot(object)
    def _sidebar_presets_ready(self, payload) -> None:
        key, request_id, presets = payload
        if self._sidebar_preset_requests.get(key) != request_id:
            return
        section = self._sessions.get(key)
        if section is None:
            return
        for preset in presets or []:
            records = [
                dict(record) for record in (preset.get("records") or [])
            ]
            section.tabs.append(create_search_tab(
                key,
                str(preset.get("title") or section.title),
                tab_id=(
                    f"{key}:preset:"
                    f"{preset.get('code') or uuid.uuid4().hex[:8]}"
                ),
                tab_kind="preset",
                limit=self._page_size,
                view_mode=(
                    self.navigation_model.entry(key).view_mode
                    if self.navigation_model.entry(key)
                    and self.navigation_model.entry(key).view_mode
                    else self._default_view_mode
                ),
                records=records,
                ensure_name_row=True,
            ))
        # Ui_searchWidget.add_tab() selected every newly added result tab, so
        # after the loop the final server preset was the active tab.
        if presets:
            section.current_tab_id = section.tabs[-1].tab_id
        if self._current_section_key == key:
            self._sync_search_tabs()
            tab_id = section.current_tab_id
            QTimer.singleShot(
                0,
                lambda: self._show_tab_if_current(key, tab_id),
            )
        self.section_state_changed.emit()
        self._save_search_cache()

    @Slot(object)
    def _sidebar_presets_failed(self, error) -> None:
        payload, worker = error
        if self.debug_log:
            self.debug_log.log(
                "ERROR",
                str(payload.get("exception") or error),
                group="server/search-presets",
                source="NavigationMixin",
                caller=2,
            )

    def _sync_section_model(self) -> None:
        self.section_model.replace([
            SectionTab(
                entry_key=section.entry_key,
                title=section.title,
                acronym=self._acronym(section.title),
                accent=section.accent,
                current=section.entry_key == self._current_section_key,
            )
            for section in self._sessions.values()
        ])

    def _current_section(self) -> SectionSession | None:
        return self._sessions.get(self._current_section_key)

    def _current_tab(self) -> SearchTabSession | None:
        section = self._current_section()
        if not section:
            return None
        return next((tab for tab in section.tabs if tab.tab_id == section.current_tab_id), None)

    def _visible_sobjects(self, tab, section=None) -> list:
        section = section or self._current_section()
        if not section:
            return list(tab.sobjects)
        sobjects = self._quick_filters.filter(
            section.search_type,
            tab.sobjects,
            tab.quick_filters,
            tab.quick_filter_tasks,
            tab.quick_filter_task_codes,
        )
        return sobjects

    def _sync_search_tabs(self, clear_suggestions: bool = True) -> None:
        section = self._current_section()
        records = []
        if section:
            records = [
                {
                    "entryKey": tab.tab_id,
                    "title": tab.title,
                    "closable": len(section.tabs) > 1,
                    "current": tab.tab_id == section.current_tab_id,
                }
                for tab in section.tabs
            ]
        self.workspace_state.set_tabs(records)
        tab = self._current_tab()
        filter_records = (
            [dict(record) for record in tab.filter_records]
            if tab and tab.filter_records
            else self._filter_records_from_filters(
                tab.extra_filters if tab else []
            )
        )
        if tab and not filter_records:
            filter_records = [self._default_search_filter_record()]
            tab.filter_records = [dict(filter_records[0])]
        self.workspace_state.filter_model.replace(filter_records)
        self._suggestion_request_id = ""
        self._tag_request_id = ""
        self._tag_records = []
        self._tag_loading = False
        self._tag_error = ""
        if clear_suggestions:
            self.workspace_state.search_suggestion_model.clear()
        self.search_text_changed.emit()
        self.search_tab_history_changed.emit()
        self.search_state_changed.emit()
        self.quick_filters_changed.emit()
        self.tag_cloud_changed.emit()

    @Slot(str)
    def activate_section(self, key: str) -> None:
        section = self._sessions.get(key)
        if not section:
            return
        if key != self._current_section_key:
            self._capture_current_tree_state()
        self._current_section_key = key
        self._save_opened_sections()
        self._sync_section_model()
        self._sync_search_tabs()
        tab = self._current_tab()
        if tab:
            tab_id = tab.tab_id
            QTimer.singleShot(0, lambda: self._show_tab_if_current(key, tab_id))

    @Slot(str, str, str, str)
    def edit_sidebar_search_presets(
        self,
        search_type: str,
        entry_name: str,
        title: str,
        search_view: str,
    ) -> None:
        """Open shared Advanced Search in a sidebar item's Search context."""
        search_type = str(search_type or "").strip()
        entry_name = str(entry_name or "").strip()
        if not search_type:
            self._notify("Select a Search Type first")
            return
        key = f"{search_type}@{entry_name}" if entry_name else search_type
        section = self._sessions.get(key)
        if section is None:
            section = self._create_section(
                key,
                str(title or entry_name or search_type),
            )
        # Do not invent a second filter editor.  The temporary/real Search
        # section supplies the same columns, relation choices and exact
        # TACTIC Handler namespace used by Advanced Search.
        section.search_type = search_type
        # The picker edits the Search Type library, so it must expose every
        # Handler-owned preset that the adjacent dropdown can select.  The
        # sidebar item's selected Search View is staged separately by the
        # shared FilterEditorController after the modal opens.
        section.search_view = ""
        tab = section.tabs[0] if section.tabs else None
        if tab is not None:
            section.current_tab_id = tab.tab_id
        self.activate_section(key)
        stype = self._active_stype()
        if stype is not None:
            if tab is not None:
                tab.stype = stype
            self.workspace_state.load_stype(stype)
        QTimer.singleShot(
            0,
            lambda: self.window_model.show_window("sidebar_advanced_search"),
        )

    def _show_tab_if_current(self, section_key: str, tab_id: str) -> None:
        section = self._sessions.get(section_key)
        if (
            not section
            or self._current_section_key != section_key
            or section.current_tab_id != tab_id
        ):
            return
        tab = next((item for item in section.tabs if item.tab_id == tab_id), None)
        if tab:
            self._show_or_load_tab(tab)

    @Slot(str)
    def close_section(self, key: str) -> None:
        if key not in self._sessions:
            return
        keys = list(self._sessions)
        closing_index = keys.index(key)
        was_current = key == self._current_section_key
        del self._sessions[key]
        if was_current:
            remaining = list(self._sessions)
            self._current_section_key = (
                remaining[min(closing_index, len(remaining) - 1)] if remaining else ""
            )
        self._sync_section_model()
        self._save_opened_sections()
        if self._current_section_key:
            self.activate_section(self._current_section_key)
        else:
            self.workspace_state.set_tabs([])
            self.workspace_model.clear()
            self.workspace_state.clear_selection()
            self._result_count = 0
            self.result_count_changed.emit()
        self.section_state_changed.emit()

    @Slot(int, int)
    def reorder_section(self, source_row: int, target_row: int) -> None:
        items = list(self._sessions.items())
        if (
            not 0 <= source_row < len(items)
            or not 0 <= target_row < len(items)
            or source_row == target_row
        ):
            return
        moved = items.pop(source_row)
        items.insert(target_row, moved)
        self._sessions = dict(items)
        self._sync_section_model()
        self._save_opened_sections()

    @Slot(str, str)
    def _activate_workspace_tab(self, key: str, title: str) -> None:
        section = self._current_section()
        if not section:
            return
        tab = next(
            (
                candidate for candidate in section.tabs
                if candidate.tab_id == key
            ),
            None,
        )
        if not tab or tab.tab_id == section.current_tab_id:
            return
        previous_tab = self._current_tab()
        if previous_tab and previous_tab.loaded:
            self._capture_current_tree_state()
        self._selection_load_timer.stop()
        self._pending_selection_load = None
        if self._detail_worker is not None:
            self._detail_worker.cancel()
        if self._versions_worker is not None:
            self._versions_worker.cancel()
        self._pending_versions_node_id = ""
        self._detail_request_id = ""
        self._versions_request_id = ""
        section.current_tab_id = tab.tab_id
        self._sync_search_tabs()
        QTimer.singleShot(
            0,
            lambda: self._show_tab_if_current(section.entry_key, tab.tab_id),
        )

    def _show_or_load_tab(self, tab: SearchTabSession) -> None:
        self._card_path.clear()
        self._pending_card_focus_id = ""
        self.workspace_model.set_process_ignore(tab.process_ignore)
        if tab.loaded:
            self._versions_request_id = ""
            self.versions_model.clear()
            visible_sobjects = self._visible_sobjects(tab)
            if tab.workspace_roots:
                self.workspace_model.replace_nodes(tab.workspace_roots, tab.stype)
            else:
                self.workspace_model.replace_sobjects(visible_sobjects, tab.stype)
                tab.workspace_roots = list(self.workspace_model._roots)
            if tab.view_mode == "tiles":
                self.workspace_model.show_card_level()
            self.workspace_state.load_stype(tab.stype)
            selected = self.workspace_model.node_for(tab.selected_node_id)
            cached_node = selected or self.workspace_model.node_for(
                tab.details_node_id
            )
            if selected and selected.search_key and tab.pending_snapshot_code:
                snapshot_code = tab.pending_snapshot_code
                snapshot_process = tab.pending_snapshot_process or None
                tab.pending_snapshot_code = ""
                tab.pending_snapshot_process = ""
                self._load_sobject_details(
                    selected.search_key,
                    process=snapshot_process,
                    snapshot_code=snapshot_code,
                )
                details_restored = True
            elif selected and selected.search_key and tab.pending_detail_process:
                detail_process = tab.pending_detail_process
                tab.pending_detail_process = ""
                self._load_sobject_details(
                    selected.search_key,
                    process=detail_process,
                )
                details_restored = True
            else:
                details_restored = (
                    bool(cached_node)
                    and self._restore_tab_details(tab, cached_node)
                )
            if not details_restored and selected and selected.search_key:
                self._pending_selection_load = (
                    selected.node_id,
                    selected.search_key,
                    selected.node_type,
                )
                self._flush_selected_loads()
            elif (
                not details_restored
                and visible_sobjects
                and not tab.selected_node_id
            ):
                self._load_sobject_details(
                    visible_sobjects[0].get_search_key()
                )
            elif not details_restored:
                self.workspace_state.clear_selection()
            self._set_result_state(tab)
            self.section_state_changed.emit()
            return
        self._load_tab(tab, append=False)

    def _append_activity(self, message: str) -> None:
        if not message:
            return
        stamp = QDateTime.currentDateTime().toString("HH:mm:ss")
        self._activity_log.append(f"{stamp}  {message}")
        self._activity_log = self._activity_log[-100:]
        self.activity_log_changed.emit()

    @Slot(str)
    def log_runtime_message(self, message: str) -> None:
        """Publish Qt/QML runtime diagnostics in the in-app activity log."""
        message = str(message or "").strip()
        self._append_activity(message)
        if self.debug_log:
            parts = [
                part.strip()
                for part in re.split(r"\s*(?:·|В·)\s*", message, maxsplit=2)
            ]
            level = parts[0] if parts and parts[0] in {
                "WARNING", "MISSING", "ERROR", "CRITICAL",
            } else "LOG"
            source = parts[1] if len(parts) > 2 else "Qt"
            body = parts[2] if len(parts) > 2 else message
            self.debug_log.log_qt_message(level, source, body)

    @staticmethod
    def _payload_size_kb(payload) -> float:
        seen: set[int] = set()

        def size_of(value, depth: int = 0) -> int:
            if value is None or depth > 8:
                return 0
            identity = id(value)
            if identity in seen:
                return 0
            seen.add(identity)
            size = sys.getsizeof(value, 0)
            if isinstance(value, dict):
                return size + sum(
                    size_of(key, depth + 1) + size_of(item, depth + 1)
                    for key, item in value.items()
                )
            if isinstance(value, (list, tuple, set, frozenset)):
                return size + sum(size_of(item, depth + 1) for item in value)
            data = getattr(value, "__dict__", None)
            if data:
                size += size_of(data, depth + 1)
            slots = getattr(type(value), "__slots__", ())
            if isinstance(slots, str):
                slots = (slots,)
            for slot in slots:
                if slot in {"__dict__", "__weakref__"}:
                    continue
                try:
                    size += size_of(getattr(value, slot), depth + 1)
                except (AttributeError, RuntimeError, TypeError):
                    continue
            return size

        try:
            return size_of(payload) / 1024.0
        except (AttributeError, RuntimeError, TypeError, ValueError):
            return 0.0

    def _transaction_metrics(self, started_at: float, payload=None) -> str:
        duration = max(0.0, time.perf_counter() - started_at)
        size_kb = self._payload_size_kb(payload)
        return f"{duration:.2f} s · {size_kb:.1f} KB"

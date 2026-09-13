"""Application controller: navigation."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
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
    create_search_tab,
    filters_from_records,
    is_result_sort_mode,
    normalize_records,
)
from ..tel_filters import quick_selection_from_records
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
        self._write_settings()
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
        self._section_state_save_timer.start()

    def _write_opened_sections(self) -> None:
        if not self._current_project_code:
            return
        try:
            from thlib.environment import cfg_controls
            config = cfg_controls.get_checkin_out_projects() or {}
            project_config = dict(config.get(self._current_project_code) or {})
            project_config["stypes_list"] = list(self._sessions)
            project_config["active_stype"] = self._current_section_key
            config[self._current_project_code] = project_config
            cfg_controls.set_checkin_out_projects(config, persist=False)
            self._config_write_queue.submit(
                config,
                filename="checkin_out_projects",
                unique_id="ui_conf",
                long_abs_path=True,
            )
        except (AttributeError, TypeError):
            pass

    def _capture_current_tree_state(self, persist_tree: bool = False) -> None:
        tab = self._current_tab()
        if not tab or not tab.loaded:
            return
        # The view owns its live Flickable coordinates.  Ask it to publish
        # them synchronously. The result model itself is retained per tab, so
        # copying every root, row, and node here would make switching cost
        # grow with the number of visible and loaded objects.
        self.result_viewport_capture_requested.emit()
        tab.card_path = list(self._card_path)
        if tab.details_payload:
            tab.details_projection = (
                self.workspace_state.capture_selection_projection()
            )
            if tab.view_mode not in {"continious", "compact", "table"}:
                tab.details_versions_projection = (
                    self.versions_model.capture_projection()
                )
        tab.tree_state_dirty = True
        if persist_tree:
            tab.tree_state = self.workspace_model.collect_tree_state(
                tab.selected_node_id
            )
            tab.tree_state_dirty = False

    @Slot(float, float)
    def capture_current_result_viewport(
        self,
        list_content_y: float,
        tile_content_y: float,
    ) -> None:
        tab = self._current_tab()
        if not tab or not tab.loaded or tab.viewport_restore_pending:
            return
        tab.list_content_y = float(list_content_y)
        tab.tile_content_y = float(tile_content_y)
        tab.list_content_y_valid = True
        tab.tile_content_y_valid = True

    def _restore_result_viewport(self, tab: SearchTabSession) -> None:
        self.result_viewport_restore_requested.emit(
            tab.list_content_y,
            tab.tile_content_y,
            tab.list_content_y_valid,
            tab.tile_content_y_valid,
        )

    @Slot()
    def restore_current_result_viewport(self) -> None:
        """Replay saved coordinates when the view mounts after its cached data."""
        tab = self._current_tab()
        if tab and tab.loaded and not tab.viewport_restore_pending:
            self._restore_result_viewport(tab)

    def _search_cache_enabled(self) -> bool:
        return bool(self._settings.get("workspace/cacheProcessTabs", True))

    def _save_search_cache(self) -> None:
        self._search_cache_save_timer.start()

    def _write_search_cache(self) -> None:
        if not self._current_project_code or not self._search_cache_enabled():
            return
        self._capture_current_tree_state()
        self._capture_current_workspace_layout()
        for section in self._sessions.values():
            for tab in section.tabs:
                if tab.tree_state_dirty and tab.workspace_model is not None:
                    tab.tree_state = tab.workspace_model.collect_tree_state(
                        tab.selected_node_id
                    )
                    tab.tree_state_dirty = False
        sections = []
        for section in self._sessions.values():
            sections.append({
                "entry_key": section.entry_key,
                "current_tab_id": section.current_tab_id,
                "sidebar_presets_initialized": (
                    section.sidebar_presets_initialized
                ),
                "tabs": [
                    {
                        "tab_id": tab.tab_id,
                        "title": tab.title,
                        "tab_kind": tab.tab_kind,
                        "navigation_target": tab.navigation_target,
                        "search_text": tab.search_text,
                        "filter_records": tab.filter_records,
                        "offset": tab.offset,
                        "next_offset": tab.next_offset,
                        "limit": tab.limit,
                        "total": tab.total,
                        "exhausted": tab.exhausted,
                        "loaded_page_offsets": tab.loaded_page_offsets,
                        "workspace_layout": deepcopy(tab.workspace_layout),
                        "tree_state": tab.tree_state,
                        "selected_node_id": tab.selected_node_id,
                        "selected_node_ids": tab.selected_node_ids,
                        "selection_anchor_id": tab.selection_anchor_id,
                        "list_content_y": tab.list_content_y,
                        "tile_content_y": tab.tile_content_y,
                        "list_content_y_valid": tab.list_content_y_valid,
                        "tile_content_y_valid": tab.tile_content_y_valid,
                        "view_mode": tab.view_mode,
                        "sort_mode": tab.sort_mode,
                        "group_mode": tab.group_mode,
                        "task_group_process": tab.task_group_process,
                        "splitter_ratio": tab.splitter_ratio,
                        "process_ignore": tab.process_ignore,
                        "selected_tags": sorted(tab.selected_tags),
                        "tag_column": tab.tag_column,
                        "quick_filter_personalized": (
                            tab.quick_filter_personalized
                        ),
                        "quick_filter_layout": tab.quick_filter_layout,
                    }
                    for tab in section.tabs
                ],
            })
        self._search_cache[self._current_project_code] = {
            "sections": sections,
        }
        self._write_search_cache_config()

    def _load_search_cache(self, project_code: str) -> dict[str, dict]:
        if not self._search_cache_enabled():
            return {}
        payload = self._search_cache.get(project_code)
        if not isinstance(payload, dict):
            return {}
        try:
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
        section.sidebar_presets_initialized = bool(
            cached.get("sidebar_presets_initialized", False)
        )

        def restored_splitter_ratio(value) -> float:
            try:
                return max(0.25, min(0.75, float(value or 0.58)))
            except (TypeError, ValueError):
                return 0.58

        def restored_page_offsets(values) -> list[int]:
            if not isinstance(values, (list, tuple)):
                return []
            offsets = set()
            for value in values[:256]:
                try:
                    offsets.add(max(0, int(value)))
                except (TypeError, ValueError):
                    continue
            return sorted(offsets)

        tabs: list[SearchTabSession] = []
        for record in cached.get("tabs") or []:
            if "quick_filter_personalized" not in record:
                continue
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
                quick_filters=quick_selection_from_records(filter_records),
                quick_filter_personalized=bool(
                    record["quick_filter_personalized"]
                ),
                quick_filter_layout=[
                    dict(group) for group in record.get("quick_filter_layout", [])
                    if isinstance(group, dict) and group.get("key")
                ],
                offset=(
                    0
                    if self._loading_mode == "infinite"
                    else max(0, int(record.get("offset") or 0))
                ),
                limit=max(20, min(
                    5000, int(record.get("limit") or self._page_size)
                )),
                next_offset=max(0, int(record.get("next_offset") or 0)),
                total=max(0, int(record.get("total") or 0)),
                exhausted=bool(record.get("exhausted", False)),
                loaded_page_offsets=restored_page_offsets(
                    record.get("loaded_page_offsets")
                ),
                workspace_layout=(
                    deepcopy(record.get("workspace_layout"))
                    if isinstance(record.get("workspace_layout"), dict)
                    else {}
                ),
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
                list_content_y=float(record.get("list_content_y") or 0.0),
                tile_content_y=float(record.get("tile_content_y") or 0.0),
                list_content_y_valid=bool(
                    record.get("list_content_y_valid", False)
                ),
                tile_content_y_valid=bool(
                    record.get("tile_content_y_valid", False)
                ),
                view_mode=(
                    str(record.get("view_mode") or self._default_view_mode)
                    if str(record.get("view_mode") or self._default_view_mode) in {
                        "continious", "compact", "splitted_vertical",
                        "splitted_horizontal", "tiles", "table"
                    } else self._default_view_mode
                ),
                sort_mode=(
                    str(record.get("sort_mode") or "name_asc")
                    if is_result_sort_mode(
                        str(record.get("sort_mode") or "name_asc")
                    ) else "name_asc"
                ),
                group_mode=(
                    str(record.get("group_mode") or "none")
                    if str(record.get("group_mode") or "none") in {
                        "none", "status", "pipeline", "task_status"
                    } else "none"
                ),
                task_group_process=str(record.get("task_group_process") or ""),
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
        entry = self.navigation_model.entry(key)
        if entry and (
            entry.entry_type != "link" or not entry.available or not entry.search_type
        ):
            raise ValueError(f"Sidebar item has no available Search Type: {key}")
        existing = self._sessions.get(key)
        if existing:
            return existing
        search_type = (
            entry.search_type if entry
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
            layout_preset=str(entry.layout_preset or "") if entry else "",
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

    def _open_sidebar_section(
        self,
        key: str,
        title: str,
        accent: str = "",
    ) -> SectionSession:
        """Return the retained sidebar workspace, initializing it once."""
        entry = self.navigation_model.entry(key)
        existing = self._sessions.get(key)
        if existing is not None:
            assigned = str(entry.layout_preset or "") if entry else ""
            if assigned != existing.layout_preset:
                existing.layout_preset = assigned
            self._ensure_sidebar_presets_initialized(existing)
            return existing
        section = self._create_section(key, title, accent)
        self._ensure_sidebar_presets_initialized(section)
        return section

    def _ensure_sidebar_presets_initialized(
        self,
        section: SectionSession,
    ) -> None:
        """Start the sidebar preset catalog only on this section's first use."""
        if section.sidebar_presets_initialized:
            return
        if not section.search_view:
            section.sidebar_presets_initialized = True
            return
        pending = self._sidebar_preset_requests.get(section.entry_key)
        if (
            isinstance(pending, tuple)
            and len(pending) == 4
            and pending[0] == str(self._current_project_code or "")
            and pending[3] is section
        ):
            return
        self._request_sidebar_presets(section)

    def _request_sidebar_presets(self, section: SectionSession) -> None:
        """Load TACTIC ``link_search`` tabs without blocking QML."""
        if not self._current_project_code or not section.search_type:
            return
        self._cancel_sidebar_preset_request(section.entry_key)
        request_id = uuid.uuid4().hex
        # Ui_sidebarItemWidget.get_item_code() was passed into
        # Ui_checkInOutWidget as ``customized_name``. Saved searches therefore
        # belong to the complete ``search_type@sidebar_name`` key, not merely
        # to the Search Type tail (for example ``assets``).
        tab_name = self._sidebar_preset_tab_name(section)
        project_code = self._current_project_code
        search_type = section.search_type
        session_token = uuid.uuid4().hex
        request_context = (
            project_code,
            request_id,
            session_token,
            section,
        )
        self._sidebar_preset_requests[section.entry_key] = request_context

        def query():
            from ..search_presets import query_search_presets

            return (query_search_presets(
                project_code,
                search_type,
                tab_name,
            ),)

        try:
            from thlib.environment import env_inst

            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            worker = env_inst.server_pool.add_task(query)
            if worker is None:
                if self._sidebar_preset_requests.get(
                    section.entry_key
                ) == request_context:
                    self._sidebar_preset_requests.pop(
                        section.entry_key, None
                    )
                return
            self._sidebar_preset_workers[section.entry_key] = worker
            worker.add_result_data((
                project_code,
                section.entry_key,
                request_id,
                session_token,
            ))
            worker.result.connect(self._sidebar_presets_ready)
            worker.error.connect(self._sidebar_presets_failed)
            worker.finished.connect(
                lambda key=section.entry_key, target=worker:
                self._release_sidebar_preset_worker(key, target)
            )
            worker.start()
        except Exception:
            if self._sidebar_preset_requests.get(
                section.entry_key
            ) == request_context:
                self._cancel_sidebar_preset_request(section.entry_key)
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

    def _cancel_sidebar_preset_request(self, key: str) -> None:
        """Detach one section's request before its session can be replaced."""
        self._sidebar_preset_requests.pop(key, None)
        worker = self._sidebar_preset_workers.pop(key, None)
        if worker is None:
            return
        try:
            worker.cancel()
        except (AttributeError, RuntimeError):
            pass

    def _invalidate_sidebar_preset_requests(self) -> None:
        """Cancel preset work before the owning project/session is replaced."""
        keys = set(self._sidebar_preset_workers)
        keys.update(self._sidebar_preset_requests)
        for key in keys:
            self._cancel_sidebar_preset_request(key)

    @Slot(object)
    def _sidebar_presets_ready(self, payload) -> None:
        presets, metadata = payload
        project_code, key, request_id, session_token = metadata
        if project_code != self._current_project_code:
            return
        section = self._sessions.get(key)
        request_context = self._sidebar_preset_requests.get(key)
        if (
            section is None
            or not isinstance(request_context, tuple)
            or len(request_context) != 4
            or request_context[:3] != (
                project_code,
                request_id,
                session_token,
            )
            or request_context[3] is not section
        ):
            return
        try:
            new_tabs = []
            existing_ids = {tab.tab_id for tab in section.tabs}
            for preset in presets or []:
                if not isinstance(preset, dict):
                    raise TypeError("Sidebar preset records must be mappings")
                records = [
                    dict(record) for record in (preset.get("records") or [])
                ]
                tab_id = (
                    f"{key}:preset:"
                    f"{preset.get('code') or uuid.uuid4().hex[:8]}"
                )
                if tab_id in existing_ids:
                    continue
                existing_ids.add(tab_id)
                new_tabs.append(create_search_tab(
                    key,
                    str(preset.get("title") or section.title),
                    tab_id=tab_id,
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
        except (AttributeError, TypeError, ValueError) as error:
            self._sidebar_preset_requests.pop(key, None)
            section.sidebar_presets_initialized = False
            if self.debug_log:
                self.debug_log.log(
                    "ERROR",
                    str(error),
                    group="server/search-presets",
                    source="NavigationMixin",
                    stacktrace=traceback.format_exc(),
                    caller=2,
                )
            return
        section.tabs.extend(new_tabs)
        section.sidebar_presets_initialized = True
        self._sidebar_preset_requests.pop(key, None)
        # Ui_searchWidget.add_tab() selected every newly added result tab, so
        # after the loop the final server preset was the active tab.
        selected_new_tab = new_tabs[-1] if new_tabs else None
        if new_tabs:
            if self._current_section_key == key:
                self._activate_workspace_tab(
                    selected_new_tab.tab_id, selected_new_tab.title
                )
            else:
                section.current_tab_id = selected_new_tab.tab_id
        if self._current_section_key == key:
            if selected_new_tab is None:
                self._sync_search_tabs()
                tab_id = section.current_tab_id
                self._show_tab_if_current(key, tab_id)
        self.section_state_changed.emit()
        self._save_search_cache()

    @Slot(object)
    def _sidebar_presets_failed(self, error) -> None:
        payload, worker = error
        metadata = worker.get_result_data() if worker is not None else None
        if metadata and len(metadata) == 4:
            project_code, key, request_id, session_token = metadata
            request_context = self._sidebar_preset_requests.get(key)
            if (
                isinstance(request_context, tuple)
                and len(request_context) == 4
                and request_context[:3] == (
                    project_code,
                    request_id,
                    session_token,
                )
            ):
                self._sidebar_preset_requests.pop(key, None)
                section = self._sessions.get(key)
                if (
                    project_code == self._current_project_code
                    and section is not None
                    and request_context[3] is section
                ):
                    section.sidebar_presets_initialized = False
            self._release_sidebar_preset_worker(key, worker)
        if self.debug_log:
            self.debug_log.log(
                "ERROR",
                str(payload.get("exception") or error),
                group="server/search-presets",
                source="NavigationMixin",
                caller=2,
            )

    def _section_glyph(self, entry_key: str) -> str:
        entry = self.navigation_model.entry(entry_key)
        return str(entry.glyph or "sidebar-link") if entry else "sidebar-link"

    def _sync_section_model(self) -> None:
        self.section_model.replace([
            SectionTab(
                entry_key=section.entry_key,
                title=section.title,
                accent=section.accent,
                current=section.entry_key == self._current_section_key,
                glyph=self._section_glyph(section.entry_key),
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

    def script_shelf_context(self) -> dict:
        section = self._current_section()
        if section is None:
            return {}
        entry = self.navigation_model.entry(section.entry_key)
        return {
            "entryKey": section.entry_key,
            "title": section.title,
            "shelfPreset": str(entry.script_shelf or "") if entry else "",
        }

    def apply_script_shelf_assignment(
        self,
        project_code: str,
        entry_key: str,
        shelf_view: str,
        saved_record: dict,
    ) -> None:
        if str(project_code or "") != self._current_project_code:
            return
        try:
            from thlib.environment import env_inst

            project = (env_inst.projects or {}).get(project_code)
            views = project.get_config_views() if project is not None else None
            records = list(views.config_dict or []) if views is not None else []
            code = str(saved_record.get("code") or "")
            view = str(saved_record.get("view") or "")
            if views is not None:
                views.config_dict = [
                    record for record in records
                    if not (
                        (code and str(record.get("code") or "") == code)
                        or (
                            view
                            and str(record.get("view") or "") == view
                            and str(record.get("search_type") or "")
                            == "SideBarWdg"
                        )
                    )
                ] + [dict(saved_record)]
        except (AttributeError, TypeError):
            pass
        if self.navigation_model.set_script_shelf(entry_key, shelf_view):
            self.search_state_changed.emit()

    def remove_script_shelf_assignments(
        self,
        project_code: str,
        shelf_view: str,
        saved_records: list[dict],
    ) -> None:
        if str(project_code or "") != self._current_project_code:
            return
        try:
            from thlib.environment import env_inst

            project = (env_inst.projects or {}).get(project_code)
            views = project.get_config_views() if project is not None else None
            if views is not None:
                saved_by_code = {
                    str(record.get("code") or ""): dict(record)
                    for record in saved_records
                    if record.get("code")
                }
                views.config_dict = [
                    saved_by_code.pop(str(record.get("code") or ""), record)
                    for record in list(views.config_dict or [])
                ] + list(saved_by_code.values())
        except (AttributeError, TypeError):
            pass
        if self.navigation_model.clear_script_shelf(shelf_view):
            self.search_state_changed.emit()

    def _capture_current_workspace_layout(self) -> None:
        """Snapshot the live dock tree into the selected Search tab."""
        tab = self._current_tab()
        dock_model = getattr(self, "dock_model", None)
        if tab is None or dock_model is None:
            return
        tab.workspace_layout = deepcopy(dock_model.capture_layout())

    def _apply_tab_workspace_layout(
        self,
        section: SectionSession,
        tab: SearchTabSession,
    ) -> bool:
        """Synchronously publish one Search tab's retained dock arrangement."""
        dock_model = getattr(self, "dock_model", None)
        if dock_model is None:
            return False
        if tab.workspace_layout:
            if dock_model.apply_layout(deepcopy(tab.workspace_layout)):
                return True
            tab.workspace_layout = {}

        applied = False
        layout_presets = getattr(self, "_workspace_layout_presets", None)
        if section.layout_preset and layout_presets is not None:
            applied = bool(
                layout_presets.apply_assigned(section.layout_preset)
            )
        # An unassigned Search tab starts from the currently presented
        # workspace. From this point on the document belongs to this tab only.
        tab.workspace_layout = deepcopy(dock_model.capture_layout())
        return applied

    def _ensure_tab_workspace_model(
        self,
        tab: SearchTabSession,
    ) -> WorkspaceItemModel:
        model = tab.workspace_model
        if isinstance(model, WorkspaceItemModel):
            return model
        model = WorkspaceItemModel()
        model.setParent(self)
        model.repository_sync = getattr(self, "repository_sync", None)
        model.set_knowledge_index(
            getattr(self, "_knowledge_link_index", {})
        )
        tab.workspace_model = model
        return model

    @staticmethod
    def _dispose_tab_workspace_model(tab: SearchTabSession) -> None:
        """Release a retained result model when its tab cannot be restored."""
        model = tab.workspace_model
        tab.workspace_model = None
        if model is not None:
            model.deleteLater()

    def _dispose_section_workspace_models(
        self,
        section: SectionSession,
    ) -> None:
        for tab in (*section.tabs, *section.closed_tabs):
            self._dispose_tab_workspace_model(tab)

    def _dispose_all_tab_workspace_models(self) -> None:
        for section in self._sessions.values():
            self._dispose_section_workspace_models(section)

    def _visible_sobjects(self, tab, section=None) -> list:
        return list(tab.sobjects)

    def _sync_search_tabs(self, clear_suggestions: bool = True) -> None:
        phase_started_at = time.perf_counter()
        section = self._current_section()
        records = []
        if section:
            records = [
                {
                    "entryKey": tab.tab_id,
                    "title": tab.title,
                    "closable": len(section.tabs) > 1,
                    "current": tab.tab_id == section.current_tab_id,
                    "resultModel": self._ensure_tab_workspace_model(tab),
                    "viewMode": tab.view_mode,
                    "splitterRatio": tab.splitter_ratio,
                }
                for tab in section.tabs
            ]
        self.workspace_state.set_tabs(records)
        self._search_tab_switch_monitor.record_phase(
            "tabRowsMs", (time.perf_counter() - phase_started_at) * 1000,
        )
        phase_started_at = time.perf_counter()
        self.workspace_state.set_result_surfaces([
            {
                "surfaceKey": (
                    f"{candidate_section.entry_key}::{candidate_tab.tab_id}"
                ),
                "current": (
                    candidate_section.entry_key == self._current_section_key
                    and candidate_tab.tab_id
                    == candidate_section.current_tab_id
                ),
                "resultModel": self._ensure_tab_workspace_model(candidate_tab),
                "viewMode": candidate_tab.view_mode,
                "splitterRatio": candidate_tab.splitter_ratio,
            }
            for candidate_section in self._sessions.values()
            for candidate_tab in candidate_section.tabs
        ])
        self._search_tab_switch_monitor.record_phase(
            "resultSurfacesMs", (time.perf_counter() - phase_started_at) * 1000,
        )
        phase_started_at = time.perf_counter()
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
        self._tag_context_key = ""
        self._tag_records = []
        self._tag_loading = False
        self._tag_error = ""
        if clear_suggestions:
            self.workspace_state.search_suggestion_model.clear()
        self.search_text_changed.emit()
        self.search_tab_history_changed.emit()
        self.search_state_changed.emit()
        self._search_tab_switch_monitor.record_phase(
            "searchChromeMs", (time.perf_counter() - phase_started_at) * 1000,
        )
        phase_started_at = time.perf_counter()
        self.quick_filters_changed.emit()
        self._search_tab_switch_monitor.record_phase(
            "quickFiltersMs", (time.perf_counter() - phase_started_at) * 1000,
        )
        self.tag_cloud_changed.emit()

    @Slot(str)
    def activate_section(self, key: str) -> None:
        section = self._sessions.get(key)
        if not section:
            return
        section_changed = key != self._current_section_key
        if not section_changed:
            self._search_tab_switch_monitor.cancel()
            self._ensure_sidebar_presets_initialized(section)
            tab = self._current_tab()
            if tab and not tab.workspace_layout:
                self._apply_tab_workspace_layout(section, tab)
            if tab and not (tab.loaded or tab.loading):
                self._sync_search_tabs()
                tab_id = tab.tab_id
                self._show_tab_if_current(key, tab_id)
            return

        switch_monitor = self._search_tab_switch_monitor
        serial = switch_monitor.begin(section.title)
        switch_started_at = switch_monitor.started_at

        def apply_switch():
            if (switch_monitor.metrics.get("serial") != serial
                    or self._sessions.get(key) is not section):
                return
            capture_started_at = time.perf_counter()
            if section_changed:
                self._capture_current_tree_state()
                self._capture_current_workspace_layout()
            capture_ms = (time.perf_counter() - capture_started_at) * 1000
            dock_model = getattr(self, "dock_model", None)
            layout_ms = 0.0
            projection_ms = 0.0
            tab = next(
                (
                    candidate for candidate in section.tabs
                    if candidate.tab_id == section.current_tab_id
                ),
                None,
            )
            prehide = getattr(dock_model, "prehide_for_layout", None)
            prehidden = bool(
                tab is not None
                and tab.workspace_layout
                and callable(prehide)
                and prehide(deepcopy(tab.workspace_layout))
            )
            try:
                self._current_section_key = key
                self._ensure_sidebar_presets_initialized(section)
                sync_started_at = time.perf_counter()
                self._sync_section_model()
                self._sync_search_tabs()
                sync_ms = (time.perf_counter() - sync_started_at) * 1000
                tab = self._current_tab()
                if tab:
                    projection_started_at = time.perf_counter()
                    self._show_tab_if_current(key, tab.tab_id)
                    projection_ms = (
                        time.perf_counter() - projection_started_at
                    ) * 1000
            finally:
                if prehidden and tab is not None:
                    layout_started_at = time.perf_counter()
                    self._apply_tab_workspace_layout(section, tab)
                    layout_ms = (
                        time.perf_counter() - layout_started_at
                    ) * 1000
            if not prehidden and tab is not None:
                layout_started_at = time.perf_counter()
                self._apply_tab_workspace_layout(section, tab)
                layout_ms = (
                    time.perf_counter() - layout_started_at
                ) * 1000
            self._save_opened_sections()
            self._save_search_cache()
            switch_monitor.commit(serial, {
                "serial": serial,
                "tab": section.title,
                "captureMs": round(capture_ms, 3),
                "feedbackWaitMs": round(
                    (capture_started_at - switch_started_at) * 1000, 3,
                ),
                "syncMs": round(sync_ms, 3),
                "layoutMs": round(layout_ms, 3),
                "projectionMs": round(projection_ms, 3),
                "pythonMs": round(
                    capture_ms + layout_ms + sync_ms + projection_ms,
                    3,
                ),
                "rows": self.workspace_model.rowCount() if tab else 0,
                "cached": bool(tab and tab.loaded),
                "kind": "section",
            })

        apply_switch()


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
        self._cancel_sidebar_preset_request(key)
        keys = list(self._sessions)
        closing_index = keys.index(key)
        was_current = key == self._current_section_key
        closing_section = self._sessions[key]
        dock_model = getattr(self, "dock_model", None)
        incoming = None
        incoming_tab = None
        prehidden = False
        if was_current:
            remaining = [candidate for candidate in keys if candidate != key]
            incoming_key = (
                remaining[min(closing_index, len(remaining) - 1)]
                if remaining else ""
            )
            incoming = self._sessions.get(incoming_key)
            if incoming is not None:
                incoming_tab = next(
                    (
                        tab for tab in incoming.tabs
                        if tab.tab_id == incoming.current_tab_id
                    ),
                    None,
                )
            prehide = getattr(dock_model, "prehide_for_layout", None)
            if (
                incoming_tab is not None
                and incoming_tab.workspace_layout
                and callable(prehide)
            ):
                prehidden = bool(
                    prehide(deepcopy(incoming_tab.workspace_layout))
                )
        try:
            del self._sessions[key]
            if was_current:
                self._current_section_key = (
                    incoming.entry_key if incoming is not None else ""
                )
                if incoming is not None:
                    self._ensure_sidebar_presets_initialized(incoming)
            self._sync_section_model()
            # Remove the retained QML surfaces before their QObject models are
            # scheduled for deletion.
            self._sync_search_tabs()
            self._dispose_section_workspace_models(closing_section)
            if self._current_section_key:
                tab = self._current_tab()
                if tab:
                    self._show_tab_if_current(
                        self._current_section_key, tab.tab_id
                    )
            else:
                self.workspace_model.clear()
                self.workspace_state.clear_selection()
                self._result_count = 0
                self.result_count_changed.emit()
        finally:
            if prehidden and incoming is not None and incoming_tab is not None:
                self._apply_tab_workspace_layout(incoming, incoming_tab)
        if not prehidden and incoming is not None and incoming_tab is not None:
            self._apply_tab_workspace_layout(incoming, incoming_tab)
        self._save_opened_sections()
        self._save_search_cache()
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
        if not tab:
            return
        switch_monitor = self._search_tab_switch_monitor
        if tab.tab_id == section.current_tab_id:
            switch_monitor.cancel()
            return
        serial = switch_monitor.begin(tab.title)
        switch_started_at = switch_monitor.started_at

        def apply_switch():
            if (switch_monitor.metrics.get("serial") != serial
                    or self._current_section() is not section
                    or tab not in section.tabs):
                return
            capture_started_at = time.perf_counter()
            previous_tab = self._current_tab()
            if previous_tab and previous_tab.loaded:
                self._capture_current_tree_state()
            if previous_tab is not None:
                self._capture_current_workspace_layout()
            capture_ms = (time.perf_counter() - capture_started_at) * 1000
            dock_model = getattr(self, "dock_model", None)
            prehide = getattr(dock_model, "prehide_for_layout", None)
            if tab.workspace_layout and callable(prehide):
                prehide(deepcopy(tab.workspace_layout))
            self._selection_load_timer.stop()
            self._pending_selection_load = None
            self._cancel_selected_payload_worker()
            self._cancel_versions_worker()
            self._pending_versions_node_id = ""
            self._detail_request_id = ""
            self._versions_request_id = ""
            sync_ms = 0.0
            projection_ms = 0.0
            layout_ms = 0.0
            try:
                section.current_tab_id = tab.tab_id
                sync_started_at = time.perf_counter()
                self._sync_search_tabs()
                sync_ms = (time.perf_counter() - sync_started_at) * 1000
                projection_started_at = time.perf_counter()
                # A cached tab is already local state. Applying it in a later
                # event-loop pass exposed the outgoing model and an empty
                # intermediate layout as separate frames.
                self._show_tab_if_current(section.entry_key, tab.tab_id)
                projection_ms = (
                    time.perf_counter() - projection_started_at
                ) * 1000
            finally:
                layout_started_at = time.perf_counter()
                self._apply_tab_workspace_layout(section, tab)
                layout_ms = (
                    time.perf_counter() - layout_started_at
                ) * 1000
            row_count = self.workspace_model.rowCount()
            switch_monitor.commit(serial, {
                "serial": serial,
                "tab": tab.title,
                "captureMs": round(capture_ms, 3),
                "feedbackWaitMs": round(
                    (capture_started_at - switch_started_at) * 1000, 3,
                ),
                "syncMs": round(sync_ms, 3),
                "layoutMs": round(layout_ms, 3),
                "projectionMs": round(projection_ms, 3),
                "pythonMs": round(
                    capture_ms + sync_ms + layout_ms + projection_ms,
                    3,
                ),
                "rows": row_count,
                "cached": bool(tab.loaded),
            })

        apply_switch()

    def _show_or_load_tab(self, tab: SearchTabSession) -> None:
        self._card_path = list(tab.card_path)
        self._pending_card_focus_id = ""
        self.workspace_model.set_process_ignore(tab.process_ignore)
        # A tab switch changes the projection as one operation.  Rebuilding
        # here would first reorganize the previous tab and then replace every
        # row again with the target tab.
        self._configure_result_organization(tab, rebuild=False)
        if tab.loaded:
            self._versions_request_id = ""
            phase_started_at = time.perf_counter()
            visible_sobjects = self._visible_sobjects(tab)
            result_model = self.workspace_model
            projection = tab.workspace_projection
            # A projection owned by this exact retained model is only a
            # readiness marker here. The live model already contains newer
            # expansion, selection, preview, and delegate state; replaying an
            # older projection would republish rows and recreate delegates.
            projection_restored = (
                projection is not None
                and getattr(projection, "owner_model", None) is result_model
            )
            if not projection_restored and projection is not None:
                projection_restored = result_model.restore_projection(
                    projection
                )
            if not projection_restored and tab.workspace_roots:
                result_model.replace_nodes(
                    tab.workspace_roots,
                    tab.stype,
                    preserve_slots=True,
                )
            elif not projection_restored:
                result_model.replace_sobjects(
                    visible_sobjects,
                    tab.stype,
                )
            if tab.view_mode == "tiles" and not projection_restored:
                result_model.show_card_level()
            elif tab.view_mode == "table":
                result_model.show_table_rows()
            if not projection_restored:
                tab.workspace_roots = list(result_model._roots)
                tab.workspace_projection = result_model.capture_projection()
            self._search_tab_switch_monitor.record_phase(
                "projectionPublishMs",
                (time.perf_counter() - phase_started_at) * 1000,
            )
            phase_started_at = time.perf_counter()
            self.workspace_state.load_stype(tab.stype)
            self._search_tab_switch_monitor.record_phase(
                "schemaMs",
                (time.perf_counter() - phase_started_at) * 1000,
            )
            phase_started_at = time.perf_counter()
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
            if (
                details_restored
                and tab.view_mode in {"continious", "compact", "table"}
            ):
                self.versions_model.clear()
            if not details_restored and selected and selected.search_key:
                self.versions_model.clear()
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
                self.versions_model.clear()
                self._load_sobject_details(
                    visible_sobjects[0].get_search_key()
                )
            elif not details_restored:
                self.versions_model.clear()
                self.workspace_state.clear_selection()
            self._search_tab_switch_monitor.record_phase(
                "detailsMs",
                (time.perf_counter() - phase_started_at) * 1000,
            )
            phase_started_at = time.perf_counter()
            self._set_result_state(tab)
            self._search_tab_switch_monitor.record_phase(
                "resultStateSignalsMs",
                (time.perf_counter() - phase_started_at) * 1000,
            )
            phase_started_at = time.perf_counter()
            self.section_state_changed.emit()
            self._search_tab_switch_monitor.record_phase(
                "sectionSignalMs",
                (time.perf_counter() - phase_started_at) * 1000,
            )
            restore_viewport = tab.viewport_restore_pending or not projection_restored
            tab.viewport_restore_pending = False
            phase_started_at = time.perf_counter()
            if restore_viewport:
                self._restore_result_viewport(tab)
            self._search_tab_switch_monitor.record_phase(
                "viewportMs",
                (time.perf_counter() - phase_started_at) * 1000,
            )
            return
        if tab.loading:
            # A first load can already be running for a retained background
            # tab. Establish its empty/loading detail projection before its
            # section layout presents selection-driven docks; otherwise they
            # would momentarily consume the outgoing section's object.
            self.versions_model.clear()
            self.workspace_state.clear_selection()
            self._set_result_state(tab)
            return
        if tab.loaded_page_offsets:
            self._restore_cached_tab(tab)
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

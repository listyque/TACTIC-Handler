"""Application controller: search tabs."""

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
from ..search_contract import create_search_tab
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

class SearchTabsMixin:
    @Slot()
    def refresh_current(self) -> None:
        tab = self._current_tab()
        if tab:
            self._capture_current_tree_state(persist_tree=True)
            tab.loaded = False
            tab.clear_result_projection()
            self._load_tab(tab, append=False, bypass_cache=True)
            if self._quick_filter_runtime.context_key:
                self._request_quick_filter_catalog(force=True)

    @Slot()
    def refresh_snapshot_browser(self) -> None:
        """Refresh the selected item's snapshots without reloading the page."""
        if self._task_snapshot_source is not None:
            search_key, process, context = self._task_snapshot_identity
            self.load_task_snapshot_context(
                self._task_snapshot_source,
                search_key,
                process,
                context,
                force=True,
            )
            return
        if self._selected_detail_key:
            self._load_sobject_details(
                self._selected_detail_key,
                self._selected_detail_process or None,
                self._selected_detail_snapshot_node_id or None,
                True,
            )

    def refresh_snapshot_browser_for(self, search_key: str) -> None:
        if search_key and search_key == self._selected_detail_key:
            self.refresh_snapshot_browser()

    @Slot(str)
    def toggle_snapshot_browser_option(self, option: str) -> None:
        if option == "all":
            self._snapshot_browser_show_all = (
                not self._snapshot_browser_show_all
            )
            self._settings["snapshotBrowser/showAll"] = (
                self._snapshot_browser_show_all
            )
            self._write_settings()
        elif option == "more":
            self._snapshot_browser_show_more = (
                not self._snapshot_browser_show_more
            )
            self._settings["snapshotBrowser/showMore"] = (
                self._snapshot_browser_show_more
            )
            self._write_settings()
        else:
            return
        self.snapshot_browser_changed.emit()

    @Slot(str)
    def set_snapshot_browser_content_mode(self, mode: str) -> None:
        if mode not in {"both", "preview", "files"}:
            return
        if self._snapshot_browser_content_mode == mode:
            return
        self._snapshot_browser_content_mode = mode
        self._settings["snapshotBrowser/contentMode"] = mode
        self._write_settings()
        self.snapshot_browser_changed.emit()

    @Slot(str)
    def set_snapshot_browser_orientation(self, orientation: str) -> None:
        if orientation not in {"horizontal", "vertical"}:
            return
        if self._snapshot_browser_orientation == orientation:
            return
        self._snapshot_browser_orientation = orientation
        self._settings["snapshotBrowser/orientation"] = orientation
        self._write_settings()
        self.snapshot_browser_changed.emit()

    @Slot(float)
    def set_snapshot_browser_splitter_ratio(self, ratio: float) -> None:
        ratio = max(0.22, min(0.78, float(ratio)))
        if abs(self._snapshot_browser_splitter_ratio - ratio) < 0.002:
            return
        self._snapshot_browser_splitter_ratio = ratio
        # A native splitter changes this value for every mouse move. Writing
        # Persist only after the drag settles; synchronous disk writes during
        # every pointer event make resizing visibly lag.
        self._snapshot_splitter_save_timer.start(180)
        self.snapshot_browser_changed.emit()

    @Slot()
    def add_search_tab(self) -> None:
        section = self._current_section()
        if not section:
            return
        self._capture_current_tree_state()
        self._capture_current_workspace_layout()
        current = self._current_tab()
        tab = create_search_tab(
            section.entry_key,
            f"New Search {len(section.tabs) + 1}",
            tab_kind="user",
            limit=self._page_size,
            view_mode=self._default_view_mode,
            ensure_name_row=True,
        )
        if current is not None:
            tab.workspace_layout = deepcopy(current.workspace_layout)
        section.tabs.append(tab)
        section.current_tab_id = tab.tab_id
        self._sync_search_tabs()
        self.section_state_changed.emit()
        # A loaded server standard is applied synchronously by the section
        # signal and may already start the correctly filtered request.
        if not tab.loading:
            self._load_tab(tab)

    @Slot(int)
    def close_search_tab(self, row: int) -> None:
        section = self._current_section()
        if not section or not 0 <= row < len(section.tabs) or len(section.tabs) == 1:
            return
        was_current = section.tabs[row].tab_id == section.current_tab_id
        if was_current:
            self._capture_current_tree_state()
            self._capture_current_workspace_layout()
        section.closed_tabs.append(section.tabs.pop(row))
        if was_current:
            target = section.tabs[min(row, len(section.tabs) - 1)]
            self._activate_workspace_tab(target.tab_id, target.title)
        else:
            self._sync_search_tabs()
        self.section_state_changed.emit()

    @Slot(int)
    def restore_closed_search_tab(self, row: int) -> None:
        section = self._current_section()
        if not section or not 0 <= row < len(section.closed_tabs):
            return
        tab = section.closed_tabs.pop(row)
        section.tabs.append(tab)
        self._activate_workspace_tab(tab.tab_id, tab.title)
        self.section_state_changed.emit()

    @Slot()
    def clear_search_tab_history(self) -> None:
        section = self._current_section()
        if not section or not section.closed_tabs:
            return
        for tab in section.closed_tabs:
            self._dispose_tab_workspace_model(tab)
        section.closed_tabs.clear()
        self.search_tab_history_changed.emit()

    @Slot(int, int)
    def reorder_search_tab(self, source_row: int, target_row: int) -> None:
        section = self._current_section()
        if (
            not section
            or not 0 <= source_row < len(section.tabs)
            or not 0 <= target_row < len(section.tabs)
            or source_row == target_row
        ):
            return
        tab = section.tabs.pop(source_row)
        section.tabs.insert(target_row, tab)
        self._sync_search_tabs()

    @Slot(str)
    def set_loading_mode(self, mode: str) -> None:
        if mode not in {"pages", "infinite"} or mode == self._loading_mode:
            return
        self._loading_mode = mode
        self._settings["search/loadingMode"] = mode
        self._write_settings()
        tab = self._current_tab()
        if tab:
            self._capture_current_tree_state(persist_tree=True)
            tab.offset = 0
            tab.next_offset = 0
            tab.exhausted = False
            tab.duplicate_pages = 0
            tab.loaded = False
            tab.clear_result_projection()
            self._load_tab(tab)
        self.paging_state_changed.emit()

    @Slot(int)
    def set_page_size(self, size: int) -> None:
        if not 20 <= size <= 5000:
            return
        tab = self._current_tab()
        if tab:
            self._capture_current_tree_state(persist_tree=True)
            tab.limit = size
            tab.offset = 0
            tab.next_offset = 0
            tab.exhausted = False
            tab.duplicate_pages = 0
            tab.loaded = False
            tab.clear_result_projection()
            self._load_tab(tab)
        self.paging_state_changed.emit()

    @Slot(int)
    def go_to_page(self, page: int) -> None:
        tab = self._current_tab()
        if not tab or self._loading_mode != "pages":
            return
        page = max(1, min(page, max(1, math.ceil(tab.total / tab.limit))))
        offset = (page - 1) * tab.limit
        if offset == tab.offset and tab.loaded:
            return
        self._capture_current_tree_state(persist_tree=True)
        tab.offset = offset
        tab.loaded = False
        tab.clear_result_projection()
        self._load_tab(tab)

    @Slot()
    def next_page(self) -> None:
        self.go_to_page(self.current_page + 1)

    @Slot()
    def previous_page(self) -> None:
        self.go_to_page(self.current_page - 1)

    @Slot()
    def load_more(self) -> None:
        tab = self._current_tab()
        if (
            not tab
            or tab.loading
            or bool(tab.error)
            or tab.cancelled
            or self._loading_mode != "infinite"
            or tab.exhausted
            or (tab.total > 0 and tab.next_offset >= tab.total)
        ):
            return
        self._load_tab(tab, append=True)

    @Slot()
    def cancel_search(self) -> None:
        tab = self._current_tab()
        if not tab or not tab.loading:
            return
        request_id = tab.request_id
        tab.request_id = uuid.uuid4().hex
        tab.loading = False
        tab.loading_append = False
        tab.error = ""
        tab.cancelled = True
        if self._active_request_id == request_id:
            self._active_request_id = ""
            self._set_loading(False, "Search cancelled")
        self.search_state_changed.emit()

    @Slot()
    def retry_search(self) -> None:
        tab = self._current_tab()
        if not tab or tab.loading:
            return
        if tab.failure_count >= 3:
            self._notify("Search retry limit reached (3 attempts)")
            return
        tab.error = ""
        tab.cancelled = False
        self._load_tab(tab, append=False)

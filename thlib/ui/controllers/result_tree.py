"""Application controller: result tree."""

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

class ResultTreeMixin:
    @staticmethod
    def _selected_tree_owner(model, tab):
        node = model.node_for(tab.selected_node_id) if tab else None
        visited = set()
        while node is not None and node.node_id not in visited:
            visited.add(node.node_id)
            if node.node_type == "sobject":
                return node
            node = model.node_for(node.parent_id)
        return None

    def _current_tree_keeps_checkin_parent(
        self,
        section_key: str,
        tab_id: str,
        model,
        search_key: str,
        owner_node_id: str = "",
    ) -> bool:
        section = self._current_section()
        tab = self._current_tab()
        if (
            section is None
            or tab is None
            or section.entry_key != section_key
            or tab.tab_id != tab_id
            or tab.workspace_model is not model
            or tab.view_mode in {"tiles", "table"}
            or not model.has_loaded_sobject(search_key, visible_only=True)
        ):
            return False
        owner = self._selected_tree_owner(model, tab)
        return bool(
            owner
            and owner.search_key == search_key
            and (not owner_node_id or owner.node_id == owner_node_id)
        )

    @Slot("QVariantMap", "QVariantMap")
    def refresh_checkin_result(self, payload, snapshot) -> None:
        """Refresh a live check-in branch without reviving stale UI state."""
        payload = dict(payload or {})
        snapshot = dict(snapshot or {})
        search_key = str(payload.get("searchKey") or "")
        context = str(payload.get("context") or "")
        process = str(
            payload.get("process")
            or context.split("/", 1)[0]
            or "publish"
        )
        snapshot_code = str(snapshot.get("code") or "")
        section = self._current_section()
        tab = self._current_tab()
        if not search_key or section is None or tab is None:
            return
        model = self.workspace_model
        owner = self._selected_tree_owner(model, tab)
        if owner is None or owner.search_key != search_key:
            return
        if not self._current_tree_keeps_checkin_parent(
            section.entry_key,
            tab.tab_id,
            model,
            search_key,
            owner.node_id,
        ):
            # Keep the established Snapshot Browser refresh when the same
            # object is still selected but its result tree was never opened.
            # The selected owner still matches here; the fallback therefore
            # cannot revive another tab or another object's details.
            self.refresh_snapshot_browser_for(search_key)
            return

        try:
            from thlib.environment import env_inst

            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            request_id = uuid.uuid4().hex
            self._checkin_tree_refresh_requests[request_id] = (
                section.entry_key,
                tab.tab_id,
                model,
                search_key,
                owner.node_id,
            )
            model.set_search_key_loading(search_key, True)
            worker = env_inst.server_pool.add_task(
                model.prepare_snapshot_branch_refresh,
                search_key,
                process,
                context,
                snapshot_code,
                owner.node_id,
                bool(
                    payload.get("updateVersionless")
                    or payload.get("onlyVersionless")
                ),
            )
            if worker is None:
                raise RuntimeError("Server worker pool is not available")
            worker.add_result_data(request_id)
            worker.result.connect(self._checkin_tree_refresh_ready)
            worker.error.connect(self._checkin_tree_refresh_failed)
            worker.start()
        except Exception as error:
            self._checkin_tree_refresh_requests.pop(
                locals().get("request_id", ""), None,
            )
            model.set_search_key_loading(search_key, False)
            if self.debug_log:
                self.debug_log.log(
                    "ERROR",
                    str(error),
                    group="checkin/tree-refresh",
                    source="Controller",
                    stacktrace=traceback.format_exc(),
                    caller=2,
                )
            self.refresh_snapshot_browser_for(search_key)

    @Slot(object)
    def _checkin_tree_refresh_ready(self, result) -> None:
        search_key, refresh, request_id = result
        request = self._checkin_tree_refresh_requests.pop(
            str(request_id or ""), None,
        )
        if request is None:
            return
        section_key, tab_id, model, expected_key, owner_node_id = request
        if str(search_key or "") != expected_key:
            model.set_search_key_loading(expected_key, False, notify=False)
            return
        if not self._current_tree_keeps_checkin_parent(
            section_key,
            tab_id,
            model,
            expected_key,
            owner_node_id,
        ):
            # The user moved on while the worker was running. Do not publish
            # even a loading-role update into the now hidden retained model.
            model.set_search_key_loading(expected_key, False, notify=False)
            return

        model.set_search_key_loading(expected_key, False)
        reveal_node_id = model.apply_snapshot_branch_refresh(refresh)
        tab = self._current_tab()
        if tab is not None:
            tab.workspace_roots = list(model._roots)
            tab.workspace_projection = model.capture_projection()
            tab.tree_state_dirty = True
        reveal_node = model.node_for(reveal_node_id)
        if reveal_node is None:
            self.refresh_snapshot_browser_for(expected_key)
            return
        self.select_result_node(
            reveal_node.node_id,
            reveal_node.search_key,
            reveal_node.node_type,
        )
        self.result_node_reveal_requested.emit(reveal_node.node_id)
        self._save_search_cache()

    @Slot(object)
    def _checkin_tree_refresh_failed(self, error) -> None:
        payload, worker = error
        request_id = str(worker.get_result_data() or "") if worker else ""
        request = self._checkin_tree_refresh_requests.pop(request_id, None)
        if request is None:
            return
        section_key, tab_id, model, search_key, owner_node_id = request
        current = self._current_tree_keeps_checkin_parent(
            section_key,
            tab_id,
            model,
            search_key,
            owner_node_id,
        )
        model.set_search_key_loading(
            search_key, False, notify=current,
        )
        if self.debug_log:
            self.debug_log.log(
                "ERROR",
                "Check-in completed, but its result tree could not refresh",
                group="checkin/tree-refresh",
                source="Controller",
                stacktrace=str(payload.get("stacktrace") or ""),
                caller=2,
            )
        if current:
            self.refresh_snapshot_browser_for(search_key)

    def _restore_viewport_if_tree_idle(self, tab_id: str) -> None:
        tab = self._current_tab()
        if (
            not tab
            or tab.tab_id != tab_id
            or not tab.viewport_restore_pending
            or self._restoring_nodes
        ):
            return
        tab.viewport_restore_pending = False
        self._restore_result_viewport(tab)

    def _continue_tree_restore(
        self,
        node_ids: list[str],
        tab_id: str,
    ) -> None:
        self._restore_tree_nodes(node_ids)
        self._restore_viewport_if_tree_idle(tab_id)

    def _restore_tree_nodes(self, node_ids: list[str]) -> None:
        for node_id in node_ids:
            node = self.workspace_model.node_for(node_id)
            if (
                not node
                or node.loaded
                or node_id in self._node_load_requests
            ):
                continue
            self._restoring_nodes.add(node_id)
            self.toggle_result_node(node_id)

    @Slot(str)
    def toggle_result_node(self, node_id: str) -> None:
        try:
            node = self.workspace_model.node_for(node_id)
            if not node or not node.has_children:
                return
            if node.loaded or node.expanded:
                self.workspace_model.toggle_node(node_id)
                self._save_search_cache()
                return
            if node_id in self._node_load_requests:
                return

            from thlib.environment import env_inst

            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            request_id = uuid.uuid4().hex
            title = node.title or node.code or "item"
            started_at = time.perf_counter()
            self._node_load_requests[node_id] = (
                request_id,
                started_at,
                title,
            )
            self.workspace_model.set_node_loading(node_id, True)
            self._set_loading(True, f"Loading item: {title}")
            worker = env_inst.server_pool.add_task(
                self.workspace_model.load_node,
                node_id,
            )
            worker.add_result_data((node_id, request_id))
            worker.result.connect(self._async_node_load_result)
            worker.error.connect(self._async_node_load_error)
            worker.start()
        except Exception as error:
            self._node_load_requests.pop(node_id, None)
            self.workspace_model.set_node_loading(node_id, False)
            self._set_loading(False, f"Item load failed: {error}")
            self._notify(str(error))

    def _set_loaded_branch_expanded(self, node, expanded: bool) -> list[str]:
        pending = []
        node.expanded = expanded
        node.restore_expanded = expanded
        for child in node.children:
            if not child.has_children:
                continue
            if expanded and not child.loaded:
                pending.append(child.node_id)
                continue
            pending.extend(
                self._set_loaded_branch_expanded(child, expanded)
            )
        return pending

    @Slot(str, bool)
    def toggle_result_node_recursive(
        self,
        node_id: str,
        recursive: bool,
    ) -> None:
        if not recursive:
            self.toggle_result_node(node_id)
            return
        node = self.workspace_model.node_for(node_id)
        if not node or not node.has_children:
            return
        if node.expanded:
            self._set_loaded_branch_expanded(node, False)
            self.workspace_model.replace_nodes(
                self.workspace_model._roots,
                self.workspace_model._stype,
            )
            self._save_search_cache()
            return
        if not node.loaded:
            self._recursive_node_loads.add(node_id)
            self.toggle_result_node(node_id)
            return
        pending = self._set_loaded_branch_expanded(node, True)
        self.workspace_model.replace_nodes(
            self.workspace_model._roots,
            self.workspace_model._stype,
        )
        for child_id in pending:
            self._recursive_node_loads.add(child_id)
            self.toggle_result_node(child_id)
        self._save_search_cache()

    @Slot(object)
    def _async_node_load_result(self, result) -> None:
        loaded_node_id, _loaded, loaded_payload, metadata = result
        node_id, request_id = metadata
        request = self._node_load_requests.get(node_id)
        if not request or request[0] != request_id:
            return
        _, started_at, title = self._node_load_requests.pop(node_id)
        restoring = node_id in self._restoring_nodes
        self._restoring_nodes.discard(node_id)
        recursive = node_id in self._recursive_node_loads
        self._recursive_node_loads.discard(node_id)
        loaded_node = self.workspace_model.node_for(loaded_node_id)
        if not self.workspace_model.apply_loaded_node(
            loaded_node_id,
            loaded_payload,
        ):
            self.workspace_model.set_node_loading(node_id, False)
            self._finish_node_loading_state(
                f"Item load was superseded: {title}"
            )
            return
        loaded_node = self.workspace_model.node_for(loaded_node_id)
        has_deferred_state = bool(
            loaded_node and loaded_node.restore_state
        )
        self.workspace_model.toggle_node(loaded_node_id)
        recursive_pending = []
        if recursive and loaded_node:
            recursive_pending = self._set_loaded_branch_expanded(
                loaded_node,
                True,
            )
            self.workspace_model.replace_nodes(
                self.workspace_model._roots,
                self.workspace_model._stype,
            )
        pending_restore, restored_selection = (
            self.workspace_model.apply_node_restore_state(loaded_node_id)
            if restoring or has_deferred_state else ([], "")
        )
        tab = self._current_tab()
        restored_search_key = ""
        if tab and restored_selection:
            tab.selected_node_id = restored_selection
            if not tab.selected_node_ids:
                tab.selected_node_ids = [restored_selection]
            if not tab.selection_anchor_id:
                tab.selection_anchor_id = restored_selection
            selected = self.workspace_model.node_for(restored_selection)
            if selected and selected.search_key:
                restored_search_key = selected.search_key
            self.section_state_changed.emit()
        # Do not recollect a partially restored tree: unloaded descendants
        # deliberately remain collapsed until their asynchronous result
        # arrives, while their original `e` state is carried in restore_state.
        if not (
            (restoring or has_deferred_state)
            and (pending_restore or self._restoring_nodes)
        ):
            self._save_search_cache()
        self.workspace_model.set_node_loading(node_id, False)
        if self._pending_card_focus_id == loaded_node_id:
            self._pending_card_focus_id = ""
            self._card_path.append(loaded_node_id)
            self.workspace_model.show_card_level(loaded_node_id)
            self.results_view_changed.emit()
        self._finish_node_loading_state(
            f"Item loaded: {title} · "
            f"{self._transaction_metrics(started_at, loaded_payload)}"
        )
        tab_id = tab.tab_id if tab else ""
        if pending_restore:
            self._continue_tree_restore(pending_restore, tab_id)
        elif tab_id:
            self._restore_viewport_if_tree_idle(tab_id)
        if recursive_pending:
            for child_id in recursive_pending:
                self._recursive_node_loads.add(child_id)
                self.toggle_result_node(child_id)
        elif restored_search_key:
            self._load_sobject_details(restored_search_key)

    @Slot(object)
    def _async_node_load_error(self, error) -> None:
        payload, worker = error
        metadata = worker.get_result_data() if worker else None
        node_id, request_id = metadata or ("", "")
        request = self._node_load_requests.get(node_id)
        if not request or request[0] != request_id:
            return
        self._report_error_payload(payload, "items/children", worker)
        _, started_at, title = self._node_load_requests.pop(node_id)
        self._restoring_nodes.discard(node_id)
        self._recursive_node_loads.discard(node_id)
        if self._pending_card_focus_id == node_id:
            self._pending_card_focus_id = ""
        self.workspace_model.set_node_loading(node_id, False)
        message = str(payload.get("exception") or error)
        self._finish_node_loading_state(
            f"Item load failed: {title} · "
            f"{self._transaction_metrics(started_at)} · {message}"
        )
        self._notify(message)

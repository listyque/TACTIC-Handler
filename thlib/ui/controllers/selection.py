"""Application controller: selection."""

from __future__ import annotations

from collections.abc import Callable
import json
import math
import re
import sys
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

class SelectionMixin:
    def _cancel_selected_payload_worker(self) -> None:
        """Detach a stale detail request before scheduling its replacement."""
        worker = self._detail_worker
        self._detail_worker = None
        if worker is None:
            return
        try:
            worker.cancel()
        except (AttributeError, RuntimeError):
            pass

    def _cancel_versions_worker(self) -> None:
        worker = self._versions_worker
        self._versions_worker = None
        if worker is None:
            return
        try:
            worker.cancel()
        except (AttributeError, RuntimeError):
            pass

    @Slot(str)
    def select_sobject(self, search_key: str) -> None:
        self._load_sobject_details(search_key)

    def _multi_selection_allowed(self, first, candidate) -> bool:
        if not first or not candidate:
            return False
        if first.parent_id != candidate.parent_id:
            return False
        if first.node_type != candidate.node_type:
            return False
        if candidate.node_type in {"process", "relation"}:
            return False
        return True

    def _selection_range(self, anchor_id: str, node_id: str) -> list[str]:
        first_row = self.workspace_model.row_for_node(anchor_id)
        last_row = self.workspace_model.row_for_node(node_id)
        if first_row < 0 or last_row < 0:
            return [node_id]
        low, high = sorted((first_row, last_row))
        anchor = self.workspace_model.node_for(anchor_id)
        return [
            candidate.node_id
            for candidate in self.workspace_model._items[low:high + 1]
            if self._multi_selection_allowed(anchor, candidate)
        ]

    @Slot(str, str, str, int, bool)
    def select_result_node(
        self,
        node_id: str,
        search_key: str,
        node_type: str,
        modifiers: int = 0,
        preserve_selection: bool = False,
    ) -> None:
        tab = self._current_tab()
        if not tab:
            return
        node = self.workspace_model.node_for(node_id)
        if not node:
            return
        if node.node_type == "sobject" and node.source:
            self.repository_sync.request_presets(node.source)
        control = bool(modifiers & Qt.KeyboardModifier.ControlModifier.value)
        shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier.value)
        alt = bool(modifiers & Qt.KeyboardModifier.AltModifier.value)
        old_ids = list(tab.selected_node_ids)
        old_current = tab.selected_node_id
        if preserve_selection and node_id in old_ids:
            selected_ids = old_ids
        elif shift and tab.selection_anchor_id:
            ranged = self._selection_range(tab.selection_anchor_id, node_id)
            selected_ids = list(dict.fromkeys(
                old_ids + ranged if control else ranged
            ))
        elif control:
            compatible = all(
                self._multi_selection_allowed(
                    self.workspace_model.node_for(selected_id),
                    node,
                )
                for selected_id in old_ids
            )
            selected_ids = list(old_ids) if compatible else []
            if node_id in selected_ids:
                selected_ids.remove(node_id)
            else:
                selected_ids.append(node_id)
            tab.selection_anchor_id = node_id
        else:
            selected_ids = [node_id]
            tab.selection_anchor_id = node_id
        tab.selected_node_ids = selected_ids
        tab.selected_node_id = node_id
        selection_changed = (
            old_current != node_id or old_ids != selected_ids
        )
        if old_current != node_id:
            tab.clear_details()
        if selection_changed:
            self.selected_node_changed.emit()
            self._cancel_selected_payload_worker()
            self._cancel_versions_worker()
            self._pending_versions_node_id = ""
            self._versions_request_id = ""
            self._detail_request_id = ""
            self.versions_model.clear()
        if old_current != node_id:
            self._pending_selection_load = (
                node_id,
                search_key,
                node_type,
            )
            self._selection_load_timer.start()
        if alt:
            self.dock_model.show_panel("snapshot")
        if selection_changed:
            self._save_search_cache()

    @Slot()
    def clear_result_selection(self) -> None:
        tab = self._current_tab()
        if not tab or not (tab.selected_node_id or tab.selected_node_ids):
            return
        tab.selected_node_id = ""
        tab.selected_node_ids = []
        tab.selection_anchor_id = ""
        self._versions_request_id = ""
        self._detail_request_id = ""
        self._cancel_selected_payload_worker()
        self._cancel_versions_worker()
        self._pending_versions_node_id = ""
        self._selection_load_timer.stop()
        self._pending_selection_load = None
        self.versions_model.clear()
        self.workspace_state.clear_selection()
        self.selected_node_changed.emit()
        self._save_search_cache()

    @Slot()
    def select_all_result_siblings(self) -> None:
        tab = self._current_tab()
        current = self.workspace_model.node_for(
            tab.selected_node_id if tab else ""
        )
        if not tab or not current or current.node_type in {"process", "relation"}:
            return
        selected_ids = [
            node.node_id
            for node in self.workspace_model._items
            if self._multi_selection_allowed(current, node)
        ]
        if not selected_ids:
            return
        tab.selected_node_ids = selected_ids
        if not tab.selection_anchor_id:
            tab.selection_anchor_id = current.node_id
        self.selected_node_changed.emit()
        self._save_search_cache()

    @Slot(str)
    def select_version_node(self, node_id: str) -> None:
        node = self.versions_model.node_for(node_id)
        if not node or node.node_type != "snapshot":
            return
        self.workspace_state._build_snapshot_browser_models([node])
        self._verify_snapshot_files_async()

    def _selected_detail_parameters(
        self,
        node_id: str,
        search_key: str,
    ):
        tab = self._current_tab()
        if not tab or tab.selected_node_id != node_id:
            return None
        node = self.workspace_model.node_for(node_id)
        if not node:
            return None
        # Details belong to the selected item's own sObject. A relation branch
        # may contain another full sObject, so walking to the tree root would
        # load the outer object's tasks, notes and snapshots instead.
        detail_owner = node
        while detail_owner and detail_owner.node_type != "sobject":
            if not detail_owner.parent_id:
                detail_owner = None
                break
            detail_owner = self.workspace_model.node_for(
                detail_owner.parent_id
            )
        detail_key = (
            detail_owner.search_key
            if detail_owner and detail_owner.node_type == "sobject"
            else search_key
        )
        if not detail_key:
            return None
        detail_process = (
            node.process or None
            if node.node_type in {"process", "snapshot"}
            else "publish" if node.node_type == "sobject" else None
        )
        return (
            detail_key,
            detail_process,
            node.node_id if node.node_type == "snapshot" else None,
        )

    def _cache_tab_details(
        self,
        tab: SearchTabSession,
        node_id: str,
        details,
        versions=None,
    ) -> None:
        if not tab or not node_id or not details or len(details) != 4:
            return
        tab.details_node_id = node_id
        tab.details_payload = tuple(details)
        tab.details_projection = None
        if versions is not None:
            tab.details_versions = list(versions)
            tab.details_versions_projection = None

    def _restore_tab_details(self, tab: SearchTabSession, node) -> bool:
        if (
            not tab
            or not node
            or tab.details_node_id != node.node_id
            or not tab.details_payload
        ):
            return False
        sobject, tasks, notes, snapshots = tab.details_payload
        if not sobject:
            return False
        parameters = self._selected_detail_parameters(
            node.node_id, node.search_key
        )
        if parameters:
            detail_key, detail_process, snapshot_node_id = parameters
            self._selected_detail_key = detail_key
            self._selected_detail_process = str(detail_process or "")
            self._selected_detail_snapshot_node_id = str(
                snapshot_node_id or ""
            )
        else:
            self._selected_detail_key = str(node.search_key or "")
            self._selected_detail_process = ""
            self._selected_detail_snapshot_node_id = ""
        self._task_snapshot_source = None
        self._task_snapshot_identity = ("", "", "")
        if not self.workspace_state.restore_selection_projection(
            tab.details_projection
        ):
            self.workspace_state.load_sobject(
                sobject, tasks, notes, snapshots, node,
                notes_process=self._selected_detail_process or None,
            )
            tab.details_projection = (
                self.workspace_state.capture_selection_projection()
            )
        if tab.view_mode not in {"continious", "compact", "table"}:
            if not self.versions_model.restore_projection(
                tab.details_versions_projection
            ):
                self.versions_model.replace_nodes(tab.details_versions)
        return True

    def _load_selected_details(self, node_id: str, search_key: str) -> None:
        parameters = self._selected_detail_parameters(node_id, search_key)
        if parameters:
            self._load_sobject_details(*parameters)

    def _prepare_selected_payload(
        self,
        node_id: str,
        detail_key: str,
        detail_process: str | None,
        snapshot_node_id: str | None,
        include_versions: bool,
    ):
        details = self._prepare_sobject_details(
            detail_key,
            detail_process,
            snapshot_node_id,
        )
        versions = (
            self.workspace_model.version_nodes_for(node_id)
            if include_versions else []
        )
        return versions, details

    def _flush_selected_loads(self) -> None:
        pending = self._pending_selection_load
        if not pending:
            return
        if self._detail_worker is not None:
            # A cancelled worker can remain queued for an arbitrary amount of
            # time. It no longer owns this selection, so do not wait for its
            # settled signal before starting the current generation.
            self._cancel_selected_payload_worker()
        self._pending_selection_load = None
        node_id, search_key, node_type = pending
        tab = self._current_tab()
        if not tab or tab.selected_node_id != node_id:
            return
        parameters = self._selected_detail_parameters(
            node_id,
            search_key,
        )
        if not parameters or node_type not in {
            "sobject", "process", "snapshot"
        }:
            return
        detail_key, detail_process, snapshot_node_id = parameters
        self._task_snapshot_source = None
        self._task_snapshot_identity = ("", "", "")
        include_versions = tab.view_mode not in {
            "continious", "compact", "table"
        }
        request_id = uuid.uuid4().hex
        self._detail_request_id = request_id
        self._versions_request_id = request_id if include_versions else ""
        self._selected_detail_key = detail_key
        self._selected_detail_process = str(detail_process or "")
        self._selected_detail_snapshot_node_id = str(
            snapshot_node_id or ""
        )
        try:
            from thlib.environment import env_inst

            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            worker = env_inst.server_pool.add_task(
                self._prepare_selected_payload,
                node_id,
                detail_key,
                detail_process,
                snapshot_node_id,
                include_versions,
            )
            if worker is None:
                raise RuntimeError("Server worker pool is not available")
            self._detail_worker = worker
            worker.add_result_data((
                node_id,
                detail_key,
                request_id,
                include_versions,
            ))
            worker.result.connect(self._async_selected_payload_result)
            worker.error.connect(self._async_selected_payload_error)
            worker.settled.connect(
                self._selected_payload_worker_settled,
                Qt.ConnectionType.QueuedConnection,
            )
            worker.start()
        except Exception as error:
            if self.debug_log:
                self.debug_log.log(
                    "ERROR",
                    str(error),
                    group="server/item_details",
                    source="Controller",
                    stacktrace=traceback.format_exc(),
                    caller=2,
                )

    @Slot(object)
    def _selected_payload_worker_settled(self, worker) -> None:
        if self._detail_worker is worker:
            self._detail_worker = None
        if self._pending_selection_load:
            self._flush_selected_loads()

    @Slot(object)
    def _async_selected_payload_result(self, result) -> None:
        versions, details, metadata = result
        node_id, detail_key, request_id, include_versions = metadata
        tab = self._current_tab()
        if (
            request_id != self._detail_request_id
            or not tab
            or tab.selected_node_id != node_id
            or detail_key != self._selected_detail_key
        ):
            return
        self._detail_worker = None
        sobject, tasks, notes, snapshots = details
        if include_versions and request_id == self._versions_request_id:
            self.versions_model.replace_nodes(versions)
        if sobject:
            selected_node = self.workspace_model.node_for(node_id)
            self._cache_tab_details(tab, node_id, details, versions)
            self.workspace_state.load_sobject(
                sobject, tasks, notes, snapshots, selected_node,
                notes_process=self._selected_detail_process or None,
            )
            self._verify_snapshot_files_async()
            self.snapshot_data_changed.emit(
                detail_key, self._selected_detail_process
            )

    @Slot(object)
    def _async_selected_payload_error(self, error) -> None:
        payload, worker = error
        metadata = worker.get_result_data() if worker else None
        request_id = metadata[2] if metadata else ""
        if request_id != self._detail_request_id:
            return
        self._detail_worker = None
        self._report_error_payload(payload, "items/details", worker)
        message = str(payload.get("exception") or error)
        self._notify(message)

    def _node_for_any(self, node_id: str):
        return (
            self.workspace_model.node_for(node_id)
            or self.versions_model.node_for(node_id)
        )

    def _prepare_versions(self, node_id: str):
        return (self.workspace_model.version_nodes_for(node_id),)

    def _request_versions(self, node_id: str) -> None:
        if self._versions_worker is not None:
            self._cancel_versions_worker()
        self._pending_versions_node_id = ""
        request_id = uuid.uuid4().hex
        self._versions_request_id = request_id
        self.versions_model.clear()
        node = self.workspace_model.node_for(node_id)
        if not node or node.node_type not in {"sobject", "process", "snapshot"}:
            return
        try:
            from thlib.environment import env_inst
            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            worker = env_inst.server_pool.add_task(
                self._prepare_versions,
                node_id,
            )
            if worker is None:
                raise RuntimeError("Server worker pool is not available")
            self._versions_worker = worker
            worker.add_result_data((node_id, request_id))
            worker.result.connect(self._async_versions_result)
            worker.error.connect(self._async_versions_error)
            worker.settled.connect(
                self._versions_worker_settled,
                Qt.ConnectionType.QueuedConnection,
            )
            worker.start()
        except Exception as error:
            self.versions_model.clear()
            if self.debug_log:
                self.debug_log.log(
                    "ERROR",
                    str(error),
                    group="server/versions",
                    source="Controller",
                    stacktrace=traceback.format_exc(),
                    caller=2,
                )

    @Slot(object)
    def _versions_worker_settled(self, worker) -> None:
        if self._versions_worker is worker:
            self._versions_worker = None
        node_id = self._pending_versions_node_id
        self._pending_versions_node_id = ""
        tab = self._current_tab()
        if node_id and tab and tab.selected_node_id == node_id:
            self._request_versions(node_id)

    @Slot(object)
    def _async_versions_result(self, result) -> None:
        nodes, metadata = result
        node_id, request_id = metadata
        tab = self._current_tab()
        if (
            request_id != self._versions_request_id
            or not tab
            or tab.selected_node_id != node_id
        ):
            return
        self._versions_worker = None
        self.versions_model.replace_nodes(nodes)
        tab.details_versions = list(nodes)

    @Slot(object)
    def _async_versions_error(self, error) -> None:
        payload, worker = error
        self._report_error_payload(payload, "items/versions", worker)
        metadata = worker.get_result_data() if worker else None
        if metadata and metadata[1] == self._versions_request_id:
            self._versions_worker = None
            self.versions_model.clear()

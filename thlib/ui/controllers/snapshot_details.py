"""Application controller: snapshot details."""

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

class SnapshotDetailsMixin:
    def load_task_snapshot_context(
        self,
        source,
        search_key: str,
        process: str,
        context: str = "",
        force: bool = False,
    ) -> None:
        """Load a task parent into the shared Snapshot Browser models."""
        search_key = str(search_key or "")
        process = str(process or "")
        context = str(context or "")
        if not source or not search_key:
            return
        identity = (search_key, process, context)
        source_token = (search_key, id(source))
        previous_identity = self._task_snapshot_identity
        self._task_snapshot_source = source
        self._task_snapshot_identity = identity
        if not self.dock_model.is_panel_presented("snapshot"):
            return
        if (
            not force
            and identity == previous_identity
            and source_token in self._task_snapshot_loaded_sources
            and self.workspace_state.snapshot_model.count() > 0
            and self._selected_detail_key == search_key
            and self._selected_detail_process == process
        ):
            return

        self._selected_detail_key = search_key
        self._selected_detail_process = process
        self._selected_detail_snapshot_node_id = ""
        request_id = uuid.uuid4().hex
        self._task_snapshot_request_id = request_id
        previous = self._task_snapshot_worker
        if previous is not None:
            try:
                previous.cancel()
            except (AttributeError, RuntimeError):
                pass
        try:
            from thlib.environment import env_inst

            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            worker = env_inst.server_pool.add_task(
                self.workspace_model.snapshot_nodes_for_source,
                source,
                search_key,
                process,
                context,
                bool(
                    force
                    or source_token not in self._task_snapshot_loaded_sources
                ),
            )
            if worker is None:
                raise RuntimeError("Server worker pool is not available")
            self._task_snapshot_worker = worker
            worker.result.connect(
                lambda result: self._task_snapshot_context_ready(
                    request_id, identity, source_token, result
                ),
                Qt.ConnectionType.QueuedConnection,
            )
            worker.error.connect(
                lambda error: self._task_snapshot_context_failed(
                    request_id, error
                ),
                Qt.ConnectionType.QueuedConnection,
            )
            worker.start()
        except Exception as error:
            self._task_snapshot_context_failed(request_id, error)

    def _task_snapshot_context_ready(
        self, request_id: str, identity: tuple, source_token: tuple, result,
    ) -> None:
        if (
            request_id != self._task_snapshot_request_id
            or identity != self._task_snapshot_identity
        ):
            return
        self._task_snapshot_worker = None
        self._task_snapshot_loaded_sources.add(source_token)
        nodes, icon_nodes = result
        self.workspace_state.replace_snapshot_nodes(nodes, icon_nodes)
        self._verify_snapshot_files_async()
        self.snapshot_data_changed.emit(identity[0], identity[1])

    def _task_snapshot_context_failed(self, request_id: str, error) -> None:
        if request_id != self._task_snapshot_request_id:
            return
        self._task_snapshot_worker = None
        payload = error[0] if isinstance(error, tuple) and error else error
        worker = (
            error[1]
            if isinstance(error, tuple) and len(error) > 1 else None
        )
        self._report_error_payload(
            payload, "snapshot_browser/task_context", worker
        )

    def invalidate_task_snapshot_context(
        self, search_key: str, process: str = "",
    ) -> None:
        identity = self._task_snapshot_identity
        if (
            self._task_snapshot_source is None
            or str(search_key or "") != identity[0]
            or (process and str(process) != identity[1])
        ):
            return
        self._task_snapshot_loaded_sources.discard(
            (identity[0], id(self._task_snapshot_source))
        )

    def mark_task_snapshot_source_current(self, search_key: str) -> None:
        if (
            self._task_snapshot_source is not None
            and str(search_key or "") == self._task_snapshot_identity[0]
        ):
            self._task_snapshot_loaded_sources.add((
                self._task_snapshot_identity[0],
                id(self._task_snapshot_source),
            ))

    @Slot(str)
    def set_results_view_mode(self, mode: str) -> None:
        if mode not in {
            "continious", "compact", "splitted_vertical",
            "splitted_horizontal", "tiles", "table"
        }:
            return
        tab = self._current_tab()
        if not tab or tab.view_mode == mode:
            return
        tab.view_mode = mode
        if mode == "tiles":
            self.workspace_model.show_card_level(
                self._card_path[-1] if self._card_path else ""
            )
        elif mode == "table":
            self._card_path.clear()
            self._pending_card_focus_id = ""
            self.workspace_model.show_table_rows()
        else:
            self._card_path.clear()
            self._pending_card_focus_id = ""
            self.workspace_model.show_tree_rows()
        self.results_view_changed.emit()
        if mode in {"continious", "compact", "tiles", "table"}:
            self._versions_request_id = ""
            self.versions_model.clear()
        elif tab.selected_node_id:
            self._request_versions(tab.selected_node_id)

    @Slot(str)
    def request_item_preview(self, node_id: str) -> None:
        # Tile and row/table views stay instantiated while switching modes.
        # Tiles request their larger card derivative through the other path;
        # table thumbnails intentionally share the row preview.
        if self.results_view_mode == "tiles":
            return
        for model in (self.workspace_model, self.versions_model):
            request = model.begin_preview_request(node_id)
            if not request:
                continue
            node_type, source = request
            request_token = model.preview_request_token(node_id)
            try:
                from thlib.environment import env_inst

                if env_inst.local_pool.is_stopped:
                    env_inst.local_pool.start()
                worker = env_inst.local_pool.add_task(
                    self._prepare_item_preview,
                    node_type,
                    source,
                )
                worker.add_result_data((
                    model, node_id, source, request_token,
                ))
                worker.result.connect(self._item_preview_ready)
                worker.error.connect(self._item_preview_error)
                worker.start()
            except Exception:
                model.cancel_preview_request(
                    node_id, source, request_token,
                )
                if self.debug_log:
                    self.debug_log.log(
                        "ERROR",
                        "Unable to prepare item preview",
                        group="items/preview",
                        source="Controller",
                        stacktrace=traceback.format_exc(),
                        caller=2,
                    )

    @Slot(str)
    def request_item_card_preview(self, node_id: str) -> None:
        if self.results_view_mode != "tiles":
            return
        for model in (self.workspace_model, self.versions_model):
            request = model.begin_card_preview_request(node_id)
            if not request:
                continue
            node_type, source = request
            request_token = model.preview_request_token(
                node_id, card=True,
            )
            try:
                from thlib.environment import env_inst

                if env_inst.local_pool.is_stopped:
                    env_inst.local_pool.start()
                worker = env_inst.local_pool.add_task(
                    self._prepare_item_card_preview,
                    node_type,
                    source,
                )
                worker.add_result_data((
                    model, node_id, source, request_token,
                ))
                worker.result.connect(self._item_card_preview_ready)
                worker.error.connect(self._item_card_preview_error)
                worker.start()
            except Exception:
                model.cancel_card_preview_request(
                    node_id, source, request_token,
                )
                if self.debug_log:
                    self.debug_log.log(
                        "ERROR",
                        "Unable to prepare card preview",
                        group="items/preview",
                        source="Controller",
                        stacktrace=traceback.format_exc(),
                        caller=2,
                    )

    @staticmethod
    def _prepare_item_preview(node_type: str, source):
        return (WorkspaceItemModel.prepare_preview(node_type, source),)

    @staticmethod
    def _prepare_item_card_preview(node_type: str, source):
        return (WorkspaceItemModel.prepare_card_preview(node_type, source),)

    @Slot(object)
    def _item_preview_ready(self, result) -> None:
        candidates, metadata = result
        model, node_id, source, request_token = metadata
        model.apply_preview(
            node_id, source, candidates, request_token,
        )

    @Slot(object)
    def _item_preview_error(self, error) -> None:
        payload, worker = error
        metadata = worker.get_result_data() if worker else None
        if metadata:
            model, node_id, source, request_token = metadata
            model.cancel_preview_request(
                node_id, source, request_token,
            )
        self._report_error_payload(payload, "items/preview", worker)

    @Slot(object)
    def _item_card_preview_ready(self, result) -> None:
        candidates, metadata = result
        model, node_id, source, request_token = metadata
        model.apply_card_preview(
            node_id, source, candidates, request_token,
        )

    @Slot(object)
    def _item_card_preview_error(self, error) -> None:
        payload, worker = error
        metadata = worker.get_result_data() if worker else None
        if metadata:
            model, node_id, source, request_token = metadata
            model.cancel_card_preview_request(
                node_id, source, request_token,
            )
        self._report_error_payload(payload, "items/preview", worker)

    @Slot(str)
    def mark_item_preview_revealed(self, node_id: str) -> None:
        self.workspace_model.mark_preview_revealed(node_id)
        self.versions_model.mark_preview_revealed(node_id)

    @Slot(str)
    def enter_card_node(self, node_id: str) -> None:
        node = self.workspace_model.node_for(node_id)
        if not node or not node.has_children:
            return
        if not node.loaded:
            self._pending_card_focus_id = node_id
            self.toggle_result_node(node_id)
            return
        if not self._card_path or self._card_path[-1] != node_id:
            self._card_path.append(node_id)
        self.workspace_model.show_card_level(node_id)
        self.results_view_changed.emit()

    @Slot()
    def leave_card_level(self) -> None:
        if self._card_path:
            self._card_path.pop()
        self.workspace_model.show_card_level(
            self._card_path[-1] if self._card_path else ""
        )
        self.results_view_changed.emit()

    @Slot(int)
    def open_card_breadcrumb(self, depth: int) -> None:
        depth = max(0, min(int(depth), len(self._card_path)))
        self._card_path = self._card_path[:depth]
        self.workspace_model.show_card_level(
            self._card_path[-1] if self._card_path else ""
        )
        self.results_view_changed.emit()

    @Slot(float)
    def set_results_splitter_ratio(self, ratio: float) -> None:
        tab = self._current_tab()
        if not tab:
            return
        ratio = max(0.25, min(0.75, float(ratio)))
        if abs(tab.splitter_ratio - ratio) < 0.001:
            return
        tab.splitter_ratio = ratio
        self.results_view_changed.emit()

    def _prepare_sobject_details(
        self,
        search_key: str,
        process: str | None = None,
        snapshot_node_id: str | None = None,
        force_snapshot_refresh: bool = False,
        snapshot_code: str | None = None,
    ):
        sobject = self.workspace_model.source_for_search_key(search_key)
        if not sobject:
            return None, [], [], []

        if not getattr(sobject, "project", None):
            from thlib.environment import env_inst

            project_code = str(sobject.info.get("project_code") or "")
            if not project_code:
                match = re.search(r"[?&]project=([^&]+)", search_key)
                project_code = match.group(1) if match else ""
            if not project_code and str(search_key).startswith("sthpw/"):
                project_code = "sthpw"
            project = None
            if env_inst.projects:
                project = env_inst.get_project_by_code(
                    project_code or getattr(self, "_current_project_code", "")
                )
            if project:
                sobject.project = project

        def values(result):
            if not result:
                return []
            records = result[0] if isinstance(result, tuple) else result
            return list(records.values())

        use_combined_query = (
            process is not None
            and callable(getattr(sobject, "get_code", None))
            and callable(getattr(sobject, "get_project", None))
            and sobject.get_project() is not None
        )
        if use_combined_query:
            from thlib import tactic_classes as tc

            tasks_data, notes_data = tc.get_tasks_and_notes(
                sobject=sobject,
                process=process,
                include_all_tasks=True,
            )
            tasks = list((tasks_data or {}).values())
            notes = list((notes_data or {}).values())
        else:
            tasks = values(sobject.get_tasks_sobjects(
                process=None,
                include_status_log=True,
            ))
            notes = values(sobject.get_notes_sobjects(process=None))
        snapshots = self.workspace_model.snapshot_nodes_for(
            search_key,
            refresh=force_snapshot_refresh,
        )
        if snapshot_code and not snapshot_node_id:
            selected = next((
                node for node in snapshots
                if str(node.code or "") == str(snapshot_code)
            ), None)
            if not selected:
                raise LookupError(
                    "Snapshot is not available: {0}".format(snapshot_code)
                )
            snapshot_node_id = selected.node_id
        if snapshot_node_id:
            selected = next(
                (
                    node for node in snapshots
                    if node.node_id == snapshot_node_id
                ),
                None,
            )
            if selected and selected.is_versionless:
                # Versionless snapshot items in the original browser expose
                # the full version history for that same process/context.
                snapshots = [
                    node for node in snapshots
                    if (
                        node.process == selected.process
                        and node.context == selected.context
                        and node.source
                    )
                ]
                snapshots = sorted(
                    snapshots,
                    key=lambda node: (
                        0 if node.is_versionless else 1,
                        -int(
                            (node.source.get_snapshot() or {}).get(
                                "version"
                            ) or 0
                        ),
                    ),
                )
            else:
                snapshots = [selected] if selected else []
        else:
            snapshots = self._snapshot_browser_nodes_for_context(
                snapshots,
                process,
            )
        return sobject, tasks, notes, snapshots

    @staticmethod
    def _snapshot_browser_nodes_for_context(
        snapshots,
        process: str | None = None,
    ):
        """Order snapshots like Ui_snapshotBrowserWidget."""
        unique = []
        seen = set()
        for node in snapshots or []:
            if not node.source:
                continue
            try:
                key = str(node.source.get_code() or "")
            except (AttributeError, KeyError, TypeError):
                key = ""
            key = key or str(node.search_key or node.node_id)
            if key in seen:
                continue
            seen.add(key)
            unique.append(node)
        if not unique:
            return []

        if process:
            chosen = [
                node for node in unique
                if str(node.process or "") == str(process)
            ]
        else:
            grouped = {}
            for node in unique:
                grouped.setdefault(str(node.process or ""), []).append(node)
            selected_process = next(
                (
                    process_name
                    for process_name in ("publish", "icon")
                    if grouped.get(process_name)
                ),
                next(
                    (
                        process_name for process_name, nodes in grouped.items()
                        if nodes
                    ),
                    "",
                ),
            )
            chosen = grouped.get(selected_process, [])

        def order(node):
            try:
                info = node.source.get_snapshot() or {}
                version = int(info.get("version") or 0)
            except (AttributeError, TypeError, ValueError):
                version = 0
            return (
                0 if node.is_versionless else 1,
                str(node.context or ""),
                -version,
            )

        return sorted(chosen, key=order)

    def _load_sobject_details(
        self,
        search_key: str,
        process: str | None = None,
        snapshot_node_id: str | None = None,
        force_snapshot_refresh: bool = False,
        snapshot_code: str | None = None,
    ) -> None:
        from thlib.environment import env_inst
        self._task_snapshot_source = None
        self._task_snapshot_identity = ("", "", "")
        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        self._selected_detail_key = search_key
        self._selected_detail_process = str(process or "")
        self._selected_detail_snapshot_node_id = str(
            snapshot_node_id or ""
        )
        self._detail_request_id = uuid.uuid4().hex
        self._detail_started_at = time.perf_counter()
        self._set_loading(True, "Loading item details")
        worker = env_inst.server_pool.add_task(
            self._prepare_sobject_details,
            search_key,
            process,
            snapshot_node_id,
            force_snapshot_refresh,
            snapshot_code,
        )
        worker.add_result_data((search_key, self._detail_request_id))
        worker.result.connect(self._async_details_result)
        worker.error.connect(self._async_details_error)
        worker.start()

    @staticmethod
    def _check_snapshot_files(items) -> tuple:
        checks = []
        for token, file_object in items:
            try:
                exists = bool(file_object.is_exists())
            except (AttributeError, KeyError, TypeError, OSError):
                exists = False
            try:
                matches = exists and file_object.is_local_current()
            except (AttributeError, KeyError, TypeError, OSError):
                matches = False
            checks.append((token, exists, matches))
        return (checks,)

    def _verify_snapshot_files_async(self) -> None:
        items = list(
            self.workspace_state._snapshot_file_objects.items()
        )
        if not items:
            return
        from thlib.environment import env_inst
        if env_inst.local_pool.is_stopped:
            env_inst.local_pool.start()
        request_id = uuid.uuid4().hex
        self._snapshot_check_request_id = request_id
        worker = env_inst.local_pool.add_task(
            self._check_snapshot_files,
            items,
        )
        worker.add_result_data(request_id)
        worker.result.connect(self._snapshot_files_checked)
        worker.error.connect(
            lambda error: self._report_error_payload(
                error[0], "snapshot_browser/file_check", error[1]
            )
        )
        worker.start()

    @Slot(object)
    def _snapshot_files_checked(self, result) -> None:
        checks, request_id = result
        if request_id != self._snapshot_check_request_id:
            return
        download_previews = self._checkin_flag(
            "getPreviewsThroughHttpCheckbox", True
        )
        records = self.workspace_state.snapshot_file_model._records
        preview_tokens = {
            str(record.get("token") or "")
            for record in records
            if record.get("previewType")
        }
        for token, exists, matches in checks:
            self.workspace_state.update_snapshot_file_status(
                token,
                exists,
                matches,
            )
            if download_previews and token in preview_tokens and (
                not exists or not matches
            ):
                file_object = self.workspace_state.snapshot_file_for(token)
                if file_object:
                    self.repository_sync.schedule_file_object(
                        file_object,
                        process="preview",
                        auto_start=True,
                        is_ui_preview=True,
                    )

    @Slot(object)
    def _async_details_result(self, result) -> None:
        sobject, tasks, notes, snapshots, metadata = result
        search_key, request_id = metadata
        if (
            search_key != self._selected_detail_key
            or request_id != self._detail_request_id
        ):
            return
        if sobject:
            tab = self._current_tab()
            detail_node = None
            if tab:
                detail_node = self.workspace_model.node_for(
                    tab.selected_node_id
                ) or next((
                    node for node in self.workspace_model._roots
                    if node.search_key == search_key
                ), None)
            if tab and detail_node:
                self._cache_tab_details(
                    tab,
                    detail_node.node_id,
                    (sobject, tasks, notes, snapshots),
                )
            selected_node = next((
                node for node in snapshots
                if node.node_id == self._selected_detail_snapshot_node_id
            ), None)
            self.workspace_state.load_sobject(
                sobject, tasks, notes, snapshots, selected_node,
                notes_process=self._selected_detail_process or None,
            )
            self._finish_table_checkin(sobject)
            self._verify_snapshot_files_async()
            self.snapshot_data_changed.emit(
                search_key, self._selected_detail_process
            )
        self._set_loading(
            False,
            "Item details loaded · "
            f"{self._transaction_metrics(self._detail_started_at, snapshots)}",
        )

    @Slot(object)
    def _async_details_error(self, error) -> None:
        payload, worker = error
        metadata = worker.get_result_data() if worker else None
        search_key, request_id = metadata or ("", "")
        if request_id != self._detail_request_id:
            return
        self._discard_table_checkin(search_key)
        self._report_error_payload(payload, "items/details", worker)
        message = str(payload.get("exception") or error)
        self._set_loading(
            False,
            "Item details failed · "
            f"{self._transaction_metrics(self._detail_started_at)} · {message}",
        )
        self._notify(message)

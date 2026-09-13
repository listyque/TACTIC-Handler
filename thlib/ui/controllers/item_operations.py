"""Application controller: item operations."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
import json
import math
from pathlib import PurePath
import re
import sys
import time
import traceback

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

from tactic_handler_dcc.connectors import dcc_item_action, dcc_trigger_event
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

class ItemOperationsMixin:
    def attach_checkin_workflow(self, checkin_controller, drop_plate_controller) -> None:
        self._checkin_controller = checkin_controller
        self._drop_plate_controller = drop_plate_controller

    def attach_ingest_workflow(self, ingest_controller) -> None:
        self._ingest_controller = ingest_controller

    def repository_sync_editor_context(self) -> dict:
        """Return the active legacy Repo Sync scope without rebuilding it."""
        requested_context = getattr(
            self, "_repository_sync_editor_request", None,
        )
        if requested_context is not None:
            return dict(requested_context)

        tab = self._current_tab()
        node = self._node_for_any(tab.selected_node_id) if tab else None
        return self._repository_sync_context_for_node(node, tab=tab)

    def _repository_sync_context_for_node(
        self, node=None, *, tab=None, whole_search_type: bool = False,
    ) -> dict:
        """Build a Repo Sync scope from an explicit item or Search Type."""
        tab = tab or self._current_tab()
        while node and node.node_type != "sobject" and node.parent_id:
            node = self._node_for_any(node.parent_id)
        sobject = (
            None if whole_search_type
            else node.source if node and node.node_type == "sobject" else None
        )
        stype = None
        if sobject is not None:
            try:
                stype = sobject.get_stype()
            except AttributeError:
                pass
        if stype is None:
            # A Search Tab owns its Search Type.  Do not fall back to the
            # previously active global type: switching tabs and reopening an
            # already visible editor otherwise keeps the old scope.
            stype = getattr(tab, "stype", None) if tab else None
        current_section = getattr(self, "_current_section", None)
        section = current_section() if callable(current_section) else None
        expected_code = str(
            getattr(section, "search_type", "") or ""
        )
        try:
            actual_code = str(stype.get_code() or "") if stype else ""
        except AttributeError:
            actual_code = ""
        # A selected child sObject owns its native Search Type. The Search
        # Tab's type is relevant only for whole-Search-Type synchronization;
        # replacing a valid child type here erased its process tree.
        project = None
        if stype is None or (whole_search_type and expected_code != actual_code):
            try:
                from thlib.environment import env_inst

                project = env_inst.projects.get(self._current_project_code)
                stype = (
                    project.stypes.get(expected_code)
                    if project and project.stypes else None
                )
            except (AttributeError, KeyError, TypeError):
                stype = None
        else:
            try:
                project = stype.get_project()
            except (AttributeError, KeyError, TypeError):
                project = getattr(stype, "project", None)
        search_type = ""
        try:
            search_type = str(stype.get_code() or "") if stype else ""
        except AttributeError:
            search_type = actual_code or expected_code
        return {
            "sobject": sobject,
            "stype": stype,
            "project": project,
            "search_type": search_type or expected_code,
            "tab_name": str(tab.title if tab else "default"),
            "project_code": self._current_project_code,
        }

    def _open_repository_sync_editor(self, context: dict) -> None:
        """Open the editor with an explicit scope, avoiding selection races."""
        self._repository_sync_editor_request = dict(context)
        requested = getattr(self, "repositorySyncEditorRequested", None)
        if requested is not None:
            requested.emit()
        window_id = "repository_sync_editor"
        is_visible = getattr(self.window_model, "is_window_visible", None)
        if callable(is_visible) and is_visible(window_id):
            # `windowVisibleChanged` is not emitted for an already open
            # window, so explicitly restart the session with the new tab.
            raise_window = getattr(self.window_model, "raise_window", None)
            if callable(raise_window):
                raise_window(window_id)
        else:
            self.window_model.show_window(window_id)

    @Slot()
    def open_search_type_repository_sync(self) -> None:
        """Open legacy-style Repo Sync for every sObject in the active type."""
        tab = self._current_tab()
        context = self._repository_sync_context_for_node(
            None, tab=tab, whole_search_type=True,
        )
        if context.get("stype") is None:
            self._notify("No active Search Type is available for Repository Sync")
            return
        self._open_repository_sync_editor(context)

    def _checkin_target_for_node(self, node):
        selected = node
        target = node
        while target and target.node_type != "sobject" and target.parent_id:
            target = self._node_for_any(target.parent_id)
        if not target or target.node_type != "sobject" or target.source is None:
            return None
        process = "publish"
        context = "publish"
        if selected and selected.node_type in {"process", "snapshot"}:
            process = str(selected.process or "publish")
            context = str(selected.context or process)
        description = ""
        version = 0
        if selected and selected.node_type == "snapshot" and selected.source:
            try:
                snapshot = dict(selected.source.get_snapshot() or {})
            except (AttributeError, TypeError, ValueError):
                snapshot = {}
            description = str(snapshot.get("description") or "")
            try:
                version = max(0, int(snapshot.get("version") or 0))
            except (TypeError, ValueError):
                version = 0
        workspace_state = getattr(self, "workspace_state", None)
        pinned_description = str(
            getattr(workspace_state, "checkinDescription", "") or ""
        )
        if pinned_description:
            description = pinned_description
        return {
            "node": target,
            "source": target.source,
            "searchKey": str(target.search_key or ""),
            "projectCode": str(self._current_project_code or ""),
            "title": str(target.title or target.code or "sObject"),
            "code": str(target.code or ""),
            "process": process,
            "context": context,
            "description": description,
            "version": version,
        }

    def _begin_item_checkin(self, node, save_revision: bool = False) -> bool:
        target = self._checkin_target_for_node(node)
        return self._prepare_checkin_target(target, save_revision)

    def _prepare_checkin_target(
        self, target: dict | None, save_revision: bool = False,
    ) -> bool:
        checkin = getattr(self, "_checkin_controller", None)
        drop_plate = getattr(self, "_drop_plate_controller", None)
        if not checkin or not drop_plate or not target:
            self._notify("The selected item cannot be prepared for check-in")
            return False
        checkin.prepare_workspace_target(
            search_key=target["searchKey"],
            source=target["source"],
            project_code=target["projectCode"],
            title=target["title"],
            code=target["code"],
            process=target["process"],
            context=target["context"],
            description=target["description"],
            save_revision=save_revision,
            snapshot_version=target["version"] if save_revision else None,
            checkin_type=target.get("checkinType", ""),
            transfer_mode=target.get("transferMode", ""),
        )
        return True

    def _finish_table_checkin(self, source) -> None:
        pending = dict(
            getattr(self, "_pending_table_checkin", {}) or {}
        )
        if not pending or source is None:
            return
        try:
            search_key = str(source.get_search_key() or "")
        except AttributeError:
            return
        if search_key != pending.get("targetSearchKey"):
            return
        self._pending_table_checkin = {}
        try:
            code = str(source.get_code() or "")
            title = str(source.get_title() or code or "sObject")
        except (AttributeError, KeyError, TypeError):
            code = ""
            title = "sObject"
        if self._prepare_checkin_target({
            "source": source,
            "searchKey": search_key,
            "projectCode": str(self._current_project_code or ""),
            "title": title,
            "code": code,
            "process": pending["process"],
            "context": pending["context"],
            "description": "",
            "version": 0,
            "checkinType": pending.get("checkinType", ""),
            "transferMode": pending.get("transferMode", ""),
        }):
            self._checkin_controller.set_process_and_context(
                pending["process"], pending["context"]
            )

    def _discard_table_checkin(self, search_key: str) -> None:
        pending = dict(
            getattr(self, "_pending_table_checkin", {}) or {}
        )
        if pending.get("targetSearchKey") == str(search_key or ""):
            self._pending_table_checkin = {}

    @Slot("QVariantList")
    def submit_checkin_files(self, values: list) -> None:
        drop_plate = getattr(self, "_drop_plate_controller", None)
        if not drop_plate:
            return
        values = list(values or [])
        if len(values) > 1:
            self._request_multi_file_checkin({
                "kind": "files",
                "values": values,
            }, len(values))
            return
        drop_plate.add_paths_and_queue(values)

    def _queue_drop_plate_or_choose_files(self) -> None:
        drop_plate = getattr(self, "_drop_plate_controller", None)
        if drop_plate and drop_plate.hasChecked:
            checked_count = int(
                getattr(drop_plate, "checkedCount", 0) or 0
            )
            if checked_count > 1:
                self._request_multi_file_checkin(
                    {"kind": "selected"}, checked_count
                )
                return
            drop_plate.add_selected_to_queue()
        else:
            self.checkinFilesRequested.emit()

    def _request_multi_file_checkin(
        self, pending: dict, file_count: int,
    ) -> None:
        self._pending_multi_file_checkin = dict(pending)
        self.multiFileCheckinModeRequested.emit(int(file_count))

    @Slot(str)
    def resolve_multi_file_checkin(self, mode: str) -> None:
        pending = dict(
            getattr(self, "_pending_multi_file_checkin", {}) or {}
        )
        self._pending_multi_file_checkin = {}
        if mode not in {"group", "individual"} or not pending:
            return
        group_checkin = mode == "group"
        drop_plate = getattr(self, "_drop_plate_controller", None)
        if drop_plate is None:
            return
        kind = str(pending.get("kind") or "")
        if kind == "files":
            drop_plate.add_paths_and_queue(
                list(pending.get("values") or []), group_checkin
            )
        elif kind == "selected":
            drop_plate.add_selected_to_queue(group_checkin)
        elif kind == "drop":
            self._queue_dropped_checkin_files(
                str(pending.get("nodeId") or ""),
                list(pending.get("paths") or []),
                str(pending.get("context") or ""),
                group_checkin,
            )

    @staticmethod
    def _file_object_from_snapshot(snapshot):
        if snapshot is None:
            return None
        try:
            grouped = snapshot.get_files_objects(group_by="type") or {}
        except (AttributeError, KeyError, TypeError):
            grouped = {}
        # Keep the original workflow's explicit preference, then accept any
        # server-defined file type.  File type labels are project data; a
        # snapshot whose primary payload is called ``file`` or something
        # custom must still be openable.
        for kind in ("main", "image"):
            files = list(grouped.get(kind) or [])
            if files:
                return files[0]
        try:
            files = list(snapshot.get_files_objects() or [])
        except (AttributeError, KeyError, TypeError):
            files = []
        for file_object in files:
            try:
                if file_object.get_type() not in {"icon", "web"}:
                    return file_object
            except (AttributeError, TypeError):
                return file_object
        if files:
            return files[0]
        return None

    @classmethod
    def _cached_sobject_file(cls, source, process: str = ""):
        """Match legacy snapshot choice using only the sObject's loaded cache."""
        processes = dict(getattr(source, "process", None) or {})
        preferred = [str(process or ""), "publish"]
        process_names = [
            name for name in dict.fromkeys([
                *preferred, *processes.keys(),
            ])
            if name and name in processes
        ]
        for process_name in process_names:
            process_object = processes[process_name]
            try:
                contexts = dict(process_object.get_contexts() or {})
            except (AttributeError, KeyError, TypeError):
                contexts = dict(getattr(process_object, "contexts", {}) or {})
            context_names = [
                name for name in dict.fromkeys([
                    process_name, *contexts.keys(),
                ])
                if name in contexts
            ]
            for context_name in context_names:
                context = contexts[context_name]
                try:
                    snapshots = (
                        context.get_versionless() or context.get_versions() or {}
                    )
                except (AttributeError, KeyError, TypeError):
                    snapshots = (
                        getattr(context, "versionless", None)
                        or getattr(context, "versions", None)
                        or {}
                    )
                for snapshot in snapshots.values():
                    file_object = cls._file_object_from_snapshot(snapshot)
                    if file_object is not None:
                        return file_object
        return None

    @Slot(bool)
    def resolve_revision_checkin(self, accepted: bool) -> None:
        node_id = str(getattr(self, "_pending_revision_checkin_node_id", ""))
        self._pending_revision_checkin_node_id = ""
        if not accepted or not node_id:
            return
        node = self._node_for_any(node_id)
        if self._begin_item_checkin(node, save_revision=True):
            self._queue_drop_plate_or_choose_files()

    def _finish_node_loading_state(self, message: str) -> None:
        if self._node_load_requests:
            next_title = next(iter(self._node_load_requests.values()))[2]
            self._set_loading(True, f"Loading item: {next_title}")
        else:
            self._set_loading(False, message)

    def _file_object_for_node(self, node_id: str):
        node = self._node_for_any(node_id)
        if not node:
            return None
        if node.node_type == "file":
            return node.source
        if node.node_type == "snapshot" and node.source:
            return self._file_object_from_snapshot(node.source)
        if node.node_type in {"sobject", "process"}:
            root = node if node.node_type == "sobject" else self.workspace_model.node_for(node.parent_id)
            if root:
                file_object = self._cached_sobject_file(
                    root.source,
                    node.process if node.node_type == "process" else "",
                )
                if file_object is not None:
                    return file_object
                stack = list(root.children)
                while stack:
                    candidate = stack.pop(0)
                    if candidate.node_type == "file" and candidate.source:
                        return candidate.source
                    if candidate.node_type == "snapshot" and candidate.source:
                        file_object = self._file_object_from_snapshot(
                            candidate.source
                        )
                        if file_object is not None:
                            return file_object
                    stack.extend(candidate.children)
        return None

    def open_file_object(self, file_object) -> None:
        """Open a repository file, downloading it first when necessary."""
        context = self._dcc_item_payload(None, file_object)
        context.update({"event": "snapshot.open", "source": "handler"})
        triggers = getattr(self, "_script_triggers", None)
        if triggers is None:
            self._open_file_object_now(file_object, context)
            return

        triggers.run_before(
            "snapshot.open",
            context,
            lambda success, _error: self._open_file_object_now(
                file_object, context
            ) if success else None,
        )

    def _open_file_object_now(self, file_object, context: dict) -> None:
        try:
            if file_object.is_exists():
                file_object.open_file()
                self._file_opened(context)
                return
            handle = self.repository_sync.schedule_file_object(
                file_object,
                process="checkout",
                auto_start=False,
                overwrite_policy="overwrite",
                is_ui_preview=False,
            )
            pending = getattr(self, "_pending_file_open_tasks", None)
            if pending is None:
                pending = set()
                self._pending_file_open_tasks = pending
            if handle.task_id in pending:
                handle.download()
                return
            pending.add(handle.task_id)
            handle.downloaded.connect(
                lambda ready_file, task_id=handle.task_id, payload=context: (
                    self._file_open_ready(task_id, ready_file, payload)
                ),
                Qt.ConnectionType.QueuedConnection,
            )
            handle.failed.connect(
                lambda failed_file, task_id=handle.task_id: (
                    self._file_open_failed(task_id, failed_file)
                ),
                Qt.ConnectionType.QueuedConnection,
            )
            handle.download()
            self._notify("Downloading the published file")
        except (
            AttributeError,
            KeyError,
            OSError,
            RuntimeError,
            TimeoutError,
            TypeError,
            ValueError,
        ) as error:
            self._notify(str(error))

    def _file_open_ready(
        self, task_id: str, file_object, context: dict,
    ) -> None:
        pending = getattr(self, "_pending_file_open_tasks", set())
        pending.discard(str(task_id or ""))
        try:
            file_object.open_file()
            self._file_opened(context)
        except (AttributeError, OSError, TypeError, ValueError) as error:
            self._notify(str(error))

    def _file_opened(self, context: dict) -> None:
        triggers = getattr(self, "_script_triggers", None)
        if triggers is not None:
            triggers.run_after("snapshot.open", context)

    def _file_open_failed(self, task_id: str, _file_object) -> None:
        pending = getattr(self, "_pending_file_open_tasks", set())
        pending.discard(str(task_id or ""))
        self._notify("The published file could not be downloaded")

    def _editor_stype_for_node(self, node):
        """Resolve editor schema from an item or its owning sObject."""
        visited = set()
        candidate = node
        while candidate and candidate.node_id not in visited:
            visited.add(candidate.node_id)
            source = candidate.source
            try:
                stype = source.get_stype() if source is not None else None
            except (AttributeError, KeyError, TypeError):
                stype = None
            if stype is not None:
                return stype
            candidate = (
                self._node_for_any(candidate.parent_id)
                if candidate.parent_id else None
            )
        return None

    def _show_process_details(
        self,
        node_id: str,
        panel: str = "",
        process_override: str = "",
    ) -> None:
        node = self.workspace_model.node_for(node_id)
        if not node:
            return
        if process_override:
            process = str(process_override)
        elif node.node_type == "sobject":
            process = "publish"
        else:
            process = str(node.process or node.context or "publish")
        mark_process_seen = getattr(
            self.workspace_model, "mark_process_seen", None
        )
        if panel in {"tasks", "notes"} and callable(mark_process_seen):
            mark_process_seen(node_id, panel, process)
        tab = self._current_tab()
        selection_changed = bool(
            tab and tab.selected_node_id != node.node_id
        )
        if selection_changed:
            self.select_result_node(
                node.node_id,
                node.search_key,
                node.node_type,
                0,
                False,
            )
        process_changed = process != self._selected_detail_process
        if process_changed:
            self._selected_detail_process = process
        if (
            panel == "tasks"
            and self._registry.invoke("show_selected_tasks_workspace")
        ):
            if process_changed and not selection_changed:
                self.workspace_state.selection_changed.emit()
            return
        if process_changed and not selection_changed:
            self.workspace_state.selection_changed.emit()
        if panel:
            self.dock_model.show_panel(panel)
        else:
            self.dock_model.show_panel("tasks")
            self.dock_model.show_panel("notes")

    @Slot(str, str, str)
    def open_process_details(
        self,
        node_id: str,
        panel: str,
        process: str,
    ) -> None:
        if panel not in {"tasks", "notes"}:
            return
        resolved_process = str(process or "publish")
        self._show_process_details(
            node_id,
            panel,
            process_override=resolved_process,
        )

    @Slot(str, str, str, str)
    def open_process_task_details(
        self,
        node_id: str,
        panel: str,
        process: str,
        task_code: str,
    ) -> None:
        if panel not in {"tasks", "notes"} or not task_code:
            return
        node = self._node_for_any(node_id)
        root_node = node
        while root_node and root_node.node_type != "sobject":
            root_node = (
                self._node_for_any(root_node.parent_id)
                if root_node.parent_id else None
            )
        if not root_node:
            return
        resolved_process = str(process or "publish")
        self._show_process_details(
            node_id,
            panel,
            process_override=resolved_process,
        )
        self.taskContextRequested.emit(
            str(task_code), str(root_node.search_key or ""), resolved_process,
        )

    def _dcc_item_payload(self, node, file_object=None) -> dict:
        root = node
        while root and root.node_type != "sobject" and root.parent_id:
            root = self._node_for_any(root.parent_id)
        target = root if root and root.node_type == "sobject" else node
        target_source = target.source if target else None
        target_info = {}
        if target_source:
            try:
                target_info = dict(target_source.get_info() or {})
            except (AttributeError, TypeError, ValueError):
                pass
        payload = {
            "project_code": str(
                getattr(self, "_current_project_code", "") or ""
            ),
            "search_key": str(target.search_key if target else ""),
            "code": str(target.code if target else ""),
            "title": str(target.title if target else ""),
            "process": str(node.process or "publish" if node else "publish"),
            "context": str(node.context or node.process or "publish" if node else "publish"),
            "node_type": str(node.node_type if node else ""),
            "target": {
                key: target_info.get(key)
                for key in ("id", "code", "name", "title", "description", "status")
                if target_info.get(key) is not None
            },
        }
        snapshot_source = (
            node.source
            if node and node.node_type == "snapshot" and node.source
            else None
        )
        if snapshot_source is None and file_object is not None:
            try:
                snapshot_source = file_object.get_snapshot()
            except AttributeError:
                pass
        if snapshot_source:
            try:
                snapshot = dict(snapshot_source.get_snapshot() or {})
            except (AttributeError, TypeError, ValueError):
                snapshot = {}
            payload["snapshot"] = {
                key: snapshot.get(key)
                for key in (
                    "code", "context", "description", "login", "process",
                    "repo", "revision", "snapshot_type", "timestamp", "version",
                )
                if snapshot.get(key) is not None
            }
            try:
                payload["snapshot"]["search_key"] = str(
                    snapshot_source.get_search_key() or ""
                )
            except AttributeError:
                pass
            if target is None:
                parent_type = str(snapshot.get("search_type") or "")
                parent_code = str(snapshot.get("search_code") or "")
                if parent_type and parent_code:
                    separator = "&" if "?" in parent_type else "?"
                    payload["search_key"] = (
                        f"{parent_type}{separator}code={parent_code}"
                    )
                    payload["code"] = parent_code
                payload["process"] = str(
                    snapshot.get("process") or payload["process"]
                )
                payload["context"] = str(
                    snapshot.get("context") or payload["context"]
                )
        if file_object:
            file_info = {}
            for key, getter in (
                ("path", "get_full_abs_path"),
                ("web_path", "get_full_web_path"),
                ("file_name", "get_filename_with_ext"),
                ("file_type", "get_type"),
            ):
                try:
                    value = getattr(file_object, getter)()
                except (AttributeError, KeyError, TypeError, ValueError):
                    continue
                if value is not None:
                    file_info[key] = str(value)
            payload["file"] = file_info
        return payload

    def _send_dcc_file_action(
        self, definition: dict, file_object, node=None, options=None
    ) -> None:
        bridge = getattr(self, "_dcc_bridge", None)
        capability = str(definition.get("capability") or "")
        if not bridge or not bridge.has_dcc_capability(capability):
            self._notify("The selected DCC client does not support this action")
            return
        try:
            if file_object.is_exists():
                payload = self._dcc_item_payload(node, file_object)
                payload.update(dict(options or {}))
                payload["path"] = file_object.get_full_abs_path()
                application_type = str(
                    getattr(bridge, "selectedApplicationType", "") or ""
                )
                event = dcc_trigger_event(
                    application_type,
                    definition.get("trigger") or f"action.{definition['id']}",
                )
                payload.update({
                    "event": event,
                    "source": "dcc",
                    "application_type": application_type,
                    "client_id": str(bridge.selectedClient or ""),
                })

                def send(success=True, _error=""):
                    if not success:
                        return
                    request_id = bridge.send_active_command(
                        capability, payload, 60.0
                    )
                    if request_id:
                        self._dcc_item_requests[request_id] = dict(payload)

                triggers = getattr(self, "_script_triggers", None)
                if triggers is None:
                    send()
                else:
                    triggers.run_before(event, payload, send)
                return
            handle = self.repository_sync.schedule_file_object(
                file_object,
                process="checkout",
                auto_start=False,
                overwrite_policy="overwrite",
            )
            handle.downloaded.connect(
                lambda ready_file, current_definition=dict(definition):
                    self._send_dcc_file_action(
                        current_definition, ready_file, node, options
                    ),
                Qt.ConnectionType.QueuedConnection,
            )
            handle.failed.connect(
                lambda _failed_file: self._notify(
                    "The published file could not be downloaded"
                ),
                Qt.ConnectionType.QueuedConnection,
            )
            handle.download()
            self._notify("Downloading the published file for the DCC client")
        except (AttributeError, KeyError, TypeError, OSError, ValueError) as error:
            self._notify(str(error))
        self._load_sobject_details(node.search_key, node.process or None)

    def request_dcc_scene_checkin(
        self, node_id: str, options: dict | None = None,
        capability: str = "prepare_checkin",
    ) -> bool:
        node = self._node_for_any(node_id)
        bridge = getattr(self, "_dcc_bridge", None)
        if not bridge or not bridge.has_dcc_capability(capability):
            self._notify("The selected DCC client cannot save its scene")
            return False
        target = self._checkin_target_for_node(node)
        if not target:
            self._notify("Select an sObject before saving a DCC scene")
            return False
        overrides = dict(options or {})
        payload = self._dcc_item_payload(node)
        payload["application_type"] = str(
            getattr(bridge, "selectedApplicationType", "") or ""
        )
        payload["generate_previews"] = bool(
            getattr(self._checkin_controller, "generatePreviews", True)
        )
        payload.update(overrides)
        started = self._checkin_controller.start_dcc_scene_checkin(
            target, payload, capability
        )
        if started:
            self._notify("DCC scene preparation started")
        else:
            self._notify(
                str(getattr(bridge, "error", "") or "")
                or "The DCC scene save could not be started"
            )
        return bool(started)

    def _send_dcc_item_action(
        self, definition: dict, node, options=None
    ) -> bool:
        bridge = getattr(self, "_dcc_bridge", None)
        capability = str(definition.get("capability") or "")
        if not bridge or not bridge.has_dcc_capability(capability):
            self._notify("The selected DCC client does not support this action")
            return False
        payload = self._dcc_item_payload(node)
        payload.update(dict(options or {}))
        application_type = str(
            getattr(bridge, "selectedApplicationType", "") or ""
        )
        event = dcc_trigger_event(
            application_type,
            definition.get("trigger") or f"action.{definition['id']}",
        )
        payload.update({
            "event": event,
            "source": "dcc",
            "application_type": application_type,
            "client_id": str(bridge.selectedClient or ""),
        })

        def send(success=True, _error=""):
            if not success:
                return
            request_id = bridge.send_active_command(
                capability, payload, 60.0
            )
            if request_id:
                self._dcc_item_requests[request_id] = dict(payload)

        triggers = getattr(self, "_script_triggers", None)
        if triggers is None:
            send()
        else:
            triggers.run_before(event, payload, send)
        return True

    @Slot(str, str, "QVariantMap", result=bool)
    def invoke_dcc_action(
        self, action_id: str, node_id: str, options=None
    ) -> bool:
        bridge = getattr(self, "_dcc_bridge", None)
        application_type = str(
            getattr(bridge, "selectedApplicationType", "") or ""
        ).lower()
        definition = dcc_item_action(application_type, action_id)
        node = self._node_for_any(node_id)
        if not definition or not node:
            self._notify("The DCC action is unavailable for this item")
            return False
        target = definition["target"]
        if target == "scene_checkin":
            return self.request_dcc_scene_checkin(
                node_id, dict(options or {}), definition["capability"]
            )
        if target == "item":
            return self._send_dcc_item_action(definition, node, options)
        file_object = self._file_object_for_node(node_id)
        if not file_object:
            self._notify("No published file is available for this item")
            return False
        self._send_dcc_file_action(definition, file_object, node, options)
        return True

    def _open_related_search(self, node_id: str, direction: str, related_code: str) -> None:
        node = self.workspace_model.node_for(node_id)
        if not node or not node.source:
            return
        source = node.source
        parent_stype = source.get_stype()
        project = parent_stype.get_project()
        related_stype = project.stypes.get(related_code)
        if not related_stype:
            self._notify(f"Related search type is unavailable: {related_code}")
            return
        if direction == "parent":
            expression = source.get_related_sobjects_tel_string(
                child_stype=parent_stype,
                parent_stype=related_stype,
                path="parent",
            )
        else:
            expression = source.get_related_sobjects_tel_string(
                child_stype=related_stype,
                parent_stype=parent_stype,
                path="child",
            )
        section = self._unfiltered_search_key_section(
            related_code,
            related_stype.get_pretty_name(),
            related_stype.get_stype_color(fmt="hex") or "",
        )
        self.activate_section(section.entry_key)
        tab = create_search_tab(
            section.entry_key,
            f"{related_stype.get_pretty_name()} related to {source.get_title()}",
            tab_kind="related",
            limit=self._page_size,
            view_mode=self._default_view_mode,
            filters=[("_expression", "in", expression)],
        )
        section.tabs.append(tab)
        section.current_tab_id = tab.tab_id
        self._sync_search_tabs()
        self._load_tab(tab)

    @Slot(str, str)
    def open_completion(self, node_id: str, related_search_type: str) -> None:
        """Open the objects counted by an sObject Completion node."""
        if not related_search_type:
            self._notify("Completion has no related Search Type")
            return
        self._open_related_search(node_id, "child", related_search_type)

    def _open_named_folder(self, node, folder_type: str) -> None:
        """Resolve versionless/version paths through TACTIC's naming engine."""
        if not node or not node.search_key:
            self._notify("No TACTIC path is available for this item")
            return
        process = node.process or "publish"

        def resolve_paths():
            import thlib.global_functions as gf
            import thlib.tactic_classes as tc
            from thlib.environment import env_tactic
            named = tc.get_dirs_with_naming(
                node.search_key,
                process_list=[process],
            )
            relative_paths = list(named.get(folder_type) or [])
            if not relative_paths:
                return ([],)
            relative_path = relative_paths[0]
            paths = []
            for _key, repository in env_tactic.get_all_base_dirs():
                info = repository.get("value") or []
                if len(info) > 4 and info[4]:
                    paths.append(gf.form_path(f"{info[0]}/{relative_path}"))
            return (paths,)

        try:
            from thlib.environment import env_inst
            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            started_at = time.perf_counter()
            self._set_loading(True, f"Resolving {folder_type} folder")
            worker = env_inst.server_pool.add_task(resolve_paths)
            worker.add_result_data((folder_type, started_at))
            worker.result.connect(self._open_named_folder_result)
            worker.error.connect(self._item_mutation_error)
            worker.start()
        except Exception as error:
            self._notify(str(error))

    @Slot(object)
    def _open_named_folder_result(self, result) -> None:
        paths, metadata = result
        folder_type, started_at = metadata
        if not paths:
            self._set_loading(False, f"No {folder_type} folder is configured")
            self._notify(f"No {folder_type} folder is configured")
            return
        try:
            import thlib.global_functions as gf
            gf.open_folder(paths[0], False)
            if len(paths) > 1:
                self._notify(
                    f"Opened the first of {len(paths)} active repositories"
                )
        except (OSError, TypeError, ValueError) as error:
            self._notify(str(error))
        self._set_loading(
            False,
            f"Folder resolved · {self._transaction_metrics(started_at, paths)}",
        )

    def _open_sobject_on_new_tab(self, source) -> None:
        stype = source.get_stype()
        code = str(source.get_code() or "")
        search_type = str(stype.get_code() or "") if stype else ""
        if not code or not search_type:
            return
        current_section = self._current_section()
        current_tab = self._current_tab()
        self._capture_current_tree_state()
        self._capture_current_workspace_layout()
        section = self._unfiltered_search_key_section(
            search_type,
            str(stype.get_pretty_name() or search_type),
            str(stype.get_stype_color(fmt="hex") or ""),
        )
        tab = create_search_tab(
            section.entry_key,
            str(source.get_title() or code),
            tab_kind="user",
            limit=self._page_size,
            view_mode=self._default_view_mode,
            filters=[("code", "=", code)],
        )
        if current_tab is not None:
            tab.workspace_layout = deepcopy(current_tab.workspace_layout)
        section.tabs.append(tab)
        section.current_tab_id = tab.tab_id
        if section is current_section:
            self._sync_search_tabs()
        else:
            self.activate_section(section.entry_key)
        self.section_state_changed.emit()
        if not tab.loading:
            self._load_tab(tab)

    @Slot(str, str)
    def invoke_item_action(self, command: str, node_id: str) -> None:
        if self.debug_log:
            node_for_log = self._node_for_any(node_id)
            self.debug_log.log(
                "LOG",
                f"Item action: {command}",
                group="ui/item_action",
                source="ApplicationController",
                details=str(
                    node_for_log.search_key if node_for_log else node_id
                ),
                caller=2,
            )
        if command.startswith("related:"):
            _prefix, direction, related_code = command.split(":", 2)
            self._open_related_search(node_id, direction, related_code)
            return
        node = self._node_for_any(node_id)
        source = node.source if node else None
        if command == "sobject_info":
            if not node or node.node_type != "sobject" or source is None:
                self._notify("SObject Info is unavailable for this item")
                return
            tab = self._current_tab()
            if tab and tab.selected_node_id != node.node_id:
                self.select_result_node(
                    node.node_id,
                    node.search_key,
                    node.node_type,
                    0,
                    False,
                )
            elif not tab:
                self.select_sobject(node.search_key)
            self.open_window("sobject_info")
            return
        if command.startswith("dcc_options:"):
            action_id = command.partition(":")[2]
            dcc_options = getattr(self, "dcc_options", None)
            if (
                dcc_options is None
                or node is None
                or not dcc_options.prepare_target(
                    action_id, node_id, str(node.title or node.code or "")
                )
            ):
                self._notify("DCC action options are unavailable")
                return
            self.open_window("dcc_options")
            return
        if command.startswith("dcc:"):
            self.invoke_dcc_action(command.partition(":")[2], node_id, {})
            return
        if command.startswith(("repo_sync_preset:", "repo_sync_update:")):
            preset_name = command.partition(":")[2]
            tab = self._current_tab()
            tab_name = str(tab.title if tab else "default")
            presets = self.repository_sync.presets(source)
            preset_index = next((
                index for index, preset in enumerate(presets)
                if str(preset.get("preset_name") or "") == preset_name
            ), 0)
            self.repository_sync.store_selected_preset(
                source, tab_name, preset_index, preset_name,
            )
            self.select_sobject(node.search_key if node else "")
            self.window_model.show_window("repository_sync")
            mode = "updates" if command.startswith("repo_sync_update:") else "preset"
            self.repository_sync.start_sobject_sync(
                source,
                preset_name,
                mode == "updates",
                auto_close_on_success=True,
            )
            self._notify(f"Repository Sync: {preset_name} ({mode})")
            return
        if command == "copy_skey":
            search_key = self.workspace_model.search_key_for(node_id)
            try:
                search_key = source.get_search_key() if source else search_key
            except AttributeError:
                pass
            if search_key:
                QGuiApplication.clipboard().setText(
                    search_key if search_key.startswith("skey://") else f"skey://{search_key}"
                )
                self._notify("Search key copied")
            return
        file_object = self._file_object_for_node(node_id)
        if command in {"copy_path", "copy_web_path", "copy_absolute"} and file_object:
            getter = "get_full_web_path" if command == "copy_web_path" else "get_full_abs_path"
            try:
                QGuiApplication.clipboard().setText(str(getattr(file_object, getter)()))
                self._notify("Path copied")
            except (AttributeError, KeyError, TypeError) as error:
                self._notify(str(error))
            return
        if command == "copy_image" and file_object:
            try:
                image = QImage(str(file_object.get_full_abs_path()))
                if not image.isNull():
                    QGuiApplication.clipboard().setImage(image)
                    self._notify("Image copied")
                else:
                    self._notify("The selected file is not an image")
            except (AttributeError, KeyError, TypeError) as error:
                self._notify(str(error))
            return
        if command in {"folder_versionless", "folder_versions"}:
            if node and node.node_type == "snapshot" and file_object:
                try:
                    file_object.open_folder()
                except (AttributeError, KeyError, TypeError, OSError) as error:
                    self._notify(str(error))
            else:
                self._open_named_folder(
                    node,
                    "versionless" if command == "folder_versionless" else "versions",
                )
            return
        if command in {"open", "folder"}:
            if not file_object:
                self._notify("No published file is available for this item")
                return
            try:
                if command == "open":
                    self.open_file_object(file_object)
                else:
                    file_object.open_folder()
            except (AttributeError, KeyError, TypeError, OSError) as error:
                self._notify(str(error))
            return
        if command in {"tasks", "notes"}:
            self._show_process_details(node_id, command)
            return
        if command == "process_notes":
            self._show_process_details(node_id)
            return
        if command == "repo_sync":
            context = self._repository_sync_context_for_node(node)
            if context.get("sobject") is None:
                self._notify("The selected item cannot be synchronized")
                return
            self._open_repository_sync_editor(context)
            return
        if command == "knowledge_article":
            knowledge = getattr(self, "knowledge", None)
            if (
                not node
                or node.node_type != "sobject"
                or knowledge is None
                or not knowledge.open_for_object(node.search_key)
            ):
                self._notify("The linked Knowledge Base article is unavailable")
            return
        if command == "open_watch_folder" and node:
            try:
                import thlib.global_functions as gf
                from thlib.environment import env_inst, env_tactic
                from ..workspace_models.watch_folders import (
                    _watch_folder_record,
                )
                try:
                    project = source.get_project() if source else None
                except AttributeError:
                    project = None
                if not project:
                    project = (env_inst.projects or {}).get(
                        self._current_project_code
                    )
                watch = _watch_folder_record(project, node.search_key)
                repository_codes = set(watch.get("rep") or [])
                for _key, repository in env_tactic.get_all_base_dirs():
                    info = repository.get("value") or []
                    if (
                        len(info) > 4
                        and info[4]
                        and info[3] in repository_codes
                    ):
                        path = gf.form_path(f"{info[0]}/{watch.get('path') or ''}")
                        gf.open_folder(path, False)
                        return
                self._notify("No active repository is configured for this watch folder")
            except (AttributeError, KeyError, TypeError, OSError) as error:
                self._notify(str(error))
            return
        if command in {"watch_folder", "create_watch", "edit_watch", "delete_watch"}:
            if not node:
                self._notify("Select an sObject before managing a watch folder")
                return
            self.select_sobject(node.search_key)
            watch_folders = getattr(self, "watch_folders", None)
            if not watch_folders:
                self._notify("Watch Folders are unavailable")
                return
            if command == "create_watch":
                watch_folders.begin_add_for_source(node.source, "item")
            elif command == "edit_watch" or (
                command == "watch_folder"
                and node.watch_state != "none"
            ):
                watch_folders.begin_edit_search_key(
                    node.search_key, "item"
                )
            elif command == "watch_folder":
                watch_folders.begin_add_for_source(node.source, "item")
            elif command == "delete_watch":
                watch_folders.request_remove_search_key(
                    node.search_key, "item"
                )
            return
        if command in {"add_related", "link_related"}:
            self.select_sobject(node.search_key if node else "")
            if command == "add_related" and node:
                relation = node.relation or {}
                self._sobject_editor_request = {
                    "mode": "insert",
                    "stype": relation.get("stype"),
                    "parent_sobject": node.source,
                    "relation": dict(
                        relation.get("definition") or {}
                    ),
                    "_prepared": True,
                }
            elif command == "link_related" and node:
                relation = node.relation or {}
                definition = dict(relation.get("definition") or {})
                relationship = str(
                    definition.get("relationship")
                    or node.relationship
                    or ""
                )
                if (
                    node.node_type != "relation"
                    or relationship != "instance"
                    or relation.get("stype") is None
                    or node.source is None
                ):
                    self._sobject_link_request = {}
                    self._notify(
                        "Link SObjects is available for instance relations only"
                    )
                    return
                self._sobject_link_request = {
                    "stype": relation.get("stype"),
                    "parent_sobject": node.source,
                    "relation": definition,
                    "_prepared": True,
                }
            self.open_window("link_sobjects" if command == "link_related" else "add_sobject")
            return
        if command == "new_tab":
            if node and node.node_type == "sobject" and source:
                self._open_sobject_on_new_tab(source)
            return
        if command in {"save", "save_revision", "paste"}:
            if (
                command == "save_revision"
                and self._checkin_flag("askReplaceRevisionCheckBox", True)
            ):
                self._pending_revision_checkin_node_id = node_id
                self.revisionCheckinConfirmationRequested.emit()
                return
            if not self._begin_item_checkin(
                node, save_revision=command == "save_revision"
            ):
                return
            if command == "paste":
                clipboard = QGuiApplication.clipboard()
                mime_data = clipboard.mimeData()
                urls = list(mime_data.urls()) if mime_data and mime_data.hasUrls() else []
                if not urls and mime_data and mime_data.hasText():
                    urls = [
                        QUrl.fromLocalFile(line.strip())
                        for line in mime_data.text().splitlines()
                        if line.strip()
                    ]
                if urls:
                    self.submit_checkin_files(urls)
                else:
                    self._notify("The clipboard does not contain file paths")
                return
            self._queue_drop_plate_or_choose_files()
            return
        if command == "preview":
            if self._begin_item_checkin(node):
                self._checkin_controller.set_process("icon")
                self._checkin_controller.set_context("icon")
                self.dock_model.show_panel("drop_plate")
                self._queue_drop_plate_or_choose_files()
            return
        if command == "unlink":
            if not node or not source:
                return
            relation_node = self.workspace_model.node_for(node.parent_id)
            relation = (relation_node.relation or {}).get("definition") if relation_node else None
            instance_type = (relation or {}).get("instance_type")
            parent = relation_node.source if relation_node else None
            if not instance_type or not parent:
                self._notify("Selected item is not an instance relation")
                return
            import thlib.tactic_classes as tc
            schema = source.get_stype().get_schema()
            parent_relation = schema.get_parent_instance(
                instance_type,
                source.get_stype().get_code(),
            )

            def unlink_sobject():
                return tc.edit_multiple_instance_sobjects(
                    self._current_project_code,
                    exclude_search_keys=[source.get_search_key()],
                    parent_key=parent.get_search_key(),
                    instance_type=instance_type,
                    path=(parent_relation or {}).get("path"),
                )

            try:
                self._start_item_mutation(
                    "Unlinking sObject",
                    unlink_sobject,
                    ("unlink", source.get_search_key(), ""),
                    self._item_mutation_result,
                )
            except Exception as error:
                self._notify(str(error))
            return
        if command == "edit" and node and source is not None:
            stype = self._editor_stype_for_node(node)
            if stype is not None:
                self._sobject_editor_request = {
                    "mode": "edit",
                    "stype": stype,
                    "sobject": source,
                    "parent_sobject": None,
                    "_prepared": True,
                }
                self.open_window("add_sobject")
            else:
                self._notify("The current search type is unavailable")
            return
        if command in {"db", "db_selected"}:
            self.dock_model.show_panel("db_table")
            return
        if command in {"delete", "delete_tree", "delete_selected"}:
            selected_ids = (
                list(self._current_tab().selected_node_ids)
                if command == "delete_selected" and self._current_tab()
                else [node_id]
            )
            selected_sources = [
                selected.source
                for selected_id in selected_ids
                if (
                    (selected := self.workspace_model.node_for(selected_id))
                    and selected.source
                )
            ]
            delete_controller = getattr(self, "sobject_delete", None)
            if delete_controller is None:
                self._notify("Delete SObject editor is unavailable")
                return
            delete_controller.begin(selected_sources, "items")
            return
        if command in {"duplicate", "duplicate_quick"}:
            if not node or node.node_type != "sobject" or source is None:
                self._notify("Select an sObject to duplicate")
                return
            duplicate_controller = getattr(
                self, "sobject_duplicate", None
            )
            if duplicate_controller is None:
                self._notify("Duplicate sObject editor is unavailable")
                return
            if command == "duplicate_quick":
                duplicate_controller.quick_duplicate(source)
            else:
                duplicate_controller.begin(source)
        elif command == "link":
            self._notify(
                "Open Link SObjects from an instance relation"
            )
        elif command == "ingest":
            ingest = getattr(self, "_ingest_controller", None)
            if node.node_type != "relation" or ingest is None:
                self._notify("Select a child relation before ingesting files")
                return
            ingest.open_for_relation(node_id)
        elif command == "save":
            self.window_model.show_window("commit_queue")
        else:
            self._notify(f"Item action: {command}")

    @Slot(str, str, "QVariantMap")
    def invoke_table_widget_action(
        self, kind: str, node_id: str, values: dict,
    ) -> None:
        node = self._node_for_any(node_id)
        if not node:
            return
        values = dict(values or {})
        target_key = str(values.get("targetSearchKey") or node.search_key)
        if kind == "sobject_detail":
            if target_key == node.search_key:
                self.invoke_item_action("sobject_info", node_id)
            else:
                self.select_sobject(target_key)
                self.open_window("sobject_info")
            return
        if kind in {"file_list", "metadata"}:
            if target_key != node.search_key:
                self.select_sobject(target_key)
                self.open_window("sobject_info")
            else:
                self.invoke_item_action("sobject_info", node_id)
            return
        if kind == "delete":
            if values.get("available") is not False:
                self.invoke_item_action("delete", node_id)
            return
        if kind == "explorer":
            path = str(values.get("path") or "")
            if not path:
                self._notify("No TACTIC path is available for this item")
                return
            try:
                import thlib.global_functions as gf
                gf.open_folder(path, False)
            except (OSError, TypeError, ValueError) as error:
                self._notify(str(error))
            return
        if kind != "checkin":
            return
        if values.get("available") is False:
            self._notify("The configured check-in target is unavailable")
            return
        process = str(values.get("process") or "publish")
        context = str(values.get("context") or process)
        checkin_type = str(values.get("checkinMode") or "")
        transfer_mode = str(values.get("transferMode") or "")
        if target_key != node.search_key:
            self._pending_table_checkin = {
                "targetSearchKey": target_key,
                "process": process,
                "context": context,
                "checkinType": checkin_type,
                "transferMode": transfer_mode,
            }
            self.select_sobject(target_key)
            self.dock_model.show_panel("drop_plate")
            return
        target = self._checkin_target_for_node(node)
        if target:
            target["process"] = process
            target["context"] = context
            target["checkinType"] = checkin_type
            target["transferMode"] = transfer_mode
        if not self._prepare_checkin_target(target):
            return
        self._checkin_controller.set_process_and_context(process, context)
        self.dock_model.show_panel("drop_plate")

    @Slot(str, "QVariantList", str)
    def queue_dropped_files(self, node_id: str, urls: list, context: str) -> None:
        node = self.workspace_model.node_for(node_id)
        if not node:
            return
        process = node.process if node.node_type == "process" else context
        paths = self._local_drop_paths(urls)
        if not paths:
            return
        if node.node_type == "relation":
            ingest = getattr(self, "_ingest_controller", None)
            if ingest is None:
                self._notify("File ingest is unavailable")
                return
            ingest.quick_ingest(node_id, paths)
            return
        if process == "icon" and not self._paths_can_drop_as_icon(paths):
            self._notify(
                "Object icons accept TACTIC preview images only: "
                "JPEG, PNG, or TIFF"
            )
            return
        if len(paths) > 1:
            self._request_multi_file_checkin({
                "kind": "drop",
                "nodeId": node_id,
                "paths": paths,
                "context": context,
            }, len(paths))
            return
        self._queue_dropped_checkin_files(
            node_id, paths, context, False
        )

    def _queue_dropped_checkin_files(
        self, node_id: str, paths: list[str], context: str,
        group_checkin: bool,
    ) -> None:
        node = self.workspace_model.node_for(node_id)
        if not node or node.node_type == "relation" or not paths:
            return
        process = node.process if node.node_type == "process" else context
        if not self._begin_item_checkin(node):
            return
        checkin = getattr(self, "_checkin_controller", None)
        if checkin and process:
            checkin.set_process_and_context(process, context or process)
        self.window_model.show_window("commit_queue")
        if group_checkin:
            self._drop_plate_controller.add_dropped_paths(
                paths,
                icon_target=process == "icon",
                group_checkin=True,
            )
        else:
            self._drop_plate_controller.add_dropped_paths(
                paths, icon_target=process == "icon"
            )
        self._notify(
            f"Preparing {len(paths)} file(s) for {process or 'publish'}"
        )

    @staticmethod
    def _local_drop_paths(urls: list) -> list[str]:
        paths = []
        for value in urls or []:
            url = value if isinstance(value, QUrl) else QUrl(str(value))
            path = url.toLocalFile()
            if not path and not url.scheme():
                path = str(value)
            if path:
                paths.append(path)
        return paths

    @staticmethod
    def _paths_can_drop_as_icon(paths: list[str]) -> bool:
        import thlib.global_functions as gf

        if not paths:
            return False
        for path in paths:
            extension = PurePath(str(path)).suffix.lstrip(".")
            file_format = gf.file_format(extension)
            if len(file_format) < 4 or file_format[3] != "preview":
                return False
        return True

    @Slot("QVariantList", result=bool)
    def can_drop_as_icon(self, urls: list) -> bool:
        """Return whether every dragged file is a TACTIC preview image."""
        return self._paths_can_drop_as_icon(self._local_drop_paths(urls))


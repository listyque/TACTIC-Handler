"""Application controller: item operations."""

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

class ItemOperationsMixin:
    def attach_checkin_workflow(self, checkin_controller, drop_plate_controller) -> None:
        self._checkin_controller = checkin_controller
        self._drop_plate_controller = drop_plate_controller

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
        checkin = getattr(self, "_checkin_controller", None)
        drop_plate = getattr(self, "_drop_plate_controller", None)
        target = self._checkin_target_for_node(node)
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
            snapshot_version=target["version"],
        )
        return True

    @Slot("QVariantList")
    def submit_checkin_files(self, values: list) -> None:
        drop_plate = getattr(self, "_drop_plate_controller", None)
        if not drop_plate:
            return
        drop_plate.add_paths_and_queue(values)

    def _queue_drop_plate_or_choose_files(self) -> None:
        drop_plate = getattr(self, "_drop_plate_controller", None)
        if drop_plate and drop_plate.hasChecked:
            drop_plate.add_selected_to_queue()
        else:
            self.checkinFilesRequested.emit()

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
            try:
                grouped = node.source.get_files_objects(group_by="type") or {}
                for kind in ("main", "maya", "image", "playblast", "icon", "web"):
                    if grouped.get(kind):
                        return grouped[kind][0]
            except (AttributeError, KeyError, TypeError):
                return None
        if node.node_type in {"sobject", "process"}:
            root = node if node.node_type == "sobject" else self.workspace_model.node_for(node.parent_id)
            if root:
                stack = list(root.children)
                while stack:
                    candidate = stack.pop(0)
                    if candidate.node_type == "file" and candidate.source:
                        return candidate.source
                    if candidate.node_type == "snapshot" and candidate.source:
                        try:
                            grouped = candidate.source.get_files_objects(group_by="type") or {}
                            for kind in ("main", "maya", "image", "playblast", "icon", "web"):
                                if grouped.get(kind):
                                    return grouped[kind][0]
                        except (AttributeError, KeyError, TypeError):
                            pass
                    stack.extend(candidate.children)
        return None

    def _show_process_details(self, node_id: str, panel: str = "") -> None:
        node = self.workspace_model.node_for(node_id)
        if not node:
            return
        process = (
            "publish" if node.node_type == "sobject"
            else str(node.process or node.context or "publish")
        )
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
        if process != self._selected_detail_process:
            self._selected_detail_process = process
            if not selection_changed:
                self.workspace_state.selection_changed.emit()
        if panel:
            self.dock_model.show_panel(panel)
        else:
            self.dock_model.show_panel("tasks")
            self.dock_model.show_panel("notes")

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
            "project_code": str(self._current_project_code or ""),
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
        if node and node.node_type == "snapshot" and node.source:
            try:
                snapshot = dict(node.source.get_snapshot() or {})
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

    def _send_dcc_file_action(self, action: str, file_object, node=None) -> None:
        bridge = getattr(self, "_dcc_bridge", None)
        if not bridge or not bridge.has_dcc_capability(action):
            self._notify("The selected DCC client does not support this action")
            return
        try:
            if file_object.is_exists():
                payload = self._dcc_item_payload(node, file_object)
                request_id = bridge.send_dcc_action(
                    action, file_object.get_full_abs_path(), payload
                )
                if request_id:
                    self._dcc_item_requests.add(request_id)
                return
            handle = self.repository_sync.schedule_file_object(
                file_object,
                process="checkout",
                auto_start=False,
                overwrite_policy="overwrite",
            )
            handle.downloaded.connect(
                lambda ready_file, current_action=action:
                    self._send_dcc_file_action(current_action, ready_file, node),
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
        section_key = (
            self.navigation_model.key_for_search_type(related_code)
            or f"{related_code}@direct"
        )
        section = self._create_section(
            section_key,
            related_stype.get_pretty_name(),
            related_stype.get_stype_color(fmt="hex") or "",
        )
        self.activate_section(section.entry_key)
        tab = SearchTabSession(
            tab_id=f"{section.entry_key}:search:{uuid.uuid4().hex[:8]}",
            title=f"{related_stype.get_pretty_name()} related to {source.get_title()}",
            extra_filters=[("_expression", "in", expression)],
            limit=self._page_size,
            view_mode=self._default_view_mode,
        )
        section.tabs.append(tab)
        section.current_tab_id = tab.tab_id
        self._sync_search_tabs()
        self._load_tab(tab)

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
        if command == "dcc_save_scene":
            bridge = getattr(self, "_dcc_bridge", None)
            capability = (
                "prepare_checkin"
                if bridge and bridge.has_dcc_capability("prepare_checkin")
                else "save_current_scene"
            )
            if not bridge or not bridge.has_dcc_capability(capability):
                self._notify("The selected DCC client cannot save its scene")
                return
            target = self._checkin_target_for_node(node)
            if not target:
                self._notify("Select an sObject before saving a DCC scene")
                return
            payload = self._dcc_item_payload(node)
            payload["generate_previews"] = bool(
                getattr(self._checkin_controller, "generatePreviews", True)
            )
            request_id = bridge.send_active_command(
                capability, payload, 120.0,
            )
            if request_id:
                self._dcc_checkin_requests[request_id] = {
                    **target,
                    "saveRevision": False,
                }
                self._notify("DCC scene preparation started")
            return
        if command.startswith(("repo_sync_preset:", "repo_sync_update:")):
            preset_name = command.partition(":")[2]
            self.select_sobject(node.search_key if node else "")
            self.window_model.show_window("repository_sync")
            mode = "updates" if command.startswith("repo_sync_update:") else "preset"
            self.repository_sync.start_sobject_sync(
                source,
                preset_name,
                mode == "updates",
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
        if command in {"dcc_open", "dcc_import", "dcc_reference"}:
            if not file_object:
                self._notify("No published file is available for this item")
                return
            self._send_dcc_file_action(
                command.removeprefix("dcc_"), file_object, node
            )
            return
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
                    file_object.open_file()
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
            self.select_sobject(node.search_key if node else "")
            self.window_model.show_window("repository_sync")
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
            self.select_sobject(node.search_key if node else "")
            self.dock_model.show_panel("watch_folders")
            return
        if command in {"add_related", "link_related"}:
            self.select_sobject(node.search_key if node else "")
            if command == "add_related" and node:
                relation = node.relation or {}
                self._sobject_editor_request = {
                    "mode": "insert",
                    "stype": relation.get("stype"),
                    "parent_sobject": node.source,
                    "_prepared": True,
                }
            elif command == "link_related" and node:
                relation = node.relation or {}
                self._sobject_link_request = {
                    "stype": relation.get("stype"),
                    "parent_sobject": node.source,
                    "relation": relation.get("definition") or {},
                    "_prepared": True,
                }
            self.open_window("link_sobjects" if command == "link_related" else "add_sobject")
            return
        if command == "new_tab" and source:
            try:
                self._search_by_key(f"skey://{source.get_search_key()}")
            except AttributeError:
                pass
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
            try:
                stype = source.get_stype()
            except (AttributeError, KeyError, TypeError):
                stype = None
            if stype is not None:
                self._sobject_editor_request = {
                    "mode": "edit",
                    "stype": stype,
                    "sobject": source,
                    "parent_sobject": None,
                }
                self.window_model.show_window("add_sobject")
            return
        window_map = {
            "duplicate": "duplicate_sobject",
            "link": "link_sobjects",
        }
        if command in {"db", "db_selected"}:
            self.dock_model.show_panel("db_table")
            return
        if command in {"delete", "delete_tree", "delete_selected"}:
            self._pending_item_node_id = node_id
            self._pending_item_action = command
            self.open_window("delete_sobject")
            return
        if command in window_map:
            if command == "duplicate":
                self._pending_item_node_id = node_id
                self._pending_item_action = command
            self.open_window(window_map[command])
        elif command == "ingest":
            self.dock_model.show_panel("drop_plate")
        elif command == "save":
            self.window_model.show_window("commit_queue")
        else:
            self._notify(f"Item action: {command}")

    @Slot(str, "QVariantList", str)
    def queue_dropped_files(self, node_id: str, urls: list, context: str) -> None:
        node = self.workspace_model.node_for(node_id)
        if not node:
            return
        process = node.process if node.node_type == "process" else context
        paths = []
        for value in urls or []:
            url = value if isinstance(value, QUrl) else QUrl(str(value))
            path = url.toLocalFile()
            if path:
                paths.append(path)
        if not paths:
            return
        if not self._begin_item_checkin(node):
            return
        checkin = getattr(self, "_checkin_controller", None)
        if checkin and process:
            checkin.set_process_and_context(process, context or process)
        self.window_model.show_window("commit_queue")
        self._drop_plate_controller.add_dropped_paths(
            paths, icon_target=process == "icon"
        )
        self._notify(
            f"Preparing {len(paths)} file(s) for {process or 'publish'}"
        )

    @Slot(str)
    def confirm_item_action(self, window_id: str) -> None:
        if window_id not in {"delete_sobject", "duplicate_sobject"} or not self._pending_item_node_id:
            self._notify("This operation is not connected yet")
            return
        node = self.workspace_model.node_for(self._pending_item_node_id)
        if not node or not node.source:
            self._notify("Selected item is no longer available")
            return
        try:
            import thlib.tactic_classes as tc
            from thlib.environment import env_inst
            project_code = self._current_project_code
            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            action = self._pending_item_action
            selected_ids = (
                list(self._current_tab().selected_node_ids)
                if action == "delete_selected" and self._current_tab()
                else [node.node_id]
            )
            selected_sources = [
                selected.source
                for selected_id in selected_ids
                if (
                    (selected := self.workspace_model.node_for(selected_id))
                    and selected.source
                )
            ]

            def mutate_selected():
                if action == "duplicate":
                    return (tc.duplicate_sobjects(
                        [node.source.get_search_key()],
                        {"new_name": None, "related_search_type": []},
                    ),)
                sources = list(selected_sources)
                if action == "delete_tree":
                    sources.extend(
                        child.source for child in node.children
                        if child.node_type == "snapshot" and child.source
                    )
                server = tc.server_start(project=project_code)
                return ([
                    server.delete_sobject(
                        source.get_search_key(),
                        include_dependencies=False,
                    )
                    for source in sources
                ],)

            worker = env_inst.server_pool.add_task(mutate_selected)
            worker.add_result_data((window_id, action))
            worker.result.connect(self._mutation_result)
            worker.error.connect(self._mutation_error)
            self._set_loading(
                True,
                "Duplicating item" if action == "duplicate" else "Deleting item(s)",
            )
            worker.start()
        except Exception as error:
            self._notify(str(error))

    @Slot(object)
    def _mutation_result(self, result) -> None:
        _server_result, metadata = result
        window_id, action = metadata
        self.window_model.close_window(window_id)
        self._pending_item_node_id = ""
        self._pending_item_action = ""
        self._notify("sObject duplicated" if action == "duplicate" else "Item deleted")
        self._set_loading(
            False,
            "sObject duplicated" if action == "duplicate" else "Item(s) deleted",
        )
        self.refresh_current()

    @Slot(object)
    def _mutation_error(self, error) -> None:
        payload, worker = error
        self._report_error_payload(payload, "items/mutation", worker)
        message = str(payload.get("exception") or error)
        self._pending_item_node_id = ""
        self._pending_item_action = ""
        self._set_loading(False, f"Item mutation failed · {message}")
        self._notify(message)

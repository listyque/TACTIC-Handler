"""Application controller: item actions."""

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

class ItemActionsMixin:
    def attach_dcc_bridge(self, bridge) -> None:
        previous = getattr(self, "_dcc_bridge", None)
        if previous:
            try:
                previous.commandFinished.disconnect(
                    self._dcc_item_command_finished
                )
            except (RuntimeError, TypeError):
                pass
        self._dcc_bridge = bridge
        self._dcc_item_requests = set()
        self._dcc_checkin_requests = {}
        if bridge:
            bridge.commandFinished.connect(self._dcc_item_command_finished)

    def _dcc_available(self, action: str) -> bool:
        bridge = getattr(self, "_dcc_bridge", None)
        return bool(bridge and bridge.has_dcc_capability(action))

    @Slot(str, bool, "QVariantMap", str)
    def _dcc_item_command_finished(
        self, request_id: str, success: bool, payload: dict, error: str
    ) -> None:
        requests = getattr(self, "_dcc_item_requests", set())
        checkin_request = getattr(
            self, "_dcc_checkin_requests", {}
        ).pop(request_id, None)
        if checkin_request is not None:
            if not success:
                self._notify(error or "DCC scene preparation failed")
                return
            if payload.get("cancelled") or payload.get("success") is False:
                self._notify(
                    str(payload.get("message") or "DCC scene preparation cancelled")
                )
                return
            paths = []
            for record in [
                *(payload.get("files") or []),
                *(payload.get("previews") or []),
            ]:
                path = (
                    record.get("path") if isinstance(record, dict)
                    else record
                )
                if path:
                    paths.append(str(path))
            if not paths and payload.get("path"):
                paths.append(str(payload["path"]))
            try:
                self._checkin_controller.prepare_external_checkin(
                    search_key=checkin_request["searchKey"],
                    source=checkin_request["source"],
                    project_code=checkin_request["projectCode"],
                    title=checkin_request["title"],
                    code=checkin_request["code"],
                    context=checkin_request["context"],
                    description=checkin_request["description"],
                    paths=paths,
                    save_revision=checkin_request["saveRevision"],
                    snapshot_version=checkin_request["version"],
                    queue_when_ready=True,
                )
                self._notify("DCC scene prepared for Commit Queue")
            except (OSError, TypeError, ValueError) as exception:
                self._notify(str(exception))
            return
        if request_id not in requests:
            return
        requests.discard(request_id)
        if success:
            path = str(payload.get("opened_path") or payload.get("path") or "")
            self._notify(path or "DCC action completed")
        else:
            self._notify(error or "DCC action failed")

    @Slot(str, result="QVariantList")
    def item_menu_actions(self, node_id: str) -> list[dict]:
        node = self._node_for_any(node_id)
        if not node:
            return []

        def item(title: str, icon: str, command: str) -> dict:
            return {"title": title, "icon": icon, "command": command}

        separator = {"separator": True}
        tab = self._current_tab()
        selected_ids = list(tab.selected_node_ids) if tab else []
        if (
            node.node_type in {"sobject", "snapshot"}
            and node_id in selected_ids
            and len(selected_ids) > 1
        ):
            return [
                item(
                    f"Edit {len(selected_ids)} Selected in DB Editor",
                    "table_edit",
                    "db_selected",
                ),
                separator,
                item(
                    f"Delete All Selected ({len(selected_ids)})",
                    "delete",
                    "delete_selected",
                ),
            ]
        if node.node_type == "file":
            return [
                item("Open File", "folder_open", "open"),
                item("Show Folder", "folder", "folder"),
                separator,
                item("Copy File Path", "content_copy", "copy_path"),
                item("Copy Web Link", "link", "copy_web_path"),
                item("Copy To Clipboard", "content_copy", "copy_image"),
            ]
        if node.node_type == "snapshot":
            if not node.source:
                return [
                    item("Save snapshot", "save", "save"),
                    separator,
                    item("Show Folder", "folder", "folder_versionless"),
                    item("Show Folder Versions", "folder_open", "folder_versions"),
                ]
            actions = []
            if not node.is_multiple and self._dcc_available("open"):
                actions.append(item("Open scene", "deployed_code", "dcc_open"))
            else:
                actions.append(item(
                    "Open snapshot" if not node.is_multiple else "Open snapshot folder",
                    "folder_open",
                    "open" if not node.is_multiple else "folder",
                ))
            if self._dcc_available("prepare_checkin") or self._dcc_available("save_current_scene"):
                actions.append(item("Save scene", "save", "dcc_save_scene"))
            if not node.is_multiple and self._dcc_available("import"):
                actions.append(item("Import", "input", "dcc_import"))
            if not node.is_multiple and self._dcc_available("reference"):
                actions.append(item("Create Reference", "link", "dcc_reference"))
            actions.extend([
                item("Save snapshot", "save", "save"),
                separator,
                item("Save from Clipboard", "content_paste", "paste"),
                item("Add revision (override current file)", "history", "save_revision"),
                separator,
                item("Show Folder", "folder", "folder"),
                item("Copy Search Key", "content_copy", "copy_skey"),
                item("Edit Info", "edit", "edit"),
                separator,
                item("Delete", "delete", "delete"),
            ])
            if node.is_versionless:
                actions.append(item("Delete Whole Tree", "delete_forever", "delete_tree"))
            return actions
        if node.node_type == "process":
            actions = []
            if self._dcc_available("prepare_checkin") or self._dcc_available("save_current_scene"):
                actions.append(item("Save scene", "save", "dcc_save_scene"))
            actions.extend([
                item("Save snapshot", "save", "save"),
                item("Save from Clipboard", "content_paste", "paste"),
                separator,
                item("Show Folder", "folder", "folder_versionless"),
                item("Show Folder Versions", "folder_open", "folder_versions"),
                separator,
                item("Edit DB Table", "edit", "db"),
            ])
            if node.watch_state != "none":
                actions.insert(3, item("Show Watch folder", "visibility", "open_watch_folder"))
            return actions
        if node.node_type == "relation":
            return [
                item("Ingest Files", "upload", "ingest"),
                item("Add new Related sObject", "add_circle", "add_related"),
                *(
                    [item("Link sObjects Interface", "link", "link_related")]
                    if node.relationship == "instance" else []
                ),
            ]

        # Context-menu construction runs in the GUI thread and must only read
        # the already prepared workspace model. Calling an SObject here
        # can unexpectedly touch the server/cache and stall a right click.
        has_snapshot = bool(
            node.preview_url
            or any(
                child.node_type in {"process", "snapshot"}
                for child in node.children
            )
        )
        actions = []
        if has_snapshot:
            if self._dcc_available("open"):
                actions.append(item("Open scene", "deployed_code", "dcc_open"))
            else:
                actions.append(item("Open snapshot", "folder_open", "open"))
        if self._dcc_available("prepare_checkin") or self._dcc_available("save_current_scene"):
            actions.append(item("Save scene", "save", "dcc_save_scene"))
        actions.extend([
            item("Save snapshot", "save", "save"),
            separator,
            item("Duplicate", "control_point_duplicate", "duplicate"),
            item("Change Preview", "image", "preview"),
            item("Save from Clipboard", "content_paste", "paste"),
        ])
        if has_snapshot:
            actions.extend([
                separator,
                item("Add revision (override current file)", "history", "save_revision"),
            ])
        actions.extend([
            separator,
            item("Show Folder", "folder", "folder_versionless"),
            item("Show Folder Versions", "folder_open", "folder_versions"),
            separator,
        ])
        if node.watch_state == "none":
            actions.append(item("Create Watch Folder", "visibility", "create_watch"))
        else:
            actions.extend([
                item("Show Watch folder", "folder_open", "open_watch_folder"),
                item("Edit Watch Folder", "edit", "edit_watch"),
                item("Delete Watch Folder", "visibility_off", "delete_watch"),
            ])
        actions.extend([
            separator,
            item("Copy Search Key", "content_copy", "copy_skey"),
            item("Open On New Tab", "tab", "new_tab"),
            item("Edit Info", "edit", "edit"),
        ])
        if node.relationship == "instance":
            actions.extend([separator, item("Unlink", "link_off", "unlink")])
        actions.extend([separator, item("Delete", "delete", "delete")])
        return actions

    @Slot(str, result="QVariantMap")
    def item_drag_payload(self, node_id: str) -> dict:
        """Mirror Ui_itemWidget/Ui_snapshotItemWidget mouseMoveEvent MIME."""
        node = self._node_for_any(node_id)
        if not node:
            return {}
        if node.node_type == "sobject":
            payload = {"text/plain": node.title or node.code}
            if node.search_key:
                payload["application/x-tactic-search-key"] = (
                    node.search_key
                )
            return payload
        file_object = self._file_object_for_node(node_id)
        if not file_object:
            return {"text/plain": node.title or node.file_path}
        payload = {}
        try:
            web_path = str(file_object.get_full_web_path() or "")
            if web_path:
                payload["text/plain"] = web_path
        except (AttributeError, KeyError, TypeError):
            pass
        try:
            local_path = str(file_object.get_full_abs_path() or "")
            if local_path:
                payload["text/uri-list"] = [
                    QUrl.fromLocalFile(local_path)
                ]
                payload.setdefault("text/plain", local_path)
        except (AttributeError, KeyError, TypeError):
            pass
        return payload

    @staticmethod
    def _checkin_flag(name: str, default: bool = False) -> bool:
        try:
            import thlib.global_functions as gf
            from thlib.environment import cfg_controls
            for config in (
                cfg_controls.get_checkin_out(),
                cfg_controls.get_checkin(),
            ):
                value = gf.get_value_from_config(config, name)
                if value not in (None, ""):
                    return bool(int(value))
        except (AttributeError, KeyError, TypeError, ValueError):
            pass
        return default

    @Slot(str, int, result=bool)
    def handle_item_double_click(
        self,
        node_id: str,
        modifiers: int,
    ) -> bool:
        """Apply the configured item double-click action."""
        node = self._node_for_any(node_id)
        if not node:
            return False
        shift = bool(
            modifiers & Qt.KeyboardModifier.ShiftModifier.value
        )
        if (
            shift
            and node.node_type == "snapshot"
            and self._checkin_flag("doubleClickOpenCheckBox")
        ):
            self.invoke_item_action("open", node_id)
            return True
        if (
            node.node_type in {"sobject", "process", "snapshot"}
            and self._checkin_flag("doubleClickSaveCheckBox")
        ):
            self.invoke_item_action("save", node_id)
            return True
        return False

    @Slot(str, result="QVariantList")
    def relation_menu_actions(self, node_id: str) -> list[dict]:
        node = self.workspace_model.node_for(node_id)
        if not node or node.node_type != "sobject" or not node.source:
            return []
        stype = node.source.get_stype()
        schema = stype.get_schema() if stype else None
        project = stype.get_project() if stype else None
        actions = []
        for relation in (getattr(schema, "parents", None) or []):
            if relation.get("type") == "many_to_many" or relation.get("relationship") == "instance":
                continue
            code = relation.get("to")
            related_stype = project.stypes.get(code) if project else None
            title = related_stype.get_pretty_name() if related_stype else code
            actions.append({"title": title, "icon": "arrow_upward", "command": f"related:parent:{code}"})
        children = getattr(schema, "children", None) or []
        if children and actions:
            actions.append({"separator": True})
        for relation in children:
            if relation.get("type") == "many_to_many":
                continue
            code = relation.get("from")
            related_stype = project.stypes.get(code) if project else None
            title = related_stype.get_pretty_name() if related_stype else code
            actions.append({"title": title, "icon": "arrow_downward", "command": f"related:child:{code}"})
        return actions

    @Slot(str, result="QVariantList")
    def repo_sync_menu_actions(self, node_id: str) -> list[dict]:
        """Build Ui_itemWidget.show_sync_menu from the live server presets."""
        node = self.workspace_model.node_for(node_id)
        if not node or node.node_type != "sobject" or not node.source:
            return []
        actions = [{
            "title": "Open Repo Sync",
            "icon": "cloud_sync",
            "command": "repo_sync",
        }]
        try:
            presets = self.repository_sync.presets(node.source)
        except Exception as error:
            self._notify(str(error))
            return actions
        if not presets:
            return actions
        current = presets[0]
        actions.extend([
            {"header": True, "title": "Current preset:"},
            {
                "title": current.get("pretty_preset_name") or "Default",
                "icon": "download",
                "command": f"repo_sync_preset:{current.get('preset_name') or 'default'}",
                "secondaryCommand": (
                    f"repo_sync_update:{current.get('preset_name') or 'default'}"
                    if node.needs_sync else ""
                ),
            },
        ])
        remaining = presets[1:]
        if remaining:
            actions.append({"header": True, "title": "Other presets:"})
        for preset in remaining:
            preset_name = str(preset.get("preset_name") or "default")
            actions.append({
                "title": preset.get("pretty_preset_name") or preset_name.replace("_", " ").title(),
                "icon": "download",
                "command": f"repo_sync_preset:{preset_name}",
                "secondaryCommand": f"repo_sync_update:{preset_name}" if node.needs_sync else "",
            })
        return actions

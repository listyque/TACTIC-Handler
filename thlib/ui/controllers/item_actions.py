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
    Qt,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtGui import QGuiApplication, QImage

from tactic_handler_dcc.connectors import dcc_item_actions

from ..menu_schema import MenuRegistry
from ..quick_filters import QuickFilterCatalog
from ..repository_sync import RepositorySyncController
from ..sidebar_icons import icon_name_from_tactic
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
    @staticmethod
    def _node_has_snapshot(node) -> bool:
        if node.node_type == "snapshot":
            return node.source is not None
        if node.node_type != "sobject" or node.source is None:
            return False
        try:
            return bool(node.source.get_all_processes())
        except (AttributeError, TypeError):
            return bool(getattr(node.source, "process", None))

    @staticmethod
    def _task_assignee_record(login: str) -> dict:
        if not login:
            return {}
        try:
            from thlib.environment import env_inst
            user = (env_inst.get_all_logins() or {}).get(login)
            if not user:
                return {}
            info = dict(user.get_info() or {})
            display_name = str(user.get_display_name() or login)
            initials = "".join(
                part[:1] for part in display_name.split()[:2]
            ).upper()
            return {
                "displayName": display_name,
                "avatarUrl": str(info.get("avatar") or ""),
                "avatarColor": str(info.get("color") or ""),
                "initials": initials or login[:2].upper(),
            }
        except (AttributeError, TypeError, ValueError):
            return {}

    def _task_picker_actions(
        self, source, process: str, panel: str, accent: str = "",
    ) -> list[dict]:
        try:
            records = list(source.get_task_summaries(process) or ())
        except (AttributeError, TypeError, ValueError):
            records = []
        records.sort(key=lambda record: (
            0 if not record.get("context")
            or str(record.get("context")) == process else 1,
            str(record.get("timestamp") or ""),
            str(record.get("code") or ""),
        ))
        actions = []
        for index, record in enumerate(records):
            task_code = str(record.get("code") or "")
            if not task_code:
                continue
            assigned = str(
                record.get("assigned") or record.get("login") or ""
            )
            user = self._task_assignee_record(assigned)
            assigned_label = str(
                user.get("displayName") or assigned or "Not assigned"
            )
            status = str(record.get("status") or "")
            context = str(record.get("context") or process)
            primary = bool(
                record.get("__primary_note_branch__", index == 0)
            )
            action = {
                "title": context,
                "translate": False,
                "status": " · ".join(
                    value for value in (assigned_label, status) if value
                ),
                "statusTranslate": False,
                "icon": "task",
                "accent": str(accent or ""),
                "compactAccent": True,
                "command": "task:" + task_code,
                "process": process,
                "taskCode": task_code,
                "primaryBranch": primary,
                "avatarUrl": str(user.get("avatarUrl") or ""),
                "avatarColor": str(user.get("avatarColor") or accent or ""),
                "initials": str(user.get("initials") or assigned[:2]).upper(),
            }
            if panel == "notes":
                action["badgeCount"] = int(
                    record.get("__notes_count__") or 0
                )
                action["showZeroBadge"] = True
            actions.append(action)
        return actions

    def attach_dcc_bridge(self, bridge) -> None:
        previous = getattr(self, "_dcc_bridge", None)
        if previous:
            try:
                previous.commandFinished.disconnect(
                    self._dcc_item_command_finished
                )
                previous.stateChanged.disconnect(self.dcc_state_changed.emit)
            except (RuntimeError, TypeError):
                pass
        self._dcc_bridge = bridge
        self._dcc_item_requests = {}
        if bridge:
            bridge.commandFinished.connect(self._dcc_item_command_finished)
            bridge.stateChanged.connect(self.dcc_state_changed.emit)
        self.dcc_state_changed.emit()

    def attach_script_triggers(self, triggers) -> None:
        self._script_triggers = triggers
        self._selected_update_triggers = {}

    def _dcc_available(self, action: str) -> bool:
        bridge = getattr(self, "_dcc_bridge", None)
        return bool(bridge and bridge.has_dcc_capability(action))

    def _dcc_actions_for_node(self, node) -> list[dict]:
        bridge = getattr(self, "_dcc_bridge", None)
        application_type = str(
            getattr(bridge, "selectedApplicationType", "") or ""
        ).lower()
        if not application_type or application_type == "standalone":
            return []
        has_snapshot = bool(
            node.node_type == "file" and node.source is not None
        ) or self._node_has_snapshot(node)
        actions = []
        for definition in dcc_item_actions(application_type):
            if (
                node.node_type not in definition["scopes"]
                or not self._dcc_available(definition["capability"])
                or definition.get("requires_snapshot") and not has_snapshot
                or not definition.get("allow_multiple", True)
                and bool(getattr(node, "is_multiple", False))
            ):
                continue
            action = {
                "title": definition["title"],
                "icon": definition["icon"],
                "command": f"dcc:{definition['id']}",
                "dccActionId": definition["id"],
                "replaces": str(definition.get("replaces") or ""),
                "quick": bool(definition.get("quick")),
                "quickOrder": int(definition.get("quick_order", 100)),
                "advanced": bool(definition.get("advanced")),
            }
            if definition.get("options"):
                action.update({
                    "secondaryCommand": f"dcc_options:{definition['id']}",
                    "secondaryIcon": "edit",
                    "secondaryToolTip": f"{definition['title']} options",
                })
            actions.append(action)
        return actions

    @Slot(str, bool, "QVariantMap", str)
    def _dcc_item_command_finished(
        self, request_id: str, success: bool, payload: dict, error: str
    ) -> None:
        requests = getattr(self, "_dcc_item_requests", {})
        context = requests.pop(request_id, None)
        if context is None:
            return
        if success:
            path = str(payload.get("opened_path") or payload.get("path") or "")
            self._notify(path or "DCC action completed")
            triggers = getattr(self, "_script_triggers", None)
            if triggers is not None and context.get("event"):
                triggers.run_after(str(context["event"]), context)
        else:
            self._notify(error or "DCC action failed")

    @Slot(str, result="QVariantList")
    def item_menu_actions(self, node_id: str) -> list[dict]:
        node = self._node_for_any(node_id)
        if not node:
            return []

        def item(title: str, icon: str, command: str, *, advanced=False) -> dict:
            return {
                "title": title, "icon": icon, "command": command,
                "advanced": advanced,
            }

        separator = {"separator": True}
        tab = self._current_tab()
        selected_ids = list(tab.selected_node_ids) if tab else []
        if (
            node.node_type in {"sobject", "snapshot"}
            and node_id in selected_ids
            and len(selected_ids) > 1
        ):
            actions = [
                item(
                    "Edit %1 Selected in DB Editor",
                    "table_edit",
                    "db_selected",
                ) | {"titleArgs": [len(selected_ids)]},
                separator,
                item(
                    "Delete All Selected (%1)",
                    "delete",
                    "delete_selected",
                ) | {"titleArgs": [len(selected_ids)]},
            ]
            if node.node_type == "sobject":
                actions[0:0] = [
                    item("SObject Info", "info", "sobject_info"),
                    separator,
                ]
            return actions
        if node.node_type == "file":
            dcc_actions = self._dcc_actions_for_node(node)
            return [
                *dcc_actions,
                *([separator] if dcc_actions else []),
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
            actions = self._dcc_actions_for_node(node)
            if not any(action.get("replaces") == "open" for action in actions):
                actions.append(item(
                    "Open snapshot" if not node.is_multiple else "Open snapshot folder",
                    "folder_open",
                    "open" if not node.is_multiple else "folder",
                ))
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
            actions = self._dcc_actions_for_node(node)
            actions.extend([
                item("Save snapshot", "save", "save"),
                item("Save from Clipboard", "content_paste", "paste"),
                separator,
                item("Show Folder", "folder", "folder_versionless"),
                item("Show Folder Versions", "folder_open", "folder_versions"),
            ])
            if node.watch_state != "none":
                actions.insert(3, item("Show Watch folder", "visibility", "open_watch_folder"))
            return actions
        if node.node_type == "relation":
            return [
                *self._dcc_actions_for_node(node),
                item("Add files", "upload", "ingest"),
                item("Add new Related sObject", "add_circle", "add_related"),
                *(
                    [item("Link sObjects Interface", "link", "link_related")]
                    if node.linkable_relation else []
                ),
            ]

        # get_all_processes() reads the snapshot cache populated by search.
        # A preview or an empty pipeline process is not an openable snapshot.
        has_snapshot = self._node_has_snapshot(node)
        actions = self._dcc_actions_for_node(node)
        if (
            has_snapshot
            and not any(action.get("replaces") == "open" for action in actions)
        ):
            actions.append(item("Open snapshot", "folder_open", "open"))
        actions.extend([
            item("Save snapshot", "save", "save"),
            separator,
            item("Duplicate…", "control_point_duplicate", "duplicate", advanced=True),
            item("Change Preview", "image", "preview", advanced=True),
            item("Save from Clipboard", "content_paste", "paste"),
        ])
        duplicate_controller = getattr(self, "sobject_duplicate", None)
        if (
            duplicate_controller is not None
            and duplicate_controller.has_profile_for_source(node.source)
        ):
            duplicate_row = next(
                index for index, action in enumerate(actions)
                if action.get("command") == "duplicate"
            )
            actions.insert(
                duplicate_row + 1,
                item(
                    "Quick duplicate with last settings",
                    "content-copy",
                    "duplicate_quick",
                    advanced=True,
                ),
            )
        if has_snapshot:
            actions.extend([
                separator,
                item("Add revision (override current file)", "history", "save_revision", advanced=True),
            ])
        actions.extend([
            separator,
            item("Show Folder", "folder", "folder_versionless"),
            item("Show Folder Versions", "folder_open", "folder_versions", advanced=True),
            separator,
        ])
        if node.watch_state == "none":
            actions.append(item("Create Watch Folder", "visibility", "create_watch", advanced=True))
        else:
            actions.extend([
                item("Show Watch folder", "folder_open", "open_watch_folder", advanced=True),
                item("Edit Watch Folder", "edit", "edit_watch", advanced=True),
                item("Delete Watch Folder", "delete", "delete_watch", advanced=True),
            ])
        actions.extend([
            separator,
            item("Copy Search Key", "content_copy", "copy_skey", advanced=True),
            item("Open On New Tab", "tab", "new_tab", advanced=True),
            item("SObject Info", "info", "sobject_info", advanced=True),
            item("Edit Info", "edit", "edit"),
        ])
        if node.relationship == "instance":
            actions.extend([separator, item("Unlink", "link_off", "unlink")])
        actions.extend([separator, item(
            "Delete", "delete", "delete", advanced=node.relationship == "instance",
        )])
        return actions

    @Slot(str, result="QVariantList")
    def item_quick_actions(self, node_id: str) -> list[dict]:
        actions = self.item_menu_actions(node_id)
        quick = [dict(action) for action in actions if action.get("quick")]
        replaced = {action.get("replaces") for action in quick}
        by_command = {
            action.get("command"): action for action in actions
            if action.get("command")
        }
        for command, order in (("save", 10), ("open", 20)):
            if command not in replaced and command in by_command:
                quick.append({**by_command[command], "quickOrder": order})
        return sorted(quick, key=lambda action: action.get("quickOrder", 100))

    @Slot(str, str, result="QVariantList")
    def process_count_actions(
        self,
        node_id: str,
        panel: str,
    ) -> list[dict]:
        """Build the compact process picker for aggregate task/note badges."""
        if panel not in {"tasks", "notes"}:
            return []
        node = self._node_for_any(node_id)
        if not node:
            return []
        root_node = node
        while root_node and root_node.node_type != "sobject":
            root_node = (
                self._node_for_any(root_node.parent_id)
                if root_node.parent_id else None
            )
        if not root_node:
            return []
        source = root_node.source
        selected_process = ""
        if node.node_type != "sobject":
            selected_process = str(
                node.process or node.context or "publish"
            )
            task_actions = self._task_picker_actions(
                source, selected_process, panel, node.accent or root_node.accent,
            )
            if task_actions:
                return task_actions
        getter_name = (
            "get_notes_count" if panel == "notes" else "get_tasks_count"
        )
        try:
            raw_counts = dict(getattr(source, getter_name)() or {})
        except (AttributeError, TypeError, ValueError):
            raw_counts = {}
        counts = {}
        for process, count in raw_counts.items():
            process_name = str(process or "")
            if not process_name or process_name.startswith("__"):
                continue
            try:
                counts[process_name] = int(count or 0)
            except (TypeError, ValueError):
                counts[process_name] = 0

        pipeline = None
        pipeline_names = []
        try:
            stype = source.get_stype()
            pipelines = stype.get_pipeline() or {}
            pipeline = pipelines.get(source.get_pipeline_code())
            pipeline_names = list(
                pipeline.get_all_pipeline_names() or ()
            ) if pipeline else []
        except (AttributeError, KeyError, TypeError):
            pass

        updated_processes = (
            node.updated_comment_processes
            if panel == "notes" else node.updated_task_processes
        )
        ordered_processes = list(dict.fromkeys((
            "publish",
            *(str(value) for value in pipeline_names if value),
            *counts,
            *updated_processes,
        )))
        actions = []
        for process in ordered_processes:
            count = int(counts.get(process) or 0)
            updated = process in updated_processes
            if process != "publish" and count <= 0 and not updated:
                continue
            info = {}
            process_object = {}
            label = ""
            if pipeline is not None:
                try:
                    info = dict(pipeline.get_process_info(process) or {})
                except (AttributeError, TypeError, ValueError):
                    pass
                try:
                    process_object = dict(
                        pipeline.get_pipeline_process(process) or {}
                    )
                except (AttributeError, TypeError, ValueError):
                    pass
                try:
                    label = str(
                        pipeline.get_process_label(process) or ""
                    )
                except (AttributeError, TypeError, ValueError):
                    pass
            actions.append({
                "title": label or str(info.get("label") or process),
                "translate": False,
                "accent": str(
                    info.get("color")
                    or process_object.get("color") or root_node.accent
                ),
                "compactAccent": True,
                "command": process,
                "badgeCount": count,
                "showZeroBadge": process == "publish",
                "badgeUpdated": updated,
                "process": process,
                "taskCode": "",
            })
            task_actions = self._task_picker_actions(
                source, process, panel, actions[-1]["accent"],
            )
            if len(task_actions) > 1:
                actions[-1].update({
                    "secondaryCommand": "tasks:" + process,
                    "secondaryIcon": "chevron-right",
                    "secondaryToolTip": "Choose task",
                    "secondaryKeepOpen": True,
                })
        if selected_process:
            return [
                action for action in actions
                if str(action.get("process") or "") == selected_process
            ]
        return actions

    @Slot(str, str, str, result="QVariantList")
    def process_task_actions(
        self, node_id: str, panel: str, process: str,
    ) -> list[dict]:
        if panel not in {"tasks", "notes"}:
            return []
        node = self._node_for_any(node_id)
        root_node = node
        while root_node and root_node.node_type != "sobject":
            root_node = (
                self._node_for_any(root_node.parent_id)
                if root_node.parent_id else None
            )
        if not root_node:
            return []
        return self._task_picker_actions(
            root_node.source, str(process or "publish"), panel,
            node.accent or root_node.accent,
        )

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

        def relation_action(related_stype, code, direction):
            title = str(code or "")
            accent = ""
            icon = "sobject"
            if related_stype is not None:
                try:
                    title = str(
                        related_stype.get_pretty_name() or title
                    )
                except (AttributeError, KeyError, TypeError):
                    pass
                try:
                    accent = str(
                        related_stype.get_stype_color(fmt="hex") or ""
                    )
                except (AttributeError, KeyError, TypeError):
                    pass
                try:
                    info = related_stype.get_info() or {}
                    icon = icon_name_from_tactic(
                        info.get("icon")
                    ) or icon
                except (AttributeError, TypeError):
                    pass
            return {
                "title": title,
                "translate": False,
                "icon": icon,
                "accent": accent,
                "accentIcon": True,
                "command": f"related:{direction}:{code}",
            }

        actions = []
        for relation in (getattr(schema, "parents", None) or []):
            if (
                relation.get("type") == "many_to_many"
                or relation.get("relationship") == "instance"
            ):
                continue
            code = relation.get("to")
            related_stype = project.stypes.get(code) if project else None
            actions.append(relation_action(
                related_stype, code, "parent"
            ))
        children = getattr(schema, "children", None) or []
        if children and actions:
            actions.append({"separator": True})
        for relation in children:
            if relation.get("type") == "many_to_many":
                continue
            code = relation.get("from")
            related_stype = project.stypes.get(code) if project else None
            actions.append(relation_action(
                related_stype, code, "child"
            ))
        return actions

    @Slot(str, result="QVariantList")
    def repo_sync_menu_actions(self, node_id: str) -> list[dict]:
        """Build Ui_itemWidget.show_sync_menu from the live server presets."""
        node = self.workspace_model.node_for(node_id)
        if not node or node.node_type != "sobject" or not node.source:
            return []
        actions = [{
            "title": "Open Repo Sync",
            "icon": "repository-sync",
            "command": "repo_sync",
        }]
        self.repository_sync.request_presets(node.source)
        try:
            presets = self.repository_sync.presets(node.source)
        except Exception as error:
            self._notify(str(error))
            return actions
        if not presets:
            return actions
        tab = self._current_tab()
        tab_name = str(tab.title if tab else "default")
        selected_name = self.repository_sync.selected_preset_name(
            node.source, tab_name,
        )
        selected = next((
            index for index, preset in enumerate(presets)
            if str(preset.get("preset_name") or "") == selected_name
        ), self.repository_sync.selected_preset_index(node.source, tab_name))
        if 0 < selected < len(presets):
            presets = [
                presets[selected], *presets[:selected],
                *presets[selected + 1:],
            ]
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

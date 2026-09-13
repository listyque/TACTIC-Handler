"""Application controller: commands."""

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
    QCoreApplication,
    QDateTime,
    QObject,
    Property,
    Qt,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtGui import QGuiApplication, QImage

from tactic_handler_dcc.connectors import dcc_manifest_for, dcc_tool_actions

from ..menu_schema import MenuRegistry
from ..quick_filters import QuickFilterCatalog
from ..theme_catalog import (
    normalize_icon_set,
    normalize_theme_accents,
    normalize_theme_style,
)
from ..repository_sync import RepositorySyncController
from ..rendering import normalize_render_backend
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

class CommandsMixin:
    def attach_workspace_layout_presets(self, controller) -> None:
        """Attach the project-scoped preset owner after core composition."""
        self._workspace_layout_presets = controller

    @Slot(result=bool)
    def is_dark_theme(self) -> bool:
        return self._dark_theme

    @Slot()
    def toggle_theme(self) -> None:
        self.set_dark_theme(not self._dark_theme)

    @Slot(bool)
    def set_dark_theme(self, enabled: bool) -> None:
        if self._dark_theme == enabled:
            return
        self._dark_theme = enabled
        self._settings["appearance/darkTheme"] = enabled
        self._write_settings()
        self.dark_theme_changed.emit(enabled)
        self.accent_changed.emit()

    @Slot(str)
    def set_theme_style(self, style: str) -> None:
        style = normalize_theme_style(style)
        if self._theme_style == style:
            return
        self._theme_style = style
        self._settings["appearance/themeStyle"] = style
        self._write_settings()
        self.theme_style_changed.emit(style)
        self.accent_changed.emit()

    @Slot("QVariantMap")
    def set_theme_accents(self, values) -> None:
        normalized = normalize_theme_accents(values)
        if self._theme_accents == normalized:
            return
        self._theme_accents = normalized
        self._settings["appearance/themeAccents"] = {
            style: dict(modes)
            for style, modes in normalized.items()
        }
        self._write_settings()
        self.accent_changed.emit()

    @Slot(str)
    def set_icon_set(self, value: str) -> None:
        value = normalize_icon_set(value)
        if self._icon_set == value:
            return
        self._icon_set = value
        self._settings["appearance/iconSet"] = value
        self._write_settings()
        self.icon_set_changed.emit(value)

    def configuration_global_values(self) -> dict:
        from thlib.environment import configured_thread_counts, env_mode

        thread_counts = configured_thread_counts()

        return {
            "closeToTray": self.close_to_tray_enabled(),
            "serverThreads": thread_counts["server"],
            "localThreads": thread_counts["local"],
            "debugLogLevels": list(
                getattr(self.debug_log, "recording_levels", [
                    "ERROR", "CRITICAL",
                ])
            ),
            "configPath": str(env_mode.get_current_path() or ""),
        }

    def configuration_appearance_values(self) -> dict:
        return {
            "darkTheme": self._dark_theme,
            "themeStyle": self._theme_style,
            "themeAccents": {
                style: dict(modes)
                for style, modes in self._theme_accents.items()
            },
            "iconSet": self._icon_set,
            "clickAnimations": self._click_animations_enabled,
            "hoverAnimations": self._hover_animations_enabled,
            "fadeAnimations": self._fade_animations_enabled,
            "popupAnimations": self._popup_animations_enabled,
            "renderBackend": normalize_render_backend(
                self._settings.get(
                    "appearance/renderBackend", "automatic"
                )
            ),
        }

    def apply_global_configuration(self, values: dict) -> None:
        from thlib.environment import env_inst

        self._settings["application/closeToTray"] = bool(
            values.get("closeToTray", True)
        )
        server_threads = max(
            1, min(32, int(values.get("serverThreads", 4) or 4))
        )
        local_threads = max(
            1, min(32, int(values.get("localThreads", 4) or 4))
        )
        self._settings["performance/serverThreads"] = server_threads
        self._settings["performance/localThreads"] = local_threads
        env_inst.set_thread_counts(server_threads, local_threads)
        if self.debug_log:
            self.debug_log.set_recording_levels(values.get("debugLogLevels") or [])
        self._write_settings()
        self._notify(QCoreApplication.translate(
            "TacticHandler", "Global preferences saved"
        ))

    def apply_appearance_configuration(self, values: dict) -> None:
        previous_render_backend = normalize_render_backend(
            self._settings.get("appearance/renderBackend", "automatic")
        )
        render_backend = normalize_render_backend(
            values.get("renderBackend", "automatic")
        )
        self._settings["appearance/renderBackend"] = render_backend
        click_animations = bool(values.get("clickAnimations", True))
        hover_animations = bool(values.get("hoverAnimations", True))
        fade_animations = bool(values.get("fadeAnimations", True))
        popup_animations = bool(values.get("popupAnimations", fade_animations))
        animations_changed = (
            click_animations != getattr(
                self, "_click_animations_enabled", True
            )
            or hover_animations != getattr(
                self, "_hover_animations_enabled", True
            )
            or fade_animations != getattr(
                self, "_fade_animations_enabled", True
            )
            or popup_animations != getattr(
                self, "_popup_animations_enabled", True
            )
        )
        self._click_animations_enabled = click_animations
        self._hover_animations_enabled = hover_animations
        self._fade_animations_enabled = fade_animations
        self._popup_animations_enabled = popup_animations
        self._settings["appearance/clickAnimations"] = click_animations
        self._settings["appearance/hoverAnimations"] = hover_animations
        self._settings["appearance/fadeAnimations"] = fade_animations
        self._settings["appearance/popupAnimations"] = popup_animations
        if animations_changed:
            changed = getattr(self, "animation_preferences_changed", None)
            if changed is not None:
                changed.emit()
        self.set_dark_theme(bool(values.get("darkTheme")))
        if "themeStyle" in values:
            self.set_theme_style(values.get("themeStyle"))
        if "themeAccents" in values:
            self.set_theme_accents(values.get("themeAccents"))
        if "iconSet" in values:
            self.set_icon_set(values.get("iconSet"))
        self._write_settings()
        if render_backend != previous_render_backend:
            self._notify(
                QCoreApplication.translate(
                    "TacticHandler",
                    "Graphics backend saved. Restart TACTIC Handler to apply it.",
                )
            )
        else:
            self._notify(QCoreApplication.translate(
                "TacticHandler", "Appearance preferences saved"
            ))

    def configuration_workspace_cache_values(self) -> dict:
        return {"cacheProcessTabs": self._search_cache_enabled()}

    def apply_workspace_cache_configuration(self, values: dict) -> None:
        cache_enabled = bool(values.get("cacheProcessTabs", True))
        self._settings["workspace/cacheProcessTabs"] = cache_enabled
        if not cache_enabled:
            self.flush_search_cache()
        self._write_settings()

    def close_to_tray_enabled(self) -> bool:
        return bool(self._settings.get("application/closeToTray", True))

    def flush_search_cache(self) -> None:
        self._search_cache.clear()
        self._write_search_cache_config()

    @Slot(str, str, str)
    def select_navigation(self, key: str, title: str, command: str) -> None:
        if command == "open_configuration":
            self.invoke(command)
            return
        if command == "open_sidebar_item":
            entry = self.navigation_model.entry(key)
            if (
                not entry or not entry.available
                or entry.entry_type != "link" or not entry.search_type
            ):
                self._notify(self.tr(
                    "This sidebar item has no Search Type. Configure it in Sidebar Editor."
                ))
                return
            # The section owns its dock layout. Activation captures the
            # outgoing workspace before applying this entry's retained layout
            # (or its assigned preset on the first opening).
            self._open_sidebar_section(
                key,
                title,
                entry.accent,
            )
            self.activate_section(key)
            return
        elif command.startswith("show_"):
            self._notify(f"Opened section: {title}")
        else:
            self.invoke(command)

    @Slot(str)
    def invoke(self, command: str) -> None:
        if self.debug_log:
            self.debug_log.log(
                "LOG",
                f"UI command: {command}",
                group="ui/command",
                source="ApplicationController",
                caller=2,
            )
        self.command_requested.emit(command)
        if command.startswith("dcc_tool:"):
            bridge = getattr(self, "_dcc_bridge", None)
            application_type = str(
                getattr(bridge, "selectedApplicationType", "") or ""
            ).lower()
            action_id = command.partition(":")[2]
            action = next((
                action for action in dcc_tool_actions(application_type)
                if action["id"] == action_id
            ), {})
            if (
                action
                and bridge
                and bridge.has_dcc_capability(action["capability"])
                and bridge.send_active_command(
                    action["capability"], {}, 60.0
                )
            ):
                return
            self._notify("The selected DCC tool is unavailable")
            return
        if not self._registry.invoke(command):
            self._notify(f"Command is not registered: {command}")

    @Slot(str)
    def open_window(self, window_id: str) -> None:
        if window_id == "db_table":
            self.dock_model.show_panel("db_table")
            return
        if self.debug_log:
            self.debug_log.log(
                "LOG",
                f"Open window: {window_id}",
                group="ui/window",
                source="ApplicationController",
                caller=2,
            )
        if window_id == "process_filter_editor":
            requested = getattr(self, "processFilterEditorRequested", None)
            if requested is not None:
                requested.emit()
        if window_id in {"add_sobject", "task_editor"}:
            prepared = self._sobject_editor_request.pop("_prepared", False)
            if not prepared:
                self._sobject_editor_request = {
                    "mode": "insert",
                    "stype": self._active_stype(),
                    "parent_sobject": None,
                }
            requested = getattr(self, "sobjectEditorRequested", None)
            if requested is not None:
                requested.emit()
            is_visible = getattr(
                self.window_model, "is_window_visible", None
            )
            if callable(is_visible) and is_visible(window_id):
                raise_window = getattr(
                    self.window_model, "raise_window", None
                )
                if callable(raise_window):
                    raise_window(window_id)
                return
        elif window_id == "link_sobjects":
            prepared = self._sobject_link_request.pop("_prepared", False)
            relation = dict(self._sobject_link_request.get("relation") or {})
            valid_relation = (
                str(relation.get("relationship") or "") == "instance"
                and self._sobject_link_request.get("stype") is not None
                and self._sobject_link_request.get("parent_sobject") is not None
            )
            if not prepared or not valid_relation:
                self._sobject_link_request = {}
                self._notify(
                    "Open Link SObjects from an instance relation"
                )
                return  # Invalid relation context.
            requested = getattr(self, "sobjectLinkRequested", None)
            if requested is not None:
                requested.emit()
            is_visible = getattr(
                self.window_model, "is_window_visible", None
            )
            if callable(is_visible) and is_visible(window_id):
                raise_window = getattr(
                    self.window_model, "raise_window", None
                )
                if callable(raise_window):
                    raise_window(window_id)
                return  # The existing window has the new session.
        self.window_model.show_window(window_id)

    def sobject_editor_context(self) -> dict:
        request = dict(self._sobject_editor_request or {})
        stype = request.get("stype")
        if stype is None:
            stype = self._active_stype()
        if stype is None:
            return {}
        try:
            project = stype.get_project()
            project_code = project.get_code()
        except (AttributeError, KeyError, TypeError):
            return {}
        open_created = request.get("open_created") or getattr(
            self, "_search_by_key", None
        )
        request.update({
            "stype": stype,
            "project_code": project_code,
            "search_type": stype.get_code(),
            "refresh": request.get("refresh") or self.refresh_current,
        })
        if callable(open_created):
            request["open_created"] = open_created
        return request

    def sobject_link_context(self) -> dict:
        request = dict(self._sobject_link_request or {})
        stype = request.get("stype")
        parent = request.get("parent_sobject")
        relation = dict(request.get("relation") or {})
        if stype is None or parent is None:
            return {}
        try:
            project_code = stype.get_project().get_code()
        except (AttributeError, KeyError, TypeError):
            return {}
        return {
            "stype": stype,
            "parent_sobject": parent,
            "relation": relation,
            "project_code": project_code,
            "search_type": stype.get_code(),
            "refresh": self.refresh_current,
        }

    @Slot(str, result="QVariantList")
    def menu_actions(self, menu_id: str) -> list[dict]:
        actions = [
            action for action in self._menus.actions(menu_id)
            if action.get("command") != "show_administration"
            or self.can_administer
        ]
        if menu_id != "tools":
            return actions
        bridge = getattr(self, "_dcc_bridge", None)
        application_type = str(
            getattr(bridge, "selectedApplicationType", "") or ""
        ).lower()
        tools = [
            action for action in dcc_tool_actions(application_type)
            if bridge and bridge.has_dcc_capability(action["capability"])
        ]
        if not tools:
            return actions
        manifest = dcc_manifest_for(application_type)
        actions.extend((
            {"separator": True},
            {"title": manifest.get("title") or application_type.title(), "header": True},
            *(
                {
                    "title": action["title"],
                    "icon": action["icon"],
                    "command": f"dcc_tool:{action['id']}",
                }
                for action in tools
            ),
        ))
        return actions

    @Slot(bool, result="QVariantList")
    def snapshot_file_actions(self, include_editing: bool = True) -> list[dict]:
        actions = [
            {"title": "Open File", "icon": "folder_open", "command": "open"},
            {"title": "Show Folder", "icon": "folder", "command": "folder"},
            {"separator": True},
            {"title": "Copy File Path", "icon": "content_copy", "command": "copy_path"},
            {"title": "Copy Web Link", "icon": "link", "command": "copy_web_path"},
            {"title": "Copy To Clipboard", "icon": "content_copy", "command": "copy_image"},
        ]
        if include_editing:
            actions.extend([
                {"separator": True},
                {"title": "Edit Info", "icon": "edit", "command": "edit"},
                {"title": "Delete", "icon": "delete", "command": "delete"},
            ])
        return actions

    @Slot(result="QVariantList")
    def snapshot_browser_actions(self) -> list[dict]:
        """Return toolbar options with their current checked state."""
        return [
            {
                "title": "Preview and Files",
                "icon": "grid-view",
                "command": "content_both",
                "checked": self._snapshot_browser_content_mode == "both",
            },
            {
                "title": "Preview Only",
                "icon": "image",
                "command": "content_preview",
                "checked": self._snapshot_browser_content_mode == "preview",
            },
            {
                "title": "Files Only",
                "icon": "view-list",
                "command": "content_files",
                "checked": self._snapshot_browser_content_mode == "files",
            },
            {"separator": True},
            {
                "title": "Show All Files",
                "icon": "visibility",
                "command": "show_all",
                "checked": self._snapshot_browser_show_all,
            },
            {
                "title": "Show More Info",
                "icon": "info",
                "command": "show_more",
                "checked": self._snapshot_browser_show_more,
            },
            {"separator": True},
            {
                "title": "Horizontal orientation",
                "icon": "view_agenda",
                "command": "horizontal",
                "checked": self._snapshot_browser_orientation == "horizontal",
            },
            {
                "title": "Vertical orientation",
                "icon": "view_column",
                "command": "vertical",
                "checked": self._snapshot_browser_orientation == "vertical",
            },
        ]

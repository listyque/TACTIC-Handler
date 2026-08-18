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
    QDateTime,
    QObject,
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
from ..theme_catalog import normalize_theme_style
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

class CommandsMixin:
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
        self._settings.setValue("appearance/darkTheme", enabled)
        self.dark_theme_changed.emit(enabled)

    @Slot(str)
    def set_theme_style(self, style: str) -> None:
        style = normalize_theme_style(style)
        if self._theme_style == style:
            return
        self._theme_style = style
        self._settings.setValue("appearance/themeStyle", style)
        self.theme_style_changed.emit(style)

    def configuration_global_values(self) -> dict:
        from thlib.environment import env_mode

        return {
            "cacheProcessTabs": self._search_cache_enabled(),
            "darkTheme": self._dark_theme,
            "themeStyle": self._theme_style,
            "debugLogLevels": list(
                getattr(self.debug_log, "recording_levels", [
                    "ERROR", "CRITICAL",
                ])
            ),
            "configPath": str(env_mode.get_current_path() or ""),
        }

    def apply_global_configuration(self, values: dict) -> None:
        cache_enabled = bool(values.get("cacheProcessTabs"))
        self._settings.setValue(
            "workspace/cacheProcessTabs", cache_enabled
        )
        self.set_dark_theme(bool(values.get("darkTheme")))
        if "themeStyle" in values:
            self.set_theme_style(values.get("themeStyle"))
        if self.debug_log:
            self.debug_log.set_recording_levels(
                values.get("debugLogLevels") or []
            )
        if not cache_enabled:
            self.flush_search_cache()
        self._settings.sync()
        self._notify("Global preferences saved")

    def flush_search_cache(self) -> None:
        for key in self._settings.allKeys():
            if str(key).startswith("search/treeCacheV1/"):
                self._settings.remove(key)
        self._settings.sync()

    @Slot(str, str, str)
    def select_navigation(self, key: str, title: str, command: str) -> None:
        if command == "open_configuration":
            self.invoke(command)
            return
        if command == "open_sidebar_item":
            entry = next(
                (candidate for candidate in self.navigation_model._entries if candidate.key == key),
                None,
            )
            self._reset_sidebar_section(
                key,
                title,
                entry.accent if entry else "",
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
        if window_id in {"add_sobject", "task_editor"}:
            prepared = self._sobject_editor_request.pop("_prepared", False)
            if not prepared:
                self._sobject_editor_request = {
                    "mode": "insert",
                    "stype": self._active_stype(),
                    "parent_sobject": None,
                }
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
                return
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
        request.update({
            "stype": stype,
            "project_code": project_code,
            "search_type": stype.get_code(),
            "refresh": request.get("refresh") or self.refresh_current,
        })
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
        return self._menus.actions(menu_id)

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

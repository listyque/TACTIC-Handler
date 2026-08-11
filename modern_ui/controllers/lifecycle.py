"""Application controller: lifecycle."""

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

from ..menu_schema import (
    MenuRegistry,
    TEMPORARY_TOOL_DOCKS,
    TEMPORARY_TOOL_WINDOWS,
)
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

class LifecycleMixin:
    def _register_shell_commands(self) -> None:
        self._registry.register(
            "open_configuration",
            lambda: self.window_model.show_window("configuration"),
        )
        self._registry.register(
            "show_messages", lambda: self.window_model.show_window("messages")
        )
        self._registry.register(
            "show_notifications",
            lambda: self.window_model.show_window("notifications"),
        )
        self._registry.register(
            "show_activity_feed",
            lambda: self.window_model.show_window("activity_feed"),
        )
        self._registry.register("save_preferences", self._save_preferences)
        self._registry.register("reload_cache", self.bootstrap_server)
        self._registry.register(
            "apply_view_to_all_tabs",
            self._apply_view_to_all_tabs,
        )
        self._registry.register(
            "reset_workspace_layout",
            self.dock_model.reset_layout,
        )
        self._registry.register(
            "open_script_editor",
            lambda: self.window_model.show_window("script_editor"),
        )
        self._registry.register(
            "show_debug_log",
            lambda: self.window_model.show_window("debug_log"),
        )
        self._registry.register(
            "show_repository_sync",
            lambda: self.window_model.show_window("repository_sync"),
        )
        self._registry.register(
            "show_handler_server",
            lambda: self.window_model.show_window("handler_server"),
        )
        self._registry.register(
            "show_temporary_tools",
            self.temporary_tools_requested.emit,
        )
        for command, window_id in TEMPORARY_TOOL_WINDOWS.items():
            self._registry.register(
                command,
                lambda current_id=window_id: self._open_temporary_window(
                    current_id
                ),
            )
        for command, panel_id in TEMPORARY_TOOL_DOCKS.items():
            self._registry.register(
                command,
                lambda current_id=panel_id: self._open_temporary_dock(
                    current_id
                ),
            )
        self._registry.register(
            "temporary_edit_sobject",
            self._open_selected_sobject_editor,
        )
        self._registry.register("exit", QGuiApplication.quit)

    def _temporary_tool_error(self, target: str) -> None:
        stacktrace = traceback.format_exc()
        if self.debug_log:
            self.debug_log.log(
                "ERROR",
                f"Could not open temporary tool: {target}",
                group="ui/temporary-tools",
                source="ApplicationController",
                stacktrace=stacktrace,
                caller=2,
            )
        self._notify(f"Could not open {target}. See Debug Log.")

    def _open_temporary_window(self, window_id: str) -> None:
        try:
            self.open_window(window_id)
        except Exception:
            self._temporary_tool_error(window_id)

    def _open_temporary_dock(self, panel_id: str) -> None:
        try:
            self.dock_model.show_panel(panel_id)
        except Exception:
            self._temporary_tool_error(panel_id)

    def _open_selected_sobject_editor(self) -> None:
        node_id = self.selected_node_id
        if not node_id:
            self._notify("Select an sObject before opening Edit")
            return
        try:
            self.invoke_item_action("edit", node_id)
        except Exception:
            self._temporary_tool_error("edit_sobject")

    @Slot()
    def refresh_widget_state(self) -> None:
        self.bootstrap_server()

    @Slot()
    def shutdown(self) -> None:
        self._search_cache_save_timer.stop()
        self._write_search_cache()
        if self._window_state_timer.isActive():
            self._window_state_timer.stop()
            self._write_window_state()
        self._settings.sync()
        self.repository_sync.shutdown()
        try:
            from thlib.environment import env_inst
            env_inst.exit_pools()
        except (AttributeError, RuntimeError):
            pass

    def _apply_view_to_all_tabs(self) -> None:
        current = self._current_tab()
        if not current:
            return
        for section in self._sessions.values():
            for tab in section.tabs:
                tab.view_mode = current.view_mode
                tab.splitter_ratio = current.splitter_ratio
        self._save_search_cache()
        self.results_view_changed.emit()

    def _write_window_state(self) -> None:
        for name, value in self._window_state.items():
            self._settings.setValue(f"window/{name}", value)

    @Slot(float, float, float, float, int)
    def save_window_state(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        visibility: int,
    ) -> None:
        if visibility == 2:
            self._window_state.update({
                "x": round(x),
                "y": round(y),
                "width": max(760, round(width)),
                "height": max(560, round(height)),
                "maximized": False,
            })
        elif visibility == 4:
            self._window_state["maximized"] = True
        else:
            return
        self._window_state_timer.start(180)

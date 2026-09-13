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
    Qt,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtGui import QGuiApplication, QImage

from ..menu_schema import TOOL_WINDOWS
from ..quick_filters import QuickFilterCatalog
from ..repository_sync import RepositorySyncController
from ..window_geometry import (
    current_screens,
    resolve_window_state,
)
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
            self.reset_workspace_layout,
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
            "show_ui_performance",
            lambda: self.window_model.show_window("ui_performance"),
        )
        self._registry.register(
            "show_repository_sync",
            lambda: self.window_model.show_window("repository_sync"),
        )
        self._registry.register(
            "show_watch_folders",
            self._show_watch_folders,
        )
        self._registry.register(
            "show_handler_server",
            lambda: self.window_model.show_window("handler_server"),
        )
        self._registry.register(
            "show_help",
            lambda: self.window_model.open_help("overview"),
        )
        self._registry.register(
            "show_tools",
            self.tools_requested.emit,
        )
        for command, window_id in TOOL_WINDOWS.items():
            self._registry.register(
                command,
                lambda current_id=window_id: self._open_tool_window(
                    current_id
                ),
            )
        self._registry.register("exit", QGuiApplication.quit)

    @Slot()
    def reset_workspace_layout(self) -> None:
        self.dock_model.reset_layout()
        self.window_model.reset_layout()

    def _show_watch_folders(self) -> None:
        controller = getattr(self, "watch_folders", None)
        if controller is not None:
            controller.reload()
        self.window_model.show_window("watch_folders")

    def _tool_error(self, target: str) -> None:
        stacktrace = traceback.format_exc()
        if self.debug_log:
            self.debug_log.log(
                "ERROR",
                f"Could not open tool: {target}",
                group="ui/tools",
                source="ApplicationController",
                stacktrace=stacktrace,
                caller=2,
            )
        self._notify(f"Could not open {target}. See Debug Log.")

    def _open_tool_window(self, window_id: str) -> None:
        try:
            self.open_window(window_id)
        except Exception:
            self._tool_error(window_id)

    @Slot()
    def refresh_widget_state(self) -> None:
        self.bootstrap_server()

    @Slot()
    def shutdown(self) -> None:
        self._search_tab_switch_monitor.cancel()
        self._performance.shutdown()
        if self._section_state_save_timer.isActive():
            self._section_state_save_timer.stop()
            self._write_opened_sections()
        self._search_cache_save_timer.stop()
        self._write_search_cache()
        self._config_write_queue.shutdown()
        if self._window_state_timer.isActive():
            self._window_state_timer.stop()
            self._write_window_state()
        self._write_settings()
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
            self._settings[f"window/{name}"] = value

    @Slot(float, float, float, float, result="QVariantMap")
    def clamp_main_window_geometry(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
    ) -> dict:
        """Keep the native window inside a current monitor work area."""
        screens, primary_identity = current_screens()
        return resolve_window_state(
            {
                "x": round(x),
                "y": round(y),
                "width": round(width),
                "height": round(height),
                "maximized": False,
            },
            screens,
            primary_identity,
        )

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
            safe_state = self.clamp_main_window_geometry(
                x, y, width, height
            )
            safe_state["maximized"] = False
            self._window_state.update(safe_state)
        elif visibility == 4:
            self._window_state["maximized"] = True
        else:
            return
        self._window_state_timer.start(180)

"""Workspace presentation models."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path

from PySide6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    QObject,
    Property,
    QSettings,
    Qt,
    QUrl,
    Signal,
    Slot,
)

@dataclass(frozen=True, slots=True)
class FloatingWindow:
    window_id: str
    title: str
    kind: str
    x: float
    y: float
    width: float
    height: float
    visible: bool = False
    z: int = 0
    blocking: bool = False
    geometry_mode: str = "relative"

class FloatingWindowModel(QAbstractListModel):
    """Lifecycle and geometry for floating dialogs and utility windows."""

    IdRole = Qt.UserRole + 1
    TitleRole = Qt.UserRole + 2
    KindRole = Qt.UserRole + 3
    XRole = Qt.UserRole + 4
    YRole = Qt.UserRole + 5
    WidthRole = Qt.UserRole + 6
    HeightRole = Qt.UserRole + 7
    VisibleRole = Qt.UserRole + 8
    ZRole = Qt.UserRole + 9
    BlockingRole = Qt.UserRole + 10
    GeometryModeRole = Qt.UserRole + 11
    ContentSourceRole = Qt.UserRole + 12
    ContentPropertiesRole = Qt.UserRole + 13
    _settings_key = "workspace/floatingWindowsV1"

    _configuration_pages = frozenset({
        "server", "project", "checkin_preferences",
        "checkinout_preferences", "global_preferences",
        "maya_preferences",
    })
    _content_sources = {
        "configuration": "ConfigurationView.qml",
        "asset_browser": "AssetsBrowserView.qml",
        "sobject_info": "SObjectInfoView.qml",
        "filter_editor": "FilterEditorView.qml",
        "columns_editor": "ColumnsEditorView.qml",
        "naming_editor": "NamingEditorView.qml",
        "preview_editor": "FilePreparationEditor.qml",
        "attachments_editor": "FilePreparationEditor.qml",
        "server_presets": "ServerPresetsView.qml",
        "screenshot_maker": "ScreenshotMakerView.qml",
        "handler_server": "HandlerServerView.qml",
        "script_editor": "ScriptEditorView.qml",
        "debug_log": "DebugLogView.qml",
        "repository_sync": "RepositorySyncView.qml",
        "commit_queue": "CommitQueueView.qml",
        "messages": "MessagesView.qml",
        "notifications": "NotificationsView.qml",
        "activity_feed": "ActivityFeedView.qml",
        "user_profile": "UserProfileView.qml",
        "tasks_workspace": "TasksWorkspaceView.qml",
        "milestone_manager": "MilestoneManagerView.qml",
        "update": "UpdateView.qml",
        "create_update": "UpdateView.qml",
        "matching_templates": "MatchingTemplatesView.qml",
        "repository_editor": "RepositoryEditorView.qml",
        "db_table": "DatabaseBatchEditorView.qml",
        "maya_options": "MayaOptionsView.qml",
        "add_sobject": "SObjectFieldEditor.qml",
        "task_editor": "SObjectFieldEditor.qml",
        "link_sobjects": "LinkSObjectsView.qml",
        "confirm": "ConfirmationWindow.qml",
    }

    def __init__(self, settings: QSettings) -> None:
        super().__init__()
        self._settings = settings
        self._windows = self._restore() or self._defaults()
        self._z_counter = max((window.z for window in self._windows), default=0)

    @staticmethod
    def _defaults() -> list[FloatingWindow]:
        return [
            FloatingWindow("configuration", "Configuration", "configuration", .15, .10, .70, .76),
            FloatingWindow("server", "Server Settings", "server", .23, .16, .54, .62),
            FloatingWindow("project", "Project Settings", "project", .22, .15, .56, .64),
            FloatingWindow("checkin_preferences", "Check-in Options", "checkin_preferences", .19, .12, .62, .72),
            FloatingWindow("checkinout_preferences", "Check-in/Out Settings", "checkinout_preferences", .20, .14, .60, .67),
            FloatingWindow("global_preferences", "Global Settings", "global_preferences", .26, .20, .48, .48),
            FloatingWindow("maya_preferences", "Maya Scene Settings", "maya_preferences", .27, .20, .46, .45),
            FloatingWindow("asset_browser", "Assets Browser", "asset_browser", .12, .10, .72, .72),
            FloatingWindow("sobject_info", "SObject Info", "sobject_info", .24, .16, .52, .62),
            FloatingWindow("filter_editor", "Filter Presets", "filter_editor", .27, .20, .46, .48),
            FloatingWindow("columns_editor", "Columns Editor", "columns_editor", .26, .16, .48, .58),
            FloatingWindow("preview_editor", "Preview Editor", "preview_editor", .24, .14, .52, .64),
            FloatingWindow("attachments_editor", "Attachments", "attachments_editor", .24, .14, .52, .64),
            FloatingWindow("naming_editor", "Naming Editor", "naming_editor", .22, .12, .56, .68),
            FloatingWindow("server_presets", "Server Presets", "server_presets", .28, .20, .44, .50),
            FloatingWindow("screenshot_maker", "Screenshot Maker", "screenshot_maker", .18, .12, .64, .70),
            FloatingWindow("script_editor", "Script Editor", "script_editor", .14, .10, .72, .74),
            FloatingWindow("debug_log", "Debug Log", "debug_log", .18, .13, .64, .68),
            FloatingWindow("repository_sync", "Repository Sync Queue", "repository_sync", .18, .13, .64, .68),
            FloatingWindow("commit_queue", "Commit Queue", "commit_queue", .18, .13, .64, .68),
            FloatingWindow("messages", "Messages", "messages", .16, .12, .68, .70),
            FloatingWindow("notifications", "Notifications", "notifications", .22, .15, .56, .64),
            FloatingWindow("activity_feed", "Activity Feed", "activity_feed", .18, .12, .64, .70),
            FloatingWindow("user_profile", "User Profile", "user_profile", .18, .12, .64, .72),
            FloatingWindow("update", "Update", "update", .30, .24, .40, .42),
            FloatingWindow("create_update", "Create Update", "create_update", .28, .21, .44, .50),
            FloatingWindow("repository_editor", "Repository Editor", "repository_editor", .18, .12, .64, .70),
            FloatingWindow("matching_templates", "Matching Templates", "matching_templates", .28, .18, .45, .56),
            FloatingWindow("maya_open", "Maya Open Options", "maya_options", .31, .26, .38, .34),
            FloatingWindow("maya_import", "Maya Import Options", "maya_options", .31, .26, .38, .34),
            FloatingWindow("maya_reference", "Maya Reference Options", "maya_options", .31, .26, .38, .34),
            FloatingWindow("handler_server", "TACTIC Handler Server", "handler_server", .12, .08, .76, .78),
            FloatingWindow("add_sobject", "Add SObject", "add_sobject", .23, .16, .54, .64),
            FloatingWindow("task_editor", "Task Editor", "task_editor", .23, .16, .54, .64, blocking=True),
            FloatingWindow("milestone_manager", "Project Milestones", "milestone_manager", .24, .16, .52, .62),
            FloatingWindow("link_sobjects", "Link SObjects", "link_sobjects", .22, .16, .56, .64),
            FloatingWindow("delete_sobject", "Delete SObject", "confirm", .33, .30, .34, .30),
            FloatingWindow("duplicate_sobject", "Duplicate SObject", "confirm", .33, .30, .34, .30),
        ]

    def _restore(self) -> list[FloatingWindow] | None:
        raw = self._settings.value(self._settings_key, "", type=str)
        if not raw:
            return None
        try:
            restored = [FloatingWindow(**record) for record in json.loads(raw)]
        except (TypeError, ValueError, KeyError):
            return None
        restored_by_id = {window.window_id: window for window in restored}
        result = []
        for default in self._defaults():
            saved = restored_by_id.get(default.window_id)
            if saved:
                # Geometry and visibility are user state; labels and content
                # kinds belong to the current application schema.
                saved = replace(
                    saved,
                    title=default.title,
                    kind=default.kind,
                    blocking=default.blocking,
                )
            result.append(saved or default)
        return result

    def _save(self) -> None:
        self._settings.setValue(self._settings_key, json.dumps([asdict(window) for window in self._windows]))

    def roleNames(self) -> dict[int, bytes]:
        return {
            self.IdRole: b"windowId", self.TitleRole: b"windowTitle", self.KindRole: b"kind",
            self.XRole: b"windowX", self.YRole: b"windowY", self.WidthRole: b"windowWidth",
            self.HeightRole: b"windowHeight", self.VisibleRole: b"windowVisible", self.ZRole: b"stackOrder",
            self.BlockingRole: b"windowBlocking", self.GeometryModeRole: b"geometryMode",
            self.ContentSourceRole: b"contentSource",
            self.ContentPropertiesRole: b"contentProperties",
        }

    @classmethod
    def _content_source(cls, window: FloatingWindow) -> str:
        if window.kind in cls._configuration_pages:
            return "ConfigurationPage.qml"
        return cls._content_sources.get(window.kind, "UnregisteredWindow.qml")

    @staticmethod
    def _content_properties(window: FloatingWindow) -> dict[str, object]:
        if window.kind == "configuration":
            return {"windowId": window.window_id}
        if window.kind in FloatingWindowModel._configuration_pages:
            return {"pageId": window.kind}
        if window.kind in {"filter_editor", "matching_templates", "repository_editor"}:
            return {"windowId": window.window_id}
        if window.kind in {"preview_editor", "attachments_editor"}:
            return {"editorMode": window.kind}
        if window.kind in {"update", "create_update"}:
            return {"createMode": window.kind == "create_update"}
        if window.kind == "maya_options":
            operation = {
                "maya_import": "import",
                "maya_reference": "reference",
            }.get(window.window_id, "open")
            return {"operationMode": operation}
        if window.kind in {"add_sobject", "task_editor"}:
            return {"editorWindowId": window.window_id}
        if window.kind == "confirm":
            return {"windowId": window.window_id}
        return {}

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._windows)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._windows):
            return None
        window = self._windows[index.row()]
        return {
            self.IdRole: window.window_id, self.TitleRole: window.title, self.KindRole: window.kind,
            self.XRole: window.x, self.YRole: window.y, self.WidthRole: window.width,
            self.HeightRole: window.height, self.VisibleRole: window.visible, self.ZRole: window.z,
            self.BlockingRole: window.blocking, self.GeometryModeRole: window.geometry_mode,
            self.ContentSourceRole: self._content_source(window),
            self.ContentPropertiesRole: self._content_properties(window),
        }.get(role)

    def _row(self, window_id: str) -> int | None:
        return next((row for row, window in enumerate(self._windows) if window.window_id == window_id), None)

    def _replace(self, window_id: str, **changes) -> None:
        row = self._row(window_id)
        if row is None:
            return
        self._windows[row] = replace(self._windows[row], **changes)
        model_index = self.index(row, 0)
        self.dataChanged.emit(model_index, model_index)
        self._save()

    @Slot(str)
    def show_window(self, window_id: str) -> None:
        self._z_counter += 1
        self._replace(window_id, visible=True, z=self._z_counter)

    @Slot(str)
    def close_window(self, window_id: str) -> None:
        self._replace(window_id, visible=False)

    def is_window_visible(self, window_id: str) -> bool:
        row = self._row(window_id)
        return bool(
            row is not None and self._windows[row].visible
        )

    @Slot(str)
    def raise_window(self, window_id: str) -> None:
        self._z_counter += 1
        self._replace(window_id, z=self._z_counter)

    @Slot(str, float, float, float, float)
    def set_geometry(self, window_id: str, x: float, y: float, width: float, height: float) -> None:
        # Top-level windows use screen coordinates. Broad bounds protect
        # settings from corrupt values without tying windows to their owner.
        x = max(-100000.0, min(100000.0, x))
        y = max(-100000.0, min(100000.0, y))
        width = max(296.0, min(10000.0, width))
        height = max(206.0, min(10000.0, height))
        self._replace(
            window_id,
            x=x,
            y=y,
            width=width,
            height=height,
            geometry_mode="absolute",
        )

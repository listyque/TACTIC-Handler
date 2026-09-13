"""Workspace presentation models."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from PySide6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    QObject,
    Property,
    QSortFilterProxyModel,
    QTimer,
    Qt,
    QUrl,
    Signal,
    Slot,
)

from tactic_handler_dcc.connectors import dcc_configuration_pages

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
    ParentWindowRole = Qt.UserRole + 14
    helpTopicChanged = Signal()
    layoutReset = Signal()
    windowVisibilityChanged = Signal(str, bool)
    _settings_key = "workspace/floatingWindows"
    # These editors are valid only for an explicitly prepared item/relation.
    # Restore their geometry, but never restore them open with stale context.
    _context_required_windows = frozenset({
        "link_sobjects", "watch_folder_editor",
        "process_filter_editor", "repository_sync_editor",
        "quick_filter_editor",
        "ingest_files",
        "sidebar_search_preview", "administration", "schema_search_type", "process_dependencies",
        "project_wizard",
        "project_editor",
        "delete_sobject",
        "duplicate_sobject",
        "add_sobject", "task_editor",
        "screenshot_maker",
        "naming_editor",
        "error",
    })

    _configuration_pages = frozenset({
        "server", "repository", "project", "checkin_preferences",
        "global_preferences", "appearance", "tasks_preferences", "cache",
    })

    @classmethod
    def _configuration_page_ids(cls) -> frozenset[str]:
        return cls._configuration_pages | frozenset(
            page["id"] for page in dcc_configuration_pages()
        )
    _content_sources = {
        "configuration": "ConfigurationView.qml",
        "project_wizard": "ProjectWizardView.qml",
        "project_editor": "ProjectEditorView.qml",
        "sobject_info": "SObjectInfoView.qml",
        "process_filter_editor": "ProcessFilterEditorView.qml",
        "quick_filter_editor": "QuickFilterEditorView.qml",
        "advanced_search": "AdvancedSearchView.qml",
        "columns_editor": "ColumnsEditorView.qml",
        "naming_editor": "NamingEditorView.qml",
        "server_presets": "ServerPresetsView.qml",
        "screenshot_maker": "ScreenshotMakerView.qml",
        "handler_server": "HandlerServerView.qml",
        "script_editor": "ScriptEditorView.qml",
        "script_shelf_editor": "ScriptShelfEditorView.qml",
        "script_trigger_editor": "ScriptTriggerEditorView.qml",
        "help": "HelpView.qml",
        "debug_log": "DebugLogView.qml",
        "ui_performance": "UiPerformanceView.qml",
        "error": "ErrorDialog.qml",
        "repository_sync": "RepositorySyncView.qml",
        "repository_sync_editor": "RepositorySyncEditorView.qml",
        "commit_queue": "CommitQueueView.qml",
        "ingest_files": "IngestFilesView.qml",
        "messages": "MessagesView.qml",
        "notifications": "NotificationsView.qml",
        "activity_feed": "ActivityFeedView.qml",
        "user_profile": "UserProfileView.qml",
        "sidebar_editor": "SidebarEditorView.qml",
        "administration": "AdministrationView.qml",
        "schema_search_type": "AdminSchemaTypeView.qml",
        "process_dependencies": "AdminProcessRulesView.qml",
        "sidebar_search_preview": "SidebarSearchPreview.qml",
        "tasks_workspace": "TasksWorkspaceView.qml",
        "milestone_manager": "MilestoneManagerView.qml",
        "update": "UpdateView.qml",
        "create_update": "UpdateView.qml",
        "matching_templates": "MatchingTemplatesView.qml",
        "repository_editor": "RepositoryEditorView.qml",
        "db_table": "DatabaseBatchEditorView.qml",
        "dcc_options": "DccOptionsView.qml",
        "add_sobject": "SObjectFieldEditor.qml",
        "task_editor": "SObjectFieldEditor.qml",
        "link_sobjects": "LinkSObjectsView.qml",
        "watch_folders": "WatchFoldersView.qml",
        "watch_folder_editor": "WatchFolderEditorView.qml",
        "delete_sobject": "DeleteSObjectView.qml",
        "duplicate_sobject": "DuplicateSObjectView.qml",
    }

    def __init__(self, settings: dict) -> None:
        super().__init__()
        self._settings = settings
        self._parent_windows: dict[str, str] = {}
        self._help_topic = "overview"
        self._windows = self._restore() or self._defaults()
        self._z_counter = max((window.z for window in self._windows), default=0)

    @staticmethod
    def _defaults() -> list[FloatingWindow]:
        return [
            FloatingWindow("configuration", "Configuration", "configuration", .15, .10, .70, .76),
            FloatingWindow("server", "Server Settings", "server", .23, .16, .54, .62),
            FloatingWindow("project", "Project Settings", "project", .22, .15, .56, .64),
            FloatingWindow("project_wizard", "Create Project", "project_wizard", .22, .14, .56, .70, blocking=True),
            FloatingWindow("project_editor", "Edit Project", "project_editor", .22, .14, .56, .70, blocking=True),
            FloatingWindow("checkin_preferences", "Check-in Options", "checkin_preferences", .19, .12, .62, .72),
            FloatingWindow("global_preferences", "Global Settings", "global_preferences", .26, .20, .48, .48),
            *(
                FloatingWindow(
                    page["id"], page.get("title") or page["application"].title(),
                    page["id"], .27, .20, .46, .45,
                )
                for page in dcc_configuration_pages()
            ),
            FloatingWindow("sobject_info", "SObject Report", "sobject_info", .12, .09, .76, .80),
            FloatingWindow("process_filter_editor", "Filter Processes", "process_filter_editor", .37, .25, .26, .50, blocking=True),
            FloatingWindow("quick_filter_editor", "Quick filters", "quick_filter_editor", .24, .12, .52, .72, blocking=True),
            FloatingWindow("columns_editor", "Columns Editor", "columns_editor", .26, .16, .48, .58),
            FloatingWindow("naming_editor", "Naming Editor", "naming_editor", .22, .12, .56, .68),
            FloatingWindow("server_presets", "Server Presets", "server_presets", .20, .14, .60, .66),
            FloatingWindow("screenshot_maker", "Screenshot Maker", "screenshot_maker", .18, .12, .64, .70),
            FloatingWindow("script_editor", "Script Editor", "script_editor", .16, .10, .68, .70),
            FloatingWindow("script_shelf_editor", "Script Shelf", "script_shelf_editor", .20, .14, .60, .66),
            FloatingWindow("script_trigger_editor", "Script Triggers", "script_trigger_editor", .18, .12, .64, .72),
            FloatingWindow("help", "Help", "help", .15, .10, .70, .76),
            FloatingWindow("debug_log", "Debug Log", "debug_log", .18, .13, .64, .68),
            FloatingWindow("ui_performance", "UI responsiveness", "ui_performance", .15, .12, .70, .70),
            FloatingWindow("error", "Application Error", "error", .18, .16, .64, .68, blocking=True),
            FloatingWindow("repository_sync", "Repository Sync Queue", "repository_sync", .18, .13, .64, .68),
            FloatingWindow("repository_sync_editor", "Repository Sync", "repository_sync_editor", .10, .08, .80, .82, blocking=True),
            FloatingWindow("commit_queue", "Commit Queue", "commit_queue", .18, .13, .64, .68),
            FloatingWindow("ingest_files", "Add files", "ingest_files", .16, .10, .68, .76),
            FloatingWindow("messages", "Messages", "messages", .16, .12, .68, .70),
            FloatingWindow("notifications", "Notifications", "notifications", .22, .15, .56, .64),
            FloatingWindow("activity_feed", "Activity Feed", "activity_feed", .18, .12, .64, .70),
            FloatingWindow("user_profile", "User Profile", "user_profile", .18, .12, .64, .72),
            FloatingWindow("users", "Users", "user_profile", .12, .08, .76, .82),
            FloatingWindow("sidebar_editor", "Sidebar Editor", "sidebar_editor", .10, .08, .80, .82, blocking=True),
            FloatingWindow("administration", "Administration", "administration", .08, .06, .84, .86, blocking=True),
            FloatingWindow("schema_search_type", "New Search Type", "schema_search_type", .20, .12, .60, .76, blocking=True),
            FloatingWindow("process_dependencies", "Process dependencies", "process_dependencies", .16, .10, .68, .80, blocking=True),
            FloatingWindow("sidebar_search_preview", "Search preview", "sidebar_search_preview", .08, .06, .84, .86, blocking=True),
            FloatingWindow("update", "Update", "update", .30, .24, .40, .42),
            FloatingWindow("create_update", "Create Update", "create_update", .28, .21, .44, .50),
            FloatingWindow("repository_editor", "Repository Editor", "repository_editor", .18, .12, .64, .70),
            FloatingWindow("matching_templates", "Matching Templates", "matching_templates", .28, .18, .45, .56),
            FloatingWindow("dcc_options", "DCC Action Options", "dcc_options", .31, .26, .38, .40),
            FloatingWindow("handler_server", "TACTIC Handler Server", "handler_server", .12, .08, .76, .78),
            FloatingWindow("add_sobject", "Add SObject", "add_sobject", .23, .16, .54, .64),
            FloatingWindow("task_editor", "Task Editor", "task_editor", .23, .16, .54, .64, blocking=True),
            FloatingWindow("milestone_manager", "Project Milestones", "milestone_manager", .24, .16, .52, .62),
            FloatingWindow("link_sobjects", "Link SObjects", "link_sobjects", .22, .16, .56, .64),
            FloatingWindow("watch_folders", "Watch Folders", "watch_folders", .16, .13, .68, .70, blocking=True),
            FloatingWindow("watch_folder_editor", "Watch Folder", "watch_folder_editor", .25, .20, .50, .50, blocking=True),
            FloatingWindow("delete_sobject", "Delete SObject", "delete_sobject", .20, .12, .60, .72, blocking=True),
            FloatingWindow(
                "duplicate_sobject", "Duplicate SObject",
                "duplicate_sobject", .17, .10, .66, .78,
            ),
        ]

    def _restore(self) -> list[FloatingWindow] | None:
        raw = self._settings.get(self._settings_key, "")
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
                    visible=(
                        False
                        if default.window_id in self._context_required_windows
                        else saved.visible
                    ),
                )
            result.append(saved or default)
        return result

    def _save(self) -> None:
        self._settings[self._settings_key] = json.dumps([
            asdict(window) for window in self._windows
        ])

    def roleNames(self) -> dict[int, bytes]:
        return {
            self.IdRole: b"windowId", self.TitleRole: b"windowTitle", self.KindRole: b"kind",
            self.XRole: b"windowX", self.YRole: b"windowY", self.WidthRole: b"windowWidth",
            self.HeightRole: b"windowHeight", self.VisibleRole: b"windowVisible", self.ZRole: b"stackOrder",
            self.BlockingRole: b"windowBlocking", self.GeometryModeRole: b"geometryMode",
            self.ContentSourceRole: b"contentSource",
            self.ContentPropertiesRole: b"contentProperties",
            self.ParentWindowRole: b"parentWindowId",
        }

    @classmethod
    def _content_source(cls, window: FloatingWindow) -> str:
        if window.kind in cls._configuration_page_ids():
            return "ConfigurationPage.qml"
        return cls._content_sources.get(window.kind, "UnregisteredWindow.qml")

    @staticmethod
    def _content_properties(window: FloatingWindow) -> dict[str, object]:
        if window.kind == "configuration":
            return {"windowId": window.window_id}
        if window.kind in FloatingWindowModel._configuration_page_ids():
            return {"pageId": window.kind}
        if window.kind in {
            "process_filter_editor", "matching_templates",
            "repository_editor", "repository_sync_editor",
            "quick_filter_editor",
        }:
            return {"windowId": window.window_id}
        if window.kind in {"update", "create_update"}:
            return {"createMode": window.kind == "create_update"}
        if window.kind in {"add_sobject", "task_editor"}:
            return {"editorWindowId": window.window_id}
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
            self.ParentWindowRole: self._parent_windows.get(window.window_id, ""),
        }.get(role)

    def _row(self, window_id: str) -> int | None:
        return next((row for row, window in enumerate(self._windows) if window.window_id == window_id), None)

    def _replace(self, window_id: str, **changes) -> None:
        row = self._row(window_id)
        if row is None:
            return
        previous = self._windows[row]
        self._windows[row] = replace(previous, **changes)
        model_index = self.index(row, 0)
        self.dataChanged.emit(model_index, model_index)
        self._save()
        current = self._windows[row]
        if previous.visible != current.visible:
            self.windowVisibilityChanged.emit(
                current.window_id, current.visible
            )

    @Slot(str)
    def show_window(self, window_id: str) -> None:
        if window_id == "error" and self.is_window_visible(window_id):
            self.raise_window(window_id)
            return
        if window_id in {"error", "debug_log", "help"}:
            # A sibling WindowModal can block the error itself on Windows.
            # Diagnostics must belong to the topmost existing modal instead.
            for window in sorted(self._windows, key=lambda item: item.z, reverse=True):
                if not window.visible or not window.blocking:
                    continue
                ancestor = window.window_id
                while ancestor and ancestor != window_id:
                    ancestor = self._parent_windows.get(ancestor, "")
                if not ancestor:
                    self.show_child_window(window_id, window.window_id)
                    return
        self._parent_windows.pop(window_id, None)
        self._z_counter += 1
        self._replace(window_id, visible=True, z=self._z_counter)

    @Slot(str, str)
    def show_child_window(self, window_id: str, parent_id: str) -> None:
        """Keep nested native modals attached to their invoking tool."""
        if self._row(window_id) is None or self._row(parent_id) is None:
            raise ValueError("Both windows must be registered")
        ancestor = parent_id
        while ancestor:
            if ancestor == window_id:
                raise ValueError("A window cannot own itself or an ancestor")
            ancestor = self._parent_windows.get(ancestor, "")
        self._parent_windows[window_id] = parent_id
        self._z_counter += 1
        self._replace(window_id, visible=True, z=self._z_counter)

    @Property(str, notify=helpTopicChanged)
    def helpTopic(self) -> str:
        return self._help_topic

    @Slot(str)
    def open_help(self, topic: str = "overview") -> None:
        topic = str(topic or "overview").strip() or "overview"
        if self._help_topic != topic:
            self._help_topic = topic
            self.helpTopicChanged.emit()
        self.show_window("help")

    @Slot(str)
    def close_window(self, window_id: str) -> None:
        for child, parent in tuple(self._parent_windows.items()):
            if parent == window_id and self.is_window_visible(child):
                self.close_window(child)
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

    @Slot()
    def reset_layout(self) -> None:
        """Restore safe default geometry without closing active windows."""
        defaults = {
            window.window_id: window for window in self._defaults()
        }
        changed_roles = [
            self.XRole,
            self.YRole,
            self.WidthRole,
            self.HeightRole,
            self.GeometryModeRole,
        ]
        for row, current in enumerate(self._windows):
            default = defaults.get(current.window_id)
            if default is None:
                continue
            reset = replace(
                current,
                x=default.x,
                y=default.y,
                width=default.width,
                height=default.height,
                geometry_mode=default.geometry_mode,
            )
            if reset == current:
                continue
            self._windows[row] = reset
            index = self.index(row, 0)
            self.dataChanged.emit(index, index, changed_roles)
        self._save()
        self.layoutReset.emit()


class VisibleFloatingWindowModel(QSortFilterProxyModel):
    """Floating windows currently presented by the native window host."""

    RETAINED_WORKSPACES = {"tasks_workspace", "messages", "activity_feed", "notifications"}

    def __init__(self, source: FloatingWindowModel, parent=None) -> None:
        super().__init__(parent)
        self.setSourceModel(source)
        self.setDynamicSortFilter(False)
        self._retained_rows: set[int] = set()
        self._removal_timer = QTimer(self)
        self._removal_timer.setSingleShot(True)
        self._removal_timer.setInterval(750)
        self._removal_timer.timeout.connect(self._release_hidden_rows)
        source.dataChanged.connect(self._source_data_changed)

    def _apply_filter(self) -> None:
        self.beginFilterChange()
        self.endFilterChange(QSortFilterProxyModel.Direction.Rows)

    def _source_data_changed(self, top_left, bottom_right, *_args) -> None:
        add_now = False
        remove_later = False
        source = self.sourceModel()
        for row in range(top_left.row(), bottom_right.row() + 1):
            source_index = source.index(row, 0)
            visible = bool(source.data(
                source_index, FloatingWindowModel.VisibleRole
            ))
            present = self.mapFromSource(source_index).isValid()
            if visible:
                self._retained_rows.discard(row)
            elif present:
                self._retained_rows.add(row)
            add_now = add_now or (visible and not present)
            remove_later = remove_later or (present and not visible)
        if add_now:
            self._apply_filter()
        if remove_later:
            self._removal_timer.start()

    def _release_hidden_rows(self) -> None:
        source = self.sourceModel()
        self._retained_rows = {
            row for row in self._retained_rows
            if source.data(source.index(row, 0), FloatingWindowModel.IdRole)
            in self.RETAINED_WORKSPACES
        }
        self._apply_filter()

    def filterAcceptsRow(self, source_row, source_parent) -> bool:
        source = self.sourceModel()
        if source is None:
            return False
        index = source.index(source_row, 0, source_parent)
        return (
            bool(source.data(index, FloatingWindowModel.VisibleRole))
            or source_row in self._retained_rows
        )

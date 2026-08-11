"""Public state and models for workspace docks."""

from __future__ import annotations

from PySide6.QtCore import QObject, Property, Signal

from .records import RecordListModel
from .results import WorkspaceItemModel
from .state_project_state import ProjectStateMixin
from .state_snapshot_state import SnapshotStateMixin
from .state_selection_state import SelectionStateMixin
from .state_detail_editing import DetailEditingMixin
from .state_workspace_tabs import WorkspaceTabsMixin


class WorkspaceState(
        ProjectStateMixin,
        SnapshotStateMixin,
        SelectionStateMixin,
        DetailEditingMixin,
        WorkspaceTabsMixin,
        QObject):
    description_changed = Signal(str)

    description_editor_changed = Signal()

    selection_changed = Signal()

    tab_activated = Signal(str, str)

    tab_add_requested = Signal()

    tab_close_requested = Signal(int)

    tab_reorder_requested = Signal(int, int)

    description_save_requested = Signal(str)

    note_add_requested = Signal(str)

    task_status_requested = Signal(int, str)

    def __init__(self) -> None:
        super().__init__()
        self._description = ""
        self._description_original = ""
        self._description_editing = False
        self._description_pinned = False
        self._description_saving = False
        self._description_error = ""
        self._description_target = None
        self._description_target_key = ""
        self._description_target_kind = ""
        self._description_target_title = ""
        self._project = None
        self._selected_title = ""
        self._selected_sobject = None
        self._task_sobjects = []
        self._note_sobjects = []
        self._notes_process = None
        self._notes_loaded = False
        self._preview_helper = WorkspaceItemModel()
        self.tabs_model = RecordListModel(("entryKey", "title", "closable", "current"))
        self.snapshot_model = RecordListModel((
            "nodeId", "searchKey", "title", "path", "version", "revision",
            "context", "kind", "selected", "previewUrl", "accent",
            "fileExists", "isLatest", "repository", "author", "timestamp",
            "previewItems", "files",
        ))
        self.snapshot_preview_model = RecordListModel((
            "token", "title", "url", "kind", "snapshotNodeId",
        ))
        self.snapshot_file_model = RecordListModel((
            "rowType", "token", "title", "fileType", "size", "path",
            "repository", "baseType", "depth", "exists", "previewType",
            "snapshotNodeId", "version", "checking", "matchesRemote",
        ))
        self._snapshot_file_objects: dict[str, object] = {}
        self.search_suggestion_model = RecordListModel((
            "title", "description", "keyword", "code", "values", "selected",
        ))
        self.advanced_filter_suggestion_model = RecordListModel((
            "title", "description", "keyword", "values",
        ))
        self.task_model = RecordListModel((
            "taskId", "searchKey", "process", "status", "user", "start",
            "end", "due", "progress", "description", "color", "checked",
            "notes",
        ))
        self.note_model = RecordListModel((
            "noteId", "searchKey", "author", "time", "body", "bodyHtml",
            "displayHtml", "skeyPreviews",
            "status", "process", "isOwn", "unread", "attachments",
            "attachmentCount", "entryType", "authorDisplay", "avatarUrl",
            "initials", "authorColor", "timePretty", "timeSimple",
            "statusFrom", "statusTo", "statusColor", "edited", "editedBy",
            "editedAt", "editHistory", "canEdit", "canDelete",
            "statusTimelineBefore", "statusTimelineAfter",
        ))
        self.drop_model = RecordListModel(("title", "path", "size", "process", "checked", "status"))
        self.filter_model = RecordListModel((
            "column", "relation", "value", "rowEnabled", "operator",
            "isDefault",
        ))
        self.fast_control_model = RecordListModel(("label", "value", "choices"))
        self.repo_sync_model = RecordListModel(("title", "process", "progress", "status", "checked"))
        self.commit_model = RecordListModel(("title", "context", "repository", "status", "checked"))
        self.watch_model = RecordListModel(("title", "path", "watchEnabled", "process"))
        self.configuration_page_model = RecordListModel(
            ("title", "target", "icon"),
            [
                {"title": "Server", "target": "server", "icon": "cloud_done"},
                {"title": "Projects", "target": "project", "icon": "project-diagram"},
                {"title": "Check-in Options", "target": "checkin_preferences", "icon": "tune"},
                {"title": "Check-in/Out", "target": "checkinout_preferences", "icon": "view_kanban"},
                {"title": "Global", "target": "global_preferences", "icon": "settings"},
                {"title": "Tasks", "target": "tasks_preferences", "icon": "tasks"},
                {"title": "Maya Scene", "target": "maya_preferences", "icon": "movie"},
            ],
        )

        self.task_status_model = RecordListModel(("label",))
        self.filter_column_model = RecordListModel(
            ("label", "value", "dataType")
        )
        self.filter_relation_model = RecordListModel(("label", "value"))
        self.sync_preset_model = RecordListModel(("label",))
        self.server_preset_model = RecordListModel(("label",))
        from thlib.environment import env_server
        self.server_preset_model.replace([
            {"label": preset}
            for preset in env_server.get_server_presets().get(
                "presets_list", []
            )
        ])
        self.process_tabs_model = RecordListModel(("label",))
        self.controls_tabs_model = RecordListModel(("label",))
        self.maya_format_model = RecordListModel(
            ("label", "value"),
            [
                {"label": "Maya ASCII (.ma)", "value": "mayaAscii"},
                {"label": "Maya Binary (.mb)", "value": "mayaBinary"},
            ],
        )
        self.columns_model = RecordListModel(("title", "checked"))
        self.script_language_model = RecordListModel(("label",))
        self.log_level_model = RecordListModel(("label",))
        self.user_model = RecordListModel(("label",))
        self.update_version_model = RecordListModel(("label",))
        self.template_model = RecordListModel(("label",))
        self.repository_model = RecordListModel(("label",))
        self.database_table_model = RecordListModel(("label",))
        self.search_type_model = RecordListModel(("label",))

    @Property(str, notify=selection_changed)
    def selected_title(self) -> str:
        return self._selected_title

    @Property(str, notify=description_changed)
    def description(self) -> str:
        return self._description

    @Property(str, notify=description_editor_changed)
    def descriptionOriginal(self) -> str:
        return self._description_original

    @Property(bool, notify=description_editor_changed)
    def descriptionEditing(self) -> bool:
        return self._description_editing

    @Property(bool, notify=description_editor_changed)
    def descriptionPinned(self) -> bool:
        return self._description_pinned

    @Property(bool, notify=description_editor_changed)
    def descriptionDirty(self) -> bool:
        return self._description != self._description_original

    @Property(bool, notify=description_editor_changed)
    def descriptionSaving(self) -> bool:
        return self._description_saving

    @Property(str, notify=description_editor_changed)
    def descriptionError(self) -> str:
        return self._description_error

    @Property(bool, notify=description_editor_changed)
    def descriptionCanSave(self) -> bool:
        return bool(self._description_target_key)

    @Property(str, notify=description_editor_changed)
    def descriptionTargetKind(self) -> str:
        return self._description_target_kind

    @Property(str, notify=description_editor_changed)
    def descriptionTargetTitle(self) -> str:
        return self._description_target_title

    @Property(str, notify=description_editor_changed)
    def checkinDescription(self) -> str:
        return self._description if self._description_pinned else ""

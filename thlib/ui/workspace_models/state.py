"""Public state and models for workspace docks."""

from __future__ import annotations

from PySide6.QtCore import QObject, Property, Signal

from tactic_handler_dcc.connectors import dcc_configuration_pages

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
        # Restoring one Search Tab publishes several dependent models.  The
        # flag lets presentation controllers ignore those intermediate model
        # notifications and rebuild once from the final selection instead.
        self._selection_projection_restoring = False
        self._preview_helper = WorkspaceItemModel()
        self.tabs_model = RecordListModel((
            "entryKey",
            "title",
            "closable",
            "current",
            "resultModel",
            "viewMode",
            "splitterRatio",
        ))
        # Search Type switches must not replace the model owned by a retained
        # result surface.  The tab strip above shows only the active section,
        # while this model owns every open section/tab surface for its whole
        # UI lifetime.
        self.result_surfaces_model = RecordListModel((
            "surfaceKey",
            "current",
            "resultModel",
            "viewMode",
            "splitterRatio",
        ))
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
        self._snapshot_presentation_visible = True
        self._snapshot_records: list[dict] = []
        self._snapshot_preview_records: list[dict] = []
        self._snapshot_file_records_cache: list[dict] = []
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
        self._detail_presentation_visible = True
        self._task_records_cache: list[dict] = []
        self._task_status_records_cache: list[dict] = []
        self._note_records_cache: list[dict] = []
        self.note_model = RecordListModel((
            "noteId", "searchKey", "author", "time", "body", "bodyHtml",
            "displayHtml", "skeyPreviews",
            "status", "process", "isOwn", "unread", "attachments",
            "attachmentCount", "entryType", "authorDisplay", "avatarUrl",
            "initials", "authorColor", "timePretty", "timeSimple",
            "statusFrom", "statusTo", "statusColor", "edited", "editedBy",
            "editedAt", "editHistory", "canEdit", "canDelete",
            "statusTimelineBefore", "statusTimelineAfter",
        ), identity_role="noteId")
        self.drop_model = RecordListModel(("title", "path", "size", "process", "checked", "status"))
        self.filter_model = RecordListModel((
            "column", "relation", "value", "rowEnabled", "operator",
            "isDefault", "generatedFilterKind", "generatedFilterState",
        ))
        self.repo_sync_model = RecordListModel(("title", "process", "progress", "status", "checked"))
        self.commit_model = RecordListModel(("title", "context", "repository", "status", "checked"))
        self.watch_model = RecordListModel(("title", "path", "watchEnabled", "process"))
        configuration_pages = [
            {
                "title": "Server", "target": "server", "icon": "cloud_done",
                "description": "Connection, sign-in status and server presets",
                "helpTopic": "server_configuration",
            },
            {
                "title": "Repositories", "target": "repository", "icon": "database",
                "description": "Repository locations, availability and default storage",
                "helpTopic": "repository_configuration",
            },
            {
                "title": "Projects", "target": "project", "icon": "project-diagram",
                "description": "Active project and workspace context",
                "helpTopic": "configuration.projects",
            },
            {
                "title": "Check-in Options", "target": "checkin_preferences", "icon": "tune",
                "description": "Naming and file handling defaults",
                "helpTopic": "configuration.checkin",
            },
            {
                "title": "Global", "target": "global_preferences", "icon": "settings",
                "description": "Application behavior and diagnostics",
                "helpTopic": "configuration.global",
            },
            {
                "title": "Appearance", "target": "appearance", "icon": "palette",
                "description": "Themes, animations, language and rendering",
                "helpTopic": "appearance",
            },
            {
                "title": "Cache", "target": "cache", "icon": "cached",
                "description": "Persistent server data and cache policy",
                "helpTopic": "configuration.cache",
            },
            {
                "title": "Tasks", "target": "tasks_preferences", "icon": "tasks",
                "description": "Task Browser layout and Notes inspector defaults",
                "helpTopic": "configuration.tasks",
            },
        ]
        configuration_pages.extend({
            "title": page.get("title") or page["application"].title(),
            "target": page["id"],
            "icon": page.get("icon") or "deployed_code",
            "description": page.get("description") or "",
            "helpTopic": page.get("help_topic") or "dcc_clients",
        } for page in dcc_configuration_pages())
        self.configuration_page_model = RecordListModel(
            ("title", "target", "icon", "description", "helpTopic"),
            configuration_pages,
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

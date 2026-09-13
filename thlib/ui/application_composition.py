"""Explicit feature composition for the desktop application.

The builders in this module keep dependency wiring local to a functional area.
They intentionally avoid reflection and a generic dependency-injection container:
dependencies remain visible Python arguments and every public QML name is listed
next to the feature that owns it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tactic_handler_api import _bind_current
from thlib.environment import env_read_config

from thlib.ui.application_runtime import (
    ApplicationRuntime,
    LifecycleRegistry,
    QmlBindingRegistry,
)
from thlib.ui.checkin_out import CheckinOutController
from thlib.ui.cache_controller import ServerCacheController
from thlib.ui.columns_editor import ColumnsEditorController
from thlib.ui.commit_queue import CommitQueueController
from thlib.ui.communication import CommunicationController
from thlib.ui.communication_feed import (
    ActivityFeedController,
    MessagesController,
)
from thlib.ui.configuration import (
    ConfigurationController,
    read_dcc_preferences,
)
from thlib.ui.controller import ApplicationController
from thlib.ui.debug_logging import DebugLogController
from thlib.ui.drop_plate import DropPlateController
from thlib.ui.editor_tools import ScreenshotController, ServerPresetsController
from thlib.ui.emoji import EmojiCatalog
from thlib.ui.filter_editor import FilterEditorController
from thlib.ui.handler_server_controller import HandlerServerController
from thlib.ui.help import HelpController
from thlib.ui.ingest import IngestFilesController
from thlib.ui.localization import LocalizationController
from thlib.ui.knowledge import KnowledgeController
from thlib.ui.rich_text_document import RichTextDocumentController
from thlib.ui.matching_templates import MatchingTemplatesController
from thlib.ui.dcc_options import DccOptionsController
from thlib.ui.message_attachments import (
    AttachmentUploadController,
    ChatAttachmentController,
)
from thlib.ui.milestones import MilestoneController
from thlib.ui.naming_editor import NamingEditorController
from thlib.ui.notifications import NotificationController
from thlib.ui.pointer import PointerController
from thlib.ui.process_filter_editor import ProcessFilterEditorController
from thlib.ui.project_editor import ProjectEditorController
from thlib.ui.quick_filter_editor import QuickFilterEditorController
from thlib.ui.repository_editor import RepositoryEditorController
from thlib.ui.repository_sync_editor import RepositorySyncEditorController
from thlib.ui.script_editor import ScriptEditorController
from thlib.ui.script_shelf import ScriptShelfController
from thlib.ui.script_triggers import ScriptTriggerController
from thlib.ui.server_updates import ServerUpdateService
from thlib.ui.sidebar_editor import SidebarEditorController
from thlib.ui.skey_previews import SearchKeyPreviewResolver
from thlib.ui.sobject_delete import SObjectDeleteController
from thlib.ui.sobject_duplicate import SObjectDuplicateController
from thlib.ui.sobject_editor import SObjectEditorController
from thlib.ui.sobject_info import SObjectInfoController
from thlib.ui.sobject_link import SObjectLinkController
from thlib.ui.tasks import TasksController
from thlib.ui.tray import TrayController
from thlib.ui.update_controller import UpdateController
from thlib.ui.user import UserController
from thlib.ui.administration import AdministrationController
from thlib.ui.watch_folders import WatchFoldersController
from thlib.ui.window_appearance import WindowAppearanceController
from thlib.ui.work_hours import WorkHoursController
from thlib.ui.workspace_layout_presets import (
    WorkspaceLayoutPresetController,
)


@dataclass(frozen=True)
class CoreBundle:
    controller: ApplicationController
    server_cache: ServerCacheController
    localization: LocalizationController
    help: HelpController
    window_appearance: WindowAppearanceController
    pointer: PointerController
    debug_log: DebugLogController
    sobject_delete: SObjectDeleteController
    sobject_duplicate: SObjectDuplicateController

    def qml_bindings(self) -> dict[str, Any]:
        workspace = self.controller.workspace_state
        return {
            "appController": self.controller,
            "uiPerformance": self.controller.ui_performance,
            "uiPerformanceModel": self.controller.ui_performance.model,
            "serverCacheController": self.server_cache,
            "windowAppearanceController": self.window_appearance,
            "pointerController": self.pointer,
            "sobjectDeleteController": self.sobject_delete,
            "sobjectDependencyModel": self.sobject_delete.model,
            "sobjectDuplicateController": self.sobject_duplicate,
            "sobjectDuplicateFieldModel": self.sobject_duplicate.fields,
            "sobjectDuplicateRelationModel": self.sobject_duplicate.relations,
            "sobjectDuplicateProcessModel": self.sobject_duplicate.processes,
            "localizationController": self.localization,
            "helpController": self.help,
            "debugLog": self.debug_log,
            "debugLogModel": self.debug_log.entries_model,
            "debugGroupModel": self.debug_log.groups_model,
            "navigationModel": self.controller.navigation_model,
            "sectionTabsModel": self.controller.section_model,
            "projectModel": self.controller.project_model,
            "workspaceModel": self.controller.workspace_model,
            "versionsModel": self.controller.versions_model,
            "workspaceState": workspace,
            "workspaceTabsModel": workspace.tabs_model,
            "workspaceResultSurfacesModel": workspace.result_surfaces_model,
            "searchSuggestionModel": workspace.search_suggestion_model,
            "advancedFilterSuggestionModel": workspace.advanced_filter_suggestion_model,
            "snapshotModel": workspace.snapshot_model,
            "snapshotPreviewModel": workspace.snapshot_preview_model,
            "snapshotFileModel": workspace.snapshot_file_model,
            "taskModel": workspace.task_model,
            "noteModel": workspace.note_model,
            "dropModel": workspace.drop_model,
            "filterModel": workspace.filter_model,
            "repoSyncModel": self.controller.repository_sync.model,
            "repositorySync": self.controller.repository_sync,
            "watchModel": workspace.watch_model,
            "dockModel": self.controller.dock_model,
            "windowModel": self.controller.window_model,
            "visibleDockModel": self.controller.visible_dock_model,
            "detachedDockModel": self.controller.detached_dock_model,
            "visibleWindowModel": self.controller.visible_window_model,
            "configPageModel": workspace.configuration_page_model,
            "taskStatusModel": workspace.task_status_model,
            "filterColumnModel": workspace.filter_column_model,
            "filterRelationModel": workspace.filter_relation_model,
            "syncPresetModel": workspace.sync_preset_model,
            "serverPresetModel": workspace.server_preset_model,
            "processTabsModel": workspace.process_tabs_model,
            "controlsTabsModel": workspace.controls_tabs_model,
            "columnsModel": workspace.columns_model,
            "scriptLanguageModel": workspace.script_language_model,
            "logLevelModel": workspace.log_level_model,
            "userModel": workspace.user_model,
            "updateVersionModel": workspace.update_version_model,
            "templateModel": workspace.template_model,
            "repositoryModel": workspace.repository_model,
            "databaseTableModel": workspace.database_table_model,
            "searchTypeModel": workspace.search_type_model,
        }


@dataclass(frozen=True)
class TaskBundle:
    tasks: TasksController
    milestones: MilestoneController

    def qml_bindings(self) -> dict[str, Any]:
        return {
            "tasksController": self.tasks,
            "milestoneController": self.milestones,
            "milestoneModel": self.milestones.model,
            "taskProcessModel": self.tasks.process_model,
            "advancedTaskModel": self.tasks.advanced_model,
            "advancedTaskTableModel": self.tasks.table_model,
            "taskGanttModel": self.tasks.gantt_model,
            "taskCalendarModel": self.tasks.calendar_model,
            "taskHistoryModel": self.tasks.history_model,
        }


@dataclass(frozen=True)
class CollaborationBundle:
    emoji_catalog: EmojiCatalog
    users: UserController
    layout_presets: WorkspaceLayoutPresetController
    sidebar_editor: SidebarEditorController
    administration: AdministrationController
    quick_filter_editor: QuickFilterEditorController
    skey_previews: SearchKeyPreviewResolver
    sobject_info: SObjectInfoController
    chat_attachments: ChatAttachmentController
    note_attachments: AttachmentUploadController
    knowledge_attachments: AttachmentUploadController
    knowledge_rich_text: RichTextDocumentController
    knowledge: KnowledgeController
    communication: CommunicationController
    work_hours: WorkHoursController
    messages: MessagesController
    activity_feed: ActivityFeedController
    server_updates: ServerUpdateService

    def qml_bindings(self) -> dict[str, Any]:
        return {
            "emojiCatalog": self.emoji_catalog,
            "userController": self.users,
            "workspaceLayoutPresets": self.layout_presets,
            "workspaceLayoutPresetModel": self.layout_presets.presets,
            "sidebarEditorController": self.sidebar_editor,
            "sidebarEntryModel": self.sidebar_editor.entries,
            "sidebarSecurityGroupModel": self.sidebar_editor.security_groups,
            "administrationController": self.administration,
            "administrationGroupModel": self.administration.groups,
            "administrationMemberModel": self.administration.members,
            "serverUpdateService": self.server_updates,
            "quickFilterEditorController": self.quick_filter_editor,
            "userListModel": self.users.users,
            "userActivityModel": self.users.activity,
            "userGroupModel": self.users.groups,
            "sobjectInfoController": self.sobject_info,
            "sobjectTaskStatusModel": self.sobject_info.task_statuses,
            "sobjectTaskProcessModel": self.sobject_info.task_processes,
            "sobjectTaskModel": self.sobject_info.tasks,
            "sobjectParticipantModel": self.sobject_info.participants,
            "sobjectNoteModel": self.sobject_info.notes,
            "sobjectChildModel": self.sobject_info.children,
            "sobjectChildTypeModel": self.sobject_info.child_types,
            "sobjectSnapshotProcessModel": self.sobject_info.snapshot_processes,
            "sobjectSnapshotModel": self.sobject_info.snapshots,
            "sobjectFileModel": self.sobject_info.files,
            "sobjectActivityModel": self.sobject_info.activity,
            "sobjectPropertyModel": self.sobject_info.properties,
            "workHoursController": self.work_hours,
            "workHourModel": self.work_hours.entries,
            "timesheetModel": self.work_hours.timesheet_entries,
            "workReportModel": self.work_hours.report_descriptors,
            "workReportValueModel": self.work_hours.report_values,
            "communicationController": self.communication,
            "noteAttachments": self.note_attachments,
            "noteAttachmentDraftModel": self.note_attachments.model,
            "knowledgeController": self.knowledge,
            "knowledgeNavigationModel": self.knowledge.navigation,
            "knowledgeAttachments": self.knowledge_attachments,
            "knowledgeAttachmentDraftModel": self.knowledge_attachments.model,
            "knowledgeRichText": self.knowledge_rich_text,
            "skeyPreviewResolver": self.skey_previews,
            "messagesController": self.messages,
            "messageConversationModel": self.messages.conversations,
            "messageSurfaceModel": self.messages.message_surfaces,
            "messageAttachments": self.chat_attachments,
            "messageAttachmentDraftModel": self.chat_attachments.model,
            "activityFeedController": self.activity_feed,
            "activityFeedModel": self.activity_feed.model,
        }


@dataclass(frozen=True)
class DeliveryBundle:
    columns_editor: ColumnsEditorController
    commit_queue: CommitQueueController
    checkin_out: CheckinOutController
    naming_editor: NamingEditorController
    dcc_options: DccOptionsController
    server_presets: ServerPresetsController
    screenshot: ScreenshotController
    script_editor: ScriptEditorController
    script_shelf: ScriptShelfController
    script_triggers: ScriptTriggerController
    update: UpdateController
    handler_server: HandlerServerController
    tray: TrayController
    notifications: NotificationController
    matching_templates: MatchingTemplatesController
    drop_plate: DropPlateController
    ingest_files: IngestFilesController
    watch_folders: WatchFoldersController

    def qml_bindings(self) -> dict[str, Any]:
        return {
            "trayController": self.tray,
            "columnsEditorController": self.columns_editor,
            "columnsEditorModel": self.columns_editor.model,
            "serverPresetsController": self.server_presets,
            "serverPresetsModel": self.server_presets.model,
            "screenshotController": self.screenshot,
            "scriptEditorController": self.script_editor,
            "scriptEditorModel": self.script_editor.model,
            "scriptEditorTabModel": self.script_editor.tabs,
            "scriptTriggerController": self.script_triggers,
            "scriptTriggerModel": self.script_triggers.model,
            "updateController": self.update,
            "updateModel": self.update.model,
            "handlerServerController": self.handler_server,
            "handlerClientModel": self.handler_server.clients,
            "handlerCapabilityModel": self.handler_server.capabilities,
            "handlerResultModel": self.handler_server.results,
            "notificationController": self.notifications,
            "notificationModel": self.notifications.model,
            "notificationHistoryModel": self.notifications.history,
            "notificationGroupedHistoryModel": self.notifications.filtered_history,
            "checkinOutController": self.checkin_out,
            "dccOptionsController": self.dcc_options,
            "commitQueueController": self.commit_queue,
            "commitQueueModel": self.commit_queue.model,
            "namingEditorController": self.naming_editor,
            "namingEditorModel": self.naming_editor.model,
            "dropPlateController": self.drop_plate,
            "dropPlateModel": self.drop_plate.model,
            "ingestFilesController": self.ingest_files,
            "ingestFileModel": self.ingest_files.files,
            "ingestRuleModel": self.ingest_files.rules,
            "matchingTemplatesController": self.matching_templates,
            "matchingTemplatesModel": self.matching_templates.model,
            "checkinFileModel": self.checkin_out.files,
            "checkoutSnapshotModel": self.checkin_out.checkout_snapshots,
            "checkoutFileModel": self.checkin_out.checkout_files,
            "watchFoldersController": self.watch_folders,
            "watchFoldersModel": self.watch_folders.model,
        }


@dataclass(frozen=True)
class EditorBundle:
    configuration: ConfigurationController
    repository: RepositoryEditorController
    filters: FilterEditorController
    process_filters: ProcessFilterEditorController
    repository_sync: RepositorySyncEditorController
    sobject: SObjectEditorController
    project: ProjectEditorController
    links: SObjectLinkController

    def qml_bindings(self) -> dict[str, Any]:
        return {
            "configurationController": self.configuration,
            "repositoryEditorController": self.repository,
            "repositoryEditorModel": self.repository.model,
            "filterEditorController": self.filters,
            "filterEditorModel": self.filters.model,
            "filterPresetModel": self.filters.presets,
            "processFilterEditorController": self.process_filters,
            "processFilterModel": self.process_filters.model,
            "repositorySyncEditorController": self.repository_sync,
            "repositorySyncTreeModel": self.repository_sync.model,
            "repositorySyncPresetModel": self.repository_sync.presets,
            "sobjectEditorController": self.sobject,
            "sobjectFieldModel": self.sobject.model,
            "projectEditorController": self.project,
            "sobjectLinkController": self.links,
            "linkAvailableModel": self.links.available_model,
            "linkCurrentModel": self.links.linked_model,
        }


def _build_core(
    app,
    project_root: Path,
    diagnostics_root: Path | None = None,
) -> CoreBundle:
    window_appearance = WindowAppearanceController(app)
    pointer = PointerController(app)
    debug_log = DebugLogController(diagnostics_root or project_root)
    debug_log.install()
    server_cache = ServerCacheController(app)
    controller = ApplicationController(
        debug_log=debug_log, cache_controller=server_cache
    )
    localization = LocalizationController(app, controller)
    help_controller = HelpController(
        project_root / "thlib" / "ui" / "help_articles", localization
    )
    sobject_delete = SObjectDeleteController(controller, debug_log)
    sobject_duplicate = SObjectDuplicateController(controller, debug_log)
    controller.sobject_delete = sobject_delete
    controller.sobject_duplicate = sobject_duplicate
    return CoreBundle(
        controller=controller,
        server_cache=server_cache,
        localization=localization,
        help=help_controller,
        window_appearance=window_appearance,
        pointer=pointer,
        debug_log=debug_log,
        sobject_delete=sobject_delete,
        sobject_duplicate=sobject_duplicate,
    )


def _build_tasks(core: CoreBundle) -> TaskBundle:
    tasks = TasksController(core.controller)
    milestones = MilestoneController(core.controller)
    tasks.attach_milestone_controller(milestones)
    return TaskBundle(tasks=tasks, milestones=milestones)


def _build_collaboration(
    core: CoreBundle,
    task_bundle: TaskBundle,
    project_root: Path,
) -> CollaborationBundle:
    controller = core.controller
    tasks = task_bundle.tasks
    server_updates = ServerUpdateService(controller)
    emoji_catalog = EmojiCatalog(project_root)
    users = UserController(controller)
    layout_presets = WorkspaceLayoutPresetController(
        controller, users, controller.dock_model,
    )
    controller.attach_workspace_layout_presets(layout_presets)
    skey_previews = SearchKeyPreviewResolver(
        controller, clock=server_updates.clock
    )
    sidebar_editor = SidebarEditorController(
        controller, users, layout_presets=layout_presets,
    )
    administration = AdministrationController(controller, users, previews=skey_previews)
    sidebar_editor.groupManagementRequested.connect(administration.show_groups)
    administration.groupsChanged.connect(sidebar_editor.refresh_security_groups)
    quick_filter_editor = QuickFilterEditorController(controller, users)
    users.attach_tasks_controller(tasks)
    users.attach_skey_previews(skey_previews)
    sobject_info = SObjectInfoController(
        controller,
        users=users,
        navigation=skey_previews,
        tasks=tasks,
        clock=server_updates.clock,
    )
    chat_attachments = ChatAttachmentController(controller)
    note_attachments = AttachmentUploadController(controller)
    knowledge_attachments = AttachmentUploadController(
        controller, draft_namespace="knowledge"
    )
    knowledge_rich_text = RichTextDocumentController(controller)
    knowledge = KnowledgeController(
        controller,
        knowledge_attachments,
        knowledge_rich_text,
        skey_previews=skey_previews,
        clock=server_updates.clock,
        user_model=users.users,
        draft_state=env_read_config(
            filename="drafts",
            unique_id="cache/knowledge",
            long_abs_path=True,
        ),
        config_queue=controller._config_write_queue,
    )
    controller.knowledge = knowledge
    knowledge.linkIndexChanged.connect(
        controller.update_workspace_knowledge_index
    )
    controller.attach_rich_text_navigation(skey_previews, knowledge)
    communication = CommunicationController(
        controller,
        note_attachments,
        config_queue=controller._config_write_queue,
        users=users.users,
        skey_previews=skey_previews,
        clock=server_updates.clock,
    )
    communication.attach_tasks_controller(tasks)
    work_hours = WorkHoursController(
        controller,
        tasks=tasks,
        users=users.users,
    )
    work_hours.attach_communication(communication)
    tasks.taskActivated.connect(communication.activate_task_context)
    controller.taskContextRequested.connect(communication.activate_task_context)
    communication.taskNoteCountsChanged.connect(tasks.update_task_note_counts)
    communication.noteCountChanged.connect(
        controller.update_workspace_note_count
    )
    messages = MessagesController(
        controller,
        chat_attachments,
        config_queue=controller._config_write_queue,
        users=users.users,
        skey_previews=skey_previews,
        clock=server_updates.clock,
    )
    knowledge.schemaInitialized.connect(
        messages.apply_schema_initialization
    )
    messages.schemaInitialized.connect(
        knowledge.apply_schema_initialization
    )
    messages.userProfileRequested.connect(users.open_profile)
    skey_previews.attach_navigation(
        messages=messages,
        users=users,
        communication=communication,
        knowledge=knowledge,
    )
    activity_feed = ActivityFeedController(
        controller,
        skey_previews,
        users=users.users,
        tasks=tasks,
        clock=server_updates.clock,
    )
    users.attach_activity_feed(activity_feed)
    messages.visibilityChanged.connect(server_updates.set_messages_visible)
    activity_feed.visibilityChanged.connect(server_updates.set_activity_enabled)
    tasks.advancedVisibilityChanged.connect(server_updates.set_tasks_visible)
    server_updates.batchReady.connect(core.server_cache.apply_server_batch)
    core.server_cache.invalidated.connect(messages.apply_cache_invalidation)
    core.server_cache.invalidated.connect(
        activity_feed.apply_cache_invalidation
    )
    server_updates.batchReady.connect(messages.apply_server_batch)
    server_updates.batchReady.connect(activity_feed.apply_server_batch)
    server_updates.batchReady.connect(tasks.apply_server_batch)
    server_updates.batchReady.connect(
        controller.apply_workspace_server_batch
    )
    server_updates.batchReady.connect(users.apply_server_batch)
    server_updates.batchReady.connect(quick_filter_editor.apply_server_batch)
    users.heartbeatIntervalChanged.connect(server_updates.set_presence_interval)
    server_updates.set_presence_interval(users.heartbeat_interval)
    server_updates.errorRaised.connect(
        lambda message, stacktrace: core.debug_log.raise_error(
            message,
            stacktrace=stacktrace,
            group="communication/server-updates",
        )
    )
    server_updates.warningRaised.connect(
        lambda message, stacktrace: core.debug_log.log(
            "WARNING",
            message,
            stacktrace=stacktrace,
            group="communication/server-updates",
            source="Server updates",
        )
    )
    return CollaborationBundle(
        emoji_catalog=emoji_catalog,
        users=users,
        layout_presets=layout_presets,
        sidebar_editor=sidebar_editor,
        administration=administration,
        quick_filter_editor=quick_filter_editor,
        skey_previews=skey_previews,
        sobject_info=sobject_info,
        chat_attachments=chat_attachments,
        note_attachments=note_attachments,
        knowledge_attachments=knowledge_attachments,
        knowledge_rich_text=knowledge_rich_text,
        knowledge=knowledge,
        communication=communication,
        work_hours=work_hours,
        messages=messages,
        activity_feed=activity_feed,
        server_updates=server_updates,
    )


def _build_delivery(
    app,
    project_root: Path,
    application_icon_path: Path,
    core: CoreBundle,
    task_bundle: TaskBundle,
    collaboration: CollaborationBundle,
    server_pool=None,
) -> DeliveryBundle:
    controller = core.controller
    columns_editor = ColumnsEditorController(controller, task_bundle.tasks)
    commit_queue = CommitQueueController(
        window_model=controller.window_model,
    )
    checkin_out = CheckinOutController(controller, commit_queue)
    collaboration.administration.typesEditor.attach_checkin_controller(checkin_out, commit_queue)
    collaboration.administration.schemaTypeEditor.attach_checkin_controller(checkin_out, commit_queue)
    collaboration.users.attach_checkin_controller(checkin_out)
    naming_editor = NamingEditorController(controller, checkin_out, commit_queue)
    collaboration.administration.attach_naming_editor(naming_editor)
    controller.server_state_changed.connect(naming_editor.server_changed)
    controller.window_model.windowVisibilityChanged.connect(naming_editor.window_visibility_changed)
    dcc_options = DccOptionsController(
        controller, controller.invoke_dcc_action
    )
    controller.dcc_options = dcc_options
    server_presets = ServerPresetsController(controller.workspace_state)
    screenshot = ScreenshotController(core.debug_log, commit_queue)
    script_editor = ScriptEditorController(controller, core.debug_log)
    collaboration.server_updates.batchReady.connect(
        script_editor.apply_server_batch
    )
    update = UpdateController(core.debug_log)
    handler_server = HandlerServerController(
        project_root,
        core.debug_log,
        dcc_preferences=read_dcc_preferences,
    )
    handler_server.attach_application(controller, checkin_out)
    script_editor.attach_dcc_bridge(handler_server)
    script_shelf = ScriptShelfController(
        controller,
        collaboration.users,
        script_editor,
        server_pool,
    )
    script_shelf.attach_dcc_bridge(handler_server)
    collaboration.sidebar_editor.attach_script_shelf(script_shelf)
    collaboration.server_updates.batchReady.connect(
        script_shelf.apply_server_batch
    )
    script_triggers = ScriptTriggerController(
        controller,
        collaboration.users,
        script_editor,
        server_pool,
        core.debug_log,
    )
    script_triggers.attach_dcc_bridge(handler_server)
    collaboration.server_updates.batchReady.connect(
        script_triggers.apply_server_batch
    )
    controller.attach_script_triggers(script_triggers)
    checkin_out.attach_script_triggers(script_triggers)
    core.sobject_delete.attach_script_triggers(script_triggers)
    core.sobject_duplicate.attach_script_triggers(script_triggers)
    task_bundle.tasks.attach_script_triggers(script_triggers)
    tray = TrayController(
        application_icon_path,
        controller.close_to_tray_enabled,
        app,
    )
    core.localization.languageChanged.connect(tray.retranslate)
    controller.attach_dcc_bridge(handler_server)
    checkin_out.attach_dcc_bridge(handler_server)
    dcc_options.attach_dcc_bridge(handler_server)
    notifications = NotificationController(
        controller,
        checkin_out,
        collaboration.communication,
        task_bundle.tasks,
        collaboration.messages,
        activity=collaboration.activity_feed,
    )
    tray.attach_notifications(notifications)
    commit_queue.attach_executor(checkin_out)
    _bind_current(handler_server.get_api())
    task_bundle.tasks.attach_commit_queue(commit_queue)
    matching_templates = MatchingTemplatesController()
    drop_plate = DropPlateController(
        controller,
        checkin_out,
        commit_queue,
        matching_templates,
    )
    controller.attach_checkin_workflow(checkin_out, drop_plate)
    ingest_files = IngestFilesController(controller, core.debug_log)
    controller.attach_ingest_workflow(ingest_files)
    watch_folders = WatchFoldersController(controller, checkin_out, commit_queue)
    controller.watch_folders = watch_folders
    return DeliveryBundle(
        columns_editor=columns_editor,
        commit_queue=commit_queue,
        checkin_out=checkin_out,
        naming_editor=naming_editor,
        dcc_options=dcc_options,
        server_presets=server_presets,
        screenshot=screenshot,
        script_editor=script_editor,
        script_shelf=script_shelf,
        script_triggers=script_triggers,
        update=update,
        handler_server=handler_server,
        tray=tray,
        notifications=notifications,
        matching_templates=matching_templates,
        drop_plate=drop_plate,
        ingest_files=ingest_files,
        watch_folders=watch_folders,
    )


@dataclass(frozen=True)
class ConfigurationBridge:
    """Named configuration ownership callbacks for the editor facade."""

    core: CoreBundle
    tasks: TaskBundle
    collaboration: CollaborationBundle
    delivery: DeliveryBundle

    def global_values(self) -> dict[str, Any]:
        return self.core.controller.configuration_global_values()

    def apply_global(self, values: dict[str, Any]) -> None:
        self.core.controller.apply_global_configuration(values)

    def appearance_values(self) -> dict[str, Any]:
        return {
            **self.core.controller.configuration_appearance_values(),
            "language": self.core.localization.current_language,
        }

    def apply_appearance(self, values: dict[str, Any]) -> None:
        self.core.localization.set_language(values.get("language"))
        # Install the selected translator before controller notifications are
        # emitted, including restart-required rendering changes.
        self.core.controller.apply_appearance_configuration(values)

    def reload_repository_configuration(self) -> None:
        self.core.controller.refresh_checkin_defaults()
        self.delivery.checkin_out.reload_repository_configuration()
        self.delivery.commit_queue.reload_repository_configuration()
        self.delivery.drop_plate.reload_configuration()
        self.core.controller.repository_sync.reload_configuration()

    def checkin_values(self) -> dict[str, Any]:
        controller = self.core.controller
        return {
            "loadingMode": controller.loading_mode,
            "snapshotShowAll": controller.snapshot_browser_show_all,
            "snapshotShowMore": controller.snapshot_browser_show_more,
            "snapshotContentMode": controller.snapshot_browser_content_mode,
            "snapshotOrientation": controller.snapshot_browser_orientation,
            "commitQueueAutoClean": self.delivery.commit_queue.autoClean,
        }

    def apply_checkin(self, values: dict[str, Any]) -> None:
        controller = self.core.controller
        controller.set_loading_mode(str(values.get("loadingMode") or "pages"))
        for option, key, current in (
            ("all", "snapshotShowAll", controller.snapshot_browser_show_all),
            ("more", "snapshotShowMore", controller.snapshot_browser_show_more),
        ):
            if bool(values.get(key)) != current:
                controller.toggle_snapshot_browser_option(option)
        controller.set_snapshot_browser_content_mode(
            str(values.get("snapshotContentMode") or "both")
        )
        controller.set_snapshot_browser_orientation(
            str(values.get("snapshotOrientation") or "horizontal")
        )
        self.delivery.commit_queue.set_auto_clean(
            bool(values.get("commitQueueAutoClean"))
        )
        self.reload_repository_configuration()

    def task_values(self) -> dict[str, Any]:
        return {
            **self.tasks.tasks.configuration_values(),
            "inspectorExpanded": self.collaboration.communication.taskExpanded,
        }

    def apply_tasks(self, values: dict[str, Any]) -> None:
        self.tasks.tasks.apply_configuration(values)
        self.collaboration.communication.set_task_expanded(
            bool(values.get("inspectorExpanded"))
        )

    def cache_values(self) -> dict[str, bool]:
        return {
            **self.core.server_cache.configuration_values(),
            **self.core.controller.configuration_workspace_cache_values(),
        }

    def apply_cache(self, values: dict[str, Any]) -> None:
        self.core.server_cache.apply_configuration(values)
        self.core.controller.apply_workspace_cache_configuration(values)

    def connection_values(self) -> dict[str, int]:
        return {
            "pingInterval": self.core.controller.ping_interval,
            "serverUpdateInterval": self.collaboration.server_updates.poll_interval,
            "presenceHeartbeatInterval": self.collaboration.users.heartbeat_interval,
        }

    def apply_connection(self, values: dict[str, Any]) -> None:
        self.core.controller.set_ping_interval(
            int(values.get("pingInterval", 0))
        )
        self.collaboration.server_updates.set_poll_interval(
            int(values.get("serverUpdateInterval", 30))
        )
        self.collaboration.users.set_heartbeat_interval(
            int(values.get("presenceHeartbeatInterval", 120))
        )


def _build_editors(
    core: CoreBundle,
    task_bundle: TaskBundle,
    collaboration: CollaborationBundle,
    delivery: DeliveryBundle,
) -> EditorBundle:
    controller = core.controller
    settings = ConfigurationBridge(core, task_bundle, collaboration, delivery)
    configuration = ConfigurationController(
        controller.apply_server_configuration,
        controller.notify,
        settings.global_values,
        settings.apply_global,
        controller.flush_search_cache,
        settings.apply_checkin,
        settings.task_values,
        settings.apply_tasks,
        settings.connection_values,
        settings.apply_connection,
        settings.cache_values,
        settings.apply_cache,
        core.server_cache.clear_all,
        appearance_values=settings.appearance_values,
        apply_appearance_configuration=settings.apply_appearance,
        checkin_values=settings.checkin_values,
    )
    repository = RepositoryEditorController(
        delivery.checkin_out,
        controller.workspace_state,
    )
    repository.saved.connect(
        delivery.commit_queue.reload_repository_configuration
    )
    filters = FilterEditorController(
        controller.workspace_state.filter_model.records,
        controller.workspace_state.filter_column_model.records,
        controller.search_filter_relations,
        controller.notify,
        controller.has_active_search_tab,
        controller.filter_editor_context,
        controller.stage_filter_editor_records,
    )
    filters.presetsChanged.connect(
        collaboration.sidebar_editor.invalidate_search_presets
    )
    collaboration.sidebar_editor.attach_filter_editor(filters)
    process_filters = ProcessFilterEditorController(
        controller.filter_editor_context,
        controller.apply_process_filter_settings,
        controller.notify,
    )
    controller.processFilterEditorRequested.connect(
        process_filters.begin_session
    )
    repository_sync = RepositorySyncEditorController(
        controller.repository_sync_editor_context,
        controller.repository_sync,
        controller.notify,
        core.debug_log,
    )
    controller.repositorySyncEditorRequested.connect(repository_sync.begin_session)
    sobject = SObjectEditorController(
        controller.sobject_editor_context,
        controller.notify,
        checkin=delivery.checkin_out,
    )
    sobject.attach_script_triggers(delivery.script_triggers)
    controller.sobjectEditorRequested.connect(sobject.begin_session)
    project = ProjectEditorController(
        controller.project_editor_context,
        delivery.checkin_out,
        controller.notify,
    )
    controller.projectEditRequested.connect(project.begin_session)
    links = SObjectLinkController(
        controller.sobject_link_context,
        controller.notify,
        controller.repository_sync,
    )
    links.attach_script_triggers(delivery.script_triggers)
    controller.sobjectLinkRequested.connect(links.begin_session)
    return EditorBundle(
        configuration=configuration,
        repository=repository,
        filters=filters,
        process_filters=process_filters,
        repository_sync=repository_sync,
        sobject=sobject,
        project=project,
        links=links,
    )


def _wire_presentation_lifecycle(
    core: CoreBundle,
    task_bundle: TaskBundle,
    collaboration: CollaborationBundle,
    delivery: DeliveryBundle,
) -> None:
    """Keep retained QML loaders from defining controller visibility."""
    docks = core.controller.dock_model
    windows = core.controller.window_model
    dcc_option_windows = {"dcc_options"}

    def sync_checkin_presentation() -> None:
        visible = docks.is_panel_presented("drop_plate") or any(
            windows.is_window_visible(window_id)
            for window_id in (
                "matching_templates", "naming_editor", *dcc_option_windows,
            )
        )
        delivery.checkin_out.set_selection_presentation_visible(visible)

    def dock_presentation_changed(panel_id: str, presented: bool) -> None:
        if panel_id in {"tasks", "task_calendar"}:
            task_bundle.tasks.sync_presentation()
        elif panel_id == "snapshot":
            core.controller.workspace_state.set_snapshot_presentation_visible(
                presented
            )
        elif panel_id == "notes":
            task_bundle.tasks.sync_presentation()
            core.controller.workspace_state.set_detail_presentation_visible(
                presented
            )
            collaboration.communication.set_visible(presented)
            collaboration.work_hours.set_task_context_visible(presented)
        elif panel_id == "drop_plate":
            sync_checkin_presentation()
        elif panel_id == "knowledge":
            collaboration.knowledge.set_visible(presented)

    def window_visibility_changed(window_id: str, visible: bool) -> None:
        if window_id == "activity_feed":
            collaboration.activity_feed.set_visible(visible)
        elif window_id == "notifications":
            delivery.notifications.set_visible(visible)
        elif window_id == "debug_log":
            core.debug_log.set_visible(visible)
        elif window_id == "ui_performance":
            core.controller.ui_performance.set_visible(visible)
        elif window_id in {"watch_folders", "watch_folder_editor"}:
            delivery.watch_folders.set_presentation_visible(
                any(
                    windows.is_window_visible(candidate)
                    for candidate in (
                        "watch_folders", "watch_folder_editor",
                    )
                )
            )
        if window_id in {
            "matching_templates", "naming_editor", *dcc_option_windows,
        }:
            sync_checkin_presentation()

    docks.panelPresentationChanged.connect(dock_presentation_changed)
    windows.windowVisibilityChanged.connect(window_visibility_changed)
    for panel_id in (
        "tasks", "task_calendar", "snapshot", "notes", "drop_plate",
        "knowledge",
    ):
        dock_presentation_changed(
            panel_id, docks.is_panel_presented(panel_id)
        )
    for window_id in (
        "activity_feed", "notifications", "debug_log",
        "watch_folders", "watch_folder_editor",
    ):
        window_visibility_changed(
            window_id, windows.is_window_visible(window_id)
        )


def build_application_runtime(
    app,
    project_root: Path,
    application_icon_path: Path,
    *,
    diagnostics_root: Path | None = None,
    server_pool=None,
) -> ApplicationRuntime:
    """Build the application graph without starting background work."""

    core = _build_core(app, project_root, diagnostics_root)
    tasks = _build_tasks(core)
    collaboration = _build_collaboration(core, tasks, project_root)
    delivery = _build_delivery(
        app,
        project_root,
        application_icon_path,
        core,
        tasks,
        collaboration,
        server_pool,
    )
    editors = _build_editors(core, tasks, collaboration, delivery)
    _wire_presentation_lifecycle(
        core, tasks, collaboration, delivery
    )

    bindings = QmlBindingRegistry()
    bindings.add_group("core", core.qml_bindings())
    bindings.add_group("tasks", tasks.qml_bindings())
    bindings.add_group("collaboration", collaboration.qml_bindings())
    bindings.add_group("delivery", delivery.qml_bindings())
    bindings.add_group("editors", editors.qml_bindings())

    lifecycle = LifecycleRegistry()
    lifecycle.add_services(
        (
            collaboration.server_updates,
            collaboration.administration,
            delivery.naming_editor,
            delivery.columns_editor,
            core.server_cache,
            tasks.tasks,
            collaboration.work_hours,
            collaboration.sobject_info,
            collaboration.messages,
            collaboration.communication,
            collaboration.chat_attachments,
            collaboration.note_attachments,
            collaboration.knowledge,
            collaboration.knowledge_attachments,
            delivery.watch_folders,
            delivery.ingest_files,
            delivery.screenshot,
            delivery.script_editor,
            delivery.script_shelf,
            delivery.script_triggers,
            delivery.handler_server,
            delivery.notifications,
            delivery.commit_queue,
            core.controller,
            core.debug_log,
        )
    )
    return ApplicationRuntime(
        controller=core.controller,
        localization=core.localization,
        debug_log=core.debug_log,
        tray=delivery.tray,
        handler_server=delivery.handler_server,
        server_updates=collaboration.server_updates,
        watch_folders=delivery.watch_folders,
        script_editor=delivery.script_editor,
        bindings=bindings,
        lifecycle=lifecycle,
        bundles=(core, tasks, collaboration, delivery, editors),
    )

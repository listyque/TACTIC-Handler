"""PySide6/QML entry point; legacy launchers remain untouched."""

from __future__ import annotations

import sys
import os
import re
import threading
import traceback
from pathlib import Path

# The modern application and its legacy-compatible core must share one Qt
# runtime. Prevent a host environment from making thlib.side.Qt load PySide2
# or PyQt alongside the PySide6 QML engine.
os.environ["QT_PREFERRED_BINDING"] = "PySide6"

# Keep rendering away from the GUI thread during interactive window resizing.
# The old forced "basic" loop rendered synchronously and made every complex
# QML layout visibly stall while the native resize gesture was in progress.
os.environ.setdefault("QSG_RENDER_LOOP", "threaded")

from PySide6.QtCore import (
    QEvent,
    QObject,
    QSettings,
    QTimer,
    QUrl,
    Qt,
    QtMsgType,
    Signal,
    qInstallMessageHandler,
)
from PySide6.QtGui import QFont, QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWidgets import QApplication

from modern_ui.controller import ApplicationController
from modern_ui.configuration import ConfigurationController
from modern_ui.checkin_out import CheckinOutController
from modern_ui.commit_queue import CommitQueueController
from modern_ui.drop_plate import DropPlateController
from modern_ui.matching_templates import MatchingTemplatesController
from modern_ui.maya_options import MayaOptionsController
from modern_ui.repository_editor import RepositoryEditorController
from modern_ui.repository_sync_editor import RepositorySyncEditorController
from modern_ui.watch_folders import WatchFoldersController
from modern_ui.update_controller import UpdateController
from modern_ui.tasks import TasksController
from modern_ui.milestones import MilestoneController
from modern_ui.work_hours import WorkHoursController
from modern_ui.communication import CommunicationController
from modern_ui.communication_feed import (
    ActivityFeedController,
    MessagesController,
)
from modern_ui.message_attachments import (
    AttachmentUploadController,
    ChatAttachmentController,
)
from modern_ui.notifications import NotificationController
from modern_ui.server_updates import ServerUpdateService
from modern_ui.columns_editor import ColumnsEditorController
from modern_ui.editor_tools import (
    ScreenshotController,
    ServerPresetsController,
)
from modern_ui.script_editor import ScriptEditorController
from modern_ui.debug_logging import DebugLogController
from modern_ui.filter_editor import FilterEditorController
from modern_ui.process_filter_editor import ProcessFilterEditorController
from modern_ui.quick_filter_editor import QuickFilterEditorController
from modern_ui.icon_font import (
    fontawesome_assets,
    material_design_icon_assets,
)
from modern_ui.sobject_editor import SObjectEditorController
from modern_ui.sobject_link import SObjectLinkController
from modern_ui.handler_server_controller import HandlerServerController
from modern_ui.tray import TrayController
from modern_ui.user import UserController
from modern_ui.skey_previews import SearchKeyPreviewResolver
from modern_ui.naming_editor import NamingEditorController
from modern_ui.localization import LocalizationController
from modern_ui.sidebar_editor import SidebarEditorController
from modern_ui.sobject_info import SObjectInfoController


def _is_fixedsys_directwrite_warning(message: str) -> bool:
    lowered = str(message or "").lower()
    return (
        "directwrite: createfontfacefromhdc() failed" in lowered
        and 'family="fixedsys"' in lowered
    )


def _bootstrap_message_handler(_message_type, _context, message) -> None:
    if _is_fixedsys_directwrite_warning(message):
        return
    sys.stderr.write(str(message or "") + "\n")
    sys.stderr.flush()


class FixedsysFontGuard(QObject):
    def eventFilter(self, watched, event) -> bool:
        if event.type() not in {
            QEvent.Type.Polish,
            QEvent.Type.Show,
            QEvent.Type.FontChange,
        } or not hasattr(watched, "font"):
            return False
        font = watched.font()
        if font.family().strip().lower() != "fixedsys":
            return False
        replacement = QFont(font)
        replacement.setFamily("Consolas")
        watched.setFont(replacement)
        return False


class QtRuntimeLogBridge(QObject):
    message_received = Signal(str)
    flush_requested = Signal()

    _IMAGE_NOT_FOUND_KEY = "qml/image-not-found"

    def __init__(self) -> None:
        super().__init__()
        self._pending_lock = threading.Lock()
        self._pending = {}
        self._flush_pending = False
        self._image_not_found_reported = False
        self.flush_requested.connect(
            self._schedule_flush,
            Qt.ConnectionType.QueuedConnection,
        )

    def enqueue(self, message: str) -> None:
        """Coalesce renderer/network diagnostics before touching GUI models."""
        message = str(message or "").strip()
        if not message:
            return
        lowered = message.lower()
        image_not_found = (
            "qquickimage" in lowered
            and "server replied: not found" in lowered
        )
        key = self._IMAGE_NOT_FOUND_KEY if image_not_found else message
        wake = False
        with self._pending_lock:
            bucket = self._pending.setdefault(
                key,
                {"message": message, "count": 0, "samples": []},
            )
            bucket["count"] += 1
            if image_not_found and len(bucket["samples"]) < 5:
                match = re.search(
                    r"Error transferring\s+(.+?)\s+-\s+server replied",
                    message,
                    flags=re.IGNORECASE,
                )
                sample = match.group(1) if match else message
                if sample not in bucket["samples"]:
                    bucket["samples"].append(sample)
            if not self._flush_pending:
                self._flush_pending = True
                wake = True
        if wake:
            self.flush_requested.emit()

    def _schedule_flush(self) -> None:
        QTimer.singleShot(500, self._flush)

    def _flush(self) -> None:
        with self._pending_lock:
            pending = self._pending
            self._pending = {}
            self._flush_pending = False
        for key, bucket in pending.items():
            count = int(bucket["count"])
            if key == self._IMAGE_NOT_FOUND_KEY:
                if self._image_not_found_reported:
                    continue
                samples = bucket["samples"]
                details = "; ".join(samples)
                suffix = f" Examples: {details}" if details else ""
                message = (
                    "MISSING · QML · QQuickImage: "
                    f"{count} image request{'s' if count != 1 else ''} "
                    f"returned Not Found.{suffix}"
                )
            else:
                message = bucket["message"]
                if count > 1:
                    message += f" (repeated {count} times)"
            self.message_received.emit(message)
            if key == self._IMAGE_NOT_FOUND_KEY:
                self._image_not_found_reported = True


def main() -> int:
    smoke_offline = os.environ.get("TACTIC_QML_SMOKE_OFFLINE", "") == "1"
    test_settings_dir = os.environ.get("TACTIC_QML_TEST_SETTINGS_DIR", "")
    if test_settings_dir:
        settings_path = Path(test_settings_dir).resolve()
        settings_path.mkdir(parents=True, exist_ok=True)
        QSettings.setDefaultFormat(QSettings.Format.IniFormat)
        QSettings.setPath(
            QSettings.Format.IniFormat,
            QSettings.Scope.UserScope,
            str(settings_path),
        )
    QQuickStyle.setStyle("Material")
    # Use the Windows/DirectWrite rasterizer so small desktop text retains the
    # platform's native hinting and antialiasing. Dock layers are suspended
    # while geometry changes, preventing resize-time texture resampling from
    # making these native glyphs jump between physical pixels.
    QQuickWindow.setTextRenderType(
        QQuickWindow.TextRenderType.NativeTextRendering
    )
    # Qt 6 can resolve the Windows fixed-pitch fallback to the bitmap-only
    # Fixedsys face, which DirectWrite cannot instantiate.
    QFont.insertSubstitution("Fixedsys", "Consolas")
    qInstallMessageHandler(_bootstrap_message_handler)
    # QApplication is a strict superset of QGuiApplication.  The QML shell
    # uses it normally, while QWidget-based schema editors remain available.
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app.setApplicationName("TacticHandler_Client")
    from thlib.environment import env_inst

    # Both launchers share the same pools; QML must start them before any
    # controller can enqueue validation, repository or check-in work.
    env_inst.ui_super = app
    env_inst.start_pools()
    app.styleHints().setWheelScrollLines(6)
    application_font = QFont("Segoe UI")
    application_font.setPointSizeF(9.75)
    app.setFont(application_font)
    fixedsys_font_guard = FixedsysFontGuard(app)
    app.installEventFilter(fixedsys_font_guard)
    application_icon_path = (
        Path(__file__).parent / "thlib" / "ui" / "gliph"
        / "tactic_favicon.ico"
    )
    if application_icon_path.is_file():
        app.setWindowIcon(QIcon(str(application_icon_path)))
    app.setQuitOnLastWindowClosed(False)
    localization_controller = LocalizationController(app)
    debug_log = DebugLogController(Path(__file__).parent)
    debug_log.install()
    controller = ApplicationController(debug_log=debug_log)
    tasks_controller = TasksController(controller)
    milestone_controller = MilestoneController(controller)
    tasks_controller.attach_milestone_controller(milestone_controller)
    user_controller = UserController(controller)
    sidebar_editor_controller = SidebarEditorController(
        controller, user_controller
    )
    quick_filter_editor_controller = QuickFilterEditorController(
        controller, user_controller
    )
    user_controller.attach_tasks_controller(tasks_controller)
    skey_preview_resolver = SearchKeyPreviewResolver(controller)
    user_controller.attach_skey_previews(skey_preview_resolver)
    sobject_info_controller = SObjectInfoController(
        controller,
        users=user_controller,
        navigation=skey_preview_resolver,
    )
    chat_attachment_controller = ChatAttachmentController(controller)
    note_attachment_controller = AttachmentUploadController(controller)
    communication_controller = CommunicationController(
        controller,
        note_attachment_controller,
        users=user_controller.users,
        skey_previews=skey_preview_resolver,
    )
    communication_controller.attach_tasks_controller(tasks_controller)
    work_hours_controller = WorkHoursController(
        controller, tasks=tasks_controller, users=user_controller.users
    )
    work_hours_controller.attach_communication(communication_controller)
    tasks_controller.taskActivated.connect(
        communication_controller.activate_task_context
    )
    communication_controller.noteCountChanged.connect(
        tasks_controller.update_note_count
    )
    messages_controller = MessagesController(
        controller,
        chat_attachment_controller,
        users=user_controller.users,
        skey_previews=skey_preview_resolver,
    )
    messages_controller.userProfileRequested.connect(
        user_controller.open_profile
    )
    skey_preview_resolver.attach_navigation(
        messages=messages_controller,
        users=user_controller,
        communication=communication_controller,
    )
    activity_feed_controller = ActivityFeedController(
        controller, messages_controller, skey_preview_resolver
    )
    server_update_service = ServerUpdateService(controller)
    messages_controller.visibilityChanged.connect(
        server_update_service.set_messages_visible
    )
    activity_feed_controller.visibilityChanged.connect(
        server_update_service.set_activity_enabled
    )
    tasks_controller.advancedVisibilityChanged.connect(
        server_update_service.set_tasks_visible
    )
    server_update_service.batchReady.connect(
        messages_controller.apply_server_batch
    )
    server_update_service.batchReady.connect(
        activity_feed_controller.apply_server_batch
    )
    server_update_service.batchReady.connect(
        tasks_controller.apply_server_batch
    )
    server_update_service.batchReady.connect(
        user_controller.apply_server_batch
    )
    user_controller.heartbeatIntervalChanged.connect(
        server_update_service.set_presence_interval
    )
    server_update_service.set_presence_interval(
        user_controller.heartbeat_interval
    )
    server_update_service.errorRaised.connect(
        lambda message, stacktrace: debug_log.raise_error(
            message,
            stacktrace=stacktrace,
            group="communication/server-updates",
        )
    )
    server_update_service.warningRaised.connect(
        lambda message, stacktrace: debug_log.log(
            "WARNING",
            message,
            stacktrace=stacktrace,
            group="communication/server-updates",
            source="Server updates",
        )
    )
    columns_editor_controller = ColumnsEditorController(controller)
    commit_queue_controller = CommitQueueController()
    checkin_out_controller = CheckinOutController(
        controller, commit_queue_controller
    )
    user_controller.attach_checkin_controller(checkin_out_controller)
    naming_editor_controller = NamingEditorController(
        controller, checkin_out_controller, commit_queue_controller
    )
    maya_options_controller = MayaOptionsController(
        checkin_out_controller
    )
    server_presets_controller = ServerPresetsController(
        controller.workspace_state
    )
    screenshot_controller = ScreenshotController(
        checkin_out_controller, debug_log, commit_queue_controller
    )
    script_editor_controller = ScriptEditorController(
        controller, debug_log
    )
    update_controller = UpdateController(debug_log)
    handler_server_controller = HandlerServerController(
        Path(__file__).parent, debug_log
    )
    handler_server_controller.attach_application(
        controller, checkin_out_controller
    )
    tray_controller = TrayController(application_icon_path, app)
    controller.attach_dcc_bridge(handler_server_controller)
    checkin_out_controller.attach_dcc_bridge(handler_server_controller)
    notification_controller = NotificationController(
        controller, checkin_out_controller, communication_controller,
        tasks_controller, messages_controller,
    )
    commit_queue_controller.attach_executor(checkin_out_controller)
    tasks_controller.attach_commit_queue(commit_queue_controller)
    matching_templates_controller = MatchingTemplatesController()
    drop_plate_controller = DropPlateController(
        controller,
        checkin_out_controller,
        commit_queue_controller,
        matching_templates_controller,
    )
    controller.attach_checkin_workflow(
        checkin_out_controller, drop_plate_controller
    )
    watch_folders_controller = WatchFoldersController(
        controller, checkin_out_controller, commit_queue_controller
    )
    controller.watch_folders = watch_folders_controller
    configuration_controller = ConfigurationController(
        controller.apply_server_configuration,
        controller._notify,
        lambda: {
            **controller.configuration_global_values(),
            "language": localization_controller.current_language,
        },
        lambda values: (
            controller.apply_global_configuration(values),
            localization_controller.set_language(values.get("language")),
        ),
        controller.flush_search_cache,
        lambda: (
            controller.refresh_checkin_defaults(),
            checkin_out_controller.reload_repository_configuration(),
            drop_plate_controller.reload_configuration(),
            controller.repository_sync.reload_configuration(),
        ),
        lambda: {
            **tasks_controller.configuration_values(),
            "inspectorExpanded": communication_controller.taskExpanded,
        },
        lambda values: (
            tasks_controller.apply_configuration(values),
            communication_controller.set_task_expanded(
                bool(values.get("inspectorExpanded"))
            ),
        ),
        lambda: {
            "pingInterval": controller.ping_interval,
            "serverUpdateInterval": server_update_service.poll_interval,
            "presenceHeartbeatInterval": user_controller.heartbeat_interval,
        },
        lambda values: (
            controller.set_ping_interval(int(values.get("pingInterval", 0))),
            server_update_service.set_poll_interval(
                int(values.get("serverUpdateInterval", 30))
            ),
            user_controller.set_heartbeat_interval(
                int(values.get("presenceHeartbeatInterval", 120))
            ),
        ),
    )
    repository_editor_controller = RepositoryEditorController(
        checkin_out_controller, controller.workspace_state
    )
    filter_editor_controller = FilterEditorController(
        lambda: controller.workspace_state.filter_model._records,
        lambda: controller.workspace_state.filter_column_model._records,
        controller.search_filter_relations,
        controller._notify,
        controller.has_active_search_tab,
        controller.filter_editor_context,
        controller.stage_filter_editor_records,
    )
    filter_editor_controller.presetsChanged.connect(
        sidebar_editor_controller.invalidate_search_presets
    )
    sidebar_editor_controller.attach_filter_editor(
        filter_editor_controller
    )
    process_filter_editor_controller = ProcessFilterEditorController(
        controller.filter_editor_context,
        controller.apply_process_filter_settings,
        controller._notify,
    )
    repository_sync_editor_controller = RepositorySyncEditorController(
        controller.repository_sync_editor_context,
        controller.repository_sync,
        controller._notify,
        debug_log,
    )
    controller.repositorySyncEditorRequested.connect(
        repository_sync_editor_controller.begin_session
    )
    sobject_editor_controller = SObjectEditorController(
        controller.sobject_editor_context,
        controller._notify,
    )
    sobject_link_controller = SObjectLinkController(
        controller.sobject_link_context,
        controller._notify,
        controller.repository_sync,
    )
    runtime_log_bridge = QtRuntimeLogBridge()
    runtime_log_bridge.message_received.connect(
        controller.log_runtime_message
    )

    previous_message_handler = None

    def runtime_message_handler(message_type, context, message) -> None:
        message_text = str(message or "").strip()
        lowered = message_text.lower()
        if _is_fixedsys_directwrite_warning(message_text):
            return
        # Windows temporarily locks the system clipboard while another
        # process owns it. Qt retries automatically; this line is not an
        # application failure and otherwise floods both diagnostics surfaces.
        if lowered == "retrying to obtain clipboard.":
            return
        if message_type in {
            QtMsgType.QtWarningMsg,
            QtMsgType.QtCriticalMsg,
            QtMsgType.QtFatalMsg,
        }:
            is_error = (
                message_type
                in {QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg}
                or "error" in lowered
                or "failed" in lowered
                or "cannot " in lowered
            )
            level = "ERROR" if is_error else "WARNING"
            category = str(getattr(context, "category", "") or "")
            source = "QML" if ".qml" in lowered or "qquick" in lowered else "Qt"
            if category and category != "default":
                source = f"{source}/{category}"
            runtime_log_bridge.enqueue(
                f"{level} · {source} · {message_text}"
            )
            # A failed preview may produce hundreds of renderer warnings.
            # The bridge writes one aggregated terminal/log entry instead.
            if (
                "qquickimage" in lowered
                and "server replied: not found" in lowered
            ):
                return

        # Installing a handler must not make diagnostics disappear from the
        # terminal where developers traditionally inspect TACTIC-Handler.
        if previous_message_handler:
            previous_message_handler(message_type, context, message)
        elif message_text:
            sys.stderr.write(message_text + "\n")
            sys.stderr.flush()

    previous_message_handler = qInstallMessageHandler(
        runtime_message_handler
    )
    shutdown_complete = False

    def shutdown() -> None:
        nonlocal shutdown_complete
        if shutdown_complete:
            return
        shutdown_complete = True
        server_update_service.shutdown()
        tasks_controller.shutdown()
        work_hours_controller.shutdown()
        chat_attachment_controller.shutdown()
        note_attachment_controller.shutdown()
        watch_folders_controller.shutdown()
        screenshot_controller.shutdown()
        handler_server_controller.shutdown()
        notification_controller.shutdown()
        commit_queue_controller.shutdown()
        controller.shutdown()
        debug_log.shutdown()

    engine = QQmlApplicationEngine()
    localization_controller.attach_engine(engine)
    qml_errors = []

    def destroy_qml() -> None:
        for root_object in engine.rootObjects():
            root_object.deleteLater()
        QApplication.sendPostedEvents(
            None, QEvent.Type.DeferredDelete
        )
        engine.deleteLater()
        QApplication.sendPostedEvents(
            None, QEvent.Type.DeferredDelete
        )

    def collect_qml_warnings(warnings) -> None:
        qml_errors.extend(str(warning.toString()) for warning in warnings)

    engine.warnings.connect(collect_qml_warnings)
    (
        solid_icon_glyphs,
        solid_icon_font_family,
        regular_icon_glyphs,
        regular_icon_font_family,
    ) = fontawesome_assets(Path(__file__).parent)
    engine.rootContext().setContextProperty(
        "fontAwesomeSolidGlyphs", solid_icon_glyphs
    )
    engine.rootContext().setContextProperty(
        "fontAwesomeSolidFontFamily", solid_icon_font_family
    )
    engine.rootContext().setContextProperty(
        "fontAwesomeRegularGlyphs", regular_icon_glyphs
    )
    engine.rootContext().setContextProperty(
        "qmlSmokeMode", bool(smoke_offline)
    )
    engine.rootContext().setContextProperty(
        "fontAwesomeRegularFontFamily", regular_icon_font_family
    )
    material_icon_glyphs, material_icon_font_family = (
        material_design_icon_assets(Path(__file__).parent)
    )
    engine.rootContext().setContextProperty(
        "materialDesignIconGlyphs", material_icon_glyphs
    )
    engine.rootContext().setContextProperty(
        "materialDesignIconFontFamily", material_icon_font_family
    )
    engine.rootContext().setContextProperty(
        "applicationIconUrl",
        QUrl.fromLocalFile(str(application_icon_path))
        if application_icon_path.is_file() else QUrl(),
    )
    engine.rootContext().setContextProperty("trayController", tray_controller)
    engine.rootContext().setContextProperty("appController", controller)
    engine.rootContext().setContextProperty("userController", user_controller)
    engine.rootContext().setContextProperty(
        "sidebarEditorController", sidebar_editor_controller
    )
    engine.rootContext().setContextProperty(
        "sidebarEntryModel", sidebar_editor_controller.entries
    )
    engine.rootContext().setContextProperty(
        "sidebarSecurityGroupModel", sidebar_editor_controller.security_groups
    )
    engine.rootContext().setContextProperty(
        "serverUpdateService", server_update_service
    )
    engine.rootContext().setContextProperty(
        "quickFilterEditorController", quick_filter_editor_controller
    )
    engine.rootContext().setContextProperty("userListModel", user_controller.users)
    engine.rootContext().setContextProperty("userTaskModel", user_controller.tasks)
    engine.rootContext().setContextProperty("userActivityModel", user_controller.activity)
    engine.rootContext().setContextProperty("userGroupModel", user_controller.groups)
    engine.rootContext().setContextProperty(
        "sobjectInfoController", sobject_info_controller
    )
    engine.rootContext().setContextProperty(
        "sobjectTaskStatusModel", sobject_info_controller.task_statuses
    )
    engine.rootContext().setContextProperty(
        "sobjectTaskProcessModel", sobject_info_controller.task_processes
    )
    engine.rootContext().setContextProperty(
        "sobjectTaskModel", sobject_info_controller.tasks
    )
    engine.rootContext().setContextProperty(
        "sobjectParticipantModel", sobject_info_controller.participants
    )
    engine.rootContext().setContextProperty(
        "sobjectSnapshotModel", sobject_info_controller.snapshots
    )
    engine.rootContext().setContextProperty(
        "sobjectFileModel", sobject_info_controller.files
    )
    engine.rootContext().setContextProperty(
        "sobjectActivityModel", sobject_info_controller.activity
    )
    engine.rootContext().setContextProperty(
        "sobjectPropertyModel", sobject_info_controller.properties
    )
    engine.rootContext().setContextProperty(
        "tasksController", tasks_controller
    )
    engine.rootContext().setContextProperty(
        "milestoneController", milestone_controller
    )
    engine.rootContext().setContextProperty(
        "milestoneModel", milestone_controller.model
    )
    engine.rootContext().setContextProperty(
        "taskProcessModel", tasks_controller.process_model
    )
    engine.rootContext().setContextProperty(
        "advancedTaskModel", tasks_controller.advanced_model
    )
    engine.rootContext().setContextProperty(
        "advancedTaskTableModel", tasks_controller.table_model
    )
    engine.rootContext().setContextProperty(
        "taskGanttModel", tasks_controller.gantt_model
    )
    engine.rootContext().setContextProperty(
        "taskCalendarModel", tasks_controller.calendar_model
    )
    engine.rootContext().setContextProperty(
        "taskHistoryModel", tasks_controller.history_model
    )
    engine.rootContext().setContextProperty(
        "workHoursController", work_hours_controller
    )
    engine.rootContext().setContextProperty(
        "workHourModel", work_hours_controller.entries
    )
    engine.rootContext().setContextProperty(
        "timesheetModel", work_hours_controller.timesheet_entries
    )
    engine.rootContext().setContextProperty(
        "workReportModel", work_hours_controller.report_descriptors
    )
    engine.rootContext().setContextProperty(
        "workReportValueModel", work_hours_controller.report_values
    )
    engine.rootContext().setContextProperty(
        "communicationController", communication_controller
    )
    engine.rootContext().setContextProperty(
        "noteAttachments", note_attachment_controller
    )
    engine.rootContext().setContextProperty(
        "noteAttachmentDraftModel", note_attachment_controller.model
    )
    engine.rootContext().setContextProperty(
        "messagesController", messages_controller
    )
    engine.rootContext().setContextProperty(
        "messageConversationModel", messages_controller.conversations
    )
    engine.rootContext().setContextProperty(
        "tacticMessageModel", messages_controller.messages
    )
    engine.rootContext().setContextProperty(
        "messageAttachments", chat_attachment_controller
    )
    engine.rootContext().setContextProperty(
        "messageAttachmentDraftModel", chat_attachment_controller.model
    )
    engine.rootContext().setContextProperty(
        "activityFeedController", activity_feed_controller
    )
    engine.rootContext().setContextProperty(
        "activityFeedModel", activity_feed_controller.model
    )
    engine.rootContext().setContextProperty(
        "columnsEditorController", columns_editor_controller
    )
    engine.rootContext().setContextProperty(
        "columnsEditorModel", columns_editor_controller.model
    )
    engine.rootContext().setContextProperty(
        "serverPresetsController", server_presets_controller
    )
    engine.rootContext().setContextProperty(
        "serverPresetsModel", server_presets_controller.model
    )
    engine.rootContext().setContextProperty(
        "screenshotController", screenshot_controller
    )
    engine.rootContext().setContextProperty(
        "scriptEditorController", script_editor_controller
    )
    engine.rootContext().setContextProperty(
        "scriptEditorModel", script_editor_controller.model
    )
    engine.rootContext().setContextProperty(
        "scriptEditorTabModel", script_editor_controller.tabs
    )
    engine.rootContext().setContextProperty(
        "updateController", update_controller
    )
    engine.rootContext().setContextProperty(
        "updateModel", update_controller.model
    )
    engine.rootContext().setContextProperty(
        "handlerServerController", handler_server_controller
    )
    engine.rootContext().setContextProperty(
        "handlerClientModel", handler_server_controller.clients
    )
    engine.rootContext().setContextProperty(
        "handlerCapabilityModel", handler_server_controller.capabilities
    )
    engine.rootContext().setContextProperty(
        "handlerResultModel", handler_server_controller.results
    )
    engine.rootContext().setContextProperty(
        "notificationController", notification_controller
    )
    engine.rootContext().setContextProperty(
        "notificationModel", notification_controller.model
    )
    engine.rootContext().setContextProperty(
        "notificationHistoryModel", notification_controller.history
    )
    engine.rootContext().setContextProperty(
        "notificationGroupedHistoryModel",
        notification_controller.filtered_history,
    )
    engine.rootContext().setContextProperty(
        "checkinOutController", checkin_out_controller
    )
    engine.rootContext().setContextProperty(
        "mayaOptionsController", maya_options_controller
    )
    engine.rootContext().setContextProperty(
        "commitQueueController", commit_queue_controller
    )
    engine.rootContext().setContextProperty(
        "commitQueueModel", commit_queue_controller.model
    )
    engine.rootContext().setContextProperty(
        "namingEditorController", naming_editor_controller
    )
    engine.rootContext().setContextProperty(
        "namingEditorModel", naming_editor_controller.model
    )
    engine.rootContext().setContextProperty(
        "dropPlateController", drop_plate_controller
    )
    engine.rootContext().setContextProperty(
        "dropPlateModel", drop_plate_controller.model
    )
    engine.rootContext().setContextProperty(
        "matchingTemplatesController", matching_templates_controller
    )
    engine.rootContext().setContextProperty(
        "matchingTemplatesModel", matching_templates_controller.model
    )
    engine.rootContext().setContextProperty(
        "checkinFileModel", checkin_out_controller.files
    )
    engine.rootContext().setContextProperty(
        "checkoutSnapshotModel", checkin_out_controller.checkout_snapshots
    )
    engine.rootContext().setContextProperty(
        "checkoutFileModel", checkin_out_controller.checkout_files
    )
    engine.rootContext().setContextProperty(
        "configurationController", configuration_controller
    )
    engine.rootContext().setContextProperty(
        "localizationController", localization_controller
    )
    engine.rootContext().setContextProperty(
        "repositoryEditorController", repository_editor_controller
    )
    engine.rootContext().setContextProperty(
        "repositoryEditorModel", repository_editor_controller.model
    )
    engine.rootContext().setContextProperty(
        "watchFoldersController", watch_folders_controller
    )
    engine.rootContext().setContextProperty(
        "watchFoldersModel", watch_folders_controller.model
    )
    engine.rootContext().setContextProperty(
        "filterEditorController", filter_editor_controller
    )
    engine.rootContext().setContextProperty(
        "filterEditorModel", filter_editor_controller.model
    )
    engine.rootContext().setContextProperty(
        "filterPresetModel", filter_editor_controller.presets
    )
    engine.rootContext().setContextProperty(
        "processFilterEditorController", process_filter_editor_controller
    )
    engine.rootContext().setContextProperty(
        "processFilterModel", process_filter_editor_controller.model
    )
    engine.rootContext().setContextProperty(
        "repositorySyncEditorController",
        repository_sync_editor_controller,
    )
    engine.rootContext().setContextProperty(
        "repositorySyncTreeModel", repository_sync_editor_controller.model
    )
    engine.rootContext().setContextProperty(
        "repositorySyncPresetModel",
        repository_sync_editor_controller.presets,
    )
    engine.rootContext().setContextProperty(
        "sobjectEditorController", sobject_editor_controller
    )
    engine.rootContext().setContextProperty(
        "sobjectFieldModel", sobject_editor_controller.model
    )
    engine.rootContext().setContextProperty(
        "sobjectLinkController", sobject_link_controller
    )
    engine.rootContext().setContextProperty(
        "linkAvailableModel", sobject_link_controller.available_model
    )
    engine.rootContext().setContextProperty(
        "linkCurrentModel", sobject_link_controller.linked_model
    )
    engine.rootContext().setContextProperty("debugLog", debug_log)
    engine.rootContext().setContextProperty("debugLogModel", debug_log.entries_model)
    engine.rootContext().setContextProperty("debugGroupModel", debug_log.groups_model)
    engine.rootContext().setContextProperty("navigationModel", controller.navigation_model)
    engine.rootContext().setContextProperty("sectionTabsModel", controller.section_model)
    engine.rootContext().setContextProperty("projectModel", controller.project_model)
    engine.rootContext().setContextProperty("workspaceModel", controller.workspace_model)
    engine.rootContext().setContextProperty("versionsModel", controller.versions_model)
    engine.rootContext().setContextProperty("workspaceState", controller.workspace_state)
    engine.rootContext().setContextProperty("workspaceTabsModel", controller.workspace_state.tabs_model)
    engine.rootContext().setContextProperty("searchSuggestionModel", controller.workspace_state.search_suggestion_model)
    engine.rootContext().setContextProperty(
        "advancedFilterSuggestionModel",
        controller.workspace_state.advanced_filter_suggestion_model,
    )
    engine.rootContext().setContextProperty("snapshotModel", controller.workspace_state.snapshot_model)
    engine.rootContext().setContextProperty("snapshotPreviewModel", controller.workspace_state.snapshot_preview_model)
    engine.rootContext().setContextProperty("snapshotFileModel", controller.workspace_state.snapshot_file_model)
    engine.rootContext().setContextProperty("taskModel", controller.workspace_state.task_model)
    engine.rootContext().setContextProperty("noteModel", controller.workspace_state.note_model)
    engine.rootContext().setContextProperty("dropModel", controller.workspace_state.drop_model)
    engine.rootContext().setContextProperty("filterModel", controller.workspace_state.filter_model)
    engine.rootContext().setContextProperty("fastControlModel", controller.workspace_state.fast_control_model)
    engine.rootContext().setContextProperty(
        "repoSyncModel", controller.repository_sync.model
    )
    engine.rootContext().setContextProperty(
        "repositorySync", controller.repository_sync
    )
    engine.rootContext().setContextProperty("watchModel", controller.workspace_state.watch_model)
    engine.rootContext().setContextProperty("dockModel", controller.dock_model)
    engine.rootContext().setContextProperty("windowModel", controller.window_model)
    engine.rootContext().setContextProperty("configPageModel", controller.workspace_state.configuration_page_model)
    engine.rootContext().setContextProperty("taskStatusModel", controller.workspace_state.task_status_model)
    engine.rootContext().setContextProperty("filterColumnModel", controller.workspace_state.filter_column_model)
    engine.rootContext().setContextProperty("filterRelationModel", controller.workspace_state.filter_relation_model)
    engine.rootContext().setContextProperty("syncPresetModel", controller.workspace_state.sync_preset_model)
    engine.rootContext().setContextProperty("serverPresetModel", controller.workspace_state.server_preset_model)
    engine.rootContext().setContextProperty("processTabsModel", controller.workspace_state.process_tabs_model)
    engine.rootContext().setContextProperty("controlsTabsModel", controller.workspace_state.controls_tabs_model)
    engine.rootContext().setContextProperty("mayaFormatModel", controller.workspace_state.maya_format_model)
    engine.rootContext().setContextProperty("columnsModel", controller.workspace_state.columns_model)
    engine.rootContext().setContextProperty("scriptLanguageModel", controller.workspace_state.script_language_model)
    engine.rootContext().setContextProperty("logLevelModel", controller.workspace_state.log_level_model)
    engine.rootContext().setContextProperty("userModel", controller.workspace_state.user_model)
    engine.rootContext().setContextProperty("updateVersionModel", controller.workspace_state.update_version_model)
    engine.rootContext().setContextProperty("templateModel", controller.workspace_state.template_model)
    engine.rootContext().setContextProperty("repositoryModel", controller.workspace_state.repository_model)
    engine.rootContext().setContextProperty("databaseTableModel", controller.workspace_state.database_table_model)
    engine.rootContext().setContextProperty("searchTypeModel", controller.workspace_state.search_type_model)
    qml_path = Path(__file__).parent / "modern_ui" / "qml" / "Main.qml"
    if not qml_path.is_file():
        message = f"QML startup failed: {qml_path}: file does not exist"
        sys.stderr.write(message + "\n")
        destroy_qml()
        shutdown()
        return 1
    engine.load(QUrl.fromLocalFile(str(qml_path)))
    if not engine.rootObjects():
        reason = "; ".join(qml_errors) or "QQmlApplicationEngine created no root object"
        sys.stderr.write(f"QML startup failed: {qml_path}: {reason}\n")
        destroy_qml()
        shutdown()
        return 1
    tray_controller.attach_window(engine.rootObjects()[0])
    handler_server_controller.showWindowRequested.connect(
        tray_controller.show_window
    )
    if not smoke_offline:
        # Let the first frame reach the screen before any disk or server work.
        # Cached workspace state is presentation-only; the authoritative
        # server refresh follows immediately in the background. Polling and
        # filesystem observers wait for that authoritative project selection.
        controller.project_changed.connect(server_update_service.start)
        controller.project_changed.connect(watch_folders_controller.reload)
        QTimer.singleShot(40, controller.restore_cached_workspace)
        QTimer.singleShot(80, controller.bootstrap_server)
        QTimer.singleShot(120, handler_server_controller.start_server)


    startup_hook_pending = {"value": True}

    def run_after_ui_started(_project_code="", _title="") -> None:
        if not startup_hook_pending["value"]:
            return
        if not controller.current_project_code:
            return
        startup_hook_pending["value"] = False
        try:
            from execute_after_start import execute
            execute()
        except Exception as error:
            debug_log.raise_error(
                error,
                stacktrace=traceback.format_exc(),
                group="startup/custom-scripts",
            )

    controller.project_changed.connect(run_after_ui_started)
    QTimer.singleShot(0, run_after_ui_started)
    smoke_windows = os.environ.get("TACTIC_QML_SMOKE_WINDOWS", "") == "1"
    if smoke_windows:
        original_windows = list(controller.window_model._windows)
        original_z_counter = controller.window_model._z_counter
        window_ids = [
            window.window_id for window in controller.window_model._windows
        ]
        smoke_steps = [
            (window_id, visible)
            for _pass in range(2)
            for window_id in window_ids
            for visible in (True, False)
        ]

        def advance_window_smoke() -> None:
            if not smoke_steps:
                controller.window_model._windows = original_windows
                controller.window_model._z_counter = original_z_counter
                controller.window_model._save()
                app.quit()
                return
            window_id, visible = smoke_steps.pop(0)
            if visible:
                controller.window_model.show_window(window_id)
            else:
                controller.window_model.close_window(window_id)

            def verify_and_continue() -> None:
                for window in QGuiApplication.allWindows():
                    if not window.isVisible():
                        continue
                    minimum_width = int(window.minimumWidth())
                    minimum_height = int(window.minimumHeight())
                    if window.width() < minimum_width:
                        qml_errors.append(
                            f"{window.title()}: width below minimum"
                        )
                    if window.height() < minimum_height:
                        qml_errors.append(
                            f"{window.title()}: height below minimum"
                        )
                advance_window_smoke()

            QTimer.singleShot(35, verify_and_continue)

        QTimer.singleShot(0, advance_window_smoke)
    smoke_exit_ms = int(os.environ.get("TACTIC_QML_SMOKE_EXIT_MS", "0") or 0)
    if smoke_exit_ms and not smoke_windows:
        QTimer.singleShot(smoke_exit_ms, app.quit)
    exit_code = app.exec()
    if smoke_windows and qml_errors:
        sys.stderr.write(
            "QML window smoke warnings:\n"
            + "\n".join(qml_errors)
            + "\n"
        )
        exit_code = 1
    destroy_qml()
    shutdown()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

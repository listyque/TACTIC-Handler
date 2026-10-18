import QtQuick
import QtQuick.Controls
import "../../../controls" as Controls
import "../../../" as Public
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/files/sync/queue.ui.mjs" as UI

Item {
    id: root
    required property var theme
    property var controller: repositorySync
    property var fileModel: repoSyncModel
    property int menuRow: -1
    property string menuTaskId: ""
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var frameModel: ({
            count: controller.queue_count,
            active: controller.active_count,
            discovering: controller.discovery_active,
            discoveryMode: controller.discovery_mode,
            discoveryState: controller.discovery_state,
            discoveryError: controller.discovery_error,
            processedRoots: controller.discovery_processed_roots,
            totalRoots: controller.discovery_total_roots,
            total: controller.batch_file_count,
            processed: controller.processed_file_count,
            completed: controller.completed_file_count,
            failed: controller.failed_file_count,
            progress: controller.overall_progress,
            totalSize: controller.total_size_text,
            downloadedSize: controller.transferred_size_text,
            remainingSize: controller.remaining_size_text,
            speed: controller.aggregate_speed_text,
            elapsed: controller.elapsed_text,
            eta: controller.eta_text,
            autoClean: controller.auto_clean
        })
    function dispatch(action, source) {
        if (action.index != null && fileModel.get(action.index).taskId !== action.key)
            return;
        if (action.type === "start")
            controller.start_checked();
        else if (action.type === "clear")
            controller.clear_finished();
        else if (action.type === "stopDiscovery")
            controller.cancel_discovery();
        else if (action.type === "autoClean")
            controller.set_auto_clean(action.value);
        else if (action.type === "check")
            fileModel.toggle_checked(action.index);
        else if (action.type === "retry")
            controller.retry_row(action.index);
        else if (action.type === "cancel")
            controller.cancel_row(action.index);
        else if (action.type === "menu") {
            menuRow = action.index;
            menuTaskId = action.key;
            if (action.value)
                contextMenu.openAt(source, action.value.x, action.value.y, false);
            else
                contextMenu.toggleBelow(source);
        }
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe(root.frameModel, width, height, root.language)
        views: ({
                queue: queuePort,
                busy: busyPort
            })
        onEvent: (action, source) => root.dispatch(action, source)
    }
    Component {
        id: busyPort
        Controls.BusyIndicator {
            uiTheme: root.theme
            running: true
        }
    }
    Component {
        id: queuePort
        Controls.SmoothListView {
            id: queue
            objectName: "repositorySyncQueueList"
            theme: root.theme
            model: root.fileModel
            clip: true
            spacing: 3
            Connections {
                target: root.controller
                function onActiveRowChanged() {
                    if (root.controller.active_row >= 0 && !queue.interactionMoving)
                        queue.positionViewAtIndex(root.controller.active_row, ListView.Contain);
                }
            }
            delegate: Frame.FrameView {
                id: row
                required property var model
                required property int index
                width: Math.max(0, queue.width - 16)
                height: 76
                theme: root.theme
                scene: UI.row({
                    taskId: model.taskId,
                    title: model.title,
                    process: model.process,
                    progress: model.progress,
                    checked: model.checked,
                    active: model.active,
                    phase: model.phase,
                    alreadyExists: model.alreadyExists,
                    progressValue: model.progressValue,
                    speed: model.speed,
                    localPath: model.localPath,
                    error: model.error,
                    hovered: hover.hovered
                }, index, width, root.language)
                onEvent: (action, source) => root.dispatch(action, source)
                HoverHandler {
                    id: hover
                }
            }
            ScrollBar.vertical: Controls.ScrollBar {
                theme: root.theme
                flickableTarget: queue
            }
        }
    }
    Public.ActionMenu {
        id: contextMenu
        objectName: "repositorySyncContextMenu"
        parent: Overlay.overlay
        theme: root.theme
        actions: appController.menu_actions("repo_sync")
        onTriggered: command => {
            if (root.fileModel.get(root.menuRow).taskId !== root.menuTaskId)
                return;
            if (command === "sync")
                root.controller.retry_row(root.menuRow);
            else if (command === "remove")
                root.controller.remove_row(root.menuRow);
        }
    }
}

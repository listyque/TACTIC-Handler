import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import "../../../controls" as Controls
import "../../../" as Public
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/files/queue/queue.ui.mjs" as UI
import "../../../tactic_frame/features/files/queue/previews.ui.mjs" as Previews
import "../../../tactic_frame/controls/feedback/confirmation.ui.mjs" as Confirmation
import "QueueState.js" as State

Item {
    id: root
    required property var theme
    property var controller: commitQueueController
    property bool namingPreviewExpanded: false
    property bool detailsVisible: false
    property var paneWidthDraft: null
    property var filesHeightDraft: null
    property bool contextEditing: false
    property string contextDraft: ""
    property var versionDraft: null
    property string versionError: ""
    property var filenameDraft: null
    property var descriptionDraft: null
    property string menuKind: "send"
    property string menuOperationId: ""
    property string pickerOperationId: ""
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var record: State.record(controller.selectedRecord, controller.busy)
    readonly property var sourceRows: State.files(record)
    readonly property var previewRows: State.previews(record)
    readonly property var frameModel: ({
            record,
            count: controller.count,
            selected: controller.selectedRow,
            busy: controller.busy,
            autoClean: controller.autoClean,
            applyChecked: controller.applyToChecked,
            advanced: controller.advancedOptionsExpanded,
            details: detailsVisible,
            namingExpanded: namingPreviewExpanded,
            paneWidth: paneWidthDraft === null ? Math.max(0, width - 30) * controller.splitterRatio : paneWidthDraft,
            filesHeight: filesHeightDraft === null ? controller.filesPanelHeight : filesHeightDraft,
            contextEditing,
            contextDraft,
            versionDraft,
            versionError,
            filenameDraft,
            descriptionDraft,
            localMethods: true,
            serverQueueAvailable: true,
            serverQueue: controller.serverQueue,
            clipboardKnown: true,
            clipboardHasImage: screenshotController.clipboardHasImage,
            cancelPrepared: false,
            hasReady: !versionError && controller.hasReady,
            hasCheckedReady: !versionError && controller.hasCheckedReady,
            hasCompleted: controller.hasCompleted,
            canCancel: true,
            fileCount: sourceRows.length,
            sourceTargets: sourceRows.some(file => !!file.target),
            repositories: controller.repositories.map(value => ({
                        value: value.code,
                        label: value.title
                    })),
            duplicate: controller.duplicatePending,
            duplicateDescription: controller.duplicateDescription,
            canReplace: !controller.busy,
            progress: controller.serverProgress,
            resumeAvailable: controller.serverResumeAvailable
        })
    Connections {
        target: root.controller
        function onStateChanged() {
            if (root.lastOperationId === root.controller.selectedId)
                return;
            root.lastOperationId = root.controller.selectedId;
            root.contextEditing = false;
            root.versionDraft = null;
            root.versionError = "";
            root.filenameDraft = null;
            root.descriptionDraft = null;
        }
    }
    property string lastOperationId: controller.selectedId
    onWidthChanged: if (width >= 700)
        detailsVisible = false

    function focusOperation(index) {
        presenter.focusListRow("commitQueueRows", index, "commitQueueSelect_" + controller.selectedId);
    }
    function previewAction(command) {
        if (command === "manage")
            previewManager.open();
        else if (!record.canPreview)
            return;
        else if (command === "choose") {
            pickerOperationId = controller.selectedId;
            previewPicker.open();
        } else if (command === "capture") {
            screenshotController.prepare_for_operation(controller.selectedId);
            windowModel.show_child_window("screenshot_maker", "commit_queue");
        } else if (command === "paste")
            screenshotController.paste_preview_from_clipboard(controller.selectedId);
        else if (command === "clearPreviews")
            controller.clear_selected_previews();
    }
    function command(value, operationId) {
        if (versionError && ["all", "selected", "current", "retry"].includes(value))
            return;
        const row = operationId ? controller.row_for_id(operationId) : controller.selectedRow;
        if (operationId && row < 0)
            return;
        if (value === "remove")
            controller.remove_row(row);
        else if (value === "all")
            controller.commit_all();
        else if (value === "selected")
            controller.commit_selected();
        else {
            if (row >= 0 && operationId)
                controller.select_row(row);
            if (value === "current")
                controller.commit_current();
            else if (value === "retry")
                controller.retry_current();
            else if (value === "cancel")
                controller.cancel();
        }
    }
    function dispatch(action, source) {
        const row = action.key != null ? controller.row_for_id(action.key) : action.index;
        if (["select", "check", "remove", "operationMenu"].includes(action.type) && row < 0)
            return;
        if (action.type === "select") {
            controller.select_row(row);
            if (action.focus)
                Qt.callLater(() => focusOperation(row));
            else if (width < 700)
                detailsVisible = true;
        } else if (action.type === "check")
            controller.toggle_checked(row);
        else if (action.type === "remove")
            controller.remove_row(row);
        else if (action.type === "up")
            controller.move_selected(-1);
        else if (action.type === "down")
            controller.move_selected(1);
        else if (action.type === "completed")
            controller.remove_completed();
        else if (action.type === "clear")
            clearConfirmation.open();
        else if (action.type === "help")
            windowModel.open_help("commit_queue");
        else if (action.type === "serverQueueHelp")
            windowModel.open_help("server_checkin_queue");
        else if (action.type === "autoClean")
            controller.set_auto_clean(action.value);
        else if (action.type === "serverQueue")
            controller.set_server_queue(action.value);
        else if (action.type === "navigate")
            detailsVisible = action.value === "details";
        else if (action.type === "paneWidthDraft")
            paneWidthDraft = action.value;
        else if (action.type === "paneWidthCancel")
            paneWidthDraft = null;
        else if (action.type === "filesHeightDraft")
            filesHeightDraft = action.value;
        else if (action.type === "filesHeightCancel")
            filesHeightDraft = null;
        else if (action.type === "paneWidth") {
            controller.set_splitter_ratio(action.value / Math.max(1, width - 30));
            paneWidthDraft = null;
        } else if (action.type === "filesHeight") {
            controller.set_files_panel_height(action.value);
            filesHeightDraft = null;
        } else if (action.type === "advanced")
            controller.set_advanced_options_expanded(!controller.advancedOptionsExpanded);
        else if (action.type === "applyChecked")
            controller.set_apply_to_checked(action.value);
        else if (action.type === "namingToggle")
            namingPreviewExpanded = !namingPreviewExpanded;
        else if (action.type === "namingEditor") {
            namingEditorController.prepare_operation(controller.selectedId);
            windowModel.show_window("naming_editor");
        } else if (action.type === "contextEdit") {
            contextDraft = record.contextBranch || "";
            contextEditing = true;
            Qt.callLater(() => presenter.focusControl("commitQueueContextField"));
        } else if (action.type === "contextDraft")
            contextDraft = action.value;
        else if (action.type === "contextCancel")
            contextEditing = false;
        else if (action.type === "contextCommit" && contextEditing) {
            contextEditing = false;
            controller.update_selected_context_branch(contextDraft);
        } else if (action.type === "versionDraft") {
            versionDraft = action.value;
            versionError = "";
        } else if (action.type === "versionCommit" && versionDraft != null) {
            const version = UI.versionValue(versionDraft);
            if (version == null)
                versionError = "Version must be a whole number from 0 to 9999";
            else {
                controller.update_selected("version", version);
                versionDraft = null;
                versionError = "";
            }
        } else if (action.type === "filenameDraft")
            filenameDraft = action.value;
        else if (action.type === "filenameCommit" && filenameDraft != null) {
            controller.update_selected("explicitFilename", filenameDraft);
            filenameDraft = null;
        } else if (action.type === "descriptionDraft")
            descriptionDraft = action.value;
        else if (action.type === "descriptionCommit" && descriptionDraft != null) {
            controller.update_selected("description", descriptionDraft);
            descriptionDraft = null;
        } else if (action.type === "field")
            controller.update_selected(action.field, action.value);
        else if (["removeFile", "removePreview"].includes(action.type)) {
            if (action.operationId !== controller.selectedId)
                return;
            if (action.type === "removePreview" || action.preview)
                controller.remove_selected_preview(action.index);
            else
                controller.remove_selected_file(action.index);
        } else if (action.type === "preview")
            previewAction(action.command);
        else if (["previewMenu", "sendMenu", "operationMenu"].includes(action.type)) {
            if (action.type === "operationMenu")
                controller.select_row(row);
            menuKind = action.type === "previewMenu" ? "preview" : action.type === "operationMenu" ? "operation" : "send";
            menuOperationId = action.key || controller.selectedId;
            if (action.value) {
                actionMenu.openAt(source, action.value.x, action.value.y, false);
            } else
                actionMenu.toggleBelow(source);
        } else if (action.type === "duplicate")
            controller.resolve_duplicate(action.decision);
        else if (["all", "retry", "cancel"].includes(action.type))
            command(action.type, "");
    }
    Frame.FrameView {
        id: presenter
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe(root.frameModel, width, height, root.language)
        models: ({
                operations: commitQueueModel,
                files: root.sourceRows,
                naming: UI.namingRows(root.record, root.language)
            })
        describeRow: (list, record, index) => list.source === "operations" ? UI.operationRow(root.frameModel, State.record(record, root.controller.busy), index, list.width - 16, root.language) : list.source === "naming" ? UI.namingRow(record, list.width - 16) : UI.sourceRow(root.frameModel, record, list.width - 16, root.language)
        views: ({
                preview: {
                    component: previewPort,
                    nodeProps: true
                },
                progress: {
                    component: progressPort,
                    nodeProps: true
                },
                description: descriptionPort
            })
        onEvent: (action, source) => root.dispatch(action, source)
    }
    Component {
        id: previewPort
        Controls.ItemPreview {
            property var frameNode: ({})
            theme: root.theme
            source: frameNode.source || ""
            fallbackIcon: frameNode.icon || "draft"
            fallbackText: frameNode.initials || ""
            accent: root.theme[frameNode.accent || "action"]
            cornerRadius: frameNode.radius || 4
            previewSize: width
            readyBorderEnabled: false
        }
    }
    Component {
        id: progressPort
        Controls.ProgressBar {
            property var frameNode: ({})
            theme: root.theme
            from: 0
            to: frameNode.max || 1
            value: frameNode.value || 0
            indeterminate: !!frameNode.indeterminate
            Accessible.name: frameNode.label || ""
        }
    }
    Component {
        id: descriptionPort
        Public.DescriptionEditor {
            theme: root.theme
            managed: false
            compact: true
            editorEnabled: !!root.record.canDescription
            value: root.descriptionDraft == null ? root.record.description || "" : root.descriptionDraft
            onValueEdited: value => root.descriptionDraft = value
            onEditingFinished: value => root.dispatch({
                    type: "descriptionCommit",
                    value
                })
        }
    }
    Public.ActionMenu {
        id: actionMenu
        parent: Overlay.overlay
        theme: root.theme
        actions: root.menuKind === "preview" ? UI.previewActions(root.frameModel) : root.menuKind === "operation" ? UI.operationActions(root.frameModel, root.record) : UI.sendActions(root.frameModel)
        onTriggered: command => {
            if (root.menuKind === "preview") {
                if (root.menuOperationId === root.controller.selectedId)
                    root.previewAction(command);
            } else
                root.command(command, root.menuKind === "operation" ? root.menuOperationId : "");
        }
    }
    FileDialog {
        id: previewPicker
        title: qsTr("Choose operation previews")
        fileMode: FileDialog.OpenFiles
        nameFilters: ["Images (*.apng *.avif *.bmp *.gif *.ico *.jpg *.jpeg *.png *.svg *.tga *.tif *.tiff *.webp)"]
        onAccepted: {
            if (root.pickerOperationId === root.controller.selectedId)
                root.controller.add_selected_previews(selectedFiles);
        }
    }
    Controls.Dialog {
        id: previewManager
        objectName: "commitQueuePreviewManager"
        theme: root.theme
        modal: false
        anchors.centerIn: parent
        width: Math.min(Previews.metrics.width, root.width - Previews.metrics.ownerMargin)
        height: Math.min(Previews.metrics.height, root.height - Previews.metrics.ownerMargin)
        title: qsTr("Operation previews")
        contentItem: Frame.FrameView {
            theme: root.theme
            scene: Previews.describe({
                count: root.previewRows.length,
                canEdit: !!root.record.canPreview,
                clipboardKnown: true,
                clipboardHasImage: screenshotController.clipboardHasImage
            }, width, height, root.language)
            models: ({
                    previews: root.previewRows
                })
            describeRow: (list, record) => Previews.row(record, list.width - 16, root.language)
            views: ({
                    preview: {
                        component: previewPort,
                        nodeProps: true
                    }
                })
            onEvent: action => {
                if (action.type === "preview" && action.command === "close")
                    previewManager.close();
                else
                    root.dispatch(action);
            }
        }
    }
    Controls.Dialog {
        id: clearConfirmation
        objectName: "commitQueueClearConfirmation"
        theme: root.theme
        modal: true
        anchors.centerIn: parent
        width: Math.min(Previews.metrics.clearWidth, root.width - Previews.metrics.ownerMargin)
        title: qsTr("Clear commit queue?")
        closePolicy: root.controller.busy ? Popup.NoAutoClose : Popup.CloseOnEscape | Popup.CloseOnPressOutside
        contentItem: Frame.FrameView {
            theme: root.theme
            implicitHeight: 170
            scene: Confirmation.describe({
                message: qsTr("All prepared, failed and completed operations will be removed from the queue."),
                accept: "Clear queue",
                destructive: true,
                busy: root.controller.busy
            }, width, height, root.language)
            onEvent: action => {
                if (action.type === "accept" && !root.controller.busy)
                    root.controller.clear();
                clearConfirmation.close();
            }
        }
    }
}

import QtQuick
import "../../../controls" as Controls
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/core/foundation.mjs" as Foundation
import "../../../tactic_frame/controls/buttons/metrics.mjs" as ButtonMetrics
import "../../../tactic_frame/features/files/sync/editor.ui.mjs" as UI
import "../../../tactic_frame/controls/feedback/confirmation.ui.mjs" as Confirmation

Item {
    id: root
    required property var theme
    required property string windowId
    property var controller: repositorySyncEditorController
    property real paneWidth: 350
    property int presetsRevision: 0
    property var chunkControl: null
    property var processControl: null
    property string newPresetName: ""
    property string deletePresetName: ""
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var presetRecords: {
        presetsRevision;
        return repositorySyncPresetModel.records();
    }
    FontMetrics {
        id: footerMetrics
        font: Qt.font({
            family: root.theme.fontFamily,
            pixelSize: Foundation.textStyles.body,
            weight: Font.DemiBold,
            hintingPreference: Font.PreferVerticalHinting
        })
    }
    readonly property var frameModel: ({
            buttonWidths: UI.actions(language).map(action => ButtonMetrics.buttonWidth(footerMetrics.advanceWidth(action.text), !!action.icon)),
            presets: presetRecords.map(record => ({
                        value: record.name,
                        label: record.title
                    })),
            presetName: (presetRecords[controller.selectedPreset] || {}).name || "",
            selected: controller.selectedPreset,
            validContext: controller.validContext,
            busy: controller.busy,
            error: controller.error,
            dirty: controller.dirty,
            onlyUpdates: controller.onlyUpdates,
            scopeMode: controller.scopeMode,
            discovering: repositorySync.discovery_active,
            active: repositorySync.active_count,
            togglersExpanded: !!processControl && processControl.togglersExpanded,
            paneWidth
        })
    Connections {
        target: repositorySyncPresetModel
        function onContentReplaced() {
            root.presetsRevision++;
        }
    }
    function dispatch(action) {
        if (action.type === "preset") {
            const row = presetRecords.findIndex(record => record.name === action.value);
            if (row >= 0)
                controller.select_preset(row);
        } else if (action.type === "save")
            controller.save_selected();
        else if (action.type === "add") {
            newPresetName = "";
            newPresetDialog.open();
            Qt.callLater(() => newPresetPresenter.focusControl("repositorySyncPresetName"));
        } else if (action.type === "delete") {
            deletePresetName = frameModel.presetName;
            deletePresetDialog.open();
        } else if (action.type === "scope")
            controller.set_scope_mode(action.value);
        else if (action.type === "onlyUpdates")
            controller.set_only_updates(action.value);
        else if (action.type === "paneWidth")
            paneWidth = action.value;
        else if (action.type === "close")
            windowModel.close_window(windowId);
        else if (action.type === "start") {
            if (chunkControl) {
                chunkControl.commitTextValue();
                controller.start_sync_with_chunk_size(chunkControl.value);
            }
        }
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe(root.frameModel, width, height, root.language)
        views: ({
                processes: processPort,
                queue: queuePort,
                chunk: chunkPort
            })
        onEvent: action => root.dispatch(action)
    }
    Component {
        id: processPort
        Controls.ProcessSelectionTree {
            objectName: "repositorySyncProcessPanel"
            theme: root.theme
            treeModel: repositorySyncTreeModel
            treeController: root.controller
            validContext: root.controller.validContext
            showVersionChooser: true
            emptyText: qsTr("Select an sObject or Search Type first")
            treeObjectName: "repositorySyncProcessTree"
            rowObjectName: "repositorySyncProcessTreeRow"
            Component.onCompleted: root.processControl = this
            Component.onDestruction: if (root.processControl === this)
                root.processControl = null
        }
    }
    Component {
        id: queuePort
        SyncQueueView {
            theme: root.theme
        }
    }
    Component {
        id: chunkPort
        Controls.SpinBox {
            objectName: "repositorySyncChunkSize"
            theme: root.theme
            from: 1
            to: 250
            stepSize: 1
            editable: true
            value: root.controller.partialChunkSize
            enabled: root.controller.scopeMode === "partial"
            onRealValueEdited: value => root.controller.set_partial_chunk_size(Math.round(value))
            Controls.ToolTip {
                theme: root.theme
                visible: parent.hovered && !root.theme.suppressToolTips
                text: qsTr("Objects discovered per chunk")
            }
            Component.onCompleted: root.chunkControl = this
            Component.onDestruction: if (root.chunkControl === this)
                root.chunkControl = null
        }
    }
    Controls.Dialog {
        id: newPresetDialog
        objectName: "repositorySyncCreatePresetDialog"
        theme: root.theme
        title: qsTr("Save Repository Sync preset")
        modal: true
        anchors.centerIn: parent
        width: Math.min(420, root.width - 48)
        contentItem: Frame.FrameView {
            id: newPresetPresenter
            theme: root.theme
            implicitHeight: 94
            scene: UI.createPreset({
                name: root.newPresetName,
                busy: root.controller.busy
            }, width, root.language)
            onEvent: action => {
                if (action.type === "name")
                    root.newPresetName = action.value;
                else if (action.type === "reject")
                    newPresetDialog.close();
                else if (action.type === "accept" && !root.controller.busy && root.newPresetName.trim()) {
                    root.controller.save_as(root.newPresetName);
                    newPresetDialog.close();
                }
            }
        }
    }
    Controls.Dialog {
        id: deletePresetDialog
        objectName: "repositorySyncDeletePresetDialog"
        theme: root.theme
        title: qsTr("Delete Repository Sync preset?")
        modal: true
        anchors.centerIn: parent
        width: Math.min(440, root.width - 48)
        contentItem: Frame.FrameView {
            theme: root.theme
            implicitHeight: 170
            scene: Confirmation.describe({
                message: qsTr("The selected server preset will be deleted."),
                accept: "Delete",
                destructive: true,
                busy: root.controller.busy
            }, width, height, root.language)
            onEvent: action => {
                if (action.type === "accept" && !root.controller.busy && root.deletePresetName === root.frameModel.presetName)
                    root.controller.delete_selected();
                deletePresetDialog.close();
            }
        }
    }
}

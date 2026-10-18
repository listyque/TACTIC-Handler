import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import "controls" as Controls
import "features/files" as Files
import "tactic_frame" as Frame
import "tactic_frame/features/files/ingest.ui.mjs" as UI
import "tactic_frame/controls/feedback/confirmation.ui.mjs" as Confirmation

Item {
    id: root
    required property var theme
    property var controller: ingestFilesController
    property bool advancedVisible: false
    property int rulesRevision: 0
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var frameModel: {
        rulesRevision;
        return {
            parentTitle: controller.parentTitle,
            targetTitle: controller.targetTitle,
            searchType: controller.searchType,
            options: controller.options,
            busy: controller.busy,
            rulesBusy: controller.rulesBusy,
            canDeleteRule: controller.canDeleteRule,
            canStop: true,
            canStart: !controller.conflictPending,
            count: controller.fileCount,
            ruleCount: ingestRuleModel.count(),
            advanced: advancedVisible,
            message: controller.message,
            error: controller.error
        };
    }
    Connections {
        target: ingestRuleModel
        function onContentReplaced() {
            root.rulesRevision++;
        }
    }
    function dispatch(action) {
        if (action.type === "option")
            controller.set_option(action.field, UI.optionValue(action.field, action.value));
        else if (action.type === "rule") {
            for (let index = 0; index < ingestRuleModel.count(); index++) {
                if (ingestRuleModel.get(index).ruleId === action.key) {
                    controller.select_rule(index);
                    break;
                }
            }
        } else if (action.type === "advanced")
            advancedVisible = !advancedVisible;
        else if (action.type === "clear")
            controller.clear_files();
        else if (action.type === "add")
            picker.open();
        else if (action.type === "start")
            controller.start();
        else if (action.type === "stop")
            controller.cancel();
        else if (action.type === "close")
            windowModel.hide_window("ingest_files");
        else if (action.type === "saveRule")
            controller.save_rule(controller.options.title || "");
        else if (action.type === "deleteRule")
            deleteRuleDialog.open();
        else if (action.type === "script")
            windowModel.show_window("script_editor");
    }
    Rectangle {
        anchors.fill: parent
        color: root.theme.workspace
    }
    DropArea {
        anchors.fill: parent
        enabled: !root.controller.busy
        keys: ["text/uri-list"]
        onEntered: drag => drag.acceptProposedAction()
        onDropped: drop => {
            drop.acceptProposedAction();
            root.controller.add_paths(drop.urls);
        }
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe(root.frameModel, width, height, root.language)
        models: ({
                rules: ingestRuleModel
            })
        describeRow: (list, record) => UI.ruleRow(root.frameModel, record, list.width - 16, root.language)
        views: ({
                files: fileList
            })
        onEvent: action => root.dispatch(action)
    }
    Component {
        id: fileList
        Files.IngestFileList {
            theme: root.theme
            controller: root.controller
            fileModel: ingestFileModel
            language: root.language
        }
    }
    FileDialog {
        id: picker
        title: qsTr("Choose files to ingest")
        fileMode: FileDialog.OpenFiles
        onAccepted: root.controller.add_paths(selectedFiles)
    }
    Controls.Dialog {
        id: deleteRuleDialog
        theme: root.theme
        parent: root
        title: qsTr("Delete ingest rule?")
        modal: true
        focus: true
        anchors.centerIn: parent
        width: Math.min(440, parent.width - 24)
        standardButtons: Dialog.NoButton
        contentItem: Frame.FrameView {
            implicitHeight: 170
            theme: root.theme
            scene: Confirmation.describe({
                message: qsTr("The rule will be removed from this TACTIC project."),
                accept: "Delete rule",
                destructive: true,
                busy: root.controller.busy
            }, width, height, root.language)
            onEvent: action => {
                if (action.type === "accept") {
                    deleteRuleDialog.accept();
                    root.controller.delete_selected_rule();
                } else
                    deleteRuleDialog.reject();
            }
        }
    }
    IngestConflictDialog {
        anchors.fill: parent
        theme: root.theme
        controller: root.controller
    }
}

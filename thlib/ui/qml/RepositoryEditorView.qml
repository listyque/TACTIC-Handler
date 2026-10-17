import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls
import "tactic_frame" as Frame
import "tactic_frame/features/configuration/repository.ui.mjs" as UI

Item {
    id: root
    required property var theme
    property string windowId: ""
    property int selectedRow: 0
    property int modelRevision: 0
    property bool editing: false
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var record: {
        modelRevision;
        return repositoryEditorModel.get(selectedRow);
    }
    readonly property var model: ({
            native: true,
            style: theme.style,
            record,
            selected: record.alias || "",
            busy: repositoryEditorController.busy,
            dirty: repositoryEditorController.dirty,
            notice: repositoryEditorController.message,
            teamLocal: repositoryEditorController.team_local_repository,
            editing
        })
    Component.onCompleted: repositoryEditorController.begin_edit()
    Connections {
        target: repositoryEditorModel
        function onDataChanged() {
            root.modelRevision++;
        }
        function onContentReplaced() {
            root.modelRevision++;
        }
    }
    function dispatch(action) {
        if (action.type === "field")
            repositoryEditorModel.set_value(selectedRow, action.field, action.value);
        else if (action.type === "select") {
            for (let index = 0; index < repositoryEditorModel.count(); index++)
                if (repositoryEditorModel.get(index).alias === action.alias)
                    selectedRow = index;
            editing = true;
        } else if (action.type === "add") {
            repositoryEditorController.add_custom_repository();
            selectedRow = repositoryEditorModel.count() - 1;
            editing = true;
        } else if (action.type === "remove") {
            repositoryEditorController.remove_custom_repository(selectedRow);
            selectedRow = Math.max(0, Math.min(selectedRow, repositoryEditorModel.count() - 1));
        } else if (action.type === "reset")
            repositoryEditorController.cancel();
        else if (action.type === "check")
            repositoryEditorController.check_paths();
        else if (action.type === "sync")
            teamRepositoryDialog.open();
        else if (action.type === "save") {
            if (repositoryEditorController.save() && repositoryEditorController.team_local_repository)
                teamRepositoryDialog.open();
        } else if (action.type === "close" && !repositoryEditorController.busy)
            windowModel.close_window("repository_editor");
        else if (action.type === "back")
            editing = false;
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.editor(root.model, width, height, root.language)
        models: ({
                repositories: repositoryEditorModel
            })
        describeRow: (list, record) => UI.row(root.model, record, list.width - 16)
        onEvent: action => root.dispatch(action)
    }
    Controls.Dialog {
        id: teamRepositoryDialog
        objectName: "teamRepositorySyncDialog"
        theme: root.theme
        title: qsTr("Update TACTIC repository path?")
        modal: true
        anchors.centerIn: parent
        width: Math.min(480, root.width - 32)
        onAccepted: repositoryEditorController.sync_team_repository_path()

        contentItem: Label {
            width: teamRepositoryDialog.width - teamRepositoryDialog.leftPadding - teamRepositoryDialog.rightPadding
            text: qsTr("TACTIC's server-wide repository path will be set to:") + "\n" + repositoryEditorController.current_code + " → " + repositoryEditorController.current_path + "\n\n" + qsTr("This affects every TACTIC client. Confirm only if the server can access this folder.")
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
            wrapMode: Text.WrapAnywhere
        }
        footer: Controls.DialogActions {
            theme: root.theme
            Controls.Button {
                theme: root.theme
                text: qsTr("Cancel")
                flat: true
                onClicked: teamRepositoryDialog.reject()
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Update server path")
                highlighted: true
                onClicked: teamRepositoryDialog.accept()
            }
        }
    }
}

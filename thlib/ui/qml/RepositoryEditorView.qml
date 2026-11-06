import QtQuick
import "controls" as Controls
import "tactic_frame" as Frame
import "tactic_frame/features/configuration/repository.ui.mjs" as UI
import "tactic_frame/features/files/repository_prompts.ui.mjs" as Prompts

Item {
    id: root
    required property var theme
    property string windowId: ""
    property int selectedRow: 0
    property int modelRevision: 0
    property bool editing: false
    property string pendingTeamPath: ""
    property string pendingTeamCode: ""
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
    Connections {
        target: repositoryEditorController
        function onSaved() {
            if (repositoryEditorController.team_local_repository)
                root.askTeamRepository();
        }
    }
    function askTeamRepository() {
        if (repositoryEditorController.busy)
            return;
        pendingTeamPath = repositoryEditorController.current_path;
        pendingTeamCode = repositoryEditorController.current_code;
        teamRepositoryDialog.open();
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
            askTeamRepository();
        else if (action.type === "save")
            repositoryEditorController.save(); else if (action.type === "close" && !repositoryEditorController.busy)
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
        onAccepted: {
            if (!repositoryEditorController.busy && !repositoryEditorController.dirty && root.pendingTeamPath === repositoryEditorController.current_path && root.pendingTeamCode === repositoryEditorController.current_code)
                repositoryEditorController.sync_team_repository_path();
        }
        contentItem: Frame.FrameView {
            theme: root.theme
            implicitHeight: Math.max(170, Math.min(300, root.height - 180))
            scene: Prompts.team({
                path: root.pendingTeamPath,
                code: root.pendingTeamCode,
                busy: repositoryEditorController.busy,
                changed: repositoryEditorController.dirty || root.pendingTeamPath !== repositoryEditorController.current_path || root.pendingTeamCode !== repositoryEditorController.current_code
            }, width, height, root.language)
            onEvent: action => {
                if (action.type === "accept")
                    teamRepositoryDialog.accept();
                else if (action.type === "reject")
                    teamRepositoryDialog.reject();
            }
        }
    }
}

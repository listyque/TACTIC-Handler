import QtQuick
import QtQuick.Controls
import "controls" as Controls
import QtQuick.Dialogs
import "tactic_frame" as Frame
import "tactic_frame/features/projects/templates.ui.mjs" as UI

Item {
    id: root
    required property var theme
    property string selectedCode: ""
    property string deletion: ""
    onDeletionChanged: {
        if (deletion)
            deleteConfirmation.open();
        else
            deleteConfirmation.close();
    }
    readonly property var controller: projectCreationController
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    function dispatch(action) {
        if (action.type === "select")
            selectedCode = action.code;
        else if (action.type === "install")
            archiveDialog.open();
        else if (action.type === "refresh")
            controller.reload_catalog();
        else if (action.type === "download")
            controller.template_action("download", selectedCode);
        else if (action.type === "delete")
            deletion = selectedCode;
        else if (action.type === "cancelDelete")
            deletion = "";
        else if (action.type === "confirmDelete") {
            controller.template_action("delete", deletion);
            deletion = "";
            selectedCode = "";
        } else if (action.type === "close" && !controller.busy)
            windowModel.close_window("project_templates");
        else if (action.type === "help")
            windowModel.open_help("project_creation");
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe({
            packages: root.controller.catalog.installedTemplates || [],
            selected: root.selectedCode,
            busy: root.controller.busy,
            error: root.controller.error,
            deletion: root.deletion
        }, width, height, root.language)
        onEvent: action => root.dispatch(action)
    }
    FileDialog {
        id: archiveDialog
        title: qsTr("Install template archive")
        nameFilters: [qsTr("Template archives") + " (*.zip)"]
        onAccepted: root.controller.template_action("install", selectedFile)
    }
    Controls.Dialog {
        id: deleteConfirmation
        objectName: "projectTemplateDeleteConfirmation"
        theme: root.theme
        modal: true
        title: qsTr("Delete template?")
        anchors.centerIn: parent
        width: Math.min(430, root.width - 32)
        padding: 0
        closePolicy: Popup.NoAutoClose
        contentItem: Frame.FrameView {
            implicitHeight: 220
            theme: root.theme
            scene: UI.confirmation({
                code: root.deletion,
                busy: root.controller.busy
            }, width, height, root.language)
            onEvent: action => root.dispatch({
                    type: action.type === "accept" ? "confirmDelete" : "cancelDelete"
                })
            Keys.onEscapePressed: if (!root.controller.busy)
                root.deletion = ""
        }
    }
}

import QtQuick
import "../../../controls" as Controls
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/files/workspace/forms.ui.mjs" as UI

Controls.Dialog {
    id: root
    readonly property string language: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language
    property bool deleteNew: false
    objectName: "workspaceRevertDialog"
    property string operation: "revert"
    property var request: ({})
    property string caption: ""
    property bool busy: false
    signal confirmed(string operation, var values)

    modal: true
    title: operation === "revert" ? qsTr("Revert changelist") : qsTr("Revert files")
    onOpened: {
        deleteNew = false;
        Qt.callLater(() => form.focusControl("workspaceRevertCancel"));
    }
    contentItem: Frame.FrameView {
        id: form
        theme: root.theme
        implicitHeight: Math.min(300, Math.max(160, (root.parent ? root.parent.height : 600) - 138))
        scene: UI.revert({
            caption: root.caption,
            deleteNew: root.deleteNew,
            busy: root.busy
        }, width, height, root.language)
        onEvent: action => {
            if (action.type === "deleteNew")
                root.deleteNew = action.value;
            else if (action.type === "reject")
                root.reject();
            else if (action.type === "accept" && !root.busy) {
                const values = Object.assign({}, root.request, {
                    delete_not_in_depot: root.deleteNew
                });
                root.accept();
                root.confirmed(root.operation, values);
            }
        }
    }
    footer: null
}

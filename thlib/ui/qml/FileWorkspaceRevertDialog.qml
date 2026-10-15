import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Controls.Dialog {
    id: root
    objectName: "workspaceRevertDialog"
    property string operation: "revert"
    property var request: ({})
    property string caption: ""
    property bool busy: false
    signal confirmed(string operation, var values)

    modal: true
    title: operation === "revert" ? qsTr("Revert changelist") : qsTr("Revert files")
    onOpened: { deleteNew.checked=false; cancel.forceActiveFocus() }
    contentItem: ColumnLayout {
        spacing: 12
        Label { Layout.fillWidth: true; text: root.caption; color: root.theme.secondaryText; wrapMode: Text.Wrap }
        Label {
            Layout.fillWidth: true
            text: qsTr("Revert pending changes. Local files are kept unless deletion is selected.")
            wrapMode: Text.Wrap
            color: root.theme.primaryText
        }
        Controls.CheckBox {
            id: deleteNew
            objectName: "workspaceRevertDeleteNew"
            Layout.fillWidth: true
            theme: root.theme
            text: qsTr("Delete files not in depot")
        }
        Label {
            Layout.fillWidth: true
            visible: deleteNew.checked
            text: qsTr("Only newly added local files absent from the published stream will be moved to Trash after the server revert succeeds.")
            wrapMode: Text.Wrap
            color: root.theme.secondaryText
        }
    }
    footer: Controls.DialogActions {
        theme: root.theme
        Controls.Button {
            id: cancel
            objectName: "workspaceRevertCancel"
            theme: root.theme
            text: qsTr("Cancel")
            onClicked: root.reject()
        }
        Controls.Button {
            objectName: "workspaceRevertAccept"
            theme: root.theme
            text: qsTr("Revert")
            icon.name: "undo"
            destructive: true
            enabled: !root.busy
            onClicked: {
                const values=Object.assign({},root.request,{delete_not_in_depot:deleteNew.checked})
                root.accept()
                root.confirmed(root.operation,values)
            }
        }
    }
}

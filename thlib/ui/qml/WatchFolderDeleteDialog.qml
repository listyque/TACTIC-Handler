import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Controls.Dialog {
    id: root
    required property string acceptedOrigin

    parent: Overlay.overlay
    modal: true
    dim: true
    focus: true
    anchors.centerIn: Overlay.overlay
    width: Math.min(520, Overlay.overlay.width - 32)
    title: qsTr("Delete Watch Folder?")
    standardButtons: Dialog.NoButton
    closePolicy: Popup.CloseOnEscape

    contentItem: ColumnLayout {
        spacing: 18
        Label {
            Layout.fillWidth: true
            text: qsTr("Delete this Watch Folder configuration? Existing directories and files will be kept.")
            wrapMode: Text.WordWrap
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.bodyLarge
        }
        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }
            Controls.Button {
                theme: root.theme
                text: qsTr("Cancel")
                onClicked: watchFoldersController.cancel_remove()
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Delete")
                icon.name: "delete"
                destructive: true
                onClicked: watchFoldersController.confirm_remove(false)
            }
        }
    }

    onClosed: {
        if (watchFoldersController.deletePending
                && watchFoldersController.deleteOrigin === acceptedOrigin)
            watchFoldersController.cancel_remove()
    }

    Connections {
        target: watchFoldersController
        function onDeleteChanged() {
            const shouldOpen = watchFoldersController.deletePending
                && watchFoldersController.deleteOrigin === root.acceptedOrigin
            if (shouldOpen && !root.opened)
                root.open()
            else if (!shouldOpen && root.opened)
                root.close()
        }
    }
}
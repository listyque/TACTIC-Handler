import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Md3Dialog {
    id: root
    required property string acceptedOrigin

    parent: Overlay.overlay
    modal: true
    dim: true
    focus: true
    anchors.centerIn: Overlay.overlay
    width: Math.min(520, Overlay.overlay.width - 32)
    title: qsTr("Remove Watch Folder dirs from repos?")
    standardButtons: Dialog.NoButton
    closePolicy: Popup.CloseOnEscape

    contentItem: ColumnLayout {
        spacing: 18
        Label {
            Layout.fillWidth: true
            text: qsTr("Watch Folder directories and files can also be removed from your repositories. Remove or keep these directories and files?")
            wrapMode: Text.WordWrap
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pointSize: Typography.bodyLarge
        }
        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }
            Md3Button {
                theme: root.theme
                text: qsTr("Cancel")
                onClicked: watchFoldersController.cancel_remove()
            }
            Md3Button {
                theme: root.theme
                text: qsTr("Keep")
                onClicked: watchFoldersController.confirm_remove(false)
            }
            Md3Button {
                theme: root.theme
                text: qsTr("Remove")
                icon.name: "delete"
                destructive: true
                onClicked: watchFoldersController.confirm_remove(true)
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
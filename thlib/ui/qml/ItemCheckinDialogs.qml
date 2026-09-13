import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    required property var applicationController

    function askMultiFileMode(fileCount) {
        multiFileCheckinDialog.fileCount = Number(fileCount)
        multiFileCheckinDialog.awaitingChoice = true
        multiFileCheckinDialog.open()
    }

    FileDialog {
        id: checkinFilesDialog
        objectName: "checkinFilesDialog"
        title: qsTr("Choose files for check-in")
        fileMode: FileDialog.OpenFiles
        onAccepted: root.applicationController.submit_checkin_files(selectedFiles)
    }

    Controls.Dialog {
        id: revisionCheckinDialog
        objectName: "revisionCheckinDialog"
        parent: Overlay.overlay
        theme: root.theme
        modal: true
        anchors.centerIn: Overlay.overlay
        width: Math.min(480, Overlay.overlay.width - 40)
        title: qsTr("Replace snapshot revision?")
        closePolicy: Popup.NoAutoClose
        contentItem: Label {
            width: revisionCheckinDialog.availableWidth
            text: qsTr("The file stored in this revision will be replaced. ")
                + qsTr("Use Save snapshot when you need a new version.")
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.bodyLarge
            wrapMode: Text.WordWrap
        }
        footer: DialogButtonBox {
            background: Item {}
            Controls.Button {
                theme: root.theme
                text: qsTr("Replace revision")
                destructive: true
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Cancel")
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            }
            onClicked: function(button) {
                const accepted = buttonRole(button)
                    === DialogButtonBox.AcceptRole
                revisionCheckinDialog.close()
                root.applicationController.resolve_revision_checkin(accepted)
            }
        }
    }

    Controls.Dialog {
        id: multiFileCheckinDialog
        objectName: "multiFileCheckinDialog"
        parent: Overlay.overlay
        property int fileCount: 0
        property bool awaitingChoice: false

        function finish(mode) {
            if (!awaitingChoice)
                return
            awaitingChoice = false
            close()
            root.applicationController.resolve_multi_file_checkin(mode)
        }

        theme: root.theme
        modal: true
        dim: true
        focus: true
        anchors.centerIn: Overlay.overlay
        width: Math.min(500, Overlay.overlay.width - 32)
        title: qsTr("Check in multiple files?")
        closePolicy: Popup.CloseOnEscape

        contentItem: ColumnLayout {
            spacing: 18

            Label {
                Layout.fillWidth: true
                text: qsTr(
                    "%1 files selected. Check in one group or separately in sequence?"
                ).arg(multiFileCheckinDialog.fileCount)
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.bodyLarge
                wrapMode: Text.WordWrap
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                Controls.Button {
                    objectName: "multiFileCheckinGroupButton"
                    Layout.fillWidth: true
                    theme: root.theme
                    text: qsTr("One group")
                    highlighted: true
                    onClicked: multiFileCheckinDialog.finish("group")
                }
                Controls.Button {
                    objectName: "multiFileCheckinSeparateButton"
                    Layout.fillWidth: true
                    theme: root.theme
                    text: qsTr("Separately")
                    onClicked: multiFileCheckinDialog.finish("individual")
                }
                Controls.Button {
                    objectName: "multiFileCheckinCancelButton"
                    Layout.fillWidth: true
                    theme: root.theme
                    text: qsTr("Cancel")
                    onClicked: multiFileCheckinDialog.finish("cancel")
                }
            }
        }

        onClosed: {
            if (awaitingChoice) {
                awaitingChoice = false
                root.applicationController.resolve_multi_file_checkin("cancel")
            }
        }
    }

    Connections {
        target: root.applicationController
        function onCheckinFilesRequested() {
            checkinFilesDialog.open()
        }
        function onRevisionCheckinConfirmationRequested() {
            revisionCheckinDialog.open()
        }
        function onMultiFileCheckinModeRequested(fileCount) {
            root.askMultiFileMode(fileCount)
        }
    }
}

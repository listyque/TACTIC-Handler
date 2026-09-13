pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Rectangle {
    id: root
    objectName: "knowledgeAttachmentLibrary"
    required property var theme
    required property var controller
    required property var uploadController
    required property var stagingModel
    required property var uploadedModel
    required property var documentController
    property real maximumImageWidth: 560
    property string pendingDeleteToken: ""
    property string pendingDeleteTitle: ""
    property string copiedToken: ""
    signal contentChanged
    signal closeRequested
    signal insertionRequested
    signal imageInserted

    color: root.theme.surfaceContainerLow
    radius: root.theme.surfaceRadius
    border.width: 1
    border.color: root.theme.outlineVariant
    implicitHeight: content.implicitHeight + 20

    function upload() {
        if (root.uploadController.count === 0)
            return;
        root.contentChanged();
        root.controller.upload_attachments();
    }

    function chooseAttachments() {
        stagingPanel.chooseFiles();
    }

    ColumnLayout {
        id: content
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 10
        spacing: 9

        RowLayout {
            Layout.fillWidth: true
            spacing: 7

            Controls.MaterialIcon {
                name: "attachments-editor"
                size: 18
                color: root.theme.action
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 1
                Label {
                    text: qsTr("Attached files")
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.bodyLarge
                    font.weight: Font.DemiBold
                }
                Label {
                    Layout.fillWidth: true
                    text: qsTr("Files are uploaded and attached before you insert their permanent links into the article.")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.caption
                    wrapMode: Text.Wrap
                }
            }
            Controls.Button {
                objectName: "knowledgeUploadAttachments"
                theme: root.theme
                compact: true
                text: qsTr("Attach files")
                icon.name: "attachments-editor"
                enabled: !root.controller.busy
                onClicked: root.chooseAttachments()
            }
            Controls.CompactIconButton {
                objectName: "knowledgeCloseAttachments"
                theme: root.theme
                iconName: "times"
                toolTip: qsTr("Hide attached files")
                onClicked: root.closeRequested()
            }
        }

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: draftRow.implicitHeight + 14
            visible: root.controller.draft || root.controller.localDraft
            radius: root.theme.itemRadius
            color: root.theme.blend(root.theme.tertiary, root.theme.surfaceContainerLow, 0.10)
            border.width: 1
            border.color: root.theme.tertiary

            RowLayout {
                id: draftRow
                anchors.fill: parent
                anchors.margins: 7
                spacing: 7
                Controls.MaterialIcon {
                    name: "edit"
                    size: 16
                    color: root.theme.tertiary
                }
                Label {
                    Layout.fillWidth: true
                    text: root.controller.localDraft ? qsTr("Local draft. It has not been saved to the server yet.") : qsTr("Draft reserved on the server. Only you can see it until you save the article.")
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.caption
                    wrapMode: Text.Wrap
                }
            }
        }

        AttachmentStagingPanel {
            id: stagingPanel
            Layout.fillWidth: true
            theme: root.theme
            controller: root.uploadController
            attachmentModel: root.stagingModel
            showFileChooser: false
            emptyText: qsTr("Drop files here or attach them from disk")
            onFilesAdded: root.upload()
        }

        Controls.ResponsiveFlow {
            id: attachmentFlow
            objectName: "knowledgeUploadedAttachments"
            Layout.fillWidth: true
            visible: root.uploadedModel.count() > 0
            minimumCellWidth: 220
            preferredCellWidth: 560
            maximumColumns: 1
            spacing: 8

            Repeater {
                model: root.uploadedModel
                delegate: RowLayout {
                    id: attachmentItem
                    required property int index
                    required property string token
                    required property string title
                    required property string extension
                    required property string sizeText
                    required property string previewUrl
                    required property string webUrl
                    required property bool isImage
                    objectName: "knowledgeUploadedAttachment-" + index
                    width: attachmentFlow.cellWidth()
                    spacing: 5

                    AttachmentCard {
                        objectName: "knowledgeInsertAttachment"
                        Layout.fillWidth: true
                        theme: root.theme
                        title: attachmentItem.title
                        extension: attachmentItem.extension
                        previewUrl: attachmentItem.previewUrl
                        sizeText: attachmentItem.sizeText
                        local: false
                        compact: true
                        activationLabel: attachmentItem.isImage ? qsTr("Insert image") : qsTr("Insert link")
                        activationIcon: attachmentItem.isImage ? "image" : "link"
                        enabled: attachmentItem.webUrl.length > 0
                        onActivated: {
                            root.insertionRequested();
                            if (attachmentItem.isImage)
                                root.documentController.insert_image(attachmentItem.webUrl, attachmentItem.title, root.maximumImageWidth, attachmentItem.previewUrl);
                            else
                                root.documentController.insert_link(attachmentItem.webUrl, attachmentItem.title);
                            if (attachmentItem.isImage)
                                root.imageInserted();
                        }
                    }

                    Controls.CompactIconButton {
                        objectName: "knowledgeCopyAttachmentLink"
                        theme: root.theme
                        iconName: root.copiedToken === attachmentItem.token
                            ? "check" : "content-copy"
                        iconColor: root.copiedToken === attachmentItem.token
                            ? root.theme.action : root.theme.primaryText
                        toolTip: root.copiedToken === attachmentItem.token
                            ? qsTr("Copied") : qsTr("Copy web link")
                        enabled: attachmentItem.webUrl.length > 0
                        onClicked: {
                            root.controller.copy_attachment_web_url(
                                attachmentItem.token);
                            root.copiedToken = attachmentItem.token;
                        }
                    }
                    Controls.CompactIconButton {
                        objectName: "knowledgeDeleteAttachment"
                        theme: root.theme
                        iconName: "delete"
                        iconColor: root.theme.error
                        toolTip: qsTr("Delete file")
                        enabled: !root.controller.busy
                        onClicked: {
                            root.pendingDeleteToken = attachmentItem.token;
                            root.pendingDeleteTitle = attachmentItem.title;
                            deleteDialog.open();
                        }
                    }
                }
            }
        }

        Label {
            Layout.fillWidth: true
            visible: root.uploadedModel.count() === 0 && root.uploadController.count === 0
            text: qsTr("No files uploaded to this article yet.")
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.caption
        }
    }

    Controls.Dialog {
        id: deleteDialog
        objectName: "knowledgeDeleteAttachmentDialog"
        theme: root.theme
        modal: true
        anchors.centerIn: Overlay.overlay
        width: Math.min(420, root.width - 24)
        title: qsTr("Delete article file?")
        standardButtons: Dialog.NoButton
        contentItem: ColumnLayout {
            spacing: 10
            Label {
                Layout.fillWidth: true
                text: qsTr("The TACTIC snapshot for %1 will be retired.").arg(root.pendingDeleteTitle)
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.body
                wrapMode: Text.Wrap
            }
            RowLayout {
                Layout.fillWidth: true
                Item {
                    Layout.fillWidth: true
                }
                Controls.Button {
                    objectName: "knowledgeDeleteAttachmentCancel"
                    theme: root.theme
                    text: qsTr("Cancel")
                    onClicked: deleteDialog.close()
                }
                Controls.Button {
                    objectName: "knowledgeDeleteAttachmentConfirm"
                    theme: root.theme
                    text: qsTr("Delete")
                    destructive: true
                    onClicked: {
                        root.controller.remove_attachment(root.pendingDeleteToken);
                        deleteDialog.close();
                    }
                }
            }
        }
    }
}

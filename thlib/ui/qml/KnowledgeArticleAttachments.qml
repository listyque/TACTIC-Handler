pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

ColumnLayout {
    id: root

    required property var theme
    required property var controller
    required property var uploadedModel

    objectName: "knowledgeViewerAttachments"
    visible: root.uploadedModel && root.uploadedModel.count() > 0
    spacing: 7

    Label {
        Layout.fillWidth: true
        text: qsTr("Attached files")
        color: root.theme.secondaryText
        font.family: root.theme.fontFamily
        font.pointSize: Controls.Typography.label
        font.weight: Font.DemiBold
    }

    Controls.ResponsiveFlow {
        id: attachmentFlow

        Layout.fillWidth: true
        minimumCellWidth: 220
        preferredCellWidth: 280
        maximumColumns: 3
        spacing: 8

        Repeater {
            model: root.uploadedModel

            delegate: Item {
                id: attachmentItem

                required property int index
                required property string token
                required property string title
                required property string extension
                required property string sizeText
                required property string previewUrl
                required property string webUrl
                required property bool isImage

                objectName: "knowledgeViewerAttachmentItem-" + index
                width: attachmentFlow.cellWidth()
                implicitHeight: attachmentCard.implicitHeight

                AttachmentCard {
                    id: attachmentCard

                    objectName: "knowledgeViewerAttachment-"
                        + attachmentItem.index
                    anchors.fill: parent
                    theme: root.theme
                    title: attachmentItem.title
                    extension: attachmentItem.extension
                    previewUrl: attachmentItem.previewUrl
                    sizeText: attachmentItem.sizeText
                    local: true
                    activationLabel: attachmentItem.isImage
                        ? qsTr("Open image") : qsTr("Open attachment")
                    enabled: attachmentItem.webUrl.length > 0
                    animatePreview: false
                    onActivated: root.controller.open_link(
                        attachmentItem.webUrl)
                }
            }
        }
    }
}

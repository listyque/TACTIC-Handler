import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../controls" as Controls
import "../.." as Objects
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/objects/note.ui.mjs" as UI

Frame.FrameView {
    id: root
    required property var model
    required property var controller
    property var measured: ({})
    signal previewMenu(var anchor, var record, real localX, real localY)
    signal attachmentMenu(var anchor, var record, real localX, real localY)
    signal forwardedMessage(string conversationId, string messageId)
    function measure(part, height) {
        if (height <= 0)
            return;
        Qt.callLater(function () {
            if (measured[part] !== height)
                measured = Object.assign({}, measured, {
                    [part]: height
                });
        });
    }
    implicitHeight: scene.height
    scene: UI.body({
        status: model.entryType === "status",
        statusText: model.statusTo,
        statusColor: String(model.statusColor || ""),
        text: model.entryType !== "status" && !!model.displayHtml,
        previews: !!(model.skeyPreviews || []).length,
        attachments: !!(model.attachments || []).length
    }, width, measured)
    views: ({
            status: statusPort,
            text: textPort,
            previews: previewsPort,
            attachments: attachmentsPort
        })
    Component {
        id: statusPort
        RowLayout {
            spacing: 8
            onImplicitHeightChanged: root.measure("status", implicitHeight)
            Controls.MaterialIcon {
                name: "status"
                size: 22
                color: root.model.statusColor || root.theme.action
            }
            Label {
                Layout.fillWidth: true
                text: root.model.statusTo || "—"
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 13
                font.weight: Font.Medium
                wrapMode: Text.Wrap
            }
        }
    }
    Component {
        id: textPort
        Objects.MessageBodyText {
            objectName: "noteBodyText"

            onContentHeightChanged: root.measure("text", contentHeight)
            theme: root.theme
            sourceHtml: root.model.displayHtml
            rawText: root.model.body

            onLinkActivated: link => root.controller.open_link(link)
        }
    }
    Component {
        id: previewsPort
        ColumnLayout {
            width: parent ? parent.width : 0
            onImplicitHeightChanged: root.measure("previews", implicitHeight)
            spacing: UI.bodyMetrics.gap
            Repeater {
                model: root.model.skeyPreviews
                delegate: Objects.SKeyPreviewCard {
                    id: skeyCard
                    required property var modelData
                    Layout.fillWidth: true
                    theme: root.theme
                    preview: modelData
                    onActivated: {
                        if (modelData.kind !== "message") {
                            root.controller.open_skey_preview(modelData.searchKey);
                            return;
                        }
                        const conversationId = String(modelData.conversationId || "");
                        const messageId = String(modelData.itemCode || modelData.searchKey || "");
                        if (conversationId.length && messageId.length)
                            root.forwardedMessage(conversationId, messageId);
                    }
                    onRetryRequested: root.controller.retry_skey_preview(modelData.searchKey)
                    onNestedActivated: searchKey => root.controller.open_skey_preview(searchKey)
                    onNestedRetryRequested: searchKey => root.controller.retry_skey_preview(searchKey)
                    onContextRequested: (localX, localY) => {
                        root.previewMenu(skeyCard, modelData, localX, localY);
                    }
                }
            }
        }
    }
    Component {
        id: attachmentsPort
        Controls.ResponsiveFlow {
            id: noteAttachmentFlow
            width: parent ? parent.width : 0
            onImplicitHeightChanged: root.measure("attachments", implicitHeight)
            minimumCellWidth: UI.bodyMetrics.minimumCellWidth
            preferredCellWidth: UI.bodyMetrics.preferredCellWidth
            maximumColumns: UI.bodyMetrics.maximumColumns
            spacing: UI.bodyMetrics.gap
            Repeater {
                model: root.model.attachments
                delegate: Objects.AttachmentCard {
                    id: attachmentCard
                    required property var modelData
                    width: imageAttachment ? noteAttachmentFlow.width : noteAttachmentFlow.cellWidth()
                    theme: root.theme
                    title: String(modelData.title || "Attachment")
                    extension: String(modelData.extension || "")
                    previewUrl: String(modelData.previewUrl || "")
                    sizeText: String(modelData.size || "")
                    local: !!modelData.local
                    onActivated: root.controller.attachment_action(modelData.token, "open")
                    onContextRequested: (localX, localY) => {
                        root.attachmentMenu(attachmentCard, modelData, localX, localY);
                    }
                }
            }
        }
    }
}

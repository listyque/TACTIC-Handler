import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../.." as Messages
import "../../controls" as Controls
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/messages/message.ui.mjs" as UI

Frame.FrameView {
    id: root
    required property var model
    required property var controller
    required property var host
    property var measured: ({})
    property var naturalWidths: ({})
    implicitWidth: Object.values(naturalWidths).reduce((maximum, value) => Math.max(maximum, value), 0)
    implicitHeight: scene.height
    function measure(part, item) {
        Qt.callLater(function () {
            if (!item)
                return;
            const height = part === "text" ? item.contentHeight : item.implicitHeight;
            const natural = item.implicitWidth;
            if (natural > 0 && naturalWidths[part] !== natural)
                naturalWidths = Object.assign({}, naturalWidths, {
                    [part]: natural
                });
            if (height > 0 && measured[part] !== height)
                measured = Object.assign({}, measured, {
                    [part]: height
                });
        });
    }
    scene: UI.body({
        reply: !!model.replyTo?.messageId,
        forward: !!model.forwardedFrom?.messageId,
        previews: !!model.skeyPreviews?.length,
        attachments: !!model.attachments?.length,
        text: !!model.displayHtml,
        reactions: !!model.reactions?.length
    }, width, measured)
    views: ({
            reply: replyPort,
            forward: forwardPort,
            previews: previewsPort,
            attachments: attachmentsPort,
            text: textPort,
            reactions: reactionsPort
        })
    Component {
        id: replyPort
        Messages.MessageReplyPreview {
            id: replyContent
            onImplicitHeightChanged: root.measure("reply", replyContent)
            Component.onCompleted: root.measure("reply", replyContent)
            visible: root.model.replyTo && String(root.model.replyTo.messageId || "").length > 0
            theme: root.theme
            sender: String(root.model.replyTo.senderDisplay || "")
            body: String(root.model.replyTo.body || "")
            available: root.model.replyTo.available !== false
            onActivated: root.controller.show_message(String(root.model.replyTo.messageId || ""))
        }
    }
    Component {
        id: forwardPort
        Messages.MessageForwardPreview {
            id: forwardContent
            onImplicitHeightChanged: root.measure("forward", forwardContent)
            Component.onCompleted: root.measure("forward", forwardContent)
            visible: root.model.forwardedFrom && String(root.model.forwardedFrom.messageId || "").length > 0
            theme: root.theme
            sender: String(root.model.forwardedFrom.senderDisplay || "")
            body: String(root.model.forwardedFrom.body || "")
            attachmentCount: (root.model.forwardedFrom.attachments || []).length
            available: root.model.forwardedFrom.available !== false
            onActivated: root.controller.open_forwarded_message(String(root.model.forwardedFrom.conversationId || ""), String(root.model.forwardedFrom.messageId || ""))
        }
    }
    Component {
        id: previewsPort
        ColumnLayout {
            id: previewsContent
            onImplicitHeightChanged: root.measure("previews", previewsContent)
            Component.onCompleted: root.measure("previews", previewsContent)
            visible: root.model.skeyPreviews && root.model.skeyPreviews.length > 0
            spacing: 6
            Repeater {
                model: root.model.skeyPreviews
                delegate: Messages.SKeyPreviewCard {
                    id: skeyCard
                    Layout.fillWidth: true
                    required property var modelData
                    required property int index
                    objectName: "messageSkeyPreviewCard-" + index
                    theme: root.theme
                    preview: modelData
                    animatePreview: false
                    onActivated: {
                        if (modelData.kind !== "message") {
                            root.controller.open_skey_preview(modelData.searchKey);
                            return;
                        }
                        const conversationId = String(modelData.conversationId || "");
                        const messageId = String(modelData.itemCode || modelData.searchKey || "");
                        if (!conversationId.length || !messageId.length)
                            return;
                        if (conversationId === root.controller.conversationId)
                            root.controller.show_message(messageId);
                        else
                            root.controller.open_forwarded_message(conversationId, messageId);
                    }
                    onRetryRequested: root.controller.retry_skey_preview(modelData.searchKey)
                    onNestedActivated: searchKey => root.controller.open_skey_preview(searchKey)
                    onNestedRetryRequested: searchKey => root.controller.retry_skey_preview(searchKey)
                    onContextRequested: (localX, localY) => {
                        root.host.skeyMenuValue = modelData.searchKey;
                        root.host.skeyMenuFailed = modelData.status === "error";
                        root.host.skeyMenuCanOpen = modelData.kind !== "message" || modelData.canOpen === true;
                        root.host.timelineSkeyMenu.openAt(skeyCard, localX, localY);
                    }
                }
            }
        }
    }
    Component {
        id: attachmentsPort
        Controls.ResponsiveFlow {
            id: messageAttachmentFlow
            onImplicitHeightChanged: root.measure("attachments", messageAttachmentFlow)
            Component.onCompleted: root.measure("attachments", messageAttachmentFlow)
            visible: root.model.attachments && root.model.attachments.length > 0
            minimumCellWidth: 210
            preferredCellWidth: 240
            maximumColumns: 2
            spacing: 8
            Repeater {
                model: root.model.attachments
                delegate: Messages.AttachmentCard {
                    id: attachmentCard
                    objectName: "messageAttachmentCard-" + token
                    required property string token
                    required property int size
                    required property bool hasWebPreview
                    width: imageAttachment ? messageAttachmentFlow.width : messageAttachmentFlow.cellWidth()
                    theme: root.theme
                    webPreview: hasWebPreview
                    sizeText: root.host.formatFileSize(size)
                    animatePreview: false
                    onActivated: root.controller.attachment_action(token, "open")
                    onContextRequested: (localX, localY) => {
                        root.host.attachmentMenuToken = token;
                        root.host.attachmentMenuLocal = local;
                        root.host.attachmentMenuImage = ["JPG", "JPEG", "PNG", "WEBP", "GIF", "BMP"].indexOf(extension) >= 0;
                        root.host.timelineAttachmentMenu.openAt(attachmentCard, localX, localY);
                    }
                }
            }
        }
    }
    Component {
        id: textPort
        Messages.MessageBodyText {
            id: messageBodyContent
            onImplicitHeightChanged: root.measure("text", messageBodyContent)
            Component.onCompleted: root.measure("text", messageBodyContent)
            onContentHeightChanged: root.measure("text", messageBodyContent)
            objectName: "messageBodyText"
            theme: root.theme
            sourceHtml: root.model.displayHtml
            rawText: root.model.body
            visible: sourceHtml.length > 0
            onLinkActivated: link => root.controller.open_link(link)
        }
    }
    Component {
        id: reactionsPort
        Flow {
            id: reactionsContent
            onImplicitHeightChanged: root.measure("reactions", reactionsContent)
            Component.onCompleted: root.measure("reactions", reactionsContent)
            // Flow owns its implicit height even when the whole chat
            // is hidden. Effective visibility must not change geometry.
            visible: root.model.reactions && root.model.reactions.length > 0
            layoutDirection: Qt.RightToLeft
            spacing: 5
            Repeater {
                model: root.model.reactions || []
                delegate: Messages.MessageReactionChip {
                    required property var modelData
                    width: implicitWidth
                    height: implicitHeight
                    theme: root.theme
                    emoji: String(modelData.emoji || "")
                    count: Number(modelData.count || 0)
                    checked: modelData.reactedByMe === true
                    toolTip: String(modelData.namesText || "")
                    enabled: !root.model.reactionPending
                    onClicked: root.controller.toggle_reaction(root.model.messageId, String(modelData.emoji || ""))
                }
            }
        }
    }
}

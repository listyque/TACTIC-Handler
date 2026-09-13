import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

ListView {
    id: messages
    required property var theme
    required property var host
    required property var controller
    required property var timelineModel
    required property bool current
    required property bool historyHasMore
    property bool presented: false
    objectName: "messageTimelineList"
    anchors.fill: parent
    property real wheelTargetY: contentY
    readonly property real minimumContentY:
        originY - topMargin
    readonly property real maximumContentY: Math.max(
        minimumContentY,
        originY + contentHeight + bottomMargin - height)
    readonly property bool awayFromEnd: contentHeight > height
        && contentY < maximumContentY - 36
    clip: true
    opacity: !messages.current || host.messagePresentationReady ? 1 : 0
    spacing: 0
    model: messages.timelineModel
    visible: messages.current
    boundsBehavior: Flickable.StopAtBounds
    flickDeceleration: 3600
    maximumFlickVelocity: 4800
    pixelAligned: false
    cacheBuffer: 280
    reuseItems: true
    topMargin: Math.max(0, height - contentHeight)
    ScrollBar.vertical: Controls.ScrollBar { theme: messages.theme }

    Image {
        parent: messages
        anchors.fill: parent
        z: -100
        source: messages.theme.dark
            ? "../assets/chat_bg_dark.png"
            : "../assets/chat_bg_light.png"
        fillMode: Image.Tile
        asynchronous: true
        cache: true
        smooth: true
        mipmap: true
    }

    Rectangle {
        parent: messages
        anchors.fill: parent
        z: -99
        color: messages.theme.dark
            ? messages.theme.workspace
            : messages.theme.primaryText
        opacity: messages.theme.dark ? 0.74 : 0.82
    }

    function cancelScrollAnimation() {
        wheelScroll.stop()
        jumpToLatestAnimation.stop()
        wheelTargetY = contentY
    }

    function scrollWithWheel(pixelDelta, angleDelta) {
        const delta = pixelDelta !== 0
            ? pixelDelta * 1.65
            : (angleDelta / 120) * 148
        if (delta === 0)
            return
        jumpToLatestAnimation.stop()
        const baseY = wheelScroll.running
            ? wheelTargetY : contentY
        wheelTargetY = Math.max(
            minimumContentY,
            Math.min(maximumContentY, baseY - delta)
        )
        wheelScroll.stop()
        wheelScroll.to = wheelTargetY
        wheelScroll.start()
    }

    function scrollToLatest() {
        wheelScroll.stop()
        jumpToLatestAnimation.stop()
        cancelFlick()
        if (count <= 0)
            return
        forceLayout()
        const startY = contentY
        positionViewAtIndex(count - 1, ListView.End)
        positionViewAtEnd()
        const endY = contentY
        const distance = Math.abs(endY - startY)
        if (distance > height * 2.5) {
            settleAtLatest()
            return
        }
        contentY = startY
        jumpToLatestAnimation.to = endY
        jumpToLatestAnimation.start()
    }

    function settleAtLatest() {
        if (count <= 0)
            return
        forceLayout()
        positionViewAtIndex(count - 1, ListView.End)
        positionViewAtEnd()
        wheelTargetY = contentY
    }

    function positionCachedAtLatest() {
        if (count <= 0)
            return
        positionViewAtIndex(count - 1, ListView.End)
        positionViewAtEnd()
        wheelTargetY = contentY
    }

    NumberAnimation {
        id: wheelScroll
        target: messages
        property: "contentY"
        duration: theme.scrollMotion
        easing.type: Easing.OutCubic
    }

    NumberAnimation {
        id: jumpToLatestAnimation
        target: messages
        property: "contentY"
        duration: theme.motionMedium
        easing.type: Easing.OutCubic
        onFinished: messages.settleAtLatest()
    }

    WheelHandler {
        target: null
        blocking: true
        onWheel: function(event) {
            messages.scrollWithWheel(
                event.pixelDelta.y,
                event.angleDelta.y
            )
            event.accepted = true
        }
    }

    onFlickStarted: cancelScrollAnimation()
    onCountChanged: {
        if (messages.current && !host.messagePresentationReady)
            host.finishConversationPresentation()
    }
    onContentHeightChanged: {
        if (messages.current && !host.messagePresentationReady)
            host.finishConversationPresentation()
    }
    header: Item {
        width: messages.width
        height: messages.historyHasMore ? 56 : 12
        Controls.Button {
            anchors.centerIn: parent
            visible: messages.historyHasMore
            theme: messages.theme
            text: qsTr("Earlier messages")
            icon.name: "history"
            tonal: true
            enabled: messages.current && !controller.busy
            onClicked: controller.load_more()
        }
    }
    footer: Item {
        width: messages.width
        height: 12
    }
    Column {
        anchors.centerIn: parent
        visible: messages.current && messages.count === 0
            && !controller.busy
        spacing: 8
        Controls.MaterialIcon {
            anchors.horizontalCenter: parent.horizontalCenter
            name: controller.conversationId.length > 0
                ? "chat" : "forum"
            size: 30
            color: messages.theme.secondaryText
            opacity: 0.7
        }
        Label {
            anchors.horizontalCenter: parent.horizontalCenter
            text: controller.conversationId.length > 0
                ? (controller.messageSearch.length > 0
                    ? qsTr("No matching messages")
                    : qsTr("No messages yet"))
                : qsTr("Select a conversation")
            color: messages.theme.secondaryText
            font.family: messages.theme.fontFamily
            font.pointSize: Controls.Typography.bodyLarge
        }
        Label {
            anchors.horizontalCenter: parent.horizontalCenter
            visible: controller.conversationId.length > 0
            text: controller.messageSearch.length > 0
                ? qsTr("Try another search phrase")
                : qsTr("Start the conversation below")
            color: messages.theme.secondaryText
            font.family: messages.theme.fontFamily
            font.pointSize: Controls.Typography.label
            opacity: 0.7
        }
    }
    delegate: Item {
        id: messageRow
        required property string messageId
        required property int index
        required property string sender
        required property string senderDisplay
        required property string avatarUrl
        required property string initials
        required property color senderColor
        required property string body
        required property string bodyHtml
        required property string displayHtml
        required property var skeyPreviews
        required property string timestamp
        required property string timePretty
        required property string timeSimple
        required property bool isOwn
        required property bool unread
        required property var attachments
        required property bool canEdit
        required property bool edited
        required property bool pinned
        required property string editedBy
        required property string editedAt
        required property var editHistory
        required property var replyTo
        required property var forwardedFrom
        required property bool forwardSelected
        required property var reactions
        required property bool reactionPending
        required property string deliveryStatus
        required property int deliveryRecipientCount
        required property int deliveryDeliveredCount
        required property int deliveryReadCount
        required property bool groupFirst
        required property bool groupLast
        width: messages.width
        height: messageFrame.height + (messageRow.groupLast
            ? messages.theme.communicationListSpacing
            : messages.theme.communicationGroupedSpacing)

        MessageTimelineFrame {
            id: messageFrame
            objectName: "messageTimelineFrame"
            width: parent.width
            theme: messages.theme
            outgoing: messageRow.isOwn
            avatarUrl: messageRow.avatarUrl
            initials: messageRow.initials
            avatarColor: messageRow.senderColor
            groupFirst: messageRow.groupFirst
            groupLast: messageRow.groupLast
            forwardSelected: messageRow.forwardSelected
            current: messages.currentIndex === messageRow.index
            unread: messageRow.unread
            selectionMode:
                messages.current && controller.forwardSelectionCount > 0
            onContextRequested: (localX, localY) => {
                host.prepareMessageActions(
                    messageRow, messageFrame.bubbleItem)
                host.timelineActions.openAt(
                    messageFrame.bubbleItem, localX, localY)
            }
            onSelectionRequested:
                controller.toggle_forward_selection(
                    messageRow.messageId
                )

                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            Layout.fillWidth: true
                            visible: messageRow.groupFirst
                            text: messageRow.senderDisplay
                                + (messageRow.sender
                                    && messageRow.senderDisplay !== messageRow.sender
                                    ? " (" + messageRow.sender + ")" : "")
                            color: messageRow.senderColor
                            font.family: messages.theme.fontFamily
                            font.pointSize: Controls.Typography.label
                            font.weight: Font.DemiBold
                            font.underline: senderMouse.containsMouse
                            elide: Text.ElideRight
                            MouseArea {
                                id: senderMouse
                                anchors.fill: parent
                                enabled: messageRow.sender.length > 0
                                hoverEnabled: true
                                cursorShape: enabled
                                    ? Qt.PointingHandCursor : Qt.ArrowCursor
                                onClicked: userController.open_profile(
                                    messageRow.sender)
                            }
                        }
                        Item {
                            objectName: "messageMetadataSpacer"
                            visible: !messageRow.groupFirst
                            Layout.fillWidth: true
                            implicitWidth: 0
                            implicitHeight: 1
                        }
                        Controls.MaterialIcon {
                            id: deliveryIcon
                            visible: messageRow.isOwn
                                && messageRow.deliveryRecipientCount > 0
                            name: messageRow.deliveryStatus === "sent"
                                ? "check" : "done-all"
                            color: messageRow.deliveryStatus === "read"
                                ? messages.theme.action
                                : messages.theme.secondaryText
                            size: 11
                            opacity: messageRow.deliveryStatus === "sent"
                                ? 0.72 : 1
                            MouseArea {
                                id: deliveryMouse
                                anchors.fill: parent
                                hoverEnabled: true
                            }
                            Controls.ToolTip {
                                theme: messages.theme
                                visible: deliveryMouse.containsMouse
                                text: messageRow.deliveryStatus === "read"
                                    ? qsTr("Read by %1 of %2")
                                        .arg(messageRow.deliveryReadCount)
                                        .arg(messageRow.deliveryRecipientCount)
                                    : messageRow.deliveryStatus === "delivered"
                                        ? qsTr("Delivered to %1 of %2")
                                            .arg(messageRow.deliveryDeliveredCount)
                                            .arg(messageRow.deliveryRecipientCount)
                                        : qsTr("Sent")
                            }
                        }
                        Label {
                            text: messageRow.timePretty
                            color: messages.theme.secondaryText
                            font.family: messages.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
                            MouseArea {
                                id: messageTimeMouse
                                anchors.fill: parent
                                hoverEnabled: true
                            }
                            Controls.ToolTip {
                                theme: messages.theme
                                visible: messageTimeMouse.containsMouse
                                    && messageRow.timeSimple.length > 0
                                text: messageRow.timeSimple
                            }
                        }
                        Label {
                            id: editedLabel
                            visible: messageRow.edited
                            text: qsTr("Edited")
                            color: messages.theme.secondaryText
                            font.family: messages.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
                            font.underline: editedMouse.containsMouse
                            MouseArea {
                                id: editedMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    host.selectedEditHistory =
                                        messageRow.editHistory
                                    host.openBelow(
                                        editedLabel, host.timelineEditHistory
                                    )
                                }
                            }
                            Controls.ToolTip {
                                theme: messages.theme
                                visible: editedMouse.containsMouse
                                text: qsTr("Last edited by ")
                                    + messageRow.editedBy + "  ·  "
                                    + messageRow.editedAt
                            }
                        }
                        Controls.CompactIconButton {
                            visible: controller.forwardSelectionCount > 0
                            theme: messages.theme
                            iconName: messageRow.forwardSelected
                                ? "check-circle" : "circle"
                            iconColor: messageRow.forwardSelected
                                ? messages.theme.tertiary
                                : messages.theme.secondaryText
                            toolTip: messageRow.forwardSelected
                                ? qsTr("Remove from forwarding")
                                : qsTr("Add to forwarding")
                            enabled: !controller.busy
                            onClicked: controller.toggle_forward_selection(
                                messageRow.messageId)
                        }
                        Controls.CompactIconButton {
                            visible: messageRow.pinned
                            theme: messages.theme
                            iconName: "push-pin"
                            iconColor: messages.theme.tertiary
                            backgroundColor: messages.theme.tertiaryContainer
                            round: true
                            toolTip: qsTr("Unpin message")
                            enabled: !controller.busy
                            onClicked: controller.unpin_message(
                                messageRow.messageId)
                        }
                        Controls.CompactIconButton {
                            id: addReactionButton
                            opacity: messageFrame.hovered
                                || host.timelineReactions.messageId
                                    === messageRow.messageId
                                ? 1 : 0
                            enabled: opacity > 0
                                && !messageRow.reactionPending
                            theme: messages.theme
                            iconName: "emoji"
                            toolTip: qsTr("Add reaction")
                            Behavior on opacity {
                                NumberAnimation {
                                    duration: messages.theme.hoverMotionFast
                                    easing.type: Easing.OutCubic
                                }
                            }
                            onClicked: host.openReactionPicker(
                                messageRow.messageId,
                                addReactionButton)
                        }
                        Controls.CompactIconButton {
                            id: messageActionsButton
                            opacity: messageFrame.hovered ? 1 : 0
                            enabled: opacity > 0
                                && !controller.busy
                            theme: messages.theme
                            iconName: "more-vert"
                            toolTip: qsTr("Message actions")
                            Behavior on opacity {
                                NumberAnimation {
                                    duration: messages.theme.hoverMotionFast
                                    easing.type: Easing.OutCubic
                                }
                            }
                            onClicked: {
                                host.prepareMessageActions(
                                    messageRow, messageActionsButton)
                                host.timelineActions.toggleBelow(
                                    messageActionsButton)
                            }
                        }
                    }

                    MessageReplyPreview {
                        visible: messageRow.replyTo
                            && String(
                                messageRow.replyTo.messageId || ""
                            ).length > 0
                        Layout.fillWidth: true
                        theme: messages.theme
                        sender: String(
                            messageRow.replyTo.senderDisplay || ""
                        )
                        body: String(messageRow.replyTo.body || "")
                        available: messageRow.replyTo.available !== false
                        onActivated: controller.show_message(
                            String(messageRow.replyTo.messageId || ""))
                    }

                    MessageForwardPreview {
                        visible: messageRow.forwardedFrom
                            && String(
                                messageRow.forwardedFrom.messageId || ""
                            ).length > 0
                        Layout.fillWidth: true
                        theme: messages.theme
                        sender: String(
                            messageRow.forwardedFrom.senderDisplay || ""
                        )
                        body: String(
                            messageRow.forwardedFrom.body || ""
                        )
                        attachmentCount: (
                            messageRow.forwardedFrom.attachments || []
                        ).length
                        available: messageRow.forwardedFrom.available !== false
                        onActivated: controller.open_forwarded_message(
                            String(
                                messageRow.forwardedFrom.conversationId || ""
                            ),
                            String(
                                messageRow.forwardedFrom.messageId || ""
                            ))
                    }

                    MessageBodyText {
                        objectName: "messageBodyText"
                        Layout.fillWidth: true
                        Layout.preferredHeight: contentHeight
                        theme: messages.theme
                        sourceHtml: messageRow.displayHtml
                        rawText: messageRow.body
                        visible: sourceHtml.length > 0
                        onLinkActivated: link =>
                            controller.open_link(link)
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        visible: messageRow.skeyPreviews
                            && messageRow.skeyPreviews.length > 0
                        spacing: 6
                        Repeater {
                            model: messageRow.skeyPreviews
                            delegate: SKeyPreviewCard {
                                id: skeyCard
                                required property var modelData
                                required property int index
                                objectName: "messageSkeyPreviewCard-" + index
                                Layout.fillWidth: true
                                theme: messages.theme
                                preview: modelData
                                animatePreview: false
                                onActivated: {
                                    if (modelData.kind !== "message") {
                                        controller.open_skey_preview(
                                            modelData.searchKey)
                                        return
                                    }
                                    const conversationId = String(
                                        modelData.conversationId || "")
                                    const messageId = String(
                                        modelData.itemCode
                                            || modelData.searchKey || "")
                                    if (!conversationId.length
                                            || !messageId.length)
                                        return
                                    if (conversationId
                                            === controller.conversationId)
                                        controller.show_message(messageId)
                                    else
                                        controller.open_forwarded_message(
                                            conversationId, messageId)
                                }
                                onRetryRequested: controller.retry_skey_preview(
                                    modelData.searchKey)
                                onNestedActivated: searchKey =>
                                    controller.open_skey_preview(searchKey)
                                onNestedRetryRequested: searchKey =>
                                    controller.retry_skey_preview(searchKey)
                                onContextRequested: (localX, localY) => {
                                    host.skeyMenuValue = modelData.searchKey
                                    host.skeyMenuFailed = modelData.status === "error"
                                    host.skeyMenuCanOpen = modelData.kind !== "message"
                                        || modelData.canOpen === true
                                    host.timelineSkeyMenu.openAt(
                                        skeyCard, localX, localY)
                                }
                            }
                        }
                    }

                    Controls.ResponsiveFlow {
                        id: messageAttachmentFlow
                        Layout.fillWidth: true
                        visible: messageRow.attachments
                            && messageRow.attachments.length > 0
                        minimumCellWidth: 210
                        preferredCellWidth: 240
                        maximumColumns: 2
                        spacing: 8
                        Repeater {
                            model: messageRow.attachments
                            delegate: AttachmentCard {
                                id: attachmentCard
                                required property string token
                                required property int size
                                width: imageAttachment
                                    ? messageAttachmentFlow.width
                                    : messageAttachmentFlow.cellWidth()
                                theme: messages.theme
                                sizeText: host.formatFileSize(size)
                                animatePreview: false
                                onActivated:
                                    controller.attachment_action(
                                        token, "open")
                                onContextRequested: (localX, localY) => {
                                    host.attachmentMenuToken = token
                                    host.attachmentMenuLocal = local
                                    host.attachmentMenuImage = [
                                        "JPG", "JPEG", "PNG", "WEBP", "GIF", "BMP"
                                    ].indexOf(extension) >= 0
                                    host.timelineAttachmentMenu.openAt(
                                        attachmentCard, localX, localY)
                                }
                            }
                        }
                    }

                    Flow {
                        Layout.fillWidth: true
                        Layout.preferredHeight: visible
                            ? childrenRect.height : 0
                        visible: messageRow.reactions
                            && messageRow.reactions.length > 0
                        layoutDirection: Qt.RightToLeft
                        spacing: 5
                        Repeater {
                            model: messageRow.reactions || []
                            delegate: MessageReactionChip {
                                required property var modelData
                                width: implicitWidth
                                height: implicitHeight
                                theme: messages.theme
                                emoji: String(modelData.emoji || "")
                                count: Number(modelData.count || 0)
                                checked: modelData.reactedByMe === true
                                toolTip: String(
                                    modelData.namesText || "")
                                enabled: !messageRow.reactionPending
                                onClicked:
                                    controller.toggle_reaction(
                                        messageRow.messageId,
                                        String(modelData.emoji || ""))
                            }
                        }
                    }
        }
    }

    Controls.CompactIconButton {
        parent: messages
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.rightMargin: 16
        anchors.bottomMargin: 16
        z: 200
        width: 44
        height: 44
        opacity: messages.awayFromEnd ? 1 : 0
        visible: opacity > 0
        enabled: opacity > 0
        theme: messages.theme
        iconName: "keyboard_arrow_down"
        iconSize: 23
        iconColor: messages.theme.primaryText
        backgroundColor: messages.theme.surfaceContainerHighest
        round: true
        elevated: true
        toolTip: qsTr("Jump to latest message")

        Behavior on opacity {
            NumberAnimation {
                duration: messages.theme.motionMedium
                easing.type: Easing.OutCubic
            }
        }

        onClicked: messages.scrollToLatest()
    }
}

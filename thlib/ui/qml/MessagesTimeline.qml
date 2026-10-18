import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls
import "features/messages" as MessagesFeature

Flickable {
    id: messages
    required property var theme
    required property var host
    required property var controller
    required property var timelineModel
    required property bool current
    required property bool historyHasMore
    property bool presented: false
    property string lastRevealedMessageId: ""
    readonly property int count: messageItems.count
    property int currentIndex: -1
    readonly property var currentItem: messageItems.itemAt(currentIndex)
    property bool followBottom: true
    property var viewportAnchor: null
    property real viewportAnchorOffset: 0
    objectName: "messageTimelineList"
    anchors.fill: parent
    property real wheelTargetY: contentY
    readonly property real minimumContentY: 0
    readonly property real maximumContentY: Math.max(
        minimumContentY,
        contentHeight - height)
    readonly property bool awayFromEnd: contentHeight > height
        && contentY < maximumContentY - 36
    clip: true
    opacity: !messages.current || host.messagePresentationReady ? 1 : 0
    visible: messages.current
    boundsBehavior: Flickable.StopAtBounds
    flickDeceleration: 3600
    maximumFlickVelocity: 4800
    pixelAligned: false
    contentWidth: width
    contentHeight: Math.max(height, messageColumn.height)
    flickableDirection: Flickable.VerticalFlick
    ScrollBar.vertical: Controls.ScrollBar {
        id: timelineScrollBar
        theme: messages.theme
    }
    Connections {
        target: timelineScrollBar
        function onPressedChanged() {
            messages.followBottom = !timelineScrollBar.pressed && messages.atYEnd
        }
    }

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

    function cancelWheelScroll() {
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
        followBottom = false
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
        followBottom = false
        messageColumn.forceLayout()
        jumpToLatestAnimation.to = maximumContentY
        jumpToLatestAnimation.start()
    }

    function settleAtLatest() {
        followBottom = true
        messageColumn.forceLayout()
        contentY = maximumContentY
        wheelTargetY = contentY
    }

    function keepBottomAfterLayout() {
        if (followBottom && !moving && !timelineScrollBar.pressed)
            contentY = maximumContentY
    }

    function captureViewportAnchor() {
        if (followBottom)
            return
        const top = contentY - messageColumn.y
        for (let row = 0; row < count; ++row) {
            const item = messageItems.itemAt(row)
            if (item && item.y + item.height > top) {
                viewportAnchor = item
                viewportAnchorOffset = messageColumn.y + item.y - contentY
                return
            }
        }
    }

    function restoreViewportAnchor() {
        if (!followBottom && viewportAnchor && !moving
                && !wheelScroll.running && !timelineScrollBar.pressed)
            contentY = Math.max(0, Math.min(maximumContentY,
                messageColumn.y + viewportAnchor.y - viewportAnchorOffset))
    }

    Connections {
        target: messages.viewportAnchor
        function onYChanged() { Qt.callLater(messages.restoreViewportAnchor) }
    }

    function revealLatestOnce() {
        if (count <= 0)
            return
        const messageId = String(timelineModel.get(count - 1).messageId || "")
        if (!messageId.length || messageId === lastRevealedMessageId)
            return
        lastRevealedMessageId = messageId
        cancelWheelScroll()
        cancelFlick()
        settleAtLatest()
    }

    function focusMessage(row) {
        cancelWheelScroll()
        messageColumn.forceLayout()
        const item = messageItems.itemAt(row)
        if (!item)
            return
        followBottom = row === count - 1
        contentY = followBottom ? maximumContentY : Math.max(0, Math.min(
            maximumContentY, messageColumn.y + item.y - (height - item.height) / 2))
        currentIndex = row
    }

    NumberAnimation {
        id: wheelScroll
        target: messages
        property: "contentY"
        duration: theme.scrollMotion
        easing.type: Easing.OutCubic
        onFinished: messages.followBottom = messages.atYEnd
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

    onFlickStarted: cancelWheelScroll()
    onMovementStarted: followBottom = false
    onMovementEnded: followBottom = atYEnd
    onContentYChanged: {
        if (contentY < maximumContentY - 0.5)
            followBottom = false
        captureViewportAnchor()
    }
    onHeightChanged: Qt.callLater(messages.keepBottomAfterLayout)
    onCountChanged: {
        if (messages.current && !host.messagePresentationReady)
            host.finishConversationPresentation()
    }
    onContentHeightChanged: {
        Qt.callLater(messages.keepBottomAfterLayout)
        if (messages.current && !host.messagePresentationReady)
            host.finishConversationPresentation()
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
    // Lay out only loaded pages, using exact card heights. A virtualized
    // ListView estimates unseen rich-text heights and changes its scroll range
    // while scrolling. The retained column never recreates cards on a wheel step.
    // ponytail: cost grows with loaded pages; virtualization needs exact row heights.
    Column {
        id: messageColumn
        objectName: "messageCardsColumn"
        width: messages.width
        y: Math.max(0, messages.height - height)
        Item {
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
        Repeater {
            id: messageItems
            model: messages.timelineModel
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
            mediaAttachments: messageRow.attachments
                && messageRow.attachments.some(attachment =>
                    /^(jpe?g|png|webp|gif|bmp|tiff?|tga|exr|hdr|svg|heic|avif)$/i
                        .test(String(attachment.extension || "")))
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

                    MessagesFeature.MessageHeader {
                        objectName: "messageMetadataRow"
                        Layout.fillWidth: true
                        Layout.minimumHeight: 18
                        Layout.preferredHeight: 18
                        Layout.maximumHeight: 18
                        theme: messages.theme
                        model: messageRow
                        controller: messages.controller
                        host: messages.host
                        hovered: messageFrame.hovered
                        padding: messageFrame.bubblePadding
                    }


                    MessagesFeature.MessageBody {
                        Layout.fillWidth: true
                        Layout.preferredHeight: implicitHeight
                        theme: messages.theme
                        model: messageRow
                        controller: messages.controller
                        host: messages.host
                    }

        }
    }

        }
        Item { width: messages.width; height: 12 }
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

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    property bool outgoing: false
    property string avatarUrl: ""
    property string initials: "?"
    property color avatarColor: theme.action
    property bool groupFirst: true
    property bool groupLast: true
    property bool forwardSelected: false
    property bool current: false
    property bool unread: false
    property bool selectionMode: false
    default property alias contentData: bubbleContent.data
    readonly property alias bubbleItem: messageBubble
    readonly property bool hovered: bubbleHover.hovered
    readonly property real avatarExtent: width < 380 ? 34 : 40
    readonly property real outerMargin: width < 380 ? 8 : 12
    readonly property real bubblePadding: width < 380 ? 7 : 8
    readonly property real bubbleSpacing: Math.max(
        3, theme.communicationContentSpacing - 2)
    readonly property real maximumBubbleExtent: Math.max(
        0,
        Math.min(
            520,
            width * 0.70,
            width - avatarExtent - theme.communicationAvatarSpacing
                - outerMargin * 2
        )
    )
    readonly property real naturalBubbleExtent:
        bubbleContent.implicitWidth + bubblePadding * 2
    readonly property real bubbleExtent: Math.min(
        maximumBubbleExtent,
        Math.max(width < 380 ? 104 : 116, naturalBubbleExtent)
    )
    readonly property real bubbleCornerRadius: groupFirst && groupLast
        ? theme.communicationBubbleRadius
        : theme.communicationGroupedBubbleRadius

    signal contextRequested(real localX, real localY)
    signal selectionRequested()

    implicitHeight: Math.max(
        groupLast ? avatarExtent : 0,
        messageBubble.height
    )
    height: implicitHeight

    Controls.ItemPreview {
        id: authorAvatar
        objectName: "messageTimelineAvatar"
        x: root.outgoing
            ? root.width - width - root.outerMargin : root.outerMargin
        anchors.bottom: parent.bottom
        width: root.avatarExtent
        height: root.avatarExtent
        visible: root.groupLast
        active: visible
        theme: root.theme
        source: root.avatarUrl
        fallbackIcon: "person"
        fallbackText: root.initials
        previewSize: root.avatarExtent
        round: true
        outlined: true
        accent: root.avatarColor
        animateAppearance: false
    }

    Rectangle {
        id: messageBubble
        objectName: "messageTimelineBubble"
        x: root.outgoing
            ? authorAvatar.x - root.theme.communicationAvatarSpacing - width
            : authorAvatar.x + authorAvatar.width
                + root.theme.communicationAvatarSpacing
        width: root.bubbleExtent
        height: bubbleContent.implicitHeight
            + root.bubblePadding * 2
        radius: root.bubbleCornerRadius
        topLeftRadius: root.bubbleCornerRadius
        topRightRadius: root.bubbleCornerRadius
        bottomLeftRadius: root.groupLast && !root.outgoing
            ? 0 : root.bubbleCornerRadius
        bottomRightRadius: root.groupLast && root.outgoing
            ? 0 : root.bubbleCornerRadius
        color: root.outgoing
            ? root.theme.secondaryContainer
            : root.theme.surfaceContainerHigh
        border.width: root.forwardSelected || root.current
            ? 2 : root.unread ? 1 : 0
        border.color: root.forwardSelected
            ? root.theme.tertiary : root.theme.action

        Behavior on border.width {
            NumberAnimation {
                duration: root.theme.motionFast
                easing.type: Easing.OutCubic
            }
        }

        Loader {
            anchors.left: root.outgoing ? undefined : parent.left
            anchors.right: root.outgoing ? parent.right : undefined
            anchors.bottom: parent.bottom
            active: root.groupLast
            z: -1
            anchors.leftMargin: root.outgoing ? 0
                : -root.theme.communicationGroupTailSize - 2
            anchors.rightMargin: root.outgoing
                ? -root.theme.communicationGroupTailSize - 2 : 0
            sourceComponent: Canvas {
                objectName: "messageTimelineGroupTail"
                property color tailColor: messageBubble.color
                property bool mirrored: root.outgoing
                width: root.theme.communicationGroupTailSize + 4
                height: root.theme.communicationGroupTailSize + 5

                onTailColorChanged: requestPaint()
                onMirroredChanged: requestPaint()
                onPaint: {
                    const context = getContext("2d")
                    context.clearRect(0, 0, width, height)
                    context.fillStyle = tailColor
                    context.beginPath()
                    if (root.outgoing) {
                        context.moveTo(0, 1)
                        context.lineTo(0, height)
                        context.lineTo(width - 1, height)
                        context.bezierCurveTo(
                            width * 0.58, height - 1,
                            width * 0.18, height - 7,
                            0, 3)
                    } else {
                        context.moveTo(width, 1)
                        context.lineTo(width, height)
                        context.lineTo(1, height)
                        context.bezierCurveTo(
                            width * 0.42, height - 1,
                            width * 0.82, height - 7,
                            width, 3)
                    }
                    context.closePath()
                    context.fill()
                }
            }
        }

        HoverHandler { id: bubbleHover }

        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.RightButton
            cursorShape: Qt.ArrowCursor
            onPressed: mouse => {
                root.contextRequested(mouse.x, mouse.y)
                mouse.accepted = true
            }
        }

        ColumnLayout {
            id: bubbleContent
            anchors.fill: parent
            anchors.margins: root.bubblePadding
            spacing: root.bubbleSpacing
        }

        MouseArea {
            anchors.fill: parent
            z: 100
            visible: root.selectionMode
            acceptedButtons: Qt.LeftButton
            cursorShape: Qt.PointingHandCursor
            onClicked: root.selectionRequested()
        }
    }
}

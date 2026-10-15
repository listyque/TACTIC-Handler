import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Shapes
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
    property bool mediaAttachments: false
    default property alias contentData: bubbleContent.data
    readonly property alias bubbleItem: messageBubble
    readonly property bool hovered: bubbleHover.hovered
    readonly property real avatarExtent: width < 380 ? 34 : 40
    readonly property real outerMargin: width < 380 ? 8 : 12
    readonly property real bubblePadding:
        theme.communicationBubblePadding + (width < 380 ? 0 : 3)
    readonly property real bubbleSpacing: Math.max(
        2, theme.communicationContentSpacing - 4)
    readonly property real maximumBubbleExtent: Math.max(
        0,
        Math.min(
            mediaAttachments ? width : 520,
            width * 0.70,
            width - avatarExtent - theme.communicationAvatarSpacing
                - outerMargin * 2
        )
    )
    readonly property real naturalBubbleExtent:
        bubbleContent.implicitWidth + bubblePadding * 2
    readonly property real bubbleExtent: Math.min(
        maximumBubbleExtent,
        mediaAttachments ? maximumBubbleExtent
            : Math.max(width < 380 ? 104 : 116, naturalBubbleExtent)
    )
    readonly property real bubbleCornerRadius: theme.communicationBubbleRadius

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

    Item {
        id: messageBubble
        objectName: "messageTimelineBubble"
        x: root.outgoing
            ? authorAvatar.x - root.theme.communicationAvatarSpacing - width
            : authorAvatar.x + authorAvatar.width
                + root.theme.communicationAvatarSpacing
        width: root.bubbleExtent
        height: bubbleContent.implicitHeight
            + root.bubblePadding * 2
        readonly property color fillColor: root.outgoing
            ? root.theme.secondaryContainer
            : root.theme.surfaceContainerHigh
        property real outlineWidth: root.forwardSelected || root.current
            ? 2 : root.unread ? 1 : 0
        readonly property color outlineColor: root.forwardSelected
            ? root.theme.tertiary : root.theme.action

        Behavior on outlineWidth {
            NumberAnimation {
                duration: root.theme.motionFast
                easing.type: Easing.OutCubic
            }
        }

        Shape {
            id: bubbleOutline
            objectName: "messageTimelineOutline"
            readonly property real tailExtent: root.groupLast
                ? Math.min(root.theme.communicationGroupTailSize,
                           root.theme.communicationAvatarSpacing - 2) : 0
            readonly property real inset: tailExtent + 2
            x: -inset
            y: -2
            width: messageBubble.width + inset * 2
            height: messageBubble.height + 4
            preferredRendererType: Shape.CurveRenderer
            transform: Scale {
                origin.x: bubbleOutline.width / 2
                xScale: root.outgoing ? -1 : 1
            }
            // One closed contour owns both fill and outline, including the tail.
            ShapePath {
                fillColor: messageBubble.fillColor
                strokeColor: messageBubble.outlineColor
                strokeWidth: messageBubble.outlineWidth
                joinStyle: ShapePath.RoundJoin
                PathSvg {
                    path: {
                        const l = bubbleOutline.inset
                        const t = 2
                        const r = l + messageBubble.width
                        const b = t + messageBubble.height
                        const radius = Math.min(root.bubbleCornerRadius,
                            messageBubble.height / 2, messageBubble.width / 2)
                        const arc = " A " + radius + " " + radius + " 0 0 1 "
                        let contour = "M " + (l + radius) + " " + t
                            + " H " + (r - radius) + arc + r + " " + (t + radius)
                            + " V " + (b - radius) + arc + (r - radius) + " " + b
                            + " H " + (l + radius)
                        if (root.groupLast) {
                            const tip = l - bubbleOutline.tailExtent
                            contour += " C " + l + " " + b + " " + tip + " " + b
                                + " " + tip + " " + (b - 2)
                                + " C " + tip + " " + (b - 4) + " " + l + " "
                                + (b - 4) + " " + l + " " + (b - radius)
                        } else {
                            contour += arc + l + " " + (b - radius)
                        }
                        return contour + " V " + (t + radius)
                            + arc + (l + radius) + " " + t + " Z"
                    }
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

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Shapes
import "controls" as Controls
import "tactic_frame/features/messages/messaging.state.mjs" as State

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
    readonly property real contentImplicitWidth: {
        let w = 0;
        const list = bubbleContent.children;
        for (let i = 0; i < list.length; ++i)
            w = Math.max(w, list[i].implicitWidth);
        return w;
    }
    readonly property real contentImplicitHeight: {
        let h = 0;
        let count = 0;
        const list = bubbleContent.children;
        for (let i = 0; i < list.length; ++i) {
            const child = list[i];
            const ch = child.Layout.preferredHeight >= 0 ? child.Layout.preferredHeight : child.implicitHeight;
            h += ch;
            count++;
        }
        return h + Math.max(0, count - 1) * root.bubbleSpacing;
    }
    readonly property var geometry: State.bubbleGeometry(width, contentImplicitWidth, 0, {
        media: mediaAttachments,
        last: groupLast,
        own: outgoing
    }, theme.styleName)
    readonly property real avatarExtent: geometry.avatar
    readonly property real outerMargin: geometry.margin
    readonly property real bubblePadding: geometry.padding
    readonly property real bubbleSpacing: geometry.gap
    readonly property real maximumBubbleExtent: geometry.maximum
    readonly property real naturalBubbleExtent: contentImplicitWidth + bubblePadding * 2
    readonly property real bubbleExtent: geometry.width
    readonly property real bubbleCornerRadius: geometry.corner

    function interactiveAt(item, x, y) {
        if (item.clip && !item.contains(Qt.point(x, y)))
            return false;
        for (let index = item.children.length - 1; index >= 0; --index) {
            const child = item.children[index];
            if (!child.visible || !child.enabled)
                continue;
            const point = child.mapFromItem(item, x, y);
            if (child.contains(point)) {
                if (typeof child.clicked === "function" || typeof child.activated === "function")
                    return true;
                if (typeof child.linkAt === "function" && child.linkAt(point.x, point.y).length)
                    return true;
            }
            if (interactiveAt(child, point.x, point.y))
                return true;
        }
        return false;
    }

    signal contextRequested(real localX, real localY)
    signal selectionRequested

    implicitHeight: Math.max(groupLast ? avatarExtent : 0, messageBubble.height)
    height: implicitHeight

    Controls.ItemPreview {
        id: authorAvatar
        objectName: "messageTimelineAvatar"
        x: root.outgoing ? root.width - width - root.outerMargin : root.outerMargin
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
        x: root.outgoing ? authorAvatar.x - root.theme.communicationAvatarSpacing - width : authorAvatar.x + authorAvatar.width + root.theme.communicationAvatarSpacing
        width: root.bubbleExtent
        height: root.contentImplicitHeight + root.bubblePadding * 2
        readonly property color fillColor: root.outgoing ? root.theme.secondaryContainer : root.theme.surfaceContainerHigh
        property real outlineWidth: root.forwardSelected || root.current ? 2 : root.unread ? 1 : 0
        readonly property color outlineColor: root.forwardSelected ? root.theme.tertiary : root.theme.action

        Behavior on outlineWidth {
            NumberAnimation {
                duration: root.theme.motionFast
                easing.type: Easing.OutCubic
            }
        }

        Shape {
            id: bubbleOutline
            objectName: "messageTimelineOutline"
            readonly property real tailExtent: root.groupLast ? Math.min(root.theme.communicationGroupTailSize, root.theme.communicationAvatarSpacing - 2) : 0
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
                    path: State.bubbleContour(messageBubble.width, messageBubble.height, root.bubbleCornerRadius, root.groupLast, bubbleOutline.tailExtent)
                }
            }
        }

        HoverHandler {
            id: bubbleHover
        }

        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.RightButton
            cursorShape: Qt.ArrowCursor
            onPressed: mouse => {
                root.contextRequested(mouse.x, mouse.y);
                mouse.accepted = true;
            }
        }

        ColumnLayout {
            id: bubbleContent
            anchors.fill: parent
            anchors.margins: root.bubblePadding
            spacing: root.bubbleSpacing
        }

        Controls.ActivationHandler {
            enabled: root.selectionMode
            repeatPointerTaps: true
            onActivated: (modifiers, x, y) => {
                const point = bubbleContent.mapFromItem(messageBubble, x, y);
                if (!root.interactiveAt(bubbleContent, point.x, point.y))
                    root.selectionRequested();
            }
        }
    }
}

import QtQuick
import QtQuick.Controls

ScrollBar {
    id: root

    required property var theme
    // Attached ScrollBars are re-parented to their Flickable by Qt.  The
    // explicit target can be supplied for complex/re-parented list layouts.
    property var flickableTarget: parent
    readonly property bool expanded: hovered || pressed
    readonly property bool verticalBar:
        orientation === Qt.Vertical
    readonly property real viewportExtent: {
        if (!flickableTarget)
            return 0
        return verticalBar
            ? Number(flickableTarget.height || 0)
            : Number(flickableTarget.width || 0)
    }
    readonly property real contentExtent: {
        if (!flickableTarget)
            return 0
        return verticalBar
            ? Number(flickableTarget.contentHeight || 0)
            : Number(flickableTarget.contentWidth || 0)
    }
    readonly property bool hasOverflow:
        viewportExtent > 0
        && contentExtent > viewportExtent + 0.5

    // Do not inherit the platform style's transient opacity.  The bar is
    // continuously visible while scrolling is possible and absent otherwise.
    policy: hasOverflow ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
    visible: hasOverflow
    enabled: hasOverflow
    opacity: hasOverflow ? 1 : 0
    z: 10000
    hoverEnabled: true
    interactive: true
    minimumSize: 0.06
    padding: 1
    implicitWidth: verticalBar ? (expanded ? 11 : 6) : 0
    implicitHeight: verticalBar ? 0 : (expanded ? 11 : 6)

    Behavior on opacity {
        NumberAnimation {
            duration: root.theme.motionFast
            easing.type: Easing.OutCubic
        }
    }
    Behavior on implicitWidth {
        NumberAnimation {
            duration: root.theme.motionMedium
            easing.type: Easing.OutCubic
        }
    }
    Behavior on implicitHeight {
        NumberAnimation {
            duration: root.theme.motionMedium
            easing.type: Easing.OutCubic
        }
    }

    background: Rectangle {
        radius: Math.min(width, height) / 2
        color: root.theme.outline
        opacity: root.expanded ? 0.15 : 0.055
        Behavior on opacity {
            NumberAnimation { duration: root.theme.motionFast }
        }
    }

    contentItem: Rectangle {
        implicitWidth: 5
        implicitHeight: 5
        radius: Math.min(width, height) / 2
        color: root.theme.secondaryText
        opacity: !root.enabled ? 0.18
            : root.pressed ? 0.90
            : root.hovered ? 0.72 : 0.42
        Behavior on opacity {
            NumberAnimation { duration: root.theme.motionFast }
        }
    }

    HoverHandler {
        cursorShape: root.enabled && root.interactive
            ? Qt.PointingHandCursor : Qt.ArrowCursor
    }
}

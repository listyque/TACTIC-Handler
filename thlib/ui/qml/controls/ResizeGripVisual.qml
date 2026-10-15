import QtQuick

Rectangle {
    id: root
    required property var theme
    property bool vertical: true
    property bool hovered: false
    property bool pressed: false
    property bool interacted: false
    onHoveredChanged: if (hovered) interacted = true
    onPressedChanged: if (pressed) interacted = true

    width: vertical ? 3 : Math.min(40, parent ? parent.width : 40)
    height: vertical ? Math.min(40, parent ? parent.height : 40) : 3
    radius: 1.5
    color: pressed || hovered ? theme.action : theme.outlineVariant
    opacity: pressed ? 1 : hovered ? 0.85 : 0.28
    Behavior on opacity {
        enabled: root.interacted
        NumberAnimation { duration: root.theme.hoverMotionFast; easing.type: Easing.OutCubic }
    }
    Behavior on color {
        enabled: root.interacted
        ColorAnimation { duration: root.theme.hoverMotionFast; easing.type: Easing.OutCubic }
    }
}

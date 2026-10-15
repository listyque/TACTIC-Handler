import "../tactic_frame/core/foundation.mjs" as Foundation
import QtQuick

Rectangle {
    id: root
    // Follow odd and even hit-area extents without anchor rounding.
    x: parent ? (parent.width - width) / 2 : 0
    y: parent ? (parent.height - height) / 2 : 0
    required property var theme
    property bool vertical: true
    property bool hovered: false
    property bool pressed: false
    property bool interacted: false
    onHoveredChanged: if (hovered)
        interacted = true
    onPressedChanged: if (pressed)
        interacted = true

    width: vertical ? Foundation.controls.splitter.thickness : Math.min(Foundation.controls.splitter.length, parent ? parent.width : Foundation.controls.splitter.length)
    height: vertical ? Math.min(Foundation.controls.splitter.length, parent ? parent.height : Foundation.controls.splitter.length) : Foundation.controls.splitter.thickness
    radius: Foundation.controls.splitter.thickness / 2
    color: pressed || hovered ? theme.action : theme.outlineVariant
    opacity: pressed ? Foundation.controls.splitter.pressedOpacity : hovered ? Foundation.controls.splitter.hoveredOpacity : Foundation.controls.splitter.restingOpacity
    Behavior on opacity {
        enabled: root.interacted
        NumberAnimation {
            duration: root.theme.hoverMotionFast
            easing.type: Easing.OutCubic
        }
    }
    Behavior on color {
        enabled: root.interacted
        ColorAnimation {
            duration: root.theme.hoverMotionFast
            easing.type: Easing.OutCubic
        }
    }
}

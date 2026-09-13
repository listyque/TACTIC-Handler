import QtQuick

Item {
    id: root
    required property var theme
    property bool selected: false
    property bool hovered: false
    property bool pressed: false
    property color accent: theme.contentAccent
    property bool railVisible: true
    property real railX: 0
    property real railWidth: 3
    property real railOpacity: 1
    property real railTopMargin: 5
    property real railBottomMargin: 5
    property color normalColor: theme.row
    property color selectedColor: theme.contentSelection
    property real inset: 0
    property real cornerRadius: 0
    property real borderWidth: 0
    property color borderColor: "transparent"
    property bool elevated: false
    property real shadowVerticalOffset: 3
    property bool separatorVisible: true
    property bool animateStateChanges: true
    readonly property color baseColor:
        selected ? selectedColor : normalColor
    readonly property color interactionColor: pressed
        ? theme.overlay(
            baseColor, selected ? theme.action : theme.primaryText, 0.12)
        : hovered
            ? theme.overlay(
                baseColor, selected ? theme.action : theme.primaryText, 0.08)
            : baseColor

    Rectangle {
        objectName: "itemSurfaceShadow"
        visible: root.elevated
        x: surface.x - 1
        y: surface.y + 1
        width: surface.width + 2
        height: surface.height + 2
        radius: surface.radius + 1
        color: root.theme.popupShadow
        opacity: 0.28
        antialiasing: surface.antialiasing
    }
    Rectangle {
        visible: root.elevated
        x: surface.x + 1
        y: surface.y + root.shadowVerticalOffset
        width: Math.max(0, surface.width - 2)
        height: surface.height
        radius: surface.radius
        color: root.theme.popupShadow
        opacity: 0.58
        antialiasing: surface.antialiasing
    }
    Rectangle {
        id: surface
        anchors.fill: parent
        anchors.margins: root.inset
        radius: root.cornerRadius
        color: root.interactionColor
        border.width: root.borderWidth
        border.color: root.borderColor
        antialiasing: root.cornerRadius > 0
        Behavior on color {
            enabled: root.animateStateChanges
            ColorAnimation {
                duration: root.pressed
                    ? root.theme.clickMotionFast
                    : root.hovered
                        ? root.theme.hoverMotionFast
                        : root.theme.hoverMotionMedium
                easing.type: Easing.OutCubic
            }
        }
    }
    Rectangle {
        visible: root.railVisible
        x: root.railX
        y: root.inset + root.railTopMargin
        width: root.railWidth
        height: Math.max(
            0,
            parent.height - root.inset * 2
                - root.railTopMargin - root.railBottomMargin
        )
        radius: width / 2
        color: root.accent
        opacity: root.railOpacity
        antialiasing: true
    }
    Rectangle {
        visible: root.separatorVisible
        anchors.bottom: parent.bottom
        width: parent.width
        height: 1
        color: root.theme.separator
    }
}

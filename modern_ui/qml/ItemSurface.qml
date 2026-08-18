import QtQuick

Item {
    id: root
    required property var theme
    property bool selected: false
    property bool hovered: false
    property bool pressed: false
    property color accent: "#607d8b"
    property bool railVisible: true
    property real railX: 0
    property real railWidth: 3
    property real railOpacity: 1
    property color normalColor: theme.row
    property color selectedColor: theme.selected
    property real inset: 0
    property real cornerRadius: 0
    property bool separatorVisible: true

    Rectangle {
        anchors.fill: parent
        anchors.margins: root.inset
        radius: root.cornerRadius
        color: root.selected ? root.selectedColor : root.normalColor
        antialiasing: root.cornerRadius > 0
    }
    Rectangle {
        anchors.fill: parent
        anchors.margins: root.inset
        radius: root.cornerRadius
        color: root.selected ? root.theme.action : root.theme.primaryText
        opacity: root.pressed ? 0.12 : root.hovered ? 0.08 : 0
        Behavior on opacity {
            NumberAnimation {
                duration: root.hovered ? 100 : 140
                easing.type: Easing.OutCubic
            }
        }
    }
    Rectangle {
        visible: root.railVisible
        x: root.railX
        y: root.inset + 5
        width: root.railWidth
        height: Math.max(0, parent.height - root.inset * 2 - 10)
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

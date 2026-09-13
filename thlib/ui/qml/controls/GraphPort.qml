import QtQuick

PopupAction {
    id: root

    required property var theme
    property color accent: theme.action
    property bool filled: false
    property bool activePort: false

    implicitWidth: theme.controlHeight
    implicitHeight: theme.controlHeight
    padding: 0
    Accessible.name: text

    background: Item {}
    contentItem: Item {
        Rectangle {
            anchors.centerIn: parent
            width: 24
            height: width
            radius: width / 2
            antialiasing: true
            visible: root.hovered || root.visualFocus || root.activePort
            color: root.theme.overlay(root.theme.workspace, root.accent, 0.18)
            border.width: root.visualFocus ? 1 : 0
            border.pixelAligned: false
            border.color: root.accent
        }
        Rectangle {
            objectName: "graphPortRing"
            anchors.centerIn: parent
            width: 13
            height: width
            radius: width / 2
            antialiasing: true
            color: root.filled || root.activePort ? root.accent : root.theme.workspace
            border.width: 2
            border.pixelAligned: false
            border.color: root.accent
        }
    }
    ToolTip {
        theme: root.theme
        text: root.text
        visible: root.hovered
    }
}

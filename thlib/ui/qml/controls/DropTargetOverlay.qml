import QtQuick
import QtQuick.Controls

Rectangle {
    id: root
    required property var theme
    property string iconName: "move-to-inbox"
    property string promptText: ""
    anchors.fill: parent
    anchors.margins: 6
    radius: root.theme.surfaceRadius
    color: root.theme.surfaceContainerHigh
    opacity: 0.94
    border.width: 2
    border.color: root.theme.action

    Column {
        anchors.centerIn: parent
        spacing: 8
        MaterialIcon {
            anchors.horizontalCenter: parent.horizontalCenter
            name: root.iconName
            size: 30
            color: root.theme.action
        }
        Label {
            anchors.horizontalCenter: parent.horizontalCenter
            text: root.promptText
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pixelSize: 12
            font.weight: Font.DemiBold
        }
    }
}

import QtQuick
import QtQuick.Controls

Rectangle {
    id: root

    required property var theme
    property string text: ""
    property string iconName: ""
    property color accentColor: theme.secondaryText

    implicitWidth: content.implicitWidth + 16
    implicitHeight: 24
    radius: height / 2
    color: theme.surfaceContainerHigh

    Row {
        id: content
        anchors.centerIn: parent
        spacing: 5

        MaterialIcon {
            anchors.verticalCenter: parent.verticalCenter
            visible: root.iconName.length > 0
            name: root.iconName
            size: 13
            color: root.accentColor
        }
        Label {
            anchors.verticalCenter: parent.verticalCenter
            text: root.text
            color: root.accentColor
            font.family: root.theme.fontFamily
            font.pixelSize: 8
            font.weight: Font.DemiBold
        }
    }
}

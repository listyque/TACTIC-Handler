import QtQuick
import QtQuick.Controls
import "." as Controls

Rectangle {
    id: root

    required property var theme
    property string label: ""
    property int count: 0
    property color accent: theme.action
    property bool showDot: true
    property bool showCount: true
    property bool clickable: false
    signal clicked()

    implicitWidth: content.implicitWidth + 20
    implicitHeight: 30
    radius: height / 2
    color: clickable && chipAction.hovered
        ? theme.rowHover : theme.surfaceContainerHigh
    border.width: 1
    border.color: clickable && chipAction.activeFocus
        ? theme.action : theme.outlineVariant

    Row {
        id: content

        anchors.centerIn: parent
        spacing: 7

        Rectangle {
            visible: root.showDot
            anchors.verticalCenter: parent.verticalCenter
            width: 8
            height: 8
            radius: width / 2
            color: root.accent
        }
        Label {
            anchors.verticalCenter: parent.verticalCenter
            text: root.label
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.label
        }
        Label {
            visible: root.showCount
            anchors.verticalCenter: parent.verticalCenter
            text: root.count
            color: root.accent
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.label
            font.weight: Font.DemiBold
        }
    }

    Controls.PopupAction {
        id: chipAction
        objectName: "summaryChipAction"
        anchors.fill: parent
        visible: root.clickable
        background: Item {}
        contentItem: Item {}
        Accessible.name: root.label + " " + root.count
        onClicked: root.clicked()
    }
}

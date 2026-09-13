import QtQuick
import "." as Controls

Item {
    id: root

    required property var theme
    property string iconName: ""
    property int count: 0
    property string toolTip: ""
    property bool toolTipsAllowed: true
    property color activeColor: theme.action
    property color badgeColor: activeColor
    signal clicked()

    implicitWidth: 30
    implicitHeight: 30

    Controls.CompactIconButton {
        objectName: "itemCountCompactButton"
        anchors.fill: parent
        theme: root.theme
        iconName: root.iconName
        iconColor: root.count > 0
            ? root.activeColor : root.theme.secondaryText
        iconSize: 17
        round: true
        badgeCount: root.count
        badgeColor: root.badgeColor
        toolTip: root.toolTipsAllowed ? root.toolTip : ""
        onClicked: root.clicked()
    }
}

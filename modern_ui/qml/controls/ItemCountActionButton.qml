import QtQuick
import QtQuick.Controls

Item {
    id: root

    required property var theme
    property string iconName: ""
    property int count: 0
    property string toolTip: ""
    property bool toolTipsAllowed: true
    property color activeColor: theme.action
    signal clicked()

    implicitWidth: 30
    implicitHeight: 24

    Rectangle {
        id: surface
        anchors.fill: parent
        radius: height / 2
        color: pointer.containsMouse
            ? root.theme.panelRaised : root.theme.panel
        border.width: 1
        border.color: root.theme.outline

        MaterialIcon {
            anchors.centerIn: parent
            name: root.iconName
            size: 14
            color: root.count > 0
                ? root.activeColor : root.theme.secondaryText
        }
        MaterialRipple {
            id: ripple
            color: root.theme.ripple
            shapeRadius: surface.radius
        }
    }

    Rectangle {
        visible: root.count > 0
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.rightMargin: -1
        anchors.topMargin: -1
        implicitWidth: Math.max(12, countLabel.implicitWidth + 4)
        implicitHeight: 12
        radius: 6
        color: root.activeColor

        Label {
            id: countLabel
            anchors.centerIn: parent
            text: root.count > 99 ? "99+" : String(root.count)
            color: root.theme.selectedText
            font.family: root.theme.fontFamily
            font.pixelSize: 7
            font.weight: Font.Bold
        }
    }

    MouseArea {
        id: pointer
        objectName: "itemCountActionCursorArea"
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: root.enabled
            ? Qt.PointingHandCursor : Qt.ArrowCursor
        onPressed: mouse => ripple.burst(mouse.x, mouse.y)
        onClicked: root.clicked()
    }

    Md3ToolTip {
        theme: root.theme
        visible: pointer.containsMouse
            && root.toolTipsAllowed
            && root.toolTip.length > 0
            && !root.theme.suppressToolTips
        delay: 450
        text: root.toolTip
    }
}

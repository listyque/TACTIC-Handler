import QtQuick

Item {
    id: root

    required property var theme
    property string iconName: "chevron_right"
    property string toolTip: ""
    signal clicked()

    implicitWidth: 40
    implicitHeight: 84

    Rectangle {
        id: surface
        anchors.fill: parent
        radius: root.theme.itemRadius
        color: root.theme.surfaceContainerHigh

        MaterialIcon {
            anchors.centerIn: parent
            name: root.iconName
            size: 18
            color: root.theme.primaryText
        }
        MaterialRipple {
            id: ripple
            shapeRadius: surface.radius
            color: root.theme.rippleStrong
        }
    }

    MouseArea {
        id: pointer
        objectName: "previewNavigationCursorArea"
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
            && root.toolTip.length > 0
            && !root.theme.suppressToolTips
        text: root.toolTip
    }
}

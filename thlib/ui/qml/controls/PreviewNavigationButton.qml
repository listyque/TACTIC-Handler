import QtQuick
import "." as Controls

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

        Controls.MaterialIcon {
            anchors.centerIn: parent
            name: root.iconName
            size: 18
            color: root.theme.primaryText
        }
        Controls.MaterialRipple {
            id: ripple
            theme: root.theme
            shapeRadius: surface.radius
            color: root.theme.rippleStrong
        }
    }

    HoverHandler {
        id: pointer
        objectName: "previewNavigationCursorArea"
        cursorShape: Qt.PointingHandCursor
    }

    Controls.ActivationHandler {
        enabled: root.enabled
        cursorShape: Qt.PointingHandCursor
        onPressedChanged: {
            if (pressed)
                ripple.burst(point.position.x, point.position.y)
        }
        onActivated: root.clicked()
    }

    Controls.ToolTip {
        theme: root.theme
        visible: pointer.hovered
            && root.toolTip.length > 0
            && !root.theme.suppressToolTips
        text: root.toolTip
    }
}

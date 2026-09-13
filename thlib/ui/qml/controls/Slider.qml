import QtQuick
import QtQuick.Controls.Basic as Basic
import "." as Controls

Basic.Slider {
    id: control

    required property var theme

    implicitHeight: 20

    background: Rectangle {
        x: control.leftPadding
        y: control.topPadding + control.availableHeight / 2 - height / 2
        width: control.availableWidth
        height: 4
        radius: 2
        color: control.theme.surfaceContainerHighest

        Rectangle {
            width: control.visualPosition * parent.width
            height: parent.height
            radius: parent.radius
            color: control.theme.action
        }
    }

    handle: Rectangle {
        x: control.leftPadding + control.visualPosition
            * (control.availableWidth - width)
        y: control.topPadding + control.availableHeight / 2 - height / 2
        implicitWidth: 16
        implicitHeight: 16
        radius: width / 2
        color: control.pressed ? control.theme.selected : control.theme.action
        border.width: 2
        border.color: control.theme.panelRaised
        Behavior on color {
            ColorAnimation { duration: control.theme.clickMotionFast }
        }
    }

    HoverHandler {
        objectName: "sliderCursorHandler"
        cursorShape: Qt.PointingHandCursor
    }
}

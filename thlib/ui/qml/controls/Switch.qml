import QtQuick
import QtQuick.Controls
import QtQuick.Controls as QtControls
import "." as Controls

QtControls.Switch {
    id: control

    required property var theme

    spacing: 10
    font.family: theme.fontFamily
    font.pointSize: Typography.body

    indicator: Rectangle {
        implicitWidth: 42
        implicitHeight: 24
        x: control.leftPadding
        y: (control.height - height) / 2
        radius: height / 2
        color: control.checked ? theme.action : theme.surfaceContainerHighest
        border.width: 1
        border.color: control.checked ? theme.action : theme.outline

        Rectangle {
            width: 18
            height: 18
            radius: 9
            y: 3
            x: control.checked ? parent.width - width - 3 : 3
            color: control.checked ? theme.selectedText : theme.secondaryText
            Behavior on x {
                NumberAnimation {
                    duration: theme.clickMotionMedium
                    easing.type: Easing.OutCubic
                }
            }
        }
        Behavior on color {
            ColorAnimation { duration: theme.clickMotionFast }
        }
    }

    contentItem: Label {
        leftPadding: control.indicator.width + control.spacing
        text: control.text
        color: control.enabled ? theme.primaryText : theme.disabledText
        font: control.font
        verticalAlignment: Text.AlignVCenter
    }

    HoverHandler {
        objectName: "switchCursorHandler"
        cursorShape: Qt.PointingHandCursor
    }
}

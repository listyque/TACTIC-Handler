import QtQuick
import QtQuick.Controls.Basic as Basic
import "." as Controls

Basic.TabButton {
    id: control

    required property var theme

    implicitHeight: theme.controlHeight
    font.family: theme.fontFamily
    font.pointSize: Typography.body
    font.weight: checked ? Font.DemiBold : Font.Normal

    contentItem: Basic.Label {
        text: control.text
        color: !control.enabled ? control.theme.disabledText
            : control.checked ? control.theme.action
            : control.theme.primaryText
        font: control.font
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Rectangle {
        radius: control.theme.itemRadius
        color: control.checked ? control.theme.secondaryContainer
            : control.hovered ? control.theme.rowHover : "transparent"
        border.width: control.checked ? 1 : 0
        border.color: control.theme.action
        Behavior on color {
            ColorAnimation {
                duration: control.checked
                    ? control.theme.clickMotionFast
                    : control.hovered
                        ? control.theme.hoverMotionFast
                        : control.theme.clickMotionFast
            }
        }
    }

    HoverHandler {
        objectName: "tabButtonCursorHandler"
        cursorShape: Qt.PointingHandCursor
    }
}

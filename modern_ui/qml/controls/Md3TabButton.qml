import QtQuick
import QtQuick.Controls.Basic as Basic

Basic.TabButton {
    id: control

    required property var theme

    implicitHeight: theme.controlHeight
    font.family: theme.fontFamily
    font.pixelSize: 10
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
            ColorAnimation { duration: control.theme.motionFast }
        }
    }

    HoverHandler {
        objectName: "md3TabButtonCursorHandler"
        cursorShape: control.enabled
            ? Qt.PointingHandCursor : Qt.ArrowCursor
    }
}

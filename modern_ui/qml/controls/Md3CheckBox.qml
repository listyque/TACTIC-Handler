import QtQuick
import QtQuick.Controls

CheckBox {
    id: control

    required property var theme
    property bool prominent: false

    spacing: 9
    font.family: theme.fontFamily
    font.pixelSize: 10

    indicator: Rectangle {
        implicitWidth: control.prominent ? 22 : 19
        implicitHeight: control.prominent ? 22 : 19
        x: control.leftPadding
        y: (control.height - height) / 2
        radius: Math.min(5, theme.itemRadius)
        color: control.checked ? theme.action
            : control.prominent ? theme.surfaceContainerHighest : "transparent"
        border.width: control.activeFocus || control.prominent ? 2 : 1
        border.color: control.checked || control.activeFocus
            ? theme.action
            : control.prominent ? theme.secondaryText : theme.outline

        MaterialIcon {
            anchors.centerIn: parent
            visible: control.checked
            name: "check"
            size: control.prominent ? 17 : 15
            color: theme.selectedText
        }
        Behavior on color {
            ColorAnimation { duration: theme.motionFast }
        }
    }

    contentItem: Label {
        leftPadding: control.indicator.width + control.spacing
        text: control.text
        color: control.enabled ? theme.primaryText : theme.disabledText
        font: control.font
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    HoverHandler {
        objectName: "md3CheckBoxCursorHandler"
        cursorShape: control.enabled
            ? Qt.PointingHandCursor : Qt.ArrowCursor
    }
}

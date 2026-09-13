import QtQuick
import QtQuick.Controls
import QtQuick.Controls as QtControls
import "." as Controls

QtControls.CheckBox {
    id: control

    required property var theme
    property bool prominent: false
    property bool compact: false

    spacing: compact ? 6 : 9
    implicitHeight: compact ? 30 : Math.max(36, contentItem.implicitHeight)
    font.family: theme.fontFamily
    font.pointSize: compact ? Typography.label : Typography.body

    indicator: Rectangle {
        implicitWidth: control.prominent ? 22 : control.compact ? 17 : 19
        implicitHeight: control.prominent ? 22 : control.compact ? 17 : 19
        x: control.leftPadding
        y: (control.height - height) / 2
        radius: Math.min(5, theme.itemRadius)
        color: control.checked ? theme.action
            : control.prominent ? theme.surfaceContainerHighest : "transparent"
        border.width: control.activeFocus || control.prominent ? 2 : 1
        border.color: control.checked || control.activeFocus
            ? theme.action
            : control.prominent ? theme.secondaryText : theme.outline

        Controls.MaterialIcon {
            anchors.centerIn: parent
            visible: control.checked
            name: "check"
            size: control.prominent ? 17 : control.compact ? 13 : 15
            color: theme.selectedText
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
        elide: Text.ElideRight
    }

    HoverHandler {
        objectName: "checkBoxCursorHandler"
        cursorShape: Qt.PointingHandCursor
    }
}

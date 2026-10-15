import "../tactic_frame/core/foundation.mjs" as Foundation
import QtQuick
import QtQuick.Controls
import QtQuick.Controls as QtControls
import "." as Controls

QtControls.CheckBox {
    id: control

    required property var theme
    property bool prominent: false
    property bool compact: false
    property bool wrapText: false
    property real indicatorOffset: 0

    spacing: compact ? Foundation.controls.checkBox.compactSpacing : Foundation.controls.checkBox.spacing
    implicitHeight: compact ? Foundation.controls.checkBox.compactHeight : Math.max(Foundation.controls.checkBox.height, contentItem.implicitHeight)
    font.family: theme.fontFamily
    font.pointSize: compact ? Typography.label : Typography.body

    indicator: Rectangle {
        implicitWidth: control.prominent ? Foundation.controls.checkBox.prominentIndicator : control.compact ? Foundation.controls.checkBox.compactIndicator : Foundation.controls.checkBox.indicator
        implicitHeight: control.prominent ? Foundation.controls.checkBox.prominentIndicator : control.compact ? Foundation.controls.checkBox.compactIndicator : Foundation.controls.checkBox.indicator
        x: control.leftPadding + control.indicatorOffset
        y: (control.height - height) / 2
        radius: Math.min(Foundation.controls.checkBox.radius, theme.itemRadius)
        color: control.checked ? theme.action : control.prominent ? theme.surfaceContainerHighest : "transparent"
        border.width: control.activeFocus || control.prominent ? 2 : 1
        border.color: control.checked || control.activeFocus ? theme.action : control.prominent ? theme.secondaryText : theme.outline

        Controls.MaterialIcon {
            anchors.centerIn: parent
            visible: control.checked
            name: "check"
            size: control.prominent ? Foundation.controls.checkBox.prominentIconSize : control.compact ? Foundation.controls.checkBox.compactIconSize : Foundation.controls.checkBox.iconSize
            color: theme.selectedText
        }
        Behavior on color {
            ColorAnimation {
                duration: theme.clickMotionFast
            }
        }
    }

    contentItem: Label {
        leftPadding: control.indicator.width + control.spacing
        text: control.text
        color: control.enabled ? theme.primaryText : theme.disabledText
        font: control.font
        verticalAlignment: Text.AlignVCenter
        elide: control.wrapText ? Text.ElideNone : Text.ElideRight
        wrapMode: control.wrapText ? Text.Wrap : Text.NoWrap
    }

    HoverHandler {
        objectName: "checkBoxCursorHandler"
        cursorShape: Qt.PointingHandCursor
    }
}

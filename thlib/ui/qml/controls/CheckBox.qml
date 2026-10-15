import "../tactic_frame/core/interaction.mjs" as Interaction
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
    readonly property bool mixed: checkState === Qt.PartiallyChecked
    readonly property var paint: Interaction.checkVisual({
        enabled: enabled,
        checked: checked,
        mixed: mixed,
        focused: visualFocus,
        prominent: prominent
    })

    spacing: compact ? Foundation.controls.checkBox.compactSpacing : Foundation.controls.checkBox.spacing
    implicitHeight: compact ? Foundation.controls.checkBox.compactHeight : Math.max(Foundation.controls.checkBox.height, contentItem.implicitHeight)
    font: Qt.font({
        family: theme.fontFamily,
        hintingPreference: Font.PreferVerticalHinting,
        pixelSize: compact ? Foundation.textStyles.secondary : Foundation.textStyles.body
    })

    indicator: Rectangle {
        implicitWidth: control.prominent ? Foundation.controls.checkBox.prominentIndicator : control.compact ? Foundation.controls.checkBox.compactIndicator : Foundation.controls.checkBox.indicator
        implicitHeight: control.prominent ? Foundation.controls.checkBox.prominentIndicator : control.compact ? Foundation.controls.checkBox.compactIndicator : Foundation.controls.checkBox.indicator
        x: control.leftPadding + control.indicatorOffset
        y: (control.height - height) / 2
        radius: Math.min(Foundation.controls.checkBox.radius, theme.itemRadius)
        color: control.paint.background === "transparent" ? "transparent" : theme[control.paint.background]
        border.width: control.paint.borderWidth
        border.color: theme[control.paint.border]

        Controls.MaterialIcon {
            anchors.centerIn: parent
            visible: control.checked || control.mixed
            name: control.mixed ? "minus" : "check"
            size: control.prominent ? Foundation.controls.checkBox.prominentIconSize : control.compact ? Foundation.controls.checkBox.compactIconSize : Foundation.controls.checkBox.iconSize
            color: theme[control.paint.mark]
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
        cursorShape: control.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
    }
}

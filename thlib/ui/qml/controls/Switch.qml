import "../tactic_frame/core/interaction.mjs" as Interaction
import "../tactic_frame/core/foundation.mjs" as Foundation
import QtQuick
import QtQuick.Controls
import QtQuick.Controls as QtControls
import "." as Controls

QtControls.Switch {
    id: control

    required property var theme
    readonly property var paint: Interaction.switchVisual({
        enabled: enabled,
        checked: checked,
        focused: visualFocus
    })

    spacing: Foundation.controls.switch.spacing
    font: Qt.font({
        family: theme.fontFamily,
        hintingPreference: Font.PreferVerticalHinting,
        pixelSize: Foundation.textStyles.body
    })

    indicator: Rectangle {
        implicitWidth: Foundation.controls.switch.width
        implicitHeight: Foundation.controls.switch.height
        x: control.leftPadding
        y: (control.height - height) / 2
        radius: height / 2
        color: theme[control.paint.background]
        border.width: control.paint.borderWidth
        border.color: theme[control.paint.border]

        Rectangle {
            width: Foundation.controls.switch.thumb
            height: Foundation.controls.switch.thumb
            radius: width / 2
            y: Foundation.controls.switch.inset
            x: control.checked ? parent.width - width - Foundation.controls.switch.inset : Foundation.controls.switch.inset
            color: theme[control.paint.thumb]
            Behavior on x {
                NumberAnimation {
                    duration: theme.clickMotionMedium
                    easing.type: Easing.OutCubic
                }
            }
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
    }

    HoverHandler {
        objectName: "switchCursorHandler"
        cursorShape: control.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
    }
}

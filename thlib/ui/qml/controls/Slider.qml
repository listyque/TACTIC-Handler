import "../tactic_frame/core/foundation.mjs" as Foundation
import QtQuick
import QtQuick.Controls.Basic as Basic

Basic.Slider {
    id: control

    required property var theme

    opacity: enabled ? 1 : 0.5
    stepSize: 1
    implicitHeight: Foundation.controls.slider.height

    background: Rectangle {
        x: control.leftPadding
        y: control.topPadding + control.availableHeight / 2 - height / 2
        width: control.availableWidth
        height: Foundation.controls.slider.track
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
        x: control.leftPadding + control.visualPosition * (control.availableWidth - width)
        y: control.topPadding + control.availableHeight / 2 - height / 2
        implicitWidth: Foundation.controls.slider.thumb
        implicitHeight: Foundation.controls.slider.thumb
        radius: width / 2
        color: control.pressed ? control.theme.selected : control.theme.action
        border.width: Foundation.controls.slider.thumbBorder
        border.color: control.theme.panelRaised
        Behavior on color {
            ColorAnimation {
                duration: control.theme.clickMotionFast
            }
        }
    }

    HoverHandler {
        objectName: "sliderCursorHandler"
        cursorShape: Qt.PointingHandCursor
    }
}

import "../tactic_frame/core/interaction.mjs" as Interaction
import "../tactic_frame/core/foundation.mjs" as Foundation
import QtQuick
import QtQuick.Controls.Basic as Basic
import "." as Controls

Basic.Button {
    id: control

    required property var theme
    // Dynamic windows can release their theme binding before child controls.
    property var effectiveTheme: theme
    hoverEnabled: true
    property bool destructive: false
    property bool tonal: false
    property bool compact: false
    property bool segmented: false
    property real iconSize: 0
    property string toolTip: ""
    property bool lastActivationWasTouch: false
    property double lastActivationAt: -1000

    implicitWidth: compact ? implicitHeight : Math.max(Foundation.controls.button.minimumWidth, contentItem.implicitWidth + leftPadding + rightPadding)
    implicitHeight: effectiveTheme.controlHeight
    leftPadding: segmented ? Foundation.controls.button.segmentedPaddingStart : compact ? 0 : (icon.name.length ? Foundation.controls.button.iconPadding : Foundation.controls.button.padding)
    rightPadding: segmented ? Foundation.controls.button.segmentedPaddingEnd : compact ? 0 : Foundation.controls.button.padding
    spacing: segmented ? Foundation.controls.button.segmentedSpacing : compact ? 0 : Foundation.controls.button.spacing
    font: Qt.font({
        family: effectiveTheme.fontFamily,
        hintingPreference: Font.PreferVerticalHinting,
        pixelSize: Foundation.textStyles.body,
        weight: Font.DemiBold
    })
    icon.width: segmented ? Foundation.controls.button.segmentedIconSize : Foundation.controls.button.iconSize
    icon.height: segmented ? Foundation.controls.button.segmentedIconSize : Foundation.controls.button.iconSize
    icon.color: contentColor

    readonly property var paint: Interaction.buttonVisual({
        enabled: enabled,
        pressed: down,
        hovered: hovered,
        focused: visualFocus,
        highlighted: highlighted,
        destructive: destructive,
        tonal: tonal,
        segmented: segmented,
        checked: checked,
        flat: flat
    })
    readonly property color contentColor: effectiveTheme[paint.content]

    Component.onCompleted: effectiveTheme = theme
    onThemeChanged: if (theme)
        effectiveTheme = theme

    contentItem: Item {
        implicitWidth: (buttonIcon.visible ? buttonIcon.width : 0) + (buttonLabel.visible ? buttonLabel.implicitWidth : 0) + (buttonIcon.visible && buttonLabel.visible ? control.spacing : 0)
        implicitHeight: buttonContent.implicitHeight

        Row {
            id: buttonContent
            anchors.centerIn: parent
            anchors.alignWhenCentered: false
            spacing: control.spacing

            Controls.MaterialIcon {
                id: buttonIcon
                visible: control.icon.name.length > 0
                name: control.icon.name
                size: control.iconSize > 0 ? control.iconSize : control.segmented ? Foundation.controls.button.segmentedIconSize : control.compact ? Foundation.controls.button.compactIconSize : Foundation.controls.button.iconSize
                color: control.contentColor
                anchors.verticalCenter: parent.verticalCenter
                anchors.alignWhenCentered: false
            }
            Basic.Label {
                id: buttonLabel
                objectName: "buttonLabel"
                width: Math.max(0, Math.min(implicitWidth, control.availableWidth - (buttonIcon.visible ? buttonIcon.width + control.spacing : 0)))
                elide: Text.ElideRight
                visible: !control.compact && control.text.length > 0
                text: control.text
                color: control.contentColor
                font: control.font
                anchors.verticalCenter: parent.verticalCenter
                anchors.alignWhenCentered: false
            }
        }
    }

    background: Rectangle {
        radius: control.segmented ? Math.max(3, control.effectiveTheme.itemRadius - 2) : Math.min(height / 2, control.effectiveTheme.buttonRadius)
        color: control.paint.pressedMix ? control.effectiveTheme.blend(control.effectiveTheme.error, control.effectiveTheme.workspace, 0.18) : control.paint.background === "transparent" ? "transparent" : control.effectiveTheme[control.paint.background]
        border.width: control.paint.borderWidth
        border.color: control.effectiveTheme[control.paint.border]

        Behavior on color {
            ColorAnimation {
                duration: control.down ? control.effectiveTheme.clickMotionFast : control.hovered ? control.effectiveTheme.hoverMotionFast : control.effectiveTheme.motionFast
                easing.type: Easing.OutCubic
            }
        }
    }

    HoverHandler {
        objectName: "buttonCursorHandler"
        cursorShape: control.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
    }

    TapHandler {
        acceptedDevices: PointerDevice.TouchScreen
        acceptedButtons: Qt.LeftButton
        gesturePolicy: TapHandler.DragThreshold
        onPressedChanged: {
            if (pressed) {
                control.lastActivationWasTouch = true;
                control.lastActivationAt = Date.now();
            }
        }
    }

    Controls.ToolTip {
        theme: control.effectiveTheme
        visible: control.hovered && (control.toolTip.length > 0 || (control.compact && control.text.length > 0)) && !control.effectiveTheme.suppressToolTips
        text: control.toolTip.length > 0 ? control.toolTip : control.text
    }
}

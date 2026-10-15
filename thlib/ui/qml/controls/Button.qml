import "../tactic_frame/core/foundation.mjs" as Foundation
import QtQuick
import QtQuick.Controls.Basic as Basic
import "." as Controls

Basic.Button {
    id: control

    required property var theme
    // Dynamic windows can release their theme binding before child controls.
    property var effectiveTheme: theme
    property bool destructive: false
    property bool tonal: false
    property bool compact: false
    property bool segmented: false
    property string toolTip: ""
    property bool lastActivationWasTouch: false
    property double lastActivationAt: -1000

    implicitWidth: compact ? implicitHeight : Math.max(Foundation.controls.button.minimumWidth, contentItem.implicitWidth + leftPadding + rightPadding)
    implicitHeight: effectiveTheme.controlHeight
    leftPadding: compact ? 0 : (icon.name.length ? Foundation.controls.button.iconPadding : Foundation.controls.button.padding)
    rightPadding: compact ? 0 : Foundation.controls.button.padding
    spacing: segmented ? Foundation.controls.button.segmentedSpacing : compact ? 0 : Foundation.controls.button.spacing
    font.family: effectiveTheme.fontFamily
    font.pointSize: Typography.body
    font.weight: Font.DemiBold
    icon.width: segmented ? Foundation.controls.button.segmentedIconSize : Foundation.controls.button.iconSize
    icon.height: segmented ? Foundation.controls.button.segmentedIconSize : Foundation.controls.button.iconSize
    icon.color: contentColor

    readonly property color contentColor: !enabled ? effectiveTheme.disabledText : segmented ? checked ? effectiveTheme.selectedText : effectiveTheme.secondaryText : destructive && highlighted ? effectiveTheme.onError : destructive ? effectiveTheme.error : highlighted ? effectiveTheme.selectedText : effectiveTheme.primaryText

    Component.onCompleted: effectiveTheme = theme
    onThemeChanged: if (theme)
        effectiveTheme = theme

    contentItem: Item {
        implicitWidth: buttonContent.implicitWidth
        implicitHeight: buttonContent.implicitHeight

        Row {
            id: buttonContent
            anchors.centerIn: parent
            spacing: control.spacing

            Controls.MaterialIcon {
                visible: control.icon.name.length > 0
                name: control.icon.name
                size: control.segmented ? Foundation.controls.button.segmentedIconSize : control.compact ? Foundation.controls.button.compactIconSize : Foundation.controls.button.iconSize
                color: control.contentColor
                anchors.verticalCenter: parent.verticalCenter
            }
            Basic.Label {
                visible: !control.compact && control.text.length > 0
                text: control.text
                color: control.contentColor
                font: control.font
                anchors.verticalCenter: parent.verticalCenter
            }
        }
    }

    background: Rectangle {
        radius: control.segmented ? Math.max(3, control.effectiveTheme.itemRadius - 2) : Math.min(height / 2, control.effectiveTheme.buttonRadius)
        color: control.segmented ? !control.enabled ? "transparent" : control.down ? control.effectiveTheme.surfaceContainerHighest : control.checked ? control.effectiveTheme.selected : control.hovered ? control.effectiveTheme.rowHover : "transparent" : !control.enabled ? control.effectiveTheme.surfaceContainerHigh : control.down ? control.destructive && control.highlighted ? control.effectiveTheme.blend(control.effectiveTheme.error, control.effectiveTheme.workspace, 0.18) : control.effectiveTheme.selected : control.destructive && control.highlighted ? control.effectiveTheme.error : control.highlighted ? control.effectiveTheme.action : control.hovered ? control.effectiveTheme.rowHover : control.tonal ? control.effectiveTheme.secondaryContainer : control.effectiveTheme.surfaceContainerHigh
        border.width: control.segmented || control.highlighted || control.flat ? 0 : 1
        border.color: control.destructive ? control.effectiveTheme.error : control.effectiveTheme.outlineVariant

        Behavior on color {
            ColorAnimation {
                duration: control.down ? control.effectiveTheme.clickMotionFast : control.hovered ? control.effectiveTheme.hoverMotionFast : control.effectiveTheme.motionFast
                easing.type: Easing.OutCubic
            }
        }
    }

    HoverHandler {
        objectName: "buttonCursorHandler"
        cursorShape: Qt.PointingHandCursor
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

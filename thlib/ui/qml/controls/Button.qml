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
    property string toolTip: ""
    property bool lastActivationWasTouch: false
    property double lastActivationAt: -1000

    implicitWidth: compact
        ? implicitHeight
        : Math.max(72, contentItem.implicitWidth + leftPadding + rightPadding)
    implicitHeight: effectiveTheme.controlHeight
    leftPadding: compact ? 0 : (icon.name.length ? 12 : 16)
    rightPadding: compact ? 0 : 16
    spacing: compact ? 0 : 7
    font.family: effectiveTheme.fontFamily
    font.pointSize: Typography.body
    font.weight: Font.DemiBold
    icon.width: 16
    icon.height: 16
    icon.color: contentColor

    readonly property color contentColor: !enabled
        ? effectiveTheme.disabledText
        : destructive && highlighted ? effectiveTheme.onError
        : destructive ? effectiveTheme.error
        : highlighted ? effectiveTheme.selectedText
        : effectiveTheme.primaryText

    Component.onCompleted: effectiveTheme = theme
    onThemeChanged: if (theme) effectiveTheme = theme

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
                size: control.compact ? 18 : 16
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
        radius: Math.min(height / 2, control.effectiveTheme.buttonRadius)
        color: !control.enabled
            ? control.effectiveTheme.surfaceContainerHigh
            : control.down
                ? control.destructive && control.highlighted
                    ? control.effectiveTheme.blend(
                        control.effectiveTheme.error,
                        control.effectiveTheme.workspace,
                        0.18
                    )
                    : control.effectiveTheme.selected
            : control.destructive && control.highlighted
                ? control.effectiveTheme.error
            : control.highlighted ? control.effectiveTheme.action
            : control.hovered ? control.effectiveTheme.rowHover
            : control.tonal ? control.effectiveTheme.secondaryContainer
            : control.effectiveTheme.surfaceContainerHigh
        border.width: control.highlighted || control.flat ? 0 : 1
        border.color: control.destructive
            ? control.effectiveTheme.error
            : control.effectiveTheme.outlineVariant

        Behavior on color {
            ColorAnimation {
                duration: control.down
                    ? control.effectiveTheme.clickMotionFast
                    : control.hovered
                        ? control.effectiveTheme.hoverMotionFast
                        : control.effectiveTheme.motionFast
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
                control.lastActivationWasTouch = true
                control.lastActivationAt = Date.now()
            }
        }
    }

    Controls.ToolTip {
        theme: control.effectiveTheme
        visible: control.hovered
            && (control.toolTip.length > 0
                || (control.compact && control.text.length > 0))
            && !control.effectiveTheme.suppressToolTips
        text: control.toolTip.length > 0
            ? control.toolTip : control.text
    }
}

import QtQuick
import QtQuick.Controls.Basic as Basic

Basic.Button {
    id: control

    required property var theme
    property bool destructive: false
    property bool tonal: false
    property bool compact: false
    property string toolTip: ""

    implicitWidth: compact
        ? implicitHeight
        : Math.max(72, contentItem.implicitWidth + leftPadding + rightPadding)
    implicitHeight: theme.controlHeight
    leftPadding: compact ? 0 : (icon.name.length ? 12 : 16)
    rightPadding: compact ? 0 : 16
    spacing: compact ? 0 : 7
    font.family: theme.fontFamily
    font.pixelSize: 10
    font.weight: Font.DemiBold
    icon.width: 16
    icon.height: 16
    icon.color: contentColor

    readonly property color contentColor: !enabled
        ? theme.disabledText
        : destructive ? theme.error
        : highlighted ? theme.selectedText
        : theme.primaryText

    contentItem: Item {
        implicitWidth: buttonContent.implicitWidth
        implicitHeight: buttonContent.implicitHeight

        Row {
            id: buttonContent
            anchors.centerIn: parent
            spacing: control.spacing

            MaterialIcon {
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
        radius: Math.min(height / 2, theme.buttonRadius)
        color: !control.enabled
            ? theme.surfaceContainerHigh
            : control.down ? theme.selected
            : control.highlighted ? theme.action
            : control.hovered ? theme.rowHover
            : control.tonal ? theme.secondaryContainer
            : theme.surfaceContainerHigh
        border.width: control.highlighted || control.flat ? 0 : 1
        border.color: control.destructive ? theme.error : theme.outlineVariant

        Behavior on color {
            ColorAnimation {
                duration: theme.motionFast
                easing.type: Easing.OutCubic
            }
        }
    }

    HoverHandler {
        objectName: "md3ButtonCursorHandler"
        cursorShape: control.enabled
            ? Qt.PointingHandCursor : Qt.ArrowCursor
    }

    Md3ToolTip {
        theme: control.theme
        visible: control.hovered
            && (control.toolTip.length > 0
                || (control.compact && control.text.length > 0))
            && !control.theme.suppressToolTips
        text: control.toolTip.length > 0
            ? control.toolTip : control.text
    }
}

import QtQuick
import QtQuick.Controls
import "." as Controls

Rectangle {
    id: root

    required property var theme
    property string text: ""
    property string iconName: ""
    property bool interactive: false
    property bool dense: false
    property real maximumWidth: 0
    signal clicked()
    property color accentColor: theme.secondaryText
    readonly property real interactionOpacity: !interactive
        ? 0 : chipTap.pressed ? 0.12 : chipHover.hovered ? 0.08 : 0

    implicitWidth: chipText.implicitWidth
        + (root.iconName.length > 0 ? (root.dense ? 11 : 13) + 5 : 0)
        + (root.dense ? 10 : 16)
    implicitHeight: root.dense ? 20 : 24
    width: root.maximumWidth > 0
        ? Math.min(implicitWidth, root.maximumWidth) : implicitWidth
    clip: true
    radius: height / 2
    color: interactionOpacity > 0
        ? theme.overlay(
            theme.surfaceContainerHigh,
            theme.primaryText,
            interactionOpacity
        )
        : theme.surfaceContainerHigh
    Behavior on color {
        ColorAnimation {
            duration: chipTap.pressed
                ? root.theme.clickMotionFast
                : root.theme.hoverMotionFast
            easing.type: Easing.OutCubic
        }
    }

    Row {
        id: content
        anchors.centerIn: parent
        spacing: 5

        Loader {
            id: chipIcon
            anchors.verticalCenter: parent.verticalCenter
            active: root.iconName.length > 0
            sourceComponent: Controls.MaterialIcon {
                name: root.iconName
                size: root.dense ? 11 : 13
                color: root.accentColor
            }
        }
        Label {
            id: chipText
            anchors.verticalCenter: parent.verticalCenter
            width: Math.min(implicitWidth, Math.max(
                0, root.width - (root.dense ? 10 : 16)
                    - (chipIcon.active ? chipIcon.width + content.spacing : 0)
            ))
            text: root.text
            color: root.accentColor
            font.family: root.theme.fontFamily
            font.pointSize: root.dense
                ? Typography.micro : Typography.caption
            font.weight: Font.DemiBold
            elide: root.dense ? Text.ElideMiddle : Text.ElideRight
        }
    }

    HoverHandler {
        id: chipHover
        enabled: root.interactive
        cursorShape: root.interactive ? Qt.PointingHandCursor : Qt.ArrowCursor
    }
    Controls.ActivationHandler {
        id: chipTap
        enabled: root.interactive
        onActivated: root.clicked()
    }
}

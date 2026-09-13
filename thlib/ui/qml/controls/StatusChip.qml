import QtQuick
import QtQuick.Controls
import "." as Controls

Rectangle {
    id: root

    required property var theme
    property string text: ""
    property string iconName: ""
    property bool interactive: false
    signal clicked()
    property color accentColor: theme.secondaryText
    readonly property real interactionOpacity: !interactive
        ? 0 : chipTap.pressed ? 0.12 : chipHover.hovered ? 0.08 : 0

    implicitWidth: content.implicitWidth + 16
    implicitHeight: 24
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
            anchors.verticalCenter: parent.verticalCenter
            active: root.iconName.length > 0
            sourceComponent: Controls.MaterialIcon {
                name: root.iconName
                size: 13
                color: root.accentColor
            }
        }
        Label {
            anchors.verticalCenter: parent.verticalCenter
            text: root.text
            color: root.accentColor
            font.family: root.theme.fontFamily
            font.pointSize: Typography.caption
            font.weight: Font.DemiBold
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

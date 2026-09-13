import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    property string emoji: ""
    property int count: 0
    property bool checked: false
    property string toolTip: ""
    signal clicked()

    implicitWidth: reactionRow.implicitWidth + 16
    implicitHeight: 28

    Rectangle {
        id: surface
        anchors.fill: parent
        radius: height / 2
        color: Qt.tint(
            root.theme.surfaceContainerHighest,
            Qt.rgba(
                root.theme.cyan.r,
                root.theme.cyan.g,
                root.theme.cyan.b,
                root.checked ? 0.34 : 0.18
            )
        )

        Behavior on color {
            ColorAnimation { duration: root.theme.clickMotionFast }
        }

        Controls.MaterialRipple {
            id: ripple
            theme: root.theme
            color: root.theme.rippleStrong
            shapeRadius: surface.radius
        }
    }

    RowLayout {
        id: reactionRow
        anchors.centerIn: parent
        spacing: 5

        Text {
            text: root.emoji
            font.family: root.theme.emojiFontFamily
            font.pixelSize: 18
            renderType: Text.NativeRendering
        }

        Label {
            visible: root.count > 1
            text: root.count
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
            font.weight: Font.DemiBold
        }
    }

    HoverHandler {
        id: reactionHover
        cursorShape: Qt.PointingHandCursor
    }
    Controls.ActivationHandler {
        cursorShape: Qt.PointingHandCursor
        onPressedChanged: {
            if (pressed)
                ripple.burst(point.position.x, point.position.y)
        }
        onActivated: root.clicked()
    }

    Controls.ToolTip {
        theme: root.theme
        visible: root.toolTip.length > 0 && reactionHover.hovered
        text: root.toolTip
    }
}

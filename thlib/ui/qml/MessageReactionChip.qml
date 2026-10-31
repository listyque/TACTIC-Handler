import "tactic_frame/core/foundation.mjs" as Foundation
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
    signal clicked

    implicitWidth: reactionRow.implicitWidth + Foundation.controls.reactionChip.padding * 2
    implicitHeight: Foundation.controls.reactionChip.height

    Rectangle {
        id: surface
        anchors.fill: parent
        radius: root.theme.buttonRadius
        color: Qt.tint(root.theme.surfaceContainerHighest, Qt.rgba(root.theme.cyan.r, root.theme.cyan.g, root.theme.cyan.b, root.checked ? Foundation.controls.reactionChip.checkedTintOpacity : Foundation.controls.reactionChip.tintOpacity))

        Behavior on color {
            ColorAnimation {
                duration: root.theme.clickMotionFast
            }
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
        anchors.alignWhenCentered: false
        spacing: Foundation.controls.reactionChip.spacing

        Text {
            Layout.preferredWidth: Foundation.controls.reactionChip.emojiSize
            horizontalAlignment: Text.AlignHCenter
            text: root.emoji
            font.family: root.theme.emojiFontFamily
            font.pixelSize: Foundation.controls.reactionChip.emojiSize
            renderType: Text.NativeRendering
        }

        Label {
            visible: root.count > 1
            text: root.count
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.hintingPreference: Font.PreferVerticalHinting
            font.pixelSize: Foundation.textStyles.body
            font.weight: Font.DemiBold
        }
    }

    HoverHandler {
        id: reactionHover
        cursorShape: Qt.PointingHandCursor
    }
    Controls.PopupAction {
        objectName: "reactionChipAction"
        anchors.fill: parent
        background: Item {}
        contentItem: Item {}
        Accessible.name: root.toolTip || root.emoji + " " + root.count
        Accessible.checkable: true
        Accessible.checked: root.checked
        onPressedChanged: if (pressed)
            ripple.burst(pressX, pressY)
        onClicked: root.clicked()
    }

    Controls.ToolTip {
        theme: root.theme
        visible: root.toolTip.length > 0 && reactionHover.hovered
        text: root.toolTip
    }
}

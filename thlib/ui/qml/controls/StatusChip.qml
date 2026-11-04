import "../tactic_frame/core/foundation.mjs" as Foundation
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
    signal clicked
    property color accentColor: theme.secondaryText
    readonly property real interactionOpacity: !interactive ? 0 : chipTap.down ? 0.12 : chipHover.hovered ? 0.08 : 0

    implicitWidth: chipText.implicitWidth + (root.iconName.length > 0 ? (root.dense ? Foundation.controls.statusChip.denseIconSize : Foundation.controls.statusChip.iconSize) + 5 : 0) + ((root.dense ? Foundation.controls.statusChip.densePadding : Foundation.controls.statusChip.padding) * 2)
    implicitHeight: root.dense ? Foundation.controls.statusChip.denseHeight : Foundation.controls.statusChip.height
    width: root.maximumWidth > 0 ? Math.min(implicitWidth, root.maximumWidth) : implicitWidth
    clip: true
    radius: height / 2
    color: interactionOpacity > 0 ? theme.overlay(theme.surfaceContainerHigh, theme.primaryText, interactionOpacity) : theme.surfaceContainerHigh
    Behavior on color {
        ColorAnimation {
            duration: chipTap.down ? root.theme.clickMotionFast : root.theme.hoverMotionFast
            easing.type: Easing.OutCubic
        }
    }

    Row {
        id: content
        anchors.centerIn: parent
        anchors.alignWhenCentered: false
        spacing: Foundation.controls.statusChip.spacing

        Loader {
            id: chipIcon
            anchors.verticalCenter: parent.verticalCenter
            active: root.iconName.length > 0
            sourceComponent: Controls.MaterialIcon {
                name: root.iconName
                size: root.dense ? Foundation.controls.statusChip.denseIconSize : Foundation.controls.statusChip.iconSize
                color: root.accentColor
            }
        }
        Label {
            id: chipText
            anchors.verticalCenter: parent.verticalCenter
            width: Math.min(implicitWidth, Math.max(0, root.width - ((root.dense ? Foundation.controls.statusChip.densePadding : Foundation.controls.statusChip.padding) * 2) - (chipIcon.active ? chipIcon.width + content.spacing : 0)))
            text: root.text
            color: root.accentColor
            font.family: root.theme.fontFamily
            font.hintingPreference: Font.PreferVerticalHinting
            font.pixelSize: root.dense ? Foundation.textStyles.menuHeading : Foundation.textStyles.caption
            font.weight: Font.DemiBold
            elide: root.dense ? Text.ElideMiddle : Text.ElideRight
        }
    }

    HoverHandler {
        id: chipHover
        enabled: root.interactive
        cursorShape: root.interactive ? Qt.PointingHandCursor : Qt.ArrowCursor
    }
    Controls.PopupAction {
        id: chipTap
        objectName: "statusChipAction"
        anchors.fill: parent
        visible: root.interactive
        focusPolicy: root.activeFocusOnTab && !activeFocus ? Qt.NoFocus : Qt.StrongFocus
        Accessible.ignored: root.activeFocusOnTab
        background: Item {}
        contentItem: Item {}
        Accessible.name: root.text
        onClicked: {
            if (root.activeFocusOnTab)
                root.forceActiveFocus(Qt.MouseFocusReason);
            root.clicked();
        }
    }
}

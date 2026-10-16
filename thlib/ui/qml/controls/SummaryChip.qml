import "../tactic_frame/core/foundation.mjs" as Foundation
import QtQuick
import QtQuick.Controls
import "." as Controls

Rectangle {
    id: root

    required property var theme
    property string label: ""
    property int count: 0
    property color accent: theme.action
    property bool showDot: true
    property bool showCount: true
    property bool clickable: false
    property bool compact: false
    property string iconName: ""
    signal clicked

    function focusEditor() {
        chipAction.forceActiveFocus();
    }

    readonly property real horizontalPadding: compact ? Foundation.controls.summaryChip.compactPadding : Foundation.controls.summaryChip.padding
    readonly property real auxiliaryWidth: (iconName.length ? (compact ? 14 : 16) + content.spacing : 0) + (showDot ? Foundation.controls.summaryChip.dot + content.spacing : 0) + (showCount ? countText.implicitWidth + content.spacing : 0)
    implicitWidth: caption.implicitWidth + auxiliaryWidth + horizontalPadding * 2
    implicitHeight: compact ? Foundation.controls.summaryChip.compactHeight : Foundation.controls.summaryChip.height
    radius: height / 2
    color: clickable && chipAction.hovered ? theme.rowHover : theme.surfaceContainerHigh
    border.width: compact ? 0 : 1
    border.color: clickable && chipAction.activeFocus ? theme.action : theme.outlineVariant

    Row {
        id: content

        anchors.centerIn: parent
        anchors.alignWhenCentered: false
        spacing: Foundation.controls.summaryChip.spacing

        Controls.MaterialIcon {
            visible: root.iconName.length > 0
            anchors.verticalCenter: parent.verticalCenter
            name: root.iconName
            size: root.compact ? 14 : 16
            color: root.compact ? root.accent : root.theme.primaryText
        }
        Rectangle {
            visible: root.showDot
            anchors.verticalCenter: parent.verticalCenter
            width: Foundation.controls.summaryChip.dot
            height: Foundation.controls.summaryChip.dot
            radius: width / 2
            color: root.accent
        }
        Label {
            id: caption
            width: Math.min(implicitWidth, Math.max(0, root.width - root.horizontalPadding * 2 - root.auxiliaryWidth))
            elide: Text.ElideRight
            anchors.verticalCenter: parent.verticalCenter
            textFormat: Text.PlainText
            text: root.label
            color: root.compact ? root.accent : root.theme.primaryText
            font.family: root.theme.fontFamily
            font.hintingPreference: Font.PreferVerticalHinting
            font.pixelSize: root.compact ? Foundation.textStyles.caption : Foundation.textStyles.secondary
        }
        Label {
            id: countText
            visible: root.showCount
            anchors.verticalCenter: parent.verticalCenter
            text: root.count
            color: root.accent
            font.family: root.theme.fontFamily
            font.hintingPreference: Font.PreferVerticalHinting
            font.pixelSize: root.compact ? Foundation.textStyles.caption : Foundation.textStyles.secondary
            font.weight: Font.DemiBold
        }
    }

    Controls.PopupAction {
        id: chipAction
        objectName: "summaryChipAction"
        anchors.fill: parent
        visible: root.clickable
        background: Item {}
        contentItem: Item {}
        Accessible.name: root.label + (root.showCount ? " " + root.count : "")
        onClicked: root.clicked()
    }
}

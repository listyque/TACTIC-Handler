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

    implicitWidth: content.implicitWidth + (compact ? Foundation.controls.summaryChip.compactPadding : Foundation.controls.summaryChip.padding) * 2
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
            anchors.verticalCenter: parent.verticalCenter
            text: root.label
            color: root.compact ? root.accent : root.theme.primaryText
            font.family: root.theme.fontFamily
            font.hintingPreference: Font.PreferVerticalHinting
            font.pixelSize: root.compact ? Foundation.textStyles.caption : Foundation.textStyles.secondary
        }
        Label {
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
        Accessible.name: root.label + " " + root.count
        onClicked: root.clicked()
    }
}

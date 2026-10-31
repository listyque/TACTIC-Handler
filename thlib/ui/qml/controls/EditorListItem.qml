import "../tactic_frame/core/foundation.mjs" as Foundation
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "." as Controls

Controls.PopupAction {
    id: root

    required property var theme
    property string description: ""
    property string iconName: ""
    property string badgeText: ""
    property bool selected: false
    property bool wrapTitle: false
    property color accent: theme.action

    implicitHeight: Math.max(theme.controlHeight + Foundation.controls.editorListItem.minimumExtraHeight, content.implicitHeight + padding * 2)
    padding: Foundation.controls.editorListItem.padding
    Accessible.name: text
    Accessible.description: description

    background: Controls.ItemSurface {
        theme: root.theme
        selected: root.selected
        hovered: root.hovered
        pressed: root.down
        accent: root.accent
        normalColor: "transparent"
        selectedColor: root.theme.selected
        railVisible: root.selected
        cornerRadius: root.theme.itemRadius
        separatorVisible: false
        borderWidth: root.visualFocus ? 1 : 0
        borderColor: root.theme.action
    }
    contentItem: RowLayout {
        id: content
        spacing: Foundation.controls.editorListItem.spacing
        Controls.MaterialIcon {
            visible: root.iconName.length > 0
            name: root.iconName
            size: Foundation.controls.editorListItem.iconSize
            color: root.enabled ? root.accent : root.theme.disabledText
        }
        ColumnLayout {
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            spacing: Foundation.controls.editorListItem.textSpacing
            Label {
                Layout.fillWidth: true
                text: root.text
                color: root.enabled ? root.theme.primaryText : root.theme.disabledText
                font.family: root.theme.fontFamily
                font.hintingPreference: Font.PreferVerticalHinting
                font.pixelSize: Foundation.textStyles.body
                font.weight: root.selected ? Font.DemiBold : Font.Normal
                wrapMode: root.wrapTitle ? Text.Wrap : Text.NoWrap
                maximumLineCount: root.wrapTitle ? 3 : 1
                elide: Text.ElideRight
            }
            Label {
                Layout.fillWidth: true
                visible: text.length > 0
                text: root.description
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.hintingPreference: Font.PreferVerticalHinting
                font.pixelSize: Foundation.textStyles.secondary
                wrapMode: Text.WordWrap
                maximumLineCount: 2
                elide: Text.ElideRight
            }
        }
        Controls.SummaryChip {
            theme: root.theme
            visible: root.badgeText.length > 0
            label: root.badgeText
            showDot: false
            showCount: false
        }
    }
}

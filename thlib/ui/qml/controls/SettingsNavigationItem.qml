import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "." as Controls

Controls.PopupAction {
    id: root

    required property var theme
    property string iconName: ""
    property string description: ""
    property bool selected: false
    property bool compact: false
    property bool dirty: false

    implicitHeight: 48
    leftPadding: compact ? 0 : 14
    rightPadding: compact ? 0 : 14
    Accessible.name: text
    Accessible.description: description

    background: Controls.ItemSurface {
        theme: root.theme
        selected: root.selected
        hovered: root.hovered
        pressed: root.down
        normalColor: "transparent"
        selectedColor: root.theme.selected
        cornerRadius: 14
        separatorVisible: false
        railVisible: root.selected
        railTopMargin: 13
        railBottomMargin: 13
        borderWidth: root.visualFocus ? 1 : 0
        borderColor: root.theme.action
    }

    contentItem: RowLayout {
        spacing: root.compact ? 0 : 12
        Item {
            Layout.fillWidth: root.compact
            Layout.fillHeight: true
            Layout.preferredWidth: root.compact ? -1 : 18
            Controls.MaterialIcon {
                anchors.centerIn: parent
                name: root.iconName
                size: 18
                color: root.selected ? root.theme.action : root.theme.secondaryText
            }
        }
        Label {
            Layout.fillWidth: true
            visible: !root.compact
            text: root.text
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.bodyLarge
            font.weight: root.selected ? Font.DemiBold : Font.Normal
            elide: Text.ElideRight
        }
        Rectangle {
            visible: !root.compact && root.selected && root.dirty
            Layout.preferredWidth: 7
            Layout.preferredHeight: 7
            radius: 4
            color: root.theme.action
        }
    }

    Controls.ToolTip {
        theme: root.theme
        visible: root.compact && root.hovered
        text: root.text
    }
}

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

RowLayout {
    id: root
    required property var theme
    required property string login
    required property string displayName
    required property string initials
    required property string avatarUrl
    required property string avatarColor
    property bool retired: false
    property real avatarSize: 40
    property bool emphasized: false
    opacity: retired ? 0.5 : 1
    spacing: 12

    Controls.ItemPreview {
        objectName: "userIdentityAvatar_" + root.login
        Layout.preferredWidth: root.avatarSize
        Layout.preferredHeight: root.avatarSize
        theme: root.theme
        source: root.avatarUrl
        fallbackIcon: "person"
        fallbackText: root.initials
        accent: root.avatarColor || root.theme.action
        round: true
        outlined: true
        animateAppearance: false
        previewSize: root.avatarSize
    }
    ColumnLayout {
        Layout.fillWidth: true
        Layout.minimumWidth: 0
        spacing: 3
        Label {
            Layout.fillWidth: true
            text: root.displayName || root.login
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pointSize: root.emphasized ? Controls.Typography.bodyLarge : Controls.Typography.body
            font.weight: Font.DemiBold
            elide: Text.ElideRight
        }
        Label {
            Layout.fillWidth: true
            text: root.login
            visible: text.length > 0 && text !== root.displayName
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.label
            elide: Text.ElideRight
        }
    }
}

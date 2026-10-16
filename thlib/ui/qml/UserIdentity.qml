import "tactic_frame/core/foundation.mjs" as Foundation
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
    property real avatarSize: Foundation.controls.identity.avatarSize
    property bool emphasized: false
    opacity: retired ? 0.5 : 1
    spacing: Foundation.controls.identity.spacing

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
        spacing: Foundation.controls.identity.textSpacing
        Label {
            Layout.fillWidth: true
            text: root.displayName || root.login
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.hintingPreference: Font.PreferVerticalHinting
            font.pixelSize: root.emphasized ? Foundation.textStyles.bodyLarge : Foundation.textStyles.body
            font.weight: Font.DemiBold
            elide: Text.ElideRight
        }
        Label {
            Layout.fillWidth: true
            text: root.login
            visible: text.length > 0 && text !== root.displayName
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.hintingPreference: Font.PreferVerticalHinting
            font.pixelSize: Foundation.textStyles.secondary
            elide: Text.ElideRight
        }
    }
    RowLayout {
        visible: root.retired
        spacing: 0
        Controls.MaterialIcon {
            name: "archive"
            size: 16
            color: root.theme.secondaryText
        }
        Label {
            text: qsTr("Retired")
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.hintingPreference: Font.PreferVerticalHinting
            font.pixelSize: 13
        }
    }
}

import "../tactic_frame/core/foundation.mjs" as Foundation
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "." as Controls

RowLayout {
    id: root

    required property var theme
    property string iconName: "info"
    property string label: ""
    property string value: ""

    spacing: 9
    visible: value.length > 0

    Controls.MaterialIcon {
        name: root.iconName
        size: 15
        color: root.theme.secondaryText
    }

    ColumnLayout {
        Layout.fillWidth: true
        Layout.minimumWidth: 0
        spacing: 0

        Label {
            Layout.fillWidth: true
            text: root.label
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.hintingPreference: Font.PreferVerticalHinting
            font.pixelSize: Foundation.textStyles.caption
            elide: Text.ElideRight
        }

        Label {
            Layout.fillWidth: true
            text: root.value
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.hintingPreference: Font.PreferVerticalHinting
            font.pixelSize: Foundation.textStyles.body
            elide: Text.ElideMiddle
        }
    }
}

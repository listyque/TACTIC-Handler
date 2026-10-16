import "../tactic_frame/core/foundation.mjs" as Foundation
import QtQuick
import QtQuick.Controls

Rectangle {
    id: root
    required property var theme
    property string iconName: "move-to-inbox"
    property string promptText: ""
    property bool accepted: true
    anchors.fill: parent
    anchors.margins: Foundation.controls.dropTarget.margin
    radius: root.theme.surfaceRadius
    color: root.theme.surfaceContainerHigh
    opacity: Foundation.controls.dropTarget.surfaceOpacity
    border.width: Foundation.controls.dropTarget.borderWidth
    border.color: root.accepted ? root.theme.action : root.theme.error

    Column {
        anchors.centerIn: parent
        spacing: Foundation.controls.dropTarget.spacing
        MaterialIcon {
            anchors.horizontalCenter: parent.horizontalCenter
            name: root.iconName
            size: Foundation.controls.dropTarget.iconSize
            color: root.accepted ? root.theme.action : root.theme.error
        }
        Label {
            anchors.horizontalCenter: parent.horizontalCenter
            text: root.promptText
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.hintingPreference: Font.PreferVerticalHinting
            font.pixelSize: Foundation.controls.dropTarget.textSize
            font.weight: Font.DemiBold
            width: Math.max(0, root.width - 24)
            wrapMode: Text.Wrap
            horizontalAlignment: Text.AlignHCenter
        }
    }
}

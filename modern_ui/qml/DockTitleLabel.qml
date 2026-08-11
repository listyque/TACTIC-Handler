import QtQuick
import QtQuick.Controls

Label {
    id: root

    required property var theme
    property string titleText: ""
    property bool active: true

    text: titleText.toUpperCase()
    color: theme.primaryText
    font.family: theme.fontFamily
    font.pixelSize: 9
    font.weight: active ? Font.DemiBold : Font.Medium
    font.letterSpacing: 0.55
    verticalAlignment: Text.AlignVCenter
    elide: Text.ElideRight
}

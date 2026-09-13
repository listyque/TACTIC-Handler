import QtQuick
import QtQuick.Controls
import "." as Controls

Label {
    required property var theme

    color: theme.secondaryText
    font.family: theme.fontFamily
    font.pointSize: Controls.Typography.body
    font.weight: Font.DemiBold
    font.letterSpacing: 0.5
}

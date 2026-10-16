import "../tactic_frame/core/foundation.mjs" as Foundation
import QtQuick
import QtQuick.Controls

Label {
    required property var theme

    color: theme.secondaryText
    font.family: theme.fontFamily
    font.hintingPreference: Font.PreferVerticalHinting
    font.pixelSize: Foundation.textStyles.body
    font.weight: Font.DemiBold
    font.letterSpacing: 0.5
}

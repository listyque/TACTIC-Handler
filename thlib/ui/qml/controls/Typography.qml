pragma Singleton

import QtQuick
import "../tactic_frame/core/foundation.mjs" as Foundation

QtObject {
    readonly property real micro: Foundation.typography.micro
    readonly property real caption: Foundation.typography.caption
    readonly property real label: Foundation.typography.label
    readonly property real body: Foundation.typography.body
    readonly property real bodyLarge: Foundation.typography.bodyLarge
    readonly property real title: Foundation.typography.title
    readonly property FontMetrics bodyMetrics: FontMetrics {
        font: Qt.font({
            family: Foundation.fontFamily,
            pixelSize: Foundation.textStyles.body,
            weight: Font.Normal,
            hintingPreference: Font.PreferVerticalHinting
        })
    }
    readonly property FontMetrics captionMetrics: FontMetrics {
        font: Qt.font({
            family: Foundation.fontFamily,
            pixelSize: Foundation.textStyles.caption,
            weight: Font.Normal,
            hintingPreference: Font.PreferVerticalHinting
        })
    }
}

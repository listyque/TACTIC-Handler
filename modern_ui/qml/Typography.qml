pragma Singleton

import QtQuick
import "Typography.js" as Scale

QtObject {
    // Point sizes preserve a stable physical text size across Windows display
    // scales. Pixel-sized captions looked acceptable only when HiDPI scaling
    // happened to enlarge them and became unreadable at the native 96 DPI.
    readonly property real micro: Scale.micro
    readonly property real caption: Scale.caption
    readonly property real label: Scale.label
    readonly property real body: Scale.body
    readonly property real bodyLarge: Scale.bodyLarge
}
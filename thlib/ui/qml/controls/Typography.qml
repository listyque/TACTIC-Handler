pragma Singleton

import QtQuick
import "../Typography.js" as Scale

QtObject {
    readonly property real micro: Scale.micro
    readonly property real caption: Scale.caption
    readonly property real label: Scale.label
    readonly property real body: Scale.body
    readonly property real bodyLarge: Scale.bodyLarge
    readonly property real title: Scale.title
}

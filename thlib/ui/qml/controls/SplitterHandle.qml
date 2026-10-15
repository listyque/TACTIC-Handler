import "../tactic_frame/core/foundation.mjs" as Foundation
import QtQuick
import QtQuick.Controls
import "." as Controls

Rectangle {
    id: root
    required property var theme
    property bool vertical: true

    implicitWidth: Foundation.controls.splitter.extent
    implicitHeight: Foundation.controls.splitter.extent
    color: "transparent"

    Controls.ResizeGripVisual {
        objectName: "splitterGripVisual"
        theme: root.theme
        vertical: root.vertical
        hovered: root.SplitHandle.hovered
        pressed: root.SplitHandle.pressed
    }
}

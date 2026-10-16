import "../tactic_frame/core/foundation.mjs" as Foundation
import QtQuick
import QtQuick.Controls.Material
import QtQuick.Controls as QtControls

Item {
    id: root

    required property var uiTheme
    property bool running: false
    readonly property real indicatorExtent: Math.min(width, height)
    readonly property bool canRender: running && visible && indicatorExtent >= 4

    implicitWidth: Foundation.controls.feedback.busyExtent
    implicitHeight: Foundation.controls.feedback.busyExtent

    QtControls.BusyIndicator {
        id: nativeIndicator
        objectName: "busyIndicatorArc"
        anchors.fill: parent
        padding: 0
        Material.accent: root.uiTheme.action
        running: root.canRender
        visible: root.canRender
        palette.highlight: root.uiTheme.action
        palette.dark: root.uiTheme.action
        palette.light: root.uiTheme.action
    }
}

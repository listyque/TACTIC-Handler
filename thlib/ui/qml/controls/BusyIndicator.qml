import QtQuick
import QtQuick.Controls as QtControls

Item {
    id: root

    required property var uiTheme
    property bool running: false
    readonly property real indicatorExtent: Math.min(width, height)
    readonly property bool canRender:
        running && visible && indicatorExtent >= 4

    implicitWidth: 24
    implicitHeight: 24

    QtControls.BusyIndicator {
        id: nativeIndicator
        objectName: "busyIndicatorArc"
        anchors.fill: parent
        running: root.canRender
        visible: root.canRender
        palette.highlight: root.uiTheme.action
        palette.dark: root.uiTheme.action
        palette.light: root.uiTheme.action
    }
}

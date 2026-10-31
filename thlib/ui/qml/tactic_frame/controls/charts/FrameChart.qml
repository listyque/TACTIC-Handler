pragma ComponentBehavior: Bound
import QtQuick
import "../../../controls" as Controls
import "chart.ui.mjs" as Chart

Item {
    id: root
    required property var theme
    required property var node
    property int hovered: -1
    readonly property var paintPalette: theme.framePalette
    readonly property string tip: hovered < 0 ? "" : node.labels[hovered] + ": " + Chart.number(node.chart.values[hovered], node.language)
    objectName: node.id
    activeFocusOnTab: node.focusable !== false
    Accessible.role: Accessible.Graphic
    Accessible.name: node.text
    onNodeChanged: if (canvas) {
        hovered = -1;
        canvas.requestPaint();
    }
    onPaintPaletteChanged: if (canvas)
        canvas.requestPaint()
    onHoveredChanged: if (canvas)
        canvas.requestPaint()
    Canvas {
        id: canvas
        anchors.fill: parent
        onPaint: Chart.paint(getContext("2d"), root.node.chart, role => root.theme.frameColor(role), root.hovered)
    }
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.NoButton
        hoverEnabled: true
        onPositionChanged: mouse => root.hovered = Chart.hit(root.node.chart, mouse.x, mouse.y)
        onExited: root.hovered = -1
    }
    Loader {
        anchors.fill: parent
        active: root.tip.length > 0 && !root.theme.suppressToolTips
        sourceComponent: Controls.ToolTip {
            theme: root.theme
            visible: true
            delay: 300
            text: root.tip
        }
    }
}

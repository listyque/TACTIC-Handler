import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

ConfigurationSection {
    id: root

    required property var graphData
    readonly property bool compact: width < 560
    readonly property var graphNodes: graphData.nodes || []
    readonly property var graphEdges: graphData.edges || []

    title: qsTr("Relationship map")
    description: qsTr("A read-only view of this Search Type and only its direct schema relationships.")

    onGraphDataChanged: if (visible) Qt.callLater(graph.resetView)
    onVisibleChanged: if (visible) Qt.callLater(graph.resetView)

    RowLayout {
        Layout.fillWidth: true
        spacing: 6

        Label {
            objectName: "adminSearchTypeRelationshipMapHint"
            Layout.fillWidth: true
            text: qsTr("Wheel: zoom · Middle-button drag: pan")
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.label
            wrapMode: Text.WordWrap
        }
        Controls.CompactIconButton {
            objectName: "adminSearchTypeRelationshipZoomOut"
            theme: root.theme
            iconName: "minus"
            toolTip: qsTr("Zoom out")
            onClicked: graph.zoomCentered(graph.zoom - 0.1)
        }
        Label {
            visible: !root.compact
            text: Math.round(graph.zoom * 100) + "%"
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.label
        }
        Controls.CompactIconButton {
            objectName: "adminSearchTypeRelationshipZoomIn"
            theme: root.theme
            iconName: "add"
            toolTip: qsTr("Zoom in")
            onClicked: graph.zoomCentered(graph.zoom + 0.1)
        }
        Controls.CompactIconButton {
            objectName: "adminSearchTypeRelationshipReset"
            theme: root.theme
            iconName: "refresh"
            toolTip: qsTr("Reset canvas view")
            onClicked: graph.resetView()
        }
    }
    Controls.NodeGraph {
        id: graph
        objectName: "adminSearchTypeRelationshipGraph"
        Layout.fillWidth: true
        Layout.preferredHeight: root.compact ? 300 : 360
        Layout.minimumHeight: 260
        theme: root.theme
        nodes: root.graphNodes
        edges: root.graphEdges
        selectedNode: root.graphData.center || ""
        selectedNodes: selectedNode ? [selectedNode] : []
        selectedEdge: -1
        readOnly: true
        selectionEnabled: false
    }
}

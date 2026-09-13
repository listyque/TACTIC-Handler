import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

AdminDocumentShell {
    id: root

    readonly property bool workflow: controller.mode === "workflow"
    readonly property bool creatingPipeline: workflow && !controller.identity
        && controller.document.xml !== undefined
    readonly property string searchType: controller.creationSearchType || ""
    readonly property var searchTypeInfo: (controller.metadata.searchTypes || []).find(row => row.identity === searchType) || ({})
    readonly property var missingProcesses: workflow ? controller.nodes.filter(row => row.referenceOnly).map(row => row.identity) : []
    property string page: "canvas"
    property var deletionConfirmation: null
    signal createSearchTypeRequested(real x, real y)
    signal nodeWorkflowsRequested()
    signal deleteSearchTypeRequested(string identity)

    function showDeleteConfirmation() {
        if (!root.deletionConfirmation) {
            const overlay = root.Window.contentItem
            if (!overlay) return
            root.deletionConfirmation = deletionConfirmationFactory.createObject(overlay, {
                "theme": root.theme,
                "controller": root.controller.deletionEditor
            })
        }
        root.deletionConfirmation.open()
    }

    function createSearchType() {
        const point = graph.insertionPoint()
        root.createSearchTypeRequested(point.x, point.y)
    }

    Component {
        id: deletionConfirmationFactory
        AdminSchemaDeleteConfirmation {}
    }
    Component.onDestruction: if (root.deletionConfirmation)
        root.deletionConfirmation.destroy()

    title: workflow ? qsTr("Workflow editor") : qsTr("Project schema")
    description: workflow
        ? qsTr("Arrange processes on the canvas, connect their ports and select a process to configure it.")
        : qsTr("Connect Search Types to describe how Search Objects relate to each other.")
    iconName: workflow ? "process" : "schema"
    showSelector: false
    confirmationDetails: workflow ? "" : controller.connectionEditor.saveDetails
    allowCreate: !workflow || searchType.length > 0
    createRequiresCleanDocument: workflow
    createText: workflow ? qsTr("Create") : qsTr("New Search Type")
    createObjectName: workflow ? "adminCreateDocument" : "adminCreateSchemaType"
    createAction: function() {
        if (root.workflow) root.controller.new_document()
        else root.createSearchType()
    }
    onCreatingPipelineChanged: if (creatingPipeline) {
        page = "canvas"
        graphProperties.showSelection()
    }
    editorContent: ColumnLayout {
        // The alias reparents this item into AdminDocumentShell's plain Item.
        anchors.fill: parent // qmllint disable Quick.layout-positioning
        spacing: 12

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Controls.SegmentedButton {
                objectName: "adminGraphPages"
                Layout.fillWidth: true
                Layout.minimumWidth: implicitWidth
                Layout.maximumWidth: 320
                theme: root.theme
                segmentWidth: 126
                currentValue: root.page
                model: [
                    {value: "canvas", label: "Canvas", icon: "schema"},
                    {value: "technical", label: "Technical", icon: "code"}
                ]
                onActivated: value => {
                    root.forceActiveFocus()
                    root.page = value
                }
            }
            Controls.Button {
                objectName: "adminEditPipeline"
                theme: root.theme
                text: qsTr("Pipeline settings")
                icon.name: "tune"
                visible: root.workflow && root.page === "canvas"
                onClicked: {
                    root.forceActiveFocus()
                    root.controller.clear_selection()
                    graphProperties.showSelection()
                }
            }
            Controls.CompactIconButton {
                id: arrangeButton
                objectName: "adminArrangeGraph"
                theme: root.theme
                iconName: "hierarchy"
                toolTip: qsTr("Arrange nodes")
                visible: root.page === "canvas"
                enabled: root.controller.canWrite && !root.controller.busy
                    && root.controller.nodes.length > 0
                onClicked: arrangeMenu.toggleBelow(arrangeButton)
            }
            Item { Layout.fillWidth: true }
            RowLayout {
                visible: root.page === "canvas"
                spacing: 6
                Controls.CompactIconButton {
                    theme: root.theme
                    iconName: "minus"
                    toolTip: qsTr("Zoom out") + " (−)"
                    onClicked: graph.zoomCentered(graph.zoom - 0.1)
                }
                Label {
                    text: Math.round(graph.zoom * 100) + "%"
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                }
                Controls.CompactIconButton {
                    theme: root.theme
                    iconName: "add"
                    toolTip: qsTr("Zoom in") + " (+)"
                    onClicked: graph.zoomCentered(graph.zoom + 0.1)
                }
                Controls.CompactIconButton {
                    theme: root.theme
                    iconName: "refresh"
                    toolTip: qsTr("Reset canvas view") + " (Home)"
                    onClicked: graph.resetView()
                }
            }
        }
        Label {
            objectName: "adminWorkflowSearchType"
            Layout.fillWidth: true
            visible: root.workflow
            text: root.searchType
                ? qsTr("Search Type: %1").arg(root.searchTypeInfo.label && root.searchTypeInfo.label !== root.searchType
                    ? root.searchTypeInfo.label + " · " + root.searchType : root.searchType)
                : qsTr("No Search Type is linked. Create a workflow from the Search Type editor.")
            textFormat: Text.PlainText
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.label
            wrapMode: Text.Wrap
        }
        Label {
            Layout.fillWidth: true
            visible: root.controller.metadata.shared === true
            text: qsTr("Shared pipeline: read-only. Create a project-owned pipeline to make project-specific changes.")
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.label
            wrapMode: Text.WordWrap
        }
        Label {
            objectName: "adminMissingProcesses"
            Layout.fillWidth: true
            visible: root.missingProcesses.length > 0
            text: qsTr("Connections refer to missing processes: %1. Add the missing processes or remove their connections before saving.").arg(root.missingProcesses.join(", "))
            textFormat: Text.PlainText
            color: root.theme.error
            wrapMode: Text.Wrap
        }
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: root.page === "canvas"
            spacing: 8

            Label {
                Layout.fillWidth: true
                text: graph.pendingConnection
                    ? (graph.pendingInput ? qsTr("Choose an output port. Esc cancels the connection.")
                                          : qsTr("Choose an input port. Esc cancels the connection."))
                    : qsTr("Wheel: zoom. Middle-button drag: pan. Shift/Ctrl-click or drag a frame to select nodes.")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.label
                wrapMode: Text.WordWrap
                HoverHandler { id: canvasHelpHover }
                Controls.ToolTip {
                    theme: root.theme
                    visible: canvasHelpHover.hovered
                    text: qsTr("Drag a selected node to move the group · Delete: remove selection · F: center selection · Home: reset view · Ctrl+S: save")
                }
            }
            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 12

                Controls.NodeGraph {
                    id: graph
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumWidth: 200
                    theme: root.theme
                    nodes: root.controller.nodes
                    edges: root.controller.edges
                    selectedNode: root.controller.selectedNode
                    selectedNodes: root.controller.selectedNodes
                    selectedEdge: root.controller.selectedEdge
                    readOnly: !root.controller.canWrite
                    onNodeSelected: identity => {
                        graph.forceActiveFocus()
                        root.controller.select_node(identity)
                        graphProperties.showSelection()
                    }
                    onNodesSelected: (identities, primary) => {
                        graph.forceActiveFocus()
                        root.controller.select_nodes(identities, primary)
                        graphProperties.showSelection()
                    }
                    onEdgeSelected: index => {
                        graph.forceActiveFocus()
                        root.controller.select_edge(index)
                        graphProperties.showSelection()
                    }
                    onNodeMoved: (identity, x, y) => root.controller.move_node(identity, x, y)
                    onNodesMoved: positions => root.controller.move_nodes(positions)
                    onRemoveRequested: graphProperties.requestRemoval()
                    onSaveRequested: root.requestSave()
                    onClearSelectionRequested: root.controller.clear_selection()
                    onConnectionRequested: (source, target) => {
                        graph.forceActiveFocus()
                        root.controller.connect_nodes(source, target)
                    }
                }
                AdminGraphProperties {
                    id: graphProperties
                    Layout.preferredWidth: root.workflow ? Math.min(460, root.width * 0.5) : Math.min(420, root.width * 0.45)
                    Layout.minimumWidth: root.workflow ? 300 : 240
                    Layout.maximumWidth: root.workflow ? 460 : 420
                    Layout.fillHeight: true
                    theme: root.theme
                    controller: root.controller
                    onWorkflowsRequested: root.nodeWorkflowsRequested()
                    onCreateSearchTypeRequested: root.createSearchType()
                    onDeleteSearchTypeRequested: root.deleteSearchTypeRequested(root.controller.selectedNode)
                    onNodeAddRequested: (identity, kind) => {
                        const point = graph.insertionPoint()
                        root.controller.add_node(identity, kind, point.x, point.y)
                        if (root.controller.selectedNode === identity && !root.controller.error)
                            graph.revealNode(identity)
                    }
                }
            }
        }
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: root.page === "technical"
            spacing: 12

            AdminXmlEditor {
                Layout.fillWidth: true
                Layout.fillHeight: true
                theme: root.theme
                description: qsTr("The native document for this canvas. Unknown elements and attributes are preserved.")
                sourceText: root.controller.document.xml || ""
                readOnly: !root.controller.canWrite
                onApplied: text => root.controller.apply_xml(text)
            }
        }
    }
    ActionMenu {
        id: arrangeMenu
        objectName: "adminArrangeMenu"
        parent: Overlay.overlay
        theme: root.theme
        preferredWidth: 320
        actions: [
            {title: "Automatic layout", header: true},
            {
                title: "Directed flow",
                status: "Connected nodes form readable layers; unconnected nodes fill alphabetical rows.",
                icon: "hierarchy",
                command: "flow"
            },
            {
                title: "Network clusters",
                status: "Connected components form compact webs; unconnected nodes fill alphabetical rows.",
                icon: "hub",
                command: "network"
            },
            {
                title: "Alphabetical grid",
                status: "All nodes fill balanced alphabetical rows.",
                icon: "grid-view",
                command: "grid"
            }
        ]
        onTriggered: command => {
            root.controller.arrange_nodes(command)
            Qt.callLater(graph.resetView)
        }
    }
}

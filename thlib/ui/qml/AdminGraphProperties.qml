import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Controls.EditorPanel {
    id: root

    required property var controller
    readonly property bool workflow: controller.mode === "workflow"
    readonly property bool nodeSelected: controller.selectedNode.length > 0
    readonly property int selectedNodeCount: (controller.selectedNodes || []).length
    readonly property bool selection: nodeSelected || controller.selectedEdge >= 0
    readonly property bool schemaConnection: !workflow && (controller.selectedEdge >= 0 || controller.connectionEditor.instance.length > 0)
    property string page: "selection"
    property string newNodeKind: (controller.metadata.nodeTypes || [])[0] || ""
    property string newSearchType: ""
    readonly property bool taskPipeline: controller.document.searchType === "sthpw/task"
    onTaskPipelineChanged: newNodeKind = taskPipeline ? "status" : (controller.metadata.nodeTypes || [])[0] || ""
    signal nodeAddRequested(string identity, string kind)
    signal workflowsRequested()
    signal createSearchTypeRequested()
    signal deleteSearchTypeRequested()

    function searchTypeOnCanvas(identity) {
        return root.controller.nodes.some(node => node.identity === identity && !node.referenceOnly)
    }

    function showSelection() {
        root.page = "selection"
        propertyScroll.contentY = 0
    }

    function requestRemoval() {
        if (!root.visible || !root.enabled || !root.selection || root.controller.busy
                || !root.controller.canWrite || root.controller.selectedReference || removeConfirmation.visible) return
        removeConfirmation.open()
    }

    function attributeLabel(key) {
        const labels = {
            name: qsTr("Identifier"), color: qsTr("Color"),
            from: qsTr("Source"), to: qsTr("Destination"),
            relationship: qsTr("Relationship"),
            from_col: qsTr("Child key column"), to_col: qsTr("Parent key column"),
            from_attr: qsTr("Output condition"), to_attr: qsTr("Input name")
        }
        return labels[key] || key
    }

    title: qsTr("Inspector")
    iconName: "tune"
    padding: 12
    actions: [
        Controls.Button {
            objectName: "adminSchemaNodeWorkflows"
            theme: root.theme
            compact: true
            flat: true
            visible: !root.workflow && root.nodeSelected
            icon.name: "workflow"
            text: qsTr("Edit pipelines")
            enabled: !root.controller.busy && (root.controller.metadata.searchTypes || [])
                .some(row => row.identity === root.controller.selectedNode)
                && !(root.controller.document.newTypes || {})[root.controller.selectedNode]
            onClicked: root.workflowsRequested()
        },
        Controls.Button {
            objectName: "adminDeleteSchemaSearchType"
            theme: root.theme
            compact: true
            flat: true
            destructive: true
            visible: !root.workflow && root.nodeSelected
            icon.name: "delete"
            text: qsTr("Delete Search Type…")
            enabled: root.controller.canWrite && !root.controller.busy
                && !(root.controller.document.newTypes || {})[root.controller.selectedNode]
                && (root.controller.metadata.searchTypes || []).some(row => row.identity === root.controller.selectedNode)
            onClicked: root.deleteSearchTypeRequested()
        },
        Controls.CompactIconButton {
            objectName: "adminAddProcess"
            theme: root.theme
            visible: root.workflow
            iconName: root.page === "add_node" ? "arrow-back" : "add"
            toolTip: root.page === "add_node" ? qsTr("Selection") : qsTr("Add node")
            onClicked: {
                root.forceActiveFocus()
                root.page = root.page === "add_node" ? "selection" : "add_node"
            }
        },
        Controls.CompactIconButton {
            objectName: "adminRemoveGraphSelection"
            theme: root.theme
            visible: root.workflow && root.page === "selection" && root.selection
            enabled: root.controller.canWrite && !root.controller.selectedReference
            iconName: "delete"
            iconColor: root.theme.error
            toolTip: qsTr("Remove from canvas") + " (Delete)"
            onClicked: root.requestRemoval()
        }
    ]

    Controls.SegmentedButton {
        objectName: "adminGraphInspectorPages"
        Layout.fillWidth: true
        visible: !root.workflow
        theme: root.theme
        currentValue: root.page
        model: [
            {value: "selection", label: "Selection", icon: "edit"},
            {value: "add_node", label: "Add node", icon: "add"}
        ]
        onActivated: value => {
            root.forceActiveFocus()
            root.page = value
        }
    }
    Flickable {
        id: propertyScroll
        objectName: "adminGraphPropertiesViewport"
        Layout.fillWidth: true
        Layout.fillHeight: true
        visible: !root.workflow || root.page === "add_node" || (root.selection && !root.nodeSelected)
        clip: true
        contentWidth: width
        contentHeight: propertyForm.implicitHeight + 4
        boundsBehavior: Flickable.StopAtBounds

        Connections {
            target: root
            function onPageChanged() { propertyScroll.contentY = 0 }
        }
        ColumnLayout {
            id: propertyForm
            width: Math.max(0, propertyScroll.width - propertyBar.reservedExtent - 4)
            spacing: 14

            Controls.EmptyState {
                visible: root.page === "selection" && !root.selection
                theme: root.theme
                iconName: root.workflow ? "process" : "schema"
                title: qsTr("Select a node or a connection")
                message: qsTr("Its details appear here. Use Add node to extend the canvas.")
                preferredHeight: 180
            }
            ColumnLayout {
                Layout.fillWidth: true
                visible: root.page === "add_node"
                spacing: 10
                enabled: root.controller.canWrite

                Label {
                    Layout.fillWidth: true
                    text: root.workflow
                        ? qsTr("Name the process and choose its native type.")
                        : qsTr("Choose a registered Search Type to add to the schema.")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                    wrapMode: Text.WordWrap
                }
                Controls.Button {
                    objectName: "adminCreateSchemaTypeFromInspector"
                    Layout.fillWidth: true
                    theme: root.theme
                    visible: !root.workflow
                    text: qsTr("New Search Type")
                    icon.name: "add"
                    onClicked: root.createSearchTypeRequested()
                }
                Controls.TextField {
                    id: nodeName
                    objectName: "adminNewProcessName"
                    Layout.fillWidth: true
                    theme: root.theme
                    visible: root.workflow
                    placeholderText: qsTr("Process name")
                }
                Controls.ResponsiveFlow {
                    Layout.fillWidth: true
                    visible: root.workflow
                    spacing: 6
                    minimumCellWidth: 130
                    preferredCellWidth: 160
                    maximumColumns: 2
                    Repeater {
                        model: root.controller.document.searchType === "sthpw/task"
                            ? ["status"] : root.controller.metadata.nodeTypes || []
                        delegate: Controls.EditorListItem {
                            id: newKindOption
                            required property string modelData
                            objectName: "adminNewNodeType_" + modelData
                            width: parent.cellWidth()
                            theme: root.theme
                            text: modelData
                            selected: root.newNodeKind === modelData
                            onClicked: root.newNodeKind = modelData
                            Controls.ToolTip {
                                theme: root.theme
                                text: newKindOption.modelData
                                visible: newKindOption.hovered
                            }
                        }
                    }
                }
                Controls.TextField {
                    id: typeFilter
                    objectName: "adminGraphTypeFilter"
                    Layout.fillWidth: true
                    theme: root.theme
                    visible: !root.workflow
                    placeholderText: qsTr("Find a Search Type")
                }
                ListView {
                    id: searchTypes
                    objectName: "adminGraphAvailableTypes"
                    Layout.fillWidth: true
                    Layout.preferredHeight: Math.min(260, Math.max(90, count * (root.theme.controlHeight + 24)))
                    visible: !root.workflow
                    clip: true
                    spacing: 4
                    boundsBehavior: Flickable.StopAtBounds
                    model: (root.controller.metadata.searchTypes || []).filter(row =>
                        (String(row.label || "") + " " + row.identity).toLocaleLowerCase().includes(typeFilter.text.toLocaleLowerCase()))
                    delegate: Controls.EditorListItem {
                        required property var modelData
                        objectName: "adminGraphType_" + modelData.identity
                        width: Math.max(0, searchTypes.width - typeBar.reservedExtent - 4)
                        theme: root.theme
                        text: modelData.label || modelData.identity
                        description: root.searchTypeOnCanvas(modelData.identity)
                            ? qsTr("Already on schema") + " · " + modelData.identity : modelData.identity
                        iconName: modelData.icon || "deployed-code"
                        accent: modelData.color || root.theme.action
                        selected: root.newSearchType === modelData.identity
                        onClicked: root.newSearchType = modelData.identity
                    }
                    ScrollBar.vertical: Controls.ScrollBar {
                        id: typeBar
                        theme: root.theme
                        flickableTarget: searchTypes
                    }
                }
            }
            ColumnLayout {
                Layout.fillWidth: true
                visible: root.page === "selection" && root.selection
                spacing: 12

                Label {
                    Layout.fillWidth: true
                    text: root.selectedNodeCount > 1
                        ? qsTr("%1 nodes selected").arg(root.selectedNodeCount)
                        : root.nodeSelected ? root.controller.selectedNode : qsTr("Connection")
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.bodyLarge
                    font.weight: Font.DemiBold
                    wrapMode: Text.Wrap
                }
                Loader {
                    Layout.fillWidth: true
                    active: root.schemaConnection
                    visible: active
                    sourceComponent: AdminSchemaConnection {
                        theme: root.theme
                        controller: root.controller
                    }
                }
                AdminXmlEditor {
                    objectName: "adminSelectionAttributesEditor"
                    Layout.fillWidth: true
                    Layout.preferredHeight: 300
                    Layout.minimumHeight: implicitHeight
                    theme: root.theme
                    title: qsTr("Attributes (JSON)")
                    buttonText: qsTr("Apply")
                    sourceText: root.controller.attributesText
                    readOnly: !root.controller.canWrite || root.controller.selectedReference
                    onApplied: text => root.controller.apply_attributes(text)
                }
                Label {
                    Layout.fillWidth: true
                    visible: root.controller.selectedReference || !root.workflow
                    text: root.controller.selectedReference
                        ? qsTr("This endpoint is inherited or implicit. Add the registered Search Type to this canvas to position it locally.")
                        : qsTr("Select a connection to choose its relationship type and key columns. Many-to-many creates an instance node in the draft.")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                    wrapMode: Text.WordWrap
                }
                Repeater {
                    model: root.selection && !root.schemaConnection
                        ? Object.keys(root.controller.selectedAttributes).filter(key =>
                            key !== "xpos" && key !== "ypos"
                                && !(root.workflow && root.nodeSelected && key !== "name"))
                        : []
                    delegate: ColumnLayout {
                        required property string modelData
                        Layout.fillWidth: true
                        spacing: 5
                        Label {
                            Layout.fillWidth: true
                            text: root.attributeLabel(modelData)
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.label
                            wrapMode: Text.WordWrap
                        }
                        Controls.TextField {
                            objectName: "adminGraphAttribute_" + modelData
                            Layout.fillWidth: true
                            theme: root.theme
                            text: String(root.controller.selectedAttributes[modelData] || "")
                            readOnly: modelData === "name" || !root.controller.canWrite || root.controller.selectedReference
                            onEditingFinished: {
                                if (text !== String(root.controller.selectedAttributes[modelData] || ""))
                                    root.controller.set_attribute(modelData, text)
                            }
                        }
                    }
                }
                Repeater {
                    model: root.workflow && root.selection && !root.nodeSelected
                        ? (root.workflow ? ["from_attr", "to_attr"] : ["from_col", "to_col"])
                            .filter(key => root.controller.selectedAttributes[key] === undefined) : []
                    delegate: ColumnLayout {
                        required property string modelData
                        Layout.fillWidth: true
                        spacing: 5
                        Label {
                            Layout.fillWidth: true
                            text: root.attributeLabel(modelData)
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.label
                        }
                        Controls.TextField {
                            objectName: "adminGraphAttribute_" + modelData
                            Layout.fillWidth: true
                            theme: root.theme
                            readOnly: !root.controller.canWrite
                            onEditingFinished: if (text.length) root.controller.set_attribute(modelData, text)
                        }
                    }
                }
            }
        }
        ScrollBar.vertical: Controls.ScrollBar {
            id: propertyBar
            theme: root.theme
            flickableTarget: propertyScroll
        }
    }
    Loader {
        Layout.fillWidth: true
        Layout.fillHeight: true
        active: root.workflow && root.page === "selection" && root.nodeSelected && !root.controller.selectedReference
        visible: active
        sourceComponent: AdminProcessSettings {
            theme: root.theme
            controller: root.controller
        }
    }
    Controls.EmptyState {
        objectName: "adminMissingProcessDetails"
        Layout.fillWidth: true
        Layout.fillHeight: true
        visible: root.workflow && root.page === "selection" && root.controller.selectedReference
        theme: root.theme
        iconName: "warning"
        title: qsTr("Missing process: %1").arg(root.controller.selectedNode)
        message: qsTr("Only a connection to this process exists in the XML. Use Add node to recreate it with the same name, or select and remove the connection.")
    }
    Loader {
        Layout.fillWidth: true
        Layout.fillHeight: true
        active: root.workflow && root.page === "selection" && !root.selection
        visible: active
        sourceComponent: AdminPipelineSettings {
            theme: root.theme
            controller: root.controller
        }
    }
    Controls.Button {
        objectName: "adminRemoveGraphSelection"
        Layout.fillWidth: true
        theme: root.theme
        visible: !root.workflow && root.page === "selection" && root.selection
        text: qsTr("Remove from canvas")
        icon.name: "delete"
        destructive: true
        enabled: root.controller.canWrite && !root.controller.selectedReference
        onClicked: root.requestRemoval()
    }
    Controls.Button {
        id: addNodeButton
        readonly property bool revealExisting: !root.workflow && root.searchTypeOnCanvas(root.newSearchType)
        objectName: "adminAddGraphNode"
        Layout.fillWidth: true
        theme: root.theme
        visible: root.page === "add_node"
        text: addNodeButton.revealExisting ? qsTr("Show on canvas") : qsTr("Add to canvas")
        icon.name: addNodeButton.revealExisting ? "visibility" : "add"
        highlighted: true
        enabled: root.controller.canWrite && !root.controller.busy && (root.workflow
            ? nodeName.text.trim().length > 0 && root.newNodeKind.length > 0
            : searchTypes.model.some(row => row.identity === root.newSearchType))
        onClicked: {
            const identity = root.workflow ? nodeName.text.trim() : root.newSearchType
            root.nodeAddRequested(identity, root.newNodeKind)
            if (root.controller.selectedNode === identity && !root.controller.error) {
                root.showSelection()
                nodeName.clear()
                root.newSearchType = ""
            }
        }
    }
    Controls.Dialog {
        id: removeConfirmation
        objectName: "adminRemoveGraphConfirmation"
        theme: root.theme
        parent: Overlay.overlay
        modal: true
        anchors.centerIn: parent
        width: Math.min(420, parent.width - 40)
        title: qsTr("Remove from canvas?")
        standardButtons: Dialog.NoButton
        focus: true
        onOpened: cancelRemove.forceActiveFocus()
        onAccepted: root.controller.remove_selected()
        footer: Controls.DialogActions {
            theme: root.theme
            Controls.Button {
                id: cancelRemove
                objectName: "adminCancelRemoveGraph"
                theme: root.theme
                text: qsTr("Cancel")
                onClicked: removeConfirmation.reject()
            }
            Controls.Button {
                objectName: "adminConfirmRemoveGraph"
                theme: root.theme
                text: qsTr("Remove from canvas")
                icon.name: "delete"
                destructive: true
                onClicked: removeConfirmation.accept()
            }
        }
        contentItem: Label {
            text: !root.nodeSelected
                ? qsTr("Only the selected connection will be removed when you save. Its nodes and their data will not be deleted.")
                : root.selectedNodeCount > 1
                ? qsTr("The selected nodes and their connections will be removed from the canvas when you save. Server data is not deleted.")
                : root.workflow
                ? qsTr("The change is staged until Save. Processes used by tasks, snapshots or triggers cannot be removed on the server.")
                : qsTr("Only the selected node and its connections will be removed from this schema when you save. The Search Type, its table, objects and pipelines will not be deleted.")
            color: root.theme.primaryText
            wrapMode: Text.WordWrap
        }
    }
}

import QtQuick
import QtQuick.Controls
import "../../../controls" as Controls
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/files/workspace/tree.ui.mjs" as UI

Rectangle {
    id: root
    required property var workspace
    readonly property var theme: workspace.theme
    property var workspaceList: null
    property var depotList: null
    property real navigationHeight: 0
    color: theme.panelDeep
    radius: theme.surfaceRadius
    border.color: theme.outlineVariant
    clip: true
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe({
            native: true,
            style: root.theme.style,
            treeView: workspace.workspaceState.tree_view,
            navigationHeight: root.navigationHeight
        }, width, height, workspace.language)
        views: ({
                navigation: {
                    component: navigationPort
                },
                depot: {
                    component: depotPort
                },
                workspace: {
                    component: workspacePort
                }
            })
        onEvent: action => {
            if (action.type === "treeView")
                workspace.set("tree_view", action.value);
        }
    }
    Component {
        id: navigationPort
        FileWorkspaceNavigation {
            theme: root.theme
            controller: workspace.controller
            onImplicitHeightChanged: root.navigationHeight = implicitHeight
            Component.onCompleted: root.navigationHeight = implicitHeight
            onMenuRequested: (kind, anchor) => workspace.menu(kind, anchor)
        }
    }
    Component {
        id: workspacePort
        ListView {
            id: workspaceTree
            Component.onCompleted: root.workspaceList = workspaceTree
            Keys.onPressed: event => workspace.fileKey(event, "workspace")
            objectName: "workspaceWorkspaceTree"
            anchors.fill: parent
            clip: true
            model: workspace.controller.workspace_model
            ScrollBar.vertical: Controls.ScrollBar {
                id: workspaceBar
                theme: workspace.theme
                flickableTarget: workspaceTree
            }
            MouseArea {
                z: -1
                anchors.fill: parent
                acceptedButtons: Qt.RightButton
                onClicked: mouse => {
                    workspace.actionMenu.actions = workspace.actions("tree");
                    workspace.actionMenu.openAt(parent, mouse.x, mouse.y);
                }
            }
            delegate: FileWorkspaceTreeRow {
                required property var node
                width: workspaceTree.width - workspaceBar.reservedExtent
                theme: workspace.theme
                row: node
                enabled: true
                caption: workspace.treeTitle(node)
                selected: workspace.workspaceState.selection_scope === "workspace" && workspace.workspaceState.selection_ids.indexOf(node.id) >= 0
                onSelectedByUser: modifiers => workspace.controller.select_row("workspace", node.id, modifiers)
                onMenuRequested: (source, x, y) => workspace.contextMenu("workspace", node, source, x, y)
                onDragRequested: dragData = workspace.controller.drag_payload("workspace", node.id)
                onDisclosure: workspace.act("toggle_workspace_tree", {
                    id: node.id
                })
                onActivated: workspace.workspaceActivated(node)
            }
        }
    }
    Component {
        id: depotPort
        ListView {
            id: depotTree
            Component.onCompleted: root.depotList = depotTree
            Keys.onPressed: event => workspace.fileKey(event, "depot")
            objectName: "workspaceDepotTree"
            anchors.fill: parent
            clip: true
            model: workspace.controller.depot_model
            ScrollBar.vertical: Controls.ScrollBar {
                id: depotBar
                theme: workspace.theme
                flickableTarget: depotTree
            }
            MouseArea {
                z: -1
                anchors.fill: parent
                acceptedButtons: Qt.RightButton
                onClicked: mouse => {
                    workspace.actionMenu.actions = workspace.actions("tree");
                    workspace.actionMenu.openAt(parent, mouse.x, mouse.y);
                }
            }
            delegate: FileWorkspaceTreeRow {
                required property var node
                readonly property var modelData: node
                width: depotTree.width - depotBar.reservedExtent
                theme: workspace.theme
                row: modelData
                enabled: true
                caption: workspace.treeTitle(modelData)
                selected: workspace.workspaceState.selection_scope === "depot" && workspace.workspaceState.selection_ids.indexOf(modelData.id) >= 0
                onSelectedByUser: modifiers => workspace.controller.select_row("depot", modelData.id, modifiers)
                onMenuRequested: (source, x, y) => workspace.contextMenu("depot", modelData, source, x, y)
                onDragRequested: dragData = workspace.controller.drag_payload("depot", modelData.id)
                onDisclosure: workspace.act("toggle_depot", {
                    id: modelData.id
                })
                onActivated: workspace.depotActivated(modelData)
            }
            Label {
                anchors.centerIn: parent
                visible: depotTree.count === 0
                text: qsTr("No depots")
                color: workspace.theme.secondaryText
            }
        }
    }
}

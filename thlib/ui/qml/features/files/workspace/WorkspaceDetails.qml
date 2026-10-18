import QtQuick
import QtQuick.Controls
import "../../../controls" as Controls
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/files/workspace/details.ui.mjs" as UI

Rectangle {
    id: root
    required property var workspace
    readonly property var theme: workspace.theme
    readonly property var workspaceState: workspace.state
    readonly property string kind: workspace.detailsView
    color: theme.panelDeep
    radius: theme.surfaceRadius
    border.color: theme.outlineVariant
    clip: true
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe({
            native: true,
            kind: root.kind,
            title: workspace.activeTab.custom ? workspace.activeTab.title : qsTr(workspace.activeTab.title),
            showResolved: workspace.showResolved,
            taskError: root.workspaceState.task_info.error,
            after: root.workspaceState.task_files_after,
            preview: root.workspaceState.preview,
            busy: workspace.busy
        }, width, height, workspace.language)
        views: ({
                rows: {
                    component: rowsPort
                },
                taskFiles: {
                    component: taskFilesPort
                }
            })
        onEvent: (action, source) => {
            if (action.type === "menu")
                workspace.menu("details", source);
            else if (action.type === "resolved")
                workspace.showResolved = action.value;
            else if (action.type === "more")
                workspace.act("next_task_files");
        }
    }
    Component {
        id: rowsPort
        ListView {
            id: rows
            objectName: "workspaceDetailRows"
            clip: true
            spacing: 2
            model: root.kind === "conflicts" ? (workspace.showResolved ? root.workspaceState.resolved_conflicts : root.workspaceState.conflicts) : root.workspaceState.tasks
            ScrollBar.vertical: Controls.ScrollBar {
                id: bar
                theme: root.theme
                flickableTarget: rows
            }
            delegate: Item {
                id: rowItem
                required property var modelData
                width: rows.width - bar.reservedExtent
                height: 36
                activeFocusOnTab: true
                Accessible.role: Accessible.ListItem
                Accessible.name: UI.rowText(root.kind, modelData, workspace.language)
                function select(modifiers, context) {
                    workspace.detail = modelData;
                    if (root.kind === "tasks")
                        workspace.act("task_files", {
                            task: modelData.task
                        });
                    if (root.kind === "conflicts" && !workspace.showResolved) {
                        const selected = root.workspaceState.conflict_selected;
                        if (!context || selected.indexOf(modelData.path) < 0)
                            workspace.set("conflict_selected", modifiers & Qt.ControlModifier ? (selected.includes(modelData.path) ? selected.filter(path => path !== modelData.path) : selected.concat([modelData.path])) : [modelData.path]);
                    }
                }
                Keys.onReturnPressed: select(0, false)
                Keys.onSpacePressed: select(0, false)
                Frame.FrameView {
                    anchors.fill: parent
                    theme: root.theme
                    interactive: false
                    scene: UI.row(root.kind, rowItem.modelData, width, workspace.detail === rowItem.modelData, workspace.language)
                }
                Controls.ActivationHandler {
                    onActivated: modifiers => rowItem.select(modifiers, false)
                }
                MouseArea {
                    anchors.fill: parent
                    acceptedButtons: Qt.RightButton
                    onClicked: mouse => {
                        rowItem.select(mouse.modifiers, true);
                        workspace.actionMenu.actions = workspace.actions("details");
                        workspace.actionMenu.openAt(rowItem, mouse.x, mouse.y);
                    }
                }
            }
            Label {
                anchors.centerIn: parent
                visible: rows.count === 0
                text: root.kind === "conflicts" ? qsTr("No conflicts") : qsTr("No transfers")
                color: root.theme.secondaryText
                width: parent.width
                horizontalAlignment: Text.AlignHCenter
                elide: Text.ElideRight
            }
        }
    }
    Component {
        id: taskFilesPort
        ListView {
            id: taskFiles
            objectName: "workspaceTaskFiles"
            clip: true
            model: root.workspaceState.task_files
            ScrollBar.vertical: Controls.ScrollBar {
                id: taskBar
                theme: root.theme
                flickableTarget: taskFiles
            }
            delegate: Frame.FrameView {
                required property var modelData
                width: taskFiles.width - taskBar.reservedExtent
                height: 32
                theme: root.theme
                interactive: false
                scene: UI.row("taskFiles", modelData, width, false, workspace.language)
            }
        }
    }
}

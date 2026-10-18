import QtQuick
import QtQuick.Controls
import "../../../controls" as Controls
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/files/workspace/footer.ui.mjs" as UI

Controls.DockWorkspaceFooter {
    id: root
    objectName: "fileWorkspaceFooter"
    required property var workspace
    theme: workspace.theme
    color: theme.panelDeep
    implicitHeight: theme.controlHeight
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe({
            progress: workspace.state.progress,
            busy: workspace.busy,
            workspace: workspace.state.workspace,
            selected: workspace.state.selected.length,
            logVisible: workspace.state.log_visible
        }, width, height, workspace.language)
        views: ({
                busy: {
                    component: busyPort
                },
                progress: {
                    component: progressPort
                }
            })
        onEvent: action => {
            if (action.type === "log")
                workspace.set("log_visible", !workspace.state.log_visible);
            else if (action.type === "stop")
                workspace.controller.stop();
        }
    }
    Component {
        id: busyPort
        Controls.BusyIndicator {
            uiTheme: root.theme
            running: workspace.busy
        }
    }
    Component {
        id: progressPort
        ProgressBar {
            property var frameNode: ({
                    value: 0,
                    indeterminate: false,
                    label: ""
                })
            value: frameNode.value
            indeterminate: frameNode.indeterminate
            Accessible.name: frameNode.label
        }
    }
}

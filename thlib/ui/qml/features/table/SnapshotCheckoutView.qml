import QtQuick
import "../../tactic_frame" as Frame
import "../../controls" as Controls
import "../../tactic_frame/features/files/snapshot_checkout.ui.mjs" as UI

Item {
    id: root
    required property var theme
    property var owner: tableServicesController.checkoutEditor
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    function requestClose() {
        owner.request_close();
        return !owner.isOpen;
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        focus: true
        scene: width > 0 && height > 0 ? UI.describe(root.owner.model, width, height, root.language) : {
            nodes: []
        }
        models: ({
                files: root.owner.fileModel
            })
        views: ({
                progress: {
                    component: progressPort,
                    nodeProps: true
                }
            })
        describeRow: (list, row, index) => UI.fileRow(row, list.width - 16, root.language)
        Keys.onEscapePressed: event => {
            root.owner.request_close();
            event.accepted = true;
        }
        onEvent: (action, value) => root.owner.activate(action, value)
    }
    Component {
        id: progressPort
        Controls.ProgressBar {
            property var frameNode: ({})
            theme: root.theme
            from: 0
            to: 1
            value: frameNode.value || 0
            indeterminate: !!frameNode.indeterminate
            Accessible.name: frameNode.label || ""
        }
    }
}

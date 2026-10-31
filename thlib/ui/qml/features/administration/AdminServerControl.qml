import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/configuration/server_control.ui.mjs" as UI

Item {
    id: root
    required property var theme
    required property var controller
    property string language: "en"
    property bool confirming: false
    readonly property var frameModel: ({
            workers: controller.document.workers,
            runtime: controller.metadata.runtime,
            dirty: controller.dirty || controller.writeUncertain,
            busy: controller.busy,
            restarting: controller.restarting,
            error: controller.error,
            notice: controller.notice,
            confirm: confirming
        })
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.viewport(root.frameModel, root.width, root.height, root.language)
        onEvent: action => {
            if (root.controller.busy || root.controller.restarting)
                return;
            if (action.type === "workers")
                root.controller.set_field("workers", action.value);
            else if (action.type === "save")
                root.controller.save();
            else if (action.type === "discard")
                root.controller.discard();
            else if (action.type === "refresh")
                root.controller.reload();
            else if (action.type === "restart")
                root.confirming = true;
            else if (action.type === "reject")
                root.confirming = false;
            else if (action.type === "accept") {
                root.confirming = false;
                root.controller.restart();
            }
        }
    }
}

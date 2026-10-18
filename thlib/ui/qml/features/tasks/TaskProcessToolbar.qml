import QtQuick
import "../.."
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/tasks/workspace.ui.mjs" as UI

Frame.FrameView {
    id: root
    required property var controller
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    implicitHeight: scene.height
    scene: UI.processToolbar({
        controlHeight: root.theme.controlHeight,
        title: controller.hasTarget ? controller.targetTitle : "",
        dirty: controller.dirtyProcessCount > 0,
        busy: controller.busy,
        hasTarget: controller.hasTarget
    }, width, language)
    views: ({
            surfaces: {
                component: surfacePort
            }
        })
    onEvent: action => {
        if (action.type === "save-all")
            controller.save_all_process_changes();
        else if (action.type === "discard-all")
            controller.discard_all_process_changes();
        else if (action.type === "refresh")
            controller.refresh();
    }
    Component {
        id: surfacePort
        TaskWorkspaceSurfaceSwitcher {
            theme: root.theme
            enabled: !root.controller.busy
        }
    }
}

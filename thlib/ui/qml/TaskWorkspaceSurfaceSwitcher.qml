import QtQuick
import "tactic_frame" as Frame
import "tactic_frame/features/tasks/workspace.ui.mjs" as UI

Item {
    id: root

    required property var theme

    implicitWidth: 108
    implicitHeight: root.theme.controlHeight

    function activateSurface(value) {
        if (value === "workspace") {
            tasksController.open_workspace();
            return;
        }
        tasksController.set_quick_view_mode(value);
        if (tasksController.workspaceSurface !== "quick")
            tasksController.open_quick_workspace();
    }

    Frame.FrameView {
        id: surfaceSwitcher
        objectName: "quickTaskViewSwitcher"
        anchors.fill: parent
        theme: root.theme
        scene: UI.surfaces({
            value: tasksController.workspaceSurface === "browser" ? "workspace" : tasksController.quickViewMode,
            disabled: !root.enabled,
            controlHeight: root.theme.controlHeight
        }, width, typeof localizationController === "undefined" ? "en" : localizationController.current_language)
        onEvent: (action, source) => root.activateSurface(action.value)
    }
}

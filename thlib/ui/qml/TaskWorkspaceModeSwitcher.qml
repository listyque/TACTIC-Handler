import QtQuick
import "tactic_frame" as Frame
import "tactic_frame/features/tasks/workspace.ui.mjs" as UI

Frame.FrameView {
    implicitWidth: UI.modeWidth
    implicitHeight: theme.controlHeight
    scene: UI.modes({
        view: tasksController.viewMode === "list" ? "table" : "gantt",
        controlHeight: theme.controlHeight,
        busy: tasksController.advancedSaving
    }, width, typeof localizationController === "undefined" ? "en" : localizationController.current_language)
    onEvent: action => {
        if (action.type === "mode")
            tasksController.set_view_mode(action.value === "table" ? "list" : action.value);
        else if (action.type === "calendar")
            tasksController.open_calendar();
    }
}

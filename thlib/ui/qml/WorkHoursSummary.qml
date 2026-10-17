import QtQuick
import QtQuick.Controls
import "tactic_frame" as Frame
import "tactic_frame/features/objects/inspector.ui.mjs" as UI

Frame.FrameView {
    id: root
    required property var controller
    property bool compact: false
    property var summary: controller.currentSummary
    implicitHeight: scene.height
    scene: UI.workHours({
        summary: root.summary,
        expanded: !root.compact,
        busy: root.controller.busy,
        hasTask: root.controller.hasTask
    }, width, typeof localizationController === "undefined" ? "en" : localizationController.current_language)
    onEvent: event => {
        if (event.type === "log")
            logDialog.openForCreate();
        else if (event.type === "timesheet")
            root.controller.open_timesheet();
    }
    WorkHourEditorDialog {
        id: logDialog
        parent: Overlay.overlay
        theme: root.theme
        controller: root.controller
    }
}

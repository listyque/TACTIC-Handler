import QtQuick
import QtQuick.Layouts
import "tactic_frame" as Frame
import "tactic_frame/features/tasks/workspace.ui.mjs" as UI

Item {
    id: root
    required property var theme
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    signal previewRequested(var sourceItem)
    objectName: "taskPendingChangesOverlaySlot"
    Layout.preferredHeight: 0
    Layout.minimumHeight: 0
    Layout.maximumHeight: 0
    z: 80

    Frame.FrameView {
        objectName: "taskPendingChangesBar"
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: scene.height
        theme: root.theme
        visible: tasksController.advancedDirtyCount > 0
        scene: UI.pending({
            count: tasksController.advancedDirtyCount,
            saving: tasksController.advancedSaving,
            blocked: tasksController.advancedSaving,
            preview: tasksController.viewMode === "gantt" && tasksController.ganttChangePreview.length > 0
        }, width, root.language)
        onEvent: (action, source) => {
            if (action.type === "save")
                tasksController.save_advanced_changes();
            else if (action.type === "discard")
                tasksController.discard_advanced_changes();
            else if (action.type === "preview")
                root.previewRequested(source);
        }
    }
}

import QtQuick
import QtQuick.Controls
import "../../controls" as Controls
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/tasks/columns.ui.mjs" as UI

Controls.ScrollablePopup {
    id: root
    required property var controller
    signal configureRequested
    parent: Overlay.overlay
    preferredSurfaceWidth: 416
    minimumSurfaceWidth: 240
    maximumSurfaceHeight: 500
    contentSpacing: 0
    function openBelow(source) {
        openBelowItem(source, true, 6);
    }
    function toggleBelow(source) {
        toggleBelowItem(source, true, 6);
    }
    Frame.FrameView {
        width: parent.width
        height: scene.height
        theme: root.theme
        scene: UI.describe({
            columns: root.controller.taskColumns,
            busy: root.controller.advancedSaving,
            configure: true
        }, width, typeof localizationController === "undefined" ? "en" : localizationController.current_language)
        views: ({
                width: {
                    component: widthPort,
                    nodeProps: true
                }
            })
        onEvent: action => {
            if (action.type === "visible")
                root.controller.set_task_column_visible(action.field, action.value);
            else if (action.type === "move")
                root.controller.move_task_column(action.field, action.value);
            else if (action.type === "reset")
                root.controller.reset_task_columns();
            else if (action.type === "configure") {
                root.close();
                root.configureRequested();
            }
        }
    }
    Component {
        id: widthPort
        Controls.SpinBox {
            property var frameNode: ({
                    record: {
                        width: 40
                    }
                })
            theme: root.theme
            objectName: frameNode.id || ""
            from: 40
            to: 480
            stepSize: 1
            editable: true
            value: frameNode.record.width || 40
            enabled: !!frameNode.enabled
            Accessible.name: frameNode.label || ""
            onValueModified: root.controller.set_task_column_width(frameNode.record.key, value)
        }
    }
}

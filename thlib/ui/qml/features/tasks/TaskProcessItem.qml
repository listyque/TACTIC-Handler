import QtQuick
import "../.."
import "../../controls" as Controls
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/tasks/process.ui.mjs" as UI

Frame.FrameView {
    id: root
    required property var record
    required property var controller
    required property var users
    property string mode: "cards"
    signal menuRequested(var source)
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    scene: UI.describe({
        label: record.label,
        count: record.taskCount,
        color: record.color,
        hasTask: record.hasTask,
        dirty: record.dirty,
        notes: record.notes,
        hasTarget: controller.hasTarget,
        blocked: controller.busy
    }, width, mode, language)
    views: ({
            status: {
                component: statusPort
            },
            assigned: {
                component: userPort
            }
        })
    onEvent: (action, source) => {
        if (action.type === "save")
            controller.save_process_changes(record.index);
        else if (action.type === "discard")
            controller.discard_process_changes(record.index);
        else if (action.type === "notes")
            controller.open_notes(controller.targetSearchKey, record.process, record.currentTaskCode);
        else if (action.type === "menu")
            root.menuRequested(source);
    }
    Component {
        id: statusPort
        Controls.ComboBox {
            theme: root.theme
            objectName: "quickTaskStatus_" + root.record.process
            actionField: true
            enabled: !root.controller.busy
            model: root.record.statusChoices
            textRole: "label"
            valueRole: "value"
            colorRole: "color"
            translateDisplayText: false
            currentIndex: (model || []).findIndex(row => row.value === root.record.status)
            displayText: currentIndex >= 0 ? currentText : qsTr("Select status")
            onActivated: root.controller.set_process_draft(root.record.index, "status", currentValue)
        }
    }
    Component {
        id: userPort
        UserComboBox {
            theme: root.theme
            objectName: "quickTaskAssignee_" + root.record.process
            actionField: true
            enabled: !root.controller.busy
            userModel: root.users
            model: root.record.userChoices
            textRole: "label"
            valueRole: "value"
            currentIndex: (model || []).findIndex(row => row.value === root.record.assigned)
            onActivated: root.controller.set_process_draft(root.record.index, "assigned", currentValue)
        }
    }
}

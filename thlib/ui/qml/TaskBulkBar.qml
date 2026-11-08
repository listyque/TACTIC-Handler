import QtQuick
import QtQuick.Controls
import "controls" as Controls
import "features/tasks" as Tasks
import "tactic_frame" as Frame
import "tactic_frame/features/tasks/editor.ui.mjs" as EditorUI
import "tactic_frame/features/tasks/bulk.ui.mjs" as BulkUI

Frame.FrameView {
    id: root
    objectName: "taskBulkBar"
    readonly property bool compact: scene.compact
    signal deleteRequested
    implicitHeight: visible ? 48 : 0
    visible: tasksController.advancedCheckedCount > 0
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var enabledFields: Object.keys(tasksController.bulkEditor).filter(key => key.endsWith("Enabled") && tasksController.bulkEditor[key]).map(key => ({
                start: "bid_start_date",
                end: "bid_end_date",
                milestoneCode: "milestone_code"
            })[key.slice(0, -7)] || key.slice(0, -7))
    readonly property var keys: ({
            bid_start_date: "start",
            bid_end_date: "end",
            milestone_code: "milestoneCode"
        })
    scene: BulkUI.bar({
        count: tasksController.advancedCheckedCount,
        canDelete: tasksController.canDeleteCheckedTasks,
        busy: tasksController.bulkBusy,
        blocked: tasksController.advancedDirtyCount > 0 || tasksController.advancedDeleting,
        enabled: enabledFields,
        canApply: tasksController.bulkCanApply,
        invalid: tasksController.bulkPreview.invalid,
        preview: tasksController.advancedDirtyCount > 0 ? qsTr("Save or discard row changes first") : tasksController.bulkPreview.fields === 0 ? "" : tasksController.bulkPreview.eligible + qsTr(" ready") + (tasksController.bulkPreview.unchanged > 0 ? " | " + tasksController.bulkPreview.unchanged + qsTr(" unchanged") : "") + (tasksController.bulkPreview.invalid > 0 ? " | " + tasksController.bulkPreview.invalid + qsTr(" invalid") : "")
    }, width, language)
    views: ({
            status: {
                component: statusPort
            },
            assigned: {
                component: userPort
            }
        })
    onEvent: (action, source) => {
        if (action.type === "enable")
            tasksController.set_bulk_enabled(action.field, action.value);
        else if (action.type === "more-press")
            moreFieldsPopup.rememberSourceOpen();
        else if (action.type === "more")
            moreFieldsPopup.toggleBelowItem(source, true, 6);
        else if (action.type === "apply")
            tasksController.apply_bulk();
        else if (action.type === "delete")
            root.deleteRequested();
        else if (action.type === "cancel")
            tasksController.cancel_bulk();
    }
    Component {
        id: statusPort
        Tasks.TaskBulkField {
            theme: root.theme
            controller: tasksController
            frameNode: ({
                    field: {
                        name: "status"
                    },
                    enabled: root.enabledFields.includes("status") && !tasksController.bulkBusy
                })
        }
    }
    Component {
        id: userPort
        Tasks.TaskBulkField {
            theme: root.theme
            controller: tasksController
            frameNode: ({
                    field: {
                        name: "assigned"
                    },
                    enabled: root.enabledFields.includes("assigned") && !tasksController.bulkBusy
                })
        }
    }
    Controls.ScrollablePopup {
        id: moreFieldsPopup
        objectName: "taskBulkMorePopup"
        parent: Overlay.overlay
        theme: root.theme
        preferredSurfaceWidth: 540
        minimumSurfaceWidth: 240
        maximumSurfaceHeight: 600
        contentSpacing: 8
        Frame.FrameView {
            theme: root.theme
            width: parent.width
            height: scene.height
            readonly property var keys: ({
                    bid_start_date: "start",
                    bid_end_date: "end",
                    milestone_code: "milestoneCode"
                })
            scene: EditorUI.describe({
                fields: (root.compact ? ["status", "assigned"] : []).concat(["bid_start_date", "bid_end_date", "priority", "milestone_code", "supervisor", "progress", "description"]).map(name => ({
                            name,
                            editable: name !== "progress" || tasksController.progressSupported
                        })),
                bulk: true,
                live: true,
                staging: true,
                enabled: Object.keys(tasksController.bulkEditor).filter(key => key.endsWith("Enabled") && tasksController.bulkEditor[key]).map(key => ({
                            start: "bid_start_date",
                            end: "bid_end_date",
                            milestoneCode: "milestone_code"
                        })[key.slice(0, -7)] || key.slice(0, -7)),
                busy: tasksController.bulkBusy,
                readOnly: tasksController.advancedDirtyCount > 0
            }, width, typeof localizationController === "undefined" ? "en" : localizationController.current_language)
            views: ({
                    field: {
                        component: bulkFieldPort,
                        nodeProps: true
                    }
                })
            onEvent: action => {
                if (action.type === "enable")
                    tasksController.set_bulk_enabled(keys[action.field] || action.field, action.value);
                else if (action.type === "cancel")
                    moreFieldsPopup.close();
                else if (action.type === "apply" && tasksController.stage_bulk_changes())
                    moreFieldsPopup.close();
            }
        }
        Label {
            width: parent.width
            text: tasksController.bulkPreview.targets + qsTr(" selected | ") + tasksController.bulkPreview.eligible + qsTr(" eligible | ") + tasksController.bulkPreview.unchanged + qsTr(" unchanged | ") + tasksController.bulkPreview.invalid + qsTr(" invalid | ") + tasksController.bulkPreview.skipped + qsTr(" skipped")
            color: tasksController.bulkPreview.invalid > 0 ? root.theme.error : root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.caption
            wrapMode: Text.Wrap
        }
    }
    Component {
        id: bulkFieldPort
        Tasks.TaskBulkField {
            theme: root.theme
            controller: tasksController
        }
    }
}

import QtQuick
import QtQuick.Controls
import "../../controls" as Controls
import "../.."
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/tasks/table.ui.mjs" as UI
import "../../tactic_frame/features/tasks/cells.ui.mjs" as Fields

Item {
    id: taskRow
    required property var table
    required property var record
    required property var viewport
    required property var controller
    required property var taskModel
    required property var menu
    required property var releaseCoordinator
    required property Component busyAction
    required property Component conflictAction
    required property Component errorAction
    required property Component overflowAction
    property string inlineField: ""
    property var inlineSource: null
    property var inlineRecord: ({})
    readonly property bool hovered: rowHover.hovered
    x: 0
    y: 0
    width: parent.width
    height: UI.metrics.row
    visible: !record.groupCollapsed

    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: function (mouse) {
            if (mouse.button === Qt.RightButton) {
                table.menuTaskCode = record.taskCode;
                table.menuParentKey = record.parentKey;
                table.menuProcess = record.process;
                table.menuDirty = record.dirty;
                table.menuConflict = record.conflict;
                table.menuIsNew = record.isNew;
                menu.openAt(taskRow, mouse.x, mouse.y);
            } else {
                controller.activate_advanced_task(record.taskCode, mouse.modifiers);
            }
        }
        onDoubleClicked: controller.open_object(record.parentKey)
    }
    HoverHandler {
        id: rowHover
    }

    property var lastRowScene: ({
            nodes: []
        })
    Frame.FrameView {
        anchors.fill: parent
        theme: table.theme
        scene: {
            if (record.viewPooled || record.groupCollapsed)
                return taskRow.lastRowScene;
            const next = UI.row({
                code: record.taskCode,
                title: record.parentTitle,
                process: record.process,
                processLabel: record.processLabel,
                context: record.context,
                processColor: record.processColor,
                active: record.selected,
                checked: record.checked,
                creating: record.isNew,
                expanded: record.detailsExpanded,
                hovered: taskRow.hovered,
                dirty: record.dirty,
                actionAlert: record.conflict || record.error.length > 0,
                busy: record.loading,
                start: record.start,
                end: record.end,
                overdue: record.dueState === "overdue",
                progress: record.progress,
                hoursLabel: record.hoursLabel,
                overPlan: record.overPlanHours > 0,
                pendingHours: record.pendingHours > 0,
                notes: record.notes,
                hasTask: !record.isNew,
                editableCells: true
            }, table.tableGeometry, taskRow.language);
            taskRow.lastRowScene = next;
            return next;
        }
        views: ({
                dates: {
                    component: inlineInput,
                    nodeProps: true
                },
                progress: {
                    component: inlineInput,
                    nodeProps: true
                },
                hours: {
                    component: inlineInput,
                    nodeProps: true
                },
                status: {
                    component: field_status
                },
                assignee: {
                    component: field_assignee
                },
                priority: {
                    component: field_priority
                },
                milestone: {
                    component: field_milestone
                },
                supervisor: {
                    component: field_supervisor
                },
                preview: {
                    component: previewPort
                },
                actions: {
                    component: actionPort
                }
            })
        onEvent: action => {
            if (action.type === "expand") {
                controller.activate_advanced_task(record.taskCode, 0);
                table.toggleTaskDetails(record.taskCode);
            } else if (action.type === "select") {
                controller.toggle_advanced_checked(record.taskCode);
            } else if (action.type === "notes") {
                controller.open_notes(record.parentKey, record.process, record.taskCode);
            }
        }
    }
    function closeInline() {
        if (inlinePopup.item)
            inlinePopup.item.close();
        inlinePopup.active = false;
    }
    onVisibleChanged: if (!visible)
        closeInline()
    Connections {
        target: taskRow.viewport
        function onMovementStarted() {
            taskRow.closeInline();
        }
    }
    Connections {
        target: taskRow.record
        ignoreUnknownSignals: true
        function onTaskCodeChanged() {
            taskRow.closeInline();
        }
        function onParentKeyChanged() {
            taskRow.closeInline();
        }
    }
    Component {
        id: inlineInput
        Controls.PopupAction {
            id: inlineButton
            property var frameNode: ({})
            enabled: Fields.fieldEditable(taskRow.record, frameNode.view) && !taskRow.controller.advancedBusy && !taskRow.controller.advancedSaving && (frameNode.view !== "progress" || taskRow.controller.progressSupported)
            Accessible.name: qsTr("Edit %1: %2").arg(frameNode.view === "dates" ? qsTr("Start / Deadline") : frameNode.view === "hours" ? qsTr("Hours") : qsTr("Progress")).arg(taskRow.record.parentTitle)
            background: Item {}
            contentItem: Item {}
            onClicked: {
                taskRow.closeInline();
                taskRow.controller.activate_advanced_task(taskRow.record.taskCode, 0);
                taskRow.inlineRecord = Object.assign({}, taskRow.taskModel.get(taskRow.record.index));
                taskRow.inlineField = frameNode.view;
                taskRow.inlineSource = inlineButton;
                inlinePopup.active = true;
            }
        }
    }
    Loader {
        id: inlinePopup
        objectName: "taskInlineLoader"
        active: false
        onLoaded: if (taskRow.visible && taskRow.inlineSource)
            item.openBelow(taskRow.inlineSource)
        sourceComponent: TaskInlinePopup {
            id: inlineEditor
            theme: taskRow.table.theme
            controller: taskRow.controller
            field: taskRow.inlineField
            record: taskRow.inlineRecord
            onClosed: if (inlinePopup.item === inlineEditor)
                inlinePopup.active = false
        }
    }
    Component {
        id: previewPort
        Controls.ItemPreview {
            anchors.fill: parent
            theme: table.theme
            previewSize: 34
            source: record.parentPreviewUrl
            fallbackIcon: "sobject"
            fallbackText: table.initials(record.parentTitle)
            accent: record.processColor
            round: false
            outlined: false
            animateAppearance: false
            effectsEnabled: !viewport.interactionMoving
        }
    }
    Component {
        id: actionPort
        Loader {
            anchors.fill: parent
            sourceComponent: record.loading ? taskRow.busyAction : record.conflict ? taskRow.conflictAction : record.error.length > 0 ? taskRow.errorAction : taskRow.overflowAction
        }
    }
    Component {
        id: field_status
        TaskTableEditorCell {
            anchors.fill: parent
            theme: table.theme
            releaseCoordinator: taskRow.releaseCoordinator
            editorActive: record.editorsActive
            editingAllowed: Fields.fieldEditable(record, 'status') && !controller.advancedSaving && !controller.advancedBusy
            scrolling: viewport.interactionMoving
            actionField: true
            showAccent: true
            accentColor: record.statusColor
            displayText: record.status ? (record.statusLabel || record.status) : qsTr("No status")
            editorComponent: Component {
                Controls.ComboBox {
                    objectName: "taskStatusEditor"
                    instantHover: true
                    hoverHighlighted: record.editorsActive
                    readonly property var editorRecord: {
                        const revision = record.process + record.status;
                        return taskModel.get(record.index);
                    }
                    theme: table.theme
                    actionField: true
                    model: editorRecord.statusChoices || []
                    textRole: "label"
                    valueRole: "value"
                    colorRole: "color"
                    currentColorFallback: String(record.statusColor || table.theme.action)
                    translateDisplayText: false
                    currentIndex: table.choiceIndex(editorRecord.statusChoices, record.status)
                    displayText: currentIndex >= 0 ? currentText : qsTr("No status")
                    onActivated: controller.stage_advanced_value(record.taskCode, "status", currentValue)
                }
            }
        }
    }

    Component {
        id: field_assignee
        TaskTableEditorCell {
            anchors.fill: parent
            theme: table.theme
            releaseCoordinator: taskRow.releaseCoordinator
            editorActive: record.editorsActive
            editingAllowed: Fields.fieldEditable(record, 'assigned') && !controller.advancedSaving && !controller.advancedBusy
            scrolling: viewport.interactionMoving
            actionField: true
            showAvatar: true
            userModel: userListModel
            avatarLogin: record.assigned
            avatarSource: record.assignedAvatar
            avatarInitials: table.initials(record.assignedLabel)
            displayText: record.assignedLabel
            editorComponent: Component {
                UserComboBox {
                    objectName: "taskAssigneeEditor"
                    instantHover: true
                    hoverHighlighted: record.editorsActive
                    readonly property var editorRecord: {
                        const revision = record.process + record.assigned;
                        return taskModel.get(record.index);
                    }
                    theme: table.theme
                    actionField: true
                    userModel: userListModel
                    model: editorRecord.userChoices || []
                    textRole: "label"
                    valueRole: "value"
                    currentIndex: record.assignedChoiceIndex
                    currentAvatarUrl: record.assignedAvatar
                    currentInitials: table.initials(record.assignedLabel)
                    displayText: currentIndex >= 0 ? currentText : record.assignedLabel
                    onActivated: controller.stage_advanced_value(record.taskCode, "assigned", currentValue)
                }
            }
        }
    }

    Component {
        id: field_priority
        TaskTableEditorCell {
            anchors.fill: parent
            theme: table.theme
            releaseCoordinator: taskRow.releaseCoordinator
            editingAllowed: Fields.fieldEditable(record, 'priority') && !controller.advancedSaving && !controller.advancedBusy
            editorActive: record.editorsActive
            scrolling: viewport.interactionMoving
            actionField: false
            showIndicator: true
            showAccent: true
            accentColor: record.priorityColor || table.theme.action
            displayText: record.priority ? record.priorityLabel : qsTr("No priority")
            editorComponent: Component {
                Controls.ComboBox {
                    objectName: "taskPriorityEditor"
                    instantHover: true
                    hoverHighlighted: record.editorsActive
                    readonly property var editorRecord: {
                        const revision = record.priority;
                        return taskModel.get(record.index);
                    }
                    theme: table.theme
                    actionField: false
                    showIndicator: true
                    model: editorRecord.priorityChoices && editorRecord.priorityChoices.length > 1 ? editorRecord.priorityChoices : controller.taskPriorityChoices
                    textRole: "label"
                    valueRole: "value"
                    colorRole: "color"
                    currentColorFallback: String(record.priorityColor || table.theme.action)
                    currentIndex: table.choiceIndex(model, record.priority)
                    displayText: currentIndex >= 0 && String(currentText).length > 0 ? currentText : record.priorityLabel || qsTr("No priority")
                    onActivated: controller.stage_advanced_value(record.taskCode, "priority", currentValue)
                }
            }
        }
    }

    Component {
        id: field_milestone
        TaskTableEditorCell {
            anchors.fill: parent
            theme: table.theme
            releaseCoordinator: taskRow.releaseCoordinator
            editingAllowed: Fields.fieldEditable(record, 'milestone') && !controller.advancedSaving && !controller.advancedBusy
            editorActive: record.editorsActive
            scrolling: viewport.interactionMoving
            actionField: true
            displayText: record.milestoneCode ? record.milestoneLabel : qsTr("No milestone")
            editorComponent: Component {
                Controls.ComboBox {
                    objectName: "taskMilestoneEditor"
                    instantHover: true
                    hoverHighlighted: record.editorsActive
                    readonly property var editorRecord: {
                        const revision = record.milestoneCode;
                        return taskModel.get(record.index);
                    }
                    theme: table.theme
                    actionField: true
                    model: editorRecord.milestoneChoices || []
                    textRole: "label"
                    valueRole: "value"
                    currentIndex: table.choiceIndex(editorRecord.milestoneChoices, record.milestoneCode)
                    displayText: currentIndex >= 0 ? currentText : record.milestoneLabel
                    onActivated: controller.stage_advanced_value(record.taskCode, "milestoneCode", currentValue)
                }
            }
        }
    }

    Component {
        id: field_supervisor
        TaskTableEditorCell {
            anchors.fill: parent
            theme: table.theme
            releaseCoordinator: taskRow.releaseCoordinator
            editingAllowed: Fields.fieldEditable(record, 'supervisor') && !controller.advancedSaving && !controller.advancedBusy
            editorActive: record.editorsActive
            scrolling: viewport.interactionMoving
            actionField: true
            showAvatar: true
            userModel: userListModel
            avatarLogin: record.supervisor
            avatarSource: record.supervisorAvatar
            avatarInitials: table.initials(record.supervisorLabel)
            displayText: record.supervisorLabel
            editorComponent: Component {
                UserComboBox {
                    objectName: "taskSupervisorEditor"
                    instantHover: true
                    hoverHighlighted: record.editorsActive
                    readonly property var editorRecord: {
                        const revision = record.process + record.supervisor;
                        return taskModel.get(record.index);
                    }
                    theme: table.theme
                    actionField: true
                    userModel: userListModel
                    model: editorRecord.supervisorChoices || []
                    textRole: "label"
                    valueRole: "value"
                    currentIndex: table.choiceIndex(editorRecord.supervisorChoices, record.supervisor)
                    currentAvatarUrl: record.supervisorAvatar
                    currentInitials: table.initials(record.supervisorLabel)
                    displayText: currentIndex >= 0 ? currentText : record.supervisorLabel
                    onActivated: controller.stage_advanced_value(record.taskCode, "supervisor", currentValue)
                }
            }
        }
    }
}

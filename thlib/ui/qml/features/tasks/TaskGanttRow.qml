import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../.."
import "../../controls" as Controls
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/tasks/gantt.ui.mjs" as UI
import "../../tactic_frame/features/tasks/gantt.state.mjs" as State

Column {
    id: taskRow
    required property var host
    required property var controller
    property var gesture: null

    required property int index
    required property string taskCode
    required property string parentKey
    required property string parentTitle
    required property string parentPreviewUrl
    required property string process
    required property string processLabel
    required property string processColor
    required property string status
    required property string statusColor
    required property string assignedLabel
    required property string start
    required property string end
    required property int progress
    required property string group
    required property string groupKey
    required property int groupCount
    required property bool groupFirst
    required property bool groupCollapsed
    required property string groupColor
    required property bool selected
    required property bool checked
    required property bool ganttScheduled
    required property int ganttStartDay
    required property int ganttDurationDays
    required property string ganttIssue
    required property string ganttColor
    required property string ganttSection
    required property bool ganttSectionFirst
    required property string ganttWarning
    required property int ganttGroupStartDay
    required property int ganttGroupDurationDays
    required property int ganttGroupProgress

    property bool editingSchedule: false
    property string scheduleEditMode: ""
    property int editStartDay: ganttStartDay
    property int editDurationDays: Math.max(1, ganttDurationDays)
    property int originalStartDay: ganttStartDay
    property int originalDurationDays: Math.max(1, ganttDurationDays)
    property real pressContentX: 0
    property real lastPointerX: 0
    property real panPressX: 0
    property real panContentX: 0
    property bool panMoved: false
    property int panButton: Qt.NoButton
    property int panModifiers: Qt.NoModifier
    readonly property real scheduleViewportWidth: timelineRow.width

    ListView.onPooled: {
        host.stopScheduleAutoScroll(taskRow);
        if (host.activeGestureRow === taskRow)
            host.cancelGesture();
    }

    function updateSchedule(pointerX) {
        lastPointerX = pointerX;
        if (!gesture)
            return;
        gesture = State.pointer(gesture, pointerX + host.timeline.contentX, host.dayWidth);
        editStartDay = gesture.start;
        editDurationDays = gesture.duration;
    }

    function record() {
        return {
            taskCode,
            parentKey,
            parentTitle,
            parentPreviewUrl,
            processLabel,
            processColor,
            assignedLabel,
            group,
            groupKey,
            groupCount,
            groupColor,
            ganttSection,
            ganttWarning,
            ganttIssue,
            ganttColor,
            progress,
            start,
            end,
            checked,
            selected,
            busy: controller.advancedBusy,
            hovered: rowHover.hovered,
            ganttStartDay,
            ganttDurationDays,
            ganttGroupStartDay,
            ganttGroupDurationDays,
            ganttGroupProgress
        };
    }
    function finishScheduleEdit() {
        if (!editingSchedule)
            return;
        const changed = State.changed(gesture);
        const moved = State.moved(gesture);
        const issue = gesture.fromIssue;
        const completedMode = scheduleEditMode;
        host.activeGestureRow = null;
        editingSchedule = false;
        scheduleEditMode = "";
        host.stopScheduleAutoScroll(taskRow);
        if (changed)
            controller.stage_gantt_schedule(taskCode, editStartDay, editDurationDays, completedMode);
        else if (issue && !moved)
            host.openSchedule(taskRow.record());
        else if (!moved)
            controller.activate_advanced_task(taskCode, 0);
        gesture = null;
    }

    width: host.taskList.width
    spacing: 0

    Rectangle {
        width: parent.width
        height: taskRow.ganttSectionFirst ? State.metrics.section : 0
        visible: taskRow.ganttSectionFirst
        color: "transparent"
        Frame.FrameView {
            theme: host.theme
            anchors.fill: parent
            interactive: false
            scene: UI.band("section", host.labelWidth + host.timelineContentWidth)
        }

        Frame.FrameView {
            theme: host.theme
            anchors.fill: parent
            scene: UI.section(taskRow.record(), host.labelWidth, host.language)
        }
    }

    Rectangle {
        width: parent.width
        height: taskRow.groupFirst ? State.metrics.group : 0
        visible: taskRow.groupFirst
        color: "transparent"
        Frame.FrameView {
            theme: host.theme
            anchors.fill: parent
            scene: UI.band("group", host.labelWidth + host.timelineContentWidth, taskRow.record(), taskRow.groupCollapsed)
            onEvent: action => controller.toggle_group_collapsed(action.value)
        }

        Frame.FrameView {
            theme: host.theme
            width: host.labelWidth
            height: State.metrics.group
            interactive: false
            scene: UI.group(taskRow.record(), width, taskRow.groupCollapsed)
        }
        Frame.FrameView {
            theme: host.theme
            x: host.labelWidth
            width: host.timelineViewportWidth
            height: State.metrics.group
            interactive: false
            scene: UI.groupTimeline(taskRow.record(), host.dayWidth, taskRow.groupCollapsed, host.timeline.contentX)
        }
    }

    Item {
        id: rowContent
        width: parent.width
        height: taskRow.groupCollapsed ? 0 : State.metrics.row
        visible: !taskRow.groupCollapsed

        Frame.FrameView {
            theme: host.theme
            anchors.fill: parent
            interactive: false
            scene: UI.rowSurface(taskRow.record(), host.labelWidth + host.timelineContentWidth)
        }

        Frame.FrameView {
            theme: host.theme
            width: host.labelWidth
            height: State.metrics.row
            scene: UI.taskLabel(taskRow.record(), width, host.language)
            onEvent: action => {
                if (action.type === "select")
                    controller.toggle_advanced_checked(taskRow.taskCode);
                else if (action.type === "object")
                    controller.open_object(taskRow.parentKey);
                else if (action.type === "edit")
                    host.openSchedule(taskRow.record());
                else
                    controller.activate_advanced_task(taskRow.taskCode, 0);
            }
        }

        Item {
            id: timelineRow
            anchors.left: parent.left
            anchors.leftMargin: host.labelWidth
            anchors.right: parent.right
            anchors.rightMargin: host.gutter
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            clip: true

            Item {
                id: scheduleBar
                z: 2
                visible: taskRow.ganttScheduled || taskRow.editingSchedule
                readonly property var bounds: State.bar(taskRow.editingSchedule ? taskRow.editStartDay : taskRow.ganttStartDay, taskRow.editingSchedule ? taskRow.editDurationDays : taskRow.ganttDurationDays, host.dayWidth, host.timeline.contentX)
                x: bounds.x
                y: bounds.y
                width: bounds.width
                height: bounds.height

                HoverHandler {
                    id: scheduleHover
                }

                Rectangle {
                    id: startDateChip
                    visible: scheduleHover.hovered && !taskRow.editingSchedule
                    z: 8
                    x: 0
                    y: -10
                    height: 17
                    width: startDateText.implicitWidth + 12
                    radius: height / 2
                    color: host.theme.surfaceContainerHighest
                    border.width: 1
                    border.color: host.theme.outlineVariant
                    Label {
                        id: startDateText
                        anchors.centerIn: parent
                        text: scheduleBar.width < 110 ? host.shortDate(taskRow.start) + "  \u00b7  " + host.shortDate(taskRow.end) : host.shortDate(taskRow.start)
                        color: host.theme.primaryText
                        font.family: host.theme.fontFamily
                        font.pointSize: Controls.Typography.micro
                        font.weight: Font.DemiBold
                    }
                }
                Rectangle {
                    visible: scheduleHover.hovered && !taskRow.editingSchedule && scheduleBar.width >= 110
                    z: 8
                    x: Math.max(0, scheduleBar.width - width)
                    y: -10
                    height: 17
                    width: endDateText.implicitWidth + 12
                    radius: height / 2
                    color: host.theme.surfaceContainerHighest
                    border.width: 1
                    border.color: host.theme.outlineVariant
                    Label {
                        id: endDateText
                        anchors.centerIn: parent
                        text: host.shortDate(taskRow.end)
                        color: host.theme.primaryText
                        font.family: host.theme.fontFamily
                        font.pointSize: Controls.Typography.micro
                        font.weight: Font.DemiBold
                    }
                }

                Frame.FrameView {
                    theme: host.theme
                    anchors.fill: parent
                    interactive: false
                    scene: UI.scheduleBar(Object.assign(taskRow.record(), {
                        radius: host.theme.itemRadius,
                        progress: progressHandle.displayProgress,
                        progressSupported: controller.progressSupported,
                        editing: taskRow.editingSchedule,
                        startLabel: host.dateForDay(taskRow.editStartDay),
                        endLabel: host.dateForDay(taskRow.editStartDay + taskRow.editDurationDays - 1)
                    }), width, host.language)
                }
                TaskGanttProgressHandle {
                    id: progressHandle
                    z: 5
                    theme: host.theme
                    controller: tasksController
                    taskCode: taskRow.taskCode
                    progress: taskRow.progress
                    barWidth: scheduleBar.width
                    rowHovered: rowHover.hovered
                    scheduled: taskRow.ganttScheduled
                    progressSupported: controller.progressSupported
                }
                Controls.ToolTip {
                    theme: host.theme
                    visible: scheduleHover.hovered && !taskRow.editingSchedule
                    text: taskRow.parentTitle + " · " + taskRow.processLabel + "\n" + taskRow.status + " · " + taskRow.assignedLabel + "\n" + host.compactDate(taskRow.start) + " — " + host.compactDate(taskRow.end) + " · " + taskRow.progress + "%" + (taskRow.ganttWarning ? "\n" + host.ganttMessages(taskRow.ganttWarning) : "")
                }
            }

            Frame.FrameView {
                id: unscheduledChip
                objectName: "ganttUnscheduledIssueChip"
                theme: host.theme
                visible: !taskRow.ganttScheduled && !taskRow.editingSchedule
                x: 10
                y: 10
                width: scene.width
                height: 30
                interactive: false
                scene: UI.issue(Object.assign(taskRow.record(), {
                    radius: host.theme.itemRadius
                }), host.timelineViewportWidth, host.language)
            }

            MouseArea {
                id: timelinePointer
                z: 1
                anchors.fill: parent
                hoverEnabled: true
                preventStealing: taskRow.editingSchedule
                acceptedButtons: Qt.LeftButton | Qt.MiddleButton
                cursorShape: {
                    if (taskRow.editingSchedule)
                        return Qt.ClosedHandCursor;
                    const start = taskRow.ganttStartDay * host.dayWidth - host.timeline.contentX;
                    const width = Math.max(7, taskRow.ganttDurationDays * host.dayWidth - 4);
                    if (taskRow.ganttScheduled && mouseX >= start - 12 && mouseX <= start + width + 12) {
                        if (Math.abs(mouseX - start) <= 12 || Math.abs(mouseX - start - width) <= 12)
                            return Qt.SizeHorCursor;
                        return Qt.OpenHandCursor;
                    }
                    if (!taskRow.ganttScheduled && mouseX >= 10 && mouseX <= 10 + unscheduledChip.width)
                        return Qt.OpenHandCursor;
                    return Qt.OpenHandCursor;
                }

                onPressed: function (mouse) {
                    host.wheelAnimation.stop();
                    if (mouse.button === Qt.MiddleButton) {
                        taskRow.scheduleEditMode = "pan";
                        taskRow.panPressX = mouse.x;
                        taskRow.panContentX = host.timeline.contentX;
                        taskRow.panMoved = false;
                        taskRow.panButton = mouse.button;
                        taskRow.panModifiers = mouse.modifiers;
                        return;
                    }
                    const start = taskRow.ganttStartDay * host.dayWidth - host.timeline.contentX;
                    const width = Math.max(7, taskRow.ganttDurationDays * host.dayWidth - 4);
                    let mode = "";
                    if (taskRow.ganttScheduled && mouse.x >= start - 12 && mouse.x <= start + width + 12) {
                        if (Math.abs(mouse.x - start) <= 12)
                            mode = "resize-start";
                        else if (Math.abs(mouse.x - start - width) <= 12)
                            mode = "resize-end";
                        else
                            mode = "move";
                    } else if (!taskRow.ganttScheduled && mouse.x >= 10 && mouse.x <= 10 + unscheduledChip.width) {
                        mode = "create";
                    }
                    if (!mode) {
                        taskRow.scheduleEditMode = "pan";
                        taskRow.panPressX = mouse.x;
                        taskRow.panContentX = host.timeline.contentX;
                        taskRow.panMoved = false;
                        taskRow.panButton = mouse.button;
                        taskRow.panModifiers = mouse.modifiers;
                        return;
                    }
                    taskRow.scheduleEditMode = mode;
                    host.activeGestureRow = taskRow;
                    taskRow.gesture = State.begin(taskRow.record(), mode, mouse.x + host.timeline.contentX, host.dayWidth, mode === "create");
                    taskRow.editingSchedule = true;
                    taskRow.originalStartDay = taskRow.ganttStartDay;
                    taskRow.originalDurationDays = Math.max(1, taskRow.ganttDurationDays);
                    taskRow.editStartDay = taskRow.ganttStartDay;
                    taskRow.editDurationDays = taskRow.originalDurationDays;
                    taskRow.pressContentX = mouse.x + host.timeline.contentX;
                    taskRow.lastPointerX = mouse.x;
                    if (mode === "create")
                        taskRow.updateSchedule(mouse.x);
                }
                onPositionChanged: function (mouse) {
                    if (taskRow.scheduleEditMode === "pan") {
                        if (Math.abs(mouse.x - taskRow.panPressX) > State.metrics.dragThreshold)
                            taskRow.panMoved = true;
                        const maximum = Math.max(0, host.timeline.contentWidth - host.timeline.width);
                        host.timeline.contentX = Math.max(0, Math.min(maximum, taskRow.panContentX - mouse.x + taskRow.panPressX));
                        host.timelineWheelTarget = host.timeline.contentX;
                        return;
                    }
                    if (!taskRow.editingSchedule)
                        return;
                    taskRow.updateSchedule(mouse.x);
                    if (mouse.x < 28 || mouse.x > width - 28)
                        host.startScheduleAutoScroll(taskRow);
                    else
                        host.stopScheduleAutoScroll(taskRow);
                }
                onReleased: {
                    if (taskRow.scheduleEditMode === "pan") {
                        const moved = taskRow.panMoved;
                        const button = taskRow.panButton;
                        const modifiers = taskRow.panModifiers;
                        taskRow.scheduleEditMode = "";
                        taskRow.panMoved = false;
                        taskRow.panButton = Qt.NoButton;
                        taskRow.panModifiers = Qt.NoModifier;
                        if (!moved && button === Qt.LeftButton)
                            controller.activate_advanced_task(taskRow.taskCode, modifiers);
                        return;
                    }
                    taskRow.finishScheduleEdit();
                }
                onCanceled: {
                    if (host.activeGestureRow === taskRow)
                        host.activeGestureRow = null;
                    host.stopScheduleAutoScroll(taskRow);
                    taskRow.editingSchedule = false;
                    taskRow.scheduleEditMode = "";
                    taskRow.panMoved = false;
                    taskRow.panButton = Qt.NoButton;
                    taskRow.panModifiers = Qt.NoModifier;
                }
                onDoubleClicked: {
                    if (!taskRow.editingSchedule)
                        controller.open_object(taskRow.parentKey);
                }
            }
        }

        HoverHandler {
            id: rowHover
        }
        MouseArea {
            anchors.fill: parent
            z: -1
            acceptedButtons: Qt.LeftButton
            cursorShape: Qt.PointingHandCursor
            onClicked: function (mouse) {
                controller.activate_advanced_task(taskRow.taskCode, mouse.modifiers);
            }
            onDoubleClicked: controller.open_object(taskRow.parentKey)
        }
    }
}

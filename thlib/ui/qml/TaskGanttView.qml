import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls
import "tactic_frame" as Frame
import "features/tasks" as Tasks
import "tactic_frame/features/tasks/gantt.ui.mjs" as UI
import "tactic_frame/features/tasks/gantt.state.mjs" as State

Item {
    id: root

    required property var theme
    signal deleteTasksRequested
    property real footerHorizontalOverflow: 0
    readonly property var range: tasksController.ganttRange
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var geometry: State.layout(width, height, range.days || 1, zoomLevel, gutter)
    readonly property real gutter: ganttList.contentHeight > ganttList.height + 0.5 ? 12 : 0
    readonly property int dayCount: Math.max(1, Number(range.days || 1))
    readonly property real labelWidth: geometry.labels
    readonly property real timelineViewportWidth: geometry.viewport
    property real zoomLevel: 1
    property string scaleMode: "auto"
    property var scheduleAutoScrollRow: null
    readonly property real baseDayWidth: geometry.baseDay
    readonly property real dayWidth: geometry.day
    readonly property real timelineContentWidth: geometry.timeline
    readonly property bool showDayGrid: dayWidth >= 16
    property int modelRevision: 0
    readonly property var records: {
        const version = modelRevision;
        const rows = [];
        for (let index = 0; index < taskGanttModel.count(); index++)
            rows.push(taskGanttModel.get(index));
        return rows;
    }
    Connections {
        target: taskGanttModel
        function onContentReplaced() {
            root.modelRevision++;
        }
        function onDataChanged() {
            root.modelRevision++;
        }
    }
    readonly property var projection: Object.assign({}, range, {
        tickSets: tasksController.ganttTickSets,
        weekends: tasksController.ganttWeekendSpans,
        milestones: tasksController.ganttMilestones,
        overview: tasksController.ganttOverview,
        scheduled: tasksController.ganttScheduledCount,
        unscheduled: tasksController.ganttUnscheduledCount
    })
    readonly property var displayTicks: State.ticks(projection, dayWidth, timelineHeader.contentX, timelineHeader.width)
    property var activeGestureRow: null
    property alias timeline: timelineHeader
    property alias taskList: ganttList
    property alias wheelAnimation: timelineWheelAnimation

    function cancelGesture() {
        const row = activeGestureRow;
        if (!row)
            return;
        row.editingSchedule = false;
        row.scheduleEditMode = "";
        row.gesture = null;
        stopScheduleAutoScroll(row);
        activeGestureRow = null;
    }
    Shortcut {
        sequence: "Escape"
        enabled: root.activeGestureRow !== null
        onActivated: root.cancelGesture()
    }

    function openSchedule(record) {
        scheduleEditor.showRecord(record);
    }
    Tasks.TaskScheduleDialog {
        id: scheduleEditor
        theme: root.theme
        controller: tasksController
        anchors.centerIn: parent
    }

    function compactDate(value) {
        const text = String(value || "");
        return text.length >= 10 ? text.slice(0, 10) : text || "-";
    }

    function ganttMessage(value) {
        const text = String(value || "");
        if (text === "Start and deadline are not set")
            return qsTr("Start and deadline are not set");
        if (text === "Start is not set")
            return qsTr("Start is not set");
        if (text === "Deadline is not set")
            return qsTr("Deadline is not set");
        if (text === "Deadline precedes start")
            return qsTr("Deadline precedes start");
        if (text === "Task is overdue")
            return qsTr("Task is overdue");
        if (text === "Task has no assignee")
            return qsTr("Task has no assignee");
        if (text === "Deadline falls on a weekend")
            return qsTr("Deadline falls on a weekend");
        if (text === "Assignee has overlapping tasks")
            return qsTr("Assignee has overlapping tasks");
        return text;
    }

    function ganttMessages(value) {
        return String(value || "").split("\n").map(function (part) {
            return root.ganttMessage(part);
        }).join("\n");
    }

    function shortDate(value) {
        const text = String(value || "").slice(0, 10);
        if (!text)
            return "-";
        const dateValue = new Date(text + "T00:00:00");
        if (isNaN(dateValue.getTime()))
            return text;
        return Qt.locale().toString(dateValue, "MMM d");
    }

    function dateForDay(offset) {
        return State.dateForDay(range.rangeStart, offset);
    }
    function setZoom(value, anchorX) {
        const next = State.zoomAt(geometry, timelineHeader.contentX, value, anchorX);
        zoomLevel = next.zoom;
        timelineWheelAnimation.stop();
        timelineHeader.contentX = State.clamp(next.x, 0, Math.max(0, timelineContentWidth - timelineHeader.width));
        timelineWheelTarget = timelineHeader.contentX;
    }
    function zoomBy(factor, anchorX) {
        scaleMode = "custom";
        setZoom(zoomLevel * factor, anchorX);
    }
    function setScaleMode(mode) {
        scaleMode = mode;
        setZoom(State.scaleZoom(mode, baseDayWidth), timelineHeader.width / 2);
    }
    function setOverviewPosition(position, pointerOffset) {
        timelineWheelAnimation.stop();
        timelineHeader.contentX = State.overviewPosition(position, timelineHeader.width, timelineContentWidth, pointerOffset);
        timelineWheelTarget = timelineHeader.contentX;
    }

    function revealToday() {
        const today = Number(range.todayDay);
        if (today < 0)
            return;
        timelineHeader.contentX = Math.max(0, Math.min(timelineHeader.contentWidth - timelineHeader.width, today * root.dayWidth - timelineHeader.width * 0.42));
    }

    function scrollTimeline(pixelDelta, angleDelta) {
        const delta = pixelDelta !== 0 ? pixelDelta * 1.65 : (angleDelta / 120) * 150;
        if (delta === 0)
            return;
        const maximum = Math.max(0, timelineHeader.contentWidth - timelineHeader.width);
        const base = timelineWheelAnimation.running ? timelineWheelTarget : timelineHeader.contentX;
        timelineWheelTarget = Math.max(0, Math.min(maximum, base - delta));
        timelineWheelAnimation.stop();
        timelineWheelAnimation.to = timelineWheelTarget;
        timelineWheelAnimation.start();
    }

    function startScheduleAutoScroll(taskRow) {
        scheduleAutoScrollRow = taskRow;
        scheduleAutoScroll.start();
    }

    function stopScheduleAutoScroll(taskRow) {
        if (taskRow && scheduleAutoScrollRow !== taskRow)
            return;
        scheduleAutoScroll.stop();
        scheduleAutoScrollRow = null;
    }

    Timer {
        id: scheduleAutoScroll
        interval: State.metrics.autoScrollInterval
        repeat: true
        onTriggered: {
            const taskRow = root.scheduleAutoScrollRow;
            if (!taskRow || !taskRow.editingSchedule) {
                root.stopScheduleAutoScroll(taskRow);
                return;
            }
            const maximum = Math.max(0, timelineHeader.contentWidth - timelineHeader.width);
            const next = State.autoScroll(taskRow.lastPointerX, taskRow.scheduleViewportWidth, timelineHeader.contentX, maximum);
            if (next === timelineHeader.contentX)
                return;
            timelineWheelAnimation.stop();
            timelineHeader.contentX = next;
            root.timelineWheelTarget = next;
            taskRow.updateSchedule(taskRow.lastPointerX);
        }
    }

    property real timelineWheelTarget: 0

    Shortcut {
        sequences: [StandardKey.Undo]
        enabled: root.visible && tasksController.ganttCanUndo
        onActivated: tasksController.undo_gantt_change()
    }
    Shortcut {
        sequences: [StandardKey.Redo]
        enabled: root.visible && tasksController.ganttCanRedo
        onActivated: tasksController.redo_gantt_change()
    }

    NumberAnimation {
        id: timelineWheelAnimation
        target: timelineHeader
        property: "contentX"
        duration: root.theme.motionMedium
        easing.type: Easing.OutCubic
    }

    Rectangle {
        anchors.fill: parent
        radius: root.theme.surfaceRadius
        color: root.theme.workspace
    }

    Rectangle {
        id: header
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: State.metrics.heading
        radius: root.theme.itemRadius
        color: root.theme.surfaceContainer

        Frame.FrameView {
            theme: root.theme
            width: root.labelWidth
            height: State.metrics.heading
            scene: UI.heading(root.projection, width, root.language)
        }

        Flickable {
            id: timelineHeader
            // ui-scrollbar: external-horizontal overviewTimeline
            anchors.left: parent.left
            anchors.leftMargin: root.labelWidth
            anchors.right: parent.right
            anchors.rightMargin: root.gutter
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            contentWidth: root.timelineContentWidth
            contentHeight: height
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            flickableDirection: Flickable.HorizontalFlick

            Frame.FrameView {
                theme: root.theme
                x: timelineHeader.contentX
                width: timelineHeader.width
                height: State.metrics.heading
                scene: UI.timelineHeading(root.projection, root.dayWidth, timelineHeader.contentX, width, root.language)
                onEvent: action => milestoneController.open_manager()
            }

            WheelHandler {
                target: null
                blocking: true
                onWheel: function (event) {
                    if (event.modifiers & Qt.ShiftModifier) {
                        root.scrollTimeline(event.pixelDelta.y || event.pixelDelta.x, event.angleDelta.y || event.angleDelta.x);
                    } else {
                        const steps = event.angleDelta.y ? event.angleDelta.y / 120 : event.pixelDelta.y / 80;
                        root.zoomBy(Math.pow(1.16, steps), event.position.x);
                    }
                    event.accepted = true;
                }
            }

            onFlickStarted: {
                timelineWheelAnimation.stop();
                root.timelineWheelTarget = contentX;
            }
        }
    }

    Item {
        id: body
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: header.bottom
        anchors.bottom: overview.top
        anchors.topMargin: State.metrics.headingGap
        clip: true

        Item {
            id: timelineGrid
            anchors.left: parent.left
            anchors.leftMargin: root.labelWidth
            anchors.right: parent.right
            anchors.rightMargin: root.gutter
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            clip: true

            Frame.FrameView {
                objectName: "ganttDailyGrid"
                theme: root.theme
                anchors.fill: parent
                interactive: false
                scene: UI.grid(root.projection, root.dayWidth, timelineHeader.contentX, width, height)
            }
        }

        Frame.FrameView {
            z: 2
            theme: root.theme
            x: root.labelWidth
            width: root.timelineViewportWidth
            height: parent.height
            clip: true
            interactive: false
            scene: UI.dependencies(root.records, root.records.filter(row => row.groupCollapsed).map(row => row.groupKey), root.dayWidth, timelineHeader.contentX, ganttList.contentY)
        }

        Controls.SmoothListView {
            id: ganttList
            theme: root.theme
            objectName: "ganttTaskList"
            anchors.fill: parent
            clip: true
            spacing: 0
            model: taskGanttModel
            reuseItems: true

            delegate: Tasks.TaskGanttRow {
                host: root
                controller: tasksController
            }

            footer: Item {
                width: ganttList.width
                height: tasksController.advancedHasMore ? 42 : 8
                Controls.Button {
                    anchors.centerIn: parent
                    visible: tasksController.advancedHasMore
                    enabled: !tasksController.advancedBusy
                    theme: root.theme
                    text: tasksController.advancedBusy ? qsTr("LOADING") : qsTr("LOAD MORE")
                    onClicked: tasksController.load_more_advanced()
                }
            }

            ScrollBar.vertical: Controls.ScrollBar {
                theme: root.theme
                flickableTarget: ganttList
            }
        }

        MouseArea {
            id: timelineWheelArea
            objectName: "ganttTimelineWheelArea"
            z: 20
            anchors.left: parent.left
            anchors.leftMargin: root.labelWidth
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            acceptedButtons: Qt.NoButton

            MouseArea {
                id: emptyTimelinePanArea
                objectName: "ganttEmptyTimelinePanArea"
                property real pressX: 0
                property real pressContentX: 0

                x: 0
                y: Math.max(0, Math.min(parent.height, ganttList.contentHeight - ganttList.contentY))
                width: parent.width
                height: Math.max(0, parent.height - y)
                acceptedButtons: Qt.LeftButton | Qt.MiddleButton
                cursorShape: pressed ? Qt.ClosedHandCursor : Qt.OpenHandCursor
                preventStealing: true

                onPressed: function (mouse) {
                    timelineWheelAnimation.stop();
                    pressX = mouse.x;
                    pressContentX = timelineHeader.contentX;
                }
                onPositionChanged: function (mouse) {
                    if (!pressed)
                        return;
                    const maximum = Math.max(0, timelineHeader.contentWidth - timelineHeader.width);
                    timelineHeader.contentX = Math.max(0, Math.min(maximum, pressContentX - mouse.x + pressX));
                    root.timelineWheelTarget = timelineHeader.contentX;
                }
                onReleased: root.timelineWheelTarget = timelineHeader.contentX
                onCanceled: root.timelineWheelTarget = timelineHeader.contentX
            }

            onWheel: function (wheel) {
                if (wheel.modifiers & Qt.ShiftModifier) {
                    root.scrollTimeline(wheel.pixelDelta.y || wheel.pixelDelta.x, wheel.angleDelta.y || wheel.angleDelta.x);
                } else {
                    const steps = wheel.angleDelta.y ? wheel.angleDelta.y / 120 : wheel.pixelDelta.y / 80;
                    if (steps !== 0)
                        root.zoomBy(Math.pow(1.16, steps), wheel.x);
                }
                wheel.accepted = true;
            }
        }
    }

    Item {
        id: overview
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: footer.top
        height: State.metrics.overview
        Frame.FrameView {
            theme: root.theme
            anchors.fill: parent
            interactive: false
            scene: UI.overview(Object.assign({}, root.projection, {
                warnings: tasksController.ganttWarningCount
            }), root.labelWidth, width - root.gutter, root.timelineContentWidth, timelineHeader.contentX, root.language)
        }
        MouseArea {
            id: overviewTimeline
            x: root.labelWidth
            width: root.timelineViewportWidth
            height: parent.height
            property real thumbOffset: 0
            activeFocusOnTab: true
            Keys.onLeftPressed: timelineHeader.contentX = Math.max(0, timelineHeader.contentX - 100)
            Keys.onRightPressed: timelineHeader.contentX = Math.min(root.timelineContentWidth - width, timelineHeader.contentX + 100)
            cursorShape: pressed ? Qt.ClosedHandCursor : Qt.OpenHandCursor
            onPressed: mouse => {
                const thumb = UI.overviewGeometry(width, root.timelineContentWidth, timelineHeader.contentX);
                thumbOffset = mouse.x >= thumb.x && mouse.x <= thumb.x + thumb.width ? mouse.x - thumb.x : thumb.width / 2;
                root.setOverviewPosition(mouse.x, thumbOffset);
            }
            onPositionChanged: mouse => {
                if (pressed)
                    root.setOverviewPosition(mouse.x, thumbOffset);
            }
        }
    }

    Controls.Popup {
        id: batchPopup
        theme: root.theme
        width: 284
        height: optionsFrame.scene.height + 16
        contentItem: Frame.FrameView {
            id: optionsFrame
            theme: root.theme
            scene: UI.options({
                workingDays: tasksController.ganttWorkingDays,
                resourceMode: tasksController.ganttResourceMode,
                scale: root.scaleMode,
                busy: tasksController.advancedBusy,
                checked: tasksController.advancedCheckedCount,
                dirty: tasksController.advancedDirtyCount > 0
            }, 268, root.language)
            onEvent: action => {
                if (action.type === "working")
                    tasksController.set_gantt_working_days(action.value);
                else if (action.type === "resource")
                    tasksController.set_gantt_resource_mode(action.value);
                else if (action.type === "scale-value")
                    root.setScaleMode(action.value);
                else if (action.type === "batch") {
                    tasksController.apply_gantt_batch(action.operation, action.amount);
                    batchPopup.close();
                } else if (action.type === "delete") {
                    batchPopup.close();
                    root.deleteTasksRequested();
                }
            }
        }
    }
    Controls.Popup {
        id: scalePopup
        theme: root.theme
        width: 170
        height: 186
        contentItem: Frame.FrameView {
            theme: root.theme
            scene: UI.scaleOptions(root.scaleMode, 154, root.language)
            onEvent: action => {
                root.setScaleMode(action.value);
                scalePopup.close();
            }
        }
    }

    Controls.DockWorkspaceFooter {
        id: footer
        theme: root.theme
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.leftMargin: -root.footerHorizontalOverflow
        anchors.rightMargin: -root.footerHorizontalOverflow

        Frame.FrameView {
            theme: root.theme
            anchors.fill: parent
            scene: UI.footer(Object.assign({}, root.range, {
                zoom: root.zoomLevel,
                busy: tasksController.advancedBusy,
                workingDays: tasksController.ganttWorkingDays,
                resourceMode: tasksController.ganttResourceMode,
                canUndo: tasksController.ganttCanUndo,
                canRedo: tasksController.ganttCanRedo,
                minZoom: 2 / root.baseDayWidth,
                hostWidth: root.width >= 380 ? 112 : 0
            }), width, root.language)
            onEvent: (action, source) => {
                if (action.type === "today")
                    root.revealToday();
                else if (action.type === "zoom-in")
                    root.zoomBy(1.25, timelineHeader.width / 2);
                else if (action.type === "zoom-out")
                    root.zoomBy(1 / 1.25, timelineHeader.width / 2);
                else if (action.type === "scale")
                    scalePopup.toggleBelowItem(source, true, 6);
                else if (action.type === "options")
                    batchPopup.toggleBelowItem(source, true, 6);
                else if (action.type === "working")
                    tasksController.set_gantt_working_days(!tasksController.ganttWorkingDays);
                else if (action.type === "resource")
                    tasksController.set_gantt_resource_mode(!tasksController.ganttResourceMode);
                else if (action.type === "undo")
                    tasksController.undo_gantt_change();
                else if (action.type === "redo")
                    tasksController.redo_gantt_change();
            }
        }
    }

    Frame.FrameView {
        theme: root.theme
        anchors.fill: body
        visible: taskGanttModel.count() === 0
        interactive: false
        scene: UI.empty(width, height, tasksController.advancedBusy, root.language)
    }
}

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    signal deleteTasksRequested()
    property real footerHorizontalOverflow: 0
    readonly property var range: tasksController.ganttRange
    readonly property int dayCount: Math.max(1, Number(range.days || 1))
    readonly property real labelWidth: Math.min(310, Math.max(220, width * 0.30))
    readonly property real timelineViewportWidth: Math.max(1, width - labelWidth)
    property real zoomLevel: 1.0
    property string scaleMode: "auto"
    property var scheduleAutoScrollRow: null
    readonly property real baseDayWidth: Math.max(
        10, Math.min(28, timelineViewportWidth / dayCount)
    )
    readonly property real dayWidth: Math.max(
        2, Math.min(80, baseDayWidth * zoomLevel)
    )
    readonly property real timelineContentWidth: Math.max(
        timelineViewportWidth, dayCount * dayWidth
    )
    readonly property bool showDayGrid: dayWidth >= 16
    readonly property int firstVisibleDay: Math.max(
        0, Math.floor(timelineHeader.contentX / dayWidth) - 1
    )
    readonly property int lastVisibleDay: Math.min(
        dayCount,
        Math.ceil((timelineHeader.contentX + timelineHeader.width) / dayWidth) + 1
    )
    readonly property int visibleDayBoundaries: Math.max(
        0, lastVisibleDay - firstVisibleDay + 1
    )
    readonly property var displayTicks: dayWidth >= 22
        ? (tasksController.ganttTickSets.days || [])
        : dayWidth >= 7
            ? (tasksController.ganttTickSets.weeks || [])
            : dayWidth >= 2.8
                ? (tasksController.ganttTickSets.months || [])
                : (tasksController.ganttTickSets.quarters || [])

    function compactDate(value) {
        const text = String(value || "")
        return text.length >= 10 ? text.slice(0, 10) : text || "-"
    }

    function ganttMessage(value) {
        const text = String(value || "")
        if (text === "Start and deadline are not set")
            return qsTr("Start and deadline are not set")
        if (text === "Start is not set")
            return qsTr("Start is not set")
        if (text === "Deadline is not set")
            return qsTr("Deadline is not set")
        if (text === "Deadline precedes start")
            return qsTr("Deadline precedes start")
        if (text === "Task is overdue")
            return qsTr("Task is overdue")
        if (text === "Task has no assignee")
            return qsTr("Task has no assignee")
        if (text === "Deadline falls on a weekend")
            return qsTr("Deadline falls on a weekend")
        if (text === "Assignee has overlapping tasks")
            return qsTr("Assignee has overlapping tasks")
        return text
    }

    function ganttMessages(value) {
        return String(value || "").split("\n").map(function(part) {
            return root.ganttMessage(part)
        }).join("\n")
    }

    function shortDate(value) {
        const text = String(value || "").slice(0, 10)
        if (!text)
            return "-"
        const dateValue = new Date(text + "T00:00:00")
        if (isNaN(dateValue.getTime()))
            return text
        return Qt.locale().toString(dateValue, "MMM d")
    }

    function dateForDay(offset) {
        const source = String(range.rangeStart || "")
        if (!source)
            return ""
        const value = new Date(source + "T00:00:00Z")
        value.setUTCDate(value.getUTCDate() + Number(offset || 0))
        return value.toISOString().slice(0, 10)
    }

    function dayBoundaryLevel(offset) {
        const value = new Date(dateForDay(offset) + "T00:00:00Z")
        if (isNaN(value.getTime()))
            return 0
        if (value.getUTCDate() === 1)
            return 2
        if (value.getUTCDay() === 1)
            return 1
        return 0
    }

    function setZoom(value, anchorX) {
        const next = Math.max(0.15, Math.min(5.0, Number(value || 1)))
        if (Math.abs(next - zoomLevel) < 0.001)
            return
        const anchor = Math.max(
            0, Math.min(timelineHeader.width, Number(anchorX || 0))
        )
        const anchoredDay = (timelineHeader.contentX + anchor) / dayWidth
        zoomLevel = next
        const maximum = Math.max(
            0, timelineHeader.contentWidth - timelineHeader.width
        )
        timelineWheelAnimation.stop()
        timelineHeader.contentX = Math.max(
            0, Math.min(maximum, anchoredDay * dayWidth - anchor)
        )
        timelineWheelTarget = timelineHeader.contentX
    }

    function zoomBy(factor, anchorX) {
        scaleMode = "custom"
        setZoom(zoomLevel * factor, anchorX)
    }

    function setScaleMode(mode) {
        const widths = {"days": 28, "weeks": 12, "months": 5,
                        "quarters": 2, "auto": baseDayWidth}
        const targetWidth = Number(widths[mode] || baseDayWidth)
        scaleMode = mode
        setZoom(targetWidth / baseDayWidth, timelineHeader.width / 2)
    }

    function setOverviewPosition(position, pointerOffset) {
        const maximum = Math.max(0,
            timelineHeader.contentWidth - timelineHeader.width)
        const thumbWidth = overviewThumb.width
        const travel = Math.max(0, overviewTimeline.width - thumbWidth)
        const offset = pointerOffset === undefined
            ? thumbWidth / 2 : Number(pointerOffset || 0)
        const left = Math.max(0, Math.min(
            travel, Number(position || 0) - offset
        ))
        timelineWheelAnimation.stop()
        timelineHeader.contentX = travel > 0
            ? left / travel * maximum : 0
        timelineWheelTarget = timelineHeader.contentX
    }

    function revealToday() {
        const today = Number(range.todayDay)
        if (today < 0)
            return
        timelineHeader.contentX = Math.max(
            0,
            Math.min(
                timelineHeader.contentWidth - timelineHeader.width,
                today * root.dayWidth - timelineHeader.width * 0.42
            )
        )
    }

    function scrollTimeline(pixelDelta, angleDelta) {
        const delta = pixelDelta !== 0
            ? pixelDelta * 1.65 : (angleDelta / 120) * 150
        if (delta === 0)
            return
        const maximum = Math.max(
            0, timelineHeader.contentWidth - timelineHeader.width
        )
        const base = timelineWheelAnimation.running
            ? timelineWheelTarget : timelineHeader.contentX
        timelineWheelTarget = Math.max(0, Math.min(maximum, base - delta))
        timelineWheelAnimation.stop()
        timelineWheelAnimation.to = timelineWheelTarget
        timelineWheelAnimation.start()
    }

    function startScheduleAutoScroll(taskRow) {
        scheduleAutoScrollRow = taskRow
        scheduleAutoScroll.start()
    }

    function stopScheduleAutoScroll(taskRow) {
        if (taskRow && scheduleAutoScrollRow !== taskRow)
            return
        scheduleAutoScroll.stop()
        scheduleAutoScrollRow = null
    }

    Timer {
        id: scheduleAutoScroll
        interval: 20
        repeat: true
        onTriggered: {
            const taskRow = root.scheduleAutoScrollRow
            if (!taskRow || !taskRow.editingSchedule) {
                root.stopScheduleAutoScroll(taskRow)
                return
            }
            const maximum = Math.max(
                0,
                timelineHeader.contentWidth - timelineHeader.width
            )
            let next = timelineHeader.contentX
            if (taskRow.lastPointerX < 28)
                next -= 10
            else if (taskRow.lastPointerX
                    > taskRow.scheduleViewportWidth - 28)
                next += 10
            next = Math.max(0, Math.min(maximum, next))
            if (next === timelineHeader.contentX)
                return
            timelineWheelAnimation.stop()
            timelineHeader.contentX = next
            root.timelineWheelTarget = next
            taskRow.updateSchedule(taskRow.lastPointerX)
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
        height: 54
        radius: root.theme.itemRadius
        color: root.theme.surfaceContainer

        Item {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: root.labelWidth

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 8
                spacing: 8
                Controls.MaterialIcon {
                    name: "gantt"
                    size: 16
                    color: root.theme.action
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 0
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("TASK SCHEDULE")
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                    }
                    Label {
                        Layout.fillWidth: true
                        text: tasksController.ganttScheduledCount
                            + qsTr(" scheduled")
                            + (tasksController.ganttUnscheduledCount
                                ? "  ·  "
                                    + tasksController.ganttUnscheduledCount
                                    + qsTr(" unscheduled") : "")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                        elide: Text.ElideRight
                    }
                }
            }
        }

        Flickable {
            id: timelineHeader
            // ui-scrollbar: external-horizontal overviewTimeline
            anchors.left: parent.left
            anchors.leftMargin: root.labelWidth
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            contentWidth: root.timelineContentWidth
            contentHeight: height
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            flickableDirection: Flickable.HorizontalFlick

            Item {
                width: root.timelineContentWidth
                height: timelineHeader.height

                Repeater {
                    model: root.displayTicks
                    delegate: Item {
                        required property var modelData
                        x: Number(modelData.offsetDay || 0) * root.dayWidth
                        width: Math.max(
                            48,
                            Number(modelData.spanDays || 1) * root.dayWidth
                        )
                        height: parent.height

                        Rectangle {
                            anchors.left: parent.left
                            anchors.top: parent.top
                            anchors.bottom: parent.bottom
                            width: modelData.major ? 2 : 1
                            color: modelData.major
                                ? root.theme.outline : root.theme.separator
                            opacity: modelData.major ? 0.55 : 0.7
                        }
                        Label {
                            anchors.left: parent.left
                            anchors.leftMargin: 6
                            anchors.verticalCenter: parent.verticalCenter
                            width: parent.width - 8
                            text: modelData.label
                            color: modelData.major
                                ? root.theme.primaryText
                                : root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: modelData.major ? 8 : 7
                            font.weight: modelData.major
                                ? Font.DemiBold : Font.Normal
                            elide: Text.ElideRight
                        }
                    }
                }

                Repeater {
                    model: tasksController.ganttMilestones
                    delegate: Item {
                        id: headerMilestone
                        required property var modelData
                        x: Number(modelData.offsetDay || 0) * root.dayWidth - 10
                        width: 21
                        height: parent.height
                        z: 4

                        Rectangle {
                            anchors.left: parent.horizontalCenter
                            anchors.top: parent.top
                            anchors.topMargin: 2
                            width: Math.min(150, Math.max(
                                76, milestoneLabel.implicitWidth + 43))
                            height: 22
                            radius: root.theme.fieldRadius
                            color: root.theme.tertiaryContainer
                            border.width: 1
                            border.color: root.theme.tertiary
                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 6
                                anchors.rightMargin: 6
                                spacing: 4
                                Controls.MaterialIcon {
                                    name: "milestone"
                                    size: 13
                                    color: root.theme.tertiary
                                }
                                Label {
                                    id: milestoneLabel
                                    Layout.fillWidth: true
                                    text: modelData.label
                                    color: root.theme.primaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.caption
                                    font.weight: Font.DemiBold
                                    elide: Text.ElideRight
                                }
                                Label {
                                    visible: Number(modelData.taskCount || 0) > 0
                                    text: modelData.completion + "%"
                                    color: root.theme.tertiary
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.caption
                                    font.weight: Font.Bold
                                }
                            }
                        }
                        Rectangle {
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.top: parent.top
                            anchors.topMargin: 23
                            anchors.bottom: parent.bottom
                            width: 3
                            color: root.theme.tertiary
                            opacity: 0.94
                        }
                        HoverHandler { id: headerMilestoneHover }
                        Controls.ToolTip {
                            theme: root.theme
                            visible: headerMilestoneHover.hovered
                            text: modelData.label + "  ·  " + modelData.dueDate
                                + (Number(modelData.taskCount || 0) > 0
                                    ? "  ·  " + modelData.completion + "%" : "")
                        }
                    }
                }

                Item {
                    visible: Number(root.range.todayDay) >= 0
                    x: Number(root.range.todayDay) * root.dayWidth
                    width: 3
                    height: parent.height
                    Rectangle {
                        anchors.fill: parent
                        color: root.theme.error
                        opacity: 0.82
                    }
                    Label {
                        anchors.right: parent.left
                        anchors.rightMargin: 4
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: 2
                        text: qsTr("TODAY")
                        color: root.theme.error
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.micro
                        font.weight: Font.Bold
                    }
                }
            }

            WheelHandler {
                target: null
                blocking: true
                onWheel: function(event) {
                    if (event.modifiers & Qt.ShiftModifier) {
                        root.scrollTimeline(
                            event.pixelDelta.y || event.pixelDelta.x,
                            event.angleDelta.y || event.angleDelta.x
                        )
                    } else {
                        const steps = event.angleDelta.y
                            ? event.angleDelta.y / 120
                            : event.pixelDelta.y / 80
                        root.zoomBy(
                            Math.pow(1.16, steps), event.position.x
                        )
                    }
                    event.accepted = true
                }
            }

            onFlickStarted: {
                timelineWheelAnimation.stop()
                root.timelineWheelTarget = contentX
            }
        }
    }

    Item {
        id: body
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: header.bottom
        anchors.bottom: overview.top
        anchors.topMargin: 3
        clip: true

        Item {
            id: timelineGrid
            anchors.left: parent.left
            anchors.leftMargin: root.labelWidth
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            clip: true

            Repeater {
                model: tasksController.ganttWeekendSpans
                delegate: Rectangle {
                    required property var modelData
                    x: Number(modelData.offsetDay || 0) * root.dayWidth
                        - timelineHeader.contentX
                    width: Number(modelData.durationDays || 1)
                        * root.dayWidth
                    height: timelineGrid.height
                    color: root.theme.surfaceContainerHigh
                    opacity: 0.22
                }
            }

            Item {
                id: dailyGrid
                objectName: "ganttDailyGrid"
                anchors.fill: parent
                visible: root.showDayGrid

                Repeater {
                    model: root.showDayGrid
                        ? root.visibleDayBoundaries : 0
                    delegate: Rectangle {
                        required property int index
                        readonly property int dayIndex:
                            root.firstVisibleDay + index
                        readonly property int boundaryLevel:
                            root.dayBoundaryLevel(dayIndex)

                        x: dayIndex * root.dayWidth
                            - timelineHeader.contentX
                        width: boundaryLevel === 2 ? 2 : 1
                        height: dailyGrid.height
                        color: boundaryLevel > 0
                            ? root.theme.outline : root.theme.separator
                        opacity: boundaryLevel === 2
                            ? 0.52 : boundaryLevel === 1 ? 0.38 : 0.24
                    }
                }
            }

            Repeater {
                model: root.showDayGrid ? [] : tasksController.ganttTicks
                delegate: Rectangle {
                    required property var modelData
                    x: Number(modelData.offsetDay || 0) * root.dayWidth
                        - timelineHeader.contentX
                    width: modelData.major ? 2 : 1
                    height: timelineGrid.height
                    color: modelData.major
                        ? root.theme.outline : root.theme.separator
                    opacity: modelData.major ? 0.28 : 0.38
                }
            }
            Repeater {
                model: tasksController.ganttMilestones
                delegate: Rectangle {
                    required property var modelData
                    x: Number(modelData.offsetDay || 0) * root.dayWidth
                        - timelineHeader.contentX
                    width: 3
                    height: timelineGrid.height
                    color: root.theme.tertiary
                    opacity: 0.72
                    z: 3
                }
            }
            Rectangle {
                visible: Number(root.range.todayDay) >= 0
                x: Number(root.range.todayDay) * root.dayWidth
                    - timelineHeader.contentX
                width: 2
                height: parent.height
                color: root.theme.error
                opacity: 0.52
            }
        }

        Controls.SmoothListView {
            theme: root.theme
            id: ganttList
            objectName: "ganttTaskList"
            anchors.fill: parent
            clip: true
            spacing: 0
            model: taskGanttModel
            reuseItems: true

            delegate: Column {
                id: taskRow

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
                readonly property real scheduleViewportWidth:
                    timelineRow.width

                ListView.onPooled: root.stopScheduleAutoScroll(taskRow)

                function updateSchedule(pointerX) {
                    lastPointerX = pointerX
                    const contentX = pointerX + timelineHeader.contentX
                    if (scheduleEditMode === "create") {
                        editStartDay = Math.round(contentX / root.dayWidth)
                        editDurationDays = 1
                        return
                    }
                    const delta = Math.round(
                        (contentX - pressContentX) / root.dayWidth
                    )
                    if (scheduleEditMode === "move") {
                        editStartDay = originalStartDay + delta
                        editDurationDays = originalDurationDays
                    } else if (scheduleEditMode === "resize-start") {
                        const maximum = originalStartDay
                            + originalDurationDays - 1
                        editStartDay = Math.min(
                            maximum, originalStartDay + delta
                        )
                        editDurationDays = maximum - editStartDay + 1
                    } else if (scheduleEditMode === "resize-end") {
                        editStartDay = originalStartDay
                        editDurationDays = Math.max(
                            1, originalDurationDays + delta
                        )
                    }
                }

                function finishScheduleEdit() {
                    if (!editingSchedule)
                        return
                    const changed = !ganttScheduled
                        || editStartDay !== ganttStartDay
                        || editDurationDays !== ganttDurationDays
                    const completedMode = scheduleEditMode
                    editingSchedule = false
                    scheduleEditMode = ""
                    root.stopScheduleAutoScroll(taskRow)
                    if (changed)
                        tasksController.stage_gantt_schedule(
                            taskCode, editStartDay, editDurationDays,
                            completedMode
                        )
                    else
                        tasksController.activate_advanced_task(taskCode, 0)
                }

                width: ganttList.width
                spacing: 0

                Rectangle {
                    width: parent.width
                    height: taskRow.ganttSectionFirst ? 28 : 0
                    visible: taskRow.ganttSectionFirst
                    color: root.theme.workspace

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 9
                        anchors.rightMargin: 9
                        spacing: 7
                        Controls.MaterialIcon {
                            name: taskRow.ganttSection === "scheduled"
                                ? "schedule" : "warning"
                            size: 14
                            color: taskRow.ganttSection === "scheduled"
                                ? root.theme.action : root.theme.yellow
                        }
                        Label {
                            Layout.fillWidth: true
                            text: taskRow.ganttSection === "scheduled"
                                ? qsTr("SCHEDULED TASKS")
                                : qsTr("UNSCHEDULED TASKS")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
                            font.weight: Font.DemiBold
                        }
                    }
                }

                Rectangle {
                    width: parent.width
                    height: taskRow.groupFirst ? 27 : 0
                    visible: taskRow.groupFirst
                    color: root.theme.surfaceContainerLow

                    RowLayout {
                        anchors.left: parent.left
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        width: root.labelWidth
                        anchors.leftMargin: 8
                        anchors.rightMargin: 8
                        spacing: 6
                        Controls.MaterialIcon {
                            name: taskRow.groupCollapsed
                                ? "chevron-right" : "expand-more"
                            size: 13
                            color: root.theme.secondaryText
                        }
                        Rectangle {
                            Layout.preferredWidth: 7
                            Layout.preferredHeight: 7
                            radius: 3.5
                            color: taskRow.groupColor || root.theme.action
                        }
                        Label {
                            Layout.fillWidth: true
                            text: taskRow.group.toUpperCase()
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
                            font.weight: Font.DemiBold
                            elide: Text.ElideRight
                        }
                        Label {
                            text: taskRow.groupCount
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
                        }
                    }
                    Item {
                        anchors.left: parent.left
                        anchors.leftMargin: root.labelWidth
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        clip: true

                        Rectangle {
                            visible: taskRow.ganttGroupDurationDays > 0
                            x: taskRow.ganttGroupStartDay * root.dayWidth
                                - timelineHeader.contentX
                            width: Math.max(5,
                                taskRow.ganttGroupDurationDays
                                    * root.dayWidth - 2)
                            height: taskRow.groupCollapsed ? 11 : 5
                            anchors.verticalCenter: parent.verticalCenter
                            radius: height / 2
                            color: taskRow.groupColor || root.theme.action
                            opacity: taskRow.groupCollapsed ? 0.55 : 0.34

                            Rectangle {
                                anchors.left: parent.left
                                anchors.top: parent.top
                                anchors.bottom: parent.bottom
                                width: parent.width
                                    * taskRow.ganttGroupProgress / 100
                                radius: parent.radius
                                color: taskRow.groupColor || root.theme.action
                                opacity: 0.95
                            }
                        }
                    }
                    Controls.ActivationHandler {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onActivated: tasksController.toggle_group_collapsed(
                            taskRow.groupKey
                        )
                    }
                }

                Item {
                    id: rowContent
                    width: parent.width
                    height: taskRow.groupCollapsed ? 0 : 50
                    visible: !taskRow.groupCollapsed

                    Rectangle {
                        anchors.fill: parent
                        color: taskRow.checked
                            ? root.theme.secondaryContainer
                            : taskRow.selected
                                ? root.theme.contentSelection
                                : rowHover.hovered
                                    ? root.theme.rowHover : "transparent"
                        opacity: taskRow.checked ? 0.55 : 1
                    }
                    Rectangle {
                        anchors.left: parent.left
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        width: root.labelWidth
                        color: root.theme.surfaceContainerLow
                        opacity: 0.94
                    }
                    Rectangle {
                        visible: taskRow.selected
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        width: 2
                        height: parent.height - 12
                        radius: 1
                        color: root.theme.action
                    }
                    Rectangle {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        height: 1
                        color: root.theme.separator
                    }

                    RowLayout {
                        anchors.left: parent.left
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        width: root.labelWidth
                        anchors.leftMargin: 5
                        anchors.rightMargin: 8
                        spacing: 7

                        Controls.CheckBox {
                            theme: root.theme
                            Layout.preferredWidth: 27
                            Layout.preferredHeight: 27
                            leftPadding: 3
                            checked: taskRow.checked
                            onClicked: tasksController.toggle_advanced_checked(
                                taskRow.taskCode
                            )
                        }
                        Controls.ItemPreview {
                            theme: root.theme
                            Layout.preferredWidth: 30
                            Layout.preferredHeight: 30
                            previewSize: 30
                            source: taskRow.parentPreviewUrl
                            fallbackIcon: "sobject"
                            fallbackText: taskRow.parentTitle.slice(0, 2).toUpperCase()
                            accent: taskRow.processColor
                            round: false
                            outlined: false
                            animateAppearance: false
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 0
                            Label {
                                Layout.fillWidth: true
                                text: taskRow.parentTitle
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.label
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }

                            Label {
                                Layout.fillWidth: true
                                text: taskRow.processLabel
                                    + (taskRow.assignedLabel
                                        ? "  ·  " + taskRow.assignedLabel : "")
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.micro
                                elide: Text.ElideRight
                            }
                        }
                        Controls.MaterialIcon {
                            visible: Boolean(taskRow.ganttWarning)
                            name: "warning"
                            size: 13
                            color: root.theme.yellow
                                Controls.ToolTip {
                                    theme: root.theme
                                    visible: warningHover.hovered
                                    text: root.ganttMessages(
                                        taskRow.ganttWarning
                                    )
                                }
                            HoverHandler { id: warningHover }
                        }
                    }

                    Item {
                        id: timelineRow
                        anchors.left: parent.left
                        anchors.leftMargin: root.labelWidth
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        clip: true

                        Item {
                            id: scheduleBar
                            z: 2
                            visible: taskRow.ganttScheduled
                                || taskRow.editingSchedule
                            x: (taskRow.editingSchedule
                                    ? taskRow.editStartDay
                                    : taskRow.ganttStartDay) * root.dayWidth
                                - timelineHeader.contentX
                            width: Math.max(
                                7,
                                (taskRow.editingSchedule
                                    ? taskRow.editDurationDays
                                    : taskRow.ganttDurationDays)
                                    * root.dayWidth - 4
                            )
                            height: 27
                            anchors.verticalCenter: parent.verticalCenter

                            HoverHandler { id: scheduleHover }

                            Rectangle {
                                id: startDateChip
                                visible: scheduleHover.hovered
                                    && !taskRow.editingSchedule
                                z: 8
                                x: 0
                                y: -10
                                height: 17
                                width: startDateText.implicitWidth + 12
                                radius: height / 2
                                color: root.theme.surfaceContainerHighest
                                border.width: 1
                                border.color: root.theme.outlineVariant
                                Label {
                                    id: startDateText
                                    anchors.centerIn: parent
                                    text: scheduleBar.width < 110
                                        ? root.shortDate(taskRow.start)
                                            + "  \u00b7  "
                                            + root.shortDate(taskRow.end)
                                        : root.shortDate(taskRow.start)
                                    color: root.theme.primaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.micro
                                    font.weight: Font.DemiBold
                                }
                            }
                            Rectangle {
                                visible: scheduleHover.hovered
                                    && !taskRow.editingSchedule
                                    && scheduleBar.width >= 110
                                z: 8
                                x: Math.max(0, scheduleBar.width - width)
                                y: -10
                                height: 17
                                width: endDateText.implicitWidth + 12
                                radius: height / 2
                                color: root.theme.surfaceContainerHighest
                                border.width: 1
                                border.color: root.theme.outlineVariant
                                Label {
                                    id: endDateText
                                    anchors.centerIn: parent
                                    text: root.shortDate(taskRow.end)
                                    color: root.theme.primaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.micro
                                    font.weight: Font.DemiBold
                                }
                            }

                            Rectangle {
                                anchors.fill: parent
                                radius: root.theme.itemRadius
                                color: taskRow.ganttColor || root.theme.action
                                opacity: taskRow.editingSchedule ? 0.42 : 0.30
                            }
                            Rectangle {
                                anchors.left: parent.left
                                anchors.top: parent.top
                                anchors.bottom: parent.bottom
                                width: parent.width
                                    * progressHandle.displayProgress / 100
                                radius: root.theme.itemRadius
                                color: taskRow.ganttColor || root.theme.action
                                opacity: 0.88
                            }
                            Label {
                                anchors.fill: parent
                                anchors.leftMargin: 7
                                anchors.rightMargin: 7
                                text: taskRow.editingSchedule
                                    ? root.dateForDay(taskRow.editStartDay)
                                        + " — " + root.dateForDay(
                                            taskRow.editStartDay
                                                + taskRow.editDurationDays - 1
                                        )
                                    : taskRow.processLabel + "  "
                                        + progressHandle.displayProgress + "%"
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                                font.weight: Font.DemiBold
                                verticalAlignment: Text.AlignVCenter
                                elide: Text.ElideRight
                            }

                            Rectangle {
                                visible: scheduleHover.hovered
                                    || taskRow.editingSchedule
                                anchors.left: parent.left
                                anchors.leftMargin: 2
                                anchors.verticalCenter: parent.verticalCenter
                                width: 6
                                height: 17
                                radius: 3
                                color: root.theme.primaryText
                                opacity: 0.68
                            }
                            Rectangle {
                                visible: scheduleHover.hovered
                                    || taskRow.editingSchedule
                                anchors.right: parent.right
                                anchors.rightMargin: 2
                                anchors.verticalCenter: parent.verticalCenter
                                width: 6
                                height: 17
                                radius: 3
                                color: root.theme.primaryText
                                opacity: 0.68
                            }
                            TaskGanttProgressHandle {
                                id: progressHandle
                                z: 5
                                theme: root.theme
                                controller: tasksController
                                taskCode: taskRow.taskCode
                                progress: taskRow.progress
                                barWidth: scheduleBar.width
                                rowHovered: rowHover.hovered
                                scheduled: taskRow.ganttScheduled
                                progressSupported:
                                    tasksController.progressSupported
                            }
                            Controls.ToolTip {
                                theme: root.theme
                                visible: scheduleHover.hovered
                                    && !taskRow.editingSchedule
                                text: taskRow.parentTitle + " · "
                                    + taskRow.processLabel + "\n"
                                    + taskRow.status + " · "
                                    + taskRow.assignedLabel + "\n"
                                    + root.compactDate(taskRow.start) + " — "
                                    + root.compactDate(taskRow.end) + " · "
                                    + taskRow.progress + "%"
                                    + (taskRow.ganttWarning
                                        ? "\n" + root.ganttMessages(
                                            taskRow.ganttWarning
                                        ) : "")
                            }
                        }

                        Rectangle {
                            id: unscheduledChip
                            objectName: "ganttUnscheduledIssueChip"
                            visible: !taskRow.ganttScheduled
                                && !taskRow.editingSchedule
                            anchors.left: parent.left
                            anchors.leftMargin: 10
                            anchors.verticalCenter: parent.verticalCenter
                            width: Math.floor(Math.min(
                                parent.width - 20,
                                unscheduledContent.implicitWidth + 14
                            ))
                            height: 30
                            radius: root.theme.itemRadius
                            color: root.theme.surfaceContainerHigh
                            RowLayout {
                                id: unscheduledContent
                                anchors.fill: parent
                                anchors.leftMargin: 7
                                anchors.rightMargin: 7
                                spacing: 5
                                Controls.MaterialIcon {
                                    name: "warning"
                                    size: 13
                                    color: root.theme.yellow
                                }
                                Label {
                                    id: unscheduledLabel
                                    objectName: "ganttUnscheduledIssueLabel"
                                    Layout.preferredWidth: implicitWidth
                                    text: root.ganttMessage(
                                        taskRow.ganttIssue
                                    )
                                    color: root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.label
                                }
                            }
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
                                    return Qt.ClosedHandCursor
                                const start = taskRow.ganttStartDay
                                    * root.dayWidth - timelineHeader.contentX
                                const width = Math.max(
                                    7,
                                    taskRow.ganttDurationDays
                                        * root.dayWidth - 4
                                )
                                if (taskRow.ganttScheduled
                                        && mouseX >= start - 12
                                        && mouseX <= start + width + 12) {
                                    if (Math.abs(mouseX - start) <= 12
                                            || Math.abs(
                                                mouseX - start - width
                                            ) <= 12)
                                        return Qt.SizeHorCursor
                                    return Qt.OpenHandCursor
                                }
                                if (!taskRow.ganttScheduled
                                        && mouseX >= 10
                                        && mouseX <= 10 + unscheduledChip.width)
                                    return Qt.OpenHandCursor
                                return Qt.OpenHandCursor
                            }

                            onPressed: function(mouse) {
                                timelineWheelAnimation.stop()
                                if (mouse.button === Qt.MiddleButton) {
                                    taskRow.scheduleEditMode = "pan"
                                    taskRow.panPressX = mouse.x
                                    taskRow.panContentX
                                        = timelineHeader.contentX
                                    taskRow.panMoved = false
                                    taskRow.panButton = mouse.button
                                    taskRow.panModifiers = mouse.modifiers
                                    return
                                }
                                const start = taskRow.ganttStartDay
                                    * root.dayWidth - timelineHeader.contentX
                                const width = Math.max(
                                    7,
                                    taskRow.ganttDurationDays
                                        * root.dayWidth - 4
                                )
                                let mode = ""
                                if (taskRow.ganttScheduled
                                        && mouse.x >= start - 12
                                        && mouse.x <= start + width + 12) {
                                    if (Math.abs(mouse.x - start) <= 12)
                                        mode = "resize-start"
                                    else if (Math.abs(
                                            mouse.x - start - width) <= 12)
                                        mode = "resize-end"
                                    else
                                        mode = "move"
                                } else if (!taskRow.ganttScheduled
                                        && mouse.x >= 10
                                        && mouse.x <= 10 + unscheduledChip.width) {
                                    mode = "create"
                                }
                                if (!mode) {
                                    taskRow.scheduleEditMode = "pan"
                                    taskRow.panPressX = mouse.x
                                    taskRow.panContentX
                                        = timelineHeader.contentX
                                    taskRow.panMoved = false
                                    taskRow.panButton = mouse.button
                                    taskRow.panModifiers = mouse.modifiers
                                    return
                                }
                                taskRow.scheduleEditMode = mode
                                taskRow.editingSchedule = true
                                taskRow.originalStartDay
                                    = taskRow.ganttStartDay
                                taskRow.originalDurationDays = Math.max(
                                    1, taskRow.ganttDurationDays
                                )
                                taskRow.editStartDay = taskRow.ganttStartDay
                                taskRow.editDurationDays
                                    = taskRow.originalDurationDays
                                taskRow.pressContentX = mouse.x
                                    + timelineHeader.contentX
                                taskRow.lastPointerX = mouse.x
                                if (mode === "create")
                                    taskRow.updateSchedule(mouse.x)
                            }
                            onPositionChanged: function(mouse) {
                                if (taskRow.scheduleEditMode === "pan") {
                                    if (Math.abs(mouse.x - taskRow.panPressX) > 3)
                                        taskRow.panMoved = true
                                    const maximum = Math.max(
                                        0,
                                        timelineHeader.contentWidth
                                            - timelineHeader.width
                                    )
                                    timelineHeader.contentX = Math.max(
                                        0,
                                        Math.min(
                                            maximum,
                                            taskRow.panContentX
                                                - mouse.x
                                                + taskRow.panPressX
                                        )
                                    )
                                    root.timelineWheelTarget
                                        = timelineHeader.contentX
                                    return
                                }
                                if (!taskRow.editingSchedule)
                                    return
                                taskRow.updateSchedule(mouse.x)
                                if (mouse.x < 28
                                        || mouse.x > width - 28)
                                    root.startScheduleAutoScroll(taskRow)
                                else
                                    root.stopScheduleAutoScroll(taskRow)
                            }
                            onReleased: {
                                if (taskRow.scheduleEditMode === "pan") {
                                    const moved = taskRow.panMoved
                                    const button = taskRow.panButton
                                    const modifiers = taskRow.panModifiers
                                    taskRow.scheduleEditMode = ""
                                    taskRow.panMoved = false
                                    taskRow.panButton = Qt.NoButton
                                    taskRow.panModifiers = Qt.NoModifier
                                    if (!moved && button === Qt.LeftButton)
                                        tasksController.activate_advanced_task(
                                            taskRow.taskCode, modifiers
                                        )
                                    return
                                }
                                taskRow.finishScheduleEdit()
                            }
                            onCanceled: {
                                root.stopScheduleAutoScroll(taskRow)
                                taskRow.editingSchedule = false
                                taskRow.scheduleEditMode = ""
                                taskRow.panMoved = false
                                taskRow.panButton = Qt.NoButton
                                taskRow.panModifiers = Qt.NoModifier
                            }
                            onDoubleClicked: {
                                if (!taskRow.editingSchedule)
                                    tasksController.open_object(
                                        taskRow.parentKey
                                    )
                            }
                        }

                    }

                    HoverHandler { id: rowHover }
                    MouseArea {
                        anchors.fill: parent
                        z: -1
                        acceptedButtons: Qt.LeftButton
                        cursorShape: Qt.PointingHandCursor
                        onClicked: function(mouse) {
                            tasksController.activate_advanced_task(
                                taskRow.taskCode, mouse.modifiers
                            )
                        }
                        onDoubleClicked: tasksController.open_object(
                            taskRow.parentKey
                        )
                    }
                }
            }

            footer: Item {
                width: ganttList.width
                height: tasksController.advancedHasMore ? 42 : 8
                Controls.Button {
                    anchors.centerIn: parent
                    visible: tasksController.advancedHasMore
                    enabled: !tasksController.advancedBusy
                    theme: root.theme
                    text: tasksController.advancedBusy
                        ? qsTr("LOADING") : qsTr("LOAD MORE")
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
                y: Math.max(0, Math.min(
                    parent.height,
                    ganttList.contentHeight - ganttList.contentY
                ))
                width: parent.width
                height: Math.max(0, parent.height - y)
                acceptedButtons: Qt.LeftButton | Qt.MiddleButton
                cursorShape: pressed
                    ? Qt.ClosedHandCursor : Qt.OpenHandCursor
                preventStealing: true

                onPressed: function(mouse) {
                    timelineWheelAnimation.stop()
                    pressX = mouse.x
                    pressContentX = timelineHeader.contentX
                }
                onPositionChanged: function(mouse) {
                    if (!pressed)
                        return
                    const maximum = Math.max(
                        0, timelineHeader.contentWidth - timelineHeader.width
                    )
                    timelineHeader.contentX = Math.max(
                        0, Math.min(
                            maximum,
                            pressContentX - mouse.x + pressX
                        )
                    )
                    root.timelineWheelTarget = timelineHeader.contentX
                }
                onReleased: root.timelineWheelTarget
                    = timelineHeader.contentX
                onCanceled: root.timelineWheelTarget
                    = timelineHeader.contentX
            }

            onWheel: function(wheel) {
                if (wheel.modifiers & Qt.ShiftModifier) {
                    root.scrollTimeline(
                        wheel.pixelDelta.y || wheel.pixelDelta.x,
                        wheel.angleDelta.y || wheel.angleDelta.x
                    )
                } else {
                    const steps = wheel.angleDelta.y
                        ? wheel.angleDelta.y / 120
                        : wheel.pixelDelta.y / 80
                    if (steps !== 0)
                        root.zoomBy(Math.pow(1.16, steps), wheel.x)
                }
                wheel.accepted = true
            }
        }
    }

    Rectangle {
        id: overview
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: footer.top
        height: 30
        color: root.theme.surfaceContainerLow

        Item {
            id: overviewTimeline
            anchors.left: parent.left
            anchors.leftMargin: root.labelWidth
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            clip: true

            Rectangle {
                id: overviewDataTrack
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                height: 10
                radius: 5
                color: root.theme.surfaceContainerHigh
                border.width: 1
                border.color: root.theme.outlineVariant
                clip: true

                Repeater {
                    model: tasksController.ganttOverview
                    delegate: Rectangle {
                        required property var modelData
                        x: Number(modelData.startDay || 0)
                            / root.dayCount * overviewDataTrack.width
                        width: Math.max(2,
                            Number(modelData.durationDays || 1)
                                / root.dayCount * overviewDataTrack.width)
                        height: 3
                        anchors.verticalCenter: parent.verticalCenter
                        radius: 1.5
                        color: modelData.warning
                            ? root.theme.yellow
                            : (modelData.color || root.theme.action)
                        opacity: 0.62
                    }
                }

                Repeater {
                    model: tasksController.ganttMilestones
                    delegate: Rectangle {
                        required property var modelData
                        x: Number(modelData.offsetDay || 0) / root.dayCount
                            * overviewDataTrack.width
                        width: 2
                        height: overviewDataTrack.height
                        color: root.theme.tertiary
                        opacity: 0.82
                    }
                }

                Rectangle {
                    visible: Number(root.range.todayDay) >= 0
                    x: Number(root.range.todayDay) / root.dayCount
                        * overviewDataTrack.width
                    width: 2
                    height: overviewDataTrack.height
                    color: root.theme.error
                    opacity: 0.68
                }
            }

            Rectangle {
                id: overviewThumb
                z: 3
                x: timelineHeader.contentWidth > 0
                        && timelineHeader.contentWidth > timelineHeader.width
                    ? timelineHeader.contentX
                        / (timelineHeader.contentWidth - timelineHeader.width)
                        * Math.max(0, overviewTimeline.width - width)
                    : 0
                width: timelineHeader.contentWidth > 0
                    ? Math.min(overviewTimeline.width, Math.max(
                        28, timelineHeader.width
                            / timelineHeader.contentWidth
                            * overviewTimeline.width
                    ))
                    : overviewTimeline.width
                height: 18
                anchors.verticalCenter: parent.verticalCenter
                radius: 9
                color: root.theme.secondaryContainer
                border.width: 1
                border.color: root.theme.action

                Rectangle {
                    anchors.centerIn: parent
                    width: Math.min(24, parent.width - 12)
                    height: 3
                    radius: 1.5
                    color: root.theme.secondaryText
                    opacity: 0.55
                }
            }

            MouseArea {
                id: overviewPointer
                property real thumbOffset: overviewThumb.width / 2
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: pressed
                    ? Qt.ClosedHandCursor : Qt.OpenHandCursor
                onPressed: function(mouse) {
                    const insideThumb = mouse.x >= overviewThumb.x
                        && mouse.x <= overviewThumb.x + overviewThumb.width
                    thumbOffset = insideThumb
                        ? mouse.x - overviewThumb.x
                        : overviewThumb.width / 2
                    root.setOverviewPosition(mouse.x, thumbOffset)
                }
                onPositionChanged: function(mouse) {
                    if (pressed)
                        root.setOverviewPosition(mouse.x, thumbOffset)
                }
            }
        }

        RowLayout {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: root.labelWidth
            anchors.leftMargin: 10
            anchors.rightMargin: 8
            spacing: 6
            Controls.MaterialIcon {
                name: "visibility"
                size: 12
                color: root.theme.secondaryText
            }
            Label {
                Layout.fillWidth: true
                text: tasksController.ganttWarningCount
                    ? tasksController.ganttWarningCount + qsTr(" warnings")
                    : qsTr("Project overview")
                color: tasksController.ganttWarningCount
                    ? root.theme.yellow : root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.caption
                elide: Text.ElideRight
            }
        }
    }

    Controls.Popup {
        id: batchPopup
        theme: root.theme
        width: 236
        height: batchActions.implicitHeight + 12

        contentItem: ColumnLayout {
            id: batchActions
            spacing: 4
            Label {
                Layout.fillWidth: true
                text: tasksController.advancedCheckedCount
                    + qsTr(" SELECTED TASKS")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.caption
                font.weight: Font.DemiBold
                leftPadding: 8
                bottomPadding: 4
            }
            Repeater {
                model: [
                    {"title": "Shift one day earlier", "action": "shift", "amount": -1},
                    {"title": "Shift one day later", "action": "shift", "amount": 1},
                    {"title": "Align start dates", "action": "align-start", "amount": 1},
                    {"title": "Align deadlines", "action": "align-end", "amount": 1},
                    {"title": "Schedule sequentially", "action": "sequence", "amount": 1},
                    {"title": "Extend by one day", "action": "extend", "amount": 1},
                    {"title": "Shorten by one day", "action": "shorten", "amount": 1}
                ]
                delegate: Controls.Button {
                    required property var modelData
                    Layout.fillWidth: true
                    theme: root.theme
                    flat: true
                    text: modelData.title
                    onClicked: {
                        tasksController.apply_gantt_batch(
                            modelData.action, modelData.amount
                        )
                        batchPopup.close()
                    }
                }
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 1
                color: root.theme.separator
            }
            Controls.Button {
                objectName: "ganttDeleteSelectedTasksButton"
                Layout.fillWidth: true
                theme: root.theme
                flat: true
                destructive: true
                text: qsTr("Delete selected tasks")
                icon.name: "delete"
                enabled: tasksController.advancedDirtyCount === 0
                    && !tasksController.advancedDeleting
                onClicked: {
                    batchPopup.close()
                    root.deleteTasksRequested()
                }
            }
        }
    }

    Controls.Popup {
        id: scalePopup
        theme: root.theme
        width: 154
        height: scaleActions.implicitHeight + 12

        contentItem: ColumnLayout {
            id: scaleActions
            spacing: 4
            Repeater {
                model: [
                    {"title": "Fit range", "mode": "auto"},
                    {"title": "Days", "mode": "days"},
                    {"title": "Weeks", "mode": "weeks"},
                    {"title": "Months", "mode": "months"},
                    {"title": "Quarters", "mode": "quarters"}
                ]
                delegate: Controls.Button {
                    required property var modelData
                    Layout.fillWidth: true
                    theme: root.theme
                    flat: true
                    highlighted: root.scaleMode === modelData.mode
                    text: modelData.title
                    onClicked: {
                        root.setScaleMode(modelData.mode)
                        scalePopup.close()
                    }
                }
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

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 10
            anchors.rightMargin: root.width >= 380 ? 120 : 8
            spacing: 8
            Label {
                Layout.fillWidth: true
                text: root.compactDate(root.range.rangeStart)
                    + "  —  " + root.compactDate(root.range.rangeEnd)
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.caption
                elide: Text.ElideRight
            }
            Controls.Button {
                id: batchActionsButton
                visible: tasksController.advancedCheckedCount > 0
                Layout.preferredWidth: visible ? implicitWidth : 0
                theme: root.theme
                tonal: true
                text: tasksController.advancedCheckedCount
                    + qsTr(" SELECTED")
                icon.name: "select-all"
                onPressed: batchPopup.rememberSourceOpen()
                onClicked: batchPopup.toggleBelowItem(
                    batchActionsButton, true, 6)
            }
            Controls.CompactIconButton {
                theme: root.theme
                iconName: "undo"
                toolTip: qsTr("Undo schedule change · Ctrl+Z")
                enabled: tasksController.ganttCanUndo
                onClicked: tasksController.undo_gantt_change()
            }
            Controls.CompactIconButton {
                theme: root.theme
                iconName: "redo"
                toolTip: qsTr("Redo schedule change · Ctrl+Shift+Z")
                enabled: tasksController.ganttCanRedo
                onClicked: tasksController.redo_gantt_change()
            }
            Controls.CompactIconButton {
                theme: root.theme
                iconName: "calendar-today"
                toolTip: tasksController.ganttWorkingDays
                    ? qsTr("Use calendar days") : qsTr("Use weekdays")
                elevated: tasksController.ganttWorkingDays
                onClicked: tasksController.set_gantt_working_days(
                    !tasksController.ganttWorkingDays
                )
            }
            Controls.CompactIconButton {
                theme: root.theme
                iconName: "group"
                toolTip: tasksController.ganttResourceMode
                    ? qsTr("Restore task grouping")
                    : qsTr("Group workload by assignee")
                elevated: tasksController.ganttResourceMode
                onClicked: tasksController.set_gantt_resource_mode(
                    !tasksController.ganttResourceMode
                )
            }
            Controls.CompactIconButton {
                visible: root.width >= 700
                theme: root.theme
                iconName: "zoom-out"
                toolTip: qsTr("Zoom out")
                enabled: root.zoomLevel > 0.15
                onClicked: root.zoomBy(1 / 1.25, timelineHeader.width / 2)
            }
            Controls.Button {
                id: scaleActionsButton
                visible: root.width >= 700
                theme: root.theme
                text: Math.round(root.zoomLevel * 100) + "%"
                Layout.preferredWidth: 58
                onPressed: scalePopup.rememberSourceOpen()
                onClicked: scalePopup.toggleBelowItem(
                    scaleActionsButton, true, 6)
                Controls.ToolTip {
                    theme: root.theme
                    visible: parent.hovered
                    text: qsTr("Timeline scale")
                }
            }
            Controls.CompactIconButton {
                visible: root.width >= 700
                theme: root.theme
                iconName: "zoom-in"
                toolTip: qsTr("Zoom in")
                enabled: root.zoomLevel < 5.0
                onClicked: root.zoomBy(1.25, timelineHeader.width / 2)
            }
            Controls.CompactIconButton {
                theme: root.theme
                iconName: "schedule"
                toolTip: Number(root.range.todayDay) >= 0
                    ? qsTr("Center today")
                    : qsTr("Today is outside this task range")
                enabled: Number(root.range.todayDay) >= 0
                onClicked: root.revealToday()
            }
        }
    }

    Label {
        anchors.centerIn: body
        visible: !tasksController.advancedBusy && taskGanttModel.count() === 0
        text: qsTr("No tasks match the current scope and filters")
        color: root.theme.secondaryText
        font.family: root.theme.fontFamily
        font.pointSize: Controls.Typography.label
    }
}

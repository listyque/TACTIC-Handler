import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    objectName: "taskBrowserTable"

    required property var theme
    property string menuTaskCode: ""
    property string menuParentKey: ""
    property string menuProcess: ""
    property bool menuDirty: false
    property bool menuConflict: false
    property var expandedTaskDetails: ({})
    property real footerHorizontalOverflow: 0

    function columnRecord(key) {
        const columns = tasksController.taskColumns || []
        for (let index = 0; index < columns.length; ++index) {
            if (columns[index].key === key)
                return columns[index]
        }
        return null
    }

    function columnVisible(key) {
        const record = columnRecord(key)
        return !record || Boolean(record.visible)
    }

    function columnWidth(key, fallback) {
        const record = columnRecord(key)
        const configured = record ? Number(record.width || fallback) : fallback
        const denseLimits = {
            "process": 92,
            "status": 105,
            "assignee": 118,
            "dates": 90,
            "progress": 72,
            "hours": 72,
            "notes": 38,
            "priority": 80,
            "milestone": 105,
            "supervisor": 118
        }
        const compactLimits = {
            "object": 88,
            "status": 88
        }
        if (width < 420 && compactLimits[key] !== undefined)
            return Math.min(configured, compactLimits[key])
        if (width < 1100 && denseLimits[key] !== undefined)
            return Math.min(configured, denseLimits[key])
        return configured
    }

    function responsiveColumnWidth(key, fallback, compactWidth) {
        return columnWidth(key, fallback)
    }

    function columnOrder(key, fallback) {
        const record = columnRecord(key)
        return record ? Number(record.order) : fallback
    }

    readonly property bool showAssigneeColumn:
        columnVisible("assignee") && width >= 520
    readonly property bool showDateColumn:
        columnVisible("dates") && width >= 700
    readonly property bool showProgressColumn:
        columnVisible("progress") && width >= 800
    readonly property bool showHoursColumn:
        columnVisible("hours") && width >= 900
    readonly property bool showNotesColumn:
        columnVisible("notes") && width >= 480
    readonly property bool showPriorityColumn:
        columnVisible("priority") && width >= 980
    readonly property bool showMilestoneColumn:
        columnVisible("milestone") && width >= 1180
    readonly property bool showSupervisorColumn:
        columnVisible("supervisor") && width >= 1380
    readonly property real leadingControlsWidth: 56
    readonly property real expandedColumnSpacing: 7
    readonly property real expandedObjectLeft:
        5 + leadingControlsWidth + expandedColumnSpacing
    readonly property real objectColumnWidth: Math.max(
        132, Math.min(columnWidth("object", 210), width * 0.25, 210)
    )
    readonly property real statusColumnWidth: responsiveColumnWidth(
        "status", 138, 108
    )
    readonly property real assigneeColumnWidth: columnWidth("assignee", 154)
    readonly property real dateColumnWidth: columnWidth("dates", 112)
    readonly property real progressColumnWidth: columnWidth("progress", 94)
    readonly property real hoursColumnWidth: columnWidth("hours", 86)
    readonly property real notesColumnWidth: columnWidth("notes", 48)
    readonly property real priorityColumnWidth: columnWidth("priority", 96)
    readonly property real milestoneColumnWidth: columnWidth("milestone", 132)
    readonly property real supervisorColumnWidth: columnWidth("supervisor", 154)
    readonly property int actionColumn: 13
    readonly property real tableColumnSpacing:
        width < 420 ? 3 : width < 1100 ? 5 : 7
    function choiceIndex(values, selected) {
        const source = values || []
        for (let index = 0; index < source.length; ++index) {
            if (String(source[index].value || "") === String(selected || ""))
                return index
        }
        return -1
    }

    function compactDate(value) {
        const text = String(value || "")
        return text.length >= 10 ? text.slice(0, 10) : text || "—"
    }

    function initials(value) {
        const parts = String(value || "").trim().split(/\s+/)
        if (!parts.length || !parts[0])
            return "?"
        return (parts[0][0] + (parts.length > 1 ? parts[1][0] : ""))
            .toUpperCase()
    }

    function openMenu(sourceItem, taskCode, parentKey, process, dirty, conflict) {
        menuTaskCode = taskCode
        menuParentKey = parentKey
        menuProcess = process
        menuDirty = dirty
        menuConflict = conflict
        taskMenu.openBelow(sourceItem)
    }

    function taskDetailsExpanded(taskCode) {
        return Boolean(expandedTaskDetails[String(taskCode || "")])
    }

    function toggleTaskDetails(taskCode) {
        const key = String(taskCode || "")
        const next = Object.assign({}, expandedTaskDetails)
        next[key] = !Boolean(next[key])
        expandedTaskDetails = next
    }

    component HeaderLabel: Label {
        color: root.theme.secondaryText
        font.family: root.theme.fontFamily
        font.pixelSize: 8
        font.weight: Font.DemiBold
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    Rectangle {
        id: header
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: 34
        color: root.theme.surfaceContainer
        radius: root.theme.itemRadius

        GridLayout {
            anchors.fill: parent
            anchors.leftMargin: 5
            anchors.rightMargin: 7
            columns: root.actionColumn + 1
            columnSpacing: root.tableColumnSpacing
            rowSpacing: 0

            Item {
                Layout.column: 0
                Layout.preferredWidth: root.leadingControlsWidth
                Layout.minimumWidth: root.leadingControlsWidth
                Layout.maximumWidth: root.leadingControlsWidth
                Layout.preferredHeight: 28
                Md3CheckBox {
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    width: 28
                    height: 28
                    theme: root.theme
                    leftPadding: 4
                    checked: tasksController.advancedAllVisibleChecked
                    onClicked: tasksController.set_all_advanced_checked(checked)
                }
            }
            HeaderLabel {
                Layout.column: 1 + root.columnOrder("object", 0)
                Layout.preferredWidth: root.objectColumnWidth
                Layout.minimumWidth: root.objectColumnWidth
                Layout.maximumWidth: root.objectColumnWidth
                text: qsTr("OBJECT")
            }
            HeaderLabel {
                Layout.column: 1 + root.columnOrder("status", 2)
                Layout.preferredWidth: root.statusColumnWidth
                Layout.minimumWidth: root.statusColumnWidth
                Layout.maximumWidth: root.statusColumnWidth
                text: qsTr("STATUS")
            }
            HeaderLabel {
                visible: root.showAssigneeColumn
                Layout.column: 1 + root.columnOrder("assignee", 3)
                Layout.preferredWidth: root.assigneeColumnWidth
                Layout.minimumWidth: root.assigneeColumnWidth
                Layout.maximumWidth: root.assigneeColumnWidth
                text: qsTr("ASSIGNEE")
            }
            HeaderLabel {
                visible: root.showDateColumn
                Layout.column: 1 + root.columnOrder("dates", 4)
                Layout.preferredWidth: root.dateColumnWidth
                Layout.minimumWidth: root.dateColumnWidth
                Layout.maximumWidth: root.dateColumnWidth
                text: qsTr("START / DEADLINE")
            }
            HeaderLabel {
                visible: root.showProgressColumn
                Layout.column: 1 + root.columnOrder("progress", 5)
                Layout.fillWidth: true
                Layout.preferredWidth: root.progressColumnWidth
                Layout.minimumWidth: root.progressColumnWidth
                text: qsTr("PROGRESS")
            }
            HeaderLabel {
                visible: root.showHoursColumn
                Layout.column: 1 + root.columnOrder("hours", 6)
                Layout.preferredWidth: root.hoursColumnWidth
                Layout.minimumWidth: root.hoursColumnWidth
                Layout.maximumWidth: root.hoursColumnWidth
                text: qsTr("HOURS")
            }
            HeaderLabel {
                visible: root.showNotesColumn
                Layout.column: 1 + root.columnOrder("notes", 8)
                Layout.preferredWidth: root.notesColumnWidth
                Layout.minimumWidth: root.notesColumnWidth
                Layout.maximumWidth: root.notesColumnWidth
                text: qsTr("NOTES")
                horizontalAlignment: Text.AlignHCenter
            }
            HeaderLabel {
                visible: root.showPriorityColumn
                Layout.column: 1 + root.columnOrder("priority", 8)
                Layout.preferredWidth: root.priorityColumnWidth
                Layout.minimumWidth: root.priorityColumnWidth
                Layout.maximumWidth: root.priorityColumnWidth
                text: qsTr("PRIORITY")
            }
            HeaderLabel {
                visible: root.showMilestoneColumn
                Layout.column: 1 + root.columnOrder("milestone", 9)
                Layout.preferredWidth: root.milestoneColumnWidth
                Layout.minimumWidth: root.milestoneColumnWidth
                Layout.maximumWidth: root.milestoneColumnWidth
                text: qsTr("MILESTONE")
            }
            HeaderLabel {
                visible: root.showSupervisorColumn
                Layout.column: 1 + root.columnOrder("supervisor", 10)
                Layout.preferredWidth: root.supervisorColumnWidth
                Layout.minimumWidth: root.supervisorColumnWidth
                Layout.maximumWidth: root.supervisorColumnWidth
                text: qsTr("SUPERVISOR")
            }
            Item {
                Layout.column: root.actionColumn
                Layout.preferredWidth: 30
                Layout.minimumWidth: 30
                Layout.maximumWidth: 30
            }
        }
    }

    SmoothListView {
        id: taskList
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: header.bottom
        anchors.bottom: bulkBar.top
        anchors.topMargin: 3
        clip: true
        spacing: 0
        model: advancedTaskTableModel
        reuseItems: true
        cacheBuffer: 900

        onInteractionMovingChanged: {
            if (interactionMoving && taskMenu.visible)
                taskMenu.close()
        }

        delegate: Column {
            id: taskDelegate

            required property int index
            required property string taskCode
            required property string parentKey
            required property string parentTitle
            required property string parentSearchType
            required property string parentCode
            required property string parentPreviewUrl
            required property string process
            required property string processLabel
            required property string processColor
            required property var processChoices
            required property bool isNew
            required property string context
            required property string status
            required property string statusColor
            required property var statusChoices
            required property string assigned
            required property string assignedLabel
            required property string assignedAvatar
            required property int assignedChoiceIndex
            required property var userChoices
            required property string supervisor
            required property string supervisorLabel
            required property string supervisorAvatar
            required property var supervisorChoices
            required property string priority
            required property string priorityLabel
            required property string priorityColor
            required property var priorityChoices
            readonly property var effectivePriorityChoices:
                priorityChoices && priorityChoices.length > 1
                ? priorityChoices : tasksController.taskPriorityChoices
            required property string milestoneCode
            required property string milestoneLabel
            required property string milestoneDueDate
            required property var milestoneChoices
            required property string start
            required property string end
            required property string dueState
            required property int progress
            required property string description
            required property real plannedHours
            required property real loggedHours
            required property real approvedHours
            required property real pendingHours
            required property real remainingHours
            required property real overPlanHours
            required property string hoursLabel
            required property int notes
            required property int snapshotFileCount
            required property string latestVersion
            required property string group
            required property string groupKey
            required property int groupCount
            required property bool groupFirst
            required property bool groupCollapsed
            required property string groupColor
            required property bool selected
            required property bool checked
            required property bool dirty
            required property bool loading
            required property string error
            required property bool conflict
            readonly property bool detailsExpanded:
                root.taskDetailsExpanded(taskCode)

            width: taskList.width
            height: groupHeader.height + taskContent.height
            spacing: 0

            Rectangle {
                id: groupHeader
                width: parent.width
                height: taskDelegate.groupFirst ? 28 : 0
                visible: taskDelegate.groupFirst
                color: root.theme.workspace

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 4
                    anchors.rightMargin: 8
                    spacing: 6
                    MaterialIcon {
                        name: taskDelegate.groupCollapsed
                            ? "chevron-right" : "expand-more"
                        size: 14
                        color: root.theme.secondaryText
                    }
                    Rectangle {
                        Layout.preferredWidth: 8
                        Layout.preferredHeight: 8
                        radius: 4
                        color: taskDelegate.groupColor
                            || root.theme.action
                    }
                    Label {
                        Layout.fillWidth: true
                        text: taskDelegate.group.toUpperCase()
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 9
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                    }
                    Rectangle {
                        Layout.preferredWidth: Math.max(
                            20, groupCountLabel.implicitWidth + 10
                        )
                        Layout.preferredHeight: 18
                        radius: 9
                        color: root.theme.surfaceContainerHigh
                        Label {
                            id: groupCountLabel
                            anchors.centerIn: parent
                            text: taskDelegate.groupCount
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 8
                            font.weight: Font.DemiBold
                        }
                    }
                }
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: tasksController.toggle_group_collapsed(
                        taskDelegate.groupKey
                    )
                }
            }

            Item {
                id: taskContent
                width: parent.width
                readonly property real expandedGap:
                    taskDelegate.detailsExpanded ? 6 : 0
                readonly property real bodyHeight:
                    !taskDelegate.detailsExpanded ? 58
                    : 58 + expandedDetails.detailImplicitHeight
                height: taskDelegate.groupCollapsed
                    ? 0 : bodyHeight + expandedGap
                visible: !taskDelegate.groupCollapsed
                Item {
                    id: taskRow
                    x: 0
                    y: 0
                    width: parent.width
                    height: 58
                    visible: !taskDelegate.groupCollapsed

                Rectangle {
                    objectName: "taskRowSurface_" + taskDelegate.taskCode
                    anchors.fill: parent
                    color: taskDelegate.selected
                        ? root.theme.selected
                        : taskDelegate.checked
                            ? root.theme.secondaryContainer
                        : taskDelegate.isNew
                            ? root.theme.panelDeep
                            : rowHover.hovered
                                ? root.theme.rowHover
                                : root.theme.surfaceContainerLow
                    opacity: taskDelegate.checked
                        && !taskDelegate.selected ? 0.72 : 1
                    Behavior on color {
                        enabled: !taskList.interactionMoving
                        ColorAnimation {
                            duration: root.theme.motionFast
                            easing.type: Easing.OutCubic
                        }
                    }
                }
                Rectangle {
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    width: 3
                    height: parent.height - 14
                    radius: width / 2
                    color: taskDelegate.processColor || root.theme.action
                    opacity: taskDelegate.selected
                        || taskDelegate.detailsExpanded ? 1 : 0.82
                }
                Rectangle {
                    visible: !taskDelegate.detailsExpanded
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    height: 1
                    color: root.theme.separator
                }

                MouseArea {
                    anchors.fill: parent
                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: function(mouse) {
                        if (mouse.button === Qt.RightButton) {
                            root.menuTaskCode = taskDelegate.taskCode
                            root.menuParentKey = taskDelegate.parentKey
                            root.menuProcess = taskDelegate.process
                            root.menuDirty = taskDelegate.dirty
                            root.menuConflict = taskDelegate.conflict
                            taskMenu.openAt(taskRow, mouse.x, mouse.y)
                        } else {
                            tasksController.activate_advanced_task(
                                taskDelegate.taskCode, mouse.modifiers
                            )
                        }
                    }
                    onDoubleClicked: tasksController.open_object(
                        taskDelegate.parentKey
                    )
                }
                HoverHandler { id: rowHover }

                CompactIconButton {
                    id: taskDetailsExpander
                    objectName: "taskDetailsExpander_"
                        + taskDelegate.taskCode
                    anchors.left: parent.left
                    anchors.leftMargin: 5
                    anchors.top: parent.top
                    anchors.topMargin: 15
                    width: 28
                    height: 28
                    z: 20
                    theme: root.theme
                    iconName: taskDelegate.detailsExpanded
                        ? "chevron-down" : "chevron-right"
                    iconColor: taskDelegate.detailsExpanded
                        ? root.theme.action : root.theme.secondaryText
                    backgroundColor: taskDelegate.detailsExpanded
                        ? root.theme.surfaceContainerHighest : "transparent"
                    toolTip: taskDelegate.detailsExpanded
                        ? qsTr("Collapse task details")
                        : qsTr("Expand task details")
                    enabled: !taskDelegate.loading
                    onClicked: {
                        tasksController.activate_advanced_task(
                            taskDelegate.taskCode, 0
                        )
                        root.toggleTaskDetails(taskDelegate.taskCode)
                    }
                }

                GridLayout {
                    anchors.left: parent.left
                    anchors.top: parent.top
                    width: taskDelegate.detailsExpanded
                        ? root.leadingControlsWidth
                            + root.objectColumnWidth
                            + root.expandedColumnSpacing
                        : parent.width - 12
                    height: 58
                    anchors.leftMargin: 5
                    columns: taskDelegate.detailsExpanded
                        ? 2 : root.actionColumn + 1
                    columnSpacing: taskDelegate.detailsExpanded
                        ? root.expandedColumnSpacing : root.tableColumnSpacing
                    rowSpacing: 0

                    Item {
                        Layout.column: 0
                        Layout.preferredWidth: root.leadingControlsWidth
                        Layout.minimumWidth: root.leadingControlsWidth
                        Layout.maximumWidth: root.leadingControlsWidth
                        Layout.preferredHeight: 28
                        Md3CheckBox {
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            width: 28
                            height: 28
                            theme: root.theme
                            leftPadding: 4
                            checked: taskDelegate.checked
                            onClicked: tasksController.toggle_advanced_checked(
                                taskDelegate.taskCode
                            )
                        }
                    }
                    RowLayout {
                        objectName: "taskObjectCell_" + taskDelegate.taskCode
                        Layout.column: taskDelegate.detailsExpanded
                            ? 1 : 1 + root.columnOrder("object", 0)
                        Layout.preferredWidth: root.objectColumnWidth
                        Layout.minimumWidth: root.objectColumnWidth
                        Layout.maximumWidth: root.objectColumnWidth
                        Layout.alignment: Qt.AlignLeft | Qt.AlignVCenter
                        spacing: 7
                        ItemPreview {
                            theme: root.theme
                            Layout.preferredWidth: 34
                            Layout.preferredHeight: 34
                            previewSize: 34
                            source: taskDelegate.parentPreviewUrl
                            fallbackIcon: "sobject"
                            fallbackText: root.initials(taskDelegate.parentTitle)
                            accent: taskDelegate.processColor
                            round: false
                            outlined: false
                            animateAppearance: false
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 0
                            Label {
                                Layout.fillWidth: true
                                text: taskDelegate.parentTitle
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pixelSize: 10
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }
                            Label {
                                Layout.fillWidth: true
                                text: taskDelegate.processLabel
                                    + (taskDelegate.context
                                        && taskDelegate.context
                                            !== taskDelegate.process
                                        ? " · " + taskDelegate.context : "")
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pixelSize: 8
                                elide: Text.ElideRight
                            }
                        }
                    }
                    Md3ComboBox {
                        visible: !taskDelegate.detailsExpanded
                        theme: root.theme
                        Layout.column: 1 + root.columnOrder("status", 2)
                        actionField: true
                        enabled: !tasksController.advancedSaving
                            && !tasksController.advancedBusy
                        Layout.preferredWidth: root.statusColumnWidth
                        Layout.minimumWidth: root.statusColumnWidth
                        Layout.maximumWidth: root.statusColumnWidth
                        Layout.preferredHeight: 29
                        model: taskDelegate.statusChoices
                        textRole: "label"
                        valueRole: "value"
                        colorRole: "color"
                        currentIndex: root.choiceIndex(
                            taskDelegate.statusChoices, taskDelegate.status
                        )
                        displayText: currentIndex >= 0 ? currentText : "No status"
                        onActivated: tasksController.stage_advanced_value(
                            taskDelegate.taskCode, "status", currentValue
                        )
                    }
                    Md3UserComboBox {
                        visible: !taskDelegate.detailsExpanded
                            && root.showAssigneeColumn
                        theme: root.theme
                        Layout.column: 1 + root.columnOrder("assignee", 3)
                        actionField: true
                        enabled: !tasksController.advancedSaving
                            && !tasksController.advancedBusy
                        Layout.preferredWidth: root.assigneeColumnWidth
                        Layout.minimumWidth: root.assigneeColumnWidth
                        Layout.maximumWidth: root.assigneeColumnWidth
                        Layout.preferredHeight: 29
                        userModel: userListModel
                        model: taskDelegate.userChoices
                        textRole: "label"
                        valueRole: "value"
                        currentIndex: taskDelegate.assignedChoiceIndex
                        currentAvatarUrl: taskDelegate.assignedAvatar
                        currentInitials: root.initials(
                            taskDelegate.assignedLabel
                        )
                        displayText: currentIndex >= 0
                            ? currentText : taskDelegate.assignedLabel
                        onActivated: tasksController.stage_advanced_value(
                            taskDelegate.taskCode, "assigned", currentValue
                        )
                    }
                    ColumnLayout {
                        visible: !taskDelegate.detailsExpanded
                            && root.showDateColumn
                        Layout.column: 1 + root.columnOrder("dates", 4)
                        Layout.preferredWidth: root.dateColumnWidth
                        Layout.minimumWidth: root.dateColumnWidth
                        Layout.maximumWidth: root.dateColumnWidth
                        spacing: 0
                        Label {
                            text: root.compactDate(taskDelegate.start)
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 8
                        }
                        Label {
                            text: root.compactDate(taskDelegate.end)
                            color: taskDelegate.dueState === "overdue"
                                ? root.theme.error : root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 9
                        }
                    }
                    ColumnLayout {
                        visible: !taskDelegate.detailsExpanded
                            && root.showProgressColumn
                        Layout.column: 1 + root.columnOrder("progress", 5)
                        Layout.fillWidth: true
                        Layout.preferredWidth: root.progressColumnWidth
                        Layout.minimumWidth: root.progressColumnWidth
                        spacing: 2
                        Label {
                            text: taskDelegate.progress + "%"
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pixelSize: 8
                        }
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 3
                            radius: 1.5
                            color: root.theme.surfaceContainerHighest
                            Rectangle {
                                width: parent.width * taskDelegate.progress / 100
                                height: parent.height
                                radius: parent.radius
                                color: taskDelegate.processColor
                            }
                        }
                    }
                    Label {
                        visible: !taskDelegate.detailsExpanded
                            && root.showHoursColumn
                        Layout.column: 1 + root.columnOrder("hours", 6)
                        Layout.preferredWidth: root.hoursColumnWidth
                        Layout.minimumWidth: root.hoursColumnWidth
                        Layout.maximumWidth: root.hoursColumnWidth
                        text: taskDelegate.hoursLabel
                        color: taskDelegate.overPlanHours > 0
                            ? root.theme.red
                            : taskDelegate.pendingHours > 0
                                ? root.theme.yellow : root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 9
                        font.weight: Font.DemiBold
                        verticalAlignment: Text.AlignVCenter
                    }
                    CompactIconButton {
                        visible: root.showNotesColumn
                            && !taskDelegate.detailsExpanded
                        theme: root.theme
                        Layout.column: 1 + root.columnOrder("notes", 8)
                        Layout.preferredWidth: root.notesColumnWidth
                        Layout.minimumWidth: root.notesColumnWidth
                        Layout.maximumWidth: root.notesColumnWidth
                        iconName: "comment"
                        badgeCount: taskDelegate.notes
                        toolTip: qsTr("Open notes")
                        onClicked: tasksController.open_notes(
                            taskDelegate.parentKey, taskDelegate.process,
                            taskDelegate.taskCode
                        )
                    }
                    Md3ComboBox {
                        visible: !taskDelegate.detailsExpanded
                            && root.showPriorityColumn
                        theme: root.theme
                        Layout.column: 1 + root.columnOrder("priority", 8)
                        Layout.preferredWidth: root.priorityColumnWidth
                        Layout.minimumWidth: root.priorityColumnWidth
                        Layout.maximumWidth: root.priorityColumnWidth
                        Layout.preferredHeight: 29
                        actionField: false
                        showIndicator: true
                        model: taskDelegate.effectivePriorityChoices
                        textRole: "label"
                        valueRole: "value"
                        currentIndex: root.choiceIndex(
                            taskDelegate.effectivePriorityChoices,
                            taskDelegate.priority
                        )
                        displayText: currentIndex >= 0
                                && String(currentText).length > 0
                            ? currentText
                            : taskDelegate.priorityLabel || qsTr("No priority")
                        onActivated: tasksController.stage_advanced_value(
                            taskDelegate.taskCode, "priority", currentValue
                        )
                    }
                    Md3ComboBox {
                        visible: !taskDelegate.detailsExpanded
                            && root.showMilestoneColumn
                        theme: root.theme
                        Layout.column: 1 + root.columnOrder("milestone", 9)
                        Layout.preferredWidth: root.milestoneColumnWidth
                        Layout.minimumWidth: root.milestoneColumnWidth
                        Layout.maximumWidth: root.milestoneColumnWidth
                        Layout.preferredHeight: 29
                        actionField: true
                        model: taskDelegate.milestoneChoices
                        textRole: "label"
                        valueRole: "value"
                        currentIndex: root.choiceIndex(
                            taskDelegate.milestoneChoices,
                            taskDelegate.milestoneCode
                        )
                        displayText: currentIndex >= 0
                            ? currentText : taskDelegate.milestoneLabel
                        onActivated: tasksController.stage_advanced_value(
                            taskDelegate.taskCode, "milestoneCode", currentValue
                        )
                    }
                    Md3UserComboBox {
                        visible: !taskDelegate.detailsExpanded
                            && root.showSupervisorColumn
                        theme: root.theme
                        Layout.column: 1 + root.columnOrder("supervisor", 10)
                        Layout.preferredWidth: root.supervisorColumnWidth
                        Layout.minimumWidth: root.supervisorColumnWidth
                        Layout.maximumWidth: root.supervisorColumnWidth
                        Layout.preferredHeight: 29
                        actionField: true
                        userModel: userListModel
                        model: taskDelegate.supervisorChoices
                        textRole: "label"
                        valueRole: "value"
                        currentIndex: root.choiceIndex(
                            taskDelegate.supervisorChoices,
                            taskDelegate.supervisor
                        )
                        currentAvatarUrl: taskDelegate.supervisorAvatar
                        currentInitials: root.initials(
                            taskDelegate.supervisorLabel
                        )
                        displayText: currentIndex >= 0
                            ? currentText : taskDelegate.supervisorLabel
                        onActivated: tasksController.stage_advanced_value(
                            taskDelegate.taskCode, "supervisor", currentValue
                        )
                    }
                    RowLayout {
                        visible: !taskDelegate.detailsExpanded
                        Layout.column: root.actionColumn
                        Layout.preferredWidth: 30
                        Layout.minimumWidth: 30
                        Layout.maximumWidth: 30
                        Layout.preferredHeight: 30
                        spacing: 0

                        Item {
                            Layout.preferredWidth: 30
                            Layout.preferredHeight: 30
                            BusyIndicator {
                                anchors.centerIn: parent
                                width: 22
                                height: 22
                                visible: taskDelegate.loading
                                running: visible
                            }
                            MaterialIcon {
                                anchors.centerIn: parent
                                visible: !taskDelegate.loading
                                    && !taskDelegate.conflict
                                    && taskDelegate.error.length > 0
                                name: "error"
                                size: 16
                                color: root.theme.error
                            }
                            CompactIconButton {
                                anchors.fill: parent
                                visible: !taskDelegate.loading
                                    && taskDelegate.conflict
                                theme: root.theme
                                iconName: "sync_problem"
                                iconColor: root.theme.error
                                toolTip: qsTr("Resolve server conflict")
                                onClicked: root.openMenu(
                                    this, taskDelegate.taskCode,
                                    taskDelegate.parentKey, taskDelegate.process,
                                    taskDelegate.dirty, true
                                )
                            }
                            CompactIconButton {
                                id: overflowButton
                                anchors.fill: parent
                                visible: !taskDelegate.loading
                                    && taskDelegate.error.length === 0
                                    && !taskDelegate.conflict
                                opacity: rowHover.hovered || taskDelegate.selected
                                    || taskDelegate.dirty ? 1 : 0.35
                                theme: root.theme
                                iconName: "more_vert"
                                toolTip: qsTr("Task actions")
                                onClicked: root.openMenu(
                                    overflowButton, taskDelegate.taskCode,
                                    taskDelegate.parentKey, taskDelegate.process,
                                    taskDelegate.dirty, taskDelegate.conflict
                                )
                            }
                        }
                    }
                }
                }

                Loader {
                    id: expandedDetails
                    objectName: "taskExpandedDetails_"
                        + taskDelegate.taskCode
                    readonly property real detailImplicitHeight:
                        item ? item.implicitHeight : 0
                    active: !taskDelegate.groupCollapsed
                        && taskDelegate.detailsExpanded
                    visible: active
                    x: 0
                    y: taskRow.height
                    width: parent.width
                    height: active ? detailImplicitHeight : 0

                    sourceComponent: Component {
                        TaskHiddenDetails {
                            theme: root.theme
                            controller: tasksController
                            taskCode: taskDelegate.taskCode
                            parentKey: taskDelegate.parentKey
                            process: taskDelegate.process
                            processChoices: taskDelegate.processChoices
                            isNew: taskDelegate.isNew
                            status: taskDelegate.status
                            statusChoices: taskDelegate.statusChoices
                            assigned: taskDelegate.assigned
                            assignedLabel: taskDelegate.assignedLabel
                            assignedAvatar: taskDelegate.assignedAvatar
                            userChoices: taskDelegate.userChoices
                            supervisor: taskDelegate.supervisor
                            supervisorLabel: taskDelegate.supervisorLabel
                            supervisorChoices: taskDelegate.supervisorChoices
                            priority: taskDelegate.priority
                            priorityLabel: taskDelegate.priorityLabel
                            priorityChoices:
                                taskDelegate.effectivePriorityChoices
                            milestoneCode: taskDelegate.milestoneCode
                            milestoneLabel: taskDelegate.milestoneLabel
                            milestoneChoices: taskDelegate.milestoneChoices
                            start: taskDelegate.start
                            end: taskDelegate.end
                            progress: taskDelegate.progress
                            description: taskDelegate.description
                            plannedHours: taskDelegate.plannedHours
                            processColor: taskDelegate.processColor
                            notes: taskDelegate.notes
                            contentLeftMargin: 12
                            contentRightMargin: 12
                            showTopSeparator: true
                            showStatus: root.columnVisible("status")
                            showAssignee: root.columnVisible("assignee")
                            showDates: root.columnVisible("dates")
                            showProgress: root.columnVisible("progress")
                            showHours: root.columnVisible("hours")
                            showNotes: false
                            // Column preferences only control the compact table.
                            // Expanded editing must expose every editable field.
                            showPriority: true
                            showMilestone: true
                            showSupervisor: true
                        }
                    }
                }

                Rectangle {
                    visible: taskDelegate.detailsExpanded
                    x: 0
                    y: taskContent.bodyHeight - 1
                    width: parent.width
                    height: 1
                    color: root.theme.separator
                    opacity: 0.72
                }

                CompactIconButton {
                    visible: taskDelegate.detailsExpanded
                    anchors.right: expandedActionSlot.left
                    anchors.rightMargin: 4
                    anchors.top: parent.top
                    anchors.topMargin: 14
                    width: 30
                    height: 30
                    z: 40
                    theme: root.theme
                    iconName: "comment"
                    badgeCount: taskDelegate.notes
                    toolTip: qsTr("Open notes")
                    onClicked: tasksController.open_notes(
                        taskDelegate.parentKey, taskDelegate.process,
                        taskDelegate.taskCode
                    )
                }

                Item {
                    id: expandedActionSlot
                    visible: taskDelegate.detailsExpanded
                    anchors.right: parent.right
                    anchors.rightMargin: 5
                    anchors.top: parent.top
                    anchors.topMargin: 14
                    width: 30
                    height: 30
                    z: 40

                    BusyIndicator {
                        anchors.centerIn: parent
                        width: 22
                        height: 22
                        visible: taskDelegate.loading
                        running: visible
                    }
                    MaterialIcon {
                        anchors.centerIn: parent
                        visible: !taskDelegate.loading
                            && !taskDelegate.conflict
                            && taskDelegate.error.length > 0
                        name: "error"
                        size: 16
                        color: root.theme.error
                    }
                    CompactIconButton {
                        anchors.fill: parent
                        visible: !taskDelegate.loading
                            && taskDelegate.conflict
                        theme: root.theme
                        iconName: "sync_problem"
                        iconColor: root.theme.error
                        toolTip: qsTr("Resolve server conflict")
                        onClicked: root.openMenu(
                            this, taskDelegate.taskCode,
                            taskDelegate.parentKey, taskDelegate.process,
                            taskDelegate.dirty, true
                        )
                    }
                    CompactIconButton {
                        id: expandedOverflowButton
                        anchors.fill: parent
                        visible: !taskDelegate.loading
                            && taskDelegate.error.length === 0
                            && !taskDelegate.conflict
                        theme: root.theme
                        iconName: "more_vert"
                        toolTip: qsTr("Task actions")
                        onClicked: root.openMenu(
                            expandedOverflowButton, taskDelegate.taskCode,
                            taskDelegate.parentKey, taskDelegate.process,
                            taskDelegate.dirty, taskDelegate.conflict
                        )
                    }
                }

            }
        }

        footer: Item {
            width: taskList.width
            height: tasksController.advancedHasMore ? 42 : 8
            Md3Button {
                anchors.centerIn: parent
                visible: tasksController.advancedHasMore
                enabled: !tasksController.advancedBusy
                theme: root.theme
                text: tasksController.advancedBusy
                    ? qsTr("LOADING") : qsTr("LOAD MORE")
                onClicked: tasksController.load_more_advanced()
            }
        }

        ScrollBar.vertical: Md3ScrollBar {
            theme: root.theme
            flickableTarget: taskList
        }
    }

    TaskBulkBar {
        id: bulkBar
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: footer.top
        height: implicitHeight
        theme: root.theme
    }

    Rectangle {
        id: footer
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.leftMargin: -root.footerHorizontalOverflow
        anchors.rightMargin: -root.footerHorizontalOverflow
        height: root.theme.dockWorkspaceFooterHeight
        color: root.theme.surfaceContainer

        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: 1
            color: root.theme.outlineVariant
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 10
            anchors.rightMargin: root.width >= 380 ? 120 : 8
            spacing: 10
            Label {
                text: tasksController.advancedFiltersActive
                    ? advancedTaskModel.count() + qsTr(" of ")
                        + tasksController.advancedLoadedCount + qsTr(" tasks")
                    : tasksController.advancedLoadedCount
                        + (tasksController.advancedLoadedCount === 1
                            ? qsTr(" task") : qsTr(" tasks"))
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 8
            }
            Label {
                visible: tasksController.advancedProcessCount > 0
                text: tasksController.advancedProcessCount
                    + (tasksController.advancedProcessCount === 1
                        ? qsTr(" process") : qsTr(" processes"))
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 8
            }
            Label {
                visible: tasksController.advancedCheckedCount > 0
                text: tasksController.advancedCheckedCount
                    + qsTr(" checked")
                color: root.theme.action
                font.family: root.theme.fontFamily
                font.pixelSize: 8
                font.weight: Font.DemiBold
            }
            Label {
                visible: tasksController.advancedLoadedCount
                    < tasksController.advancedTotalCount
                text: tasksController.advancedLoadedCount + qsTr(" of ")
                    + tasksController.advancedTotalCount + qsTr(" loaded")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 8
            }
            Item { Layout.fillWidth: true }
            CompactIconButton {
                visible: tasksController.advancedCheckedCount > 0
                theme: root.theme
                iconName: "close"
                toolTip: qsTr("Clear checked tasks")
                onClicked: tasksController.clear_advanced_checked()
            }
        }
    }

    Label {
        anchors.centerIn: taskList
        visible: !tasksController.advancedBusy
            && advancedTaskModel.count() === 0
        text: tasksController.advancedEmptyMessage
        color: root.theme.secondaryText
        font.family: root.theme.fontFamily
        font.pixelSize: 10
    }
    Connections {
        target: tasksController
        function onTaskDraftCreated(taskCode) {
            const next = Object.assign({}, root.expandedTaskDetails)
            next[String(taskCode || "")] = true
            root.expandedTaskDetails = next
            Qt.callLater(function() {
                for (let row = 0; row < advancedTaskTableModel.count(); ++row) {
                    if (String(advancedTaskTableModel.get(row).taskCode || "")
                            === String(taskCode || "")) {
                        taskList.positionViewAtIndex(
                            row, ListView.Contain
                        )
                        break
                    }
                }
            })
        }
        function onTaskDraftRemoved(taskCode) {
            const key = String(taskCode || "")
            const next = Object.assign({}, root.expandedTaskDetails)
            delete next[key]
            root.expandedTaskDetails = next
        }
    }
    ActionMenu {
        id: taskMenu
        parent: Overlay.overlay
        theme: root.theme
        preferredWidth: 210
        actions: [
            {
                "title": "Open object",
                "icon": "open_in_new",
                "command": "open"
            },
            {
                "title": "Open notes",
                "icon": "comment",
                "command": "notes"
            },
            {
                "title": "Edit task details",
                "icon": "edit",
                "command": "edit"
            },
            {
                "title": "Discard row changes",
                "icon": "undo",
                "command": "discard",
                "enabled": root.menuDirty
            },
            {
                "title": "Use server version",
                "icon": "cloud_download",
                "command": "server-version",
                "visible": root.menuConflict
            },
            {
                "title": "Keep my changes",
                "icon": "edit_note",
                "command": "keep-mine",
                "visible": root.menuConflict
            }
        ]
        onTriggered: function(command) {
            if (command === "open")
                tasksController.open_object(root.menuParentKey)
            else if (command === "notes")
                tasksController.open_notes(
                    root.menuParentKey, root.menuProcess, root.menuTaskCode
                )
            else if (command === "edit")
                tasksController.begin_edit_code(root.menuTaskCode)
            else if (command === "discard")
                tasksController.discard_advanced_changes(root.menuTaskCode)
            else if (command === "server-version")
                tasksController.resolve_advanced_conflict(
                    root.menuTaskCode, "server"
                )
            else if (command === "keep-mine")
                tasksController.resolve_advanced_conflict(
                    root.menuTaskCode, "mine"
                )
        }
    }
}

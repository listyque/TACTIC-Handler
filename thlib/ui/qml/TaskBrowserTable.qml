import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls
import "features/tasks" as Tasks
import "tactic_frame" as Frame
import "tactic_frame/features/tasks/workspace.ui.mjs" as WorkspaceUI
import "tactic_frame/features/tasks/table.ui.mjs" as TaskTable
import "tactic_frame/features/tasks/menus.ui.mjs" as TaskMenus
import "tactic_frame/features/tasks/cells.ui.mjs" as CellsUI

Item {
    id: root
    objectName: "taskBrowserTable"

    required property var theme
    property string menuTaskCode: ""
    property string menuParentKey: ""
    property string menuProcess: ""
    property bool menuDirty: false
    property bool menuConflict: false
    property bool menuIsNew: false
    property var expandedTaskDetails: ({})
    property real footerHorizontalOverflow: 0
    readonly property bool initialPresentationReady: initialTaskTablePresentation.ready
    signal columnContextRequested(var sourceItem, string columnKey, string columnLabel)
    signal columnsPressed
    signal columnsRequested(var sourceItem)
    signal taskDeleteRequested(string taskCode, bool checkedTasks)

    function columnRecord(key) {
        return TaskTable.column(tasksController.taskColumns, key);
    }

    function columnVisible(key) {
        const record = columnRecord(key);
        return !record || Boolean(record.visible);
    }

    function columnWidth(key, fallback) {
        return TaskTable.columnWidth(tasksController.taskColumns, key, fallback, width);
    }

    function responsiveColumnWidth(key, fallback, compactWidth) {
        return columnWidth(key, fallback);
    }

    function columnOrder(key, fallback) {
        const record = columnRecord(key);
        return record ? Number(record.order) : fallback;
    }

    readonly property bool showAssigneeColumn: TaskTable.visible(tasksController.taskColumns, "assignee", width)
    readonly property bool showStatusColumn: TaskTable.visible(tasksController.taskColumns, "status", width)
    readonly property bool showDateColumn: TaskTable.visible(tasksController.taskColumns, "dates", width)
    readonly property bool showProgressColumn: TaskTable.visible(tasksController.taskColumns, "progress", width)
    readonly property bool showHoursColumn: TaskTable.visible(tasksController.taskColumns, "hours", width)
    readonly property bool showNotesColumn: TaskTable.visible(tasksController.taskColumns, "notes", width)
    readonly property bool showPriorityColumn: TaskTable.visible(tasksController.taskColumns, "priority", width)
    readonly property bool showMilestoneColumn: TaskTable.visible(tasksController.taskColumns, "milestone", width)
    readonly property bool showSupervisorColumn: TaskTable.visible(tasksController.taskColumns, "supervisor", width)
    readonly property var tableGeometry: TaskTable.layout(tasksController.taskColumns, width)
    readonly property real horizontalContentOffset: taskList.contentX
    readonly property real leadingControlsWidth: TaskTable.metrics.leading
    readonly property real expandedColumnSpacing: 7
    readonly property real expandedObjectLeft: 5 + leadingControlsWidth + expandedColumnSpacing
    readonly property real objectColumnWidth: Math.max(132, Math.min(columnWidth("object", 210), width * 0.25, 210))
    readonly property real statusColumnWidth: responsiveColumnWidth("status", 138, 108)
    readonly property real assigneeColumnWidth: columnWidth("assignee", 154)
    readonly property real dateColumnWidth: columnWidth("dates", 112)
    readonly property real progressColumnWidth: columnWidth("progress", 94)
    readonly property real hoursColumnWidth: columnWidth("hours", 86)
    readonly property real notesColumnWidth: columnWidth("notes", 48)
    readonly property real priorityColumnWidth: columnWidth("priority", 96)
    readonly property real milestoneColumnWidth: columnWidth("milestone", 132)
    readonly property real supervisorColumnWidth: columnWidth("supervisor", 154)
    readonly property int actionColumn: 13
    readonly property real tableColumnSpacing: TaskTable.spacing(width)
    function choiceIndex(values, selected) {
        const source = values || [];
        for (let index = 0; index < source.length; ++index) {
            if (String(source[index].value || "") === String(selected || ""))
                return index;
        }
        return -1;
    }

    function compactDate(value) {
        const text = String(value || "");
        return text.length >= 10 ? text.slice(0, 10) : text || "—";
    }

    function initials(value) {
        return CellsUI.initials(value);
    }

    function openMenu(sourceItem, taskCode, parentKey, process, dirty, conflict, isNew) {
        menuTaskCode = taskCode;
        menuParentKey = parentKey;
        menuProcess = process;
        menuDirty = dirty;
        menuConflict = conflict;
        menuIsNew = isNew;
        taskMenu.openBelow(sourceItem);
    }

    function confirmTaskDelete(taskCode, checkedTasks) {
        root.taskDeleteRequested(String(taskCode || ""), Boolean(checkedTasks));
    }

    function taskDetailsExpanded(taskCode) {
        return Boolean(expandedTaskDetails[String(taskCode || "")]);
    }

    function toggleTaskDetails(taskCode) {
        const key = String(taskCode || "");
        const next = Object.assign({}, expandedTaskDetails);
        next[key] = !Boolean(next[key]);
        expandedTaskDetails = next;
    }

    TaskEditorReleaseCoordinator {
        id: editorReleaseCoordinator
        theme: root.theme
    }

    Tasks.TaskTableHeader {
        id: header
        table: root
        controller: tasksController
    }
    Controls.SmoothListView {
        id: taskList
        theme: root.theme
        objectName: "taskBrowserList"
        opacity: initialTaskTablePresentation.ready ? 1 : 0
        property int liveDelegateCount: 0
        property bool hoverEditorsEnabled: true
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: header.bottom
        anchors.bottom: bulkBar.top
        anchors.topMargin: TaskTable.metrics.headerGap
        clip: true
        spacing: 0
        model: advancedTaskTableModel
        contentWidth: Math.max(width, root.tableGeometry.width)
        flickableDirection: Flickable.AutoFlickDirection
        reuseItems: true
        // The compact row is now cheap to recreate. Four wheel steps of
        // prefetch keep scrolling smooth without retaining dozens of rows.
        cacheBuffer: 240

        function suspendHoverEditors() {
            hoverEditorsEnabled = false;
            editorHoverResumeTimer.restart();
        }

        Timer {
            id: editorHoverResumeTimer
            interval: 180
            onTriggered: {
                taskList.hoverEditorsEnabled = !taskList.interactionMoving;
            }
        }

        onContentYChanged: suspendHoverEditors()

        onInteractionMovingChanged: {
            if (interactionMoving) {
                suspendHoverEditors();
                if (taskMenu.visible)
                    taskMenu.close();
            } else if (!hoverEditorsEnabled) {
                editorHoverResumeTimer.restart();
            }
        }

        delegate: Column {
            id: taskDelegate

            Component.onCompleted: taskList.liveDelegateCount += 1
            Component.onDestruction: taskList.liveDelegateCount -= 1

            required property int index
            required property string taskCode
            required property string parentKey
            required property string parentTitle
            required property string parentPreviewUrl
            required property string process
            required property string processLabel
            required property string processColor
            required property bool isNew
            required property string context
            required property string status
            required property string statusLabel
            required property string statusColor
            required property string assigned
            required property string assignedLabel
            required property string assignedAvatar
            required property int assignedChoiceIndex
            required property string supervisor
            required property string supervisorLabel
            required property string supervisorAvatar
            required property string priority
            required property string priorityLabel
            required property string priorityColor
            required property string milestoneCode
            required property string milestoneLabel
            required property string start
            required property string end
            required property string dueState
            required property int progress
            required property string description
            required property real plannedHours
            required property real pendingHours
            required property real overPlanHours
            required property string hoursLabel
            required property int notes
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
            property bool viewPooled: false
            ListView.onPooled: viewPooled = true
            ListView.onReused: viewPooled = false
            readonly property bool detailsExpanded: root.taskDetailsExpanded(taskCode)
            readonly property bool editorsActive: !viewPooled && taskList.hoverEditorsEnabled && taskRow.hovered

            Component {
                id: taskBusyActionComponent
                Controls.BusyIndicator {
                    uiTheme: root.theme
                    width: 22
                    height: 22
                    running: true
                }
            }
            Component {
                id: taskErrorActionComponent
                Controls.MaterialIcon {
                    name: "error"
                    size: 16
                    color: root.theme.error
                }
            }
            Component {
                id: taskConflictActionComponent
                Controls.CompactIconButton {
                    theme: root.theme
                    iconName: "sync_problem"
                    iconColor: root.theme.error
                    toolTip: qsTr("Resolve server conflict")
                    onClicked: root.openMenu(this, taskDelegate.taskCode, taskDelegate.parentKey, taskDelegate.process, taskDelegate.dirty, true, taskDelegate.isNew)
                }
            }
            Component {
                id: taskOverflowActionComponent
                Controls.CompactIconButton {
                    theme: root.theme
                    iconName: "more_vert"
                    toolTip: qsTr("Task actions")
                    onClicked: root.openMenu(this, taskDelegate.taskCode, taskDelegate.parentKey, taskDelegate.process, taskDelegate.dirty, taskDelegate.conflict, taskDelegate.isNew)
                }
            }

            width: Math.max(taskList.width, root.tableGeometry.width)
            height: groupHeader.height + taskContent.height
            spacing: 0

            Loader {
                id: groupHeader
                width: parent.width
                height: taskDelegate.groupFirst ? 28 : 0
                active: !taskDelegate.viewPooled && taskDelegate.groupFirst
                sourceComponent: Frame.FrameView {
                    theme: root.theme
                    property var lastGroupScene: ({
                            nodes: []
                        })
                    scene: {
                        if (taskDelegate.viewPooled || !taskDelegate.groupFirst)
                            return lastGroupScene;
                        const next = TaskTable.group({
                            key: taskDelegate.groupKey,
                            label: taskDelegate.group,
                            color: taskDelegate.groupColor,
                            count: taskDelegate.groupCount,
                            collapsed: taskDelegate.groupCollapsed
                        }, width);
                        lastGroupScene = next;
                        return next;
                    }
                    onEvent: action => tasksController.toggle_group_collapsed(action.value)
                }
            }

            Item {
                id: taskContent
                width: parent.width
                readonly property real expandedGap: taskDelegate.detailsExpanded ? 6 : 0
                readonly property real bodyHeight: !taskDelegate.detailsExpanded ? 58 : 58 + expandedDetails.detailImplicitHeight
                height: taskDelegate.groupCollapsed ? 0 : bodyHeight + expandedGap
                visible: !taskDelegate.groupCollapsed
                Tasks.TaskBrowserRow {
                    id: taskRow
                    table: root
                    record: taskDelegate
                    viewport: taskList
                    controller: tasksController
                    taskModel: advancedTaskTableModel
                    menu: taskMenu
                    releaseCoordinator: editorReleaseCoordinator
                    busyAction: taskBusyActionComponent
                    conflictAction: taskConflictActionComponent
                    errorAction: taskErrorActionComponent
                    overflowAction: taskOverflowActionComponent
                }

                Loader {
                    id: expandedDetails
                    objectName: "taskExpandedDetails_" + taskDelegate.taskCode
                    readonly property real detailImplicitHeight: item ? item.implicitHeight : 0
                    active: !taskDelegate.groupCollapsed && taskDelegate.detailsExpanded
                    visible: active
                    x: 0
                    y: taskRow.height
                    width: parent.width
                    height: active ? detailImplicitHeight : 0

                    sourceComponent: Component {
                        TaskHiddenDetails {
                            readonly property var editorRecord: {
                                const revision = taskDelegate.process + taskDelegate.status + taskDelegate.assigned + taskDelegate.supervisor + taskDelegate.priority + taskDelegate.milestoneCode;
                                return advancedTaskTableModel.get(taskDelegate.index);
                            }
                            theme: root.theme
                            controller: tasksController
                            taskCode: taskDelegate.taskCode
                            parentKey: taskDelegate.parentKey
                            process: taskDelegate.process
                            context: taskDelegate.context
                            processChoices: editorRecord.processChoices || []
                            isNew: taskDelegate.isNew
                            status: taskDelegate.status
                            statusChoices: editorRecord.statusChoices || []
                            assigned: taskDelegate.assigned
                            assignedLabel: taskDelegate.assignedLabel
                            assignedAvatar: taskDelegate.assignedAvatar
                            userChoices: editorRecord.userChoices || []
                            supervisor: taskDelegate.supervisor
                            supervisorLabel: taskDelegate.supervisorLabel
                            supervisorChoices: editorRecord.supervisorChoices || []
                            priority: taskDelegate.priority
                            priorityLabel: taskDelegate.priorityLabel
                            priorityChoices: editorRecord.priorityChoices && editorRecord.priorityChoices.length > 1 ? editorRecord.priorityChoices : tasksController.taskPriorityChoices
                            milestoneCode: taskDelegate.milestoneCode
                            milestoneLabel: taskDelegate.milestoneLabel
                            milestoneChoices: editorRecord.milestoneChoices || []
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
            }
        }

        footer: Item {
            width: taskList.width
            height: 8
        }

        ScrollBar.horizontal: Controls.ScrollBar {
            theme: root.theme
            flickableTarget: taskList
        }
        ScrollBar.vertical: Controls.ScrollBar {
            theme: root.theme
            flickableTarget: taskList
        }
    }
    Controls.InitialBatchPresentation {
        id: initialTaskTablePresentation
        objectName: "initialTaskTablePresentation"
        view: taskList
        blocked: tasksController.advancedBusy
    }

    TaskBulkBar {
        id: bulkBar
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: footer.top
        height: implicitHeight
        theme: root.theme
        onDeleteRequested: root.confirmTaskDelete("", true)
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
            anchors.fill: parent
            theme: root.theme
            scene: WorkspaceUI.footer({
                loaded: tasksController.advancedLoadedCount,
                total: tasksController.advancedTotalCount,
                visible: advancedTaskModel.count(),
                filtered: tasksController.advancedFiltersActive,
                processes: tasksController.advancedProcessCount,
                checked: tasksController.advancedCheckedCount,
                busy: tasksController.advancedBusy,
                more: tasksController.advancedHasMore,
                reserveModes: true
            }, width, typeof localizationController === "undefined" ? "en" : localizationController.current_language)
            onEvent: action => {
                if (action.type === "more")
                    tasksController.load_more_advanced();
                else if (action.type === "clear")
                    tasksController.clear_advanced_checked();
            }
        }
    }

    Label {
        anchors.centerIn: taskList
        visible: !tasksController.advancedBusy && advancedTaskModel.count() === 0
        text: tasksController.advancedEmptyMessage
        color: root.theme.secondaryText
        font.family: root.theme.fontFamily
        font.pointSize: Controls.Typography.body
    }
    Connections {
        target: tasksController
        function onTaskDraftCreated(taskCode) {
            const next = Object.assign({}, root.expandedTaskDetails);
            next[String(taskCode || "")] = true;
            root.expandedTaskDetails = next;
            Qt.callLater(function () {
                for (let row = 0; row < advancedTaskTableModel.count(); ++row) {
                    if (String(advancedTaskTableModel.get(row).taskCode || "") === String(taskCode || "")) {
                        taskList.positionViewAtIndex(row, ListView.Contain);
                        break;
                    }
                }
            });
        }
        function onTaskDraftRemoved(taskCode) {
            const key = String(taskCode || "");
            const next = Object.assign({}, root.expandedTaskDetails);
            delete next[key];
            root.expandedTaskDetails = next;
        }
    }
    ActionMenu {
        id: taskMenu
        parent: Overlay.overlay
        theme: root.theme
        preferredWidth: 210
        actions: TaskMenus.row({
            recordEditor: true,
            notes: true,
            hasTask: !root.menuIsNew,
            dirty: root.menuDirty,
            pending: tasksController.advancedDirtyCount > 0,
            creating: root.menuIsNew,
            conflict: root.menuConflict,
            busy: tasksController.advancedDeleting,
            checked: tasksController.advancedCheckedCount
        })
        onTriggered: function (command) {
            if (command === "open")
                tasksController.open_object(root.menuParentKey);
            else if (command === "notes")
                tasksController.open_notes(root.menuParentKey, root.menuProcess, root.menuTaskCode);
            else if (command === "edit")
                tasksController.begin_edit_code(root.menuTaskCode);
            else if (command === "discard")
                tasksController.discard_advanced_changes(root.menuTaskCode);
            else if (command === "server-version")
                tasksController.resolve_advanced_conflict(root.menuTaskCode, "server");
            else if (command === "keep-mine")
                tasksController.resolve_advanced_conflict(root.menuTaskCode, "mine");
            else if (command === "delete")
                root.confirmTaskDelete(root.menuTaskCode, false);
            else if (command === "delete-checked")
                root.confirmTaskDelete("", true);
        }
    }
}

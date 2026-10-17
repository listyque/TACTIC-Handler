import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls
import "tactic_frame" as Frame
import "features/objects" as Objects
import "tactic_frame/features/objects/inspector.ui.mjs" as UI

Rectangle {
    id: root

    required property var theme
    required property var controller
    property var task: controller.currentTask
    property var objectInfo: controller.selectedObject
    property var related: controller.relatedTasks
    readonly property bool isProgress: processRecord().type === "progress"
    readonly property bool hasTask: String(task.code || "").length > 0
    readonly property int processRow: task.processRow === undefined || task.processRow === null ? -1 : Number(task.processRow)
    readonly property bool expanded: controller.taskExpanded
    signal editRequested(string taskCode)

    visible: controller.hasTarget
    implicitHeight: !visible ? 0 : inspectorLayout.implicitHeight + 12
    color: theme.surfaceContainerLow
    clip: true

    function objectInitials() {
        const words = String(objectInfo.title || "").trim().split(/\s+|_+/).filter(Boolean);
        if (!words.length)
            return "";
        return words.slice(0, 2).map(function (word) {
            return word.charAt(0).toUpperCase();
        }).join("");
    }

    function choiceIndex(values, selected) {
        const source = values || [];
        for (let index = 0; index < source.length; ++index) {
            if (String(source[index].value || "") === String(selected || ""))
                return index;
        }
        return -1;
    }

    function processRecord() {
        const processes = controller.processChoices || [];
        for (let index = 0; index < processes.length; ++index) {
            if (String(processes[index].value || "") === controller.process)
                return processes[index];
        }
        return {};
    }

    function taskTitle() {
        const context = String(task.context || "").trim();
        if (context && context !== controller.process)
            return context;
        return controller.processLabel + qsTr(" task");
    }

    function processMenuActions() {
        const actions = [
            {
                "header": true,
                "title": "Process and note context"
            }
        ];
        const processes = controller.processChoices;
        for (let i = 0; i < processes.length; ++i) {
            const process = processes[i];
            const noteCount = Number(process.count || 0);
            const processType = String(process.type || "");
            const typeLabel = processType === "built-in" ? qsTr("Built-in") : processType;
            const noteLabel = String(noteCount) + qsTr(noteCount === 1 ? " note" : " notes");
            const progressLabel = String(Number(process.approved || 0)) + " / " + String(Number(process.total || 0));
            actions.push({
                // Process labels are project data. Never translate them.
                "title": String(process.label || process.value || ""),
                "translate": false,
                "status": processType === "progress" ? qsTr("Related tasks") + " · " + progressLabel : typeLabel.length ? typeLabel + " · " + noteLabel : noteLabel,
                "statusTranslate": false,
                "icon": processType === "progress" ? "donut-small" : "",
                "accent": process.color || root.theme.action,
                "command": "process:" + process.value,
                "checked": process.value === controller.process
            });
        }
        return actions;
    }

    function taskMenuActions() {
        const actions = [
            {
                "header": true,
                "title": "Tasks for this process"
            }
        ];
        const choices = controller.taskChoices;
        for (let i = 0; i < choices.length; ++i) {
            const choice = choices[i];
            actions.push({
                "title": choice.primaryBranch ? choice.label + " · " + qsTr("Main") : choice.label,
                "status": choice.status,
                "translate": false,
                "statusTranslate": false,
                "icon": "task_alt",
                "avatarUrl": choice.avatarUrl || "",
                "avatarColor": choice.avatarColor || root.theme.action,
                "initials": choice.initials || "",
                "command": "task:" + choice.value,
                "badgeCount": Number(choice.noteCount || 0),
                "showZeroBadge": true,
                "checked": choice.selected === true
            });
        }
        return actions;
    }

    GridLayout {
        id: inspectorLayout
        columns: 1
        anchors.fill: parent
        anchors.leftMargin: 8
        anchors.rightMargin: 8
        anchors.topMargin: 5
        anchors.bottomMargin: 7
        rowSpacing: 5
        columnSpacing: 0

        Objects.ObjectInspectorQuick {
            id: taskSurface
            objectName: "taskInspectorTaskSurfaceHost"
            Layout.row: 2
            Layout.column: 0
            visible: root.expanded && !root.isProgress
            Layout.fillWidth: true
            Layout.preferredHeight: visible ? scene.height : 0
            theme: root.theme
            model: ({
                    hasTask: root.hasTask,
                    canCreate: root.processRow >= 0,
                    canEdit: root.processRow >= 0,
                    title: root.processRow >= 0 ? root.taskTitle() : "",
                    processLabel: root.controller.processLabel,
                    assignedLabel: root.task.assignedDisplay,
                    dirty: root.task.dirty === true,
                    busy: tasksController.busy,
                    status: root.task.status,
                    statuses: root.task.statusChoices,
                    assigned: root.task.assigned,
                    users: (root.task.userChoices || []).map(choice => Object.assign({}, userListModel.lookup('login', choice.value), choice)),
                    start: root.task.start,
                    end: root.task.end,
                    progress: root.task.progress,
                    validationError: root.task.validationError,
                    progressEditable: tasksController.progressSupported
                })
            onEvent: event => {
                if (event.type === "edit")
                    root.editRequested(String(root.task.code || ""));
                else if (event.type === "create")
                    root.controller.create_task_for_process();
                else if (event.type === "discard")
                    tasksController.discard_process_changes(root.processRow);
                else if (event.type === "save")
                    tasksController.save_process_changes(root.processRow);
                else if (event.type === "change")
                    tasksController.set_process_draft(root.processRow, event.field, event.value);
            }
        }
        Frame.FrameView {
            Layout.row: 2
            Layout.column: 0
            visible: root.expanded && root.isProgress
            Layout.fillWidth: true
            Layout.preferredHeight: visible ? scene.height : 0
            theme: root.theme
            scene: UI.related({
                state: root.related.state,
                count: (root.related.items || []).length,
                objectCount: root.related.objectCount,
                searchType: root.related.searchType,
                approved: root.processRecord().approved,
                total: root.processRecord().total,
                accent: root.processRecord().color
            }, width, typeof localizationController === "undefined" ? "en" : localizationController.current_language)
            models: ({
                    items: (root.related.items || []).map((record, index) => Object.assign({}, record, {
                            key: String(record.searchKey || index),
                            accent: root.processRecord().color
                        }))
                })
            describeRow: (list, record) => UI.relatedRow(record, list.width - 16, typeof localizationController === "undefined" ? "en" : localizationController.current_language)
        }

        WorkHoursSummary {
            objectName: "taskInspectorWorkHours"
            Layout.row: 1
            Layout.column: 0
            visible: root.hasTask
            Layout.fillWidth: true
            Layout.preferredHeight: visible ? (root.expanded ? 80 : 32) : 0
            theme: root.theme
            controller: workHoursController
            compact: !root.expanded
        }

        Frame.FrameView {
            id: contextHeader
            Layout.row: 0
            Layout.column: 0
            Layout.fillWidth: true
            Layout.preferredHeight: scene.height
            theme: root.theme
            scene: UI.context({
                title: root.objectInfo.title,
                typeTitle: root.objectInfo.type,
                previewUrl: root.objectInfo.previewUrl,
                initials: root.objectInitials(),
                expanded: root.expanded,
                taskCount: root.controller.taskChoices.length,
                process: root.controller.process,
                processLabel: root.controller.processLabel,
                processColor: root.processRecord().color,
                isProgress: root.isProgress,
                busy: root.controller.busy
            }, width, typeof localizationController === "undefined" ? "en" : localizationController.current_language)
            onEvent: (event, source) => {
                if (event.type === "toggle")
                    root.controller.toggle_task_expanded();
                else if (event.type === "preview")
                    root.controller.open_skey_preview(String(root.objectInfo.searchKey || ""));
                else if (event.type === "process-menu")
                    processMenu.toggleBelow(source);
                else if (event.type === "task-menu")
                    taskMenu.toggleBelow(source);
                else if (event.type === "refresh")
                    root.controller.refresh();
            }
        }
    }

    ActionMenu {
        id: processMenu
        parent: Overlay.overlay
        theme: root.theme
        preferredWidth: 320
        actions: root.processMenuActions()
        onTriggered: command => {
            if (command.indexOf("process:") === 0)
                root.controller.set_process(command.slice(8));
        }
    }

    ActionMenu {
        id: taskMenu
        parent: Overlay.overlay
        theme: root.theme
        preferredWidth: 330
        actions: root.taskMenuActions()
        onTriggered: command => {
            if (command.indexOf("task:") === 0)
                root.controller.select_task(command.slice(5));
        }
    }
}

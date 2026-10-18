import QtQuick
import QtQuick.Controls
import "../../../controls" as Controls
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/files/workspace/submit.ui.mjs" as UI

Controls.Dialog {
    id: root
    readonly property string language: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language
    property bool restrictAccess: false
    property bool reopenFiles: false
    property bool guardResolved: false
    property string unchangedPolicy: "revert"
    property string taskQuery: ""
    readonly property var frameModel: ({
            draft: draft,
            review: review,
            context: context,
            notice: notice,
            error: state.error,
            busy: controller.busy,
            ready: ready,
            selectionAll: selectionAll,
            exceptions: exceptions,
            selectedTasks: selectedTasks,
            taskChoices: taskChoices,
            taskStatus: taskStatus,
            taskCount: taskRows.length,
            restrictAccess: restrictAccess,
            reopenFiles: reopenFiles,
            guardResolved: guardResolved,
            unchangedPolicy: unchangedPolicy,
            taskQuery: taskQuery
        })
    objectName: "workspaceSubmitDialog"
    required property var controller
    readonly property var state: controller.view_data
    readonly property var review: state.review || ({})
    readonly property var context: state.submit_review || ({})
    property string draft: ""
    property bool selectionAll: true
    property var exceptions: []
    property var selectedTasks: []
    property string taskStatus: ""
    property bool tasksInitialized: false
    property bool closeAfterSave: false
    property string savedToken: ""
    property string notice: ""
    readonly property bool ready: !controller.busy && Boolean(review.number) && review.editable && !review.active_transfer && !review.integration && !review.rebase_required && review.waiting_uploads !== null
    readonly property var taskChoices: [
        {
            value: "",
            label: qsTr("Keep current status")
        }
    ].concat(selectedTasks.length ? (selectedTasks[0].statuses || []).filter(choice => selectedTasks.every(task => (task.statuses || []).some(item => item.value === choice.value))) : [])
    readonly property var taskRows: selectedTasks.concat((context.tasks?.items || []).filter(task => !selectedTasks.some(item => item.code === task.code)))
    function initializeTasks() {
        if (tasksInitialized || !visible || controller.busy || context.change !== state.change.code)
            return;
        tasksInitialized = true;
        selectedTasks = context.tasks?.linked || [];
        const updates = state.change.task_status_updates || [];
        taskStatus = updates.length && updates.every(item => item.status === updates[0].status) ? updates[0].status : "";
    }
    onReadyChanged: initializeTasks()
    function settings() {
        return {
            description: draft,
            restricted: restrictAccess,
            task_codes: selectedTasks.map(task => task.code),
            task_status_updates: taskStatus ? selectedTasks.map(task => ({
                        code: task.code,
                        status: taskStatus,
                        revision: task.revision
                    })) : []
        };
    }
    function selectFile(path, checked) {
        const values = exceptions.filter(item => item !== path);
        if (checked !== selectionAll)
            values.push(path);
        if (values.length > 1000) {
            notice = qsTr("Select at most 1000 exceptions, or switch Select all.");
            return;
        }
        exceptions = values;
    }
    function save(close) {
        closeAfterSave = close;
        savedToken = context.saved || "";
        controller.action("submit_save", Object.assign(settings(), {
            review_revision: String(review.edit_revision)
        }));
    }
    parent: Overlay.overlay
    modal: true
    draggable: true
    closePolicy: Popup.CloseOnEscape
    width: Math.min(960, parent ? parent.width - 24 : 960)
    height: Math.min(1000, parent ? parent.height - 24 : 1000)
    title: qsTr("Submit changelist #%1").arg(state.change.number || "")
    onAboutToShow: {
        x = Qt.binding(() => Math.max(0, (parent.width - width) / 2));
        y = Qt.binding(() => Math.max(0, (parent.height - height) / 2));
        draft = state.description;
        tasksInitialized = false;
        selectionAll = true;
        exceptions = [];
        selectedTasks = [];
        taskStatus = "";
        notice = "";
        closeAfterSave = false;
        restrictAccess = Boolean(state.change.restricted);
        reopenFiles = false;
        guardResolved = false;
        unchangedPolicy = "revert";
        taskQuery = "";
        Qt.callLater(initializeTasks);
    }
    onContextChanged: {
        if (closeAfterSave && context.saved && context.saved !== savedToken) {
            closeAfterSave = false;
            root.close();
        }
        initializeTasks();
    }
    function selectTask(code, checked) {
        const row = taskRows.find(row => row.code === code);
        if (!row)
            return;
        if (checked && selectedTasks.length >= 100) {
            notice = qsTr("Choose at most 100 linked tasks");
            return;
        }
        selectedTasks = checked ? selectedTasks.concat([row]) : selectedTasks.filter(task => task.code !== code);
        taskStatus = "";
    }
    function dispatch(action) {
        if (action.type === "reject") {
            reject();
            return;
        }
        if (controller.busy)
            return;
        if (action.type === "field") {
            if (["draft", "taskQuery", "taskStatus", "unchangedPolicy", "guardResolved", "reopenFiles", "restrictAccess"].includes(action.key))
                root[action.key] = action.value;
        } else if (action.type === "selectFile")
            selectFile(action.key, action.value);
        else if (action.type === "selectAll") {
            selectionAll = action.value;
            exceptions = [];
        } else if (action.type === "selectTask")
            selectTask(action.key, action.value);
        else if (action.type === "filesMore")
            controller.action("review_more", {});
        else if (action.type === "shelf")
            controller.action("submit_shelf_files", {
                shelf: action.value
            });
        else if (action.type === "shelvesMore")
            controller.action("submit_shelves", {
                after: context.shelves.after
            });
        else if (action.type === "shelfFilesMore")
            controller.action("submit_shelf_files", {
                shelf: context.shelf_files.change,
                after: context.shelf_files.after
            });
        else if (action.type === "searchTasks")
            controller.action("submit_tasks", {
                query: taskQuery
            });
        else if (action.type === "tasksMore")
            controller.action("submit_tasks", {
                query: taskQuery,
                after: context.tasks.after
            });
        else if (action.type === "save" && ready)
            save(true);
        else if (action.type === "apply" && ready)
            save(false);
        else if (action.type === "submit" && ready && (selectionAll || exceptions.length)) {
            controller.action("submit", Object.assign(settings(), {
                review_revision: String(review.edit_revision),
                submit_options: {
                    selection_all: selectionAll,
                    selection_paths: exceptions,
                    guard_resolved: guardResolved,
                    reopen: reopenFiles,
                    unchanged: unchangedPolicy
                }
            }));
            close();
        }
    }
    footer: null
    contentItem: Frame.FrameView {
        theme: root.theme
        scene: UI.describe(root.frameModel, width, height, root.language)
        models: ({
                pendingFiles: root.review.items || [],
                shelfFiles: root.context.shelf_files?.items || [],
                tasks: root.taskRows
            })
        describeRow: (list, record) => list.source === "tasks" ? UI.taskRow(root.frameModel, record, list.width - 16) : UI.fileRow(root.frameModel, record, list.width - 16, root.language, list.source === "shelfFiles")
        onEvent: action => root.dispatch(action)
    }
}

import QtQuick
import "../../.." as TH
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/files/workspace/changelist.ui.mjs" as UI

Item {
    id: root
    readonly property string language: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language
    objectName: "fileWorkspaceChangelistDetails"
    required property var theme
    required property string windowId
    property var controller: fileWorkspaceController
    readonly property var workspaceState: controller.view_data
    property var openedChange: ({})
    property string changeCode: ""
    readonly property var change: workspaceState.change.code === changeCode || !changeCode ? Object.assign({}, details.info || {}, workspaceState.change) : openedChange
    readonly property var details: workspaceState.change_details?.change === changeCode ? workspaceState.change_details : ({})
    readonly property string windowTitle: qsTr("Changelist #%1").arg(change.number || changeCode)
    property string requestId: ""
    property int requestNumber: 0
    readonly property bool loading: details.request !== requestId
    property string draft: ""
    property bool editing: false
    property bool showFiles: true
    property bool showShelves: true
    property bool showTasks: true
    readonly property bool sameChange: workspaceState.change.code === changeCode
    readonly property bool editable: sameChange && change.state === "pending" && change.owner === controller.current_user && change.workspace === workspaceState.workspace && change.depot_writable !== false && change.editable !== false && !change.active_transfer && !change.active_bulk && !change.integration && !controller.busy
    readonly property bool dirty: draft !== String(change.description || "")
    Component.onCompleted: {
        openedChange = change;
        changeCode = String(change.code || "");
        draft = String(change.description || "");
        load();
    }
    onDetailsChanged: if (details.request === requestId && details.info) {
        openedChange = details.info;
        if (!editing)
            draft = String(details.info.description || "");
    }
    onChangeChanged: if (!editing || draft === String(change.description || "")) {
        draft = String(change.description || "");
        editing = false;
    }
    function close() {
        windowModel.close_window(root.windowId);
    }
    function command(name) {
        root.close();
        root.controller.details_command(name);
    }
    function load(section, after, shelf, shelfRevision) {
        requestId = String(Date.now()) + ":" + String(++requestNumber);
        let values = {
            change: changeCode,
            request: requestId
        };
        if (section) {
            values.section = section;
            values.edit_revision = String(change.edit_revision);
            values.after = after || "";
        }
        if (shelf)
            values.shelf = shelf;
        if (shelfRevision !== undefined)
            values.shelf_revision = String(shelfRevision);
        controller.action("changelist_details", values);
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe({
            change: root.change,
            changeCode: root.changeCode,
            details: root.details,
            draft: root.draft,
            dirty: root.dirty,
            editable: root.editable,
            editing: root.editing,
            loading: root.loading,
            sameChange: root.sameChange,
            error: root.workspaceState.error,
            showFiles: root.showFiles,
            showShelves: root.showShelves,
            showTasks: root.showTasks
        }, width, height, root.language)
        views: ({
                files: {
                    component: filesTable
                },
                shelves: {
                    component: shelvesTable
                },
                tasks: {
                    component: tasksTable
                }
            })
        onEvent: (action, source) => {
            if (action.type === "close")
                root.close();
            else if (action.type === "refresh" && !root.dirty)
                root.load();
            else if (action.type === "edit" && root.editable)
                root.editing = true;
            else if (action.type === "description" && root.editable && root.editing)
                root.draft = action.value;
            else if (action.type === "save" && root.editable && root.dirty) {
                root.controller.set_value("description", root.draft);
                root.controller.action("update_change", {});
            } else if (action.type === "actions")
                menu.toggleBelowItem(source);
            else if (action.type === "toggle") {
                if (action.key === "files")
                    root.showFiles = !root.showFiles;
                else if (action.key === "shelves")
                    root.showShelves = !root.showShelves;
                else if (action.key === "tasks")
                    root.showTasks = !root.showTasks;
            } else if (action.type === "shelf")
                root.load("shelf_files", "", action.value);
            else if (action.type === "load") {
                if (action.section === "files")
                    root.load("files", root.details.files.after);
                else if (action.section === "shelves")
                    root.load("shelves", root.details.shelves.after);
                else if (action.section === "shelf_files")
                    root.load("shelf_files", root.details.shelf_files.after, root.details.shelf_files.change, root.details.shelf_files.edit_revision);
            }
        }
    }
    Component {
        id: filesTable
        FileWorkspaceChangelistFiles {
            objectName: "changelistFiles"
            theme: root.theme
            rows: root.details.files?.items || []
        }
    }
    Component {
        id: shelvesTable
        FileWorkspaceChangelistFiles {
            objectName: "changelistShelvedFiles"
            theme: root.theme
            rows: root.details.shelf_files?.items || []
        }
    }
    Component {
        id: tasksTable
        FileWorkspaceChangelistFiles {
            objectName: "changelistLinkedTasks"
            theme: root.theme
            tasks: true
            rows: root.details.tasks?.items || []
            emptyText: root.details.tasks?.unavailable ? qsTr("Task access is restricted") : qsTr("No linked tasks")
        }
    }
    TH.ActionMenu {
        id: menu
        objectName: "fileWorkspaceDetailsMenu"
        theme: root.theme
        actions: [
            {
                title: qsTr("Submit"),
                command: "submit",
                icon: "publish",
                enabled: root.editable && !root.dirty
            },
            {
                title: qsTr("Shelve"),
                command: "shelve",
                icon: "archive",
                enabled: root.editable && !root.dirty
            },
            {
                title: qsTr("Revert changelist"),
                command: "revert",
                icon: "undo",
                enabled: root.editable && !root.dirty
            }
        ]
        onTriggered: name => root.command(name)
    }
}

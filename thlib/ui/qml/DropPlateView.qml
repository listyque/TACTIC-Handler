import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import "tactic_frame" as Frame
import "tactic_frame/features/files/drop_plate.ui.mjs" as UI

Item {
    id: root
    required property var theme
    property var controller: dropPlateController
    property var checkin: checkinOutController
    property string contextGroupId: ""
    property string filter: ""
    property string filterMode: "name"
    property bool dragging: false
    property int modelRevision: 0
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var allRows: {
        modelRevision;
        return dropPlateModel.records();
    }
    readonly property var visibleRows: allRows.filter(record => UI.matches(record, filter, filterMode))
    readonly property var frameModel: ({
            native: true,
            busy: controller.busy,
            count: controller.count,
            recursive: controller.recursive,
            groupCheckin: controller.groupCheckin,
            keepFileName: checkin.keepFileName,
            filter,
            filterMode,
            dragging,
            hasTarget: checkin.hasObject,
            targetTitle: checkin.currentObject.title || "",
            hasChecked: controller.hasChecked,
            canQueue: checkin.actionAvailable,
            processes: checkin.processes,
            process: checkin.process,
            context: checkin.context,
            error: controller.error
        })
    function refreshRows() {
        modelRevision++;
    }
    Connections {
        target: dropPlateModel
        function onContentReplaced() {
            Qt.callLater(root.refreshRows);
        }
        function onDataChanged() {
            Qt.callLater(root.refreshRows);
        }
        function onRowsRemoved() {
            Qt.callLater(root.refreshRows);
        }
        function onRowsInserted() {
            Qt.callLater(root.refreshRows);
        }
        function onModelReset() {
            Qt.callLater(root.refreshRows);
        }
    }
    function dispatch(action, source) {
        if (action.type === "files")
            fileDialog.open();
        else if (action.type === "directory")
            folderDialog.open();
        else if (action.type === "paste")
            controller.paste_paths();
        else if (action.type === "templates")
            windowModel.show_window("matching_templates");
        else if (action.type === "clear")
            controller.clear();
        else if (action.type === "preference") {
            if (action.field === "recursive")
                controller.set_recursive(action.value);
            else if (action.field === "groupCheckin")
                controller.set_group_checkin(action.value);
            else if (action.field === "keepFileName")
                checkin.set_keep_file_name(action.value);
        } else if (action.type === "filter")
            filter = action.value;
        else if (action.type === "filterMode")
            filterMode = action.value;
        else if (action.type === "process")
            checkin.set_process(action.value);
        else if (action.type === "context")
            checkin.set_context(action.value);
        else if (action.type === "queue")
            controller.add_selected_to_queue();
        else if (action.type === "check")
            controller.toggle_checked_id(action.key);
        else if (action.type === "remove")
            controller.remove_id(action.key);
        else if (action.type === "menu") {
            contextGroupId = action.key;
            if (action.value)
                itemMenu.openAt(source, action.value.x, action.value.y);
            else
                itemMenu.toggleBelow(source);
        }
    }
    function menuAction(command) {
        if (command === "open")
            controller.open_file(contextGroupId);
        else if (command === "folder")
            controller.show_folder(contextGroupId);
        else if (command === "copy")
            controller.copy_path(contextGroupId, false);
        else if (command === "copy_all")
            controller.copy_path(contextGroupId, true);
        else if (command === "remove" && !controller.busy)
            controller.remove_id(contextGroupId);
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe(root.frameModel, width, height, root.language)
        models: ({
                groups: root.visibleRows
            })
        describeRow: (list, record) => UI.row(root.frameModel, record, list.width - 16, root.language)
        onEvent: (action, source) => root.dispatch(action, source)
    }
    DropArea {
        anchors.fill: parent
        enabled: !root.controller.busy
        onEntered: drag => {
            root.dragging = true;
            drag.acceptProposedAction();
        }
        onExited: root.dragging = false
        onDropped: drop => {
            root.dragging = false;
            if (drop.hasUrls) {
                root.controller.add_paths(drop.urls);
                drop.acceptProposedAction();
            }
        }
    }
    FileDialog {
        id: fileDialog
        title: qsTr("Add files to Drop Plate")
        fileMode: FileDialog.OpenFiles
        onAccepted: root.controller.add_paths(selectedFiles)
    }
    FolderDialog {
        id: folderDialog
        title: qsTr("Add directory to Drop Plate")
        onAccepted: root.controller.add_paths([selectedFolder])
    }
    ActionMenu {
        id: itemMenu
        objectName: "dropPlateFileMenu"
        theme: root.theme
        parent: Overlay.overlay
        preferredWidth: 220
        actions: UI.actions(root.frameModel)
        onTriggered: command => root.menuAction(command)
    }
}

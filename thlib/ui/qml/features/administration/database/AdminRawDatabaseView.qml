import QtQuick
import QtQuick.Dialogs
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/administration/database/raw.ui.mjs" as UI
import "../../../tactic_frame/features/administration/database/raw.state.mjs" as State
import "../../../tactic_frame/features/administration/admin.document.mjs" as Document

Item {
    id: root
    objectName: "rawDatabasePage"
    required property var theme
    required property var controller
    property bool saveActionsInHeader: false
    property string language: "en"
    property var ui: State.initial()
    readonly property bool allowCreate: false
    readonly property bool allowReload: true
    readonly property bool allowSave: true
    readonly property string createText: ""
    readonly property string createObjectName: ""
    readonly property bool canCreateDocument: false
    readonly property bool canReloadDocument: Document.policy(frameModel).reload
    readonly property var frameModel: ({
            ready: !!controller.identity,
            identity: controller.identity,
            canWrite: controller.canWrite,
            canLoad: true,
            busy: controller.busy,
            dirty: controller.dirty,
            uncertain: controller.uncertain,
            error: controller.error,
            catalog: controller.catalog,
            metadata: controller.metadata,
            rows: controller.rows,
            columns: controller.metadata.columns || [],
            controlHeight: theme.controlHeight
        })
    readonly property var frameScene: body.scene
    function cellScene(grid, record, row, column) {
        return UI.cell(grid, record, row, column, frameModel, ui, language);
    }
    function toolbarScene(width) {
        return UI.toolbar(frameModel, ui, width, language);
    }
    function dispatch(action) {
        const result = State.transition(ui, frameModel, action);
        ui = result.ui;
        for (const command of result.commands) {
            switch (command.type) {
            case "select":
                controller.select(command.identity);
                break;
            case "add":
                controller.new_document();
                break;
            case "deleteRow":
                controller.toggle_delete(command.row);
                break;
            case "cell":
                controller.open_cell(command.row, command.name);
                break;
            case "page":
                controller.page(command.offset);
                break;
            case "drop":
                controller.drop_table(command.name);
                break;
            case "export":
                exportDialog.open();
                break;
            case "save":
                controller.save();
                break;
            case "reload":
                controller.reload(command.force);
                break;
            case "discard":
                controller.discard();
                break;
            case "focusGrid":
                Qt.callLater(() => body.focusGrid(command.grid, command.row, command.column, command.id));
                break;
            default:
                throw Error("Unsupported Raw database command: " + command.type);
            }
        }
    }
    function requestSave() {
        dispatch({
            type: "save"
        });
    }
    function reloadDocument() {
        dispatch({
            type: "reload"
        });
    }
    function discardChanges() {
        dispatch({
            type: "discard"
        });
    }
    Frame.FrameView {
        id: toolbar
        width: root.width
        height: root.saveActionsInHeader ? 0 : 38
        visible: !root.saveActionsInHeader
        theme: root.theme
        scene: root.saveActionsInHeader ? ({
                nodes: []
            }) : root.toolbarScene(width)
        onEvent: action => root.dispatch(action)
    }
    Frame.FrameView {
        id: body
        y: toolbar.height ? toolbar.height + 8 : 0
        width: root.width
        height: Math.max(1, root.height - y)
        theme: root.theme
        models: ({
                rows: root.controller.tableModel
            })
        describeCell: root.cellScene
        scene: UI.describe(root.frameModel, root.ui, width, height, root.language)
        onEvent: action => root.dispatch(action)
    }
    FileDialog {
        id: exportDialog
        title: UI.translate("Export CSV", root.language)
        fileMode: FileDialog.SaveFile
        nameFilters: ["CSV (*.csv)"]
        onAccepted: root.controller.export_csv(selectedFile)
    }
}

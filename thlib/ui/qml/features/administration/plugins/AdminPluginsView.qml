pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Dialogs
import "../../.."
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/administration/plugins/plugins.ui.mjs" as UI

Item {
    id: root
    required property var theme
    required property var controller
    property string language: "en"
    property bool saveActionsInHeader: true
    property var ui: UI.initial()
    signal helpRequested
    readonly property var frameModel: ({
            catalog: controller.catalog,
            document: controller.document,
            metadata: controller.metadata,
            identity: controller.identity,
            canWrite: controller.canWrite,
            busy: controller.busy,
            dirty: controller.dirty,
            uncertain: controller.writeUncertain,
            error: controller.error
        })
    function toolbarScene(width) {
        return UI.toolbar(frameModel, width, language);
    }
    function dispatch(event) {
        const result = UI.transition(ui, frameModel, event);
        ui = result.ui;
        for (const command of result.commands) {
            switch (command.type) {
            case "help":
                root.helpRequested();
                break;
            case "select":
                controller.focus(command.identity);
                break;
            case "request":
                controller.perform(command.action, command.values);
                break;
            case "field":
                controller.set_field(command.field, command.value);
                break;
            case "save":
                controller.save();
                break;
            case "discard":
                controller.discard();
                break;
            case "error":
                controller.fail(command.value);
                break;
            case "upload":
                filePicker.packageUpload = !!command.package;
                filePicker.replaceUpload = !!command.replace;
                filePicker.open();
                break;
            }
        }
    }
    function requestSave() {
        dispatch({
            type: "save"
        });
    }
    function discardChanges() {
        dispatch({
            type: "discard"
        });
    }
    function rowScene(list, record) {
        return UI.row(list, record, frameModel, language);
    }
    Frame.FrameView {
        id: toolbar
        width: root.width
        height: root.saveActionsInHeader ? 0 : 40
        visible: !root.saveActionsInHeader
        theme: root.theme
        scene: root.saveActionsInHeader ? ({
                nodes: []
            }) : root.toolbarScene(width)
        onEvent: event => root.dispatch(event)
    }
    Frame.FrameView {
        y: toolbar.height ? toolbar.height + UI.toolbarGap : 0
        width: root.width
        height: Math.max(0, root.height - y)
        theme: root.theme
        models: ({
                plugins: UI.catalog(root.frameModel, root.ui),
                files: root.controller.metadata.files || [],
                sourceEditor: root.controller.sourceEditor
            })
        describeRow: root.rowScene
        scene: UI.describe(root.frameModel, root.ui, width, height, root.language)
        onEvent: event => root.dispatch(event)
    }
    FileDialog {
        id: filePicker
        property bool packageUpload: false
        property bool replaceUpload: false
        title: packageUpload ? qsTr("Install plugin ZIP") : qsTr("Upload plugin file")
        nameFilters: packageUpload ? [qsTr("ZIP archives (*.zip)")] : [qsTr("All files (*)")]
        onAccepted: root.controller.upload(selectedFile, packageUpload, replaceUpload)
    }
}

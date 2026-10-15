import QtQuick
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/administration/layouts/layout.ui.mjs" as UI
import "../../../tactic_frame/features/administration/layouts/layout.state.mjs" as State

Item {
    id: root
    required property var theme
    required property var controller
    property string language: typeof localizationController !== "undefined" ? localizationController.current_language : qsTr("Search Types") === "Search Types" ? "en" : "ru"
    property bool saveActionsInHeader: false
    property var ui: State.initial()
    readonly property var frameModel: UI.model(controller.model, ui)
    readonly property var frameScene: body.scene
    readonly property var rows: Object.assign({}, UI.models(frameModel), {
        sourceEditor: controller.sourceEditor
    })
    readonly property bool allowSave: true
    readonly property bool allowReload: true
    readonly property bool allowCreate: false
    readonly property bool canReloadDocument: !controller.busy && frameModel.canLoad
    function rowScene(list, record) {
        return UI.row(list, record, frameModel, ui, language);
    }
    function toolbarScene(width) {
        return UI.toolbar(frameModel, ui, width, language);
    }
    function synchronize() {
        const blank = State.blankXml(frameModel);
        if (blank) {
            controller.initialize_xml(blank);
            return;
        }
        ui = State.synchronize(ui, frameModel);
    }
    function dispatch(event) {
        const result = State.transition(ui, frameModel, event);
        ui = result.ui;
        controller.set_presentation_dirty(State.pending(ui));
        for (const command of result.commands) {
            switch (command.type) {
            case "xml":
                controller.set_xml(command.value);
                break;
            case "context":
                controller.set_context(command.field, command.value);
                break;
            case "source":
                controller.select_source(command.value);
                break;
            case "newView":
                controller.new_view(command.view, command.xml);
                break;
            case "check":
                controller.check();
                break;
            case "save":
                controller.save();
                break;
            case "discard":
                controller.discard();
                break;
            case "reload":
                controller.reload(command.force);
                break;
            case "openView":
                controller.open_view();
                break;
            case "help":
                if (typeof appController !== "undefined")
                    appController.open_window("help");
                break;
            default:
                throw Error("Unsupported layout command: " + command.type);
            }
            if (!controller.model.error)
                ui = State.completed(ui, command);
        }
        controller.set_presentation_dirty(State.pending(ui));
    }
    function requestSave() {
        root.forceActiveFocus();
        dispatch({
            type: "save"
        });
    }
    function discardChanges() {
        dispatch({
            type: "discard"
        });
    }
    function reloadDocument() {
        dispatch({
            type: "reload"
        });
    }
    Connections {
        target: root.controller
        function onStateChanged() {
            root.synchronize();
        }
    }
    Component.onCompleted: synchronize()
    Frame.FrameView {
        id: toolbar
        width: root.width
        height: root.saveActionsInHeader ? 0 : 38
        visible: !root.saveActionsInHeader
        theme: root.theme
        scene: root.toolbarScene(width)
        onEvent: action => root.dispatch(action)
    }
    Frame.FrameView {
        id: body
        y: root.saveActionsInHeader ? 0 : 46
        width: root.width
        height: root.height - y
        theme: root.theme
        scene: UI.describe(root.frameModel, root.ui, width, height, root.language)
        models: root.rows
        describeRow: root.rowScene
        onEvent: action => root.dispatch(action)
    }
}

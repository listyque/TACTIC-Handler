import QtQuick
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/administration/workflow/process_rules.ui.mjs" as UI
import "../../../tactic_frame/features/administration/workflow/process_rules.state.mjs" as State

Item {
    id: root
    required property var theme
    property var controller: administrationController.workflowEditor.rulesEditor
    property string language: typeof localizationController !== "undefined" ? localizationController.current_language : qsTr("Search Types") === "Search Types" ? "en" : "ru"
    property var ui: State.initial()
    readonly property var frameModel: ({
            ready: controller.document.rules !== undefined,
            canWrite: controller.canWrite,
            canLoad: !!controller.identity,
            busy: controller.busy,
            dirty: controller.dirty,
            uncertain: controller.writeUncertain,
            error: controller.error,
            message: "",
            identity: controller.identity,
            document: {
                rules: controller.document.rules || []
            },
            metadata: controller.metadata,
            selected: controller.selectedIndex,
            rule: controller.selectedRule
        })
    readonly property var frameScene: body.scene
    readonly property var rows: UI.models(frameModel, ui)
    function rowScene(list, record) {
        return UI.row(list, record, frameModel, language);
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
                controller.select_rule(command.index);
                break;
            case "add":
                controller.add_rule(command.kind);
                break;
            case "remove":
                controller.remove_rule();
                break;
            case "field":
                controller.set_rule_field(command.field, command.value);
                break;
            case "target":
                controller.set_target(command.process, command.enabled === true ? String(command.value) : command.status, command.enabled === true || command.value === true);
                break;
            case "output":
                controller.set_output(command.process, command.value);
                break;
            case "items":
                controller.show_item_page(command.offset);
                break;
            case "object":
                controller.open_object(command.key);
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
            case "close":
                controller.request_close();
                break;
            default:
                throw Error("Unsupported process dependencies command: " + command.type);
            }
        }
    }
    function requestSave() {
        dispatch({
            type: "save"
        });
    }
    function requestClose() {
        dispatch({
            type: "close"
        });
    }
    function selectVisibleRule() {
        if (["trigger", "notification"].indexOf(ui.page) >= 0 && controller.selectedRule.kind !== ui.page)
            controller.select_rule((controller.document.rules || []).findIndex(row => row.kind === ui.page));
    }
    Connections {
        target: root.controller
        function onStateChanged() {
            root.selectVisibleRule();
        }
    }
    Component.onCompleted: selectVisibleRule()
    Frame.FrameView {
        id: toolbar
        width: root.width
        height: 38
        theme: root.theme
        scene: root.toolbarScene(width)
        onEvent: action => root.dispatch(action)
    }
    Frame.FrameView {
        id: body
        y: 46
        width: root.width
        height: root.height - y
        theme: root.theme
        scene: UI.describe(root.frameModel, root.ui, width, height, root.language)
        models: root.rows
        describeRow: root.rowScene
        onEvent: action => root.dispatch(action)
    }
}

import QtQuick
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/administration/users/users.ui.mjs" as UI
import "../../../tactic_frame/features/administration/users/users.state.mjs" as State

Item {
    id: root
    required property var theme
    required property var controller
    property bool saveActionsInHeader: false
    property string language: "en"
    property var ui: State.initial()
    readonly property string createText: UI.translate("Create user", language)
    readonly property string createObjectName: "adminCreateDocument"
    readonly property bool allowCreate: true
    readonly property bool allowReload: true
    readonly property bool allowSave: true
    readonly property bool canCreateDocument: State.permissions(frameModel).create
    readonly property bool canReloadDocument: State.permissions(frameModel).reload
    readonly property string currentIdentity: controller.identity
    readonly property var frameModel: ({
            draft: controller.document.login === undefined ? null : controller.document,
            identity: controller.identity,
            profile: UI.profile(controller.document, controller.identity ? controller.profile : null),
            ready: controller.metadata.fields !== undefined,
            canWrite: controller.canWrite,
            canLoad: true,
            busy: controller.busy,
            dirty: controller.dirty,
            uncertain: controller.uncertain,
            error: controller.error,
            message: controller.message,
            userCount: controller.usersModel.count(),
            groupCount: controller.groupsModel.count()
        })
    onCurrentIdentityChanged: ui = Object.assign({}, ui, {
        page: "profile"
    })

    function rowScene(list, record) {
        return UI.row(list, record, frameModel, ui, language);
    }
    function toolbarScene(width) {
        return UI.toolbar(frameModel, ui, width, language);
    }
    function dispatch(action) {
        const result = State.transition(ui, frameModel, action);
        ui = result.ui;
        for (const command of result.commands) {
            switch (command.type) {
            case "create":
                controller.new_document();
                break;
            case "select":
                controller.select(command.login);
                break;
            case "query":
                controller.set_query(command.value);
                break;
            case "showRetired":
                controller.set_show_retired(command.value);
                break;
            case "field":
                controller.set_field(command.field, command.value);
                break;
            case "member":
                controller.set_group(command.name, command.value);
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
            case "error":
                controller.fail(command.text);
                break;
            case "focus":
                Qt.callLater(() => body.focusControl(command.id));
                break;
            default:
                throw Error("Unsupported Users command: " + command.type);
            }
        }
    }
    function createDocument() {
        dispatch({
            type: "create"
        });
    }
    function reloadDocument() {
        dispatch({
            type: "reload"
        });
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

    Frame.FrameView {
        id: toolbar
        objectName: "adminUserToolbar"
        width: root.width
        height: root.saveActionsInHeader ? 0 : UI.metrics.control
        visible: !root.saveActionsInHeader
        theme: root.theme
        scene: root.saveActionsInHeader ? ({
                nodes: []
            }) : root.toolbarScene(width)
        onEvent: action => root.dispatch(action)
    }
    Frame.FrameView {
        id: body
        y: toolbar.height ? toolbar.height + UI.metrics.toolbarGap : 0
        width: root.width
        height: Math.max(1, root.height - y)
        theme: root.theme
        models: ({
                users: root.controller.usersModel,
                groups: root.controller.groupsModel
            })
        describeRow: root.rowScene
        scene: UI.describe(root.frameModel, root.ui, width, height, root.language)
        onEvent: action => root.dispatch(action)
    }
}

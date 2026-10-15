import QtQuick
import "tactic_frame" as Frame
import "tactic_frame/features/administration/groups/groups.ui.mjs" as UI
import "tactic_frame/features/administration/groups/groups.state.mjs" as State

Item {
    id: root
    required property var theme
    required property var controller
    required property var groupsModel
    required property var membersModel
    property bool saveActionsInHeader: false
    property string language: "en"
    property var ui: State.initial()
    readonly property string editorPage: ui.page
    readonly property var frameModel: ({
        draft: controller.draft.name === undefined ? null : controller.draft,
        ready: controller.groupCatalogLoaded, canWrite: controller.canManage, canLoad: controller.canManage,
        busy: controller.busy, dirty: controller.dirty, uncertain: controller.groupUncertain,
        error: controller.error, message: controller.groupMessage,
        groupCount: groupsModel.count(), userCount: membersModel.count(), memberCount: controller.memberCount
    })
    readonly property bool canCreateGroup: State.permissions(frameModel).create
    readonly property bool canReloadGroup: State.permissions(frameModel).reload
    function rowScene(list, record) {return UI.row(list, record, frameModel, ui, language)}
    function toolbarScene(width) {return UI.toolbar(frameModel, ui, width, language, false)}
    function dispatch(action) {
        const result = State.transition(ui, frameModel, action)
        ui = result.ui
        for (const command of result.commands) {
            switch (command.type) {
            case "create": controller.new_group(); break
            case "query": controller.set_user_query(command.value); break
            case "select": controller.select_group(command.code); break
            case "field": controller.set_field(command.field, command.value); break
            case "member": controller.set_member(command.login, command.value); break
            case "save": controller.save(); break
            case "reload": controller.reload(command.force); break
            case "discard": controller.discard(); break
            case "error": controller.set_group_error(command.text); break
            case "focus": Qt.callLater(() => body.focusControl(command.id)); break
            default: throw Error("Unsupported Groups command: " + command.type)
            }
        }
    }
    function createGroup() {dispatch({type: "create"})}
    function reloadGroup() {dispatch({type: "reload"})}
    function requestSave() {dispatch({type: "save"})}
    function discardChanges() {dispatch({type: "discard"})}
    Frame.FrameView {
        id: toolbar
        objectName: "adminGroupToolbar"
        x: 0; y: 0; width: root.width; height: root.saveActionsInHeader ? 0 : UI.metrics.control
        visible: !root.saveActionsInHeader
        theme: root.theme
        scene: root.saveActionsInHeader ? ({nodes: []}) : root.toolbarScene(width)
        onEvent: action => root.dispatch(action)
    }
    Frame.FrameView {
        id: body
        x: 0; y: toolbar.height ? toolbar.height + UI.metrics.toolbarGap : 0
        width: root.width; height: Math.max(1, root.height - y)
        theme: root.theme; models: ({groups: root.groupsModel, members: root.membersModel})
        describeRow: root.rowScene
        scene: UI.describe(root.frameModel, root.ui, width, height, root.language)
        onEvent: action => root.dispatch(action)
    }
}

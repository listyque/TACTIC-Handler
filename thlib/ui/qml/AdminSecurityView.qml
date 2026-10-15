import QtQuick
import "tactic_frame" as Frame
import "tactic_frame/features/administration/security/security.ui.mjs" as UI
import "tactic_frame/features/administration/security/security.state.mjs" as State
import "tactic_frame/features/administration/admin.document.mjs" as Document

Item {
    id: root
    required property var theme
    required property var controller
    property bool saveActionsInHeader: false
    property string language: "en"
    property var ui: State.initial()
    property bool reloading: false
    readonly property bool allowCreate: false
    readonly property bool allowReload: true
    readonly property bool allowSave: true
    readonly property string createText: ""
    readonly property string createObjectName: ""
    readonly property bool canCreateDocument: false
    readonly property bool canReloadDocument: Document.policy(frameModel).reload
    readonly property var frameModel: ({
        ready: controller.document.groups !== undefined,
        canWrite: controller.canWrite, canLoad: true, busy: controller.busy,
        dirty: controller.dirty, uncertain: controller.writeUncertain,
        pendingText: State.pending(ui), error: controller.error, message: controller.message,
        group: controller.selectedGroup, groups: controller.groupCatalog,
        groupDocument: controller.groupDocument, records: controller.rules,
        attributes: controller.selectedAttributes, selected: controller.selectedRule,
        metadata: controller.metadata, matrixRows: controller.matrixTargets,
        matrixGroups: controller.matrixGroups,
        selectedCell: ui.selectedCell ? controller.matrix.cell_at(ui.selectedCell.row, ui.selectedCell.column) : null,
        xmlSource: controller.groupDocument.xml || "", jsonSource: controller.ruleText,
        inheritedSource: (controller.metadata.globalDefaultRulesByLevel || {})[controller.groupDocument.accessLevel] || ""
    })
    readonly property var rows: UI.models(frameModel, ui, language)
    readonly property var frameScene: body.scene
    function rowScene(list, record) {return UI.row(list, record, frameModel, ui, language)}
    function cellScene(grid, record, row, column) {return UI.cell(grid, record, row, column, frameModel, ui, language)}
    function toolbarScene(width) {return UI.toolbar(frameModel, ui, width, language)}
    function synchronize(force) {ui = State.synchronize(ui, frameModel, force)}
    function dispatch(action) {
        const result = State.transition(ui, frameModel, action)
        ui = result.ui
        controller.set_presentation_dirty(State.pending(ui))
        for (const command of result.commands) {
            switch (command.type) {
            case "filterMatrix": controller.matrix.filter(ui.scope, ui.query, ui.groupQuery); break
            case "group": controller.select_group(command.value); synchronize(true); break
            case "matrix": {
                const cell = controller.matrix.cell_at(command.row, command.column)
                if (!cell.custom && !cell.locked) controller.matrix.set_allowed(command.row, command.column, !cell.checked)
                break
            }
            case "inherit": controller.matrix.inherit(command.row, command.column); break
            case "focusGrid": Qt.callLater(() => body.focusGrid(command.grid, command.row, command.column, command.id)); break
            case "focus": Qt.callLater(() => {if (!body.focusControl(command.id)) body.focusControl(command.fallback)}); break
            case "selectRule": controller.select_rule(command.index); synchronize(true); break
            case "addRule": controller.add_rule(command.scope); synchronize(true); break
            case "removeRule": controller.remove_rule(); synchronize(true); break
            case "attribute": controller.set_attribute(command.field, String(command.value)); break
            case "target": controller.set_target(command.attributes); break
            case "groupField": controller.set_group_field(command.field, command.value); break
            case "ruleAccess": controller.set_rule_access(command.index, command.value); break
            case "applyText":
                if (command.page === "rule") controller.apply_rule(command.text)
                else controller.apply_xml(command.text)
                if (!controller.error) synchronize(true)
                break
            case "save": controller.save(); break
            case "reload": reloading = true; controller.reload(command.force); break
            case "discard": controller.set_presentation_dirty(false); controller.discard(); synchronize(true); break
            default: throw Error("Unsupported Access rules command: " + command.type)
            }
        }
        controller.set_presentation_dirty(State.pending(ui))
    }
    function reloadDocument() {dispatch({type: "reload"})}
    function requestSave() {dispatch({type: "save"})}
    function discardChanges() {dispatch({type: "discard"})}
    Component.onCompleted: {controller.matrix.filter(ui.scope, ui.query, ui.groupQuery); synchronize(true)}
    Connections {
        target: root.controller
        function onRulesChanged() {
            if (root.reloading && !root.controller.busy) {
                root.reloading = false
                if (!root.controller.error) {root.synchronize(true); return}
            }
            root.synchronize(false)
        }
    }
    Frame.FrameView {
        id: toolbar
        width: root.width; height: root.saveActionsInHeader ? 0 : 38
        visible: !root.saveActionsInHeader; theme: root.theme
        scene: root.saveActionsInHeader ? ({nodes: []}) : root.toolbarScene(width)
        onEvent: action => root.dispatch(action)
    }
    Frame.FrameView {
        id: body
        y: toolbar.height ? toolbar.height + 8 : 0
        width: root.width; height: Math.max(1, root.height - y)
        theme: root.theme
        models: ({matrix: root.controller.matrix, rules: root.rows.rules, allRules: root.rows.allRules, targets: root.rows.targets})
        describeRow: root.rowScene; describeCell: root.cellScene
        scene: UI.describe(root.frameModel, root.ui, width, height, root.language)
        onEvent: action => root.dispatch(action)
    }
}

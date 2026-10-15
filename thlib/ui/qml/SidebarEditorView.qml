import QtQuick
import "tactic_frame" as Frame
import "tactic_frame/features/administration/sidebar/sidebar.ui.mjs" as UI
import "tactic_frame/features/administration/sidebar/sidebar.state.mjs" as State

Item {
    id: root
    required property var theme
    readonly property var controller: sidebarEditorController
    property bool saveActionsInHeader: false
    property string language: typeof localizationController !== "undefined" ? localizationController.current_language : "en"
    property var ui: State.initial()
    readonly property var frameModel: ({ready: controller.ready, projectTitle: controller.projectTitle, canWrite: controller.canEdit, canLoad: true,
        busy: controller.busy, dirty: controller.dirty, uncertain: controller.uncertain, error: controller.error,
        selected: controller.selectedRow, entry: controller.selectedEntry, source: controller.sidebarSource, previewGroup: controller.previewGroup,
        entries: controller.entryRecords.filter(row => row.entryVisible), groups: controller.groupRecords, xml: controller.xmlText,
        previewOptions: controller.previewGroupOptions, typeOptions: controller.searchTypes, presetOptions: controller.searchPresetOptions,
        resultOptions: controller.resultViewOptions, widgetOptions: controller.widgetTypeOptions,
        layoutOptions: controller.layoutPresets ? controller.layoutPresets.options : [], shelfOptions: controller.scriptShelf ? controller.scriptShelf.assignmentOptions : []})
    readonly property var frameScene: body.scene
    function toolbarScene(width) {return UI.toolbar(frameModel, ui, width, language)}
    function rowScene(list, record) {return UI.row(list, record, frameModel, ui, language)}
    function applyText() {
        for (const key of Object.keys(ui.text)) {
            controller.update_selected(key, ui.text[key])
            if (controller.error) return false
        }
        if (ui.xml !== null) {
            controller.set_xml_text(ui.xml)
            controller.apply_xml()
            if (controller.error) return false
        }
        ui = State.transition(ui, frameModel, {type: "applied"}).ui
        controller.set_presentation_dirty(false)
        return true
    }
    function dispatch(action) {
        const result = State.transition(ui, frameModel, action)
        for (const command of result.commands) {
            if (!["reload", "discard", "help"].includes(command.type) && !applyText()) return
            switch (command.type) {
            case "apply": break
            case "select": controller.select_entry(command.index); break
            case "toggle": controller.toggle_folder(command.index); break
            case "source": controller.set_sidebar_source(command.value); break
            case "preview": controller.set_preview_group(command.value); break
            case "mode": controller.set_mode(command.value); break
            case "back": break
            case "field": controller.update_selected(command.field, command.value); break
            case "group": controller.set_group_allowed(command.code, command.value); break
            case "add": controller.add_entry(command.value); break
            case "move": controller.move_selected(command.value); break
            case "delete": controller.delete_selected(); break
            case "search": controller.open_search(); break
            case "groups": controller.open_group_manager(); break
            case "save": controller.save(); break
            case "reload": controller.set_presentation_dirty(false); controller.reload(); break
            case "discard": controller.set_presentation_dirty(false); controller.discard(); break
            case "help": windowModel.open_help("sidebar_editor"); break
            default: throw Error("Unsupported Sidebar command: " + command.type)
            }
            if (controller.error && !["reload", "discard"].includes(command.type)) return
            result.ui = State.completed(result.ui, command)
        }
        ui = result.ui
        controller.set_presentation_dirty(State.pending(ui))
        if (["select", "field"].includes(action.type)) Qt.callLater(controller.refresh_search_presets)
    }
    function requestSave() {dispatch({type: "save"})}
    function discardChanges() {dispatch({type: "discard"})}
    function reloadDocument() {dispatch({type: "reload"})}
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
        width: root.width; height: Math.max(1, root.height - y); theme: root.theme
        scene: UI.describe(root.frameModel, root.ui, width, height, root.language)
        models: ({entries: root.frameModel.entries, groups: root.frameModel.groups.map((row, index) => Object.assign({index}, row))}); describeRow: root.rowScene
        onEvent: action => root.dispatch(action)
    }
}

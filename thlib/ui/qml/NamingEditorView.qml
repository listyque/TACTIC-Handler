import QtQuick
import "tactic_frame" as Frame
import "tactic_frame/features/administration/naming/naming.ui.mjs" as UI
import "tactic_frame/features/administration/naming/naming.state.mjs" as State

Item {
    id: root
    required property var theme
    property var controller: namingEditorController
    property bool embedded: false
    property bool saveActionsInHeader: false
    property string language: typeof localizationController !== "undefined" ? localizationController.current_language : qsTr("Naming rules") === "Naming rules" ? "en" : "ru"
    property var ui: State.initial()
    readonly property var record: controller.selectedRule
    readonly property var frameModel: ({ready: Object.keys(record).length > 0, canWrite: controller.canWrite, canLoad: !!controller.currentObject.searchType,
        busy: controller.busy, dirty: controller.dirty, uncertain: controller.writeUncertain, error: controller.error, message: controller.message,
        identity: controller.isNew ? "" : String(record.code || ""), document: record, rules: controller.frameRules,
        searchType: controller.currentObject.searchType || "", project: controller.currentObject.projectCode || "", targetTitle: controller.currentObject.title || "",
        typeMode: controller.typeMode, previewMode: "local", items: [], itemCount: 0, itemOffset: 0,
        sample: {file: controller.sampleFile, version: controller.sampleVersion, process: controller.previewProcess, context: controller.previewContext, fileType: controller.sampleFileType, key: controller.currentObject.searchKey || ""},
        previewResults: [{mode: "local", path: controller.previewPath, directory: controller.previewDirectory, file: controller.previewFilename, status: controller.previewStatus}]
    })
    readonly property var frameScene: body.scene
    readonly property bool allowCreate: true
    readonly property bool allowReload: true
    readonly property bool allowSave: true
    readonly property bool canCreateDocument: controller.canWrite && !controller.busy && !controller.writeUncertain
    readonly property bool canReloadDocument: !controller.busy
    readonly property string createText: qsTr("Create naming rule")
    readonly property string createObjectName: "namingCreate"
    function toolbarScene(width) {return UI.toolbar(frameModel, ui, width, language)}
    function rowScene(list, record) {return UI.row(list, record, frameModel, language)}
    function applyText() {
        for (const key of Object.keys(ui.text)) controller.set_field(key, ui.text[key])
        ui = State.transition(ui, frameModel, {type: "applied"}).ui
        controller.set_presentation_dirty(false)
    }
    function dispatch(action) {
        const result = State.transition(ui, frameModel, action)
        ui = result.ui
        for (const command of result.commands) {
            if (["reload", "discard"].indexOf(command.type) < 0) applyText()
            switch(command.type) {
            case "apply": break
            case "field": controller.set_field(command.field, command.value); break
            case "sample":
                switch(command.field) {
                case "file": controller.set_sample_file(command.value); break
                case "version": controller.set_sample_version(command.value); break
                case "process": controller.set_preview_process(command.value); break
                case "context": controller.set_preview_context(command.value); break
                case "fileType": controller.set_sample_file_type(command.value); break
                }
                break
            case "select": {const row = controller.frameRules.find(row => row.identity === command.identity); if (row) controller.select_rule(row.index); break}
            case "create": controller.create_rule(); break
            case "duplicate": controller.duplicate_rule(); break
            case "reload": controller.reload(); break
            case "discard": controller.set_presentation_dirty(false); controller.reset(); break
            case "save": controller.save(); break
            default: throw Error("Unsupported Naming command: " + command.type)
            }
            ui = State.completed(ui, command)
        }
        controller.set_presentation_dirty(State.pending(ui))
    }
    function reloadDocument() {dispatch({type: "reload"})}
    function requestSave() {dispatch({type: "save"})}
    function discardChanges() {dispatch({type: "discard"})}
    onVisibleChanged: if (!visible && controller) applyText()
    Component.onDestruction: if (controller) applyText()
    Frame.FrameView {id: toolbar; width: root.width; height: root.saveActionsInHeader ? 0 : 38; visible: !root.saveActionsInHeader; theme: root.theme; scene: root.toolbarScene(width); onEvent: action => root.dispatch(action)}
    Frame.FrameView {id: body; x: 0; y: root.saveActionsInHeader ? 0 : 46; width: root.width; height: root.height-y; theme: root.theme; scene: UI.describe(root.frameModel, root.ui, width, height, root.language); models: ({namingRules: root.controller.frameRules}); describeRow: root.rowScene; onEvent: action => root.dispatch(action)}
}

import QtQuick
import "controls" as Controls
import "tactic_frame" as Frame
import "tactic_frame/features/administration/search_types/search_types.ui.mjs" as UI
import "tactic_frame/features/administration/search_types/search_types.state.mjs" as State

Item {
    id: root
    objectName: "adminSearchTypesView"
    readonly property var previewDialog: imageDialog
    required property var theme
    required property var controller
    property bool saveActionsInHeader: false
    property bool creationOnly: false
    property var namingController: null
    property var namingView: null
    property string projectCode: ""
    property string language: typeof localizationController !== "undefined" ? localizationController.current_language : qsTr("Search Types") === "Search Types" ? "en" : "ru"
    property string title: qsTr("Search Types")
    property string description: ""
    property string confirmationMessage: ""
    property var ui: State.initial()
    readonly property string page: ui.page
    readonly property bool namingPage: ui.page === "naming"
    readonly property bool creatingType: controller.document.hasPipeline !== undefined
    readonly property bool namingLocked: !!namingController && (namingController.busy || namingController.dirty)
    readonly property bool presentationVisible: visible && !!Window.window && Window.window.visible
    readonly property bool allowCreate: !creationOnly && !namingLocked && !namingPage
    readonly property bool allowReload: !creationOnly && !namingLocked && !namingPage
    readonly property bool allowSave: !namingPage && (!creationOnly || ui.page === "ready" || !!controller.identity)
    readonly property bool canCreateDocument: allowCreate && controller.canWrite && !controller.busy && !controller.dirty
    readonly property bool canReloadDocument: allowReload && !controller.busy
    readonly property string createText: qsTr("New Search Type")
    readonly property string createObjectName: "adminCreateDocument"
    readonly property var frameModel: ({ready: Object.keys(controller.document).length > 0, canWrite: controller.canWrite && controller.metadata.tableAvailable !== false,
        canLoad: true, busy: controller.busy || !!namingController && namingController.busy, dirty: controller.dirty, uncertain: controller.writeUncertain, error: controller.error, message: "",
        identity: controller.identity, document: controller.document, metadata: controller.metadata, catalog: controller.catalog,
        creationOnly: root.creationOnly, namingLocked: root.namingLocked, relationshipGraph: controller.relationshipGraph,
        previewUrl: String(controller.previewUrl || ""), previewStaged: !!controller.document.previewPath, previewQueued: controller.previewQueued, previewError: "",
        confirmationText: root.confirmationMessage
    })
    readonly property var frameScene: body.scene
    readonly property var rows: ({types: UI.records(frameModel, ui), fields: UI.existing(frameModel, ui)})
    signal openWorkflowRequested(string identity)
    signal createWorkflowRequested()
    function rowScene(list, record) {return UI.row(list, record, frameModel, ui, language)}
    function toolbarScene(width) {return UI.toolbar(frameModel, ui, width, language)}
    function dispatch(action) {
        const result = State.transition(ui, frameModel, action)
        ui = result.ui
        for (const command of result.commands) {
            switch(command.type) {
            case "field": controller.set_field(command.field, command.value); break
            case "page":
                if (command.value === "naming" && (!namingController || !namingController.begin_search_type(projectCode, controller.identity, controller.document.title || controller.identity))) return
                break
            case "select": controller.select(command.identity); break
            case "create": controller.new_document(); break
            case "save": controller.save(); break
            case "reload": controller.reload(command.force); break
            case "discard": controller.discard(); break
            case "addField": if (!controller.add_column(command.name, command.columnType)) return; break
            case "removeDraft": controller.remove_column(command.index); break
            case "removeField": controller.set_column_removed(command.name, (controller.document.removedColumns || []).indexOf(command.name) < 0); break
            case "preview": imageDialog.open(); break
            case "clearPreview": controller.set_preview_path(""); break
            case "queue": if (typeof appController !== "undefined") appController.open_window("commit_queue"); break
            case "workflow": if (command.identity) root.openWorkflowRequested(command.identity); else root.createWorkflowRequested(); break
            default: throw Error("Unsupported Search Types command: " + command.type)
            }
            ui = State.completed(ui, command, frameModel)
        }
    }
    function requestSave() {dispatch({type: "save"})}
    function discardChanges() {dispatch({type: "discard"})}
    function createDocument() {dispatch({type: "create"})}
    function reloadDocument() {dispatch({type: "reload"})}
    onPresentationVisibleChanged: controller.set_presentation_visible(presentationVisible)
    Component.onCompleted: {controller.set_presentation_visible(presentationVisible); ui = State.synchronize(ui, frameModel)}
    Component.onDestruction: {if (controller) {controller.set_presentation_visible(false)}}
    Connections {
        target: root.controller
        function onStateChanged() {
            root.ui = State.synchronize(root.ui, root.frameModel)
            if (root.namingPage && root.namingController && !root.controller.busy && root.controller.identity && root.controller.identity !== root.namingController.currentObject.searchType)
                if (!root.namingController.begin_search_type(root.projectCode, root.controller.identity, root.controller.document.title || root.controller.identity)) root.ui = Object.assign({}, root.ui, {page: "summary"})
        }
    }
    Component {id: namingFactory; NamingEditorView {theme: root.theme; controller: root.namingController; language: root.language; embedded: true; Component.onCompleted: root.namingView = this; Component.onDestruction: root.namingView = null}}
    Controls.ImageFileDialog {id: imageDialog; objectName: "adminSearchTypePreviewDialog"; title: qsTr("Choose Search Type preview"); onImageSelected: (row, image) => root.controller.set_preview_path(image)}
    Frame.FrameView {id: toolbar; width: root.width; height: root.saveActionsInHeader ? 0 : 38; visible: !root.saveActionsInHeader; theme: root.theme; scene: root.toolbarScene(width); onEvent: action => root.dispatch(action)}
    Frame.FrameView {id: body; x: 0; y: root.saveActionsInHeader ? 0 : 46; width: root.width; height: root.height-y; theme: root.theme; scene: UI.describe(root.frameModel, root.ui, width, height, root.language); models: root.rows; views: ({naming: namingFactory}); describeRow: root.rowScene; onEvent: action => root.dispatch(action)}
}

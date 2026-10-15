import QtQuick
import "tactic_frame" as Frame
import "tactic_frame/features/administration/workflow/graph_editor.ui.mjs" as UI
import "tactic_frame/features/administration/workflow/graph_editor.state.mjs" as State

Item {
    id: root
    objectName: "adminGraphView"
    required property var theme
    required property var controller
    property bool saveActionsInHeader: false
    property string language: typeof localizationController !== "undefined" ? localizationController.current_language : qsTr("Search Types") === "Search Types" ? "en" : "ru"
    readonly property bool workflow: controller.mode === "workflow"
    readonly property string title: workflow ? qsTr("Workflow editor") : qsTr("Project schema")
    readonly property string description: ""
    readonly property string iconName: workflow ? "process" : "schema"
    readonly property string page: ui.page
    readonly property bool allowSave: true
    readonly property bool allowReload: true
    readonly property bool allowCreate: !workflow || !!controller.creationSearchType
    readonly property bool canCreateDocument: allowCreate && !controller.busy && !controller.writeUncertain && (controller.canWrite || !!controller.metadata.canCreate) && (!workflow || !controller.dirty)
    readonly property bool canReloadDocument: !controller.busy
    readonly property string createText: workflow ? qsTr("Create workflow") : qsTr("New Search Type")
    readonly property string createObjectName: workflow ? "adminCreateDocument" : "adminCreateSchemaType"
    property var ui: State.initial()
    property var deletionConfirmation: null
    readonly property var connection: workflow ? null : controller.connectionEditor
    readonly property var frameModel: ({mode: workflow ? "workflow" : "schema", ready: !!controller.document.xml, canWrite: controller.canWrite,
        canLoad: true, busy: controller.busy, dirty: controller.dirty, uncertain: controller.writeUncertain, pendingText: State.pending(ui),
        saveAllowed: !workflow || !!String(controller.document.name || "").trim(), error: controller.error, message: "", identity: controller.identity,
        document: controller.document, catalog: controller.catalog, metadata: controller.metadata, creationSearchType: controller.creationSearchType,
        nodes: controller.nodes, edges: controller.edges, selectedNode: controller.selectedNode, selectedNodes: controller.selectedNodes, selectedEdge: controller.selectedEdge,
        xml: controller.nativeXml, attributes: controller.attributesText, settings: controller.settingsText, processSettings: controller.processSettings,
        processKind: controller.processKind, processProperties: controller.processProperties, processDescription: controller.processDescription, processCatalog: controller.processCatalog,
        connection: connection ? connection.edge : {}, instance: connection ? connection.instance : "", instanceLinks: connection ? connection.instanceLinks : [],
        createColumns: connection ? connection.createColumns : false, columnCatalog: columnCatalog(), columnsBusy: connection ? connection.loading : false,
        columnsError: connection ? connection.error : "", confirmationDetails: connection ? connection.saveDetails : ""
    })
    readonly property var frameScene: body.scene
    readonly property var rows: UI.models(frameModel, ui, language)
    signal createSearchTypeRequested(real x, real y)
    signal nodeWorkflowsRequested()
    signal deleteSearchTypeRequested(string identity)
    function columnCatalog() {
        if (!connection) return {}
        const catalog = Object.assign({}, connection.columnCatalog), columns = connection.columns
        for (const identity of Object.keys(columns)) catalog[identity] = Object.assign({}, catalog[identity] || {}, {columns: columns[identity]})
        return catalog
    }
    function rowScene(list, record) {return UI.row(list, record, frameModel, ui, language)}
    function toolbarScene(width) {return UI.toolbar(frameModel, ui, width, language)}
    function showDeleteConfirmation() {
        if (!deletionConfirmation) {
            if (!root.Window.contentItem) return
            deletionConfirmation = deletionFactory.createObject(root.Window.contentItem, {theme: root.theme, controller: controller.deletionEditor})
        }
        deletionConfirmation.open()
    }
    function insertionPoint() {return body.graphCommand("adminGraphCanvas", {type: "point"}) || {x: 40, y: 40}}
    function dispatch(action) {
        const result = State.transition(ui, frameModel, action)
        ui = result.ui
        controller.set_presentation_dirty(State.pending(ui))
        for (const command of result.commands) {
            switch (command.type) {
            case "save": controller.save(); break
            case "reload": controller.reload(command.force); break
            case "discard": controller.discard(); break
            case "field": controller.set_field(command.field, command.value); break
            case "attribute": controller.set_attribute(command.key, String(command.value)); break
            case "setting": controller.set_process_setting(command.section, command.key, command.value); break
            case "description": controller.set_process_description(command.value); break
            case "selectNodes": controller.select_nodes(command.identities, command.primary || ""); break
            case "selectEdge": controller.select_edge(command.index); break
            case "clear": controller.clear_selection(); break
            case "moveNodes": controller.move_nodes(command.positions); break
            case "connect": controller.connect_nodes(command.from, command.to); break
            case "remove": controller.remove_selected(); break
            case "addNode": {
                const point = insertionPoint()
                controller.add_node(command.identity, command.kind, point.x, point.y)
                if (!controller.error) Qt.callLater(() => body.graphCommand("adminGraphCanvas", {type: "reveal"}))
                break
            }
            case "layout": controller.arrange_nodes(command.style); Qt.callLater(() => body.graphCommand("adminGraphCanvas", {type: "reset"})); break
            case "selectPipeline": controller.select(command.identity); break
            case "createWorkflow": controller.new_document(command.searchType || ""); break
            case "createType": {const point = insertionPoint(); root.createSearchTypeRequested(point.x, point.y); break}
            case "deleteType": root.deleteSearchTypeRequested(controller.selectedNode); break
            case "nodeWorkflows": root.nodeWorkflowsRequested(); break
            case "taskWorkflow": controller.open_task_workflow(); break
            case "dependencies": controller.rulesEditor.open(); break
            case "column": if (command.value) connection.set_column(command.key, command.value); break
            case "renameInstance": connection.rename_instance(command.value); break
            case "relationship": if (command.value === "many_to_many") connection.make_many_to_many(); else controller.set_attribute("relationship", command.value); break
            case "createColumns": connection.set_create_columns(command.value); break
            case "reverse": connection.reverse(); break
            case "restoreDirect": connection.restore_direct(); break
            case "refreshColumns": connection.refresh_columns(); break
            case "apply":
                if (command.key === "xml") controller.apply_xml(command.value)
                else if (command.key === "attributes") controller.apply_attributes(command.value)
                else if (command.key === "settings") controller.apply_settings(command.value)
                else if (command.key === "script") controller.set_process_setting("default", "script", command.value)
                if (!controller.error) ui = State.applied(ui, command.key)
                break
            default: throw Error("Unsupported graph command: " + command.type)
            }
            if (!controller.error) ui = State.completed(ui, command)
        }
        controller.set_presentation_dirty(State.pending(ui))
    }
    function requestSave() {dispatch({type: "save"})}
    function discardChanges() {dispatch({type: "discard"})}
    function createDocument() {dispatch({type: workflow ? "createWorkflow" : "createType", searchType: controller.creationSearchType})}
    function reloadDocument() {dispatch({type: "reload"})}
    Component {id: deletionFactory; AdminSchemaDeleteConfirmation {}}
    Component.onDestruction: if (deletionConfirmation) deletionConfirmation.destroy()
    Connections {
        target: root.controller
        function onSelectionChanged() {if (root.connection && root.visible) root.connection.load_columns()}
    }
    Frame.FrameView {id: toolbar; width: root.width; height: root.saveActionsInHeader ? 0 : 38; visible: !root.saveActionsInHeader; theme: root.theme; scene: root.toolbarScene(width); onEvent: action => root.dispatch(action)}
    Frame.FrameView {id: body; y: root.saveActionsInHeader ? 0 : 46; width: root.width; height: root.height-y; theme: root.theme; scene: UI.describe(root.frameModel, root.ui, width, height, root.language); models: root.rows; describeRow: root.rowScene; onEvent: action => root.dispatch(action)}
}

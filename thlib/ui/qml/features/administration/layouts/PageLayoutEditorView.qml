import QtQuick
import QtQuick.Window
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/administration/layouts/page.ui.mjs" as UI
import "../../../tactic_frame/features/administration/layouts/page.state.mjs" as State
import "../../../tactic_frame/features/administration/layouts/page.reports.mjs" as Reports
import "../../../tactic_frame/features/administration/layouts/page.links.mjs" as Links
import "../../table" as Tables
import "../../../controls" as Controls
import "../../.." as Shell

Item {
    id: root
    required property var theme
    required property var controller
    property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    // Copy the values once; nested traversal must not retain a QVariant property reference.
    readonly property var editorSnapshot: ({
            document: Object.assign({}, root.controller.document),
            metadata: Object.assign({}, root.controller.metadata),
            catalog: Array.from(root.controller.catalog)
        })
    property bool saveActionsInHeader: false
    property var ui: State.initial()
    property var canvasBoxes: []
    property var contexts: Object.create(null)
    property string previousDocument: ""
    readonly property string documentProject: root.editorSnapshot.metadata.project || ""
    onDocumentProjectChanged: {
        contexts = Object.create(null);
        previousDocument = "";
        ui = State.initial();
    }
    Keys.onPressed: event => {
        const focused = root.Window.window?.activeFocusItem;
        if (event.isAutoRepeat || (focused && focused.cursorPosition !== undefined))
            return;
        const action = State.shortcut(String.fromCharCode(event.key), !!(event.modifiers & (Qt.ControlModifier | Qt.MetaModifier)), !!(event.modifiers & Qt.ShiftModifier), !!(event.modifiers & Qt.AltModifier));
        if (action) {
            root.dispatch(action);
            event.accepted = true;
        }
    }
    readonly property var dataScope: Reports.scope(root.editorSnapshot.document, ui)
    readonly property string dataKey: JSON.stringify([root.editorSnapshot.metadata.sourceEpoch, dataScope])
    onDataKeyChanged: Qt.callLater(requestSource)
    function requestSource() {
        controller.load_source(dataScope.searchType, null, dataScope.recordKey, dataScope.editView || "edit");
    }
    readonly property string documentName: root.editorSnapshot.document.name || ""
    onDocumentNameChanged: {
        if (previousDocument) {
            contexts[previousDocument] = Links.context(ui);
            const names = Object.keys(contexts);
            if (names.length > 32)
                delete contexts[names[0]];
        }
        ui = Object.assign(State.initial(), contexts[documentName] || {});
        previousDocument = documentName;
        controller.set_presentation_dirty(false);
        Qt.callLater(revealSelection);
    }
    readonly property bool allowSave: true
    readonly property bool allowReload: true
    readonly property bool allowCreate: false
    readonly property bool canReloadDocument: !controller.busy
    readonly property var frameModel: UI.model({
        document: root.editorSnapshot.document,
        project: root.editorSnapshot.metadata.project || "",
        origin: root.editorSnapshot.metadata.origin || "",
        catalog: root.editorSnapshot.catalog,
        dirty: controller.dirty,
        busy: controller.busy,
        uncertain: controller.writeUncertain,
        canWrite: controller.canWrite,
        canLoad: true,
        checked: JSON.stringify(root.editorSnapshot.metadata.checkedDocument) === JSON.stringify(root.editorSnapshot.document),
        error: controller.error,
        sourceXml: root.editorSnapshot.metadata.sourceXml || "",
        searchTypes: root.editorSnapshot.metadata.searchTypes || [],
        dataSource: root.editorSnapshot.metadata.dataSource || {},
        dataBusy: root.editorSnapshot.metadata.dataBusy || false,
        dataError: root.editorSnapshot.metadata.dataError || ""
    }, ui)
    function toolbarScene(width) {
        return UI.toolbar(frameModel, ui, width, language);
    }
    function rowScene(list, row) {
        return UI.row(list, row, frameModel, ui, language);
    }
    function revealSelection() {
        if (ui.layersHidden || ui.preview || ui.source)
            return;
        const rows = UI.models(frameModel, ui).pageBlocks;
        body.focusListRow("pageBlocks", rows.findIndex(row => row.key === (ui.selected || "page")), "");
    }
    function dispatch(event) {
        if (event.type === "align")
            event = Object.assign({}, event, {
                boxes: canvasBoxes
            });
        const result = State.transition(ui, frameModel, event);
        ui = result.ui;
        if (["selection", "select", "togglePanel"].includes(event.type))
            Qt.callLater(revealSelection);
        controller.set_presentation_dirty(Object.keys(ui.text).length > 0);
        for (const command of result.commands) {
            switch (command.type) {
            case "source":
                controller.load_source(command.searchType, command.query, command.recordKey, command.editView || "edit");
                break;
            case "document":
                controller.replace_document(command.document);
                break;
            case "load":
                controller.select(command.name);
                break;
            case "create":
                controller.create(command.name, command.title);
                break;
            case "save":
                controller.save();
                break;
            case "discard":
                controller.discard();
                break;
            case "reload":
                controller.reload_document(command.force);
                break;
            case "check":
                break;
            case "open":
                controller.open_saved();
                break;
            case "card":
                administrationController.open_page_card(command.searchType, command.view);
                break;
            case "columns":
                administrationController.open_page_columns(command.searchType, command.view);
                break;
            case "linkedPage":
                administrationController.open_linked_page(command.name);
                break;
            default:
                throw Error("Unsupported page command: " + command.type);
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
    function reloadDocument() {
        dispatch({
            type: "reload"
        });
    }
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
        Frame.FrameViewport {
            id: bodyViewport
            target: body
        }
        scene: UI.describe(root.frameModel, root.ui, bodyViewport.size.width, bodyViewport.size.height, root.language)
        models: Object.assign({}, UI.models(root.frameModel, root.ui), {
            sourceEditor: root.controller.sourceEditor
        })
        describeRow: root.rowScene
        views: ({
                pageTools: {
                    component: toolsComponent,
                    nodeProps: true
                },
                pagePreview: {
                    component: previewComponent
                }
            })
        onEvent: action => root.dispatch(action)
    }
    Component {
        id: toolsComponent
        Item {
            id: menuOwner
            property var frameNode: ({})
            readonly property var menu: toolsMenu
            Controls.Button {
                id: toolsButton
                objectName: "pageEditorToolsButton"
                anchors.fill: parent
                theme: root.theme
                text: menuOwner.frameNode.label || ""
                icon.name: "more-vert"
                toolTip: text
                Accessible.name: toolTip
                onClicked: toolsMenu.openBelow(toolsButton)
            }
            Shell.ActionMenu {
                id: toolsMenu
                parent: root
                objectName: "pageEditorToolsMenu"
                theme: root.theme
                alignBelowRight: true
                actions: menuOwner.frameNode.actions || []
                onTriggered: command => root.dispatch(UI.toolEvent(command))
            }
        }
    }
    Component {
        id: previewComponent
        Loader {
            active: !!root.editorSnapshot.metadata.previewOwner
            sourceComponent: Tables.CustomLayoutView {
                language: root.language
                theme: root.theme
                services: root.editorSnapshot.metadata.previewOwner.services
                owner: root.editorSnapshot.metadata.previewOwner.owner
                previewItems: root.editorSnapshot.metadata.previewOwner.items
                controller: root.editorSnapshot.metadata.application
                columnsController: typeof columnsEditorController === "undefined" ? null : columnsEditorController
                users: typeof userController === "undefined" ? [] : userController.users
                administration: typeof administrationController === "undefined" ? null : administrationController
                editing: true
                canvasViewport: root.ui.canvas
                selectedBlocks: root.ui.selection
                multiSelect: root.ui.multiSelect
                snap: root.ui.snap
                onSelectionEdited: keys => root.dispatch({
                        type: "selection",
                        keys
                    })
                onCanvasBoxesEdited: boxes => root.canvasBoxes = boxes
                guides: !root.ui.preview
                selectedBlock: root.ui.preview ? "" : root.ui.selected
                onBlockSelected: key => root.dispatch({
                        type: "select",
                        key
                    })
                onGeometryEdited: (value, boxes) => root.dispatch({
                        type: "geometry",
                        value,
                        boxes
                    })
            }
        }
    }
}

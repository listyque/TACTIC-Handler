import QtQuick
import QtQuick.Window
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/administration/layouts/page.ui.mjs" as UI
import "../../../tactic_frame/features/administration/layouts/page.state.mjs" as State
import "../../../tactic_frame/features/administration/layouts/page.reports.mjs" as Reports
import "../../table" as Tables

Item {
    id: root
    required property var theme
    required property var controller
    property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    property bool saveActionsInHeader: false
    property var ui: State.initial()
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
    readonly property var dataScope: Reports.scope(controller.document, ui)
    readonly property string dataKey: JSON.stringify([controller.metadata.sourceEpoch, dataScope])
    onDataKeyChanged: Qt.callLater(requestSource)
    function requestSource() {
        controller.load_source(dataScope.searchType, null, dataScope.recordKey);
    }
    readonly property string documentName: controller.document.name || ""
    onDocumentNameChanged: {
        ui = State.initial();
        controller.set_presentation_dirty(false);
    }
    readonly property bool allowSave: true
    readonly property bool allowReload: true
    readonly property bool allowCreate: false
    readonly property bool canReloadDocument: !controller.busy
    readonly property var frameModel: UI.model({
        document: controller.document,
        catalog: controller.catalog,
        dirty: controller.dirty,
        busy: controller.busy,
        uncertain: controller.writeUncertain,
        canWrite: controller.canWrite,
        canLoad: true,
        checked: JSON.stringify(controller.metadata.checkedDocument) === JSON.stringify(controller.document),
        error: controller.error,
        searchTypes: controller.metadata.searchTypes || [],
        dataSource: controller.metadata.dataSource || {},
        dataBusy: controller.metadata.dataBusy || false,
        dataError: controller.metadata.dataError || ""
    }, ui)
    function toolbarScene(width) {
        return UI.toolbar(frameModel, ui, width, language);
    }
    function rowScene(list, row) {
        return UI.row(list, row, frameModel, ui, language);
    }
    function dispatch(event) {
        const result = State.transition(ui, frameModel, event);
        ui = result.ui;
        controller.set_presentation_dirty(Object.keys(ui.text).length > 0);
        for (const command of result.commands) {
            switch (command.type) {
            case "source":
                controller.load_source(command.searchType, command.query, command.recordKey);
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
        scene: UI.describe(root.frameModel, root.ui, width, height, root.language)
        models: UI.models(root.frameModel)
        describeRow: root.rowScene
        views: ({
                pagePreview: {
                    component: previewComponent
                }
            })
        onEvent: action => root.dispatch(action)
    }
    Component {
        id: previewComponent
        Loader {
            active: !!root.controller.metadata.previewOwner
            sourceComponent: Tables.CustomLayoutView {
                language: root.language
                theme: root.theme
                services: root.controller.metadata.previewOwner.services
                owner: root.controller.metadata.previewOwner.owner
                previewItems: root.controller.metadata.previewOwner.items
                controller: root.controller.metadata.application
                columnsController: typeof columnsEditorController === "undefined" ? null : columnsEditorController
                users: typeof userController === "undefined" ? [] : userController.users
                administration: typeof administrationController === "undefined" ? null : administrationController
                editing: true
                canvasViewport: root.ui.canvas
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

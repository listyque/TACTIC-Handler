import QtQuick
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/administration/columns/columns.ui.mjs" as UI
import "../../../tactic_frame/features/administration/columns/columns.state.mjs" as State

Item {
    id: root
    required property var theme
    required property string projectCode
    property bool canWrite: true
    property bool saveActionsInHeader: false
    property string language: typeof localizationController !== "undefined" ? localizationController.current_language : "en"
    readonly property var controller: columnsEditorController
    readonly property bool presentationVisible: visible && !!Window.window && Window.window.visible
    property var ui: State.initial()
    property string selectedCatalogIdentity: ""
    property string catalogXmlText: ""
    property string catalogXmlOriginal: ""
    property var catalogWizardData: ({})
    property bool catalogReloading: false
    property bool catalogSaving: false
    property string message: ""
    property string focusError: ""
    readonly property bool catalogDirty: catalogXmlText !== catalogXmlOriginal || State.pending(ui) || controller.catalogUncertain
    readonly property bool canReloadCatalog: !controller.busy
    readonly property var catalogRows: UI.records(frameModel, ui)
    readonly property var selectedCatalog: controller.definitionCatalog.find(row => row.identity === selectedCatalogIdentity) || ({})
    readonly property var elements: catalogWizardData.elements || []
    readonly property var definitionElements: catalogWizardData.definitionElements || []
    readonly property var element: elements.find(row => row.path === ui.path) || definitionElements.find(row => row.path === ui.path) || elements[0] || definitionElements[0] || ({})
    readonly property var frameModel: ({
            ready: !!selectedCatalog.identity,
            canWrite: canWrite,
            canLoad: true,
            busy: controller.busy,
            dirty: catalogDirty,
            uncertain: controller.catalogUncertain,
            error: focusError || controller.error,
            message: message,
            xml: catalogXmlText,
            records: controller.definitionCatalog,
            selected: selectedCatalog,
            wizard: catalogWizardData,
            elements: elements,
            definitionElements: definitionElements,
            element: element,
            typeOptions: controller.definitionCatalogSearchTypes,
            widgetOptions: controller.widget_options_for(element.widget || "", !!ui.showAllWidgets)
        })
    readonly property var frameScene: body.scene
    function toolbarScene(width) {
        return UI.toolbar(frameModel, ui, width, language);
    }
    function rowScene(list, record) {
        return UI.row(list, record, frameModel, ui);
    }
    function reloadCatalogWizard() {
        catalogWizardData = controller.catalog_wizard(catalogXmlText, selectedCatalog.view || "", selectedCatalog.searchType || "");
    }
    function updateCatalogWizardValue(path, field, value) {
        const changed = controller.update_catalog_wizard(catalogXmlText, path, field, String(value));
        if (!changed)
            return false;
        catalogXmlText = changed;
        message = "";
        reloadCatalogWizard();
        return true;
    }
    function selectCatalog(record, force) {
        if (!force && catalogDirty)
            return;
        selectedCatalogIdentity = record ? record.identity : "";
        focusError = "";
        catalogXmlText = record ? record.config : "";
        catalogXmlOriginal = catalogXmlText;
        reloadCatalogWizard();
        ui = State.selected(ui, elements, "");
    }
    function refreshCatalogSelection(force) {
        selectCatalog(catalogRows.find(row => row.identity === selectedCatalogIdentity) || catalogRows[0] || null, force);
    }
    function applyText() {
        const keys = Object.keys(ui.text).sort((a, b) => a === "xml" ? -1 : b === "xml" ? 1 : 0);
        for (const key of keys)
            if (!updateCatalogWizardValue(element.path, key, ui.text[key]))
                return false;
        ui = State.transition(ui, frameModel, {
            type: "applied"
        }).ui;
        return true;
    }
    function dispatch(event) {
        const result = State.transition(ui, frameModel, event);
        for (const command of result.commands) {
            if (!["reload", "discard", "xml"].includes(command.type) && !applyText())
                return;
            switch (command.type) {
            case "apply":
                break;
            case "filter":
                ui = result.ui;
                refreshCatalogSelection(false);
                break;
            case "select":
                selectCatalog(controller.definitionCatalog.find(row => row.identity === command.identity), false);
                break;
            case "column":
                break;
            case "mode":
                if (command.value === "simple")
                    reloadCatalogWizard();
                break;
            case "back":
                break;
            case "change":
                if (!updateCatalogWizardValue(element.path, command.field, command.value))
                    return;
                break;
            case "xml":
                catalogXmlText = command.value;
                message = "";
                break;
            case "save":
                catalogSaving = true;
                if (!controller.save_catalog_xml(Number(selectedCatalog.row), catalogXmlText))
                    catalogSaving = false;
                break;
            case "reload":
                catalogReloading = true;
                controller.reload_definition_catalog(projectCode);
                break;
            case "discard":
                catalogXmlText = catalogXmlOriginal;
                reloadCatalogWizard();
                break;
            default:
                throw Error("Unsupported Columns command: " + command.type);
            }
            result.ui = State.completed(result.ui, command, frameModel);
        }
        ui = result.ui;
    }
    function requestSave() {
        dispatch({
            type: "save"
        });
    }
    function reloadCatalog() {
        dispatch({
            type: "reload"
        });
    }
    function discardChanges() {
        dispatch({
            type: "discard"
        });
    }
    function applyRequestedFocus() {
        if (!presentationVisible || !controller.focusPending || !controller.definitionCatalogLoaded || catalogDirty)
            return;
        const type = controller.requestedSearchType, view = controller.requestedDefinitionTarget === "edit_definition" ? "edit_definition" : controller.requestedView;
        const source = State.definitionSource(controller.definitionCatalog, {
            searchType: type,
            view: view,
            column: controller.requestedName,
            code: controller.requestedDefinitionCode
        }, row => controller.catalog_wizard(row.config, row.view).elements);
        ui = Object.assign({}, ui, {
            query: "",
            searchType: type,
            editing: true
        });
        selectCatalog(source, true);
        if (!source && controller.requestedName)
            focusError = "Column definition was not found in saved configurations.";
        ui = State.selected(ui, elements, controller.requestedName);
        controller.consume_definition_focus();
    }
    onProjectCodeChanged: {
        selectCatalog(null, true);
        ui = State.initial();
        if (presentationVisible)
            controller.load_definition_catalog(projectCode);
    }
    onPresentationVisibleChanged: if (presentationVisible) {
        controller.load_definition_catalog(projectCode);
        applyRequestedFocus();
    }
    Component.onCompleted: if (presentationVisible) {
        controller.load_definition_catalog(projectCode);
        refreshCatalogSelection(false);
        applyRequestedFocus();
    }
    Connections {
        target: root.controller
        function onFocusRequested() {
            root.applyRequestedFocus();
        }
        function onStateChanged() {
            if (root.controller.busy)
                return;
            if (root.catalogReloading) {
                root.catalogReloading = false;
                if (!root.controller.error) {
                    root.ui = Object.assign({}, root.ui, {
                        text: {}
                    });
                    root.refreshCatalogSelection(true);
                    root.message = "";
                }
            } else if (root.catalogSaving) {
                root.catalogSaving = false;
                if (!root.controller.error) {
                    root.refreshCatalogSelection(true);
                    root.message = "TACTIC definition saved";
                }
            } else if (!root.catalogDirty && (root.selectedCatalog.config !== root.catalogXmlOriginal || !root.selectedCatalogIdentity && root.controller.definitionCatalog.length))
                root.refreshCatalogSelection(false);
            root.applyRequestedFocus();
        }
    }
    Frame.FrameView {
        id: toolbar
        width: root.width
        height: root.saveActionsInHeader ? 0 : 38
        visible: !root.saveActionsInHeader
        theme: root.theme
        scene: root.saveActionsInHeader ? ({
                nodes: []
            }) : root.toolbarScene(width)
        onEvent: action => root.dispatch(action)
    }
    Frame.FrameView {
        id: body
        y: toolbar.height ? toolbar.height + 8 : 0
        width: root.width
        height: Math.max(1, root.height - y)
        theme: root.theme
        scene: UI.describe(root.frameModel, root.ui, width, height, root.language)
        models: ({
                definitions: root.catalogRows,
                columns: root.elements
            })
        describeRow: root.rowScene
        onEvent: action => root.dispatch(action)
    }
}

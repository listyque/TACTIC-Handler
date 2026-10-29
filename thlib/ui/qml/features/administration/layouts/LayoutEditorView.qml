import QtQuick
import QtQuick.Window
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/administration/layouts/layout.ui.mjs" as UI
import "../../../tactic_frame/features/administration/layouts/layout.state.mjs" as State
import "../../../tactic_frame/features/administration/layouts/layout.samples.mjs" as Samples
import "../../.." as Shell
import "../../../controls" as Controls

Item {
    id: root
    required property var theme
    required property var controller
    property string language: typeof localizationController !== "undefined" ? localizationController.current_language : qsTr("Search Types") === "Search Types" ? "en" : "ru"
    property bool saveActionsInHeader: false
    property var ui: State.initial()
    readonly property var navigationParent: State.navigationParent(ui)
    readonly property var editorSnapshot: Object.assign({}, root.controller.model)
    readonly property var frameModel: UI.model(editorSnapshot, ui, language, root.Window.window ? root.Window.window.width : width)
    readonly property var frameScene: body.scene
    readonly property var rows: Object.assign({}, UI.models(frameModel, language), {
        sourceEditor: controller.sourceEditor
    })
    readonly property bool allowSave: true
    readonly property bool allowReload: true
    readonly property bool allowCreate: false
    readonly property bool canReloadDocument: !controller.busy && frameModel.canLoad
    function rowScene(list, record) {
        return UI.row(list, record, frameModel, ui, language);
    }
    function toolbarScene(width) {
        return UI.toolbar(frameModel, ui, width, language, saveActionsInHeader);
    }
    function synchronize() {
        const blank = State.blankXml(frameModel);
        if (blank) {
            controller.initialize_xml(blank);
            return;
        }
        const next = State.synchronize(ui, frameModel);
        if (next !== ui) {
            ui = next;
            Qt.callLater(revealSelection);
        }
    }
    function revealSelection() {
        body.focusListRow("layoutElementsList", rows.layoutElements.findIndex(row => row.name === ui.selected), "");
    }
    function dispatch(event) {
        const result = State.transition(ui, frameModel, event);
        ui = result.ui;
        if (event.type === "select")
            Qt.callLater(revealSelection);
        controller.set_presentation_dirty(State.pending(ui));
        for (const command of result.commands) {
            switch (command.type) {
            case "reference":
                controller.open_reference(command.searchType, command.view, command.source);
                break;
            case "xml":
                controller.set_xml(command.value);
                break;
            case "context":
                controller.set_context(command.field, command.value);
                break;
            case "source":
                controller.select_source(command.value);
                break;
            case "newView":
                controller.new_view(command.view, command.xml);
                break;
            case "check":
                controller.check();
                break;
            case "save":
                controller.save();
                break;
            case "discard":
                controller.discard();
                break;
            case "reload":
                controller.reload(command.force);
                break;
            case "openView":
                controller.open_view();
                break;
            case "help":
                if (typeof appController !== "undefined")
                    appController.open_window("help");
                break;
            default:
                throw Error("Unsupported layout command: " + command.type);
            }
            if (!controller.model.error)
                ui = State.completed(ui, command);
        }
        controller.set_presentation_dirty(State.pending(ui));
    }
    function requestSave() {
        root.forceActiveFocus();
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
    Connections {
        target: root.controller
        function onStateChanged() {
            root.synchronize();
        }
    }
    Component.onCompleted: synchronize()
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
        models: root.rows
        describeRow: root.rowScene
        views: ({
                itemResults: {
                    component: liveResults
                }
            })
        onEvent: action => root.dispatch(action)
    }
    Component {
        id: liveResults
        Item {
            Loader {
                anchors.fill: parent
                active: !!root.controller.application && !!root.frameModel.liveInterface?.table?.item_layout
                visible: !root.frameModel.samplePreview
                sourceComponent: realResults
            }
            Loader {
                anchors.fill: parent
                // Keep the canvas owner alive while its scene clears on real-data updates.
                visible: !!root.frameModel.samplePreview
                sourceComponent: sampleResults
            }
            Controls.SelectableText {
                visible: !root.frameModel.liveInterface?.table?.item_layout
                theme: root.theme
                text: root.frameModel.error || root.frameModel.previewError || root.frameModel.sampleError || qsTr("Loading interface...")
            }
        }
    }
    Component {
        id: sampleResults
        Frame.FrameView {
            id: samplePreview
            theme: root.theme
            scene: Samples.scene(root.frameModel.liveInterface?.table?.item_layout, root.frameModel.samplePreview, width, height, root.ui.selected, root.ui.page !== "resolved", root.language, root.Window.window ? root.Window.window.width : root.width, "")
            views: ({
                    canvasOverlay: {
                        component: sampleCanvas
                    }
                })
            onEvent: action => {
                if (action.type === "select")
                    root.dispatch({
                        type: "select",
                        name: action.name
                    });
            }
            Component {
                id: sampleCanvas
                CanvasSelection {
                    theme: root.theme
                    boxes: samplePreview.scene.canvasBoxes || []
                    selected: root.ui.selected
                    onSelectedKey: key => root.dispatch({
                            type: "select",
                            name: key
                        })
                    onCommitted: value => root.dispatch({
                            type: "geometry",
                            value
                        })
                }
            }
        }
    }
    Component {
        id: realResults
        Shell.SearchResultSurface {
            enabled: root.ui.page !== "resolved"
            theme: root.theme
            controller: root.controller.application
            expansionOwner: root.controller
            resultModel: root.controller.previewModel
            current: root.ui.page !== "resolved"
            viewMode: root.frameModel.liveInterface?.table?.item_layout?.collection === "grid" ? "tiles" : "continious"
            splitterRatio: 0.5
            presentationActive: visible
            configuredLayout: root.frameModel.liveInterface?.table?.item_layout || null
            layoutEditing: root.ui.page !== "resolved"
            selectedLayoutElement: root.ui.page === "resolved" ? "" : root.ui.selected
            onLayoutGeometryEdited: value => root.dispatch({
                    type: "geometry",
                    value
                })
            onLayoutElementSelected: name => root.dispatch({
                    type: "select",
                    name
                })
        }
    }
}

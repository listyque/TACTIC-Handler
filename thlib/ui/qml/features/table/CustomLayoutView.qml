pragma ComponentBehavior: Bound
import QtQuick
import "../../tactic_frame" as Frame
import "../../controls" as Controls
import "../../tactic_frame/features/table/layout.ui.mjs" as Layout
import "../../tactic_frame/features/table/record.parts.mjs" as Parts
import "../../tactic_frame/features/table/report.ui.mjs" as Report
import "../../tactic_frame/features/table/page.filters.mjs" as Filters
import "../../tactic_frame/features/administration/layouts/canvas.mjs" as Canvas
import "../../tactic_frame/features/administration/layouts/page.viewport.mjs" as Viewport
import "../administration/layouts" as Editors
import "../.." as Shell

Frame.FrameView {
    id: root
    required property var services
    required property var controller
    required property var columnsController
    required property var users
    required property var administration
    property var itemSurfaces: null
    property var itemVersions: null
    property var owner: services.customLayout
    property bool editing: false
    property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    property bool guides: true
    property string selectedBlock: ""
    property var selectedBlocks: []
    property bool multiSelect: false
    property bool snap: false
    signal selectionEdited(var keys)
    signal canvasBoxesEdited(var boxes)
    onSceneChanged: canvasBoxesEdited(scene.canvasBoxes || [])
    property var previewItems: null
    property var canvasViewport: null
    Frame.FrameViewport {
        id: viewport
        target: root
    }
    readonly property var canvasSize: canvasViewport ? Viewport.dimensions(canvasViewport, viewport.size.width, viewport.size.height) : ({
            width: viewport.size.width,
            height: viewport.size.height,
            scale: 1
        })
    property var recordForms: ({})
    readonly property int formGeneration: document.layoutGeneration || 0
    onFormGenerationChanged: recordForms = Parts.interrupted(recordForms)
    property string formIdentity: JSON.stringify([document.layoutView, document.targetSearchKey])
    onFormIdentityChanged: recordForms = ({})
    property var filterDraft: ({})
    readonly property string filterKey: JSON.stringify([document.layoutView, document.targetSearchKey, document.layoutFilters])
    onFilterKeyChanged: filterDraft = Filters.initial(document.layoutFilters || [])
    signal blockSelected(string key)
    signal geometryEdited(var change, var boxes)
    readonly property var document: owner.document
    FontMetrics {
        id: regular
        font.family: root.theme.fontFamily
        font.pixelSize: 64
        font.hintingPreference: Font.PreferVerticalHinting
    }
    FontMetrics {
        id: semibold
        font.family: root.theme.fontFamily
        font.pixelSize: 64
        font.weight: Font.DemiBold
        font.hintingPreference: Font.PreferVerticalHinting
    }
    FontMetrics {
        id: bold
        font.family: root.theme.fontFamily
        font.pixelSize: 64
        font.weight: Font.Bold
        font.hintingPreference: Font.PreferVerticalHinting
    }
    function measure(text, size, weight) {
        const metrics = weight === 700 ? bold : weight === 600 ? semibold : regular;
        // Reading the font keeps content sizing bound to initial/theme font changes.
        const pixels = metrics.font.pixelSize;
        return metrics.advanceWidth(String(text)) * size / Math.max(1, pixels);
    }
    readonly property var baseScene: Layout.describe(Object.assign({}, document, {
        layoutTables: owner.tableModels || {},
        layoutForms: recordForms,
        layoutFilterDraft: filterDraft,
        layoutEditing: editing,
        layoutDesigning: editing && guides
    }), canvasSize.width - (canvasViewport ? 24 : 0), Math.max(1, canvasSize.height - (canvasViewport ? 24 : 0)), language, true, controller.server_url || "", measure)
    readonly property var decoratedScene: editing && guides ? Canvas.decorate(baseScene, "editorPath") : baseScene
    scene: canvasViewport ? Viewport.describe(decoratedScene, canvasViewport, viewport.size.width, viewport.size.height) : decoratedScene
    models: owner.tableModels || ({})
    describeCell: Report.cell
    views: ({
            layoutItems: {
                component: itemsComponent,
                nodeProps: true
            },
            layoutMarkdown: {
                component: markdownComponent,
                nodeProps: true
            },
            layoutTable: {
                component: tableComponent,
                nodeProps: true
            },
            canvasOverlay: {
                component: canvasComponent
            }
        })
    onEvent: action => {
        if (editing)
            return;
        if (action.type === 'layout-split') {
            owner.set_state(Layout.resize(document.layoutState, action));
            return;
        }
        if (action.type === 'record-form') {
            try {
                const result = Parts.change(recordForms, document, action);
                recordForms = result.store;
                if (result.command)
                    owner.save_form(action.key, result.command);
            } catch (error) {
                owner.filter_error(String(error.message || error));
            }
            return;
        }
        if (action.type === 'page-filter') {
            filterDraft = Filters.change(filterDraft, action);
            return;
        }
        if (action.type === 'page-filter-apply' || action.type === 'page-filter-reset') {
            try {
                if (action.type === 'page-filter-reset')
                    filterDraft = Filters.initial(document.layoutFilters || []);
                owner.apply_filters(action.type === 'page-filter-reset' ? {} : Filters.values(document.layoutFilters, filterDraft));
            } catch (error) {
                owner.filter_error(String(error.message || error));
            }
            return;
        }
        if (action.type === "layout-tab")
            owner.select_page(action.key);
        else if (action.type === "layout-close-tab")
            owner.close_page(action.key);
        else if (action.type === "layout-change")
            owner.set_state(Layout.change(document.layoutState, action.selector, action.value));
        else
            owner.activate(action);
    }
    Connections {
        target: root.owner
        ignoreUnknownSignals: true
        function onFormSettled(identity, result) {
            root.recordForms = Parts.settled(root.recordForms, identity, result, result.failure);
        }
    }
    Component {
        id: canvasComponent
        Editors.CanvasSelection {
            viewportScale: root.canvasSize.scale
            theme: root.theme
            boxes: root.scene.canvasBoxes || []
            selected: root.selectedBlock
            selection: root.selectedBlocks
            multiple: !!root.canvasViewport
            multiSelect: root.multiSelect
            snap: root.snap
            onSelectionEdited: keys => root.selectionEdited(keys)
            onSelectedKey: key => root.blockSelected(key)
            onCommitted: change => root.geometryEdited(change, root.scene.canvasBoxes || [])
        }
    }
    Component {
        id: itemsComponent
        Item {
            property var frameNode: ({})
            Loader {
                anchors.fill: parent
                active: !!root.previewItems || (!!root.itemSurfaces && !!root.itemVersions)
                sourceComponent: DashboardItems {
                    theme: root.theme
                    owner: root.owner
                    controller: root.controller
                    columnsController: root.columnsController
                    users: root.users
                    surfacesModel: root.itemSurfaces
                    versionsModel: root.itemVersions
                    previewItems: root.previewItems
                }
            }
        }
    }
    Component {
        id: markdownComponent
        Controls.DocumentPane {
            enabled: !root.editing
            property var frameNode: ({})
            theme: root.theme
            text: frameNode.text || ""
            contentInset: frameNode.contentInset === undefined ? 14 : frameNode.contentInset
            documentKey: frameNode.key || ""
            onLinkActivated: link => root.controller.open_rich_link(link)
            onFormatRequested: (document, style) => root.owner.format_document(document, style)
        }
    }
    Component {
        id: tableComponent
        Item {
            id: host
            property var frameNode: ({})
            Loader {
                anchors.fill: parent
                active: !!root.owner.table(host.frameNode.key || "", root.services.nestedRevision)
                sourceComponent: NestedTableView {
                    enabled: !root.editing
                    scope: root.owner.table(host.frameNode.key || "", root.services.nestedRevision)
                    theme: root.theme
                    controller: root.controller
                    services: root.services
                    columnsController: root.columnsController
                    userModel: root.users
                    administration: root.administration
                }
            }
        }
    }
}

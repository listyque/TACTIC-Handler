pragma ComponentBehavior: Bound
import QtQuick
import "../../tactic_frame" as Frame
import "../../controls" as Controls
import "../../tactic_frame/features/table/layout.ui.mjs" as Layout
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
    property var previewItems: null
    property var canvasViewport: null
    readonly property var canvasSize: canvasViewport ? Viewport.dimensions(canvasViewport, width, height) : ({
            width,
            height,
            scale: 1
        })
    property var filterDraft: ({})
    readonly property string filterKey: JSON.stringify([document.layoutView, document.targetSearchKey, document.layoutFilters])
    onFilterKeyChanged: filterDraft = Filters.initial(document.layoutFilters || [])
    signal blockSelected(string key)
    signal geometryEdited(var change, var boxes)
    readonly property var document: owner.document
    readonly property var baseScene: Layout.describe(Object.assign({}, document, {
        layoutTables: owner.tableModels || {},
        layoutFilterDraft: filterDraft,
        layoutEditing: editing
    }), canvasSize.width - (canvasViewport ? 24 : 0), Math.max(1, canvasSize.height - (canvasViewport ? 24 : 0)), language, true, controller.server_url || "")
    readonly property var decoratedScene: editing && guides ? Canvas.decorate(baseScene, "editorPath") : baseScene
    scene: canvasViewport ? Viewport.describe(decoratedScene, canvasViewport, width, height) : decoratedScene
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
    Component {
        id: canvasComponent
        Editors.CanvasSelection {
            viewportScale: root.canvasSize.scale
            theme: root.theme
            boxes: root.scene.canvasBoxes || []
            selected: root.selectedBlock
            onSelectedKey: key => root.blockSelected(key)
            onCommitted: change => root.geometryEdited(change, root.scene.canvasBoxes || [])
        }
    }
    Component {
        id: itemsComponent
        Item {
            property var frameNode: ({})
            Loader {
                active: !!root.previewItems
                anchors.fill: parent
                sourceComponent: Shell.SearchResultSurface {
                    enabled: !root.editing
                    theme: root.theme
                    controller: root.controller
                    expansionOwner: root.previewItems
                    resultModel: root.previewItems.previewModel
                    configuredLayout: root.previewItems.model.liveInterface?.table?.item_layout || null
                    viewMode: "continious"
                    layoutEditing: true
                    current: true
                    presentationActive: visible
                }
            }
            Loader {
                anchors.fill: parent
                active: !root.previewItems && !!root.itemSurfaces && !!root.itemVersions
                sourceComponent: DashboardItems {
                    theme: root.theme
                    owner: root.owner
                    controller: root.controller
                    columnsController: root.columnsController
                    users: root.users
                    surfacesModel: root.itemSurfaces
                    versionsModel: root.itemVersions
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
                    nestedTableFactory: nestedComponent
                }
            }
        }
    }
    Component {
        id: nestedComponent
        NestedTableView {
            enabled: !root.editing
            theme: root.theme
            controller: root.controller
            services: root.services
            columnsController: root.columnsController
            userModel: root.users
            administration: root.administration
            nestedTableFactory: nestedComponent
            onClosed: root.services.close_nested(scope)
        }
    }
}

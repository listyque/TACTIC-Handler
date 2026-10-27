pragma ComponentBehavior: Bound
import QtQuick
import "../../tactic_frame" as Frame
import "../../controls" as Controls
import "../../tactic_frame/features/table/layout.ui.mjs" as Layout
import "../../tactic_frame/features/administration/layouts/canvas.mjs" as Canvas
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
    property string selectedBlock: ""
    property var previewItems: null
    signal blockSelected(string key)
    signal geometryEdited(var change, var boxes)
    readonly property var document: owner.document
    readonly property var baseScene: Layout.describe(Object.assign({}, document, {
        layoutTables: owner.tableModels || {}
    }), width, height, typeof localizationController === "undefined" ? "en" : localizationController.current_language, true, controller.server_url || "")
    scene: editing ? Canvas.decorate(baseScene, "editorPath") : baseScene
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

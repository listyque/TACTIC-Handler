pragma ComponentBehavior: Bound
import QtQuick
import "../../tactic_frame" as Frame
import "../../controls" as Controls
import "../../tactic_frame/features/table/layout.ui.mjs" as Layout

Frame.FrameView {
    id: root
    required property var services
    required property var controller
    required property var columnsController
    required property var users
    required property var administration
    property var owner: services.customLayout
    readonly property var document: owner.document
    scene: Layout.describe(Object.assign({}, document, {
        layoutTables: owner.tableModels || {}
    }), width, height, typeof localizationController === "undefined" ? "en" : localizationController.current_language, true, controller.server_url || "")
    views: ({
            layoutTree: {
                component: treeComponent,
                nodeProps: true
            },
            layoutMarkdown: {
                component: markdownComponent,
                nodeProps: true
            },
            layoutTable: {
                component: tableComponent,
                nodeProps: true
            }
        })
    onEvent: action => {
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
        id: treeComponent
        Item {
            id: treeHost
            property var frameNode: ({})
            Loader {
                anchors.fill: parent
                active: !!root.owner.tree(treeHost.frameNode.key || "")
                sourceComponent: DashboardTreeView {
                    theme: root.theme
                    reader: root.owner.tree(treeHost.frameNode.key)
                }
            }
        }
    }
    Component {
        id: markdownComponent
        Controls.DocumentPane {
            property var frameNode: ({})
            theme: root.theme
            text: frameNode.text || ""
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

pragma ComponentBehavior: Bound
import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/table/layout.ui.mjs" as Layout

Frame.FrameView {
    id: root
    required property var services
    required property var controller
    required property var columnsController
    required property var users
    required property var administration
    readonly property var document: services.document
    readonly property var owner: services.customLayout
    scene: Layout.describe(Object.assign({}, document, {
        layoutTables: owner.tableModels || {}
    }), width, height, typeof localizationController === "undefined" ? "en" : localizationController.current_language, true, controller.server_url || "")
    views: ({
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

import QtQuick
import "../../.." as TH
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/files/workspace/graph.ui.mjs" as UI

Item {
    id: root
    required property var theme
    required property var controller
    signal editStream(var row, bool child)
    readonly property var state: controller.view_data
    readonly property var nodes: state.graph_nodes || []
    readonly property string language: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language
    function menu(row, item, x, y) {
        if (row)
            controller.set_value("catalog_detail", row);
        context.actions = [
            {
                title: qsTr("New stream"),
                translate: false,
                icon: "add",
                command: "new"
            }
        ];
        if (row)
            context.actions = context.actions.concat([
                {
                    title: qsTr("New child stream"),
                    translate: false,
                    icon: "source-branch",
                    command: "child",
                    enabled: Boolean(row.writable)
                },
                {
                    title: qsTr("Edit stream"),
                    translate: false,
                    icon: "edit",
                    command: "edit",
                    enabled: Boolean(row.writable)
                }
            ]);
        context.openAt(item, x, y);
    }
    TH.ActionMenu {
        id: context
        theme: root.theme
        onTriggered: command => root.editStream(command === "new" ? ({}) : root.state.catalog_detail, command === "child")
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe({
            native: true,
            nodes: root.nodes,
            edges: root.state.graph_edges || [],
            zoom: root.state.graph_zoom || 1,
            selected: root.state.catalog_detail?.code,
            busy: root.controller.busy,
            after: root.state.catalog_after,
            edgesAfter: root.state.graph_after
        }, width, height, root.language)
        views: ({
                streamGraphEdges: {
                    component: edgeCanvas
                }
            })
        onEvent: (action, source) => {
            const row = root.nodes.find(row => row.code === action.key);
            if (action.type === "new")
                root.editStream({}, false);
            else if (action.type === "select" && row)
                root.controller.set_value("catalog_detail", row);
            else if (action.type === "edit" && row)
                root.editStream(row, false);
            else if (action.type === "menu")
                root.menu(row || null, source, action.value.x, action.value.y);
            else if (action.type === "zoom")
                root.controller.set_value("graph_zoom", action.value);
            else if (action.type === "refresh")
                root.controller.action("catalog_page", {});
            else if (action.type === "more")
                root.controller.action("catalog_page", {
                    more: true
                });
            else if (action.type === "moreEdges")
                root.controller.action("catalog_page", {
                    edges: true
                });
        }
    }
    Component {
        id: edgeCanvas
        Canvas {
            id: canvas
            onWidthChanged: requestPaint()
            onHeightChanged: requestPaint()
            Connections {
                target: root.controller
                function onStateChanged() {
                    canvas.requestPaint();
                }
            }
            Connections {
                target: root.theme
                function onFramePaletteChanged() {
                    canvas.requestPaint();
                }
            }
            onPaint: {
                const context = getContext("2d");
                context.reset();
                UI.paint(context, root.nodes, root.state.graph_edges || [], root.state.graph_zoom || 1, role => root.theme[role]);
            }
        }
    }
}

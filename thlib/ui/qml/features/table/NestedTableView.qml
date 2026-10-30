pragma ComponentBehavior: Bound
import QtQuick
import "../.." as Tables
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/table/nested.ui.mjs" as UI

Item {
    id: root
    required property var theme
    required property var controller
    required property var columnsController
    required property var userModel
    required property var services
    required property var administration
    required property var scope
    implicitHeight: root.scope ? UI.extent(root.scope.model, width) : UI.height
    signal closed
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var description: root.scope ? UI.describe(root.scope.model, width, height, root.language) : ({
            nodes: []
        })
    readonly property var body: description.nodes.find(node => node.id === "nestedTableBody") || ({
            x: 0,
            y: 0,
            width: 0,
            height: 0
        })
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: ({
                nodes: root.description.nodes.filter(node => node.id !== "nestedTableBody")
            })
        models: ({
                rows: root.scope ? UI.rows(root.scope.model, root.width, root.height) : []
            })
        views: ({
                tableSearch: searchComponent
            })
        describeRow: (list, row, index) => root.scope ? UI.row(root.scope.model, row, root.language, list.width - 16) : ({
                    nodes: []
                })
        onEvent: (action, value) => {
            if (action.type === "close")
                root.closed();
            else if (root.scope)
                root.scope.activate(action, value);
        }
    }
    Component {
        id: searchComponent
        Tables.TacticSearchField {
            anchors.fill: parent
            theme: root.theme
            controller: root.scope
            suggestionModel: root.scope ? root.scope.searchSuggestions : null
            placeholderText: qsTr("Search objects")
        }
    }
    Loader {
        objectName: "nestedTableBody"
        x: root.body.x
        y: root.body.y
        width: root.body.width
        height: root.body.height
        active: root.body.width > 0
        visible: active
        function initialize() {
            if (!active || source.toString().length > 0)
                return;
            setSource(Qt.resolvedUrl("../../SearchResultTable.qml"), {
                objectName: "nestedMainTable",
                theme: root.theme,
                controller: root.controller,
                selectionOwner: Qt.binding(() => root.scope || root.controller),
                selectable: Qt.binding(() => root.scope && root.scope.model.selection !== false),
                columnsController: Qt.binding(() => root.scope ? root.scope.tableColumns : root.columnsController),
                resultModel: Qt.binding(() => root.scope ? root.scope.tableModel : null),
                tableServices: root.services,
                userModel: root.userModel,
                rowHeight: UI.rowHeight,
                presentationActive: true
            });
        }
        Component.onCompleted: initialize()
        onActiveChanged: initialize()
        onLoaded: {
            item.effectiveRowHeightChanged.connect(function () {
                if (item && root.scope && typeof root.scope.set_table_row_height === "function")
                    root.scope.set_table_row_height(item.effectiveRowHeight);
            });
            item.processCountMenuRequested.connect(processCounts.openProcessCountMenu);
            item.actionMenuRequested.connect(function (nodeId, actions, anchor, x, y, below) {
                rowMenu.nodeId = nodeId;
                rowMenu.actions = actions;
                rowMenu.openAt(anchor, x, y, below);
            });
        }
    }
    Tables.ProcessCountMenu {
        id: processCounts
        theme: root.theme
        controller: root.controller
    }
    Tables.ActionMenu {
        id: rowMenu
        objectName: "nestedRowMenu"
        property string nodeId: ""
        theme: root.theme
        onTriggered: command => root.controller.invoke_item_action(command, nodeId)
    }
}

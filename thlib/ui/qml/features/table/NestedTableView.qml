pragma ComponentBehavior: Bound
import QtQuick
import "../.." as Tables
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/table/nested.ui.mjs" as UI
import "../../tactic_frame/features/tasks/cells.ui.mjs" as TaskCells

Item {
    id: root
    required property var theme
    required property var controller
    required property var columnsController
    required property var userModel
    required property var services
    required property var administration
    required property var scope
    property Component nestedTableFactory: null
    signal closed
    signal menuRequested(string nodeId, var anchor)
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: root.scope ? UI.describe(root.scope.model, width, height, root.language) : ({
                nodes: []
            })
        models: ({
                rows: root.scope ? UI.rows(root.scope.model, root.width) : []
            })
        views: ({
                tableSearch: searchComponent,
                nestedTable: {
                    component: detailComponent,
                    nodeProps: true
                },
                tableCell: {
                    component: cellComponent,
                    nodeProps: true
                }
            })
        describeRow: (list, row, index) => root.scope ? UI.row(root.scope.model, row, root.language, list.width - 16) : ({
                    nodes: []
                })
        onEvent: (action, value) => {
            if (action.type === "close")
                root.closed();
            else if (action.type === "operate")
                root.menuRequested(action.nodeId, value);
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
    Component {
        id: detailComponent
        Item {
            id: detailHost
            property var frameNode: ({})
            property var childView: null
            readonly property var childScope: root.services ? root.services.nested_row(frameNode.nodeId || "", root.services.nestedRevision) : null
            function updateView() {
                if (childView) {
                    childView.destroy();
                    childView = null;
                }
                if (childScope && root.nestedTableFactory)
                    childView = root.nestedTableFactory.createObject(detailHost, {
                        scope: childScope,
                        width: Qt.binding(() => detailHost.width),
                        height: Qt.binding(() => detailHost.height)
                    });
            }
            onChildScopeChanged: updateView()
            Component.onCompleted: updateView()
        }
    }
    Component {
        id: cellComponent
        Item {
            id: cellHost
            property var frameNode: ({
                    column: {
                        cell: {
                            kind: "text"
                        }
                    },
                    record: {},
                    cell: {}
                })
            Tables.TacticTableCellDisplay {
                anchors.fill: parent
                theme: root.theme
                controller: root.controller
                selectionOwner: root.scope
                columnsController: root.columnsController
                userModel: root.userModel
                tableServices: root.services
                administration: root.administration
                nodeId: cellHost.frameNode.nodeId || ""
                kind: cellHost.frameNode.cell.kind || cellHost.frameNode.column.cell.kind || "text"
                cell: cellHost.frameNode.cell
                textValue: String(cellHost.frameNode.cell.text || "")
                columnIndex: cellHost.frameNode.column.index || 0
                previewActive: true
                previewUrl: cellHost.frameNode.cell.image || ""
                previewRevealed: true
                title: TaskCells.initials(cellHost.frameNode.record.name || cellHost.frameNode.record.title || cellHost.frameNode.record.code || "")
                accent: root.theme.action
                comments: 0
                tasks: 0
                displayOptions: cellHost.frameNode.column.displayOptions || ({})
                widgetClass: cellHost.frameNode.column.displayClass || cellHost.frameNode.column.resolvedClass || ""
            }
        }
    }
}

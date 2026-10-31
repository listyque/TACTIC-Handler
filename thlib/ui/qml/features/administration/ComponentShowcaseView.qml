pragma ComponentBehavior: Bound
import QtQuick
import Qt.labs.qmlmodels
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/administration/showcase.ui.mjs" as UI

Item {
    id: root
    required property var theme
    required property var sourceEditor
    property string language: "en"
    property var model: UI.initial()
    readonly property var scene: UI.describe(model, UI.catalogue, width, height, language)
    function dispatch(event) {
        model = UI.transition(model, event, UI.catalogue);
    }
    TableModel {
        id: sampleCells
        rows: UI.models(root.model).sampleCells
        TableModelColumn {
            display: "selected"
        }
        TableModelColumn {
            display: "name"
        }
        TableModelColumn {
            display: "value"
        }
    }
    Frame.FrameView {
        objectName: "componentShowcase"
        anchors.fill: parent
        theme: root.theme
        scene: root.scene
        models: Object.assign({}, UI.models(root.model), {
            sampleCells: sampleCells,
            families: UI.families(UI.catalogue, root.model, root.language),
            sourceEditor: root.sourceEditor
        })
        views: ({
                showcaseMenu: {
                    component: menuExample,
                    nodeProps: true
                },
                showcaseDialog: {
                    component: dialogExample,
                    nodeProps: true
                }
            })
        describeCell: (grid, record, row, column) => UI.cell(grid, record, row, column, root.model, root.language)
        describeRow: (list, record) => UI.row(list, record, root.model, root.language)
        onEvent: action => root.dispatch(action)
    }
    Component {
        id: menuExample
        ShowcaseMenu {
            theme: root.theme
            onEvent: action => root.dispatch(action)
        }
    }
    Component {
        id: dialogExample
        ShowcaseDialog {
            theme: root.theme
            onEvent: action => root.dispatch(action)
        }
    }
}

pragma ComponentBehavior: Bound
import QtQuick
import Qt.labs.qmlmodels
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/administration/showcase.variants.mjs" as UI
import "../../tactic_frame/controls/catalog/variants.mjs" as Variants
import "../../tactic_frame/controls/catalog.ui.mjs" as Base

Item {
    id: root
    required property var theme
    required property var sourceEditor
    required property var sampleServices
    property var frameNode: ({})
    readonly property var model: frameNode.model || Variants.initial("button")
    state: frameNode.state || "default"
    readonly property string language: frameNode.language || "en"
    signal event(var action)
    function dispatch(action) {
        event({
            type: frameNode.gallery ? "galleryEvent" : "variantEvent",
            id: frameNode.gallery,
            value: action
        });
    }
    TableModel {
        id: cells
        rows: root.model.id.indexOf("table") === 0 ? Array.from({
            length: 50
        }, () => ({
                    a: "",
                    b: "",
                    c: ""
                })) : []
        TableModelColumn {
            display: "a"
        }
        TableModelColumn {
            display: "b"
        }
        TableModelColumn {
            display: "c"
        }
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe(root.model, width, root.language, root.state)
        models: ({
                cells: cells,
                treeRows: Base.treeRows(root.model),
                sourceEditor: root.sourceEditor
            })
        views: ({
                example: control
            })
        describeRow: (list, record) => Variants.row(list, record, root.model, root.language, root.state)
        describeCell: (grid, record, row, column) => Variants.cell(grid, record, row, column, root.model, root.state)
        onEvent: action => root.dispatch(action)
    }
    Component {
        id: control
        ShowcaseControl {
            userModel: root.sampleServices.users
            emojiModel: root.sampleServices.emoji
            theme: root.theme
            language: root.language
            example: Variants.find(root.model.id)
            value: root.model.value
            disabled: ["disabled", "loading"].includes(root.state)
            readOnly: root.state === "readonly"
            onEvent: action => root.dispatch(action)
        }
    }
}

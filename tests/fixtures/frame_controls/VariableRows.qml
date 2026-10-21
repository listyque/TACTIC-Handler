import QtQuick
import "../../../thlib/ui/qml/tactic_frame" as Frame
import "../../../thlib/ui/qml/tactic_frame/core/frame.mjs" as Contract

Frame.FrameView {
    id: root
    property var records: []
    signal selected(var action)
    onEvent: action => root.selected(action)
    models: ({
            rows: records
        })
    scene: ({
            nodes: [Contract.node("List", "variableRows", Contract.rect(0, 0, width, height), {
                    source: "rows",
                    keyField: "key",
                    fields: ["key", "text", "extent"],
                    rowHeight: 40,
                    rowGap: 0,
                    rowHeightField: "extent",
                    scrollbarId: "variableRowsScrollBar"
                })]
        })
    describeRow: (list, record, index) => ({
                nodes: [Contract.button("item-" + record.key, Contract.rect(0, 0, list.width - 16, 40), record.text, "", {
                        type: "selected",
                        key: record.key
                    }, true)]
            })
}

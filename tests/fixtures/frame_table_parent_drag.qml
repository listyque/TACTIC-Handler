import QtQuick
import "../../thlib/ui/qml/tactic_frame" as Frame
import "../../thlib/ui/qml/tactic_frame/core/frame.mjs" as Nodes
import "../../thlib/ui/qml/features/table" as Table

Item {
    required property var theme
    required property var controller
    required property var services
    required property var cell
    Frame.FrameView {
        theme: parent.theme
        width: 80
        height: 100
        scene: ({nodes: [Nodes.node("Action", "parentDragSource", Nodes.rect(0, 0, 80, 100), {
            text: "Drag parent", enabled: true, dragValue: {searchType: "contract/entity", searchKeys: ["contract/entity?project=demo&code=B"]}})]})
    }
    Table.ServiceCell {
        theme: parent.theme
        controller: parent.controller
        services: parent.services
        administration: null
        cell: parent.cell
        nodeId: "N1"
        x: 100
        width: 280
        height: 100
    }
}

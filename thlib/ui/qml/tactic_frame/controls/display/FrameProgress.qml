pragma ComponentBehavior: Bound
import QtQuick
import "../../../controls" as Controls

Controls.ProgressBar {
    id: root
    required property var node
    property bool interactive: true
    signal event(var action)
    objectName: root.node.id
    Accessible.name: root.node.text
    from: root.node.min ?? 0
    to: root.node.max ?? 1
    value: root.node.value ?? 0
    indeterminate: !!root.node.indeterminate
}

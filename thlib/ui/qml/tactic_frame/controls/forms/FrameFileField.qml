pragma ComponentBehavior: Bound
import QtQuick
import "../../../controls" as Controls

Loader {
    id: root
    required property var node
    required property var theme
    property bool interactive: true
    signal event(var action)
    // FileInput renders its own Frame scene; resolve only this active branch.
    Component.onCompleted: setSource(Qt.resolvedUrl("../../../controls/FileInput.qml"), {
        theme: root.theme,
        objectName: root.node.id
    })
    Binding {
        target: root.item
        property: "value"
        value: root.node.text
        when: !!root.item
    }
    Binding {
        target: root.item
        property: "editable"
        value: root.interactive && !!root.node.enabled && !root.node.readOnly
        when: !!root.item
    }
    Connections {
        target: root.item
        function onValueEdited(value) {
            if (!root.node.action)
                return;
            root.event(Object.assign({}, root.node.action, {
                value: value ? [String(value)] : []
            }));
        }
    }
}

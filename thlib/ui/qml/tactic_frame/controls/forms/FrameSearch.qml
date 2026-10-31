pragma ComponentBehavior: Bound
import QtQuick
import "../../../controls" as Controls

Controls.SearchField {
    id: root
    required property var node
    property bool interactive: true
    signal event(var action)
    objectName: root.node.id
    text: root.node.text
    placeholderText: root.node.placeholder || ""
    Accessible.name: root.node.label || ""
    enabled: root.interactive && !!root.node.enabled
    readOnly: !!root.node.readOnly
    suggestions: root.node.suggestions || []
    errorText: root.node.errorText || ""
    clearOnEscape: false
    onSearchEdited: value => {
        if (root.node.action)
            root.event(Object.assign({}, root.node.action, {
                value
            }));
    }
    onSearchRequested: root.event(root.node.commitAction)
    onSuggestionAccepted: (index, record) => {
        if (root.node.acceptAction)
            root.event(Object.assign({}, root.node.acceptAction, {
                value: record
            }));
    }
}

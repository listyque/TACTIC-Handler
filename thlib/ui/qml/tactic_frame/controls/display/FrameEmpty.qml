pragma ComponentBehavior: Bound
import QtQuick
import "../../../controls" as Controls

Controls.EmptyState {
    id: root
    required property var node
    property bool interactive: true
    signal event(var action)
    objectName: root.node.id
    title: root.node.text
    message: root.node.message || ""
    iconName: root.node.icon || "info"
    error: !!root.node.error
    actionText: root.node.actionText || ""
    actionIcon: root.node.actionIcon || ""
    enabled: root.interactive && !!root.node.enabled && !root.node.readOnly
    onActionRequested: root.event(root.node.action)
}

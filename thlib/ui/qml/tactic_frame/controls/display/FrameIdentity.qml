pragma ComponentBehavior: Bound
import QtQuick
import "../../../controls" as Controls
import "../../.." as TH

TH.UserIdentity {
    id: root
    required property var node
    property bool interactive: true
    signal event(var action)
    property color accent: theme.action
    objectName: root.node.id
    login: root.node.login || ""
    displayName: root.node.text
    initials: root.node.initials || ""
    avatarUrl: root.node.url || ""
    avatarColor: root.accent
    avatarSize: root.node.avatarSize || 40
    retired: !!root.node.retired
    emphasized: !!root.node.emphasized
}

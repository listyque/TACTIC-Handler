pragma ComponentBehavior: Bound

import QtQuick
import "controls" as Controls

Loader {
    id: root

    required property var theme
    required property bool compact
    required property bool revealed
    required property bool selected
    required property real leadingSpace
    required property string dccApplication
    required property string nodeId
    property var actions: []

    signal actionRequested(string command)

    readonly property real buttonSize: compact ? 24 : 28
    readonly property real buttonSpacing: 5

    width: leadingSpace + actions.length * buttonSize
        + Math.max(0, actions.length - 1) * buttonSpacing
    height: buttonSize
    active: revealed
    visible: revealed
    enabled: revealed

    function refreshActions() {
        actions = appController.item_quick_actions(nodeId)
    }

    Component.onCompleted: refreshActions()
    onNodeIdChanged: refreshActions()
    onRevealedChanged: if (revealed) refreshActions()
    onDccApplicationChanged: refreshActions()

    sourceComponent: Item {
        Repeater {
            model: root.actions

            Controls.CompactIconButton {
                id: actionDelegate
                required property var modelData
                required property int index
                objectName: actionDelegate.modelData.replaces === "save"
                    ? "workspaceInlineSaveAction"
                    : actionDelegate.modelData.replaces === "open"
                        ? "workspaceInlineOpenAction"
                        : actionDelegate.modelData.dccActionId === "import"
                            ? "workspaceInlineImportAction"
                            : actionDelegate.modelData.dccActionId === "reference"
                                ? "workspaceInlineReferenceAction"
                                : "workspaceInlineAction_" + String(
                                    actionDelegate.modelData.dccActionId
                                    || actionDelegate.index)
                x: root.leadingSpace + actionDelegate.index * (
                    root.buttonSize + root.buttonSpacing
                )
                width: root.buttonSize
                height: root.buttonSize
                theme: root.theme
                iconName: String(
                    actionDelegate.modelData.icon || "deployed_code"
                )
                iconSize: root.compact ? 14 : 16
                iconColor: root.selected
                    ? root.theme.contentSelectionText
                    : root.theme.secondaryText
                round: true
                toolTip: qsTr(String(actionDelegate.modelData.title || ""))
                Accessible.role: Accessible.Button
                Accessible.name: toolTip
                onClicked: root.actionRequested(String(
                    actionDelegate.modelData.command || ""
                ))
            }
        }
    }
}

pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import "../.." as TH
import "../../controls" as Controls

Controls.Button {
    id: root
    property var frameNode: ({})
    signal event(var action)
    text: frameNode.text || ""
    enabled: !!frameNode.enabled
    onClicked: menu.openBelow(root)
    TapHandler {
        acceptedButtons: Qt.RightButton
        onTapped: eventPoint => menu.openAt(root, eventPoint.position.x, eventPoint.position.y, false)
    }
    TH.ActionMenu {
        id: menu
        objectName: "sampleActionMenu"
        theme: root.theme
        frameComposition: true
        parent: Overlay.overlay
        actions: root.frameNode.actions || []
        onTriggered: command => root.event(Object.assign({}, root.frameNode.action, {
                value: command
            }))
    }
    onEnabledChanged: if (!enabled)
        menu.close()
    Component.onDestruction: menu.close()
}

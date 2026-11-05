import QtQuick
import "../../controls" as Controls

Controls.CompactIconButton {
    id: root
    objectName: "batchRenderLaunchButton"
    required property var controller
    property bool roomAvailable: true
    readonly property var launchAction: controller.launchActions.find(action => action.command === "client_plugin:th_batch_render") || null
    visible: roomAvailable && launchAction !== null
    enabled: !!launchAction && launchAction.enabled
    iconName: "movie"
    iconColor: theme.action
    round: true
    toolTip: qsTr("Batch Render")
    onClicked: controller.open_plugin("th_batch_render")
}

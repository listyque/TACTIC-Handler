import QtQuick
import "controls" as Controls
import "tactic_frame" as Frame
import "tactic_frame/features/objects/snapshot.ui.mjs" as UI

Item {
    id: root
    required property var theme
    required property var controller
    signal optionsPressed
    signal optionsRequested(var sourceItem)
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    height: UI.metrics.toolbar
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.toolbar({
            contentMode: root.controller.snapshot_browser_content_mode,
            imageMode: root.controller.snapshot_browser_image_mode
        }, width, root.language)
        views: ({
                options: optionsComponent
            })
        onEvent: action => {
            if (action.type === "image")
                root.controller.set_snapshot_browser_image_mode(action.value);
            else if (action.type === "refresh")
                root.controller.refresh_snapshot_browser();
        }
    }
    Component {
        id: optionsComponent
        Controls.CompactIconButton {
            theme: root.theme
            round: true
            backgroundColor: root.theme.surfaceContainerHigh
            iconName: "more_vert"
            iconSize: 16
            toolTip: qsTr("Snapshot Browser options")
            onPressed: root.optionsPressed()
            onClicked: root.optionsRequested(this)
        }
    }
}

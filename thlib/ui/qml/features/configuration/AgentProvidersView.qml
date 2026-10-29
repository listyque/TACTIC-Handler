import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/configuration/providers.ui.mjs" as UI

Item {
    id: root
    required property var theme
    property var controller: agentProvidersController
    property bool embedded: false
    property bool active: visible
    onActiveChanged: if (embedded)
        controller.set_embedded_active(active)
    Component.onCompleted: if (embedded)
        controller.set_embedded_active(active)
    Component.onDestruction: if (embedded)
        controller.set_embedded_active(false)
    readonly property string language: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe(root.controller.model, width, height, root.language)
        onEvent: action => root.controller.handle(action)
    }
}

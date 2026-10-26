import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/configuration/mcp.ui.mjs" as UI

Item {
    id: root
    required property var theme
    property var controller: agentMcpController
    readonly property string language: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe(root.controller.model, width, height, root.language)
        onEvent: action => root.controller.handle(action)
    }
}

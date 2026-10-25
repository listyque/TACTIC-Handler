import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/scripts/request.ui.mjs" as UI

Item {
    id: root
    required property var theme
    property var controller: agentRequestController
    readonly property string uiLanguage: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe(root.controller.model, width, height, root.uiLanguage)
        onEvent: function (action) {
            root.controller.handle(action.type, action.value === undefined ? "" : action.value);
        }
    }
}

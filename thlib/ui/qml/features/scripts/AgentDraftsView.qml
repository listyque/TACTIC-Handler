import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/scripts/drafts.ui.mjs" as UI

Item {
    id: root
    required property var controller
    required property var theme
    signal back
    readonly property string uiLanguage: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language
    Component.onCompleted: controller.open()
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe(root.controller.model, width, height, root.uiLanguage)
        onEvent: function (action) {
            if (action.type === "back")
                root.back();
            else
                root.controller.handle(action.type, action.value === undefined ? "" : action.value);
        }
    }
}

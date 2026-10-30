import QtQuick
import "tactic_frame" as Frame
import "tactic_frame/features/support/diagnostics/system.ui.mjs" as UI

Item {
    id: root
    required property var theme
    property var controller: systemInfoController
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe(root.controller.model, width, height, root.language)
        onEvent: action => {
            if (action.type === "copy")
                root.controller.copy(UI.report(root.controller.model, root.language));
            else
                root.controller.handle(action);
        }
    }
}

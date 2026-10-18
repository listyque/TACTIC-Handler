import QtQuick
import "../../../controls" as Controls
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/files/workspace/forms.ui.mjs" as UI

Controls.Dialog {
    id: root
    readonly property string language: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language

    objectName: "workspaceComparisonDialog"
    required property var controller
    readonly property var comparison: controller.view_data.comparison || ({})
    title: qsTr("File comparison")
    modal: false
    width: Math.max(260, Math.min(900, parent ? parent.width - 24 : 900))
    height: Math.max(180, Math.min(600, parent ? parent.height - 24 : 600))
    x: parent ? (parent.width - width) / 2 : 0
    y: parent ? (parent.height - height) / 2 : 0
    signal externalRequested
    contentItem: Frame.FrameView {
        id: form
        theme: root.theme
        scene: UI.comparison({
            comparison: root.comparison,
            busy: root.controller.busy
        }, width, height, root.language)
        onEvent: action => {
            if (action.type === "reject")
                root.close();
            else if (action.type === "external" && !root.controller.busy)
                root.externalRequested();
        }
    }
    footer: null
}

import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/objects/editor.ui.mjs" as UI

Frame.FrameView {
    id: root
    required property var model
    required property string part
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    implicitHeight: scene.height
    scene: UI[part](model, width, language)
}

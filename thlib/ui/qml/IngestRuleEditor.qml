import QtQuick
import "tactic_frame" as Frame
import "tactic_frame/features/files/ingest.ui.mjs" as UI

Frame.FrameView {
    id: root
    required property var controller
    signal deleteRuleRequested
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    scene: UI.ruleEditor({
        options: controller.options,
        busy: controller.busy,
        canDeleteRule: controller.canDeleteRule
    }, width, language)
    implicitHeight: scene.height
    onEvent: action => {
        if (action.type === "option")
            controller.set_option(action.field, UI.optionValue(action.field, action.value));
        else if (action.type === "saveRule")
            controller.save_rule(controller.options.title || "");
        else if (action.type === "deleteRule")
            root.deleteRuleRequested();
        else if (action.type === "script")
            windowModel.show_window("script_editor");
    }
}

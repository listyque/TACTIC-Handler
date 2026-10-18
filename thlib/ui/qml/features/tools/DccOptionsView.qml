import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/tools/dcc.ui.mjs" as UI

Frame.FrameView {
    id: root
    readonly property string language: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language
    scene: UI.describe({
        schema: dccOptionsController.schema,
        values: dccOptionsController.values,
        target: dccOptionsController.targetTitle || dccOptionsController.applicationTitle,
        available: dccOptionsController.available,
        error: dccOptionsController.error,
        style: root.theme.styleName
    }, width, height, language)
    onEvent: action => {
        if (action.type === "run")
            dccOptionsController.confirm();
        else if (action.type === "field")
            dccOptionsController.set_value(action.field, action.value);
        else if (action.type === "step")
            dccOptionsController.set_value(action.field, Number(dccOptionsController.values[action.field] || 0) + action.value);
    }
}

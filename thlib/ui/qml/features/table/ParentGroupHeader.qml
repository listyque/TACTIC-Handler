import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/table/parent.ui.mjs" as UI

Frame.FrameView {
    id: root
    objectName: "searchResultTableParentGroup"
    required property var model
    property bool editable: false
    property string server: ""
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    signal toggleRequested
    signal createRequested
    scene: UI.group(model, width, language, editable, server)
    onEvent: action => {
        if (action.type === "toggle")
            toggleRequested();
        else if (action.type === "create-child")
            createRequested();
    }
}

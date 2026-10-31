pragma ComponentBehavior: Bound
import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/administration/showcase.ui.mjs" as UI

Item {
    id: root
    required property var theme
    required property var sourceEditor
    property string language: "en"
    property var model: UI.initial()
    readonly property var scene: UI.describe(model, UI.catalogue, width, height, language)
    function dispatch(event) {
        model = UI.transition(model, event, UI.catalogue);
    }
    Frame.FrameView {
        objectName: "componentShowcase"
        anchors.fill: parent
        theme: root.theme
        scene: root.scene
        models: ({
                families: UI.families(UI.catalogue, root.model, root.language),
                sourceEditor: root.sourceEditor
            })
        describeRow: (list, record) => UI.row(list, record, root.model, root.language)
        onEvent: action => root.dispatch(action)
    }
}

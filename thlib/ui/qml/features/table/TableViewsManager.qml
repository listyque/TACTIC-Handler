import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/table/views.ui.mjs" as UI

Item {
    id: root
    required property var theme
    property var controller: tableViewsController
    property var ui: UI.initial()
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    Component.onCompleted: ui = Object.assign({}, ui, {
        selected: controller.model.current || "table"
    })
    Connections {
        target: root.controller
        function onChanged() {
            if (!root.controller.model.busy && !root.controller.model.error)
                root.ui = UI.loaded(root.ui, root.controller.model);
        }
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe(root.controller.model, root.ui, width, height, root.language)
        models: ({
                views: UI.rows(root.controller.model, root.ui)
            })
        describeRow: (list, record) => UI.row(list, record, root.ui, root.controller.model, root.language)
        onEvent: action => {
            const result = UI.transition(root.ui, root.controller.model, action);
            root.ui = result.ui;
            if (result.command)
                root.controller.run(result.command);
        }
    }
}

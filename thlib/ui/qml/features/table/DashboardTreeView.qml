import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/table/tree.ui.mjs" as Tree

Frame.FrameView {
    id: root
    required property var reader
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    scene: Tree.describe(reader.model, width, height, language)
    models: ({
            rows: Tree.rows(reader.model)
        })
    describeRow: (list, item, index) => Tree.row(reader.model, item, list.width - 16, language)
    onEvent: action => reader.activate(action)
}

import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/tools/database.ui.mjs" as UI

Frame.FrameView {
    id: root
    readonly property string language: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language
    property string column: ""
    property string bulkValue: ""
    readonly property var columns: appController.selected_result_fields
    onColumnsChanged: if (!columns.includes(column))
        column = columns.length ? columns[0] : ""
    readonly property var projection: ({
            count: appController.selected_result_count,
            columns: root.columns,
            column: root.column,
            bulkValue: root.bulkValue,
            busy: appController.loading
        })
    models: ({
            objects: appController.selected_result_records
        })
    scene: UI.batch(root.projection, width, height, language)
    describeRow: (list, record, index) => UI.row(list, record, index, root.projection)
    onEvent: action => {
        if (action.type === "column")
            root.column = action.value;
        else if (action.type === "bulkValue")
            root.bulkValue = action.value;
        else if (action.type === "bulk" && root.column && !appController.loading)
            appController.update_selected_items(root.column, root.bulkValue);
    }
}

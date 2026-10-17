import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/search/conditions.ui.mjs" as UI

Frame.FrameView {
    id: row
    required property int index
    required property string column
    required property var relation
    required property var value
    required property bool rowEnabled
    required property string operator
    required property bool isDefault
    required property var generatedFilterKind
    required property var generatedFilterState
    required property var application
    required property var recordsModel
    required property var columnsModel
    required property var suggestions
    property bool presentationActive: true
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var record: {
        const choices = [];
        for (let index = 0; index < columnsModel.count(); index++)
            choices.push(columnsModel.get(index));
        const column = choices.find(choice => choice.value === row.column);
        const state = generatedFilterState || {};
        return {
            column: row.column,
            columnTitle: column ? column.label : row.column,
            relation: row.relation,
            value: row.value,
            rowEnabled: row.rowEnabled,
            operator: row.operator,
            isDefault: row.isDefault,
            generatedFilterKind: row.generatedFilterKind,
            generatedTitle: state.translatable ? qsTr(state.title || "Quick filter") : state.title || "",
            relations: application.search_filter_relations(row.column),
            columns: choices
        };
    }
    readonly property var valueControl: (scene.nodes[0] ? scene.nodes[0].children : []).find(node => node.view === "value")
    height: UI.rowHeight(record, width)
    scene: ({
            nodes: [UI.row(record, index, width, language, {
                    columns: record.columns,
                    valueView: "value",
                    reorder: true,
                    count: row.recordsModel.count(),
                    busy: row.application.search_state === "loading"
                })]
        })
    views: ({
            value: valueComponent
        })
    onEvent: action => {
        if (action.type === "condition") {
            if (action.field === "rowEnabled")
                recordsModel.toggle_checked(index);
            else if (action.field === "column")
                application.set_search_filter_column(index, action.value);
            else
                recordsModel.set_value(index, action.field, action.value);
        } else if (action.type === "operator")
            recordsModel.set_value(index, "operator", operator === "or" ? "and" : "or");
        else if (action.type === "detach")
            application.detach_generated_search_filter(index);
        else if (action.type === "add")
            application.add_search_filter();
        else if (action.type === "move")
            application.move_search_filter(index, action.delta);
        else if (action.type === "remove")
            recordsModel.remove(index);
    }
    Component {
        id: valueComponent
        ConditionValue {
            theme: row.theme
            application: row.application
            recordsModel: row.recordsModel
            suggestions: row.suggestions
            index: row.index
            column: row.column
            value: row.value
            rowEnabled: !!row.valueControl && row.valueControl.enabled
            presentationActive: row.presentationActive
        }
    }
}

pragma ComponentBehavior: Bound

import QtQuick
import "tactic_frame/features/objects/fields.ui.mjs" as UI

Item {
    id: root

    required property var theme
    required property var fieldModel
    required property string itemPrefix
    property string repeaterObjectName: ""
    property bool editorBusy: false
    property string editorMode: "edit"
    property real minimumCellWidth: 430
    property int maximumColumns: 3
    property real spacing: theme.spacing.content
    readonly property int columnCount: UI.columnCount(width, fields.count, minimumCellWidth, maximumColumns, spacing)
    property var positions: []
    signal previewRequested(int row)

    function cellWidth() {
        return Math.max(0, (width - spacing * (columnCount - 1)) / columnCount);
    }

    function arrange() {
        const heights = [];
        for (let index = 0; index < fields.count; ++index)
            heights.push(fields.itemAt(index) ? fields.itemAt(index).height : 0);
        const layout = UI.arrange(width, heights, minimumCellWidth, maximumColumns, spacing);
        positions = layout.cells.map(cell => cell.y);
        implicitHeight = layout.height;
    }

    onWidthChanged: Qt.callLater(arrange)
    onColumnCountChanged: Qt.callLater(arrange)
    onSpacingChanged: Qt.callLater(arrange)

    Repeater {
        id: fields
        objectName: root.repeaterObjectName
        model: root.fieldModel
        onItemAdded: Qt.callLater(root.arrange)
        onItemRemoved: Qt.callLater(root.arrange)

        delegate: Item {
            id: fieldItem
            objectName: root.itemPrefix + fieldName
            required property int index
            required property string fieldName
            required property string title
            required property string fieldType
            required property var fieldValue
            required property var fieldOptions
            required property string fieldDescription
            required property string fieldIcon
            required property string fieldError
            required property bool fieldRequired
            required property bool fieldReadOnly

            width: root.cellWidth()
            height: fieldDelegate.implicitHeight
            x: (index % root.columnCount) * (width + root.spacing)
            y: root.positions[index] || 0
            onHeightChanged: Qt.callLater(root.arrange)
            SObjectFieldDelegate {
                id: fieldDelegate
                width: parent.width
                theme: root.theme
                fieldModel: root.fieldModel
                fieldRow: fieldItem.index
                editorBusy: root.editorBusy
                editorMode: root.editorMode
                fieldName: fieldItem.fieldName
                title: fieldItem.title
                fieldType: fieldItem.fieldType
                fieldValue: fieldItem.fieldValue
                fieldOptions: fieldItem.fieldOptions
                description: fieldItem.fieldDescription
                iconName: fieldItem.fieldIcon
                errorText: fieldItem.fieldError
                requiredField: fieldItem.fieldRequired
                readOnlyField: fieldItem.fieldReadOnly
                onPreviewRequested: row => root.previewRequested(row)
            }
        }
    }
}

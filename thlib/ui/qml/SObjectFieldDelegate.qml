import QtQuick

SObjectFieldFrame {
    id: root

    required property var fieldModel
    required property bool editorBusy
    required property string editorMode
    required property int fieldRow
    required property string fieldType
    required property var fieldValue
    required property var fieldOptions
    signal previewRequested(int row)

    editorData: SObjectValueEditor {
        anchors.left: parent.left
        anchors.right: parent.right
        theme: root.theme
        fieldModel: root.fieldModel
        editorBusy: root.editorBusy
        editorMode: root.editorMode
        fieldName: root.fieldName
        fieldType: root.fieldType
        fieldValue: root.fieldValue
        fieldOptions: root.fieldOptions
        errorText: root.errorText
        readOnlyField: root.readOnlyField
        onValueEdited: value => root.fieldModel.setValue(root.fieldRow, value)
        onPreviewRequested: root.previewRequested(root.fieldRow)
        onPreviewFilesAdded: values =>
            root.fieldModel.add_preview_files(root.fieldRow, values)
        onPreviewFileRemoved: index =>
            root.fieldModel.remove_preview_file(root.fieldRow, index)
        onPreviewFilesCleared:
            root.fieldModel.clear_preview_files(root.fieldRow)
    }
}

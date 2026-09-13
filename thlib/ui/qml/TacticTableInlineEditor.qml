pragma ComponentBehavior: Bound

import QtQuick

Item {
    id: root

    required property var theme
    required property var controller
    required property var columnsController
    required property string nodeId
    required property string columnName
    property bool editable: false
    property bool pooled: false
    property bool editing: false
    property bool discarding: false
    property var descriptor: ({})

    signal selectRequested()
    signal focusTableRequested()

    function beginEditing() {
        if (!root.columnsController
                || typeof root.columnsController.cell_editor !== "function")
            return
        const nextDescriptor = root.columnsController.cell_editor(
            root.nodeId, root.columnName
        )
        if (!nextDescriptor || !nextDescriptor.fieldType)
            return
        root.selectRequested()
        root.discarding = false
        root.descriptor = nextDescriptor
        root.editing = true
    }

    function commit(value) {
        if (!root.editing || root.discarding)
            return
        const current = root.descriptor
        root.editing = false
        if (String(value ?? "") === String(current.fieldValue ?? ""))
            return
        const changes = ({})
        changes[String(current.submitName || root.columnName)] = value
        root.controller.update_selected_item_fields(root.nodeId, changes)
    }

    function cancel() {
        root.discarding = true
        root.editing = false
        root.focusTableRequested()
        Qt.callLater(function() { root.discarding = false })
    }

    onPooledChanged: {
        if (pooled)
            cancel()
    }

    MouseArea {
        objectName: "tableCellEditArea_" + root.columnName
        anchors.fill: parent
        enabled: root.editable && !root.editing
        acceptedButtons: Qt.LeftButton
        propagateComposedEvents: true
        cursorShape: Qt.IBeamCursor
        onClicked: mouse => mouse.accepted = false
        onDoubleClicked: mouse => {
            mouse.accepted = true
            root.beginEditing()
        }
    }

    Loader {
        id: editor
        objectName: "tableCellEditor_" + root.columnName
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        anchors.margins: 4
        height: Math.max(parent.height - 8, 0)
        active: root.editing

        sourceComponent: SObjectValueEditor {
            theme: root.theme
            compact: true
            autoActivate: true
            editorMode: "edit"
            fieldName: String(root.descriptor.fieldName || "")
            fieldType: String(root.descriptor.fieldType || "string")
            fieldValue: root.descriptor.fieldValue
            fieldOptions: root.descriptor.fieldOptions || []
            errorText: String(root.descriptor.fieldError || "")
            readOnlyField: false
            onValueEdited: value => root.commit(value)
            onCancelRequested: root.cancel()
        }
    }
}

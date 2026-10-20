pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import "controls" as Controls
import "features/table" as Table
import "tactic_frame/features/table/inline.ui.mjs" as InlineUI

Item {
    id: root
    clip: true

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
    readonly property string editorMode: tagsEditor ? "tags" : descriptor.fieldType === "multiline" || descriptor.submitName === "description" || columnName === "description" ? "multiline" : descriptor.fieldType === "enum" || ["status", "process", "pipeline", "project"].indexOf(descriptor.fieldType) >= 0 ? "select" : descriptor.fieldType === "bool" ? "bool" : ["date", "datetime", "color", "user", "time"].indexOf(descriptor.fieldType) >= 0 ? descriptor.fieldType : "text"
    readonly property bool textPanel: InlineUI.explicitSave(editorMode)
    readonly property bool tagsEditor: descriptor.fieldType === "tags" || descriptor.fieldName === "keywords"

    signal selectRequested
    signal focusTableRequested

    function beginEditing() {
        if (!root.columnsController || typeof root.columnsController.cell_editor !== "function")
            return;
        const nextDescriptor = root.columnsController.cell_editor(root.nodeId, root.columnName);
        if (!nextDescriptor || !nextDescriptor.fieldType)
            return;
        root.selectRequested();
        root.discarding = false;
        root.descriptor = nextDescriptor;
        root.editing = true;
    }

    function commit(value) {
        if (!root.editing || root.discarding)
            return;
        const current = root.descriptor;
        root.editing = false;
        if (String(value ?? "") === String(current.fieldValue ?? ""))
            return;
        const changes = ({});
        changes[String(current.submitName || root.columnName)] = value;
        root.controller.update_selected_item_fields(root.nodeId, changes);
    }

    function cancel() {
        root.discarding = true;
        root.editing = false;
        root.focusTableRequested();
        Qt.callLater(function () {
            root.discarding = false;
        });
    }

    onPooledChanged: {
        if (pooled)
            cancel();
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
            mouse.accepted = true;
            root.beginEditing();
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
        active: root.editing && !root.textPanel

        sourceComponent: inlineEditor
    }

    Component {
        id: inlineEditor
        Table.ValueEditor {
            theme: root.theme
            descriptor: root.descriptor
            mode: root.editorMode
            controlHeight: Math.max(36, root.height - 8)
            onSaved: value => root.commit(value)
            onCancelled: root.cancel()
        }
    }
    Loader {
        anchors.fill: parent
        active: root.editing && root.textPanel
        sourceComponent: Item {
            Component.onCompleted: Qt.callLater(function () {
                popup.openBelowItem(root, true, 4);
            })
            Controls.ScrollablePopup {
                id: popup
                parent: Overlay.overlay
                theme: root.theme
                preferredSurfaceWidth: ["multiline", "tags"].indexOf(root.editorMode) >= 0 ? 620 : Math.max(300, root.width)
                maximumSurfaceHeight: 520
                settledClosePolicy: Popup.CloseOnEscape
                onClosed: if (root.editing)
                    root.cancel()
                Table.ValueEditor {
                    theme: root.theme
                    width: parent.width
                    height: implicitHeight
                    descriptor: root.descriptor
                    mode: root.editorMode
                    count: Math.max(1, root.controller.selected_result_node_ids.length)
                    onSaved: value => {
                        root.commit(value);
                        popup.close();
                    }
                    onCancelled: popup.close()
                }
            }
        }
    }
}

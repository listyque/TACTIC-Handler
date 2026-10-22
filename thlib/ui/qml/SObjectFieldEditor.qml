import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "controls" as Controls
import "features/objects" as Objects

Item {
    id: root
    required property var theme
    required property string editorWindowId
    readonly property bool compact: width < 660
    readonly property real minimumFieldCardWidth: 430
    readonly property int maximumFieldColumns: 3
    readonly property var model: sobjectEditorController.presentation
    function insertBatchToken(token) {
        const owner = root.Window.window;
        const editor = owner ? owner.activeFocusItem : null;
        if (editor && editor.insertBatchToken)
            editor.insertBatchToken(token);
    }
    function action(event) {
        if (event.type === "mode")
            sobjectEditorController.set_batch_enabled(event.value === "batch");
        else if (event.type === "count")
            sobjectEditorController.set_batch_count(event.value);
        else if (event.type === "item")
            sobjectEditorController.show_batch_item(event.value);
        else if (event.type === "token")
            root.insertBatchToken(event.value);
        else if (event.type === "back")
            sobjectEditorController.leave_batch_preview();
        else if (event.type === "refresh")
            sobjectEditorController.begin_session();
        else if (event.type === "cancel")
            windowModel.close_window(root.editorWindowId);
        else if (event.type === "check")
            sobjectEditorController.check_saved();
        else if (event.type === "submit") {
            if (root.model.batchEnabled && !root.model.batchPreview)
                sobjectEditorController.preview_batch();
            else
                sobjectEditorController.submit();
        }
    }
    Connections {
        target: sobjectEditorController
        function onSaved(searchKey) {
            windowModel.close_window(root.editorWindowId);
        }
    }
    Controls.ImageFileDialog {
        id: previewFileDialog
        allowMultiple: true
        onImagesSelected: (row, images) => {
            if (row >= 0)
                sobjectFieldModel.add_preview_files(row, images);
        }
    }
    Rectangle {
        anchors.fill: parent
        color: root.theme.panelDeep
    }
    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        Objects.ObjectEditorSurface {
            Layout.fillWidth: true
            Layout.preferredHeight: implicitHeight
            theme: root.theme
            model: root.model
            part: "header"
            onEvent: event => root.action(event)
        }
        ScrollView {
            id: formScroll
            objectName: "sobjectEditorFormScroll"
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: availableWidth
            contentHeight: formColumn.implicitHeight
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            ScrollBar.vertical: Controls.ScrollBar {
                objectName: "sobjectEditorFormVerticalScrollBar"
                theme: root.theme
                flickableTarget: formScroll.contentItem
            }
            Column {
                id: formColumn
                width: formScroll.availableWidth
                topPadding: 18
                bottomPadding: 20
                spacing: 10
                Objects.ObjectEditorSurface {
                    width: Math.max(0, parent.width - 40)
                    height: implicitHeight
                    x: 20
                    theme: root.theme
                    model: root.model
                    part: "tools"
                    views: ({
                            batchCount: batchCountPort
                        })
                    onEvent: event => root.action(event)
                }
                SObjectFieldGrid {
                    objectName: "sobjectEditorFieldFlow"
                    width: Math.max(0, parent.width - 40)
                    x: 20
                    theme: root.theme
                    fieldModel: sobjectFieldModel
                    itemPrefix: "sobjectEditorFieldItem_"
                    repeaterObjectName: "sobjectEditorFieldRepeater"
                    editorBusy: sobjectEditorController.busy
                    editorMode: sobjectEditorController.mode
                    minimumCellWidth: root.minimumFieldCardWidth
                    maximumColumns: root.maximumFieldColumns
                    onPreviewRequested: row => previewFileDialog.openForRow(row)
                }
            }
        }
        Objects.ObjectEditorSurface {
            objectName: "sobjectEditorFooter"
            Layout.fillWidth: true
            Layout.preferredHeight: implicitHeight
            theme: root.theme
            model: root.model
            part: "footer"
            onEvent: event => root.action(event)
        }
    }
    Component {
        id: batchCountPort
        Controls.SpinBox {
            theme: root.theme
            from: 2
            to: 100
            value: root.model.batchCount
            enabled: !root.model.busy
            Accessible.name: qsTr("Number of objects")
            onRealValueEdited: value => sobjectEditorController.set_batch_count(value)
        }
    }
}

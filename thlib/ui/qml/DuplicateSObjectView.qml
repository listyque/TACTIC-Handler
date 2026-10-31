import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls
import "tactic_frame" as Frame
import "tactic_frame/features/objects/duplicate.ui.mjs" as UI

Item {
    id: root
    objectName: "duplicateSObjectView"
    required property var theme
    readonly property var model: sobjectDuplicateController.presentation
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property bool compactLayout: width < 700
    readonly property bool compactFooter: width < 1000
    readonly property real minimumFieldCardWidth: 430
    readonly property int maximumFieldColumns: 3
    function action(event) {
        if (event.type === "step")
            sobjectDuplicateController.set_step(event.value);
        else if (event.type === "remember")
            sobjectDuplicateController.rememberSettings = event.value;
        else if (event.type === "relation")
            sobjectDuplicateController.set_relation_mode(event.index, event.value);
        else if (event.type === "choice")
            sobjectDuplicateController.set_process_choice(event.index, event.name, event.value);
        else if (event.type === "back")
            sobjectDuplicateController.previous_step();
        else if (event.type === "next")
            sobjectDuplicateController.next_step();
        else if (event.type === "duplicate")
            sobjectDuplicateController.duplicate();
        else if (event.type === "retry")
            sobjectDuplicateController.retry();
        else if (event.type === "cancel")
            sobjectDuplicateController.cancel();
        else if (event.type === "help")
            windowModel.open_help("duplicating_objects");
    }
    Controls.ImageFileDialog {
        id: previewFileDialog
        onImageSelected: (row, image) => {
            if (row >= 0)
                sobjectDuplicateFieldModel.setValue(row, image);
        }
    }
    Rectangle {
        anchors.fill: parent
        color: root.theme.panelDeep
    }
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: root.theme.spacing.content
        spacing: root.theme.spacing.content
        Frame.FrameView {
            Layout.fillWidth: true
            Layout.preferredHeight: scene.height
            theme: root.theme
            scene: UI.header(root.model, width, root.language)
            onEvent: event => root.action(event)
        }
        Frame.FrameView {
            objectName: "duplicateSObjectSteps"
            Layout.fillWidth: true
            Layout.preferredHeight: scene.height
            theme: root.theme
            scene: UI.tabs(root.model, width, root.language)
            onEvent: event => root.action(event)
        }
        ScrollView {
            id: pages
            objectName: "duplicateSObjectPageLoader"
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: availableWidth
            contentHeight: content.implicitHeight
            leftPadding: 6
            rightPadding: 10 + UI.scrollbarExtent
            topPadding: 6
            bottomPadding: 10
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            ScrollBar.vertical: Controls.ScrollBar {
                theme: root.theme
                flickableTarget: pages.contentItem
            }
            Column {
                id: content
                width: pages.availableWidth
                spacing: 10
                Frame.FrameView {
                    width: parent.width
                    height: scene.height
                    theme: root.theme
                    scene: UI.body(root.model, width, root.language)
                    onEvent: event => root.action(event)
                }
                SObjectFieldGrid {
                    objectName: "duplicateFieldFlow"
                    visible: root.model.ready && root.model.step === 0 && !root.model.busy
                    width: parent.width
                    height: visible ? implicitHeight : 0
                    theme: root.theme
                    fieldModel: sobjectDuplicateFieldModel
                    itemPrefix: "duplicateFieldItem_"
                    repeaterObjectName: "duplicateFieldRepeater"
                    editorBusy: root.model.saving
                    minimumCellWidth: root.minimumFieldCardWidth
                    maximumColumns: root.maximumFieldColumns
                    onPreviewRequested: row => previewFileDialog.openForRow(row)
                }
            }
        }
        Frame.FrameView {
            objectName: "duplicateSObjectFooter"
            Layout.fillWidth: true
            Layout.preferredHeight: scene.height
            theme: root.theme
            scene: UI.footer(root.model, width, root.language)
            onEvent: event => root.action(event)
        }
    }
    ContentLoadingOverlay {
        objectName: "duplicateLoadingOverlay"
        readonly property var loadingState: UI.busyState(root.model, root.language)
        theme: root.theme
        visible: !!loadingState
        x: pages.x
        y: pages.y
        width: pages.width
        height: pages.height
        message: loadingState ? loadingState.message : ""
        cancellable: loadingState ? loadingState.cancellable : false
        onCancelRequested: sobjectDuplicateController.cancel()
    }
}

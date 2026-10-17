import QtQuick
import "tactic_frame" as Frame
import "tactic_frame/features/search/visibility.ui.mjs" as UI
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    required property string windowId
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property bool compact: width < 520

    Rectangle {
        anchors.fill: parent
        color: root.theme.panelDeep
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 6

        Frame.FrameView {
            objectName: "processFilterHeader"
            Layout.fillWidth: true
            Layout.preferredHeight: scene.contentHeight
            theme: root.theme
            scene: UI.header({
                title: processFilterEditorController.context_title
            }, width, root.language)
        }
        Controls.ProcessSelectionTree {
            Layout.fillWidth: true
            Layout.fillHeight: true
            theme: root.theme
            treeModel: processFilterModel
            treeController: processFilterEditorController
            validContext: processFilterEditorController.valid_context
            emptyText: qsTr("Select a Search Tab first")
            treeObjectName: "processFilterTree"
            rowObjectName: "processFilterRow"
        }

        Frame.FrameView {
            objectName: "processFilterFooter"
            Layout.fillWidth: true
            Layout.preferredHeight: scene.contentHeight
            theme: root.theme
            scene: UI.footer({
                valid: processFilterEditorController.valid_context,
                dirty: processFilterEditorController.dirty
            }, width, root.language)
            onEvent: action => {
                if (action.type === "cancel") {
                    processFilterEditorController.cancel();
                    windowModel.close_window(root.windowId);
                } else if (action.type === "save")
                    processFilterEditorController.save();
                else if (action.type === "saveClose" && processFilterEditorController.save())
                    windowModel.close_window(root.windowId);
            }
        }
    }
}

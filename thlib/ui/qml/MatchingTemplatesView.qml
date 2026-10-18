import QtQuick
import QtQuick.Controls
import "tactic_frame" as Frame
import "tactic_frame/features/files/matching.ui.mjs" as UI

Item {
    id: root
    required property var theme
    required property string windowId
    property var controller: matchingTemplatesController
    property bool editing: false
    property real paneWidth: 0
    property int modelRevision: 0
    property string example: ""
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var frameModel: {
        modelRevision;
        return {
            selected: controller.selectedRow,
            record: controller.selectedTemplate,
            count: matchingTemplatesModel.count(),
            dirty: controller.dirty,
            result: UI.testResult(controller.testResult, language),
            example,
            processes: checkinOutController ? checkinOutController.processes : [],
            contexts: checkinOutController ? checkinOutController.contexts : [],
            editing,
            paneWidth
        };
    }
    Component.onCompleted: {
        controller.begin_edit();
        example = controller.testExample;
    }
    Component.onDestruction: if (controller)
        controller.cancel()
    Connections {
        target: matchingTemplatesModel
        function onContentReplaced() {
            root.modelRevision++;
        }
    }
    function dispatch(action, source) {
        if (action.type === "select") {
            controller.select_row(action.index);
            if (action.focus) {
                const controlId = "matchingTemplateSelect_" + controller.selectedTemplate.templateId;
                Qt.callLater(() => presenter.focusListRow("matchingTemplatesList", action.index, controlId));
            } else
                editing = true;
        } else if (action.type === "enabled") {
            controller.select_row(action.index);
            controller.update_selected("enabled", action.value);
        } else if (action.type === "field")
            controller.update_selected(action.field, action.value);
        else if (action.type === "example")
            example = action.value;
        else if (action.type === "test")
            controller.test_pattern(example);
        else if (action.type === "create") {
            controller.create_template();
            editing = true;
        } else if (action.type === "duplicate")
            controller.duplicate_selected();
        else if (action.type === "move_up")
            controller.move_selected(-1);
        else if (action.type === "move_down")
            controller.move_selected(1);
        else if (action.type === "delete")
            controller.delete_selected();
        else if (action.type === "save") {
            if (controller.save())
                windowModel.close_window(windowId);
        } else if (action.type === "close") {
            controller.cancel();
            windowModel.close_window(windowId);
        } else if (action.type === "back")
            editing = false;
        else if (action.type === "splitter")
            paneWidth = action.value;
        else if (action.type === "menu")
            templateMenu.toggleBelow(source);
    }
    Rectangle {
        anchors.fill: parent
        color: root.theme.panelDeep
    }
    Frame.FrameView {
        id: presenter
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe(root.frameModel, width, height, root.language)
        models: ({
                templates: matchingTemplatesModel
            })
        describeRow: (list, record) => UI.row(root.frameModel, record, list.width - 16, root.language)
        onEvent: (action, source) => root.dispatch(action, source)
    }
    ActionMenu {
        id: templateMenu
        parent: Overlay.overlay
        theme: root.theme
        preferredWidth: 220
        actions: UI.actions(root.frameModel)
        onTriggered: command => root.dispatch({
                type: command
            })
    }
}

import QtQuick
import "controls" as Controls
import "tactic_frame" as Frame
import "tactic_frame/features/projects/project.ui.mjs" as UI

Item {
    id: root
    required property var theme
    readonly property var controller: projectCreationController
    property bool discard: false
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var model: ({
            product: "TACTIC HANDLER",
            style: theme.style,
            draft: controller.draft,
            step: controller.step,
            ready: controller.ready,
            busy: controller.busy,
            createdCode: controller.createdCode,
            error: controller.error,
            templates: controller.templates.map(row => Object.assign({}, row, {
                    dataLabel: true
                })),
            themes: controller.themes.map(row => Object.assign({}, row, {
                    dataLabel: true
                })),
            image: !!controller.draft.previewPath,
            uncertain: controller.uncertain,
            discard
        })
    function requestClose() {
        if (controller.busy)
            return false;
        if (UI.wizardDirty(controller.draft, controller.draft.previewPath) || controller.createdCode) {
            discard = true;
            return false;
        }
        return true;
    }
    function dispatch(action) {
        if (action.type === "field")
            controller.set_value(action.field, action.value);
        else if (action.type === "page")
            controller.select_step(Number(action.value));
        else if (action.type === "next")
            controller.next_step();
        else if (action.type === "back")
            controller.previous_step();
        else if (action.type === "submit")
            controller.submit();
        else if (action.type === "refresh")
            controller.reload_catalog();
        else if (action.type === "templates")
            windowModel.show_child_window("project_templates", "project_wizard");
        else if (action.type === "help")
            windowModel.open_help("project_creation");
        else if (action.type === "keep")
            discard = false;
        else if (action.type === "discard" && !controller.busy)
            windowModel.close_window("project_wizard");
        else if (action.type === "close" && requestClose())
            windowModel.close_window("project_wizard");
    }
    Connections {
        target: root.controller
        function onSessionStarted() {
            root.discard = false;
        }
        function onCompleted() {
            windowModel.close_window("project_wizard");
        }
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.wizard(root.model, width, height, root.language)
        views: ({
                image: projectImage
            })
        onEvent: action => root.dispatch(action)
    }
    Component {
        id: projectImage
        Controls.ImagePicker {
            theme: root.theme
            previewSize: 160
            previewUrl: root.controller.previewUrl
            stagedPath: root.controller.draft.previewPath || ""
            fallbackText: root.controller.draft.title || root.controller.draft.code || ""
            enabled: !root.controller.busy && !root.controller.createdCode && root.controller.step !== 3
            dialogTitle: qsTr("Choose project preview")
            onSelectionRequested: image => root.controller.set_value("previewPath", image)
        }
    }
}

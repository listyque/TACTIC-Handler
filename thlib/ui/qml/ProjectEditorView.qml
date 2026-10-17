import QtQuick
import "controls" as Controls
import "tactic_frame" as Frame
import "tactic_frame/features/projects/editor.ui.mjs" as UI

Item {
    id: root
    required property var theme
    property bool discard: false
    readonly property var controller: projectEditorController
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var model: ({
            values: {
                code: controller.code,
                title: controller.title,
                category: controller.category,
                type: controller.projectType,
                description: controller.description,
                archived: controller.archived,
                isTemplate: controller.isTemplate
            },
            stagedImage: !!controller.previewPath,
            busy: controller.busy,
            error: controller.error,
            dirty: controller.dirty,
            discard,
            style: theme.style
        })
    function requestClose() {
        if (controller.busy)
            return false;
        if (controller.dirty) {
            discard = true;
            return false;
        }
        return true;
    }
    function dispatch(action) {
        if (action.type === "field") {
            if (action.field === "title")
                controller.set_title(action.value);
            else if (action.field === "category")
                controller.set_category(action.value);
            else if (action.field === "type")
                controller.set_project_type(action.value);
            else if (action.field === "description")
                controller.set_description(action.value);
            else if (action.field === "archived")
                controller.set_archived(action.value);
            else if (action.field === "isTemplate")
                controller.set_template(action.value);
        } else if (action.type === "save")
            controller.submit();
        else if (action.type === "help")
            windowModel.open_help("project_creation");
        else if (action.type === "keep")
            discard = false;
        else if (action.type === "discard" && !controller.busy)
            windowModel.close_window("project_editor");
        else if (action.type === "close" && requestClose())
            windowModel.close_window("project_editor");
    }
    Connections {
        target: root.controller
        function onSessionStarted() {
            root.discard = false;
        }
        function onSaved(projectCode) {
            windowModel.close_window("project_editor");
        }
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe(root.model, width, height, root.language)
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
            stagedPath: root.controller.previewPath
            fallbackText: root.controller.code.slice(0, 2).toUpperCase()
            dialogTitle: qsTr("Choose project preview")
            enabled: !root.controller.busy
            statusText: stagedPath ? qsTr("A new preview is ready to be queued") : qsTr("Current project preview")
            description: qsTr("Choose a large image; the repository web representation is used automatically when available.")
            onSelectionRequested: image => root.controller.set_preview_path(image)
        }
    }
}

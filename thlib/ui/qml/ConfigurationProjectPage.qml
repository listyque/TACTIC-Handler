import QtQuick
import "tactic_frame" as Frame
import "tactic_frame/features/projects/catalog.ui.mjs" as UI

Item {
    id: root
    required property var theme
    property var selected: ({})
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var model: ({
            selected,
            currentCode: appController.current_project_code,
            currentTitle: appController.current_project_title,
            canManage: true,
            counts: {
                retired: projectModel.retiredCount,
                templates: projectModel.templateCount,
                builtins: projectModel.builtinCount
            },
            totalCount: projectModel.totalCount,
            visibleCount: projectModel.visibleCount,
            busy: projectCreationController.busy,
            error: projectCreationController.error,
            filters: {
                retired: projectModel.showRetired,
                templates: projectModel.showTemplates,
                builtins: projectModel.showBuiltins
            }
        })
    Component.onCompleted: appController.refresh_projects()
    function dispatch(action) {
        if (action.type === "select")
            selected = action.record;
        else if (action.type === "filter") {
            if (action.field === "retired")
                projectModel.setShowRetired(action.value);
            else if (action.field === "templates")
                projectModel.setShowTemplates(action.value);
            else if (action.field === "builtins")
                projectModel.setShowBuiltins(action.value);
        } else if (action.type === "activate")
            appController.select_project(action.code);
        else if (action.type === "deactivate")
            appController.deactivate_project();
        else if (action.type === "edit")
            appController.edit_project(action.code);
        else if (action.type === "archive")
            projectCreationController.export_project(action.code);
        else if (action.type === "create")
            windowModel.show_window("project_wizard");
        else if (action.type === "refresh")
            appController.refresh_projects();
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe(root.model, width, height, root.language)
        models: ({
                projects: projectModel
            })
        describeRow: (list, record) => UI.row(root.model, record, list.width - 16, root.language)
        onEvent: action => root.dispatch(action)
    }
}

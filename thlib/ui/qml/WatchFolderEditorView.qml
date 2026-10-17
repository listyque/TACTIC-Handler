import QtQuick
import "tactic_frame" as Frame
import "tactic_frame/features/objects/watch.ui.mjs" as UI

Item {
    id: root
    required property var theme
    property string repositoryChoice: ""
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var selectedRepositories: (watchFoldersController.repositories || []).filter(row => (watchFoldersController.editor.repositories || []).indexOf(row.value) >= 0)
    readonly property var availableRepositories: UI.available(watchFoldersController.repositories || [], watchFoldersController.editor.repositories || [], language)
    readonly property string choice: availableRepositories.some(row => row.value === repositoryChoice) ? repositoryChoice : availableRepositories.length ? availableRepositories[0].value : ""
    readonly property var frameModel: ({
            path: watchFoldersController.editor.path || "",
            busy: watchFoldersController.busy,
            available: availableRepositories,
            choice: choice,
            selectedCount: selectedRepositories.length,
            error: watchFoldersController.message,
            canSave: watchFoldersController.canSaveEditor
        })
    function dispatch(action) {
        if (action.type === "path")
            watchFoldersController.set_editor_value("path", action.value);
        else if (action.type === "choice")
            repositoryChoice = action.value;
        else if (action.type === "remove")
            watchFoldersController.toggle_editor_repository(action.value, false);
        else if (action.type === "add") {
            if (choice === "__all__") {
                for (const row of watchFoldersController.repositories)
                    watchFoldersController.toggle_editor_repository(row.value, true);
            } else if (choice)
                watchFoldersController.toggle_editor_repository(choice, true);
        } else if (action.type === "save")
            watchFoldersController.save_edit();
        else if (action.type === "cancel")
            watchFoldersController.cancel_edit();
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe(root.frameModel, width, height, root.language)
        models: ({
                repositories: root.selectedRepositories
            })
        describeRow: (list, row) => UI.repositoryRow(root.frameModel, row, list.width - 16, root.language)
        onEvent: action => root.dispatch(action)
    }
}

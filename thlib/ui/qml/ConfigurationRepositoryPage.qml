import QtQuick
import "tactic_frame" as Frame
import "tactic_frame/features/configuration/repository.ui.mjs" as UI

Item {
    id: root
    required property var theme
    property int modelRevision: 0
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var model: {
        modelRevision;
        const records = [];
        for (let index = 0; index < repositoryEditorModel.count(); index++) {
            const record = repositoryEditorModel.get(index);
            records.push(Object.assign({}, record, {
                path: Qt.platform.os === "windows" ? record.windowsPath : record.linuxPath
            }));
        }
        return {
            native: true,
            style: theme.style,
            records,
            currentTitle: repositoryEditorController.current_title,
            currentPath: repositoryEditorController.current_path,
            busy: repositoryEditorController.busy,
            notice: repositoryEditorController.message
        };
    }
    function refresh() {
        repositoryEditorController.begin_edit();
    }
    Component.onCompleted: refresh()
    Connections {
        target: repositoryEditorModel
        function onDataChanged() {
            root.modelRevision++;
        }
        function onContentReplaced() {
            root.modelRevision++;
        }
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.summary(root.model, width, height, root.language)
        onEvent: action => {
            if (action.type === "edit")
                windowModel.show_window("repository_editor");
            else if (action.type === "check")
                repositoryEditorController.check_paths();
        }
    }
}

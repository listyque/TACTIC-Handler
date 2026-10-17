import QtQuick
import "tactic_frame" as Frame
import "." as Objects
import "features/objects" as ObjectParts
import "tactic_frame/features/objects/delete.ui.mjs" as UI

Item {
    id: root
    objectName: "deleteSObjectView"
    required property var theme
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var model: sobjectDeleteController.presentation
    readonly property var scene: UI.describe(root.model, width, height, root.language)
    readonly property var dataModels: UI.models(root.model, root.language)
    Component {
        id: dependencyPort
        ObjectParts.ObjectDependencyList {
            theme: root.theme
            rows: frameNode ? root.dataModels[frameNode.source] || [] : []
        }
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: root.scene
        models: root.dataModels
        views: ({
                dependencies: {
                    component: dependencyPort,
                    nodeProps: true
                }
            })
        describeRow: (list, record) => list.id === "deleteSObjectTargets" ? UI.target(record, list.width - 16) : UI.dependency(record, list.width - 16)
        onEvent: action => {
            if (action.type === "help")
                windowModel.open_help("deleting_objects");
            else if (action.type === "cancel")
                sobjectDeleteController.cancel();
            else if (action.type === "delete")
                sobjectDeleteController.confirm_delete();
            else if (action.type === "retry")
                sobjectDeleteController.retry();
            else if (action.type === "expand")
                sobjectDeleteController.toggle_group(action.index);
            else if (action.type === "check")
                sobjectDeleteController.set_group_checked(action.index, action.value);
        }
    }
    Objects.ContentLoadingOverlay {
        theme: root.theme
        visible: !!root.scene.loading
        x: root.scene.loading ? root.scene.loading.bounds.x : 0
        y: root.scene.loading ? root.scene.loading.bounds.y : 0
        width: root.scene.loading ? root.scene.loading.bounds.width : 0
        height: root.scene.loading ? root.scene.loading.bounds.height : 0
        message: root.scene.loading ? root.scene.loading.message : ""
        cancellable: root.scene.loading ? root.scene.loading.cancellable : false
        onCancelRequested: sobjectDeleteController.cancel()
    }
}

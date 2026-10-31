import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/configuration/database_resources.ui.mjs" as UI

Item {
    id: root
    required property var theme
    required property var controller
    property string language: "en"
    Component.onCompleted: controller.open()
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.page({
            document: root.controller.document,
            metadata: root.controller.metadata,
            catalog: root.controller.catalog,
            identity: root.controller.identity,
            canWrite: root.controller.canWrite,
            busy: root.controller.busy,
            dirty: root.controller.dirty,
            uncertain: root.controller.writeUncertain,
            error: root.controller.error,
            confirm: root.controller.confirmation,
            database: root.controller.database,
            project: root.controller.projectTarget
        }, width, height, root.language)
        onEvent: action => {
            if (action.type === "field")
                root.controller.set_field(action.field, action.value);
            else if (action.type === "select")
                root.controller.choose(action.value);
            else if (action.type === "new")
                root.controller.choose("new");
            else if (action.type === "refresh")
                root.controller.reload();
            else if (action.type === "discard")
                root.controller.discard();
            else if (action.type === "save")
                root.controller.save();
            else if (action.type === "database")
                root.controller.set_database(action.value);
            else if (action.type === "project")
                root.controller.set_project(action.value);
            else
                root.controller.action(action.type);
        }
    }
}

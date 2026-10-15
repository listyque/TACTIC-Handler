import QtQuick
import QtQuick.Controls
import "../../../controls" as Controls
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/administration/schema/schema_delete.ui.mjs" as UI

Controls.Dialog {
    id: root
    required property var controller
    property string language: typeof localizationController !== "undefined" ? localizationController.current_language : qsTr("Search Types") === "Search Types" ? "en" : "ru"
    readonly property var frameModel: ({
            identity: controller.identity,
            schemaRevision: controller.schemaRevision,
            metadata: controller.metadata,
            canWrite: controller.canWrite,
            busy: controller.busy,
            deleting: controller.deleting,
            uncertain: controller.writeUncertain,
            error: controller.error,
            confirmation: controller.document.confirmation || ""
        })
    objectName: "adminDeleteSearchTypeConfirmation"
    title: qsTr("Delete Search Type from project")
    modal: true
    focus: true
    width: Math.min(540, parent.width - 24)
    height: Math.min(700, parent.height - 24)
    anchors.centerIn: parent
    closePolicy: controller.deleting ? Popup.NoAutoClose : Popup.CloseOnEscape
    standardButtons: Dialog.NoButton
    onOpened: body.focusControl("adminDeleteSearchTypeCancel")
    onClosed: controller.cancel()
    function dispatch(event) {
        for (const command of UI.transition(frameModel, event)) {
            if (command.type === "confirmation")
                controller.set_field("confirmation", command.value);
            else if (command.type === "delete")
                controller.save();
            else if (command.type === "reload")
                controller.reload(true);
            else if (command.type === "close")
                root.close();
        }
    }
    Connections {
        target: root.controller
        function onCommitted() {
            root.close();
        }
    }
    contentItem: Frame.FrameView {
        id: body
        theme: root.theme
        scene: UI.describe(root.frameModel, width, height, root.language)
        onEvent: action => root.dispatch(action)
    }
}

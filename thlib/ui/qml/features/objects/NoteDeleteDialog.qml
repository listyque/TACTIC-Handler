import QtQuick
import QtQuick.Controls
import "../../controls" as Controls
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/objects/note.ui.mjs" as UI

Controls.Dialog {
    id: root
    required property var controller
    property int row: -1
    property string searchKey: ""
    property string text: ""
    property bool submitted: false
    title: qsTr("Delete note?")
    modal: true
    closePolicy: controller.busy ? Popup.NoAutoClose : Popup.CloseOnEscape
    standardButtons: Dialog.NoButton
    onOpened: submitted = false
    contentItem: Frame.FrameView {
        id: content
        theme: root.theme
        implicitHeight: scene.height
        scene: UI.remove({
            text: root.text,
            busy: root.controller.busy,
            uncertain: root.controller.uncertain,
            error: root.controller.error
        }, width, typeof localizationController === "undefined" ? "en" : localizationController.current_language)
        onEvent: event => {
            if (event.type === "text")
                root.text = event.value;
            else if (event.type === "cancel")
                root.close();
            else if (event.type === "delete") {
                root.submitted = true;
                root.controller.remove(root.row, root.searchKey);
            }
        }
    }
    Connections {
        target: root.controller
        function onStateChanged() {
            if (root.opened && root.submitted && !root.controller.busy) {
                root.submitted = false;
                if (!root.controller.error)
                    root.close();
            }
        }
    }
}

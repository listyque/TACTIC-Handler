import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import "controls" as Controls
import "tactic_frame" as Frame
import "tactic_frame/features/messages/attachments.ui.mjs" as UI

Frame.FrameView {
    id: root
    required property var controller
    required property var attachmentModel
    property bool previews: false
    readonly property string language: typeof localizationController === 'undefined' ? 'en' : localizationController.current_language
    implicitWidth: scene.width
    implicitHeight: 26
    scene: UI.controls({
        count: controller.count,
        busy: controller.busy,
        canCancel: true
    }, language)
    function openDrafts(source) {
        draftsPopup.toggleBelowItem(source || root, true, 6);
    }
    onEvent: (action, source) => {
        if (action.type === "choose")
            fileDialog.open();
        else if (action.type === "paste")
            controller.add_clipboard_image();
        else if (action.type === "drafts-press")
            draftsPopup.rememberSourceOpen();
        else if (action.type === "drafts")
            openDrafts(source);
        else if (action.type === "clear")
            controller.clear();
        else if (action.type === "cancel")
            controller.cancel();
    }
    FileDialog {
        id: fileDialog
        title: qsTr("Attach files")
        fileMode: FileDialog.OpenFiles
        onAccepted: root.controller.add_files(selectedFiles)
    }
    Controls.Popup {
        id: draftsPopup
        theme: root.theme
        parent: Overlay.overlay
        width: Math.min(340, Math.max(250, (parent ? parent.width : root.width) - 24))
        height: Math.min(300, Math.max(150, (parent ? parent.height : root.height) - 30))
        padding: 10
        contentItem: Frame.FrameView {
            theme: root.theme
            scene: UI.panel({
                previews: root.previews
            }, width, height, root.language)
            models: ({
                    drafts: root.attachmentModel
                })
            describeRow: (node, record) => UI.row(Object.assign({}, record, {
                    previews: root.previews,
                    busy: root.controller.busy
                }), Math.max(0, node.width - 16), root.language)
            onEvent: action => {
                if (action.type === "previews")
                    root.previews = action.value;
                else if (action.type === "remove") {
                    for (let index = 0; index < root.attachmentModel.count(); index++)
                        if (root.attachmentModel.get(index).token === action.key) {
                            root.controller.remove(index);
                            break;
                        }
                }
            }
        }
    }
    Connections {
        target: root.controller
        function onStateChanged() {
            if (!root.controller.count)
                draftsPopup.close();
        }
    }
}

import QtQuick
import QtQuick.Dialogs
import "../../controls" as Controls
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/scripts/request.ui.mjs" as UI

Item {
    id: root
    required property var theme
    property var controller: agentRequestController
    readonly property string uiLanguage: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe(root.controller.model, width, height, root.uiLanguage)
        views: ({
                context: {
                    component: chatPort,
                    nodeProps: true
                },
                transcript: {
                    component: chatPort,
                    nodeProps: true
                },
                attachments: {
                    component: chatPort,
                    nodeProps: true
                }
            })
        onEvent: function (action) {
            if (action.type === "attach")
                fileDialog.open();
            else
                root.controller.handle(action.type, action.value === undefined ? "" : action.value);
        }
    }
    Component {
        id: chatPort
        AgentChatPort {
            theme: root.theme
            language: root.uiLanguage
            previews: root.controller.model.previews || ({})
            onAction: action => root.controller.handle(action.type, action.value === undefined ? "" : action.value)
        }
    }
    FileDialog {
        id: fileDialog
        title: qsTr("Attach files")
        fileMode: FileDialog.OpenFiles
        onAccepted: root.controller.add_files(selectedFiles)
    }
    Shortcut {
        sequences: [StandardKey.Paste]
        enabled: root.visible && root.controller.clipboard_has_attachment
        onActivated: root.controller.paste_attachment()
    }
    Controls.AttachmentDropArea {
        anchors.fill: parent
        theme: root.theme
        attachmentController: root.controller
        enabled: !root.controller.model.uploading && !root.controller.model.busy
    }
}

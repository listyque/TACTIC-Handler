import QtQuick
import QtQuick.Dialogs
import "../../controls" as Controls
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/scripts/request.ui.mjs" as UI
import "../../tactic_frame/features/scripts/history.ui.mjs" as History

Item {
    id: root
    required property var theme
    property var controller: agentRequestController
    readonly property string uiLanguage: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe(root.controller.model, width, height, root.uiLanguage)
        models: ({
                agentHistoryRows: History.rows(root.controller.model, root.uiLanguage)
            })
        describeRow: function (node, record) {
            return History.row(root.controller.model, record, node.width - 16, root.uiLanguage);
        }
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
                },
                permissions: {
                    component: chatPort,
                    nodeProps: true
                }
            })
        onEvent: function (action) {
            const changed = History.change(root.controller.model, action, width < 940);
            if (changed) {
                root.controller.set_history(changed);
                return;
            }
            if ((action.type === "select" || action.type === "historyNew") && width < 940)
                root.controller.set_history(Object.assign({}, root.controller.model.history, {
                    mobile: false
                }));
            if (action.type === "historyEdit" && !action.value)
                root.controller.set_history(Object.assign({}, root.controller.model.history, {
                    mobile: width < 940
                }));
            if (action.type === "providers")
                agentProvidersController.open();
            else if (action.type === "attach")
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
            onAction: function (action) {
                if (action.type === "providers")
                    agentProvidersController.open();
                else
                    root.controller.handle(action.type, action.value === undefined ? "" : action.value);
            }
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

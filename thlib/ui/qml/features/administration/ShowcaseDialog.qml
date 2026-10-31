pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import "../../controls" as Controls
import "../../tactic_frame/core/foundation.mjs" as Foundation

Item {
    id: root
    required property var theme
    property var frameNode: ({})
    signal event(var action)
    property string outcome: ""
    function synchronize() {
        if (frameNode.open && !dialog.visible) {
            outcome = "";
            dialog.open();
        } else if (!frameNode.open && dialog.visible)
            dialog.close();
    }
    onFrameNodeChanged: Qt.callLater(synchronize)
    Component.onCompleted: synchronize()
    Component.onDestruction: dialog.close()
    Controls.Dialog {
        id: dialog
        objectName: "sampleConfirmation"
        theme: root.theme
        parent: Overlay.overlay
        width: Math.min(root.frameNode.popupWidth || 440, parent ? parent.width - 24 : 440)
        x: parent ? (parent.width - width) / 2 : 0
        y: parent ? (parent.height - height) / 2 : 0
        title: root.frameNode.text || ""
        translateTitle: false
        modal: true
        contentItem: Label {
            text: root.frameNode.message || ""
            color: root.frameNode.error ? root.theme.error : root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pixelSize: Foundation.textStyles.body
            wrapMode: Text.Wrap
        }
        footer: Controls.DialogActions {
            theme: root.theme
            Controls.Button {
                objectName: "sampleConfirmCancel"
                theme: root.theme
                text: root.frameNode.cancelText || qsTr("Cancel")
                onClicked: dialog.reject()
            }
            Controls.Button {
                objectName: "sampleConfirmApply"
                theme: root.theme
                text: root.frameNode.acceptText || qsTr("Apply")
                enabled: !!root.frameNode.enabled
                onClicked: {
                    root.outcome = "accept";
                    dialog.accept();
                }
            }
        }
        onClosed: if (root.frameNode.open)
            root.event(Object.assign({}, root.frameNode.action, {
                value: root.outcome || "cancel"
            }))
    }
}

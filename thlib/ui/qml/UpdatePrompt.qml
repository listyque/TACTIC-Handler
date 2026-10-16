import QtQuick
import "controls" as Controls
import "tactic_frame" as Frame
import "tactic_frame/controls/feedback/confirmation.ui.mjs" as Confirmation

Item {
    id: root
    required property var theme
    required property var controller
    required property var windows

    Connections {
        target: root.controller
        function onUpdateAvailable(version) {
            prompt.releaseVersion = version;
            prompt.open();
        }
    }

    Controls.Dialog {
        id: prompt
        objectName: "availableUpdateDialog"
        theme: root.theme
        property string releaseVersion: ""
        modal: true
        anchors.centerIn: parent
        width: Math.min(420, root.width - 24)
        title: qsTr("Update available")
        height: 310
        contentItem: Frame.FrameView {
            implicitHeight: 210
            theme: root.theme
            scene: Confirmation.describe({
                message: qsTr("Version %1 is available. Install it now?").arg(prompt.releaseVersion),
                accept: "Install update",
                reject: "Later",
                acceptId: "installUpdateButton"
            }, width, height, typeof localizationController === "undefined" ? "en" : localizationController.current_language)
            onEvent: action => {
                if (action.type === "accept")
                    prompt.accept();
                else
                    prompt.reject();
            }
        }
        onAccepted: {
            root.controller.install_selected();
            root.windows.show_window("update");
        }
    }
}

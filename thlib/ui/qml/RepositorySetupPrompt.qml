import QtQuick
import QtQuick.Controls
import "controls" as Controls
import "tactic_frame" as Frame
import "tactic_frame/features/files/repository_prompts.ui.mjs" as Prompts

Item {
    id: root

    required property var theme
    required property var applicationController
    required property var configurationController
    required property var repositoryController
    required property var windows
    required property bool smokeMode
    property bool shownThisSession: false
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language

    function evaluate() {
        if (root.smokeMode || root.shownThisSession || !root.repositoryController.configuration_loaded || !root.repositoryController.configuration_required)
            return;
        root.shownThisSession = true;
        setupDialog.open();
    }

    function refreshAfterConnection() {
        if (root.applicationController.server_state !== "online")
            return;
        root.repositoryController.begin_edit();
        Qt.callLater(root.evaluate);
    }

    Component.onCompleted: {
        refreshAfterConnection();
        Qt.callLater(root.evaluate);
    }

    Connections {
        target: root.applicationController

        function onServer_state_changed() {
            root.refreshAfterConnection();
        }
    }

    Connections {
        target: root.repositoryController

        function onConfigurationChanged() {
            Qt.callLater(root.evaluate);
            if (!root.repositoryController.configuration_required && setupDialog.opened)
                setupDialog.close();
        }
    }

    Controls.Dialog {
        id: setupDialog
        objectName: "repositorySetupPrompt"
        theme: root.theme
        modal: true
        anchors.centerIn: Overlay.overlay
        width: Math.min(480, root.width - 40)
        title: qsTr("Configure repository storage")
        closePolicy: Popup.NoAutoClose

        contentItem: Frame.FrameView {
            theme: root.theme
            implicitHeight: Math.max(180, Math.min(280, root.height - 180))
            scene: Prompts.setup({}, width, height, root.language)
            onEvent: action => {
                setupDialog.close();
                if (action.type === "accept") {
                    root.configurationController.select_page("repository");
                    root.windows.show_window("configuration");
                }
            }
        }
    }
}

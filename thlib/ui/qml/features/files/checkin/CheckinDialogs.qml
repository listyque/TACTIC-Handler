import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import "../../../controls" as Controls
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/files/object_checkin.ui.mjs" as UI

Item {
    id: root
    required property var theme
    required property var applicationController
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language

    function askMultiFileMode(fileCount) {
        multiFileCheckinDialog.fileCount = Number(fileCount);
        multiFileCheckinDialog.awaitingChoice = true;
        multiFileCheckinDialog.open();
    }
    FileDialog {
        id: checkinFilesDialog
        objectName: "checkinFilesDialog"
        title: qsTr("Choose files for check-in")
        fileMode: FileDialog.OpenFiles
        onAccepted: root.applicationController.submit_checkin_files(selectedFiles)
    }
    Controls.Dialog {
        id: revisionCheckinDialog
        objectName: "revisionCheckinDialog"
        parent: Overlay.overlay
        theme: root.theme
        modal: true
        anchors.centerIn: Overlay.overlay
        width: Math.max(0, Math.min(480, (Overlay.overlay ? Overlay.overlay.width : root.width) - 40))
        title: qsTr("Replace snapshot revision?")
        closePolicy: Popup.NoAutoClose
        onAccepted: root.applicationController.resolve_revision_checkin(true)
        onRejected: root.applicationController.resolve_revision_checkin(false)
        contentItem: Frame.FrameView {
            theme: root.theme
            implicitHeight: Math.min(170, Math.max(130, root.height - 138))
            scene: UI.revision({}, width, height, root.language)
            onEvent: action => {
                if (action.type === "accept")
                    revisionCheckinDialog.accept();
                else if (action.type === "reject")
                    revisionCheckinDialog.reject();
            }
        }
    }
    Controls.Dialog {
        id: multiFileCheckinDialog
        objectName: "multiFileCheckinDialog"
        parent: Overlay.overlay
        property int fileCount: 0
        property bool awaitingChoice: false
        function finish(mode) {
            if (!awaitingChoice)
                return;
            awaitingChoice = false;
            close();
            root.applicationController.resolve_multi_file_checkin(mode);
        }
        theme: root.theme
        modal: true
        dim: true
        focus: true
        anchors.centerIn: Overlay.overlay
        width: Math.max(0, Math.min(500, (Overlay.overlay ? Overlay.overlay.width : root.width) - 32))
        title: qsTr("Check in multiple files?")
        closePolicy: Popup.CloseOnEscape
        contentItem: Frame.FrameView {
            theme: root.theme
            readonly property var choice: UI.modeChoice({
                count: multiFileCheckinDialog.fileCount,
                mode: "group"
            }, width, root.language)
            implicitHeight: choice.height
            scene: ({
                    nodes: choice.nodes
                })
            onEvent: action => multiFileCheckinDialog.finish(action.value)
        }
        onClosed: {
            if (awaitingChoice) {
                awaitingChoice = false;
                root.applicationController.resolve_multi_file_checkin("cancel");
            }
        }
    }
    Connections {
        target: root.applicationController
        function onCheckinFilesRequested() {
            checkinFilesDialog.open();
        }
        function onRevisionCheckinConfirmationRequested() {
            revisionCheckinDialog.open();
        }
        function onMultiFileCheckinModeRequested(fileCount) {
            root.askMultiFileMode(fileCount);
        }
    }
}

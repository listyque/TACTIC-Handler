import QtQuick
import QtQuick.Controls
import "controls" as Controls
import "tactic_frame" as Frame
import "tactic_frame/features/files/ingest.ui.mjs" as UI

Item {
    id: root
    required property var theme
    required property var controller
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    function syncDialog() {
        if (controller.conflictPending && !dialog.opened)
            dialog.open();
        else if (!controller.conflictPending && dialog.opened)
            dialog.close();
    }
    Controls.Dialog {
        id: dialog
        objectName: "ingestConflictDialog"
        theme: root.theme
        parent: root
        title: qsTr("Resolve matching names")
        modal: true
        focus: true
        anchors.centerIn: parent
        width: Math.min(620, Math.max(0, parent.width - 24))
        closePolicy: Popup.CloseOnEscape
        standardButtons: Dialog.NoButton
        contentItem: Frame.FrameView {
            theme: root.theme
            scene: UI.conflict({
                conflictCount: root.controller.conflictCount,
                conflictNames: root.controller.conflictNames,
                canUpdateConflicts: root.controller.canUpdateConflicts
            }, width, root.language)
            implicitHeight: scene.height
            onEvent: action => root.controller.resolve_ingest_conflict(action.decision)
        }
        onClosed: if (root.controller.conflictPending)
            root.controller.resolve_ingest_conflict("cancel")
    }
    Connections {
        target: root.controller
        function onStateChanged() {
            root.syncDialog();
        }
    }
    Component.onCompleted: Qt.callLater(root.syncDialog)
}

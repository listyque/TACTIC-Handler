import QtQuick
import QtQuick.Controls

DropArea {
    id: root

    required property var theme
    required property var attachmentController
    property string promptText: qsTr("Drop files to attach")

    function stageUrls(urls) {
        if (!root.enabled || !urls || urls.length === 0
                || !root.attachmentController)
            return false
        root.attachmentController.add_files(urls)
        return true
    }

    onDropped: function(drop) {
        if (!drop.hasUrls || !root.stageUrls(drop.urls))
            return
        drop.acceptProposedAction()
    }

    DropTargetOverlay {
        visible: root.containsDrag
        theme: root.theme
        iconName: "attach-file"
        promptText: root.promptText
    }
}

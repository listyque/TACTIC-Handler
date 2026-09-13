import QtQuick
import "controls" as Controls

Controls.CompactIconButton {
    id: root

    required property var controller
    required property var sourceEditor
    required property string scriptToken
    signal syncRequested

    objectName: "scriptEditorSavedHistoryButton"
    iconName: "cloud-done"
    enabled: root.scriptToken.length > 0
        && (!root.controller.busy || root.controller.savedHistoryLoading)
    toolTip: qsTr("Saved versions")
    onPressed: historyPopup.rememberSourceOpen()
    onClicked: {
        root.syncRequested()
        historyPopup.toggleBelow(root)
    }

    RevisionHistoryPopup {
        id: historyPopup

        objectName: "scriptSavedRevisionHistoryPopup"
        theme: root.theme
        historyModel: root.controller.savedHistoryModel
        historyLoaded: root.controller.savedHistoryLoaded
        historyLoading: root.controller.savedHistoryLoading
        historyCount: root.controller.savedHistoryCount
        heading: qsTr("Saved versions")
        emptyText: qsTr("No earlier saved versions are available")
        entryObjectNamePrefix: "scriptSavedRevisionHistoryEntry-"

        onAboutToShow: root.controller.load_saved_history()
        onRevisionRequested: revisionId =>
            root.controller.restore_saved_revision(revisionId)
    }

    Connections {
        target: root.controller

        function onSavedRevisionReady(source) {
            root.sourceEditor.replaceText(source)
            root.syncRequested()
        }
    }
}

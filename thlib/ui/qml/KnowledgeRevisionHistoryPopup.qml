import QtQuick

RevisionHistoryPopup {
    id: root

    required property var controller

    objectName: "knowledgeRevisionHistoryPopup"
    historyModel: root.controller.historyModel
    historyLoaded: root.controller.historyLoaded
    historyLoading: root.controller.historyLoading
    historyCount: root.controller.historyCount
    heading: qsTr("Change history")
    emptyText: qsTr("No earlier revisions are available")
    entryObjectNamePrefix: "knowledgeRevisionHistoryEntry-"

    onAboutToShow: root.controller.load_history()
    onRevisionRequested: revisionId =>
        root.controller.preview_history_revision(revisionId)
}

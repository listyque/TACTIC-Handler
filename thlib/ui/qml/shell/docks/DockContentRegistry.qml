import QtQuick
import "../.."
import QtQuick.Window
import "../../features/table" as Table

Item {
    id: root
    required property var theme
    required property string pageTitle
    signal notice(string message)
    signal requestDockMenu(var sourceItem)

    readonly property Component results: resultsContent
    readonly property Component snapshot: snapshotContent
    readonly property Component tasks: tasksContent
    readonly property Component taskCalendar: taskCalendarContent
    readonly property Component timesheet: timesheetContent
    readonly property Component workReports: workReportsContent
    readonly property Component costReports: costReportsContent
    readonly property Component description: descriptionContent
    readonly property Component notes: notesContent
    readonly property Component dropPlate: dropPlateContent
    readonly property Component advancedSearch: advancedSearchContent
    readonly property Component repoSync: repoSyncContent
    readonly property Component commitQueue: commitQueueContent
    readonly property Component databaseEditor: databaseEditorContent
    readonly property Component watchFolders: watchFoldersContent
    readonly property Component knowledge: knowledgeContent

    Component {
        id: resultsContent
        Loader {
            sourceComponent: tableServicesController.workspaceLayout.active ? workspacePage : searchPage
            Component {
                id: searchPage
                SearchWorkspaceView {
                    theme: root.theme
                    pageTitle: root.pageTitle
                    onRequestDockMenu: sourceItem => root.requestDockMenu(sourceItem)
                }
            }
            Component {
                id: workspacePage
                Table.WorkspacePage {
                    theme: root.theme
                    services: tableServicesController
                    controller: appController
                    columnsController: columnsEditorController
                    users: userListModel
                    administration: administrationController
                    itemSurfaces: workspaceResultSurfacesModel
                    itemVersions: versionsModel
                }
            }
        }
    }

    Component {
        id: snapshotContent
        SnapshotBrowser {
            theme: root.theme
            onNotice: message => root.notice(message)
        }
    }
    Component {
        id: tasksContent
        TaskDockView {
            theme: root.theme
        }
    }
    Component {
        id: taskCalendarContent
        TaskCalendarView {
            theme: root.theme
        }
    }
    Component {
        id: timesheetContent
        TimesheetView {
            theme: root.theme
        }
    }
    Component {
        id: workReportsContent
        WorkReportsView {
            theme: root.theme
        }
    }
    Component {
        id: costReportsContent
        CostReportsView {
            theme: root.theme
        }
    }
    Component {
        id: descriptionContent
        DescriptionEditor {
            theme: root.theme
            anchors.fill: parent
            showTargetHeader: false
            value: workspaceState ? workspaceState.description : ""
            targetTitle: workspaceState ? workspaceState.descriptionTargetTitle : ""
            targetKind: workspaceState ? workspaceState.descriptionTargetKind : ""
            editing: Boolean(workspaceState && workspaceState.descriptionEditing)
            pinned: Boolean(workspaceState && workspaceState.descriptionPinned)
            dirty: Boolean(workspaceState && workspaceState.descriptionDirty)
            saving: Boolean(workspaceState && workspaceState.descriptionSaving)
            canSave: Boolean(workspaceState && workspaceState.descriptionCanSave)
            editorEnabled: Boolean(workspaceState && workspaceState.descriptionTargetTitle.length)
            errorText: workspaceState ? workspaceState.descriptionError : ""
            onEditRequested: workspaceState.begin_description_edit()
            onValueEdited: value => workspaceState.set_description(value)
            onSaveRequested: workspaceState.commit_description()
            onCancelRequested: workspaceState.cancel_description_edit()
            onPinRequested: workspaceState.freeze_description()
            onUnpinRequested: workspaceState.unfreeze_description()
        }
    }
    Component {
        id: notesContent
        CommunicationView {
            theme: root.theme
            compact: true
        }
    }
    Component {
        id: dropPlateContent
        DropPlateView {
            theme: root.theme
        }
    }
    Component {
        id: advancedSearchContent
        AdvancedSearchView {
            theme: root.theme
        }
    }
    Component {
        id: repoSyncContent
        RepositorySyncView {
            theme: root.theme
        }
    }
    Component {
        id: commitQueueContent
        CommitWorkspaceView {
            theme: root.theme
        }
    }
    Component {
        id: databaseEditorContent
        DatabaseEditorView {
            theme: root.theme
        }
    }

    Component {
        id: watchFoldersContent
        WatchFoldersView {
            theme: root.theme
        }
    }
    Component {
        id: knowledgeContent
        KnowledgeBaseView {
            theme: root.theme
        }
    }
}

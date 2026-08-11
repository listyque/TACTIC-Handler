import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    property var theme
    property string kind: ""
    property string windowId: ""

    Loader {
        anchors.fill: parent
        sourceComponent: root.kind === "configuration" ? configurationForm
            : root.kind === "server"
                || root.kind === "project"
                || root.kind === "checkin_preferences"
                || root.kind === "checkinout_preferences"
                || root.kind === "global_preferences"
                || root.kind === "maya_preferences"
                ? configurationPageForm
            : root.kind === "asset_browser" ? assetsBrowserForm
            : root.kind === "sobject_info" ? sobjectInfoForm
            : root.kind === "filter_editor" ? filterEditorForm
            : root.kind === "columns_editor" ? columnsEditorForm
            : root.kind === "naming_editor" ? namingEditorForm
            : root.kind === "preview_editor"
                || root.kind === "attachments_editor" ? fileEditorForm
            : root.kind === "server_presets" ? serverPresetsForm
            : root.kind === "screenshot_maker" ? screenshotMakerForm
            : root.kind === "handler_server" ? handlerServerForm
            : root.kind === "script_editor" ? scriptEditorForm
            : root.kind === "debug_log" ? debugLogForm
            : root.kind === "repository_sync" ? repositorySyncForm
            : root.kind === "commit_queue" ? commitQueueForm
            : root.kind === "messages" ? messagesForm
            : root.kind === "notifications" ? notificationsForm
            : root.kind === "activity_feed" ? activityFeedForm
            : root.kind === "user_profile" ? userProfileForm
            : root.kind === "tasks_workspace" ? tasksWorkspaceForm
            : root.kind === "milestone_manager" ? milestoneManagerForm
            : root.kind === "update"
                || root.kind === "create_update" ? updateForm
            : root.kind === "matching_templates" ? matchingTemplatesForm
            : root.kind === "repository_editor" ? repositoryEditorForm
            : root.kind === "db_table" ? databaseForm
            : root.kind === "maya_options" ? mayaOptionsForm
            : root.kind === "add_sobject"
                || root.kind === "task_editor"
                || root.kind === "link_sobjects" ? sobjectEditForm
            : root.kind === "confirm" ? confirmForm : genericForm
    }

    Component {
        id: configurationForm
        ConfigurationView { theme: root.theme; windowId: root.windowId }
    }
    Component {
        id: configurationPageForm
        ConfigurationPage { theme: root.theme; pageId: root.kind }
    }
    Component {
        id: assetsBrowserForm
        AssetsBrowserView { theme: root.theme }
    }
    Component {
        id: sobjectInfoForm
        SObjectInfoView { theme: root.theme }
    }
    Component {
        id: filterEditorForm
        FilterEditorView { theme: root.theme; windowId: root.windowId }
    }
    Component {
        id: columnsEditorForm
        ColumnsEditorView { theme: root.theme }
    }
    Component {
        id: fileEditorForm
        FilePreparationEditor { theme: root.theme; editorMode: root.kind }
    }
    Component {
        id: namingEditorForm
        NamingEditorView { theme: root.theme }
    }
    Component {
        id: serverPresetsForm
        ServerPresetsView { theme: root.theme }
    }
    Component {
        id: screenshotMakerForm
        ScreenshotMakerView { theme: root.theme }
    }
    Component {
        id: handlerServerForm
        HandlerServerView { theme: root.theme }
    }
    Component {
        id: scriptEditorForm
        ScriptEditorView { theme: root.theme }
    }
    Component {
        id: debugLogForm
        DebugLogView { theme: root.theme }
    }
    Component {
        id: repositorySyncForm
        RepositorySyncView { theme: root.theme }
    }
    Component {
        id: commitQueueForm
        CommitQueueView { theme: root.theme }
    }
    Component {
        id: messagesForm
        MessagesView { theme: root.theme }
    }
    Component {
        id: notificationsForm
        NotificationsView { theme: root.theme }
    }
    Component {
        id: activityFeedForm
        ActivityFeedView { theme: root.theme }
    }
    Component {
        id: userProfileForm
        UserProfileView { theme: root.theme }
    }
    Component {
        id: tasksWorkspaceForm
        TasksWorkspaceView { theme: root.theme }
    }
    Component {
        id: milestoneManagerForm
        MilestoneManagerView { theme: root.theme }
    }
    Component {
        id: updateForm
        UpdateView {
            theme: root.theme
            createMode: root.kind === "create_update"
        }
    }
    Component {
        id: matchingTemplatesForm
        MatchingTemplatesView { theme: root.theme; windowId: root.windowId }
    }
    Component {
        id: repositoryEditorForm
        RepositoryEditorView { theme: root.theme; windowId: root.windowId }
    }
    Component {
        id: databaseForm
        DatabaseBatchEditorView { theme: root.theme }
    }
    Component {
        id: mayaOptionsForm
        MayaOptionsView {
            theme: root.theme
            operationMode: root.windowId === "maya_import" ? "import"
                : root.windowId === "maya_reference" ? "reference" : "open"
        }
    }
    Component {
        id: sobjectEditForm
        Loader {
            sourceComponent: root.kind === "add_sobject"
                    || root.kind === "task_editor"
                ? schemaDrivenSobjectForm : linkSobjectForm
        }
    }
    Component {
        id: schemaDrivenSobjectForm
        SObjectFieldEditor {
            theme: root.theme
            editorWindowId: root.windowId
        }
    }
    Component {
        id: linkSobjectForm
        LinkSObjectsView { theme: root.theme }
    }
    Component {
        id: confirmForm
        Item {
            Rectangle { anchors.fill: parent; color: root.theme.panelDeep }
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 10
                MaterialIcon {
                    name: "priority_high"
                    size: 28
                    color: root.theme.yellow
                    Layout.alignment: Qt.AlignHCenter
                }
                Label {
                    text: root.windowId === "duplicate_sobject"
                        ? qsTr("Duplicate selected sObject?")
                        : qsTr("Delete selected sObject?")
                    color: root.theme.primaryText
                    font.pixelSize: 12
                    Layout.alignment: Qt.AlignHCenter
                }
                Label {
                    text: root.windowId === "delete_sobject"
                        ? (appController.selected_result_count > 1
                            ? appController.selected_result_count
                                + qsTr(" selected items will be removed from TACTIC. ")
                                + qsTr("This cannot be undone.")
                            : qsTr("The item will be removed from TACTIC. ")
                                + qsTr("This cannot be undone."))
                        : qsTr("A new server item will be created from the ")
                            + qsTr("selected object.")
                    color: root.theme.secondaryText
                    font.pixelSize: 9
                    wrapMode: Text.WordWrap
                    horizontalAlignment: Text.AlignHCenter
                    Layout.fillWidth: true
                }
                Item { Layout.fillHeight: true }
                RowLayout {
                    Layout.alignment: Qt.AlignHCenter
                    Md3Button {
                        theme: root.theme
                        text: root.windowId === "duplicate_sobject"
                            ? qsTr("Duplicate") : qsTr("Delete")
                        destructive: root.windowId !== "duplicate_sobject"
                        onClicked: appController.confirm_item_action(
                            root.windowId
                        )
                    }
                    Md3Button {
                        theme: root.theme
                        text: qsTr("Cancel")
                        onClicked: windowModel.close_window(root.windowId)
                    }
                }
            }
        }
    }
    Component {
        id: genericForm
        Item {
            Rectangle { anchors.fill: parent; color: root.theme.panelDeep }
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 14
                Label {
                    text: qsTr("TACTIC-Handler")
                    color: root.theme.primaryText
                    font.pixelSize: 13
                }
                Label {
                    text: qsTr("No view is registered for this window.")
                    color: root.theme.secondaryText
                    font.pixelSize: 10
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
            }
        }
    }
}

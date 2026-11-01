import QtQuick
import QtQuick.Window
import QtQml.Models
import "features/support/identity" as Identity
import "tactic_frame" as Frame
import "tactic_frame/features/support/identity/profile.ui.mjs" as UI

Item {
    id: root
    required property var theme
    property string userSearch: ""
    property bool closeWhenEditorCloses: false
    property bool activityExpanded: false
    property bool directoryExpanded: true
    property real directoryWidth: 252
    property real activityHeight: 0
    readonly property var profileController: userController
    readonly property var taskWorkspaceController: tasksController
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var frameModel: ({
            profile: userController.profile,
            directory: userController.directoryVisible,
            directoryExpanded,
            directoryWidth,
            query: userSearch,
            canManage: userController.canManageUsers,
            canEdit: userController.canEdit,
            saving: userController.editingBusy,
            busy: userController.busy,
            tasksBusy: userController.tasksBusy,
            taskSummary: userController.taskSummary,
            statusSummary: userController.taskStatusSummary,
            processSummary: userController.taskProcessSummary,
            viewWorkHours: userController.canViewWorkHours,
            workHourSummary: userController.workHourSummary,
            activityCount: userActivityModel.count(),
            relatedBusy: userController.tasksBusy,
            activityHeight,
            expanded: activityExpanded,
            error: userController.error,
            activityError: userController.activityError
        })
    SortFilterProxyModel {
        id: filteredUsers
        model: userListModel
        property string query: root.userSearch
        onQueryChanged: invalidate()
        filters: FunctionFilter {
            column: 0
            function filter(data: RoleData): bool {
                return UI.matchesUser(data, root.userSearch);
            }
        }
    }
    component RoleData: QtObject {
        property string login
        property string displayName
        property string email
        property var groups
    }
    UserProfileEditorDialog {
        id: profileEditor
        anchors.centerIn: parent
        theme: root.theme
        controller: userController
        onClosed: if (root.closeWhenEditorCloses) {
            root.closeWhenEditorCloses = false;
            if (root.Window.window)
                root.Window.window.close();
        }
    }
    function requestClose() {
        if (profileEditor.visible && (profileEditor.dirty || profileEditor.uncertain || userController.editingBusy)) {
            closeWhenEditorCloses = true;
            profileEditor.requestClose(false);
            return false;
        }
        return true;
    }
    function row(list, record) {
        return UI.userRow(frameModel, record, list.width - 16, language);
    }
    function dispatch(action) {
        if (action.type === "user") {
            userController.select_profile(action.login);
            directoryExpanded = false;
        } else if (action.type === "query")
            userSearch = action.value;
        else if (action.type === "directoryWidth")
            directoryWidth = action.value;
        else if (action.type === "showDirectory")
            directoryExpanded = true;
        else if (action.type === "create")
            profileEditor.openForCreate();
        else if (action.type === "edit")
            profileEditor.openForProfile();
        else if (action.type === "editGroups")
            profileEditor.openForGroups();
        else if (action.type === "refresh")
            userController.refresh();
        else if (action.type === "logout")
            userController.logout();
        else if (action.type === "message")
            messagesController.open_direct_conversation(userController.profile.login);
        else if (action.type === "tasks") {
            if (action.key)
                tasksController.open_for_user_filter(userController.profile.login, action.key, action.value);
            else
                tasksController.open_for_user(userController.profile.login);
        } else if (action.type === "activity")
            userController.open_full_activity();
        else if (action.type === "expand")
            activityExpanded = !activityExpanded;
    }
    Component {
        id: activityComponent
        Identity.UserProfileActivity {
            theme: root.theme
            controller: userController
            records: userActivityModel
            expanded: root.activityExpanded
            function publishHeight() {
                root.activityHeight = contentHeight;
            }
            // Publish measurements after Frame finishes applying the scene.
            onContentHeightChanged: Qt.callLater(publishHeight)
        }
    }
    Rectangle {
        anchors.fill: parent
        color: root.theme.workspace
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: UI.describe(root.frameModel, root.width, root.height, root.language)
        models: ({
                users: filteredUsers
            })
        views: ({
                activity: activityComponent
            })
        describeRow: root.row
        onEvent: action => root.dispatch(action)
    }
}

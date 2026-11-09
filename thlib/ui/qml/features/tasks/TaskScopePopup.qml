import QtQuick
import QtQuick.Controls
import "../../controls" as Controls
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/tasks/scope.ui.mjs" as UI

Controls.ScrollablePopup {
    id: root
    required property var controller
    required property var users
    property string selectedIcon: "inventory-2"
    property bool chooseTeam: false
    property var userOptions: []
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    parent: Overlay.overlay
    preferredSurfaceWidth: 280
    minimumSurfaceWidth: 200
    maximumSurfaceHeight: 400
    padding: 5
    contentSpacing: 0
    function refreshUsers() {
        const rows = [];
        for (let i = 0; i < users.count(); ++i) {
            const record = users.get(i);
            rows.push(Object.assign({}, record, {
                value: record.login,
                label: record.displayName || record.login
            }));
        }
        userOptions = rows;
    }
    function openBelow(source) {
        chooseTeam = false;
        refreshUsers();
        openBelowItem(source, true, 6);
    }
    function toggleBelow(source) {
        chooseTeam = false;
        refreshUsers();
        toggleBelowItem(source, true, 6);
    }
    function toggleTeamsBelow(source) {
        chooseTeam = true;
        refreshUsers();
        toggleBelowItem(source, true, 6);
    }
    Connections {
        target: root.users
        function onContentReplaced() {
            if (root.opened)
                root.refreshUsers();
        }
    }
    Frame.FrameView {
        width: parent.width
        height: scene.height
        theme: root.theme
        scene: UI.describe({
            scope: ["object", "multiple"].includes(root.controller.advancedScope) ? "selected" : root.controller.advancedScope,
            identity: root.controller.advancedUser,
            personal: root.controller.personalScope,
            selectedIcon: root.selectedIcon,
            searchTypeTitle: root.controller.searchTypeScopeName,
            searchTypeAvailable: root.controller.searchTypeScopeAvailable,
            blocked: root.controller.advancedBusy || root.controller.advancedSaving,
            chooseTeam: root.chooseTeam,
            users: root.userOptions,
            teams: root.controller.teamOptions,
            radius: root.theme.itemRadius
        }, width, root.language)
        onEvent: action => {
            if (action.type === "scope") {
                if (action.value === "team") {
                    root.chooseTeam = true;
                    return;
                }
                root.chooseTeam = false;
                if (action.value === "selected")
                    root.controller.use_current_object();
                else if (action.value === "search_type")
                    root.controller.use_current_search_type();
                else if (action.value === "project")
                    root.controller.use_project();
                else if (action.value === "user")
                    root.controller.open_for_user("");
                if (action.value !== "user")
                    root.close();
            } else if (action.type === "identity") {
                if (action.scope === "team")
                    root.controller.open_for_team(action.value);
                else
                    root.controller.open_for_user(action.value);
                root.close();
            }
        }
    }
}

import "tactic_frame" as Frame
import "tactic_frame/controls/forms/people.ui.mjs" as UI
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    readonly property string language: typeof localizationController === 'undefined' ? 'en' : localizationController.current_language
    property var selectedLogins: []
    property var excludedLogins: []
    property bool includeCurrent: false
    property bool multiple: true
    property alias searchText: searchField.text
    signal selectionChanged(var logins)

    function isExcluded(login, current) {
        return (!root.includeCurrent && current) || root.excludedLogins.indexOf(login) >= 0;
    }

    UserFilter {
        id: filteredUsers
        model: userListModel
        searchText: searchField.text
        excludedLogins: root.excludedLogins
    }

    function toggle(login) {
        const user = userListModel.lookup("login", login);
        if (!user.login || root.isExcluded(user.login, user.current))
            return;
        let values = root.selectedLogins.slice();
        const index = values.indexOf(login);
        if (index >= 0)
            values.splice(index, 1);
        else if (root.multiple)
            values.push(login);
        else
            values = [login];
        root.selectedLogins = values;
        root.selectionChanged(values);
    }

    function reset() {
        searchField.clear();
        root.selectedLogins = [];
        root.selectionChanged([]);
    }

    function setSelection(logins, notify) {
        searchField.clear();
        root.selectedLogins = Array.from(logins || []);
        if (notify === undefined || notify)
            root.selectionChanged(root.selectedLogins);
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 8

        RowLayout {
            Layout.fillWidth: true
            spacing: 7

            Controls.SearchField {
                id: searchField
                Layout.fillWidth: true
                theme: root.theme
                placeholderText: qsTr("Search users")
            }
        }

        ListView {
            id: usersList
            objectName: "userPickerList"
            readonly property real scrollGutter: UI.metrics.scrollbar
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 0
            model: filteredUsers
            section.property: "primaryGroup"
            section.criteria: ViewSection.FullString
            section.delegate: UserGroupSection {
                required property string section
                objectName: "userPickerSection_" + section
                width: Math.max(0, usersList.width - usersList.scrollGutter)
                theme: root.theme
                title: section
            }
            ScrollBar.vertical: Controls.ScrollBar {
                objectName: "userPickerScrollBar"
                theme: root.theme
                flickableTarget: usersList
            }

            delegate: Item {
                id: userRow
                objectName: "userPickerRow_" + login
                required property string login
                required property string displayName
                required property string initials
                required property string avatarUrl
                required property string avatarColor
                required property var groups
                required property string primaryGroup
                required property bool current
                readonly property bool currentUnavailable: userRow.current && !root.includeCurrent
                readonly property bool selectable: !root.isExcluded(userRow.login, userRow.current)
                readonly property bool chosen: root.selectedLogins.indexOf(userRow.login) >= 0
                width: Math.max(0, usersList.width - usersList.scrollGutter)
                height: UI.metrics.row

                Frame.FrameView {
                    anchors.fill: parent
                    theme: root.theme
                    scene: UI.row({
                        login: userRow.login,
                        displayName: userRow.displayName,
                        initials: userRow.initials,
                        avatarUrl: userRow.avatarUrl,
                        avatarColor: userRow.avatarColor,
                        groups: userRow.groups,
                        picker: true,
                        selected: userRow.chosen,
                        selectable: userRow.selectable,
                        currentUnavailable: userRow.currentUnavailable
                    }, width, root.language)
                    onEvent: action => root.toggle(action.login)
                }
            }
        }
    }
}

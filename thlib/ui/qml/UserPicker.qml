import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    property var selectedLogins: []
    property var excludedLogins: []
    property bool includeCurrent: false
    property bool multiple: true
    property alias searchText: searchField.text
    signal selectionChanged(var logins)

    function isExcluded(login, current) {
        return (!root.includeCurrent && current)
            || root.excludedLogins.indexOf(login) >= 0
    }

    UserFilter {
        id: filteredUsers
        model: userListModel
        searchText: searchField.text
        excludedLogins: root.excludedLogins
    }

    function toggle(login) {
        const user = userListModel.lookup("login", login)
        if (!user.login || root.isExcluded(user.login, user.current))
            return
        let values = root.selectedLogins.slice()
        const index = values.indexOf(login)
        if (index >= 0)
            values.splice(index, 1)
        else if (root.multiple)
            values.push(login)
        else
            values = [login]
        root.selectedLogins = values
        root.selectionChanged(values)
    }

    function reset() {
        searchField.clear()
        root.selectedLogins = []
        root.selectionChanged([])
    }

    function setSelection(logins, notify) {
        searchField.clear()
        root.selectedLogins = Array.from(logins || [])
        if (notify === undefined || notify)
            root.selectionChanged(root.selectedLogins)
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
            readonly property real scrollGutter: 16
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
                width: Math.max(
                    0, usersList.width - usersList.scrollGutter
                )
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
                readonly property bool currentUnavailable:
                    userRow.current && !root.includeCurrent
                readonly property bool selectable:
                    !root.isExcluded(userRow.login, userRow.current)
                readonly property bool chosen:
                    root.selectedLogins.indexOf(userRow.login) >= 0
                width: Math.max(0, usersList.width - usersList.scrollGutter)
                height: 54

                Controls.ItemSurface {
                    anchors.fill: parent
                    theme: root.theme
                    selected: userRow.chosen
                    hovered: userRow.selectable && userMouse.containsMouse
                    pressed: userRow.selectable && userMouse.pressed
                    accent: root.theme.action
                    cornerRadius: 12
                    railVisible: false
                    separatorVisible: false
                }
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 8
                    anchors.rightMargin: 8
                    spacing: 8

                    Controls.ItemPreview {
                        objectName: "userPickerAvatar_" + userRow.login
                        Layout.preferredWidth: 36
                        Layout.preferredHeight: 36
                        theme: root.theme
                        source: userRow.avatarUrl
                        fallbackIcon: "person"
                        fallbackText: userRow.initials
                        previewSize: 36
                        round: true
                        outlined: true
                        selected: userRow.chosen
                        accent: userRow.avatarColor.length
                            ? userRow.avatarColor : root.theme.action
                        opacity: userRow.selectable ? 1 : 0.58
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 1
                        Label {
                            Layout.fillWidth: true
                            text: userRow.displayName || userRow.login
                            color: userRow.chosen
                                ? root.theme.selectedText
                                : userRow.selectable
                                    ? root.theme.primaryText
                                    : root.theme.disabledText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.body
                            font.weight: Font.DemiBold
                            elide: Text.ElideRight
                        }
                        Label {
                            Layout.fillWidth: true
                            text: userRow.login + (
                                userRow.groups.length > 0
                                ? "  ·  " + userRow.groups.join(", ") : ""
                            )
                            color: userRow.chosen
                                ? root.theme.selectedText
                                : userRow.selectable
                                    ? root.theme.secondaryText
                                    : root.theme.disabledText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
                            elide: Text.ElideRight
                        }
                    }
                    Controls.MaterialIcon {
                        visible: userRow.chosen
                        name: "check-circle"
                        size: 18
                        color: root.theme.selectedText
                    }
                    Controls.StatusChip {
                        objectName: "userPickerCurrentMarker"
                        visible: userRow.currentUnavailable
                        theme: root.theme
                        text: qsTr("Current user")
                        iconName: "lock"
                        accentColor: root.theme.disabledText
                    }
                }
                MouseArea {
                    id: userMouse
                    anchors.fill: parent
                    enabled: userRow.selectable
                    hoverEnabled: true
                    cursorShape: userRow.selectable
                        ? Qt.PointingHandCursor : Qt.ArrowCursor
                    onClicked: root.toggle(userRow.login)
                }
            }
        }
    }
}

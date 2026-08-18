import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

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

    function matches(login, displayName) {
        const value = searchField.text.trim().toLowerCase()
        return value.length === 0
            || String(login).toLowerCase().indexOf(value) >= 0
            || String(displayName).toLowerCase().indexOf(value) >= 0
    }

    function groupHasAvailable(group) {
        for (let index = 0; index < userListModel.count(); ++index) {
            const user = userListModel.get(index)
            if (String(user.primaryGroup || "") === String(group || "")
                    && !root.isExcluded(user.login, user.current)
                    && root.matches(user.login, user.displayName))
                return true
        }
        return false
    }

    function toggle(login) {
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

    function setSelection(logins) {
        searchField.clear()
        root.selectedLogins = Array.from(logins || [])
        root.selectionChanged(root.selectedLogins)
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 8

        RowLayout {
            Layout.fillWidth: true
            spacing: 7

            MaterialIcon {
                name: "search"
                size: 18
                color: root.theme.secondaryText
            }
            Md3TextField {
                id: searchField
                Layout.fillWidth: true
                theme: root.theme
                placeholderText: qsTr("Search users")
            }
        }

        ListView {
            id: usersList
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 0
            model: userListModel
            section.property: "primaryGroup"
            section.criteria: ViewSection.FullString
            section.delegate: UserGroupSection {
                required property string section
                width: ListView.view.width
                theme: root.theme
                title: section
                shown: root.groupHasAvailable(section)
            }
            ScrollBar.vertical: Md3ScrollBar { theme: root.theme }

            delegate: Item {
                id: userRow
                required property string login
                required property string displayName
                required property string initials
                required property string avatarUrl
                required property var groups
                required property string primaryGroup
                required property bool current
                readonly property bool available:
                    !root.isExcluded(userRow.login, userRow.current)
                    && root.matches(userRow.login, userRow.displayName)
                readonly property bool chosen:
                    root.selectedLogins.indexOf(userRow.login) >= 0
                width: usersList.width
                height: available ? 54 : 0
                visible: available

                ItemSurface {
                    anchors.fill: parent
                    theme: root.theme
                    selected: userRow.chosen
                    hovered: userMouse.containsMouse
                    pressed: userMouse.pressed
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

                    ItemPreview {
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
                        accent: root.theme.action
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 1
                        Label {
                            Layout.fillWidth: true
                            text: userRow.displayName || userRow.login
                            color: userRow.chosen
                                ? root.theme.selectedText
                                : root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Typography.body
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
                                : root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Typography.caption
                            elide: Text.ElideRight
                        }
                    }
                    MaterialIcon {
                        visible: userRow.chosen
                        name: "check-circle"
                        size: 18
                        color: root.theme.selectedText
                    }
                }
                MouseArea {
                    id: userMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.toggle(userRow.login)
                }
            }
        }
    }
}

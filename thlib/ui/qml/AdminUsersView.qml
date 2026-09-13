import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

AdminDocumentShell {
    id: root
    readonly property bool compact: width < 780
    title: qsTr("Users")
    description: qsTr("Server accounts, profiles and contact details")
    iconName: "person"
    showSelector: false
    allowCreate: true

    editorContent: RowLayout {
        // The alias reparents this item into AdminDocumentShell's plain Item.
        anchors.fill: parent // qmllint disable Quick.layout-positioning
        spacing: 12
        Controls.EditorPanel {
            Layout.preferredWidth: root.compact ? 220 : 290
            Layout.fillHeight: true
            theme: root.theme
            title: qsTr("User directory")
            iconName: "groups"
            Controls.SearchField {
                objectName: "adminUserSearch"
                Layout.fillWidth: true
                theme: root.theme
                placeholderText: qsTr("Name, login or email")
                onSearchEdited: query => root.controller.set_query(query)
            }
            Controls.CheckBox {
                objectName: "adminShowRetiredUsers"
                Layout.fillWidth: true
                theme: root.theme
                text: qsTr("Show retired users")
                checked: root.controller.showRetired
                onToggled: root.controller.set_show_retired(checked)
            }
            ListView {
                id: users
                objectName: "adminUsersList"
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 4
                boundsBehavior: Flickable.StopAtBounds
                model: root.controller.usersModel
                delegate: Controls.PopupAction {
                    id: userRow
                    required property string login
                    required property string displayName
                    required property string avatarUrl
                    required property string avatarColor
                    required property string initials
                    required property bool retired
                    readonly property bool selected: root.controller.identity === login
                    objectName: "adminUser_" + login
                    width: users.width - usersBar.reservedExtent - 4
                    implicitHeight: identity.implicitHeight + 20
                    padding: 10
                    text: displayName
                    Accessible.name: displayName + " " + login
                    Accessible.description: retired ? qsTr("Retired user") : ""
                    enabled: !root.controller.dirty
                    background: Controls.ItemSurface {
                        theme: root.theme
                        selected: userRow.selected
                        hovered: userRow.hovered
                        pressed: userRow.down
                        normalColor: "transparent"
                        selectedColor: root.theme.selected
                        railVisible: userRow.selected
                        cornerRadius: root.theme.itemRadius
                        separatorVisible: false
                        borderWidth: userRow.visualFocus ? 1 : 0
                        borderColor: root.theme.action
                    }
                    contentItem: ColumnLayout {
                        id: identity
                        spacing: 5
                        UserIdentity {
                            Layout.fillWidth: true
                            theme: root.theme
                            login: userRow.login
                            displayName: userRow.displayName
                            initials: userRow.initials
                            avatarUrl: userRow.avatarUrl
                            avatarColor: userRow.avatarColor
                            retired: userRow.retired
                        }
                        Label {
                            Layout.fillWidth: true
                            visible: userRow.retired
                            text: qsTr("Retired user")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.label
                        }
                    }
                    onClicked: root.controller.select(login)
                }
                ScrollBar.vertical: Controls.ScrollBar {
                    id: usersBar
                    objectName: "adminUsersScrollBar"
                    theme: root.theme
                    flickableTarget: users
                }
                Controls.EmptyState {
                    anchors.centerIn: parent
                    width: parent.width - usersBar.reservedExtent - 8
                    visible: users.count === 0 && !root.controller.busy
                    theme: root.theme
                    iconName: "person"
                    title: qsTr("No users match the search")
                }
            }
        }
        AdminUserDetails {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumWidth: 0
            theme: root.theme
            controller: root.controller
        }
    }
}

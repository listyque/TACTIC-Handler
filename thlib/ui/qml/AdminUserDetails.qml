import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Controls.EditorPanel {
    id: root
    required property var controller
    property string page: "profile"
    readonly property bool hasUser: controller.document.login !== undefined
    readonly property string currentIdentity: controller.identity
    readonly property bool twoColumns: form.width > 620
    readonly property var profileFields: [
        {key: "first_name", label: qsTr("First name")},
        {key: "last_name", label: qsTr("Last name")},
        {key: "display_name", label: qsTr("Display name")},
        {key: "department", label: qsTr("Department")},
        {key: "email", label: qsTr("Email")},
        {key: "phone_number", label: qsTr("Phone number")},
        {key: "address", label: qsTr("Address")}
    ]
    readonly property var accountFields: [
        {key: "upn", label: qsTr("UPN")},
        {key: "namespace", label: qsTr("Namespace")},
        {key: "project_code", label: qsTr("Project code")},
        {key: "license_type", label: qsTr("License type")},
        {key: "hourly_wage", label: qsTr("Hourly wage")}
    ]
    onCurrentIdentityChanged: page = "profile"
    onPageChanged: form.contentY = 0

    Controls.EmptyState {
        Layout.fillWidth: true
        Layout.fillHeight: true
        visible: !root.hasUser
        theme: root.theme
        iconName: "person"
        title: qsTr("Select a user or create a new account")
    }
    RowLayout {
        Layout.fillWidth: true
        visible: root.hasUser
        spacing: 12
        UserIdentity {
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            theme: root.theme
            login: root.controller.profile.login || ""
            displayName: root.controller.profile.displayName || qsTr("New user")
            initials: root.controller.profile.initials || "?"
            avatarUrl: root.controller.profile.avatarUrl || ""
            avatarColor: root.controller.profile.avatarColor || ""
            retired: root.controller.document.s_status === "retired"
            avatarSize: 60
            emphasized: true
        }
        Controls.CompactIconButton {
            objectName: "adminUserManageGroups"
            theme: root.theme
            iconName: "groups"
            toolTip: qsTr("Edit group membership")
            enabled: root.controller.canWrite && !root.controller.busy
            onClicked: root.page = "groups"
        }
    }
    Controls.SegmentedButton {
        objectName: "adminUserEditorTabs"
        Layout.fillWidth: true
        visible: root.hasUser
        theme: root.theme
        currentValue: root.page
        model: [
            {value: "profile", label: qsTr("Profile"), icon: "person", translate: false},
            {value: "account", label: qsTr("Account"), icon: "security", translate: false},
            {value: "groups", label: qsTr("Groups"), icon: "groups", translate: false}
        ]
        onActivated: value => root.page = value
    }
    Flickable {
        id: form
        objectName: "adminUserForm"
        Layout.fillWidth: true
        Layout.fillHeight: true
        visible: root.hasUser
        enabled: root.controller.canWrite && !root.controller.busy
        clip: true
        contentWidth: width
        contentHeight: fields.implicitHeight
        boundsBehavior: Flickable.StopAtBounds
        ColumnLayout {
            id: fields
            width: form.width - formBar.reservedExtent - 4
            spacing: 12
            Label {
                Layout.fillWidth: true
                visible: root.page === "profile"
                text: qsTr("These details are shown in profiles, messages and user pickers.")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.label
                wrapMode: Text.WordWrap
            }
            ColumnLayout {
                Layout.fillWidth: true
                visible: root.page === "profile"
                spacing: 5
                Controls.SectionLabel { theme: root.theme; text: qsTr("Login") }
                Controls.TextField {
                    objectName: "adminUserLogin"
                    Layout.fillWidth: true
                    theme: root.theme
                    text: root.controller.document.login || ""
                    readOnly: root.controller.identity.length > 0
                    placeholderText: qsTr("Unique login, without spaces")
                    onTextEdited: root.controller.set_field("login", text)
                }
            }
            GridLayout {
                Layout.fillWidth: true
                visible: root.page !== "groups"
                columns: root.twoColumns ? 2 : 1
                columnSpacing: 12
                rowSpacing: 12
                uniformCellWidths: true
                Repeater {
                    model: root.page === "profile" ? root.profileFields
                        : root.page === "account" ? root.accountFields : []
                    delegate: ColumnLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        visible: root.controller.document[modelData.key] !== undefined
                        spacing: 5
                        Controls.SectionLabel { theme: root.theme; text: modelData.label }
                        Controls.TextField {
                            objectName: "adminUserField_" + modelData.key
                            Layout.fillWidth: true
                            Layout.minimumWidth: 0
                            theme: root.theme
                            text: String(root.controller.document[modelData.key] ?? "")
                            onTextEdited: root.controller.set_field(modelData.key, text)
                        }
                    }
                }
            }
            ColumnLayout {
                Layout.fillWidth: true
                visible: root.page === "account"
                spacing: 8
                Controls.SectionLabel { theme: root.theme; text: qsTr("Password") }
                Controls.TextField {
                    objectName: "adminUserPassword"
                    Layout.fillWidth: true
                    theme: root.theme
                    text: root.controller.document.password || ""
                    placeholderText: qsTr("Leave empty to keep the current password")
                    echoMode: TextInput.Password
                    onTextEdited: root.controller.set_field("password", text)
                }
                Controls.CheckBox {
                    objectName: "adminUserRetired"
                    Layout.fillWidth: true
                    theme: root.theme
                    text: qsTr("Retired")
                    checked: root.controller.document.s_status === "retired"
                    onToggled: root.controller.set_field("s_status", checked ? "retired" : "")
                }
                Label {
                    Layout.fillWidth: true
                    text: qsTr("Retiring keeps this user's history. Clear this option to reactivate the account, then save.")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                    wrapMode: Text.WordWrap
                }
            }
            UserGroupMembershipEditor {
                Layout.fillWidth: true
                visible: root.page === "groups"
                theme: root.theme
                model: root.controller.groupsModel
                selectedGroups: root.controller.document.groups || []
                onGroupToggled: (code, selected) => root.controller.set_group(code, selected)
            }
        }
        ScrollBar.vertical: Controls.ScrollBar {
            id: formBar
            objectName: "adminUserFormScrollBar"
            theme: root.theme
            flickableTarget: form
        }
    }
}

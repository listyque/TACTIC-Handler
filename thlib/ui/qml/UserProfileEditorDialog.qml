import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import "controls" as Controls

Controls.Dialog {
    id: root

    required property var controller
    property string mode: "profile"
    property var selectedGroups: []
    property var groupAccessLevels: ({})
    property bool awaitingSave: false
    property bool creating: false
    property url pendingAvatarUrl: ""
    property bool uploadAvatarAfterCreate: false

    title: creating ? qsTr("Add user")
        : mode === "groups" ? qsTr("Edit group membership")
        : qsTr("Edit user profile")
    width: 680
    height: 690
    closePolicy: Popup.CloseOnEscape

    function setGroupSelected(code, selected) {
        const value = String(code || "")
        const next = selectedGroups.slice()
        const index = next.indexOf(value)
        if (selected && index < 0)
            next.push(value)
        else if (!selected && index >= 0)
            next.splice(index, 1)
        selectedGroups = next
    }

    function setGroupAccessLevel(code, value) {
        const next = Object.assign({}, groupAccessLevels)
        next[String(code || "")] = String(value || "").trim()
        groupAccessLevels = next
    }

    function loadProfile() {
        const profile = creating ? {} : (controller.profile || {})
        loginField.text = String(profile.login || "")
        firstNameField.text = String(profile.firstName || "")
        lastNameField.text = String(profile.lastName || "")
        displayNameField.text = String(profile.displayName || "")
        emailField.text = String(profile.email || "")
        phoneField.text = String(profile.phoneNumber || "")
        addressField.text = String(profile.address || "")
        departmentField.text = String(profile.department || "")
        passwordField.clear()
        upnField.text = String(profile.upn || "")
        namespaceField.text = String(profile.namespace || "")
        statusField.text = String(profile.status || "")
        projectField.text = String(profile.accountProject || "")
        licenseField.text = String(profile.licenseType || "")
        wageField.text = String(profile.hourlyWage || "")
    }

    function loadGroups() {
        const values = []
        const levels = {}
        for (let index = 0; index < userGroupModel.count(); ++index) {
            const record = userGroupModel.get(index)
            if (record.member)
                values.push(String(record.code || ""))
            levels[String(record.code || "")] = String(
                record.accessLevel || ""
            )
        }
        selectedGroups = values
        groupAccessLevels = levels
    }

    function openForProfile() {
        creating = false
        mode = "profile"
        awaitingSave = false
        uploadAvatarAfterCreate = false
        pendingAvatarUrl = ""
        loadProfile()
        loadGroups()
        open()
    }

    function openForGroups() {
        creating = false
        mode = "groups"
        awaitingSave = false
        uploadAvatarAfterCreate = false
        pendingAvatarUrl = ""
        loadGroups()
        open()
    }

    function openForCreate() {
        creating = true
        mode = "profile"
        awaitingSave = false
        uploadAvatarAfterCreate = false
        pendingAvatarUrl = ""
        selectedGroups = []
        loadProfile()
        open()
        Qt.callLater(() => loginField.forceActiveFocus())
    }

    function save() {
        const values = {
            "login": loginField.text,
            "first_name": firstNameField.text,
            "last_name": lastNameField.text,
            "display_name": displayNameField.text,
            "email": emailField.text,
            "phone_number": phoneField.text,
            "address": addressField.text,
            "department": departmentField.text,
            "password": passwordField.text,
            "upn": upnField.text,
            "namespace": namespaceField.text,
            "s_status": statusField.text,
            "project_code": projectField.text,
            "license_type": licenseField.text,
            "hourly_wage": wageField.text
        }
        uploadAvatarAfterCreate = creating && String(pendingAvatarUrl).length > 0
        awaitingSave = creating
            ? controller.create_user(values, selectedGroups)
            : mode === "groups"
            ? controller.save_group_settings(
                selectedGroups, groupAccessLevels
            )
            : controller.save_profile(values)
        if (awaitingSave)
            passwordField.clear()
    }

    Connections {
        target: root.controller
        function onProfileSaved() {
            if (root.awaitingSave) {
                if (root.uploadAvatarAfterCreate)
                    root.controller.queue_avatar(root.pendingAvatarUrl)
                root.awaitingSave = false
                root.close()
            }
        }
    }

    FileDialog {
        id: avatarDialog
        title: qsTr("Choose avatar image")
        fileMode: FileDialog.OpenFile
        nameFilters: [qsTr("Images (*.jpg *.jpeg *.png *.webp)")]
        onAccepted: {
            if (root.creating) {
                root.pendingAvatarUrl = selectedFile
            } else if (root.controller.queue_avatar(selectedFile)) {
                root.pendingAvatarUrl = selectedFile
            }
        }
    }

    contentItem: ColumnLayout {
        spacing: 12

        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            Controls.ItemPreview {
                Layout.preferredWidth: 54
                Layout.preferredHeight: 54
                theme: root.theme
                source: String(root.pendingAvatarUrl).length
                    ? root.pendingAvatarUrl
                    : root.controller.profile.avatarUrl || ""
                fallbackIcon: "person"
                fallbackText: root.creating ? "?"
                    : root.controller.profile.initials || "?"
                previewSize: 54
                round: true
                outlined: true
                animateAppearance: false
                accent: root.creating
                    ? root.theme.action
                    : root.controller.profile.avatarColor || root.theme.action
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Label {
                    Layout.fillWidth: true
                    text: root.creating ? qsTr("New user")
                        : root.controller.profile.displayName || qsTr("User")
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 13
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }
                Label {
                    text: root.creating ? loginField.text
                        : root.controller.profile.login || ""
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                }
            }
            Controls.Button {
                theme: root.theme
                visible: root.mode === "profile"
                text: qsTr("CHANGE AVATAR")
                icon.name: "image-edit"
                onClicked: avatarDialog.open()
            }
        }

        Controls.SegmentedButton {
            visible: root.controller.canManageUsers
            Layout.fillWidth: true
            theme: root.theme
            model: [
                {"label": qsTr("Profile"), "value": "profile", "icon": "person"},
                {"label": qsTr("Groups"), "value": "groups", "icon": "groups"}
            ]
            currentValue: root.mode
            onActivated: value => {
                root.mode = value
                if (!root.creating) {
                    if (value === "groups")
                        root.loadGroups()
                    else
                        root.loadProfile()
                }
            }
        }

        ScrollView {
            id: editorScroll

            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: availableWidth
            contentHeight: editorContent.implicitHeight
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            ScrollBar.vertical: Controls.ScrollBar {
                id: editorScrollBar
                objectName: "userProfileEditorScrollBar"
                theme: root.theme
                flickableTarget: editorScroll
            }

            ColumnLayout {
                id: editorContent

                width: editorScroll.availableWidth - editorScrollBar.reservedExtent - 4
                spacing: 10

                GridLayout {
                    visible: root.mode === "profile"
                    Layout.fillWidth: true
                    columns: 2
                    columnSpacing: 10
                    rowSpacing: 10

                    Controls.TextField {
                        id: loginField
                        visible: root.creating
                        Layout.fillWidth: true
                        Layout.columnSpan: 2
                        theme: root.theme
                        placeholderText: qsTr("Login")
                    }

                    Controls.TextField {
                        id: firstNameField
                        Layout.fillWidth: true
                        theme: root.theme
                        placeholderText: qsTr("First name")
                    }
                    Controls.TextField {
                        id: lastNameField
                        Layout.fillWidth: true
                        theme: root.theme
                        placeholderText: qsTr("Last name")
                    }
                    Controls.TextField {
                        id: displayNameField
                        Layout.fillWidth: true
                        theme: root.theme
                        placeholderText: qsTr("Display name")
                    }
                    Controls.TextField {
                        id: departmentField
                        Layout.fillWidth: true
                        theme: root.theme
                        placeholderText: qsTr("Department")
                    }
                    Controls.TextField {
                        id: emailField
                        Layout.fillWidth: true
                        theme: root.theme
                        placeholderText: qsTr("Email")
                    }
                    Controls.TextField {
                        id: phoneField
                        Layout.fillWidth: true
                        theme: root.theme
                        placeholderText: qsTr("Phone number")
                    }
                    Controls.TextField {
                        id: addressField
                        Layout.fillWidth: true
                        Layout.columnSpan: 2
                        theme: root.theme
                        placeholderText: qsTr("Address")
                    }
                    Controls.TextField {
                        id: passwordField
                        Layout.fillWidth: true
                        Layout.columnSpan: 2
                        theme: root.theme
                        placeholderText: qsTr("New password — leave empty to keep current")
                        echoMode: TextInput.Password
                    }

                    Label {
                        visible: root.controller.canManageUsers
                        Layout.columnSpan: 2
                        text: qsTr("ACCOUNT SETTINGS")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                        font.weight: Font.DemiBold
                    }
                    Controls.TextField {
                        id: upnField
                        visible: root.controller.canManageUsers
                        Layout.fillWidth: true
                        theme: root.theme
                        placeholderText: qsTr("UPN")
                    }
                    Controls.TextField {
                        id: namespaceField
                        visible: root.controller.canManageUsers
                        Layout.fillWidth: true
                        theme: root.theme
                        placeholderText: qsTr("Namespace")
                    }
                    Controls.TextField {
                        id: statusField
                        visible: root.controller.canManageUsers
                        Layout.fillWidth: true
                        theme: root.theme
                        placeholderText: qsTr("Account status")
                    }
                    Controls.TextField {
                        id: projectField
                        visible: root.controller.canManageUsers
                        Layout.fillWidth: true
                        theme: root.theme
                        placeholderText: qsTr("Project code")
                    }
                    Controls.TextField {
                        id: licenseField
                        visible: root.controller.canManageUsers
                        Layout.fillWidth: true
                        theme: root.theme
                        placeholderText: qsTr("License type")
                    }
                    Controls.TextField {
                        id: wageField
                        visible: root.controller.canManageUsers
                        Layout.fillWidth: true
                        theme: root.theme
                        placeholderText: qsTr("Hourly wage")
                        validator: DoubleValidator { bottom: 0 }
                    }
                }

                UserGroupMembershipEditor {
                    visible: root.mode === "groups"
                    Layout.fillWidth: true
                    theme: root.theme
                    model: userGroupModel
                    selectedGroups: root.selectedGroups
                    showAccessLevels: !root.creating
                    accessLevels: root.groupAccessLevels
                    onGroupToggled: (code, selected) => root.setGroupSelected(code, selected)
                    onAccessLevelEdited: (code, value) => root.setGroupAccessLevel(code, value)
                }
            }
        }

        Label {
            visible: root.controller.editingError.length > 0
            Layout.fillWidth: true
            text: root.controller.editingError
            color: root.theme.error
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.label
            wrapMode: Text.WordWrap
        }
    }

    footer: Controls.DialogActions {
        theme: root.theme
        Controls.Button {
            objectName: "userProfileEditorCancel"
            theme: root.theme
            text: qsTr("Cancel")
            enabled: !root.controller.editingBusy
            onClicked: root.reject()
        }
        Controls.Button {
            objectName: "userProfileEditorSave"
            theme: root.theme
            text: root.creating ? qsTr("Create") : qsTr("Save")
            icon.name: "save"
            highlighted: true
            enabled: !root.controller.editingBusy
            onClicked: root.save()
        }
    }
}

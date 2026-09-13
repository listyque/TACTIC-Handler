import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

ColumnLayout {
    id: root

    required property var theme
    required property var controller
    required property var groupsModel
    required property var membersModel
    property string editorPage: "members"
    readonly property bool compact: width < 780
    readonly property bool hasGroup: controller.draft.name !== undefined
    spacing: 12

    AdminSaveBar {
        objectName: "adminGroupToolbar"
        Layout.fillWidth: true
        theme: root.theme
        busy: root.controller.busy
        dirty: root.controller.dirty
        canWrite: root.controller.canManage
        saveObjectName: "saveSecurityGroup"
        onDiscardRequested: root.controller.discard()
        onSaveRequested: root.controller.save()
        leadingActions: [
            Controls.Button {
                objectName: "createSecurityGroup"
                theme: root.theme
                text: qsTr("Create group")
                icon.name: "person-add"
                enabled: root.controller.canManage && !root.controller.busy && !root.controller.dirty
                onClicked: {
                    root.controller.new_group()
                    root.editorPage = "details"
                    groupName.forceActiveFocus()
                }
            },
            Controls.CompactIconButton {
                theme: root.theme
                iconName: "refresh"
                toolTip: qsTr("Reload from server")
                enabled: !root.controller.busy && !root.controller.dirty
                onClicked: root.controller.reload()
            }
        ]
    }
    Label {
        Layout.fillWidth: true
        visible: root.controller.error.length > 0
        text: root.controller.error
        color: root.theme.error
        font.pointSize: Controls.Typography.body
        wrapMode: Text.WordWrap
    }
    RowLayout {
        Layout.fillWidth: true
        Layout.fillHeight: true
        Layout.minimumHeight: 150
        spacing: 12

        Controls.EditorPanel {
            Layout.preferredWidth: root.compact ? 190 : 250
            Layout.fillHeight: true
            theme: root.theme
            title: qsTr("Groups")
            iconName: "groups"

            ListView {
                id: groupList
                objectName: "securityGroupsList"
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 4
                model: root.groupsModel
                boundsBehavior: Flickable.StopAtBounds
                delegate: Controls.EditorListItem {
                    required property var model
                    required property string code
                    required property string name
                    required property int memberCount
                    objectName: "securityGroup_" + code
                    width: groupList.width - groupBar.reservedExtent - 4
                    theme: root.theme
                    text: name
                    description: model.description
                    badgeText: String(memberCount)
                    selected: root.controller.draft.code === code
                    enabled: !root.controller.busy && !root.controller.dirty
                    onClicked: root.controller.select_group(code)
                }
                ScrollBar.vertical: Controls.ScrollBar {
                    id: groupBar
                    objectName: "securityGroupsScrollBar"
                    theme: root.theme
                    flickableTarget: groupList
                }
                Controls.EmptyState {
                    anchors.centerIn: parent
                    width: parent.width - groupBar.reservedExtent - 8
                    visible: groupList.count === 0 && !root.controller.busy
                    theme: root.theme
                    iconName: "groups"
                    title: qsTr("No user groups yet")
                }
            }
        }

        Controls.EditorPanel {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumWidth: 0
            theme: root.theme
            title: root.hasGroup ? root.controller.draft.name || qsTr("New group") : qsTr("Group")
            description: root.hasGroup ? qsTr("Members: %1").arg(root.controller.memberCount) : ""
            iconName: "groups"

            Controls.EmptyState {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: !root.hasGroup
                theme: root.theme
                iconName: "groups"
                title: qsTr("Select a group or create a new one")
            }
            Controls.SegmentedButton {
                objectName: "securityGroupEditorTabs"
                Layout.fillWidth: true
                visible: root.hasGroup
                theme: root.theme
                currentValue: root.editorPage
                model: [
                    {value: "members", label: qsTr("Members"), icon: "person", translate: false},
                    {value: "details", label: qsTr("Group details"), icon: "edit", translate: false}
                ]
                onActivated: value => root.editorPage = value
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumWidth: 0
                visible: root.hasGroup && root.editorPage === "members"
                enabled: !root.controller.busy && root.controller.canManage
                spacing: 8
                Controls.TextField {
                    objectName: "securityMemberSearch"
                    Layout.fillWidth: true
                    theme: root.theme
                    placeholderText: qsTr("Search users")
                    onTextEdited: root.controller.set_user_query(text)
                }
                Label {
                    Layout.fillWidth: true
                    text: qsTr("Check the people who belong to this group")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                    wrapMode: Text.WordWrap
                }
                ListView {
                    id: memberList
                    objectName: "securityMembersList"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 4
                    model: root.membersModel
                    boundsBehavior: Flickable.StopAtBounds
                    delegate: Controls.CheckBox {
                        id: memberRow
                        required property string login
                        required property string displayName
                        required property bool member
                        required property string initials
                        required property string avatarUrl
                        required property string avatarColor
                        required property bool retired
                        objectName: "securityMember_" + login
                        width: memberList.width - memberBar.reservedExtent - 4
                        implicitHeight: Math.max(root.theme.controlHeight + 10, memberContent.implicitHeight + 18)
                        leftPadding: 10
                        rightPadding: 10
                        theme: root.theme
                        text: displayName
                        checked: member
                        Accessible.description: login
                        background: Controls.ItemSurface {
                            theme: root.theme
                            selected: memberRow.checked
                            hovered: memberRow.hovered
                            pressed: memberRow.down
                            normalColor: root.theme.surfaceContainerLow
                            selectedColor: root.theme.surfaceContainerHigh
                            railVisible: false
                            cornerRadius: root.theme.itemRadius
                            separatorVisible: false
                        }
                        contentItem: Item {
                            implicitHeight: memberContent.implicitHeight
                            RowLayout {
                                id: memberContent
                                anchors.left: parent.left
                                anchors.leftMargin: memberRow.indicator.width + memberRow.spacing
                                anchors.right: parent.right
                                anchors.verticalCenter: parent.verticalCenter
                                spacing: 9
                                UserIdentity {
                                    Layout.fillWidth: true
                                    theme: root.theme
                                    login: memberRow.login
                                    displayName: memberRow.displayName
                                    initials: memberRow.initials
                                    avatarUrl: memberRow.avatarUrl
                                    avatarColor: memberRow.avatarColor
                                    retired: memberRow.retired
                                }
                                Controls.MaterialIcon {
                                    visible: memberRow.retired
                                    name: "inventory-2"
                                    size: 18
                                    color: root.theme.secondaryText
                                    Accessible.name: qsTr("Retired")
                                }
                            }
                        }
                        onToggled: root.controller.set_member(login, checked)
                    }
                    ScrollBar.vertical: Controls.ScrollBar {
                        id: memberBar
                        objectName: "securityMembersScrollBar"
                        theme: root.theme
                        flickableTarget: memberList
                    }
                    Controls.EmptyState {
                        anchors.centerIn: parent
                        width: parent.width - memberBar.reservedExtent - 8
                        visible: memberList.count === 0
                        theme: root.theme
                        iconName: "person"
                        title: qsTr("No users match the search")
                    }
                }
            }

            Flickable {
                id: details
                objectName: "securityGroupDetails"
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: root.hasGroup && root.editorPage === "details"
                enabled: !root.controller.busy && root.controller.canManage
                clip: true
                contentWidth: width
                contentHeight: detailsForm.implicitHeight
                boundsBehavior: Flickable.StopAtBounds
                ColumnLayout {
                    id: detailsForm
                    width: details.width - detailsBar.reservedExtent - 4
                    spacing: 12
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("Group identifier")
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.body
                        font.weight: Font.DemiBold
                    }
                    Controls.TextField {
                        id: groupName
                        objectName: "securityGroupName"
                        Layout.fillWidth: true
                        theme: root.theme
                        text: root.controller.draft.name || ""
                        readOnly: Boolean(root.controller.draft.code)
                        placeholderText: qsTr("Unique identifier")
                        onTextEdited: root.controller.set_field("name", text)
                    }
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("The identifier is used in access rules and cannot be changed after creation.")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                        wrapMode: Text.WordWrap
                    }
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("Description")
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.body
                        font.weight: Font.DemiBold
                    }
                    Controls.TextArea {
                        objectName: "securityGroupDescription"
                        Layout.fillWidth: true
                        Layout.minimumHeight: root.theme.controlHeight * 2
                        theme: root.theme
                        text: root.controller.draft.description || ""
                        placeholderText: qsTr("What is this group responsible for?")
                        onTextChanged: {
                            if (activeFocus && text !== (root.controller.draft.description || ""))
                                root.controller.set_field("description", text)
                        }
                    }
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("Membership changes apply on the server. Sidebar visibility rules are configured separately for each sidebar item.")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                        wrapMode: Text.WordWrap
                    }
                }
                ScrollBar.vertical: Controls.ScrollBar {
                    id: detailsBar
                    objectName: "securityDetailsScrollBar"
                    theme: root.theme
                    flickableTarget: details
                }
            }
        }
    }
}

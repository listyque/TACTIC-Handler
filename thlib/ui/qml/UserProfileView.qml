import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    property string userSearch: ""
    property bool activityExpanded: false
    readonly property var profileController: userController
    readonly property var taskWorkspaceController: tasksController

    UserFilter {
        id: filteredUsers
        model: userListModel
        searchText: root.userSearch
    }

    function hours(value) {
        const number = Number(value || 0)
        return number.toLocaleString(Qt.locale(), "f", number % 1 ? 1 : 0)
    }

    UserProfileEditorDialog {
        id: profileEditor
        anchors.centerIn: parent
        theme: root.theme
        controller: userController
    }

    Rectangle {
        anchors.fill: parent
        color: root.theme.workspace
    }

    SplitView {
        anchors.fill: parent
        anchors.margins: 12
        orientation: Qt.Horizontal
        handle: Rectangle {
            visible: userController.directoryVisible
            implicitWidth: visible ? 8 : 0
            color: "transparent"
        }

        Rectangle {
            visible: userController.directoryVisible
            SplitView.preferredWidth: 252
            SplitView.minimumWidth: 210
            SplitView.maximumWidth: 360
            radius: 12
            color: root.theme.panel
            border.width: 1
            border.color: root.theme.outlineVariant
            clip: true

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 14
                spacing: 12

                RowLayout {
                    Layout.fillWidth: true
                    Controls.SectionLabel {
                        Layout.fillWidth: true
                        theme: root.theme
                        text: qsTr("USERS")
                    }
                    Label {
                        text: userListModel.count()
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                    }
                    Controls.CompactIconButton {
                        theme: root.theme
                        visible: userController.canManageUsers
                        enabled: !userController.editingBusy
                        iconName: "person-add"
                        toolTip: qsTr("Add user")
                        onClicked: profileEditor.openForCreate()
                    }
                }

                Controls.SearchField {
                    Layout.fillWidth: true
                    theme: root.theme
                    placeholderText: qsTr("Search users")
                    text: root.userSearch
                    onTextChanged: root.userSearch = text
                }

                ListView {
                    id: usersList
                    objectName: "userDirectoryList"
                    readonly property real scrollBarGutter: 16

                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 6
                    model: filteredUsers
                    section.property: "primaryGroup"
                    section.criteria: ViewSection.FullString
                    section.delegate: UserGroupSection {
                        required property string section
                        width: Math.max(
                            0,
                            usersList.width - usersList.scrollBarGutter
                        )
                        theme: root.theme
                        title: section
                    }

                    delegate: Item {
                        id: userRow
                        objectName: "userDirectoryRow_" + login

                        required property string login
                        required property string displayName
                        required property string initials
                        required property string email
                        required property string avatarUrl
                        required property string avatarColor
                        required property var groups
                        required property string primaryGroup
                        required property bool current
                        required property bool selected
                        required property bool presenceKnown
                        required property bool online
                        required property string lastSeen

                        width: Math.max(
                            0, usersList.width - usersList.scrollBarGutter
                        )
                        height: 68

                        Controls.ItemSurface {
                            anchors.fill: parent
                            theme: root.theme
                            selected: userRow.selected
                            hovered: userMouse.containsMouse
                            pressed: userMouse.pressed
                            accent: userRow.current
                                ? root.theme.green : root.theme.action
                            cornerRadius: root.theme.itemRadius
                            inset: 1
                            railVisible: userRow.current
                            separatorVisible: false
                        }
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 9
                            anchors.rightMargin: 9
                            spacing: 9

                            Controls.ItemPreview {
                                Layout.preferredWidth: 34
                                Layout.preferredHeight: 34
                                theme: root.theme
                                source: userRow.avatarUrl
                                fallbackIcon: "person"
                                fallbackText: userRow.initials
                                previewSize: 34
                                round: true
                                outlined: true
                                animateAppearance: false
                                accent: userRow.avatarColor.length
                                    ? userRow.avatarColor : root.theme.action
                            }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 1
                                Label {
                                    Layout.fillWidth: true
                                    text: userRow.displayName
                                    color: userRow.selected
                                        ? root.theme.selectedText
                                        : root.theme.primaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.body
                                    font.weight: Font.DemiBold
                                    elide: Text.ElideRight
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: userRow.groups && userRow.groups.length
                                        ? userRow.groups[0] : userRow.login
                                    color: userRow.selected
                                        ? root.theme.selectedText
                                        : root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.caption
                                    elide: Text.ElideRight
                                }
                            }
                            Rectangle {
                                visible: userRow.presenceKnown
                                Layout.preferredWidth: 7
                                Layout.preferredHeight: 7
                                radius: 4
                                color: userRow.online
                                    ? root.theme.green : root.theme.red
                            }
                        }
                        MouseArea {
                            id: userMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: userController.select_profile(userRow.login)
                        }
                    }
                    ScrollBar.vertical: Controls.ScrollBar {
                        id: usersScrollBar
                        objectName: "userDirectoryScrollBar"
                        theme: root.theme
                        flickableTarget: usersList
                    }
                }
            }
        }

        Rectangle {
            SplitView.fillWidth: true
            radius: 12
            color: root.theme.panel
            border.width: 1
            border.color: root.theme.outlineVariant
            clip: true

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 10

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 194
                    radius: 9
                    color: root.theme.surfaceContainerHigh

                    GridLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 16
                        anchors.rightMargin: 12
                        anchors.topMargin: 13
                        anchors.bottomMargin: 13
                        columns: 7
                        columnSpacing: 10
                        rowSpacing: 4

                        Controls.ItemPreview {
                            Layout.row: 0
                            Layout.column: 0
                            Layout.rowSpan: 2
                            Layout.preferredWidth: 168
                            Layout.preferredHeight: 168
                            theme: root.theme
                            source: userController.profile.avatarUrl || ""
                            fallbackIcon: "person"
                            fallbackText: userController.profile.initials || "?"
                            previewSize: 168
                            round: true
                            outlined: true
                            accent: userController.profile.avatarColor
                                || root.theme.action
                        }
                        ColumnLayout {
                            Layout.row: 0
                            Layout.column: 1
                            Layout.columnSpan: 2
                            Layout.fillWidth: true
                            Layout.minimumWidth: 170
                            spacing: 2
                            Label {
                                Layout.fillWidth: true
                                text: userController.profile.displayName
                                    || qsTr("User")
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pixelSize: 18
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 6
                                Rectangle {
                                    visible: !!userController.profile.presenceKnown
                                    Layout.preferredWidth: 7
                                    Layout.preferredHeight: 7
                                    radius: 4
                                    color: userController.profile.online
                                        ? root.theme.green : root.theme.red
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: {
                                        const login = userController.profile.login || ""
                                        const presence = userController.profile.presenceKnown
                                            ? (userController.profile.online
                                                ? qsTr("Online") : qsTr("Offline"))
                                            : qsTr("Status unavailable")
                                        return login.length
                                            ? login + " · " + presence : presence
                                    }
                                    color: root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.body
                                    elide: Text.ElideRight
                                }
                            }
                        }
                        RowLayout {
                            Layout.row: 1
                            Layout.column: 1
                            Layout.columnSpan: 6
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            Layout.topMargin: 4
                            spacing: 18

                            ColumnLayout {
                                Layout.fillWidth: true
                                Layout.alignment: Qt.AlignVCenter
                                spacing: 5

                                Controls.SectionLabel {
                                    theme: root.theme
                                    text: qsTr("PROFILE")
                                }
                                GridLayout {
                                    Layout.fillWidth: true
                                    columns: width >= 560 ? 3 : 2
                                    columnSpacing: 14
                                    rowSpacing: 4

                                    Controls.ProfileInfoRow {
                                        Layout.fillWidth: true
                                        theme: root.theme
                                        iconName: "briefcase"
                                        label: qsTr("Project")
                                        value: userController.profile.project || ""
                                    }
                                    Controls.ProfileInfoRow {
                                        Layout.fillWidth: true
                                        theme: root.theme
                                        iconName: "envelope"
                                        label: qsTr("Email")
                                        value: userController.profile.email || ""
                                    }
                                    Controls.ProfileInfoRow {
                                        Layout.fillWidth: true
                                        theme: root.theme
                                        iconName: "phone"
                                        label: qsTr("Contact")
                                        value: userController.profile.contact || ""
                                    }
                                    Controls.ProfileInfoRow {
                                        Layout.fillWidth: true
                                        theme: root.theme
                                        iconName: "address-book"
                                        label: qsTr("Address")
                                        value: userController.profile.address || ""
                                    }
                                    Controls.ProfileInfoRow {
                                        Layout.fillWidth: true
                                        theme: root.theme
                                        iconName: "briefcase"
                                        label: qsTr("Department")
                                        value: userController.profile.department || ""
                                    }
                                    Controls.ProfileInfoRow {
                                        Layout.fillWidth: true
                                        theme: root.theme
                                        iconName: "server"
                                        label: qsTr("Server")
                                        value: userController.profile.server || ""
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillHeight: true
                                Layout.preferredWidth: 1
                                color: root.theme.separator
                            }

                            ColumnLayout {
                                Layout.preferredWidth: 300
                                Layout.maximumWidth: 360
                                Layout.minimumWidth: 210
                                Layout.alignment: Qt.AlignVCenter
                                spacing: 5

                                RowLayout {
                                    Layout.fillWidth: true
                                    Controls.SectionLabel {
                                        Layout.fillWidth: true
                                        theme: root.theme
                                        text: qsTr("GROUPS AND ROLES")
                                    }
                                    Controls.CompactIconButton {
                                        theme: root.theme
                                        visible: userController.canManageUsers
                                        iconName: "groups"
                                        toolTip: qsTr("Edit group membership")
                                        onClicked: profileEditor.openForGroups()
                                    }
                                }
                                Flow {
                                    Layout.fillWidth: true
                                    spacing: 6
                                    Repeater {
                                        model: userController.profile.groups || []
                                        delegate: Controls.SummaryChip {
                                            required property var modelData
                                            theme: root.theme
                                            label: modelData.label || ""
                                            showDot: true
                                            showCount: false
                                            accent: root.theme.action
                                        }
                                    }
                                    Repeater {
                                        model: userController.profile.roles || []
                                        delegate: Controls.SummaryChip {
                                            required property var modelData
                                            theme: root.theme
                                            label: String(modelData || "")
                                            showDot: false
                                            showCount: false
                                        }
                                    }
                                }
                                Label {
                                    visible: (userController.profile.groups || []).length === 0
                                        && (userController.profile.roles || []).length === 0
                                    text: qsTr("No groups or roles returned by TACTIC")
                                    color: root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.label
                                }
                            }
                        }
                        Controls.Button {
                            Layout.row: 0
                            Layout.column: 3
                            theme: root.theme
                            visible: !!userController.profile.login
                                && !userController.profile.current
                            text: qsTr("MESSAGE")
                            icon.name: "message"
                            highlighted: true
                            enabled: !messagesController.busy
                                && appController.server_state === "online"
                            onClicked: messagesController.open_direct_conversation(
                                userController.profile.login
                            )
                        }
                        Controls.CompactIconButton {
                            Layout.row: 0
                            Layout.column: 4
                            theme: root.theme
                            visible: userController.canEdit
                            iconName: "edit"
                            toolTip: qsTr("Edit user profile")
                            enabled: !userController.editingBusy
                                && appController.server_state === "online"
                            onClicked: profileEditor.openForProfile()
                        }
                        RefreshIconButton {
                            Layout.row: 0
                            Layout.column: 5
                            theme: root.theme
                            toolTip: qsTr("Refresh profile")
                            enabled: !userController.busy
                                && !userController.tasksBusy
                                && appController.server_state === "online"
                            onClicked: userController.refresh()
                        }
                        Controls.CompactIconButton {
                            Layout.row: 0
                            Layout.column: 6
                            theme: root.theme
                            visible: !!userController.profile.current
                            iconName: "logout"
                            iconColor: root.theme.red
                            toolTip: qsTr("Sign out")
                            enabled: !userController.busy
                            onClicked: userController.logout()
                        }
                    }
                }

                ScrollView {
                    id: profileScroll

                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    contentWidth: availableWidth
                    ScrollBar.vertical: Controls.ScrollBar { theme: root.theme }

                    ColumnLayout {
                        width: profileScroll.availableWidth
                        spacing: 0

                        Flow {
                            id: contentFlow

                            Layout.fillWidth: true
                            Layout.leftMargin: 12
                            Layout.rightMargin: 12
                            Layout.topMargin: 8
                            Layout.bottomMargin: 12
                            spacing: 0

                            Item {
                                width: contentFlow.width >= 860
                                    ? Math.floor(contentFlow.width * 0.61)
                                    : contentFlow.width
                                height: taskSummaryColumn.implicitHeight

                                UserWorkSummary {
                                    id: taskSummaryColumn

                                    anchors.left: parent.left
                                    anchors.right: parent.right
                                    anchors.rightMargin: contentFlow.width >= 860
                                        ? 24 : 0
                                    theme: root.theme
                                    userController: root.profileController
                                    tasksController: root.taskWorkspaceController
                                }
                                Rectangle {
                                    visible: contentFlow.width >= 860
                                    anchors.top: parent.top
                                    anchors.bottom: parent.bottom
                                    anchors.right: parent.right
                                    width: 1
                                    color: root.theme.separator
                                }
                            }

                            Item {
                                width: contentFlow.width >= 860
                                    ? contentFlow.width - Math.floor(contentFlow.width * 0.61)
                                    : contentFlow.width
                                height: profileColumn.implicitHeight

                                ColumnLayout {
                                    id: profileColumn
                                    anchors.left: parent.left
                                    anchors.right: parent.right
                                    anchors.leftMargin: contentFlow.width >= 860 ? 24 : 0
                                    anchors.topMargin: contentFlow.width >= 860 ? 0 : 24
                                    spacing: 12

                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 8

                                        Controls.SectionLabel {
                                            Layout.fillWidth: true
                                            theme: root.theme
                                            text: qsTr("RECENT ACTIVITY")
                                        }
                                        Controls.CompactIconButton {
                                            objectName: "openFullUserActivityButton"
                                            theme: root.theme
                                            iconName: "activity-feed"
                                            toolTip: qsTr("Open full activity")
                                            onClicked:
                                                userController.open_full_activity()
                                        }
                                    }
                                    Repeater {
                                        id: recentActivityRepeater

                                        model: userActivityModel
                                        delegate: Item {
                                            id: activityRow

                                            required property int index
                                            required property string searchKey
                                            required property string targetSearchKey
                                            required property string targetTitle
                                            required property string targetType
                                            required property string targetTypeTitle
                                            required property string kind
                                            required property string title
                                            required property string detail
                                            required property string actor
                                            required property string actorLabel
                                            required property string actorAvatar
                                            required property string actorInitials
                                            required property string actorColor
                                            required property string timestamp
                                            required property string timestampPretty
                                            required property string timestampFull
                                            required property string itemCode
                                            required property string itemTitle
                                            required property string itemType
                                            required property string itemTypeTitle
                                            required property string itemTypeColor
                                            required property string relationAction
                                            required property string typeColor
                                            required property string processColor
                                            required property string project
                                            required property string process
                                            required property string context
                                            required property string version
                                            required property string statusBefore
                                            required property string statusAfter
                                            required property string statusBeforeColor
                                            required property string statusAfterColor
                                            required property var changes
                                            required property string taskCode
                                            required property real hours
                                            required property string workDay
                                            required property string workDayPretty
                                            required property string workHourAction
                                            required property string workHourCategory
                                            required property string workHourStatus
                                            required property string workHourOwner
                                            required property bool serverGenerated
                                            readonly property bool inPreview: index < 6
                                                || root.activityExpanded

                                            visible: inPreview
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: inPreview
                                                ? activityCard.implicitHeight : 0

                                            ActivityEventCard {
                                                id: activityCard
                                                anchors.fill: parent
                                                theme: root.theme
                                                kind: activityRow.kind
                                                eventTitle: activityRow.title
                                                detail: activityRow.detail
                                                actor: activityRow.actor
                                                actorLabel: activityRow.actorLabel
                                                actorAvatar: activityRow.actorAvatar
                                                actorInitials: activityRow.actorInitials
                                                actorColor: activityRow.actorColor
                                                timestamp: activityRow.timestamp
                                                timestampPretty:
                                                    activityRow.timestampPretty
                                                timestampFull:
                                                    activityRow.timestampFull
                                                targetSearchKey:
                                                    activityRow.targetSearchKey
                                                targetTitle:
                                                    activityRow.targetTitle
                                                targetType: activityRow.targetType
                                                targetTypeTitle:
                                                    activityRow.targetTypeTitle
                                                itemCode: activityRow.itemCode
                                                itemTitle: activityRow.itemTitle
                                                itemType: activityRow.itemType
                                                itemTypeTitle:
                                                    activityRow.itemTypeTitle
                                                itemTypeColor:
                                                    activityRow.itemTypeColor
                                                relationAction:
                                                    activityRow.relationAction
                                                typeColor: activityRow.typeColor
                                                processColor: activityRow.processColor
                                                process: activityRow.process
                                                context: activityRow.context
                                                version: activityRow.version
                                                statusBefore:
                                                    activityRow.statusBefore
                                                statusAfter:
                                                    activityRow.statusAfter
                                                statusBeforeColor:
                                                    activityRow.statusBeforeColor
                                                statusAfterColor:
                                                    activityRow.statusAfterColor
                                                changes: activityRow.changes
                                                taskCode: activityRow.taskCode
                                                hours: activityRow.hours
                                                workDay: activityRow.workDay
                                                workDayPretty:
                                                    activityRow.workDayPretty
                                                workHourAction:
                                                    activityRow.workHourAction
                                                workHourCategory:
                                                    activityRow.workHourCategory
                                                workHourStatus:
                                                    activityRow.workHourStatus
                                                workHourOwner:
                                                    activityRow.workHourOwner
                                                serverGenerated:
                                                    activityRow.serverGenerated
                                                canOpenActivity:
                                                    activityRow.searchKey.length > 0
                                                canOpenTarget:
                                                    activityRow.targetSearchKey.length > 0
                                                onActivityRequested:
                                                    activityRow.taskCode.length
                                                        ? userController.open_task_activity(
                                                            activityRow.targetSearchKey,
                                                            activityRow.taskCode,
                                                            activityRow.process
                                                        )
                                                        : userController.open_activity(
                                                            activityRow.searchKey
                                                        )
                                                onTargetRequested:
                                                    activityRow.taskCode.length
                                                        ? userController.open_task_activity(
                                                            activityRow.targetSearchKey,
                                                            activityRow.taskCode,
                                                            activityRow.process
                                                        )
                                                        : activityRow.kind === "message"
                                                        ? userController.open_activity(
                                                            activityRow.searchKey
                                                        )
                                                        : userController.open_activity_target(
                                                            activityRow.targetSearchKey
                                                        )
                                            }
                                        }
                                    }
                                    Controls.Button {
                                        Layout.alignment: Qt.AlignLeft
                                        visible: recentActivityRepeater.count > 6
                                        theme: root.theme
                                        text: root.activityExpanded
                                            ? qsTr("SHOW LESS")
                                            : qsTr("SHOW MORE") + " ("
                                                + recentActivityRepeater.count + ")"
                                        icon.name: root.activityExpanded
                                            ? "expand-less" : "expand-more"
                                        onClicked: root.activityExpanded = !root.activityExpanded
                                    }
                                    Label {
                                        visible: !userController.busy
                                            && recentActivityRepeater.count === 0
                                        text: userController.activityError
                                            ? qsTr("Activity is unavailable")
                                            : qsTr("No recent activity")
                                        color: root.theme.secondaryText
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Controls.Typography.label
                                    }
                                }
                            }
                        }

                        Label {
                            Layout.fillWidth: true
                            Layout.leftMargin: 22
                            Layout.rightMargin: 22
                            Layout.bottomMargin: 18
                            visible: userController.error.length > 0
                            text: userController.error
                            color: root.theme.red
                            wrapMode: Text.WordWrap
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.label
                        }
                    }
                }
            }

            ContentLoadingOverlay {
                anchors.fill: parent
                z: 20
                theme: root.theme
                // Related activity/tasks load independently.  The bootstrap
                // profile must remain usable while either request is active.
                visible: (userController.busy || userController.tasksBusy)
                    && !userController.profile.login
                message: userController.tasksBusy
                    ? qsTr("Loading task summary…")
                    : qsTr("Loading user profile…")
            }
        }
    }
}

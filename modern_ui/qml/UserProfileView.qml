import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    required property var theme
    property string userSearch: ""
    property bool activityExpanded: false

    function matchesUser(name, login, groups) {
        const query = root.userSearch.trim().toLowerCase()
        if (!query.length)
            return true
        const groupText = (groups || []).join(" ")
        return (String(name || "") + " " + String(login || "")
            + " " + groupText).toLowerCase().indexOf(query) >= 0
    }

    function groupHasMatches(group) {
        for (let index = 0; index < userListModel.count(); ++index) {
            const user = userListModel.get(index)
            if (String(user.primaryGroup || "") === String(group || "")
                    && root.matchesUser(user.displayName, user.login, user.groups))
                return true
        }
        return false
    }

    function hours(value) {
        const number = Number(value || 0)
        return number.toLocaleString(Qt.locale(), "f", number % 1 ? 1 : 0)
    }

    component SectionLabel: Label {
        required property var theme
        color: theme.secondaryText
        font.family: theme.fontFamily
        font.pixelSize: 10
        font.weight: Font.DemiBold
        font.letterSpacing: 0.5
    }

    component SummaryChip: Rectangle {
        id: chip

        required property var theme
        property string label: ""
        property int count: 0
        property color accent: theme.action
        property bool showDot: true
        property bool showCount: true

        implicitWidth: chipRow.implicitWidth + 20
        implicitHeight: 30
        radius: 15
        color: theme.surfaceContainerHigh
        border.width: 1
        border.color: theme.outlineVariant

        Row {
            id: chipRow
            anchors.centerIn: parent
            spacing: 7

            Rectangle {
                visible: chip.showDot
                anchors.verticalCenter: parent.verticalCenter
                width: 8
                height: 8
                radius: 4
                color: chip.accent
            }
            Label {
                anchors.verticalCenter: parent.verticalCenter
                text: chip.label
                color: chip.theme.primaryText
                font.family: chip.theme.fontFamily
                font.pixelSize: 9
            }
            Label {
                visible: chip.showCount
                anchors.verticalCenter: parent.verticalCenter
                text: chip.count
                color: chip.accent
                font.family: chip.theme.fontFamily
                font.pixelSize: 9
                font.weight: Font.DemiBold
            }
        }
    }

    component ProfileRow: RowLayout {
        id: profileRow

        required property var theme
        property string iconName: ""
        property string label: ""
        property string value: ""

        spacing: 9
        visible: value.length > 0

        MaterialIcon {
            name: parent.iconName
            size: 15
            color: parent.theme.secondaryText
        }
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 0
            Label {
                text: profileRow.label
                color: profileRow.theme.secondaryText
                font.family: profileRow.theme.fontFamily
                font.pixelSize: 8
            }
            Label {
                Layout.fillWidth: true
                text: profileRow.value
                color: profileRow.theme.primaryText
                font.family: profileRow.theme.fontFamily
                font.pixelSize: 10
                elide: Text.ElideMiddle
            }
        }
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
                    SectionLabel {
                        Layout.fillWidth: true
                        theme: root.theme
                        text: qsTr("USERS")
                    }
                    Label {
                        text: userListModel.count()
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 9
                    }
                    CompactIconButton {
                        theme: root.theme
                        visible: userController.canManageUsers
                        enabled: !userController.editingBusy
                        iconName: "person-add"
                        toolTip: qsTr("Add user")
                        onClicked: profileEditor.openForCreate()
                    }
                }

                Md3TextField {
                    Layout.fillWidth: true
                    theme: root.theme
                    placeholderText: qsTr("Search users")
                    text: root.userSearch
                    onTextChanged: root.userSearch = text
                }

                ListView {
                    id: usersList

                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 6
                    model: userListModel
                    section.property: "primaryGroup"
                    section.criteria: ViewSection.FullString
                    section.delegate: UserGroupSection {
                        required property string section
                        width: ListView.view.width
                        theme: root.theme
                        title: section
                        shown: root.groupHasMatches(section)
                    }

                    delegate: Item {
                        id: userRow

                        required property string login
                        required property string displayName
                        required property string initials
                        required property string email
                        required property string avatarUrl
                        required property var groups
                        required property string primaryGroup
                        required property bool current
                        required property bool selected
                        required property bool presenceKnown
                        required property bool online
                        required property string lastSeen
                        readonly property bool matches: root.matchesUser(
                            displayName, login, groups
                        )

                        width: usersList.width
                        height: matches ? 68 : 0
                        visible: matches

                        ItemSurface {
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

                            ItemPreview {
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
                                accent: userRow.current
                                    ? root.theme.green : root.theme.action
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
                                    font.pixelSize: 10
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
                                    font.pixelSize: 8
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
                    ScrollBar.vertical: Md3ScrollBar { theme: root.theme }
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

                        ItemPreview {
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
                            accent: userController.profile.current
                                ? root.theme.green : root.theme.action
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
                                    font.pixelSize: 10
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

                                SectionLabel {
                                    theme: root.theme
                                    text: qsTr("PROFILE")
                                }
                                GridLayout {
                                    Layout.fillWidth: true
                                    columns: width >= 560 ? 3 : 2
                                    columnSpacing: 14
                                    rowSpacing: 4

                                    ProfileRow {
                                        Layout.fillWidth: true
                                        theme: root.theme
                                        iconName: "briefcase"
                                        label: qsTr("Project")
                                        value: userController.profile.project || ""
                                    }
                                    ProfileRow {
                                        Layout.fillWidth: true
                                        theme: root.theme
                                        iconName: "envelope"
                                        label: qsTr("Email")
                                        value: userController.profile.email || ""
                                    }
                                    ProfileRow {
                                        Layout.fillWidth: true
                                        theme: root.theme
                                        iconName: "phone"
                                        label: qsTr("Contact")
                                        value: userController.profile.contact || ""
                                    }
                                    ProfileRow {
                                        Layout.fillWidth: true
                                        theme: root.theme
                                        iconName: "briefcase"
                                        label: qsTr("Department")
                                        value: userController.profile.department || ""
                                    }
                                    ProfileRow {
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
                                    SectionLabel {
                                        Layout.fillWidth: true
                                        theme: root.theme
                                        text: qsTr("GROUPS AND ROLES")
                                    }
                                    CompactIconButton {
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
                                        delegate: SummaryChip {
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
                                        delegate: SummaryChip {
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
                                    font.pixelSize: 9
                                }
                            }
                        }
                        Md3Button {
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
                        CompactIconButton {
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
                        CompactIconButton {
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
                    ScrollBar.vertical: Md3ScrollBar { theme: root.theme }

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

                                ColumnLayout {
                                    id: taskSummaryColumn
                                    anchors.left: parent.left
                                    anchors.right: parent.right
                                    anchors.rightMargin: contentFlow.width >= 860 ? 24 : 0
                                    spacing: 12

                                    RowLayout {
                                        Layout.fillWidth: true
                                        SectionLabel {
                                            Layout.fillWidth: true
                                            theme: root.theme
                                            text: qsTr("TASK SUMMARY")
                                        }
                                        Label {
                                            text: qsTr("%1 tasks").arg(
                                                userController.taskSummary.total || 0
                                            )
                                            color: root.theme.secondaryText
                                            font.family: root.theme.fontFamily
                                            font.pixelSize: 9
                                        }
                                    }

                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 14

                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            spacing: 1
                                            Label {
                                                text: userController.taskSummary.active || 0
                                                color: root.theme.primaryText
                                                font.family: root.theme.fontFamily
                                                font.pixelSize: 22
                                                font.weight: Font.DemiBold
                                            }
                                            Label {
                                                text: qsTr("Active")
                                                color: root.theme.secondaryText
                                                font.family: root.theme.fontFamily
                                                font.pixelSize: 9
                                            }
                                        }
                                        Rectangle {
                                            Layout.preferredWidth: 1
                                            Layout.preferredHeight: 38
                                            color: root.theme.separator
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            spacing: 1
                                            Label {
                                                text: userController.taskSummary.overdue || 0
                                                color: Number(text) > 0
                                                    ? root.theme.red : root.theme.primaryText
                                                font.family: root.theme.fontFamily
                                                font.pixelSize: 22
                                                font.weight: Font.DemiBold
                                            }
                                            Label {
                                                text: qsTr("Overdue")
                                                color: root.theme.secondaryText
                                                font.family: root.theme.fontFamily
                                                font.pixelSize: 9
                                            }
                                        }
                                        Rectangle {
                                            Layout.preferredWidth: 1
                                            Layout.preferredHeight: 38
                                            color: root.theme.separator
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            spacing: 1
                                            Label {
                                                text: userController.taskSummary.dueThisWeek || 0
                                                color: root.theme.primaryText
                                                font.family: root.theme.fontFamily
                                                font.pixelSize: 22
                                                font.weight: Font.DemiBold
                                            }
                                            Label {
                                                text: qsTr("Due this week")
                                                color: root.theme.secondaryText
                                                font.family: root.theme.fontFamily
                                                font.pixelSize: 9
                                            }
                                        }
                                    }

                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 1
                                        color: root.theme.separator
                                    }

                                    SectionLabel {
                                        theme: root.theme
                                        text: qsTr("BY STATUS")
                                    }
                                    Flow {
                                        Layout.fillWidth: true
                                        spacing: 6
                                        Repeater {
                                            model: userController.taskStatusSummary
                                            delegate: SummaryChip {
                                                required property var modelData
                                                theme: root.theme
                                                label: modelData.label || qsTr("Unspecified")
                                                count: Number(modelData.count || 0)
                                                accent: modelData.color || root.theme.action
                                            }
                                        }
                                    }

                                    SectionLabel {
                                        theme: root.theme
                                        text: qsTr("BY PROCESS")
                                    }
                                    Flow {
                                        Layout.fillWidth: true
                                        spacing: 6
                                        Repeater {
                                            model: userController.taskProcessSummary
                                            delegate: SummaryChip {
                                                required property var modelData
                                                theme: root.theme
                                                label: modelData.label || qsTr("Unspecified")
                                                count: Number(modelData.count || 0)
                                                accent: modelData.color || root.theme.action
                                            }
                                        }
                                    }

                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 5
                                        RowLayout {
                                            Layout.fillWidth: true
                                            SectionLabel {
                                                Layout.fillWidth: true
                                                theme: root.theme
                                                text: qsTr("WORKLOAD")
                                            }
                                            Label {
                                                text: qsTr("%1 / %2 h").arg(
                                                    root.hours(userController.taskSummary.loggedHours)
                                                ).arg(root.hours(
                                                    userController.taskSummary.plannedHours
                                                ))
                                                color: root.theme.secondaryText
                                                font.family: root.theme.fontFamily
                                                font.pixelSize: 9
                                            }
                                        }
                                        Rectangle {
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 7
                                            radius: 4
                                            color: root.theme.surfaceContainerHigh
                                            Rectangle {
                                                width: parent.width * Math.min(1,
                                                    Number(userController.taskSummary.workloadPercent || 0) / 100
                                                )
                                                height: parent.height
                                                radius: parent.radius
                                                color: root.theme.action
                                            }
                                        }
                                    }

                                    RowLayout {
                                        Layout.fillWidth: true
                                        Md3Button {
                                            theme: root.theme
                                            text: qsTr("OPEN TASK MANAGER")
                                            icon.name: "tasks"
                                            highlighted: true
                                            onClicked: tasksController.open_for_user(
                                                userController.login
                                            )
                                        }
                                        Item { Layout.fillWidth: true }
                                    }

                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 62
                                        visible: workHoursController.canManage
                                        radius: root.theme.itemRadius
                                        color: root.theme.surfaceContainerHigh
                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.leftMargin: 12
                                            anchors.rightMargin: 12
                                            spacing: 14
                                            MaterialIcon {
                                                name: "groups"
                                                size: 17
                                                color: root.theme.action
                                            }
                                            ColumnLayout {
                                                Layout.fillWidth: true
                                                spacing: 1
                                                Label {
                                                    text: qsTr("SUPERVISOR SUMMARY")
                                                    color: root.theme.primaryText
                                                    font.family: root.theme.fontFamily
                                                    font.pixelSize: 9
                                                    font.weight: Font.DemiBold
                                                }
                                                Label {
                                                    text: qsTr("Approved %1 h · Pending %2 h").arg(
                                                        root.hours(userController.taskSummary.approvedHours)
                                                    ).arg(root.hours(
                                                        userController.taskSummary.pendingHours
                                                    ))
                                                    color: root.theme.secondaryText
                                                    font.family: root.theme.fontFamily
                                                    font.pixelSize: 9
                                                }
                                            }
                                        }
                                    }

                                    Label {
                                        Layout.fillWidth: true
                                        visible: !userController.tasksBusy
                                            && (userController.taskSummary.total || 0) === 0
                                        text: qsTr("No assigned tasks in the current project")
                                        color: root.theme.secondaryText
                                        font.family: root.theme.fontFamily
                                        font.pixelSize: 9
                                    }
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

                                    SectionLabel {
                                        theme: root.theme
                                        text: qsTr("RECENT ACTIVITY")
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
                                            required property string kind
                                            required property string title
                                            required property string detail
                                            required property string actor
                                            required property string timestamp
                                            required property string project
                                            required property string process
                                            required property string context
                                            required property string version
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
                                                timestamp: activityRow.timestamp
                                                targetSearchKey:
                                                    activityRow.targetSearchKey
                                                targetTitle:
                                                    activityRow.targetTitle
                                                targetType: activityRow.targetType
                                                process: activityRow.process
                                                context: activityRow.context
                                                version: activityRow.version
                                                canOpenActivity:
                                                    activityRow.searchKey.length > 0
                                                canOpenTarget:
                                                    activityRow.targetSearchKey.length > 0
                                                onActivityRequested:
                                                    userController.open_activity(
                                                        activityRow.searchKey
                                                    )
                                                onTargetRequested:
                                                    activityRow.kind === "message"
                                                        ? userController.open_activity(
                                                            activityRow.searchKey
                                                        )
                                                        : userController.open_activity_target(
                                                            activityRow.targetSearchKey
                                                        )
                                            }
                                        }
                                    }
                                    Md3Button {
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
                                        font.pixelSize: 9
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
                            font.pixelSize: 9
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

import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Window

ApplicationWindow {
    id: window
    x: Math.max(
        Screen.virtualX,
        Math.min(
            appController.window_x,
            Screen.virtualX + Screen.width - width
        )
    )
    y: Math.max(
        Screen.virtualY,
        Math.min(
            appController.window_y,
            Screen.virtualY + Screen.height - height
        )
    )
    width: Math.min(appController.window_width, Screen.width)
    height: Math.min(appController.window_height, Screen.height)
    minimumWidth: 760
    minimumHeight: 640
    visible: true
    visibility: appController.window_maximized
        ? Window.Maximized : Window.Windowed
    title: handlerServerController.selectedClient
        ? qsTr("TACTIC-Handler · Connected to ")
            + handlerServerController.selectedApplicationType
                .charAt(0).toUpperCase()
            + handlerServerController.selectedApplicationType.slice(1)
        : "TACTIC-Handler"

    function saveWindowState() {
        appController.save_window_state(
            window.x,
            window.y,
            window.width,
            window.height,
            Number(window.visibility)
        )
    }

    onXChanged: saveWindowState()
    onYChanged: saveWindowState()
    onWidthChanged: saveWindowState()
    onHeightChanged: saveWindowState()
    onVisibilityChanged: saveWindowState()

    property bool dark: true
    property string themeStyle: appController.theme_style
    property string pageKey: appController.current_page_key
    property string pageTitle: appController.current_page_title
    property string pendingPageKey: pageKey
    property string pendingPageTitle: pageTitle
    property string projectTitle: appController.current_project_title
    readonly property bool workspaceAccessible:
        appController.server_state === "online"
        && appController.has_ticket
        && !appController.authentication_required
    readonly property bool serverConfigured:
        appController.server_url.indexOf("http://") === 0
        || appController.server_url.indexOf("https://") === 0
    function userActionsWithMessageBadge(actions, unreadCount) {
        return actions.map(action => {
            const copy = Object.assign({}, action)
            if (copy.command === "show_messages")
                copy.badgeCount = unreadCount
            return copy
        })
    }
    property var userMenuActions: window.userActionsWithMessageBadge(
        appController.menu_actions("user"), messagesController.unreadCount
    )
    property var configMenuActions: appController.menu_actions("configuration")
    property var temporaryToolsActions:
        appController.menu_actions("temporary_tools")
    property var connectionMenuActions: [
        {"title": "Connection", "header": true},
        {"title": "Ping now", "icon": "sync", "command": "ping_now"},
        {"separator": true},
        {"title": "Automatic connection check", "header": true},
        {"title": "Off", "icon": "visibility_off", "command": "ping_0",
            "checked": appController.ping_interval === 0},
        {"title": "Every 10 seconds", "icon": "schedule", "command": "ping_10",
            "checked": appController.ping_interval === 10},
        {"title": "Every 60 seconds", "icon": "schedule", "command": "ping_60",
            "checked": appController.ping_interval === 60},
        {"separator": true},
        {"title": "Server updates", "header": true},
        {"title": "Messages, reactions, activity and tasks",
            "status": "One batched server request", "icon": "dynamic_feed",
            "enabled": false},
        {"title": "Every 5 seconds", "icon": "schedule", "command": "updates_5",
            "checked": serverUpdateService.poll_interval === 5},
        {"title": "Every 10 seconds", "icon": "schedule", "command": "updates_10",
            "checked": serverUpdateService.poll_interval === 10},
        {"title": "Every 30 seconds", "icon": "schedule", "command": "updates_30",
            "checked": serverUpdateService.poll_interval === 30},
        {"title": "Every 60 seconds", "icon": "schedule", "command": "updates_60",
            "checked": serverUpdateService.poll_interval === 60},
        {"separator": true},
        {"title": "Presence heartbeat", "header": true},
        {"title": "Every 30 seconds", "icon": "system_activity", "command": "heartbeat_30",
            "checked": userController.heartbeat_interval === 30},
        {"title": "Every 60 seconds", "icon": "system_activity", "command": "heartbeat_60",
            "checked": userController.heartbeat_interval === 60},
        {"title": "Every 120 seconds", "icon": "system_activity", "command": "heartbeat_120",
            "checked": userController.heartbeat_interval === 120},
        {"title": "Every 300 seconds", "icon": "system_activity", "command": "heartbeat_300",
            "checked": userController.heartbeat_interval === 300}
    ]
    color: theme.workspace

    Theme {
        id: theme
        dark: window.dark
        styleName: window.themeStyle
        suppressToolTips: drawer.opened
            || projectChooser.opened
            || userMenu.opened
            || configMenu.opened
            || toolsMenu.opened
            || connectionMenu.opened
            || dccClientMenu.opened
    }
    Material.theme: window.dark ? Material.Dark : Material.Light
    Material.accent: theme.action

    FileDialog {
        id: checkinFilesDialog
        title: qsTr("Choose files for check-in")
        fileMode: FileDialog.OpenFiles
        onAccepted: appController.submit_checkin_files(selectedFiles)
    }

    Md3Dialog {
        id: revisionCheckinDialog
        theme: theme
        modal: true
        anchors.centerIn: Overlay.overlay
        width: Math.min(480, window.width - 40)
        title: qsTr("Replace snapshot revision?")
        closePolicy: Popup.NoAutoClose
        contentItem: Label {
            width: revisionCheckinDialog.availableWidth
            text: qsTr("The file stored in this revision will be replaced. ")
                + qsTr("Use Save snapshot when you need a new version.")
            color: theme.secondaryText
            font.family: theme.fontFamily
            font.pixelSize: 11
            wrapMode: Text.WordWrap
        }
        footer: DialogButtonBox {
            background: Item {}
            Md3Button {
                theme: theme
                text: qsTr("Replace revision")
                destructive: true
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            }
            Md3Button {
                theme: theme
                text: qsTr("Cancel")
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            }
            onClicked: function(button) {
                const accepted = buttonRole(button) === DialogButtonBox.AcceptRole
                revisionCheckinDialog.close()
                appController.resolve_revision_checkin(accepted)
            }
        }
    }

    Connections {
        target: appController
        function onCheckinFilesRequested() {
            checkinFilesDialog.open()
        }
        function onRevisionCheckinConfirmationRequested() {
            revisionCheckinDialog.open()
        }
    }
    function changePage(key, title) {
        if (key === pageKey) return
        pendingPageKey = key
        pendingPageTitle = title
        workspaceTransition.restart()
    }
    function showNotice(message) { notificationController.notify(message) }
    function closeTopBarPopups(exceptPopup) {
        if (projectChooser !== exceptPopup && projectChooser.opened) projectChooser.close()
        if (userMenu !== exceptPopup && userMenu.opened) userMenu.close()
        if (configMenu !== exceptPopup && configMenu.opened) configMenu.close()
        if (toolsMenu !== exceptPopup && toolsMenu.opened) toolsMenu.close()
        if (connectionMenu !== exceptPopup && connectionMenu.opened) connectionMenu.close()
        if (dccClientMenu !== exceptPopup && dccClientMenu.opened) dccClientMenu.close()
    }
    function projectAcronym() {
        const words = window.projectTitle.replace(/_/g, " ").split(/\s+/)
        return words.slice(0, 2).map(word => word.length ? word[0] : "").join("").toUpperCase()
    }

    Connections {
        target: appController
        function onDark_theme_changed(enabled) { window.dark = enabled }
        function onPage_changed(key, title) { window.changePage(key, title); drawer.selectedKey = key }
        function onProject_changed(code, title) { window.projectTitle = title }
        function onTemporary_tools_requested() {
            window.closeTopBarPopups(toolsMenu)
            toolsMenu.toggleBelow(settingsButton)
        }
    }
    Connections {
        target: handlerServerController
        function onClientActionReported(message) {
            window.showNotice(message)
        }
    }
    Component.onCompleted: {
        window.dark = appController.is_dark_theme()
    }
    onClosing: function(close) {
        close.accepted = false
        trayController.handle_close(
            handlerServerController.connectedClientCount > 0
        )
    }

    Rectangle {
        id: topAppBar
        anchors.top: parent.top
        width: parent.width
        height: 64
        color: theme.topBar
        Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: theme.separator }
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 8
            anchors.rightMargin: 12
            spacing: 4

            CompactIconButton {
                Layout.preferredWidth: 48
                Layout.preferredHeight: 48
                theme: theme
                iconName: drawer.opened ? "close" : "menu"
                iconColor: theme.primaryText
                round: true
                toolTip: drawer.opened
                    ? qsTr("Close navigation") : qsTr("Open navigation")
                onClicked: {
                    window.closeTopBarPopups(null)
                    drawer.opened ? drawer.close() : drawer.open()
                }
            }

            Item {
                id: projectButton
                Layout.preferredWidth: Math.min(260, Math.max(176, window.width * 0.21))
                Layout.preferredHeight: 44
                Rectangle {
                    id: projectSurface
                    anchors.fill: parent
                    radius: 14
                    color: projectMouse.pressed ? theme.selected
                        : projectMouse.containsMouse ? theme.rowHover : theme.panel
                    border.width: 1
                    border.color: theme.outline
                    Behavior on color { ColorAnimation { duration: 110 } }
                    MaterialRipple {
                        id: projectRipple
                        shapeRadius: projectSurface.radius
                        color: theme.ripple
                    }
                }
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 7
                    anchors.rightMargin: 10
                    spacing: 9
                    ItemPreview {
                        Layout.preferredWidth: 32
                        Layout.preferredHeight: 32
                        theme: theme
                        previewSize: 32
                        cornerRadius: 7
                        outlined: true
                        accent: theme.toolBar
                        source: appController.current_project_preview
                        fallbackText: window.projectAcronym()
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 0
                        Label {
                            text: qsTr("Project")
                            color: theme.secondaryText
                            font.family: theme.fontFamily
                            font.pixelSize: 9
                            font.weight: Font.Medium
                        }
                        Label {
                            text: window.projectTitle
                            color: theme.primaryText
                            font.family: theme.fontFamily
                            font.pixelSize: 13
                            font.weight: Font.DemiBold
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                        }
                    }
                    MaterialIcon { name: "keyboard_arrow_down"; size: 18; color: theme.secondaryText }
                }
                MouseArea {
                    id: projectMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onPressed: mouse => {
                        projectChooser.sourceWasOpen = projectChooser.opened
                        projectRipple.burst(mouse.x, mouse.y)
                    }
                    onClicked: {
                        if (drawer.opened)
                            drawer.close()
                        window.closeTopBarPopups(projectChooser)
                        projectChooser.toggle()
                    }
                }
            }

            Item { Layout.fillWidth: true }

            Item {
                id: notificationActivityButton
                readonly property bool showingProgress:
                    appController.loading
                    && appController.server_state !== "connecting"
                readonly property string progressText:
                    appController.loading_message || "Working"

                Layout.preferredWidth: showingProgress
                    ? Math.min(
                        240,
                        Math.max(136, notificationActivityLabel.implicitWidth + 54)
                    )
                    : 48
                Layout.preferredHeight: 48

                Behavior on Layout.preferredWidth {
                    NumberAnimation {
                        duration: 180
                        easing.type: Easing.OutCubic
                    }
                }

                Rectangle {
                    id: notificationActivitySurface
                    anchors.centerIn: parent
                    width: parent.width - 2
                    height: 40
                    radius: 20
                    color: notificationActivityButton.showingProgress
                        ? theme.panel : "transparent"
                    border.width: notificationActivityButton.showingProgress ? 1 : 0
                    border.color: theme.outlineVariant

                    Rectangle {
                        anchors.fill: parent
                        radius: parent.radius
                        color: theme.primaryText
                        opacity: notificationActivityMouse.pressed ? 0.12
                            : notificationActivityMouse.containsMouse ? 0.08 : 0
                        Behavior on opacity {
                            NumberAnimation {
                                duration: notificationActivityMouse.containsMouse
                                    ? 100 : 140
                                easing.type: Easing.OutCubic
                            }
                        }
                    }

                    MaterialRipple {
                        id: notificationActivityRipple
                        shapeRadius: notificationActivitySurface.radius
                        color: theme.ripple
                    }
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: notificationActivityButton.showingProgress
                        ? 10 : 0
                    anchors.rightMargin: notificationActivityButton.showingProgress
                        ? 12 : 0
                    spacing: 7

                    BusyIndicator {
                        visible: notificationActivityButton.showingProgress
                        running: visible
                        Layout.preferredWidth: 22
                        Layout.preferredHeight: 22
                        palette.highlight: theme.action
                    }
                    Label {
                        id: notificationActivityLabel
                        visible: notificationActivityButton.showingProgress
                        Layout.fillWidth: true
                        text: notificationActivityButton.progressText
                        color: theme.primaryText
                        font.family: theme.fontFamily
                        font.pixelSize: 10
                        font.weight: Font.Medium
                        elide: Text.ElideRight
                        maximumLineCount: 1
                    }
                    MaterialIcon {
                        visible: !notificationActivityButton.showingProgress
                        Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
                        Layout.fillWidth: true
                        name: "system_activity"
                        size: 20
                        color: theme.primaryText
                    }
                }

                MouseArea {
                    id: notificationActivityMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onPressed: mouse => notificationActivityRipple.burst(
                        mouse.x - notificationActivitySurface.x,
                        mouse.y - notificationActivitySurface.y
                    )
                    onClicked: appController.open_window("notifications")

                    Md3ToolTip {
                        theme: theme
                        visible: notificationActivityMouse.containsMouse
                            && !theme.suppressToolTips
                        delay: 450
                        text: notificationActivityButton.showingProgress
                            ? notificationActivityButton.progressText
                            : qsTr("System activity")
                    }
                }
            }

            Item {
                id: connectionButton
                visible: window.width >= 900
                Layout.preferredWidth: 106
                Layout.preferredHeight: 48
                Rectangle {
                    id: connectionSurface
                    anchors.centerIn: parent
                    width: parent.width - 2
                    height: 40
                    radius: 20
                    color: "transparent"
                    Rectangle {
                        anchors.fill: parent
                        radius: parent.radius
                        color: theme.primaryText
                        opacity: connectionMouse.pressed ? 0.12
                            : connectionMouse.containsMouse ? 0.08 : 0
                        Behavior on opacity {
                            NumberAnimation {
                                duration: connectionMouse.containsMouse ? 100 : 140
                                easing.type: Easing.OutCubic
                            }
                        }
                    }
                    MaterialRipple {
                        id: connectionRipple
                        shapeRadius: connectionSurface.radius
                        color: theme.ripple
                    }
                }
                Row {
                    anchors.centerIn: parent
                    spacing: 7
                    Rectangle {
                        anchors.verticalCenter: parent.verticalCenter
                        width: 8
                        height: 8
                        radius: 4
                        color: appController.server_state === "online" ? theme.green
                            : appController.server_state === "error" ? theme.red : theme.yellow
                    }
                    Label {
                        anchors.verticalCenter: parent.verticalCenter
                        text: appController.server_state === "online"
                            ? qsTr("Connected")
                            : appController.server_state === "error"
                                ? qsTr("Offline") : qsTr("Connecting")
                        color: theme.secondaryText
                        font.family: theme.fontFamily
                        font.pixelSize: 10
                        font.weight: Font.Medium
                    }
                }
                MouseArea {
                    id: connectionMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onPressed: mouse => {
                        connectionMenu.sourceWasOpen = connectionMenu.opened
                        connectionRipple.burst(
                            mouse.x - connectionSurface.x,
                            mouse.y - connectionSurface.y
                        )
                    }
                    onClicked: {
                        window.closeTopBarPopups(connectionMenu)
                        connectionMenu.toggleBelow(connectionButton)
                    }
                    Md3ToolTip {
                        theme: theme
                        visible: connectionMouse.containsMouse
                            && !theme.suppressToolTips
                        delay: 450
                        text: appController.server_message
                            + "\n" + appController.server_url
                    }
                }
            }

            Item {
                id: dccClientButton
                readonly property bool expandedLabel: window.width >= 1280
                visible: handlerServerController.selectedClient.length > 0
                Layout.preferredWidth: expandedLabel ? 238 : 104
                Layout.preferredHeight: 48
                Rectangle {
                    id: dccClientSurface
                    anchors.centerIn: parent
                    width: parent.width - 2
                    height: 40
                    radius: 20
                    color: dccClientMouse.pressed ? theme.selected
                        : dccClientMouse.containsMouse
                            ? theme.rowHover : theme.panel
                    border.width: 1
                    border.color: theme.outlineVariant
                    Behavior on color { ColorAnimation { duration: 110 } }
                    MaterialRipple {
                        id: dccClientRipple
                        shapeRadius: dccClientSurface.radius
                        color: theme.ripple
                    }
                }
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 9
                    anchors.rightMargin: 8
                    spacing: 6
                    MaterialIcon {
                        name: "deployed_code"
                        size: 18
                        color: theme.action
                    }
                    ColumnLayout {
                        visible: dccClientButton.expandedLabel
                        Layout.fillWidth: true
                        spacing: 0
                        Label {
                            Layout.fillWidth: true
                            text: qsTr("DCC CLIENTS")
                            color: theme.secondaryText
                            font.family: theme.fontFamily
                            font.pixelSize: 8
                            font.weight: Font.DemiBold
                            elide: Text.ElideRight
                        }
                        Label {
                            Layout.fillWidth: true
                            text: handlerServerController.connectedClientCount
                                + qsTr(" connected")
                            color: theme.primaryText
                            font.family: theme.fontFamily
                            font.pixelSize: 9
                            elide: Text.ElideRight
                        }
                    }
                    Rectangle {
                        Layout.fillWidth: !dccClientButton.expandedLabel
                        Layout.preferredWidth: dccClientButton.expandedLabel
                            ? 105 : 62
                        Layout.preferredHeight: 30
                        radius: 15
                        color: theme.secondaryContainer
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 9
                            anchors.rightMargin: 9
                            spacing: 0
                            Label {
                                visible: dccClientButton.expandedLabel
                                Layout.fillWidth: true
                                text: qsTr("ACTIVE · ")
                                    + handlerServerController
                                        .selectedApplicationType.toUpperCase()
                                color: theme.action
                                font.family: theme.fontFamily
                                font.pixelSize: 7
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }
                            Label {
                                Layout.fillWidth: true
                                text: dccClientButton.expandedLabel
                                    ? handlerServerController.selectedClient
                                    : handlerServerController
                                        .selectedApplicationType.toUpperCase()
                                color: theme.primaryText
                                font.family: theme.fontFamily
                                font.pixelSize: dccClientButton.expandedLabel
                                    ? 8 : 9
                                font.weight: Font.DemiBold
                                horizontalAlignment: dccClientButton.expandedLabel
                                    ? Text.AlignLeft : Text.AlignHCenter
                                elide: Text.ElideRight
                            }
                        }
                    }
                    MaterialIcon {
                        name: "keyboard_arrow_down"
                        size: 14
                        color: theme.secondaryText
                    }
                }
                MouseArea {
                    id: dccClientMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onPressed: mouse => {
                        dccClientMenu.sourceWasOpen = dccClientMenu.opened
                        dccClientRipple.burst(
                            mouse.x - dccClientSurface.x,
                            mouse.y - dccClientSurface.y
                        )
                    }
                    onClicked: {
                        window.closeTopBarPopups(dccClientMenu)
                        dccClientMenu.toggleBelow(dccClientButton)
                    }
                    Md3ToolTip {
                        theme: theme
                        visible: dccClientMouse.containsMouse
                            && !theme.suppressToolTips
                        delay: 450
                        text: handlerServerController.selectedClientLabel
                    }
                }
            }

            CompactIconButton {
                Layout.preferredWidth: 48
                Layout.preferredHeight: 48
                theme: theme
                iconName: "commit_queue"
                iconColor: commitQueueController.unfinishedCount > 0
                    ? theme.action : theme.primaryText
                round: true
                badgeCount: commitQueueController.unfinishedCount
                toolTip: commitQueueController.unfinishedCount > 0
                    ? qsTr("Commit Queue · ")
                        + commitQueueController.unfinishedCount
                        + qsTr(" unfinished")
                    : qsTr("Commit Queue")
                onClicked: appController.open_window("commit_queue")
            }

            CompactIconButton {
                Layout.preferredWidth: 48
                Layout.preferredHeight: 48
                theme: theme
                iconName: "dynamic_feed"
                iconColor: activityFeedController.unreadCount > 0
                    ? theme.action : theme.primaryText
                round: true
                badgeCount: activityFeedController.unreadCount
                toolTip: qsTr("Activity Feed")
                onClicked: appController.open_window("activity_feed")
            }
            CompactIconButton {
                Layout.preferredWidth: 48
                Layout.preferredHeight: 48
                theme: theme
                iconName: window.dark ? "light_mode" : "dark_mode"
                iconColor: theme.primaryText
                round: true
                toolTip: window.dark
                    ? qsTr("Use light theme") : qsTr("Use dark theme")
                onClicked: appController.toggle_theme()
            }
            CompactIconButton {
                id: settingsButton
                Layout.preferredWidth: 48
                Layout.preferredHeight: 48
                theme: theme
                iconName: "more_vert"
                iconColor: theme.primaryText
                round: true
                toolTip: qsTr("More options")
                onPressed: configMenu.sourceWasOpen = configMenu.opened
                onClicked: {
                    if (drawer.opened)
                        drawer.close()
                    window.closeTopBarPopups(configMenu)
                    configMenu.toggleBelow(settingsButton)
                }
            }

            Item {
                id: userButton
                Layout.preferredWidth: 48
                Layout.preferredHeight: 48
                Rectangle {
                    id: userSurface
                    anchors.centerIn: parent
                    width: 40
                    height: 40
                    radius: 20
                    color: userMouse.pressed ? theme.selected
                        : userMouse.containsMouse ? theme.rowHover : theme.panel
                    border.width: 1
                    border.color: userMouse.containsMouse ? theme.action : theme.outline
                    clip: true
                    Behavior on color { ColorAnimation { duration: 110 } }
                    ItemPreview {
                        id: currentUserAvatar
                        anchors.fill: parent
                        anchors.margins: 1
                        theme: theme
                        source: userController.avatarUrl
                        fallbackIcon: "person"
                        fallbackText: userController.initials
                        previewSize: 38
                        round: true
                        cornerRadius: 19
                        accent: theme.action
                    }
                    MaterialRipple {
                        id: userRipple
                        shapeRadius: 20
                        color: theme.rippleStrong
                    }
                }
                Rectangle {
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.rightMargin: -1
                    anchors.topMargin: -1
                    visible: messagesController.unreadCount > 0
                    implicitWidth: Math.max(
                        16, userUnreadLabel.implicitWidth + 7
                    )
                    implicitHeight: 16
                    radius: 8
                    color: theme.error
                    border.width: 2
                    border.color: theme.surface
                    z: 3
                    Label {
                        id: userUnreadLabel
                        anchors.centerIn: parent
                        text: messagesController.unreadCount > 99
                            ? "99+" : String(messagesController.unreadCount)
                        color: theme.selectedText
                        font.family: theme.fontFamily
                        font.pixelSize: 8
                        font.weight: Font.Bold
                    }
                }
                MouseArea {
                    id: userMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onPressed: mouse => {
                        userMenu.sourceWasOpen = userMenu.opened
                        userRipple.burst(
                            mouse.x - userSurface.x,
                            mouse.y - userSurface.y
                        )
                    }
                    onClicked: {
                        if (drawer.opened)
                            drawer.close()
                        window.closeTopBarPopups(userMenu)
                        userMenu.toggleBelow(userButton)
                    }
                    Md3ToolTip {
                        theme: theme
                        visible: userMouse.containsMouse
                            && !theme.suppressToolTips
                        delay: 500
                        text: userController.displayName
                            + (userController.login
                                ? "\n" + userController.login : "")
                    }
                }
            }
        }
    }

    Item {
        id: workspaceLayer
        anchors.top: topAppBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        opacity: 1
        SectionTabRail {
            id: sectionRail
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.bottom: parent.bottom
            theme: theme
            model: sectionTabsModel
            onSelected: key => appController.activate_section(key)
            onClosed: key => appController.close_section(key)
            onReordered: (sourceRow, targetRow) =>
                appController.reorder_section(sourceRow, targetRow)
        }
        DockHost {
            id: workspace
            anchors.top: parent.top
            anchors.left: sectionRail.right
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            theme: theme
            pageTitle: window.pageTitle
            projectTitle: window.projectTitle
            onNotice: function(message) { window.showNotice(message) }
            onRequestDockMenu: sourceItem => dockMenu.toggleBelow(sourceItem)
        }
        // In the source Ui_checkInOutTabWidget the overlay belongs to the
        // project workspace, below Ui_topBarWidget rather than over it.
        NavigationDrawer {
            id: drawer
            model: navigationModel
            theme: theme
            onSelected: (key, title, command) => {
                appController.select_navigation(key, title, command)
                drawer.close()
            }
        }
    }
    SequentialAnimation {
        id: workspaceTransition
        NumberAnimation { target: workspaceLayer; property: "opacity"; to: 0; duration: 70 }
        ScriptAction { script: { window.pageKey = window.pendingPageKey; window.pageTitle = window.pendingPageTitle } }
        NumberAnimation { target: workspaceLayer; property: "opacity"; to: 1; duration: 130; easing.type: Easing.OutCubic }
    }

    ProjectChooser {
        id: projectChooser; model: projectModel; theme: theme
        onProjectSelected: code => appController.select_project(code)
    }
    DockMenu {
        id: dockMenu
        parent: Overlay.overlay
        theme: theme
        panelModel: dockModel
        x: Math.max(8, window.width - width - 58)
        y: topAppBar.height - 2
    }
    ActionMenu {
        id: userMenu
        parent: Overlay.overlay
        theme: theme
        actions: window.userMenuActions
        onTriggered: command => appController.invoke(command)
    }
    ActionMenu {
        id: configMenu
        parent: Overlay.overlay
        theme: theme
        actions: window.configMenuActions
        onTriggered: command => appController.invoke(command)
    }
    ActionMenu {
        id: toolsMenu
        parent: Overlay.overlay
        theme: theme
        preferredWidth: 340
        actions: window.temporaryToolsActions
        onTriggered: command => appController.invoke(command)
    }
    ActionMenu {
        id: connectionMenu
        parent: Overlay.overlay
        theme: theme
        preferredWidth: 330
        actions: window.connectionMenuActions
        onTriggered: command => {
            if (command === "ping_now")
                appController.ping_server()
            else if (command.indexOf("ping_") === 0)
                appController.set_ping_interval(Number(command.slice(5)))
            else if (command.indexOf("updates_") === 0)
                serverUpdateService.set_poll_interval(
                    Number(command.slice(8))
                )
            else if (command.indexOf("heartbeat_") === 0)
                userController.set_heartbeat_interval(
                    Number(command.slice(10))
                )
        }
    }
    ActionMenu {
        id: dccClientMenu
        parent: Overlay.overlay
        theme: theme
        preferredWidth: 290
        actions: handlerServerController.clientMenuActions
        onTriggered: command => {
            if (command.indexOf("dcc_client:") === 0)
                handlerServerController.select_client_id(command.slice(11))
        }
    }
    Item {
        id: startupLoadingOverlay
        anchors.fill: parent
        anchors.topMargin: topAppBar.height
        z: 900
        visible: opacity > 0
        opacity: appController.server_state === "connecting" ? 1 : 0

        Behavior on opacity {
            NumberAnimation {
                duration: 200
                easing.type: appController.server_state === "connecting"
                    ? Easing.InSine : Easing.OutSine
            }
        }

        Rectangle {
            anchors.fill: parent
            color: theme.workspace
            opacity: theme.dark ? 0.92 : 0.88
        }

        ColumnLayout {
            anchors.centerIn: parent
            spacing: 14

            Item {
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: 80
                Layout.preferredHeight: 80

                Rectangle {
                    anchors.fill: parent
                    radius: width / 2
                    color: theme.panelRaised
                    border.width: 1
                    border.color: theme.outline
                }
                BusyIndicator {
                    anchors.centerIn: parent
                    width: 56
                    height: 56
                    running: startupLoadingOverlay.opacity > 0
                    palette.highlight: theme.action
                }
            }

            Label {
                Layout.alignment: Qt.AlignHCenter
                text: qsTr("Loading TACTIC-Handler")
                color: theme.primaryText
                font.family: theme.fontFamily
                font.pixelSize: 15
                font.weight: Font.DemiBold
            }
            Label {
                Layout.alignment: Qt.AlignHCenter
                text: appController.loading_message
                color: theme.secondaryText
                font.family: theme.fontFamily
                font.pixelSize: 11
            }
        }

        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.AllButtons
        }
    }

    Rectangle {
        id: accessGate
        anchors.fill: parent
        z: 950
        visible: appController.server_state !== "connecting"
            && !window.workspaceAccessible
        color: theme.workspace

        ColumnLayout {
            anchors.centerIn: parent
            width: Math.min(560, parent.width - 48)
            spacing: 14

            Rectangle {
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: 64
                Layout.preferredHeight: 64
                radius: 22
                color: theme.surfaceContainerHighest

                MaterialIcon {
                    anchors.centerIn: parent
                    name: window.serverConfigured ? "key" : "settings"
                    size: 28
                    color: theme.action
                }
            }
            Label {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                text: !window.serverConfigured
                    ? qsTr("Configure TACTIC server")
                    : !appController.has_ticket
                        || appController.authentication_required
                        ? qsTr("Sign in to TACTIC")
                        : qsTr("TACTIC is unavailable")
                color: theme.primaryText
                font.family: theme.fontFamily
                font.pixelSize: 20
                font.weight: Font.DemiBold
            }
            Label {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                text: !window.serverConfigured
                    ? qsTr("Set a server address and account before opening the workspace.")
                    : appController.server_message
                        || qsTr("Generate a ticket to open the workspace.")
                color: theme.secondaryText
                font.family: theme.fontFamily
                font.pixelSize: 11
                wrapMode: Text.WordWrap
            }
            ColumnLayout {
                Layout.fillWidth: true
                Layout.topMargin: 8
                spacing: 6

                Label {
                    text: qsTr("TACTIC server preset")
                    color: theme.secondaryText
                    font.family: theme.fontFamily
                    font.pixelSize: 9
                    font.weight: Font.DemiBold
                }
                Md3ComboBox {
                    id: gateServerPreset
                    Layout.fillWidth: true
                    Layout.preferredHeight: 42
                    theme: theme
                    model: serverPresetModel
                    textRole: "label"
                    currentIndex: {
                        const current = appController.server_preset
                        for (let row = 0; row < serverPresetModel.count(); ++row) {
                            if (serverPresetModel.get(row).label === current)
                                return row
                        }
                        return serverPresetModel.count() ? 0 : -1
                    }
                    onActivated: {
                        const presetName = currentText
                        if (!presetName.length
                                || presetName === appController.server_preset)
                            return
                        appController.select_server_preset(presetName)
                    }
                }
            }
            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 8
                spacing: 8

                Md3Button {
                    theme: theme
                    text: qsTr("Configuration")
                    icon.name: "settings"
                    onClicked: windowModel.show_window("configuration")
                }
                Md3Button {
                    theme: theme
                    visible: window.serverConfigured
                    text: qsTr("Sign in")
                    icon.name: "key"
                    highlighted: !appController.has_ticket
                        || appController.authentication_required
                    onClicked: appController.request_authentication()
                }
                Md3Button {
                    theme: theme
                    visible: window.serverConfigured
                        && appController.has_ticket
                        && !appController.authentication_required
                    text: qsTr("Retry")
                    icon.name: "refresh"
                    highlighted: true
                    onClicked: appController.bootstrap_server()
                }
            }
        }

        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.AllButtons
            z: -1
        }
    }

    WindowHost {
        theme: theme
        workspaceEnabled: window.workspaceAccessible || qmlSmokeMode
    }
    ErrorDialog {
        ownerWindow: window
        theme: theme
    }
    LoginDialog {
        ownerWindow: window
        theme: theme
    }
    NotificationStack {
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.rightMargin: 18
        anchors.bottomMargin: 18
        width: Math.min(390, window.width - 36)
        theme: theme
        z: 1200
    }
}

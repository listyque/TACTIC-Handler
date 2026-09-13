import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Layouts
import QtQuick.Window
import "controls" as Controls

ApplicationWindow {
    id: window
    readonly property string applicationThemeStyleName: theme.styleName
    readonly property color applicationThemeAccentColor: theme.accentColor
    readonly property color applicationThemeBaseColor: theme.baseColor
    x: appController.window_x
    y: appController.window_y
    width: appController.window_width
    height: appController.window_height
    minimumWidth: Math.max(
        sizing.windowMinimumWidth("main"),
        dockModel.minimumHostWidth + sectionRail.width
    )
    minimumHeight: Math.max(
        sizing.windowMinimumHeight("main"),
        dockModel.minimumHostHeight + topAppBar.height
    )
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

    function syncNativeFrame() {
        windowAppearanceController.apply(
            window,
            window.dark,
            theme.topBar,
            theme.primaryText
        )
    }

    function syncErrorWindow() {
        if (debugLog.error_visible)
            windowModel.show_window("error")
        else
            windowModel.close_window("error")
    }

    function clampToAvailableScreen() {
        const safe = appController.clamp_main_window_geometry(
            window.x, window.y, window.width, window.height
        )
        if (!safe)
            return
        window.width = safe.width
        window.height = safe.height
        window.x = safe.x
        window.y = safe.y
    }

    property bool windowStateReady: false
    Timer {
        id: windowStateSaveTimer
        interval: 400
        repeat: false
        onTriggered: {
            if (window.windowStateReady
                    && window.visibility === Window.Windowed)
                window.saveWindowState()
        }
    }
    function scheduleWindowStateSave() {
        if (windowStateReady && visibility === Window.Windowed)
            windowStateSaveTimer.restart()
    }
    onXChanged: scheduleWindowStateSave()
    onYChanged: scheduleWindowStateSave()
    onWidthChanged: scheduleWindowStateSave()
    onHeightChanged: scheduleWindowStateSave()
    onVisibilityChanged: function(visibility) {
        windowStateSaveTimer.stop()
        if (visibility !== Window.Hidden)
            Qt.callLater(window.syncNativeFrame)
        if (windowStateReady && visibility === Window.Maximized)
            saveWindowState()
        else
            scheduleWindowStateSave()
    }

    property bool dark: true
    property string themeStyle: appController.theme_style
    onDarkChanged: Qt.callLater(window.syncNativeFrame)
    onThemeStyleChanged: Qt.callLater(window.syncNativeFrame)
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
    property var toolsActions: appController.menu_actions("tools")
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

    WindowSizing { id: sizing }

    Theme {
        id: theme
        dark: window.dark
        styleName: window.themeStyle
        accentColor: appController.accent_color
        baseColor: appController.base_color
        clickAnimationsEnabled: appController.click_animations_enabled
        hoverAnimationsEnabled: appController.hover_animations_enabled
        fadeAnimationsEnabled: appController.fade_animations_enabled
        popupAnimationsEnabled: appController.popup_animations_enabled
        onTopBarChanged: Qt.callLater(window.syncNativeFrame)
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

    ItemCheckinDialogs {
        anchors.fill: parent
        theme: theme
        applicationController: appController
    }

    WatchFolderDeleteDialog {
        theme: theme
        acceptedOrigin: "item"
    }
    RepositorySetupPrompt {
        anchors.fill: parent
        theme: theme
        applicationController: appController
        configurationController: configurationController
        repositoryController: repositoryEditorController
        windows: windowModel
        smokeMode: qmlSmokeMode
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
        function onServer_state_changed() {
            window.configMenuActions = appController.menu_actions("configuration")
        }
        function onPage_changed(key, title) { window.changePage(key, title); drawer.selectedKey = key }
        function onProject_changed(code, title) { window.projectTitle = title }
        function onTools_requested() {
            window.toolsActions = appController.menu_actions("tools")
            window.closeTopBarPopups(toolsMenu)
            toolsMenu.toggleBelow(settingsButton)
        }
    }
    Connections {
        target: handlerServerController
        function onClientActionReported(kind, message, detail) {
            notificationController.push(kind, message, detail)
        }
    }
    Connections {
        target: debugLog
        function onError_changed() {
            window.syncErrorWindow()
        }
    }
    Component.onCompleted: {
        window.dark = appController.is_dark_theme()
        window.syncErrorWindow()
        Qt.callLater(window.syncNativeFrame)
        Qt.callLater(function() {
            if (!qmlSmokeMode && window.visibility === Window.Windowed)
                window.clampToAvailableScreen()
            window.windowStateReady = true
        })
    }
    onClosing: function(close) {
        windowStateSaveTimer.stop()
        if (windowStateReady)
            saveWindowState()
        close.accepted = trayController.handle_close()
    }

    Rectangle {
        id: topAppBar
        anchors.top: parent.top
        width: parent.width
        height: 44
        color: "transparent"
        clip: false
        z: 100

        readonly property real controlExtent: 36
        readonly property real controlSurfaceExtent: 32
        readonly property real projectExtent: 36
        readonly property real projectPreviewExtent: 28

        Rectangle {
            id: topAppBarSurface
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            height: topAppBar.height
            color: theme.topBar
            border.width: 0
            border.color: theme.outlineVariant

            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: 1
                color: theme.separator
            }

        }
        RowLayout {
            id: topAppBarContent
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            height: topAppBar.height
            anchors.leftMargin: 8
            anchors.rightMargin: 12
            spacing: 2


            Controls.CompactIconButton {
                Layout.preferredWidth: topAppBar.controlExtent
                Layout.preferredHeight: topAppBar.controlExtent
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
                readonly property bool lastActivationWasTouch:
                    projectActivation.lastActivationWasTouch
                readonly property double lastActivationAt:
                    projectActivation.lastActivationAt
                Layout.preferredWidth: Math.min(
                    260,
                    Math.max(window.width < 640 ? 132 : 176,
                        window.width * 0.21)
                )
                Layout.preferredHeight: topAppBar.projectExtent
                Rectangle {
                    id: projectSurface
                    anchors.fill: parent
                    radius: 12
                    color: projectActivation.pressed ? theme.selected
                        : projectHover.hovered ? theme.rowHover : theme.panel
                    border.width: 1
                    border.color: theme.outline
                    Behavior on color { ColorAnimation { duration: theme.hoverMotionFast } }
                    Controls.MaterialRipple {
                        id: projectRipple
                        theme: theme
                        shapeRadius: projectSurface.radius
                        color: theme.ripple
                    }
                }
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 7
                    anchors.rightMargin: 10
                    spacing: 9
                    Controls.ItemPreview {
                        Layout.preferredWidth: topAppBar.projectPreviewExtent
                        Layout.preferredHeight: topAppBar.projectPreviewExtent
                        theme: theme
                        previewSize: topAppBar.projectPreviewExtent
                        cornerRadius: 6
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
                            font.pointSize: Controls.Typography.label
                            font.weight: Font.Medium
                            visible: false
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
                    Controls.MaterialIcon { name: "keyboard_arrow_down"; size: 18; color: theme.secondaryText }
                }
                Controls.ActivationHandler {
                    id: projectActivation
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onPressedChanged: {
                        if (!pressed)
                            return
                        projectChooser.sourceWasOpen = projectChooser.opened
                        projectRipple.burst(
                            point.position.x, point.position.y)
                    }
                    onActivated: {
                        if (drawer.opened)
                            drawer.close()
                        window.closeTopBarPopups(projectChooser)
                        projectChooser.toggle(projectButton)
                    }
                }
                HoverHandler {
                    id: projectHover
                    cursorShape: Qt.PointingHandCursor
                }
            }

            Item { Layout.fillWidth: true }

            Item {
                id: notificationActivityButton
                readonly property bool showingProgress:
                    appController.loading
                    || appController.server_state === "connecting"
                readonly property string progressText:
                    qsTr(appController.loading_message
                        || appController.server_message
                        || "Loading TACTIC workspace")
                readonly property bool compactProgress: window.width < 760
                readonly property real progressExtent: compactProgress
                    ? topAppBar.controlExtent : 220
                property real progressReveal: showingProgress ? 1.0 : 0.0

                clip: true
                Layout.preferredWidth: topAppBar.controlExtent
                    + (progressExtent - topAppBar.controlExtent) * progressReveal
                Layout.preferredHeight: topAppBar.controlExtent

                Behavior on progressReveal {
                    NumberAnimation {
                        duration: theme.motionMedium
                        easing.type: Easing.OutCubic
                    }
                }

                Rectangle {
                    id: notificationActivitySurface
                    anchors.centerIn: parent
                    width: parent.width - 2
                    height: topAppBar.controlSurfaceExtent
                    radius: height / 2
                    color: "transparent"
                    border.width: 1
                    border.color: Qt.rgba(
                        theme.outlineVariant.r,
                        theme.outlineVariant.g,
                        theme.outlineVariant.b,
                        theme.outlineVariant.a
                            * notificationActivityButton.progressReveal
                    )

                    Rectangle {
                        anchors.fill: parent
                        radius: parent.radius
                        color: theme.panel
                        opacity: notificationActivityButton.progressReveal
                    }
                    Rectangle {
                        anchors.fill: parent
                        radius: parent.radius
                        color: theme.primaryText
                        opacity: notificationActivityMouse.pressed ? 0.12
                            : notificationActivityMouse.containsMouse ? 0.08 : 0
                        Behavior on opacity {
                            NumberAnimation {
                                duration: notificationActivityMouse.pressed
                                    ? theme.clickMotionFast
                                    : theme.hoverMotionFast
                                easing.type: Easing.OutCubic
                            }
                        }
                    }

                    Controls.MaterialRipple {
                        id: notificationActivityRipple
                        theme: theme
                        shapeRadius: notificationActivitySurface.radius
                        color: theme.ripple
                    }
                }

                Controls.MaterialIcon {
                    anchors.centerIn: parent
                    name: "system_activity"
                    size: 20
                    color: theme.primaryText
                    opacity: 1.0 - notificationActivityButton.progressReveal
                    visible: opacity > 0.01
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin:
                        notificationActivityButton.compactProgress ? 7 : 10
                    anchors.rightMargin:
                        notificationActivityButton.compactProgress ? 7 : 12
                    spacing: 7
                    opacity: notificationActivityButton.progressReveal
                    visible: opacity > 0.01

                    Controls.BusyIndicator {
                        uiTheme: theme
                        running: notificationActivityButton.showingProgress
                        Layout.preferredWidth: 22
                        Layout.preferredHeight: 22
                    }
                    Label {
                        id: notificationActivityLabel
                        visible: !notificationActivityButton.compactProgress
                        Layout.fillWidth: true
                        text: notificationActivityButton.progressText
                        color: theme.primaryText
                        font.family: theme.fontFamily
                        font.pointSize: Controls.Typography.body
                        font.weight: Font.Medium
                        elide: Text.ElideRight
                        maximumLineCount: 1
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

                    Controls.ToolTip {
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
                readonly property bool lastActivationWasTouch:
                    connectionActivation.lastActivationWasTouch
                readonly property double lastActivationAt:
                    connectionActivation.lastActivationAt
                readonly property bool expandedLabel: window.width >= 900
                readonly property color statusColor:
                    appController.server_state === "online" ? theme.green
                    : appController.server_state === "error"
                        ? theme.red : theme.yellow
                Layout.preferredWidth: expandedLabel
                    ? 106 : topAppBar.controlExtent
                Layout.preferredHeight: topAppBar.controlExtent
                Rectangle {
                    id: connectionSurface
                    anchors.centerIn: parent
                    width: parent.width - 2
                    height: topAppBar.controlSurfaceExtent
                    radius: height / 2
                    color: "transparent"
                    Rectangle {
                        anchors.fill: parent
                        radius: parent.radius
                        color: theme.primaryText
                        opacity: connectionActivation.pressed ? 0.12
                            : connectionHover.hovered ? 0.08 : 0
                        Behavior on opacity {
                            NumberAnimation {
                                duration: connectionActivation.pressed
                                    ? theme.clickMotionFast
                                    : connectionHover.hovered
                                        ? theme.hoverMotionFast
                                        : theme.hoverMotionMedium
                                easing.type: Easing.OutCubic
                            }
                        }
                    }
                    Controls.MaterialRipple {
                        id: connectionRipple
                        theme: theme
                        shapeRadius: connectionSurface.radius
                        color: theme.ripple
                    }
                }
                Row {
                    anchors.centerIn: parent
                    spacing: 7
                    Controls.MaterialIcon {
                        visible: !connectionButton.expandedLabel
                        anchors.verticalCenter: parent.verticalCenter
                        name: "online"
                        size: 18
                        color: connectionButton.statusColor
                    }
                    Rectangle {
                        visible: connectionButton.expandedLabel
                        anchors.verticalCenter: parent.verticalCenter
                        width: 8
                        height: 8
                        radius: 4
                        color: connectionButton.statusColor
                    }
                    Label {
                        visible: connectionButton.expandedLabel
                        anchors.verticalCenter: parent.verticalCenter
                        text: appController.server_state === "online"
                            ? qsTr("Connected")
                            : appController.server_state === "error"
                                ? qsTr("Offline") : qsTr("Connecting")
                        color: theme.secondaryText
                        font.family: theme.fontFamily
                        font.pointSize: Controls.Typography.body
                        font.weight: Font.Medium
                    }
                }
                Controls.ActivationHandler {
                    id: connectionActivation
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onPressedChanged: {
                        if (!pressed)
                            return
                        connectionMenu.sourceWasOpen = connectionMenu.opened
                        connectionRipple.burst(
                            point.position.x - connectionSurface.x,
                            point.position.y - connectionSurface.y
                        )
                    }
                    onActivated: {
                        window.closeTopBarPopups(connectionMenu)
                        connectionMenu.toggleBelow(connectionButton)
                    }
                }
                HoverHandler {
                    id: connectionHover
                    cursorShape: Qt.PointingHandCursor
                }
                Controls.ToolTip {
                    theme: theme
                    visible: connectionHover.hovered
                        && !theme.suppressToolTips
                    delay: 450
                    text: qsTr(appController.server_message)
                        + "\n" + appController.server_url
                }
            }

            Item {
                id: dccClientButton
                readonly property bool lastActivationWasTouch:
                    dccClientActivation.lastActivationWasTouch
                readonly property double lastActivationAt:
                    dccClientActivation.lastActivationAt
                readonly property bool expandedLabel: window.width >= 1280
                readonly property bool compactIconOnly: window.width < 720
                visible: handlerServerController.selectedClient.length > 0
                Layout.preferredWidth: expandedLabel ? 238
                    : compactIconOnly ? topAppBar.controlExtent : 104
                Layout.preferredHeight: topAppBar.controlExtent
                clip: true
                Rectangle {
                    id: dccClientSurface
                    anchors.centerIn: parent
                    width: parent.width - 2
                    height: topAppBar.controlSurfaceExtent
                    radius: height / 2
                    color: dccClientActivation.pressed ? theme.selected
                        : dccClientHover.hovered
                            ? theme.rowHover : theme.panel
                    border.width: 1
                    border.color: theme.outlineVariant
                    Behavior on color { ColorAnimation { duration: theme.hoverMotionFast } }
                    Controls.MaterialRipple {
                        id: dccClientRipple
                        theme: theme
                        shapeRadius: dccClientSurface.radius
                        color: theme.ripple
                    }
                }
                Controls.MaterialIcon {
                    anchors.centerIn: parent
                    visible: dccClientButton.compactIconOnly
                    name: "deployed_code"
                    size: 18
                    color: theme.action
                }
                RowLayout {
                    visible: !dccClientButton.compactIconOnly
                    anchors.fill: parent
                    anchors.leftMargin: 9
                    anchors.rightMargin: 8
                    spacing: 6
                    Controls.MaterialIcon {
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
                            font.pointSize: Controls.Typography.caption
                            font.weight: Font.DemiBold
                            elide: Text.ElideRight
                        }
                        Label {
                            Layout.fillWidth: true
                            text: handlerServerController.connectedClientCount
                                + qsTr(" connected")
                            color: theme.primaryText
                            font.family: theme.fontFamily
                            font.pointSize: Controls.Typography.label
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
                                font.pointSize: Controls.Typography.micro
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
                    Controls.MaterialIcon {
                        name: "keyboard_arrow_down"
                        size: 14
                        color: theme.secondaryText
                    }
                }
                Controls.ActivationHandler {
                    id: dccClientActivation
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onPressedChanged: {
                        if (!pressed)
                            return
                        dccClientMenu.sourceWasOpen = dccClientMenu.opened
                        dccClientRipple.burst(
                            point.position.x - dccClientSurface.x,
                            point.position.y - dccClientSurface.y
                        )
                    }
                    onActivated: {
                        window.closeTopBarPopups(dccClientMenu)
                        dccClientMenu.toggleBelow(dccClientButton)
                    }
                }
                HoverHandler {
                    id: dccClientHover
                    cursorShape: Qt.PointingHandCursor
                }
                Controls.ToolTip {
                    theme: theme
                    visible: dccClientHover.hovered
                        && !theme.suppressToolTips
                    delay: 450
                    text: handlerServerController.selectedClientLabel
                }
            }

            Controls.CompactIconButton {
                Layout.preferredWidth: topAppBar.controlExtent
                Layout.preferredHeight: topAppBar.controlExtent
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

            Controls.CompactIconButton {
                Layout.preferredWidth: topAppBar.controlExtent
                Layout.preferredHeight: topAppBar.controlExtent
                theme: theme
                iconName: "dynamic_feed"
                iconColor: activityFeedController.unreadCount > 0
                    ? theme.action : theme.primaryText
                round: true
                badgeCount: activityFeedController.unreadCount
                toolTip: qsTr("Activity Feed")
                onClicked: appController.open_window("activity_feed")
            }
            Controls.CompactIconButton {
                Layout.preferredWidth: topAppBar.controlExtent
                Layout.preferredHeight: topAppBar.controlExtent
                theme: theme
                iconName: "theme_mode"
                iconColor: theme.primaryText
                round: true
                toolTip: window.dark
                    ? qsTr("Use light theme") : qsTr("Use dark theme")
                onClicked: appController.toggle_theme()
            }
            Controls.CompactIconButton {
                id: settingsButton
                Layout.preferredWidth: topAppBar.controlExtent
                Layout.preferredHeight: topAppBar.controlExtent
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
                objectName: "topBarUserButton"
                readonly property bool lastActivationWasTouch:
                    userActivation.lastActivationWasTouch
                readonly property double lastActivationAt:
                    userActivation.lastActivationAt
                Layout.preferredWidth: topAppBar.controlExtent
                Layout.preferredHeight: topAppBar.controlExtent
                Rectangle {
                    id: userSurface
                    anchors.centerIn: parent
                    width: topAppBar.controlSurfaceExtent
                    height: topAppBar.controlSurfaceExtent
                    radius: width / 2
                    color: userActivation.pressed ? theme.selected
                        : userHover.hovered ? theme.rowHover : theme.panel
                    border.width: 1
                    border.color: userHover.hovered
                        ? theme.action : theme.outline
                    clip: true
                    Behavior on color { ColorAnimation { duration: theme.hoverMotionFast } }
                    Controls.ItemPreview {
                        id: currentUserAvatar
                        anchors.fill: parent
                        anchors.margins: 1
                        theme: theme
                        source: userController.avatarUrl
                        fallbackIcon: "person"
                        fallbackText: userController.initials
                        previewSize: topAppBar.controlSurfaceExtent - 2
                        round: true
                        cornerRadius: previewSize / 2
                        accent: userController.avatarColor
                    }
                    Controls.MaterialRipple {
                        id: userRipple
                        theme: theme
                        shapeRadius: userSurface.radius
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
                        font.pointSize: Controls.Typography.caption
                        font.weight: Font.Bold
                    }
                }
                Controls.ActivationHandler {
                    id: userActivation
                    objectName: "topBarUserActivation"
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onPressedChanged: {
                        if (!pressed)
                            return
                        userMenu.sourceWasOpen = userMenu.opened
                        userRipple.burst(
                            point.position.x - userSurface.x,
                            point.position.y - userSurface.y
                        )
                    }
                    onActivated: {
                        if (drawer.opened)
                            drawer.close()
                        window.closeTopBarPopups(userMenu)
                        userMenu.toggleBelow(userButton)
                    }
                }
                HoverHandler {
                    id: userHover
                    cursorShape: Qt.PointingHandCursor
                }
                Controls.ToolTip {
                    theme: theme
                    visible: userHover.hovered
                        && !theme.suppressToolTips
                    delay: 500
                    text: userController.displayName
                        + (userController.login
                            ? "\n" + userController.login : "")
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
            anchors.left: parent.left; anchors.leftMargin: sectionRail.reservedWidth
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
            sidebarEditingAvailable: userController.canManageUsers
            onEditSidebarRequested: appController.invoke("show_sidebar_editor")
            onSelected: (key, title, command) => {
                appController.select_navigation(key, title, command)
                drawer.close()
            }
        }
    }
    SequentialAnimation {
        id: workspaceTransition
        NumberAnimation { target: workspaceLayer; property: "opacity"; to: 0; duration: theme.motionInstant }
        ScriptAction { script: { window.pageKey = window.pendingPageKey; window.pageTitle = window.pendingPageTitle } }
        NumberAnimation { target: workspaceLayer; property: "opacity"; to: 1; duration: theme.motionFast; easing.type: Easing.OutCubic }
    }

    ProjectChooser {
        id: projectChooser; model: projectModel; theme: theme
        onProjectSelected: code => appController.select_project(code)
    }
    DockMenu {
        id: dockMenu
        parent: Overlay.overlay
        theme: theme
        panelModel: dockModel; layoutPresetController: workspaceLayoutPresets
        onResetLayoutRequested:
            appController.invoke("reset_workspace_layout")
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
        actions: window.toolsActions
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
        onOpened: handlerServerController.refresh_client_details()
        onTriggered: command => {
            if (command.indexOf("dcc_client:") === 0)
                handlerServerController.select_client_id(command.slice(11))
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

                Controls.MaterialIcon {
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
                    : qsTr(appController.server_message)
                        || qsTr("Generate a ticket to open the workspace.")
                color: theme.secondaryText
                font.family: theme.fontFamily
                font.pointSize: Controls.Typography.bodyLarge
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
                    font.pointSize: Controls.Typography.label
                    font.weight: Font.DemiBold
                }
                Controls.ComboBox {
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

                Controls.Button {
                    theme: theme
                    text: qsTr("Configuration")
                    icon.name: "settings"
                    onClicked: windowModel.show_window("configuration")
                }
                Controls.Button {
                    theme: theme
                    visible: window.serverConfigured
                    text: qsTr("Sign in")
                    icon.name: "key"
                    highlighted: !appController.has_ticket
                        || appController.authentication_required
                    onClicked: appController.request_authentication()
                }
                Controls.Button {
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
    LoginDialog {
        ownerWindow: window
        theme: theme
    }
    NotificationToastWindow {
        id: notificationToastWindow
        theme: theme
        controller: notificationController
        notifications: notificationModel
        screen: window.screen
    }
}

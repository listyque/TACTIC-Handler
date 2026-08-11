import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: page

    required property var theme
    required property string pageId
    property bool managed: false

    Loader {
        anchors.fill: parent
        sourceComponent: page.pageId === "server" ? serverForm
            : page.pageId === "project" ? projectForm
            : page.pageId === "checkin_preferences" ? checkinOptionsPageForm
            : page.pageId === "checkinout_preferences"
                ? checkinOutOptionsPageForm
            : page.pageId === "global_preferences" ? globalPreferencesForm
            : page.pageId === "tasks_preferences" ? taskPreferencesForm
            : page.pageId === "maya_preferences" ? mayaPreferencesForm
            : null
    }

    Component {
        id: checkinOptionsPageForm
        CheckinOptionsPage { theme: page.theme; managed: page.managed }
    }

    Component {
        id: checkinOutOptionsPageForm
        CheckinOutOptionsPage { theme: page.theme; managed: page.managed }
    }

    Component {
        id: serverForm

        Item {
            id: serverPanel
            property bool loadingValues: true
            property bool hasProxyPassword: false
            readonly property var pingSeconds: [0, 10, 60]
            readonly property var updateSeconds: [5, 10, 30, 60]
            readonly property var heartbeatSeconds: [30, 60, 120, 300]

            function intervalIndex(options, value, fallback) {
                const index = options.indexOf(Number(value))
                return index >= 0 ? index : fallback
            }

            function formValues() {
                return {
                    "serverUrl": serverAddress.text,
                    "presetName": serverPreset.currentText,
                    "userName": userName.text,
                    "siteEnabled": siteEnabled.checked,
                    "siteName": siteName.text,
                    "proxyEnabled": proxyEnabled.checked,
                    "proxyLogin": proxyLogin.text,
                    "proxyServer": proxyServer.text,
                    "proxyPassword": proxyPassword.text,
                    "hasProxyPassword": hasProxyPassword,
                    "pingInterval": pingSeconds[pingInterval.currentIndex],
                    "serverUpdateInterval": updateSeconds[
                        serverUpdateInterval.currentIndex
                    ],
                    "presenceHeartbeatInterval": heartbeatSeconds[
                        heartbeatInterval.currentIndex
                    ]
                }
            }

            function loadValues(values) {
                loadingValues = true
                serverAddress.text = values.serverUrl || ""
                userName.text = values.userName || ""
                siteEnabled.checked = Boolean(values.siteEnabled)
                siteName.text = values.siteName || ""
                proxyEnabled.checked = Boolean(values.proxyEnabled)
                proxyLogin.text = values.proxyLogin || ""
                proxyServer.text = values.proxyServer || ""
                proxyPassword.clear()
                hasProxyPassword = Boolean(values.hasProxyPassword)
                pingInterval.currentIndex = intervalIndex(
                    pingSeconds, values.pingInterval, 0
                )
                serverUpdateInterval.currentIndex = intervalIndex(
                    updateSeconds, values.serverUpdateInterval, 2
                )
                heartbeatInterval.currentIndex = intervalIndex(
                    heartbeatSeconds, values.presenceHeartbeatInterval, 2
                )
                for (let row = 0; row < serverPresetModel.count(); ++row) {
                    if (serverPresetModel.get(row).label
                            === values.presetName) {
                        serverPreset.currentIndex = row
                        break
                    }
                }
                loadingValues = false
            }

            function syncValues() {
                loadValues(configurationController.page_values("server"))
            }

            function updateValues() {
                if (!page.managed || loadingValues)
                    return
                configurationController.update_page(
                    "server", formValues()
                )
            }

            function selectPreset() {
                if (loadingValues)
                    return
                loadValues(configurationController.server_preset_values(
                    serverPreset.currentText
                ))
                updateValues()
            }

            Component.onCompleted: syncValues()

            Connections {
                target: configurationController

                function onSessionStarted() {
                    serverPanel.syncValues()
                }

                function onPageReset(pageId) {
                    if (pageId === "server")
                        serverPanel.syncValues()
                }
            }

            ScrollView {
                id: serverScroll
                anchors.fill: parent
                contentWidth: availableWidth
                contentHeight: serverContent.implicitHeight + 40
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                ScrollBar.vertical: Md3ScrollBar {
                    theme: page.theme
                    flickableTarget: serverScroll
                }

                ColumnLayout {
                    id: serverContent
                    x: 22
                    y: 20
                    width: Math.max(0, serverScroll.availableWidth - 44)
                    spacing: 14

                    ConfigurationSection {
                        Layout.fillWidth: true
                        theme: page.theme
                        title: qsTr("Connection")
                        description: qsTr("Server endpoint and the active connection preset.")
                        iconName: "cloud"

                        GridLayout {
                            Layout.fillWidth: true
                            columns: 2
                            columnSpacing: 14
                            rowSpacing: 8

                            Label {
                                text: qsTr("Server address")
                                color: page.theme.secondaryText
                                font.pixelSize: 10
                            }
                            Md3TextField {
                                theme: page.theme
                                id: serverAddress
                                Layout.fillWidth: true
                                Layout.preferredHeight: 42
                                placeholderText: qsTr("http://server")
                                color: page.theme.primaryText
                                placeholderTextColor: page.theme.disabledText
                                selectByMouse: true
                                leftPadding: 13
                                rightPadding: 13
                                onTextEdited: serverPanel.updateValues()
                                background: Rectangle {
                                    radius: 11
                                    color: page.theme.surfaceContainerHigh
                                    border.width: serverAddress.activeFocus ? 2 : 1
                                    border.color: serverAddress.activeFocus
                                        ? page.theme.action : page.theme.outline
                                }
                            }

                            Label {
                                text: qsTr("Server preset")
                                color: page.theme.secondaryText
                                font.pixelSize: 10
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 6
                                Md3ComboBox {
                                    id: serverPreset
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 42
                                    theme: page.theme
                                    model: serverPresetModel
                                    textRole: "label"
                                    onActivated: serverPanel.selectPreset()
                                }
                                CompactIconButton {
                                    theme: page.theme
                                    iconName: "edit"
                                    toolTip: qsTr("Edit server presets")
                                    onClicked: windowModel.show_window("server_presets")
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 42
                            radius: 12
                            color: page.theme.surfaceContainerHigh

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 12
                                anchors.rightMargin: 12
                                spacing: 9
                                MaterialIcon {
                                    name: configurationController.server_test_status
                                        === "success" ? "cloud_done"
                                        : configurationController.server_test_status
                                            === "error" ? "cloud_off"
                                            : "cloud_sync"
                                    size: 17
                                    color: configurationController.server_test_status
                                        === "success" ? page.theme.green
                                        : configurationController.server_test_status
                                            === "error" ? page.theme.red
                                            : page.theme.action
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: configurationController.server_test_message
                                        || qsTr("Test changes before saving them.")
                                    color: page.theme.secondaryText
                                    font.pixelSize: 9
                                    elide: Text.ElideRight
                                }
                                BusyIndicator {
                                    visible:
                                        configurationController.server_test_busy
                                    running: visible
                                    Layout.preferredWidth: 22
                                    Layout.preferredHeight: 22
                                }
                                Md3Button {
                                    theme: page.theme
                                    visible:
                                        !configurationController.server_test_busy
                                    flat: true
                                    text: qsTr("Test")
                                    icon.name: "network_check"
                                    onClicked:
                                        configurationController.test_server(
                                            serverPanel.formValues()
                                        )
                                }
                                Md3Button {
                                    theme: page.theme
                                    visible:
                                        !configurationController.server_test_busy
                                    highlighted: true
                                    text: qsTr("Generate ticket")
                                    icon.name: "key"
                                    onClicked: {
                                        if (page.managed) {
                                            if (configurationController.apply_current())
                                                appController.request_authentication()
                                        } else {
                                            appController.apply_server_configuration(
                                                serverAddress.text,
                                                serverPreset.currentText
                                            )
                                        }
                                    }
                                }
                            }
                        }
                    }

                    ConfigurationSection {
                        Layout.fillWidth: true
                        theme: page.theme
                        title: qsTr("Account and routing")
                        description: qsTr("Authentication identity, portal site and optional proxy.")
                        iconName: "admin_panel_settings"

                        GridLayout {
                            Layout.fillWidth: true
                            columns: 2
                            columnSpacing: 14
                            rowSpacing: 8

                            Label {
                                text: qsTr("User")
                                color: page.theme.secondaryText
                                font.pixelSize: 10
                            }
                            Md3TextField {
                                theme: page.theme
                                id: userName
                                Layout.fillWidth: true
                                Layout.preferredHeight: 42
                                color: page.theme.primaryText
                                placeholderText: qsTr("TACTIC login")
                                placeholderTextColor: page.theme.disabledText
                                selectByMouse: true
                                onTextEdited: serverPanel.updateValues()
                                background: Rectangle {
                                    radius: 11
                                    color: page.theme.surfaceContainerHigh
                                    border.width: userName.activeFocus ? 2 : 1
                                    border.color: userName.activeFocus
                                        ? page.theme.action : page.theme.outline
                                }
                            }

                            Md3CheckBox {
                                theme: page.theme
                                id: siteEnabled
                                text: qsTr("Use portal site")
                                onToggled: serverPanel.updateValues()
                            }
                            Md3TextField {
                                theme: page.theme
                                id: siteName
                                Layout.fillWidth: true
                                Layout.preferredHeight: 42
                                enabled: siteEnabled.checked
                                color: page.theme.primaryText
                                placeholderText: qsTr("Site name")
                                placeholderTextColor: page.theme.disabledText
                                selectByMouse: true
                                onTextEdited: serverPanel.updateValues()
                                background: Rectangle {
                                    radius: 11
                                    color: page.theme.surfaceContainerHigh
                                    border.width: siteName.activeFocus ? 2 : 1
                                    border.color: siteName.activeFocus
                                        ? page.theme.action : page.theme.outline
                                }
                            }

                            Md3CheckBox {
                                theme: page.theme
                                id: proxyEnabled
                                text: qsTr("Use proxy")
                                onToggled: serverPanel.updateValues()
                            }
                            Md3TextField {
                                theme: page.theme
                                id: proxyServer
                                Layout.fillWidth: true
                                Layout.preferredHeight: 42
                                enabled: proxyEnabled.checked
                                color: page.theme.primaryText
                                placeholderText: qsTr("Proxy server")
                                placeholderTextColor: page.theme.disabledText
                                selectByMouse: true
                                onTextEdited: serverPanel.updateValues()
                                background: Rectangle {
                                    radius: 11
                                    color: page.theme.surfaceContainerHigh
                                    border.width: proxyServer.activeFocus ? 2 : 1
                                    border.color: proxyServer.activeFocus
                                        ? page.theme.action : page.theme.outline
                                }
                            }

                            Label {
                                text: qsTr("Proxy login")
                                color: page.theme.secondaryText
                                font.pixelSize: 10
                            }
                            Md3TextField {
                                theme: page.theme
                                id: proxyLogin
                                Layout.fillWidth: true
                                Layout.preferredHeight: 42
                                enabled: proxyEnabled.checked
                                color: page.theme.primaryText
                                placeholderText: qsTr("Optional")
                                placeholderTextColor: page.theme.disabledText
                                selectByMouse: true
                                onTextEdited: serverPanel.updateValues()
                                background: Rectangle {
                                    radius: 11
                                    color: page.theme.surfaceContainerHigh
                                    border.width: proxyLogin.activeFocus ? 2 : 1
                                    border.color: proxyLogin.activeFocus
                                        ? page.theme.action : page.theme.outline
                                }
                            }

                            Label {
                                text: qsTr("Proxy password")
                                color: page.theme.secondaryText
                                font.pixelSize: 10
                            }
                            Md3TextField {
                                id: proxyPassword
                                theme: page.theme
                                Layout.fillWidth: true
                                Layout.preferredHeight: 42
                                enabled: proxyEnabled.checked
                                echoMode: TextInput.Password
                                placeholderText: serverPanel.hasProxyPassword
                                    ? qsTr("Stored password — enter to replace")
                                    : qsTr("Proxy password")
                                onTextEdited: serverPanel.updateValues()
                            }
                        }
                    }

                    ConfigurationSection {
                        Layout.fillWidth: true
                        theme: page.theme
                        title: qsTr("Background checks")
                        description: qsTr("Intervals for recurring TACTIC requests. Messages, reactions, activity and task changes share one batched update request.")
                        iconName: "schedule"

                        GridLayout {
                            Layout.fillWidth: true
                            columns: 2
                            columnSpacing: 14
                            rowSpacing: 8

                            Label {
                                text: qsTr("Connection ping")
                                color: page.theme.secondaryText
                                font.pixelSize: 10
                            }
                            Md3ComboBox {
                                id: pingInterval
                                Layout.fillWidth: true
                                theme: page.theme
                                model: [
                                    qsTr("Off"),
                                    qsTr("Every 10 seconds"),
                                    qsTr("Every 60 seconds")
                                ]
                                onActivated: serverPanel.updateValues()
                            }

                            Label {
                                text: qsTr("Server updates")
                                color: page.theme.secondaryText
                                font.pixelSize: 10
                            }
                            Md3ComboBox {
                                id: serverUpdateInterval
                                Layout.fillWidth: true
                                theme: page.theme
                                model: [
                                    qsTr("Every 5 seconds"),
                                    qsTr("Every 10 seconds"),
                                    qsTr("Every 30 seconds"),
                                    qsTr("Every 60 seconds")
                                ]
                                onActivated: serverPanel.updateValues()
                            }

                            Label {
                                text: qsTr("Presence heartbeat")
                                color: page.theme.secondaryText
                                font.pixelSize: 10
                            }
                            Md3ComboBox {
                                id: heartbeatInterval
                                Layout.fillWidth: true
                                theme: page.theme
                                model: [
                                    qsTr("Every 30 seconds"),
                                    qsTr("Every 60 seconds"),
                                    qsTr("Every 120 seconds"),
                                    qsTr("Every 300 seconds")
                                ]
                                onActivated: serverPanel.updateValues()
                            }

                            Item { Layout.preferredWidth: 1; Layout.preferredHeight: 1 }
                            Label {
                                Layout.fillWidth: true
                                text: qsTr("Presence heartbeat is always enabled so online status remains reliable.")
                                color: page.theme.secondaryText
                                font.pixelSize: 9
                                wrapMode: Text.WordWrap
                            }
                        }
                    }

                    Md3Button {
                        theme: page.theme
                        visible: !page.managed
                        Layout.alignment: Qt.AlignRight
                        text: qsTr("Apply server")
                        icon.name: "save"
                        onClicked: appController.apply_server_configuration(
                            serverAddress.text,
                            serverPreset.currentText
                        )
                    }

                    Item {
                        Layout.preferredHeight: 8
                    }
                }
            }
        }
    }

    Component {
        id: projectForm

        Item {
            id: projectPanel
            property string selectedCode: ""
            property string selectedTitle: ""
            property string selectedStatus: ""

            RowLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 14

                ConfigurationSection {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    theme: page.theme
                    title: qsTr("Available projects")
                    description: qsTr("Select a project to make it active in the workspace.")
                    iconName: "project-diagram"

                    ListView {
                        id: projectList
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        spacing: 4
                        model: projectModel
                        delegate: Item {
                            id: projectRow
                            required property string projectCode
                            required property string title
                            required property string category
                            required property string status
                            width: projectList.width
                            height: 56
                            readonly property bool selected:
                                projectPanel.selectedCode === projectCode

                            Rectangle {
                                anchors.fill: parent
                                radius: 11
                                color: projectRow.selected
                                    ? page.theme.selected
                                    : projectMouse.containsMouse
                                        ? page.theme.rowHover
                                        : page.theme.surfaceContainerHigh
                                border.width: 1
                                border.color: projectRow.selected
                                    ? page.theme.action
                                    : page.theme.outlineVariant
                            }
                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 12
                                anchors.rightMargin: 10
                                spacing: 10
                                Rectangle {
                                    Layout.preferredWidth: 32
                                    Layout.preferredHeight: 32
                                    radius: 10
                                    color: page.theme.secondaryContainer
                                    MaterialIcon {
                                        anchors.centerIn: parent
                                        name: "folder_special"
                                        size: 17
                                        color: page.theme.action
                                    }
                                }
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 2
                                    Label {
                                        Layout.fillWidth: true
                                        text: projectRow.title
                                        color: page.theme.primaryText
                                        font.pixelSize: 11
                                        font.weight: Font.DemiBold
                                        elide: Text.ElideRight
                                    }
                                    Label {
                                        Layout.fillWidth: true
                                        text: projectRow.projectCode
                                            + (projectRow.category.length
                                                ? " · " + projectRow.category
                                                : "")
                                        color: page.theme.secondaryText
                                        font.pixelSize: 9
                                        elide: Text.ElideRight
                                    }
                                }
                                Label {
                                    text: projectRow.status || "UNKNOWN"
                                    color: page.theme.secondaryText
                                    font.pixelSize: 8
                                    font.weight: Font.DemiBold
                                }
                            }
                            MouseArea {
                                id: projectMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    projectPanel.selectedCode = projectRow.projectCode
                                    projectPanel.selectedTitle = projectRow.title
                                    projectPanel.selectedStatus = projectRow.status
                                }
                                onDoubleClicked: {
                                    projectPanel.selectedCode = projectRow.projectCode
                                    appController.select_project(projectRow.projectCode)
                                }
                            }
                        }
                        ScrollBar.vertical: Md3ScrollBar {
                            theme: page.theme
                            flickableTarget: projectList
                        }
                    }
                }

                ConfigurationSection {
                    Layout.preferredWidth: Math.max(250, parent.width * .34)
                    Layout.fillHeight: true
                    theme: page.theme
                    title: qsTr("Workspace project")
                    description: qsTr("Project selection is shared with the main project chooser.")
                    iconName: "workspaces"

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        Label {
                            text: qsTr("CURRENT")
                            color: page.theme.secondaryText
                            font.pixelSize: 8
                            font.weight: Font.DemiBold
                        }
                        Label {
                            Layout.fillWidth: true
                            text: appController.current_project_title
                                || qsTr("No active project")
                            color: page.theme.primaryText
                            font.pixelSize: 13
                            font.weight: Font.DemiBold
                            wrapMode: Text.WordWrap
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 92
                        radius: 12
                        color: page.theme.surfaceContainerHigh
                        border.width: 1
                        border.color: page.theme.outlineVariant

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 4
                            Label {
                                text: projectPanel.selectedCode.length
                                    ? qsTr("SELECTED PROJECT")
                                    : qsTr("SELECT A PROJECT")
                                color: page.theme.secondaryText
                                font.pixelSize: 8
                                font.weight: Font.DemiBold
                            }
                            Label {
                                Layout.fillWidth: true
                                text: projectPanel.selectedTitle
                                    || qsTr("Choose an item from the list")
                                color: projectPanel.selectedTitle.length
                                    ? page.theme.primaryText
                                    : page.theme.disabledText
                                font.pixelSize: 11
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }
                            Label {
                                Layout.fillWidth: true
                                text: projectPanel.selectedCode
                                    + (projectPanel.selectedStatus.length
                                        ? " · " + projectPanel.selectedStatus : "")
                                color: page.theme.secondaryText
                                font.pixelSize: 9
                                elide: Text.ElideRight
                            }
                        }
                    }

                    Md3Button {
                        theme: page.theme
                        highlighted: true
                        Layout.fillWidth: true
                        enabled: projectPanel.selectedCode.length > 0
                        text: qsTr("Activate selected project")
                        icon.name: "arrow_forward"
                        onClicked:
                            appController.select_project(projectPanel.selectedCode)
                    }

                    Item {
                        Layout.fillHeight: true
                    }
                }
            }
        }
    }

    Component {
        id: checkinOutPreferencesForm

        Item {
            ScrollView {
                id: checkinOutScroll
                anchors.fill: parent
                contentWidth: availableWidth
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                ScrollBar.vertical: Md3ScrollBar {
                    theme: page.theme
                }

                ColumnLayout {
                    x: 22
                    y: 20
                    width: Math.max(0, checkinOutScroll.availableWidth - 44)
                    spacing: 14

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 14

                        ConfigurationSection {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            theme: page.theme
                            title: qsTr("Process tabs")
                            description: qsTr("Search types available in the current project.")
                            iconName: "account_tree"

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 3
                                Repeater {
                                    model: processTabsModel
                                    delegate: Md3CheckBox {
                                        theme: page.theme
                                        required property string label
                                        Layout.fillWidth: true
                                        text: label
                                        checked: true
                                        enabled: false
                                    }
                                }
                                Label {
                                    visible: processTabsModel.count() === 0
                                    Layout.fillWidth: true
                                    text: qsTr("Select a project to load its process tabs.")
                                    color: page.theme.secondaryText
                                    font.pixelSize: 9
                                    wrapMode: Text.WordWrap
                                }
                            }
                        }

                        ConfigurationSection {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            theme: page.theme
                            title: qsTr("Workspace panels")
                            description: qsTr("Legacy control tabs and their order.")
                            iconName: "view_kanban"

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 3
                                Repeater {
                                    model: controlsTabsModel
                                    delegate: Md3CheckBox {
                                        theme: page.theme
                                        required property string label
                                        Layout.fillWidth: true
                                        text: label
                                        checked: true
                                        enabled: false
                                    }
                                }
                                Label {
                                    visible: controlsTabsModel.count() === 0
                                    Layout.fillWidth: true
                                    text: qsTr("Panel visibility is still read from the legacy configuration.")
                                    color: page.theme.secondaryText
                                    font.pixelSize: 9
                                    wrapMode: Text.WordWrap
                                }
                            }
                        }
                    }

                    ConfigurationSection {
                        Layout.fillWidth: true
                        theme: page.theme
                        title: qsTr("Layout behaviour")
                        description: qsTr("How the last workspace layout is reused.")
                        iconName: "dashboard_customize"

                        Md3CheckBox {
                            theme: page.theme
                            Layout.fillWidth: true
                            text: qsTr("Apply the last opened tab layout to all tabs")
                            checked: true
                            enabled: false
                        }
                    }

                    Item {
                        Layout.preferredHeight: 8
                    }
                }
            }
        }
    }

    Component {
        id: globalPreferencesForm

        Item {
            id: globalPanel
            property bool loadingValues: true

            function formValues() {
                return {
                    "cacheProcessTabs": cacheProcessTabs.checked,
                    "darkTheme": darkTheme.checked,
                    "themeStyle": themeStyle.currentValue || "md3",
                    "language": interfaceLanguage.currentValue || "en",
                    "configPath": configurationPath.text
                }
            }

            function syncValues() {
                const values = configurationController.page_values(
                    "global_preferences"
                )
                loadingValues = true
                cacheProcessTabs.checked = Boolean(values.cacheProcessTabs)
                darkTheme.checked = Boolean(values.darkTheme)
                const selectedTheme = values.themeStyle || "md3"
                for (let row = 0; row < themeStyle.count; ++row) {
                    if (themeStyle.model[row].value === selectedTheme) {
                        themeStyle.currentIndex = row
                        break
                    }
                }
                const selectedLanguage = values.language || "en"
                for (let row = 0; row < interfaceLanguage.count; ++row) {
                    if (interfaceLanguage.model[row].value
                            === selectedLanguage) {
                        interfaceLanguage.currentIndex = row
                        break
                    }
                }
                configurationPath.text = values.configPath || ""
                loadingValues = false
            }

            function updateValues() {
                if (!page.managed || loadingValues)
                    return
                configurationController.update_page(
                    "global_preferences", formValues()
                )
            }

            Component.onCompleted: syncValues()

            Connections {
                target: configurationController

                function onSessionStarted() {
                    globalPanel.syncValues()
                }

                function onPageReset(pageId) {
                    if (pageId === "global_preferences")
                        globalPanel.syncValues()
                }
            }

            ScrollView {
                id: globalScroll
                anchors.fill: parent
                contentWidth: availableWidth
                contentHeight: globalContent.implicitHeight + 40
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                ScrollBar.vertical: Md3ScrollBar {
                    theme: page.theme
                    flickableTarget: globalScroll
                }

                ColumnLayout {
                    id: globalContent
                    x: 22
                    y: 20
                    width: Math.max(0, globalScroll.availableWidth - 44)
                    spacing: 14

                    ConfigurationSection {
                        Layout.fillWidth: true
                        theme: page.theme
                        title: qsTr("Workspace startup")
                        description: qsTr("Restore cached search tabs and their local UI state.")
                        iconName: "cached"

                        Md3CheckBox {
                            theme: page.theme
                            id: cacheProcessTabs
                            Layout.fillWidth: true
                            text: qsTr("Cache process tabs for a faster launch")
                            onToggled: globalPanel.updateValues()
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 12

                            Label {
                                text: qsTr("Interface style")
                                color: page.theme.primaryText
                                font.family: page.theme.fontFamily
                                font.pixelSize: 10
                            }
                            Md3ComboBox {
                                id: themeStyle
                                theme: page.theme
                                Layout.fillWidth: true
                                model: appController.theme_options
                                textRole: "label"
                                valueRole: "value"
                                onActivated: globalPanel.updateValues()
                            }
                        }
                        Label {
                            Layout.fillWidth: true
                            text: themeStyle.currentIndex >= 0
                                ? qsTr(themeStyle.model[
                                    themeStyle.currentIndex].description)
                                : ""
                            color: page.theme.secondaryText
                            font.family: page.theme.fontFamily
                            font.pixelSize: 9
                            wrapMode: Text.WordWrap
                        }

                        Md3Button {
                            theme: page.theme
                            Layout.alignment: Qt.AlignLeft
                            text: qsTr("Flush tabs cache")
                            icon.name: "delete_sweep"
                            onClicked:
                                configurationController.flush_search_cache()
                        }
                    }

                    ConfigurationSection {
                        Layout.fillWidth: true
                        theme: page.theme
                        title: qsTr("Language")
                        description: qsTr(
                            "Choose the language used by the application interface."
                        )
                        iconName: "language"

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 12

                            Label {
                                text: qsTr("Interface language")
                                color: page.theme.primaryText
                                font.family: page.theme.fontFamily
                                font.pixelSize: 10
                            }
                            Md3ComboBox {
                                id: interfaceLanguage
                                theme: page.theme
                                Layout.fillWidth: true
                                model: localizationController.language_options
                                textRole: "label"
                                valueRole: "value"
                                onActivated: globalPanel.updateValues()
                            }
                        }
                    }

                    ConfigurationSection {
                        Layout.fillWidth: true
                        theme: page.theme
                        title: qsTr("Appearance")
                        description: qsTr("Uses the same theme setting as the main toolbar.")
                        iconName: "palette"

                        Md3CheckBox {
                            theme: page.theme
                            id: darkTheme
                            Layout.fillWidth: true
                            text: qsTr("Use dark theme")
                            onToggled: globalPanel.updateValues()
                        }
                    }

                    ConfigurationSection {
                        Layout.fillWidth: true
                        theme: page.theme
                        title: qsTr("Configuration location")
                        description: qsTr("The active legacy configuration root.")
                        iconName: "folder_open"

                        Md3TextField {
                            theme: page.theme
                            id: configurationPath
                            Layout.fillWidth: true
                            Layout.preferredHeight: 42
                            readOnly: true
                            selectByMouse: true
                            color: page.theme.secondaryText
                            background: Rectangle {
                                radius: 11
                                color: page.theme.surfaceContainerHigh
                                border.width: 1
                                border.color: page.theme.outlineVariant
                            }
                        }
                        Label {
                            Layout.fillWidth: true
                            text: qsTr("Changing this path is not supported by the legacy bootstrap.")
                            color: page.theme.secondaryText
                            font.pixelSize: 9
                            wrapMode: Text.WordWrap
                        }
                    }

                    Item {
                        Layout.preferredHeight: 8
                    }
                }
            }
        }
    }

    Component {
        id: taskPreferencesForm

        Item {
            id: taskPreferencesPanel
            property bool loadingValues: true

            function choiceIndex(model, value) {
                for (let row = 0; row < model.length; ++row) {
                    if (String(model[row].value) === String(value || ""))
                        return row
                }
                return 0
            }

            function formValues() {
                const columns = []
                for (let row = 0; row < taskColumnSettings.count; ++row) {
                    const value = taskColumnSettings.get(row)
                    columns.push({
                        "key": value.key,
                        "label": value.label,
                        "width": value.columnWidth,
                        "visible": value.columnVisible,
                        "required": value.required,
                        "order": row
                    })
                }
                return {
                    "viewMode": defaultTaskView.currentValue || "list",
                    "sortMode": defaultTaskSort.currentValue || "due",
                    "groupMode": defaultTaskGroup.currentValue || "process",
                    "inspectorExpanded": inspectorExpanded.checked,
                    "columns": columns
                }
            }

            function syncValues() {
                const values = configurationController.page_values(
                    "tasks_preferences"
                )
                loadingValues = true
                defaultTaskView.currentIndex = choiceIndex(
                    defaultTaskView.model, values.viewMode
                )
                defaultTaskSort.currentIndex = choiceIndex(
                    defaultTaskSort.model, values.sortMode
                )
                defaultTaskGroup.currentIndex = choiceIndex(
                    defaultTaskGroup.model, values.groupMode
                )
                inspectorExpanded.checked = Boolean(values.inspectorExpanded)
                taskColumnSettings.clear()
                const columns = values.columns || []
                for (let row = 0; row < columns.length; ++row) {
                    const column = columns[row]
                    taskColumnSettings.append({
                        "key": column.key,
                        "label": column.label,
                        "columnWidth": column.width,
                        "columnVisible": column.visible,
                        "required": column.required
                    })
                }
                loadingValues = false
            }

            function updateValues() {
                if (!page.managed || loadingValues)
                    return
                configurationController.update_page(
                    "tasks_preferences", formValues()
                )
            }

            Component.onCompleted: syncValues()

            Connections {
                target: configurationController

                function onSessionStarted() {
                    taskPreferencesPanel.syncValues()
                }

                function onPageReset(pageId) {
                    if (pageId === "tasks_preferences")
                        taskPreferencesPanel.syncValues()
                }
            }

            ListModel { id: taskColumnSettings }

            ScrollView {
                id: taskPreferencesScroll
                anchors.fill: parent
                contentWidth: availableWidth
                contentHeight: taskPreferencesContent.implicitHeight + 40
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                ScrollBar.vertical: Md3ScrollBar {
                    theme: page.theme
                    flickableTarget: taskPreferencesScroll
                }

                ColumnLayout {
                    id: taskPreferencesContent
                    x: 22
                    y: 20
                    width: Math.max(
                        0, taskPreferencesScroll.availableWidth - 44
                    )
                    spacing: 14

                    ConfigurationSection {
                        Layout.fillWidth: true
                        theme: page.theme
                        title: qsTr("Task Browser defaults")
                        description: qsTr("Initial view, ordering and grouping for detailed task management.")
                        iconName: "tasks"

                        GridLayout {
                            Layout.fillWidth: true
                            columns: 2
                            columnSpacing: 12
                            rowSpacing: 8

                            Label {
                                text: qsTr("View")
                                color: page.theme.primaryText
                                font.pixelSize: 10
                            }
                            Md3ComboBox {
                                id: defaultTaskView
                                theme: page.theme
                                Layout.fillWidth: true
                                model: [
                                    {"label": "Table", "value": "list"},
                                    {"label": "Gantt", "value": "gantt"}
                                ]
                                textRole: "label"
                                valueRole: "value"
                                onActivated: taskPreferencesPanel.updateValues()
                            }

                            Label {
                                text: qsTr("Sort")
                                color: page.theme.primaryText
                                font.pixelSize: 10
                            }
                            Md3ComboBox {
                                id: defaultTaskSort
                                theme: page.theme
                                Layout.fillWidth: true
                                model: [
                                    {"label": "Deadline", "value": "due"},
                                    {"label": "Recently changed", "value": "recent"},
                                    {"label": "Process", "value": "process"},
                                    {"label": "Assignee", "value": "user"},
                                    {"label": "Status", "value": "status"},
                                    {"label": "Parent object", "value": "object"}
                                ]
                                textRole: "label"
                                valueRole: "value"
                                onActivated: taskPreferencesPanel.updateValues()
                            }

                            Label {
                                text: qsTr("Group")
                                color: page.theme.primaryText
                                font.pixelSize: 10
                            }
                            Md3ComboBox {
                                id: defaultTaskGroup
                                theme: page.theme
                                Layout.fillWidth: true
                                model: [
                                    {"label": "By Process", "value": "process"},
                                    {"label": "By Status", "value": "status"},
                                    {"label": "By Assignee", "value": "user"},
                                    {"label": "By Parent Object", "value": "object"},
                                    {"label": "By Project", "value": "project"},
                                    {"label": "By Search Type", "value": "search_type"},
                                    {"label": "No Groups", "value": "none"}
                                ]
                                textRole: "label"
                                valueRole: "value"
                                onActivated: taskPreferencesPanel.updateValues()
                            }
                        }

                        Md3CheckBox {
                            id: inspectorExpanded
                            theme: page.theme
                            Layout.fillWidth: true
                            text: qsTr("Expand Task Inspector when Notes opens")
                            onToggled: taskPreferencesPanel.updateValues()
                        }
                    }

                    ConfigurationSection {
                        Layout.fillWidth: true
                        theme: page.theme
                        title: qsTr("Task table columns")
                        description: qsTr("Choose visible columns, their width and display order. Object and Status remain available.")
                        iconName: "view_column"

                        Repeater {
                            model: taskColumnSettings

                            delegate: Rectangle {
                                id: taskColumnRow
                                required property int index
                                required property string key
                                required property string label
                                required property int columnWidth
                                required property bool columnVisible
                                required property bool required

                                Layout.fillWidth: true
                                Layout.preferredHeight: 44
                                radius: page.theme.itemRadius
                                color: page.theme.surfaceContainerHigh

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 8
                                    anchors.rightMargin: 6
                                    spacing: 7

                                    Md3CheckBox {
                                        theme: page.theme
                                        checked: taskColumnRow.columnVisible
                                        enabled: !taskColumnRow.required
                                        onToggled: {
                                            if (taskPreferencesPanel.loadingValues)
                                                return
                                            taskColumnSettings.setProperty(
                                                taskColumnRow.index,
                                                "columnVisible", checked
                                            )
                                            taskPreferencesPanel.updateValues()
                                        }
                                    }
                                    Label {
                                        Layout.fillWidth: true
                                        text: taskColumnRow.label
                                        color: page.theme.primaryText
                                        font.pixelSize: 10
                                        elide: Text.ElideRight
                                    }
                                    Md3SpinBox {
                                        theme: page.theme
                                        Layout.preferredWidth: 118
                                        from: 40
                                        to: 480
                                        stepSize: 4
                                        value: taskColumnRow.columnWidth
                                        onValueModified: {
                                            taskColumnSettings.setProperty(
                                                taskColumnRow.index,
                                                "columnWidth", value
                                            )
                                            taskPreferencesPanel.updateValues()
                                        }
                                    }
                                    CompactIconButton {
                                        theme: page.theme
                                        iconName: "arrow_upward"
                                        toolTip: qsTr("Move column left")
                                        enabled: taskColumnRow.index > 0
                                        onClicked: {
                                            taskColumnSettings.move(
                                                taskColumnRow.index,
                                                taskColumnRow.index - 1, 1
                                            )
                                            taskPreferencesPanel.updateValues()
                                        }
                                    }
                                    CompactIconButton {
                                        theme: page.theme
                                        iconName: "arrow_downward"
                                        toolTip: qsTr("Move column right")
                                        enabled: taskColumnRow.index
                                            < taskColumnSettings.count - 1
                                        onClicked: {
                                            taskColumnSettings.move(
                                                taskColumnRow.index,
                                                taskColumnRow.index + 1, 1
                                            )
                                            taskPreferencesPanel.updateValues()
                                        }
                                    }
                                }
                            }
                        }
                    }

                    Label {
                        Layout.fillWidth: true
                        text: qsTr("Dock and window geometry is restored separately for each workspace. Active rows, checked tasks and temporary filters are never saved as defaults.")
                        color: page.theme.secondaryText
                        font.pixelSize: 9
                        wrapMode: Text.WordWrap
                    }

                    Item { Layout.preferredHeight: 8 }
                }
            }
        }
    }

    Component {
        id: mayaPreferencesForm

        Item {
            id: mayaPanel
            property bool loadingValues: true

            function formValues() {
                const row = mayaFormat.currentIndex
                const record = row >= 0 ? mayaFormatModel.get(row) : null
                return {
                    "currentWorkdir": mayaWorkdir.text,
                    "saveFormat": record ? record.value : "",
                    "createMayaDirs": createMayaDirs.checked,
                    "createPlayblast": createPlayblast.checked
                }
            }

            function syncValues() {
                const values = configurationController.page_values(
                    "maya_preferences"
                )
                loadingValues = true
                mayaWorkdir.text = values.currentWorkdir || ""
                createMayaDirs.checked = Boolean(values.createMayaDirs)
                createPlayblast.checked = Boolean(values.createPlayblast)
                for (let row = 0; row < mayaFormatModel.count(); ++row) {
                    if (mayaFormatModel.get(row).value
                            === values.saveFormat) {
                        mayaFormat.currentIndex = row
                        break
                    }
                }
                loadingValues = false
            }

            function updateValues() {
                if (!page.managed || loadingValues)
                    return
                configurationController.update_page(
                    "maya_preferences", formValues()
                )
            }

            Component.onCompleted: syncValues()

            Connections {
                target: configurationController

                function onSessionStarted() {
                    mayaPanel.syncValues()
                }

                function onPageReset(pageId) {
                    if (pageId === "maya_preferences")
                        mayaPanel.syncValues()
                }
            }

            ScrollView {
                id: mayaScroll
                anchors.fill: parent
                contentWidth: availableWidth
                contentHeight: mayaContent.implicitHeight + 40
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                ScrollBar.vertical: Md3ScrollBar {
                    theme: page.theme
                    flickableTarget: mayaScroll
                }

                ColumnLayout {
                    id: mayaContent
                    x: 22
                    y: 20
                    width: Math.max(0, mayaScroll.availableWidth - 44)
                    spacing: 14

                    ConfigurationSection {
                        Layout.fillWidth: true
                        theme: page.theme
                        title: qsTr("Maya scene environment")
                        description: qsTr("Scene workspace and the preferred Maya file format.")
                        iconName: "movie"

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            Label {
                                text: qsTr("Current work directory")
                                color: page.theme.secondaryText
                                font.pixelSize: 10
                            }
                            Md3TextField {
                                theme: page.theme
                                id: mayaWorkdir
                                Layout.fillWidth: true
                                Layout.preferredHeight: 42
                                placeholderText: qsTr("No work directory selected")
                                color: page.theme.primaryText
                                placeholderTextColor: page.theme.disabledText
                                selectByMouse: true
                                readOnly: true
                                leftPadding: 13
                                rightPadding: 13
                                background: Rectangle {
                                    radius: 11
                                    color: page.theme.surfaceContainerHigh
                                    border.width: 1
                                    border.color: page.theme.outlineVariant
                                }
                            }
                            Label {
                                text: qsTr("Maya saving format")
                                color: page.theme.secondaryText
                                font.pixelSize: 10
                            }
                            Md3ComboBox {
                                id: mayaFormat
                                Layout.fillWidth: true
                                Layout.preferredHeight: 42
                                theme: page.theme
                                model: mayaFormatModel
                                textRole: "label"
                                displayText: currentText
                                    || "Select Maya save format"
                                onActivated: mayaPanel.updateValues()
                            }
                        }
                    }

                    ConfigurationSection {
                        Layout.fillWidth: true
                        theme: page.theme
                        title: qsTr("Scene creation")
                        description: qsTr("Defaults exposed to the existing Maya integration.")
                        iconName: "settings_suggest"

                        Md3CheckBox {
                            theme: page.theme
                            id: createMayaDirs
                            Layout.fillWidth: true
                            text: qsTr("Create Maya directories and workspace.mel")
                            onToggled: mayaPanel.updateValues()
                        }
                        Md3CheckBox {
                            theme: page.theme
                            id: createPlayblast
                            Layout.fillWidth: true
                            text: qsTr("Create screenshot / playblast")
                            onToggled: mayaPanel.updateValues()
                        }
                    }

                    Item {
                        Layout.preferredHeight: 8
                    }
                }
            }
        }
    }
}

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls
Item {
    id: root
    objectName: "configurationServerPage"
    required property var theme
    property bool managed: false
    property bool loadingValues: true
    readonly property bool signedIn:
        appController.has_ticket
        && !appController.authentication_required
        && appController.login_name.length > 0
    readonly property var updateSeconds: [5, 10, 30, 60]
    readonly property var batchDelays: [100, 200, 500, 1000]

    function intervalIndex(options, value, fallback) {
        const index = options.indexOf(Number(value))
        return index >= 0 ? index : fallback
    }

    function formValues() {
        return {
            "serverUpdateBatchDelay": batchDelays[serverUpdateBatchDelay.currentIndex],
            "serverUrl": serverAddress.text,
            "rpcTransport": rpcTransport.currentIndex === 1 ? "json" : "xmlrpc",
            "serverUpdateMode": serverUpdateMode.currentIndex === 1 ? "sse" : "poll",
            "presetName": serverPreset.currentText,
            "serverUpdateInterval": updateSeconds[
                serverUpdateInterval.currentIndex
            ],
            "updateSearchKey": updateSearchKey.text,
            "queryMode": queryMode.currentIndex === 1
                ? "plugin" : "local"
        }
    }

    function loadValues(values) {
        loadingValues = true
        serverUpdateMode.currentIndex = values.serverUpdateMode === "sse" ? 1 : 0
        serverUpdateBatchDelay.currentIndex = intervalIndex(batchDelays, values.serverUpdateBatchDelay, 1)
        serverAddress.text = values.serverUrl || ""
        rpcTransport.currentIndex = values.rpcTransport === "json" ? 1 : 0
        updateSearchKey.text = values.updateSearchKey || ""
        queryMode.currentIndex = values.queryMode === "plugin" ? 1 : 0
        serverUpdateInterval.currentIndex = intervalIndex(
            updateSeconds, values.serverUpdateInterval, 2
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
        if (!root.managed || loadingValues)
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
            root.syncValues()
        }

        function onPageReset(pageId) {
            if (pageId === "server")
                root.syncValues()
        }
    }

    ScrollView {
        id: serverScroll
        anchors.fill: parent
        contentWidth: availableWidth
        contentHeight: serverContent.implicitHeight + 40
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        ScrollBar.vertical: Controls.ScrollBar {
            theme: root.theme
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
                theme: root.theme
                title: qsTr("Connection")
                description: qsTr("Server endpoint, active preset and current sign-in status.")
                iconName: "cloud"

                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Server address")
                    description: qsTr("TACTIC HTTP endpoint used by the active server preset and connection test.")
                    Controls.TextField {
                        theme: root.theme
                        id: serverAddress
                        Layout.preferredWidth: 360
                        Layout.preferredHeight: 40
                        placeholderText: qsTr("http://server")
                        color: root.theme.primaryText
                        placeholderTextColor: root.theme.disabledText
                        selectByMouse: true
                        onTextEdited: {
                            queryMode.currentIndex = 0
                            root.updateValues()
                        }
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Server preset")
                    description: qsTr("Select a saved endpoint and its account and routing configuration.")
                    RowLayout {
                        Controls.ComboBox {
                            id: serverPreset
                            Layout.preferredWidth: 270
                            theme: root.theme
                            model: serverPresetModel
                            textRole: "label"
                            onActivated: root.selectPreset()
                        }
                        Controls.CompactIconButton {
                            theme: root.theme
                            iconName: "edit"
                            toolTip: qsTr("Edit presets and routing")
                            onClicked: windowModel.show_window("server_presets")
                        }
                    }
                }

                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("API transport")
                    description: qsTr("XML-RPC supports Legacy TACTIC and TACTIC Stream. JSON requires TACTIC Stream. Saved separately for each preset; applying reconnects.")
                    Controls.ComboBox {
                        id: rpcTransport
                        objectName: "rpcTransportCombo"
                        Layout.preferredWidth: 230
                        theme: root.theme
                        model: [qsTr("XML-RPC"), qsTr("JSON (TACTIC Stream)")]
                        onActivated: root.updateValues()
                    }
                }

                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Query execution")
                    description: qsTr("Local mode needs no server installation. Plugin mode installs or updates the server package on first use with an administrator ticket.")
                    Controls.ComboBox {
                        id: queryMode
                        objectName: "queryModeCombo"
                        Layout.preferredWidth: 210
                        theme: root.theme
                        model: [qsTr("Local"), qsTr("Server plugin")]
                        onActivated: root.updateValues()
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 58
                    radius: 14
                    color: root.theme.surfaceContainerLow

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 11
                        spacing: 10
                        Rectangle {
                            Layout.preferredWidth: 36
                            Layout.preferredHeight: 36
                            radius: 18
                            color: root.theme.surfaceContainerHighest
                            Controls.MaterialIcon {
                                anchors.centerIn: parent
                                name: "account-circle"
                                size: 19
                                color: root.signedIn
                                    ? root.theme.action
                                    : root.theme.secondaryText
                            }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            Layout.minimumWidth: 0
                            spacing: 1
                            Label {
                                Layout.fillWidth: true
                                text: qsTr("Current account")
                                color: root.theme.secondaryText
                                font.pointSize: Controls.Typography.caption
                                elide: Text.ElideRight
                            }
                            Label {
                                Layout.fillWidth: true
                                text: root.signedIn
                                    ? appController.login_name
                                    : qsTr("No active TACTIC account")
                                color: root.theme.primaryText
                                font.pointSize: Controls.Typography.bodyLarge
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }
                        }
                        Controls.StatusChip {
                            theme: root.theme
                            text: root.signedIn
                                ? qsTr("Signed in")
                                : qsTr("Not signed in")
                            iconName: root.signedIn
                                ? "check-circle" : "key"
                            accentColor: root.signedIn
                                ? root.theme.green
                                : root.theme.secondaryText
                        }
                    }
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 42
                    radius: 12
                    color: root.theme.surfaceContainerHigh

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 12
                        spacing: 9
                        Controls.MaterialIcon {
                            name: configurationController.server_test_status
                                === "success" ? "cloud_done"
                                : configurationController.server_test_status
                                    === "error" ? "cloud_off"
                                    : "cloud_sync"
                            size: 17
                            color: configurationController.server_test_status
                                === "success" ? root.theme.green
                                : configurationController.server_test_status
                                    === "error" ? root.theme.red
                                    : root.theme.action
                        }
                        Label {
                            objectName: "serverTestMessage"
                            Layout.fillWidth: true
                            text: qsTr(configurationController.server_test_message)
                                || qsTr("Test changes before saving them.")
                            color: root.theme.secondaryText
                            font.pointSize: Controls.Typography.label
                            elide: Text.ElideRight
                        }
                        Controls.BusyIndicator {
                            uiTheme: root.theme
                            visible:
                                configurationController.server_test_busy
                            running: visible
                            Layout.preferredWidth: 22
                            Layout.preferredHeight: 22
                        }
                        Controls.Button {
                            theme: root.theme
                            visible:
                                !configurationController.server_test_busy
                            flat: true
                            text: qsTr("Test")
                            icon.name: "network_check"
                            onClicked:
                                configurationController.test_server(
                                    root.formValues()
                                )
                        }
                        Controls.Button {
                            theme: root.theme
                            visible:
                                !configurationController.server_test_busy
                            highlighted: true
                            text: qsTr("Generate ticket")
                            icon.name: "key"
                            onClicked: {
                                if (root.managed) {
                                    if (configurationController.apply_current())
                                        appController.request_authentication()
                                } else {
                                    appController.apply_server_configuration(
                                        serverAddress.text,
                                        serverPreset.currentText, false, root.formValues().rpcTransport
                                    )
                                }
                            }
                        }
                    }
                }
            }

            ConfigurationSection {
                Layout.fillWidth: true
                theme: root.theme
                title: qsTr("Background checks")
                description: qsTr("Committed changes are coalesced by one server worker. Only subscribed data is refreshed; presence and authentication keep their own heartbeat.")
                iconName: "schedule"

                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Update delivery")
                    description: qsTr("Server push (SSE) uses the TACTIC Stream collector and refreshes only subscribed data. Other servers require periodic checks.")
                    Controls.ComboBox {
                        id: serverUpdateMode
                        objectName: "serverUpdateMode"
                        Layout.preferredWidth: 210
                        theme: root.theme
                        model: [qsTr("Periodic checks"), qsTr("Server push (SSE)")]
                        onActivated: root.updateValues()
                    }
                }
                Controls.SettingsRow {
                    visible: serverUpdateMode.currentIndex === 1
                    theme: root.theme
                    title: qsTr("Update batching delay")
                    description: qsTr("Combine arriving changes before reading data. A longer delay reduces requests during bursts; it also delays visible updates.")
                    Controls.ComboBox {
                        id: serverUpdateBatchDelay
                        objectName: "serverUpdateBatchDelay"
                        Layout.preferredWidth: 210
                        theme: root.theme
                        model: [qsTr("100 ms"), qsTr("200 ms"), qsTr("500 ms"), qsTr("1000 ms")]
                        onActivated: root.updateValues()
                    }
                }
                Controls.SettingsRow {
                    visible: serverUpdateMode.currentIndex === 0
                    theme: root.theme
                    title: qsTr("Server updates")
                    description: qsTr("Interval for the shared request, including the connection check and presence heartbeat.")
                    showDivider: false
                    Controls.ComboBox {
                        id: serverUpdateInterval
                        objectName: "serverUpdateInterval"
                        Layout.preferredWidth: 210
                        theme: root.theme
                        model: [
                            qsTr("Every 5 seconds"),
                            qsTr("Every 10 seconds"),
                            qsTr("Every 30 seconds"),
                            qsTr("Every 60 seconds")
                        ]
                        onActivated: root.updateValues()
                    }
                }
            }

            ConfigurationSection {
                Layout.fillWidth: true
                theme: root.theme
                title: qsTr("Application updates")
                description: qsTr("Check ZIP snapshots on this TACTIC sObject at startup and once a day.")
                iconName: "system_update"

                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Update sObject search key")
                    description: qsTr("Leave empty to disable automatic checks. Publish release ZIPs as snapshots of this object.")
                    showDivider: false
                    Controls.TextField {
                        id: updateSearchKey
                        theme: root.theme
                        Layout.fillWidth: true
                        Layout.preferredWidth: 360
                        placeholderText: qsTr("project/search_type?project=project&code=CODE")
                        onTextEdited: root.updateValues()
                    }
                }
            }

            Controls.Button {
                theme: root.theme
                visible: !root.managed
                Layout.alignment: Qt.AlignRight
                text: qsTr("Apply server")
                icon.name: "save"
                onClicked: appController.apply_server_configuration(
                    serverAddress.text,
                    serverPreset.currentText, false, root.formValues().rpcTransport
                )
            }

            Item {
                Layout.preferredHeight: 8
            }
        }
    }
}

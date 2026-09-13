import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls
Item {
    id: root
    required property var theme
    property bool managed: false
    property bool loadingValues: true
    property var diagnosticLevelValues: ({})
    readonly property var diagnosticLevelOptions: [
        { "value": "LOG", "label": qsTr("Log") },
        { "value": "INFO", "label": qsTr("Information") },
        { "value": "WARNING", "label": qsTr("Warning") },
        { "value": "MISSING", "label": qsTr("Missing files") },
        { "value": "EXCEPTION", "label": qsTr("Exception") },
        { "value": "ERROR", "label": qsTr("Error") },
        { "value": "CRITICAL", "label": qsTr("Critical") },
        { "value": "API", "label": qsTr("API") }
    ]

    function enabledDiagnosticLevels() {
        const result = []
        for (let index = 0;
                index < diagnosticLevelOptions.length; ++index) {
            const level = diagnosticLevelOptions[index].value
            if (diagnosticLevelValues[level])
                result.push(level)
        }
        return result
    }

    function formValues() {
        return {
            "closeToTray": closeToTray.checked,
            "serverThreads": serverThreads.value,
            "localThreads": localThreads.value,
            "debugLogLevels": enabledDiagnosticLevels(),
            "configPath": configurationPath.text
        }
    }

    function syncValues() {
        const values = configurationController.page_values("global_preferences")
        loadingValues = true
        closeToTray.checked = values.closeToTray === undefined
            ? true : Boolean(values.closeToTray)
        serverThreads.value = Number(values.serverThreads || 4)
        localThreads.value = Number(values.localThreads || 4)
        const selectedLevels = values.debugLogLevels || ["ERROR", "CRITICAL"]
        const levelValues = {}
        for (let index = 0; index < selectedLevels.length; ++index)
            levelValues[selectedLevels[index]] = true
        diagnosticLevelValues = levelValues
        configurationPath.text = values.configPath || ""
        loadingValues = false
    }

    function updateValues() {
        if (!root.managed || loadingValues)
            return
        configurationController.update_page("global_preferences", formValues())
    }

    Component.onCompleted: syncValues()

    Connections {
        target: configurationController

        function onSessionStarted() {
            root.syncValues()
        }

        function onPageReset(pageId) {
            if (pageId === "global_preferences")
                root.syncValues()
        }
    }

    ScrollView {
        id: globalScroll
        anchors.fill: parent
        contentWidth: availableWidth
        contentHeight: globalContent.implicitHeight + 40
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        ScrollBar.vertical: Controls.ScrollBar {
            theme: root.theme
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
                theme: root.theme
                title: qsTr("Application window")
                description: qsTr("Choose what happens when the main window is closed.")
                iconName: "floating"

                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Close to system tray")
                    description: qsTr("Keep TACTIC Handler running in the system tray when the main window close button is pressed. Disable this to exit completely.")
                    showDivider: false
                    Controls.Switch {
                        id: closeToTray
                        objectName: "closeToTraySwitch"
                        theme: root.theme
                        text: ""
                        onToggled: root.updateValues()
                    }
                }
            }

            ConfigurationSection {
                Layout.fillWidth: true
                theme: root.theme
                title: qsTr("Notifications")
                description: qsTr(
                    "Choose which background updates appear as pop-up notifications."
                )
                iconName: "notifications"

                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Activity feed notifications")
                    description: qsTr(
                        "Show a bottom-right notification when another user creates a new activity event. This setting applies immediately."
                    )
                    showDivider: true
                    Controls.Switch {
                        id: activityFeedNotifications
                        objectName: "activityFeedNotificationsSwitch"
                        theme: root.theme
                        text: ""
                        enabled:
                            typeof activityFeedController !== "undefined"
                        checked:
                            typeof activityFeedController !== "undefined"
                            ? activityFeedController.notificationsEnabled
                            : true
                        Accessible.name: qsTr("Activity feed notifications")
                        onToggled: {
                            if (typeof activityFeedController !== "undefined")
                                activityFeedController.set_notifications_enabled(
                                    checked
                                )
                        }
                    }
                }

                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Message notifications")
                    description: qsTr(
                        "Show a bottom-right notification for new messages when their conversation is not open. This setting applies immediately."
                    )
                    showDivider: false
                    Controls.Switch {
                        id: messageNotifications
                        objectName: "messageNotificationsSwitch"
                        theme: root.theme
                        text: ""
                        enabled: typeof messagesController !== "undefined"
                        checked:
                            typeof messagesController !== "undefined"
                            ? messagesController.notificationsEnabled
                            : true
                        Accessible.name: qsTr("Message notifications")
                        onToggled: {
                            if (typeof messagesController !== "undefined")
                                messagesController.set_notifications_enabled(
                                    checked
                                )
                        }
                    }
                }
            }

            ConfigurationSection {
                Layout.fillWidth: true
                theme: root.theme
                title: qsTr("Background workers")
                description: qsTr("Limit parallel server requests and local background work.")
                iconName: "ui-performance"

                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("TACTIC request threads")
                    description: qsTr("Maximum simultaneous XMLRPC requests. Repository Sync sends this many different chunks at once.")
                    Controls.SpinBox {
                        id: serverThreads
                        objectName: "serverThreadsSpinBox"
                        Layout.preferredWidth: 112
                        theme: root.theme
                        from: 1
                        to: 32
                        onValueChanged: root.updateValues()
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Local worker threads")
                    description: qsTr("Maximum simultaneous local background operations. This does not change the Repository Sync download limit.")
                    showDivider: false
                    Controls.SpinBox {
                        id: localThreads
                        objectName: "localThreadsSpinBox"
                        Layout.preferredWidth: 112
                        theme: root.theme
                        from: 1
                        to: 32
                        onValueChanged: root.updateValues()
                    }
                }
            }

            ConfigurationSection {
                Layout.fillWidth: true
                theme: root.theme
                title: qsTr("Diagnostics")
                description: qsTr("Choose which event types are written to the diagnostic log.")
                iconName: "bug_report"

                Repeater {
                    model: root.diagnosticLevelOptions
                    delegate: Controls.SettingsRow {
                        required property int index
                        required property var modelData
                        theme: root.theme
                        title: modelData.label
                        description: modelData.value === "LOG"
                            ? qsTr("General runtime details useful during development.")
                            : modelData.value === "INFO"
                                ? qsTr("Normal lifecycle and completed operation information.")
                            : modelData.value === "WARNING"
                                ? qsTr("Recoverable conditions that may require attention.")
                            : modelData.value === "MISSING"
                                ? qsTr("Repository or local files that could not be found.")
                            : modelData.value === "EXCEPTION"
                                ? qsTr("Caught Python and QML exceptions with diagnostic context.")
                            : modelData.value === "ERROR"
                                ? qsTr("Failed operations that prevented the requested action.")
                            : modelData.value === "CRITICAL"
                                ? qsTr("Failures that can stop a subsystem or application workflow.")
                                : qsTr("TACTIC API calls and their runtime diagnostics.")
                        showDivider: index < root.diagnosticLevelOptions.length - 1
                        Controls.Switch {
                            theme: root.theme
                            text: ""
                            checked: Boolean(
                                root.diagnosticLevelValues[modelData.value]
                            )
                            onToggled: {
                                if (root.loadingValues)
                                    return
                                const values = Object.assign(
                                    {}, root.diagnosticLevelValues
                                )
                                values[modelData.value] = checked
                                root.diagnosticLevelValues = values
                                root.updateValues()
                            }
                        }
                    }
                }
            }

            ConfigurationSection {
                Layout.fillWidth: true
                theme: root.theme
                title: qsTr("Configuration location")
                description: qsTr("Location used by the shared TACTIC Handler configuration API.")
                iconName: "folder_open"

                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Active configuration root")
                    description: qsTr("This path is managed by the application environment and is shown here for diagnostics.")
                    showDivider: false
                    Controls.TextField {
                        theme: root.theme
                        id: configurationPath
                        Layout.preferredWidth: 360
                        Layout.preferredHeight: 40
                        readOnly: true
                        selectByMouse: true
                        color: root.theme.secondaryText
                    }
                }
            }

            Item {
                Layout.preferredHeight: 8
            }
        }
    }
}

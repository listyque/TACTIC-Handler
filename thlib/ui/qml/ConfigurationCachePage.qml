import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    property bool managed: false
    property bool loadingValues: true

    function formValues() {
        return {
            "cacheProcessTabs": cacheProcessTabs.checked,
            "reference": referenceData.checked,
            "search": searchResults.checked,
            "snapshots": snapshotsFiles.checked,
            "relations": relations.checked,
            "tasks": tasks.checked,
            "notes": notes.checked,
            "messages": messages.checked,
            "activity": activity.checked,
            "work_hours": workHours.checked
        }
    }

    function syncValues() {
        const values = configurationController.page_values("cache")
        loadingValues = true
        cacheProcessTabs.checked = values.cacheProcessTabs === undefined
            ? true : Boolean(values.cacheProcessTabs)
        referenceData.checked = Boolean(values.reference)
        searchResults.checked = Boolean(values.search)
        snapshotsFiles.checked = Boolean(values.snapshots)
        relations.checked = Boolean(values.relations)
        tasks.checked = Boolean(values.tasks)
        notes.checked = Boolean(values.notes)
        messages.checked = Boolean(values.messages)
        activity.checked = Boolean(values.activity)
        workHours.checked = Boolean(values.work_hours)
        loadingValues = false
    }

    function updateValues() {
        if (!root.managed || loadingValues)
            return
        configurationController.update_page("cache", formValues())
    }

    Component.onCompleted: syncValues()

    Connections {
        target: configurationController

        function onSessionStarted() {
            root.syncValues()
        }

        function onPageReset(pageId) {
            if (pageId === "cache")
                root.syncValues()
        }
    }

    ScrollView {
        id: cacheScroll
        objectName: "cacheScrollView"
        anchors.fill: parent
        contentWidth: availableWidth
        contentHeight: cacheContent.implicitHeight + 40
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        ScrollBar.vertical: Controls.ScrollBar {
            objectName: "cacheScrollBar"
            theme: root.theme
            flickableTarget: cacheScroll
        }

        ColumnLayout {
            id: cacheContent
            x: 22
            y: 20
            width: Math.max(0, cacheScroll.availableWidth - 44)
            spacing: 14

            ConfigurationSection {
                Layout.fillWidth: true
                theme: root.theme
                title: qsTr("Workspace cache")
                description: qsTr("Control saved Search Tab layout separately from cached server records.")
                iconName: "cached"

                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Cache process tabs")
                    description: qsTr("Restore search process tabs from the persistent cache instead of rebuilding every tab during startup.")
                    Controls.Switch {
                        id: cacheProcessTabs
                        theme: root.theme
                        text: ""
                        onToggled: root.updateValues()
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Clear tabs cache")
                    description: qsTr("Discard cached search tabs and rebuild them from current project data on the next load.")
                    showDivider: false
                    Controls.Button {
                        theme: root.theme
                        text: qsTr("Clear")
                        flat: true
                        icon.name: "delete_sweep"
                        onClicked: configurationController.flush_search_cache()
                    }
                }
            }

            ConfigurationSection {
                Layout.fillWidth: true
                theme: root.theme
                title: qsTr("Cached server data")
                description: qsTr("Choose which unchanged TACTIC data may be restored locally. Refresh actions always bypass these caches.")
                iconName: "cached"

                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Projects and reference data")
                    description: qsTr("Projects, Search Types, pipelines, processes, statuses, users, groups and tags.")
                    Controls.Switch {
                        id: referenceData
                        theme: root.theme
                        text: ""
                        onToggled: root.updateValues()
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Search results and sObjects")
                    description: qsTr("Ordered search pages and unchanged object fields used by Search Tabs.")
                    Controls.Switch {
                        id: searchResults
                        theme: root.theme
                        text: ""
                        onToggled: root.updateValues()
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Snapshots and files")
                    description: qsTr("Snapshot and file metadata. Repository files remain managed by Repository Sync.")
                    Controls.Switch {
                        id: snapshotsFiles
                        theme: root.theme
                        text: ""
                        onToggled: root.updateValues()
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Children and relations")
                    description: qsTr("Expanded child branches and linked-object membership.")
                    Controls.Switch {
                        id: relations
                        theme: root.theme
                        text: ""
                        onToggled: root.updateValues()
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Tasks")
                    description: qsTr("Task Manager scopes, pages and task metadata.")
                    Controls.Switch {
                        id: tasks
                        theme: root.theme
                        text: ""
                        onToggled: root.updateValues()
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Notes")
                    description: qsTr("Object and process note histories with attachment metadata.")
                    Controls.Switch {
                        id: notes
                        theme: root.theme
                        text: ""
                        onToggled: root.updateValues()
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Messages")
                    description: qsTr("A bounded set of recent conversation histories and attachment metadata.")
                    Controls.Switch {
                        id: messages
                        theme: root.theme
                        text: ""
                        onToggled: root.updateValues()
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Activity Feed")
                    description: qsTr("Recent activity pages and complete calendar day counts.")
                    Controls.Switch {
                        id: activity
                        theme: root.theme
                        text: ""
                        onToggled: root.updateValues()
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Work hours")
                    description: qsTr("Timesheet and report query results for previously opened ranges.")
                    showDivider: false
                    Controls.Switch {
                        id: workHours
                        theme: root.theme
                        text: ""
                        onToggled: root.updateValues()
                    }
                }
            }

            ConfigurationSection {
                Layout.fillWidth: true
                theme: root.theme
                title: qsTr("Cache maintenance")
                description: qsTr("Clearing raises the cache generation first, so an older background request cannot restore cleared data.")
                iconName: "delete-sweep"

                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Clear all cached server data")
                    description: qsTr("Search tabs will keep their layout, but server records will be loaded again when needed.")
                    showDivider: false
                    Controls.Button {
                        theme: root.theme
                        text: serverCacheController.busy
                            ? qsTr("Clearing…") : qsTr("Clear cache")
                        destructive: true
                        flat: true
                        enabled: !serverCacheController.busy
                        onClicked: clearConfirmation.open()
                    }
                }
            }

            Label {
                visible: serverCacheController.message.length > 0
                Layout.fillWidth: true
                text: serverCacheController.message
                color: root.theme.secondaryText
                font.pointSize: Controls.Typography.label
                wrapMode: Text.WordWrap
            }

            Item { Layout.preferredHeight: 8 }
        }
    }

    Controls.Dialog {
        id: clearConfirmation
        theme: root.theme
        anchors.centerIn: parent
        width: Math.max(280, Math.min(460, root.width - 40))
        modal: true
        padding: 22

        contentItem: ColumnLayout {
            spacing: 8
            Label {
                Layout.fillWidth: true
                text: qsTr("Clear cached server data?")
                color: root.theme.primaryText
                font.pixelSize: 16
                font.weight: Font.DemiBold
            }
            Label {
                Layout.fillWidth: true
                text: qsTr("Projects, Search Types, users, search results, tasks, notes, messages and activity will be downloaded again when requested.")
                color: root.theme.secondaryText
                wrapMode: Text.WordWrap
            }
        }

        footer: DialogButtonBox {
            leftPadding: 14
            rightPadding: 14
            bottomPadding: 14
            background: Item {}
            Controls.Button {
                theme: root.theme
                text: qsTr("Cancel")
                flat: true
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
                onClicked: clearConfirmation.close()
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Clear cache")
                destructive: true
                DialogButtonBox.buttonRole: DialogButtonBox.DestructiveRole
                onClicked: {
                    clearConfirmation.close()
                    configurationController.clear_data_cache()
                }
            }
        }
    }
}

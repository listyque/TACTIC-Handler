import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls
Item {
    id: root
    required property var theme
    property bool managed: false
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
            "quickViewMode": defaultQuickView.currentValue || "cards",
            "workspaceSurface": defaultTaskSurface.currentValue || "quick",
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
        defaultQuickView.currentIndex = choiceIndex(
            defaultQuickView.model, values.quickViewMode
        )
        defaultTaskSurface.currentIndex = choiceIndex(
            defaultTaskSurface.model, values.workspaceSurface
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
        if (!root.managed || loadingValues)
            return
        configurationController.update_page(
            "tasks_preferences", formValues()
        )
    }

    Component.onCompleted: syncValues()

    Connections {
        target: configurationController

        function onSessionStarted() {
            root.syncValues()
        }

        function onPageReset(pageId) {
            if (pageId === "tasks_preferences")
                root.syncValues()
        }
    }

    ListModel { id: taskColumnSettings }

    ScrollView {
        id: taskPreferencesScroll
        anchors.fill: parent
        contentWidth: availableWidth
        contentHeight: taskPreferencesContent.implicitHeight + 40
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        ScrollBar.vertical: Controls.ScrollBar {
            theme: root.theme
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
                theme: root.theme
                title: qsTr("Task workspace defaults")
                description: qsTr("Initial task surface, presentation, ordering and grouping.")
                iconName: "tasks"

                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Initial task surface")
                    description: qsTr("Open Quick Tasks or the detailed Task Browser first.")
                    Controls.ComboBox {
                        id: defaultTaskSurface
                        objectName: "taskPreferencesSurfaceCombo"
                        theme: root.theme
                        Layout.preferredWidth: 200
                        model: [
                            {"label": qsTr("Quick Tasks"), "value": "quick"},
                            {"label": qsTr("Task Browser"), "value": "browser"}
                        ]
                        textRole: "label"
                        valueRole: "value"
                        onActivated: root.updateValues()
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Quick Tasks presentation")
                    description: qsTr("Show editable process cards or a compact task list.")
                    Controls.ComboBox {
                        id: defaultQuickView
                        objectName: "taskPreferencesQuickViewCombo"
                        theme: root.theme
                        Layout.preferredWidth: 200
                        model: [
                            {"label": qsTr("Cards"), "value": "cards"},
                            {"label": qsTr("Compact list"), "value": "compact"}
                        ]
                        textRole: "label"
                        valueRole: "value"
                        onActivated: root.updateValues()
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Initial view")
                    description: qsTr("View opened first when Task Browser has no saved local state.")
                    Controls.ComboBox {
                        id: defaultTaskView
                        theme: root.theme
                        Layout.preferredWidth: 200
                        model: [
                            {"label": qsTr("Table"), "value": "list"},
                            {"label": qsTr("Gantt"), "value": "gantt"}
                        ]
                        textRole: "label"
                        valueRole: "value"
                        onActivated: root.updateValues()
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Initial sorting")
                    description: qsTr("Default order used before the user applies a table or column sort.")
                    Controls.ComboBox {
                        id: defaultTaskSort
                        theme: root.theme
                        Layout.preferredWidth: 220
                        model: [
                            {"label": qsTr("Deadline"), "value": "due"},
                            {"label": qsTr("Recently changed"), "value": "recent"},
                            {"label": qsTr("Process"), "value": "process"},
                            {"label": qsTr("Assignee"), "value": "user"},
                            {"label": qsTr("Status"), "value": "status"},
                            {"label": qsTr("Parent object"), "value": "object"},
                            {"label": qsTr("Priority"), "value": "priority"},
                            {"label": qsTr("Milestone"), "value": "milestone"},
                            {"label": qsTr("Supervisor"), "value": "supervisor"}
                        ]
                        textRole: "label"
                        valueRole: "value"
                        onActivated: root.updateValues()
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Initial grouping")
                    description: qsTr("Default group structure used when Task Browser is opened.")
                    Controls.ComboBox {
                        id: defaultTaskGroup
                        theme: root.theme
                        Layout.preferredWidth: 220
                        model: [
                            {"label": qsTr("By Process"), "value": "process"},
                            {"label": qsTr("By Status"), "value": "status"},
                            {"label": qsTr("By Assignee"), "value": "user"},
                            {"label": qsTr("By Parent Object"), "value": "object"},
                            {"label": qsTr("By Project"), "value": "project"},
                            {"label": qsTr("By Search Type"), "value": "search_type"},
                            {"label": qsTr("No Groups"), "value": "none"}
                        ]
                        textRole: "label"
                        valueRole: "value"
                        onActivated: root.updateValues()
                    }
                }
                Controls.SettingsRow {
                    theme: root.theme
                    title: qsTr("Task Inspector expanded")
                    description: qsTr("Open Task Inspector in its expanded state when no saved dock state exists.")
                    showDivider: false
                    Controls.Switch {
                        id: inspectorExpanded
                        theme: root.theme
                        text: ""
                        onToggled: root.updateValues()
                    }
                }
            }

            ConfigurationSection {
                Layout.fillWidth: true
                theme: root.theme
                title: qsTr("Task table columns")
                description: qsTr("Choose visible columns, their width and display order. Object remains visible.")
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
                        radius: root.theme.itemRadius
                        color: root.theme.surfaceContainerHigh

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 8
                            anchors.rightMargin: 6
                            spacing: 7

                            Controls.CheckBox {
                                theme: root.theme
                                checked: taskColumnRow.columnVisible
                                enabled: !taskColumnRow.required
                                onToggled: {
                                    if (root.loadingValues)
                                        return
                                    taskColumnSettings.setProperty(
                                        taskColumnRow.index,
                                        "columnVisible", checked
                                    )
                                    root.updateValues()
                                }
                            }
                            Label {
                                Layout.fillWidth: true
                                text: taskColumnRow.label
                                color: root.theme.primaryText
                                font.pointSize: Controls.Typography.body
                                elide: Text.ElideRight
                            }
                            Controls.SpinBox {
                                theme: root.theme
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
                                    root.updateValues()
                                }
                            }
                            Controls.CompactIconButton {
                                theme: root.theme
                                iconName: "arrow_upward"
                                toolTip: qsTr("Move column left")
                                enabled: taskColumnRow.index > 0
                                onClicked: {
                                    taskColumnSettings.move(
                                        taskColumnRow.index,
                                        taskColumnRow.index - 1, 1
                                    )
                                    root.updateValues()
                                }
                            }
                            Controls.CompactIconButton {
                                theme: root.theme
                                iconName: "arrow_downward"
                                toolTip: qsTr("Move column right")
                                enabled: taskColumnRow.index
                                    < taskColumnSettings.count - 1
                                onClicked: {
                                    taskColumnSettings.move(
                                        taskColumnRow.index,
                                        taskColumnRow.index + 1, 1
                                    )
                                    root.updateValues()
                                }
                            }
                        }
                    }
                }
            }

            Label {
                Layout.fillWidth: true
                text: qsTr("Dock and window geometry is restored separately for each workspace. Task scope, filters, collapsed groups, calendar position and the selected task resume separately for each project. Checked tasks and unsaved edits are never restored.")
                color: root.theme.secondaryText
                font.pointSize: Controls.Typography.label
                wrapMode: Text.WordWrap
            }

            Item { Layout.preferredHeight: 8 }
        }
    }
}

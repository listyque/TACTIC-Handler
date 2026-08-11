import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    required property var theme
    property bool embedded: false
    readonly property bool narrowToolbar: width < 900
    readonly property bool compactScopeControls: root.embedded && width < 1280
    readonly property bool minimalToolbar: root.embedded && width < 520
    readonly property bool directGroupVisible:
        !root.embedded || root.width >= 720
    readonly property bool directSortVisible:
        !root.embedded || root.width >= 1180
    readonly property bool workspaceOverflowRequired:
        root.embedded && (!root.directSortVisible
            || !root.directGroupVisible || root.minimalToolbar)

    function searchTypeScopeLabel() {
        const name = String(tasksController.searchTypeScopeName || "")
        return name.length > 0
            ? qsTr("All") + " " + name
            : qsTr("Search Type")
    }

    function scopeLabel() {
        if (tasksController.advancedScope === "multiple")
            return qsTr("Selected").toUpperCase()
        if (tasksController.advancedScope === "object")
            return qsTr("Selected").toUpperCase()
        if (tasksController.advancedScope === "search_type")
            return root.searchTypeScopeLabel()
        if (tasksController.advancedScope === "user")
            return tasksController.personalScope
                ? qsTr("My Tasks").toUpperCase()
                : qsTr("User").toUpperCase()
        if (tasksController.advancedScope === "project")
            return qsTr("Project").toUpperCase()
        if (tasksController.advancedScope === "team")
            return qsTr("Team").toUpperCase()
        return qsTr("Object").toUpperCase()
    }

    function scopeIcon() {
        if (tasksController.advancedScope === "multiple")
            return "select_all"
        if (tasksController.advancedScope === "search_type")
            return "table_view"
        if (tasksController.advancedScope === "user")
            return "person"
        if (tasksController.advancedScope === "project")
            return "workspaces"
        if (tasksController.advancedScope === "team")
            return "group"
        return "inventory_2"
    }

    function objectScopeLabel() {
        return qsTr("Selected").toUpperCase()
    }

    function objectScopeIcon() {
        return tasksController.advancedScope === "multiple"
            ? "select_all" : "inventory_2"
    }

    function scopeMenuActions() {
        const actions = [
            {"title": "Selected",
             "icon": root.objectScopeIcon(), "command": "object",
             "checked": tasksController.advancedScope === "object"
                || tasksController.advancedScope === "multiple"},
            {"title": root.searchTypeScopeLabel(), "translate": false,
             "icon": "table_view", "command": "search_type",
             "enabled": tasksController.searchTypeScopeAvailable,
             "checked": tasksController.advancedScope === "search_type"},
            {"title": "Project tasks", "icon": "workspaces", "command": "project",
             "checked": tasksController.advancedScope === "project"},
            {"title": "Teams", "icon": "group", "command": "teams",
             "checked": tasksController.advancedScope === "team"},
            {"title": "My tasks", "icon": "person", "command": "my_tasks",
             "checked": tasksController.personalScope}
        ]
        return actions
    }

    function choiceIndex(values, selected) {
        for (let index = 0; index < values.length; ++index) {
            if (String(values[index].value || "") === String(selected || ""))
                return index
        }
        return -1
    }

    function teamMenuActions() {
        const actions = [{"header": true, "title": "TACTIC teams"}]
        const teams = tasksController.teamOptions
        if (teams.length === 0) {
            actions.push({
                "title": "No team scopes available",
                "status": "Team membership comes from TACTIC login groups",
                "icon": "group",
                "enabled": false
            })
            return actions
        }
        for (let index = 0; index < teams.length; ++index) {
            const team = teams[index]
            actions.push({
                "title": team.label,
                "status": team.members + (team.members === 1
                    ? " member" : " members"),
                "icon": "group",
                "command": "team:" + team.value,
                "checked": tasksController.advancedScope === "team"
                    && tasksController.advancedUser === team.value
            })
        }
        return actions
    }

    function workspaceMenuActions() {
        const actions = [
            {"header": true, "title": "Task actions"},
            {"title": "Quick task editor", "icon": "view_agenda",
             "command": "quick"},
            {"title": "Quick filters", "icon": "filter_alt",
             "command": "filters"},
            {"separator": true},
            {"header": true, "title": "Sort"}
        ]
        const sortOptions = tasksController.sortOptions
        for (let index = 0; index < sortOptions.length; ++index) {
            const option = sortOptions[index]
            actions.push({
                "title": option.label,
                "icon": "sort",
                "command": "sort:" + option.value,
                "checked": tasksController.sortMode === option.value
            })
        }
        actions.push({"separator": true})
        actions.push({"header": true, "title": "Group"})
        const groupOptions = tasksController.groupOptions
        for (let groupIndex = 0;
                groupIndex < groupOptions.length; ++groupIndex) {
            const group = groupOptions[groupIndex]
            actions.push({
                "title": group.label,
                "icon": "layers",
                "command": "group:" + group.value,
                "checked": tasksController.groupMode === group.value
            })
        }
        actions.push({"separator": true})
        actions.push({
            "title": "Clear filters",
            "icon": "filter_alt_off",
            "command": "clear"
        })
        return actions
    }

    function columnMenuActions() {
        const actions = [{"header": true, "title": qsTr("Visible columns")}]
        const columns = tasksController.taskColumns || []
        for (let index = 0; index < columns.length; ++index) {
            const column = columns[index]
            actions.push({
                "title": qsTr(column.label),
                "icon": column.visible ? "visibility" : "visibility_off",
                "command": "column:" + column.key,
                "checked": Boolean(column.visible),
                "enabled": !Boolean(column.required),
                "status": column.required ? qsTr("Always visible") : ""
            })
        }
        actions.push({"separator": true})
        actions.push({
            "title": qsTr("Configure columns"),
            "icon": "view_column",
            "command": "configure"
        })
        return actions
    }

    function ganttPreviewActions() {
        const actions = [{"header": true, "title": "Pending Gantt changes"}]
        const changes = tasksController.ganttChangePreview
        for (let index = 0; index < changes.length; ++index) {
            const change = changes[index]
            actions.push({
                "title": change.title + " · " + change.process,
                "status": change.start.slice(0, 10) + " — "
                    + change.end.slice(0, 10) + " · "
                    + change.progress + "%",
                "icon": "schedule",
                "enabled": false
            })
        }
        return actions
    }

    Rectangle {
        anchors.fill: parent
        color: root.theme.workspace
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.leftMargin: root.embedded ? 0 : 10
        anchors.rightMargin: root.embedded ? 0 : 10
        anchors.topMargin: root.embedded ? 0 : 10
        anchors.bottomMargin: root.embedded ? 0 : 10
        spacing: root.embedded ? 5 : 7

        Rectangle {
            visible: !root.embedded
            Layout.fillWidth: true
            Layout.preferredHeight: visible ? 48 : 0
            radius: root.theme.surfaceRadius
            color: root.theme.surfaceContainerLow

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 8
                spacing: 7

                MaterialIcon {
                    name: "tasks"
                    size: 19
                    color: root.theme.action
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 0
                    Label {
                        Layout.fillWidth: true
                        text: tasksController.advancedTitle
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 11
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                    }
                    Label {
                        Layout.fillWidth: true
                        text: tasksController.advancedLoadedCount
                            + qsTr(" loaded tasks")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 8
                        elide: Text.ElideRight
                    }
                }
                Md3Button {
                    theme: root.theme
                    text: root.objectScopeLabel()
                    icon.name: root.objectScopeIcon()
                    tonal: tasksController.advancedScope === "object"
                        || tasksController.advancedScope === "multiple"
                    onClicked: tasksController.use_current_object()
                }
                Md3Button {
                    theme: root.theme
                    text: qsTr("MY TASKS")
                    icon.name: "person"
                    tonal: tasksController.personalScope
                    onClicked: tasksController.open_for_user("")
                }
                Md3Button {
                    theme: root.theme
                    text: qsTr("PROJECT")
                    icon.name: "workspaces"
                    tonal: tasksController.advancedScope === "project"
                    onClicked: tasksController.use_project()
                }
                CompactIconButton {
                    id: teamScopeButton
                    theme: root.theme
                    iconName: "group"
                    toolTip: tasksController.teamOptions.length > 0
                        ? qsTr("Open a team task scope")
                        : qsTr("No team scopes are available from your TACTIC login groups")
                    elevated: tasksController.advancedScope === "team"
                    onClicked: teamScopeMenu.toggleBelow(teamScopeButton)
                }
                RefreshIconButton {
                    theme: root.theme
                    toolTip: qsTr("Refresh tasks")
                    enabled: !tasksController.advancedBusy
                        && !tasksController.advancedSaving
                        && tasksController.advancedDirtyCount === 0
                    onClicked: tasksController.refresh_advanced()
                }
            }
        }

        TaskWorkspaceSummary {
            visible: !root.embedded
            Layout.fillWidth: true
            Layout.preferredHeight: visible ? implicitHeight : 0
            theme: root.theme
        }

        Rectangle {
            objectName: "taskWorkspaceToolbar"
            Layout.fillWidth: true
            Layout.preferredHeight: root.embedded
                ? root.theme.dockWorkspaceHeaderHeight
                    - root.theme.dockTitleHeight
                : 42
            radius: root.embedded ? 0 : root.theme.surfaceRadius
            color: root.embedded
                ? root.theme.toolBar : root.theme.surfaceContainerLow

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: root.embedded ? 10 : 8
                anchors.rightMargin: root.embedded ? 7 : 8
                anchors.bottomMargin: root.embedded ? 1 : 0
                spacing: root.embedded ? 4 : 6

                Md3FilledActionButton {
                    id: taskCreateButton
                    objectName: "taskWorkspaceCreateButton"
                    theme: root.theme
                    Layout.preferredWidth: root.theme.controlHeight
                    Layout.minimumWidth: root.theme.controlHeight
                    Layout.maximumWidth: root.theme.controlHeight
                    Layout.preferredHeight: root.theme.controlHeight
                    compact: true
                    iconName: "add"
                    toolTip: tasksController.canCreateAdvancedTask
                        ? qsTr("Create a task for the selected sObject")
                        : qsTr("Select an sObject with a task process first")
                    enabled: tasksController.canCreateAdvancedTask
                        && !tasksController.advancedBusy
                        && !tasksController.advancedSaving
                    onClicked: tasksController.create_advanced_task_draft()
                }
                CompactIconButton {
                    id: milestoneManagerButton
                    objectName: "taskMilestoneManagerButton"
                    theme: root.theme
                    Layout.preferredWidth: root.theme.controlHeight
                    Layout.minimumWidth: root.theme.controlHeight
                    Layout.maximumWidth: root.theme.controlHeight
                    Layout.preferredHeight: root.theme.controlHeight
                    iconName: "milestone"
                    iconColor: root.theme.action
                    backgroundColor: root.theme.surfaceContainerHigh
                    toolTip: qsTr("Manage milestones")
                    onClicked: milestoneController.open_manager()
                }
                Md3TextField {
                    id: taskSearchField
                    objectName: "taskWorkspaceSearchField"
                    theme: root.theme
                    Layout.fillWidth: true
                    Layout.minimumWidth: root.minimalToolbar
                        ? 90 : root.embedded ? 120 : 180
                    Layout.preferredHeight: root.theme.controlHeight
                    placeholderText: qsTr("Search tasks")
                    onTextEdited: tasksController.set_filter("text", text)
                }
                CompactIconButton {
                    id: quickFilterButton
                    objectName: "taskWorkspaceQuickFilterButton"
                    visible: !root.minimalToolbar
                    theme: root.theme
                    Layout.preferredWidth: visible
                        ? root.theme.controlHeight : 0
                    Layout.preferredHeight: root.theme.controlHeight
                    iconName: "filter_alt"
                    badgeCount: tasksController.activeQuickFilterCount
                    toolTip: qsTr("Quick task filters")
                    backgroundColor: root.theme.surfaceContainerHigh
                    onPressed: quickFilterPopup.sourceWasOpen
                        = quickFilterPopup.opened
                    onClicked: quickFilterPopup.toggleBelow(quickFilterButton)
                }
                Md3SegmentedButton {
                    id: embeddedScopeSwitcher
                    objectName: "embeddedScopeSwitcher"
                    visible: root.embedded && !root.compactScopeControls
                    Layout.preferredWidth: 560
                    Layout.minimumWidth: 460
                    Layout.preferredHeight: root.theme.controlHeight
                    Layout.alignment: Qt.AlignVCenter
                    theme: root.theme
                    segmentWidth: 108
                    minimumSegmentWidth: 88
                    model: [
                        {"label": "Selected",
                         "icon": root.objectScopeIcon(),
                         "value": "object"},
                        {"label": root.searchTypeScopeLabel(),
                         "translate": false,
                         "icon": "table_view", "value": "search_type",
                         "enabled": tasksController.searchTypeScopeAvailable},
                        {"label": "Project", "icon": "workspaces",
                         "value": "project"},
                        {"label": "Teams", "icon": "group",
                         "value": "team", "reselectable": true},
                        {"label": "My Tasks", "icon": "person",
                         "value": "my_tasks"}
                    ]
                    currentValue: tasksController.personalScope
                        ? "my_tasks"
                        : tasksController.advancedScope === "object"
                            ? "object"
                        : tasksController.advancedScope === "multiple"
                            ? "object"
                            : tasksController.advancedScope === "search_type"
                                ? "search_type"
                            : tasksController.advancedScope === "project"
                                ? "project"
                                : tasksController.advancedScope === "team"
                                    ? "team" : ""
                    onActivated: function(value) {
                        if (value === "object")
                            tasksController.use_current_object()
                        else if (value === "search_type")
                            tasksController.use_current_search_type()
                        else if (value === "project")
                            tasksController.use_project()
                        else if (value === "team")
                            teamScopeMenu.toggleBelow(embeddedScopeSwitcher)
                        else if (value === "my_tasks")
                            tasksController.open_for_user("")
                    }
                }
                Md3Button {
                    id: embeddedScopeButton
                    objectName: "embeddedScopeButton"
                    visible: root.compactScopeControls
                        && !root.minimalToolbar
                    theme: root.theme
                    text: root.scopeLabel()
                    icon.name: root.scopeIcon()
                    tonal: true
                    Layout.preferredHeight: root.theme.controlHeight
                    onClicked: scopeMenu.toggleBelow(embeddedScopeButton)
                }
                CompactIconButton {
                    id: compactScopeButton
                    objectName: "compactScopeButton"
                    visible: root.minimalToolbar
                    theme: root.theme
                    Layout.preferredWidth: visible
                        ? root.theme.controlHeight : 0
                    Layout.preferredHeight: root.theme.controlHeight
                    iconName: root.scopeIcon()
                    elevated: true
                    toolTip: qsTr("Task scope: ") + root.scopeLabel()
                    onClicked: scopeMenu.toggleBelow(compactScopeButton)
                }
                Md3ComboBox {
                    id: taskSortModeCombo
                    objectName: "taskSortModeCombo"
                    visible: root.directSortVisible
                    theme: root.theme
                    Layout.preferredWidth: visible ? 132 : 0
                    Layout.preferredHeight: root.theme.controlHeight
                    Layout.alignment: Qt.AlignVCenter
                    model: tasksController.sortOptions
                    textRole: "label"
                    displayText: currentIndex >= 0
                        ? qsTr("Sort: %1").arg(qsTr(currentText))
                        : qsTr("Sort tasks")
                    currentIndex: root.choiceIndex(
                        tasksController.sortOptions,
                        tasksController.sortMode
                    )
                    leadingIcon: "sort"
                    onActivated: tasksController.set_sort_mode(
                        tasksController.sortOptions[index].value
                    )
                }
                Md3ComboBox {
                    id: taskGroupModeCombo
                    objectName: "taskGroupModeCombo"
                    visible: root.directGroupVisible
                    theme: root.theme
                    Layout.preferredWidth: visible ? 148 : 0
                    Layout.preferredHeight: root.theme.controlHeight
                    Layout.alignment: Qt.AlignVCenter
                    model: tasksController.groupOptions
                    textRole: "label"
                    currentIndex: root.choiceIndex(
                        tasksController.groupOptions,
                        tasksController.groupMode
                    )
                    leadingIcon: "layers"
                    onActivated: tasksController.set_group_mode(
                        tasksController.groupOptions[index].value
                    )
                }
                CompactIconButton {
                    id: quickWorkspaceButton
                    objectName: "taskQuickWorkspaceButton"
                    visible: !root.minimalToolbar
                    theme: root.theme
                    Layout.preferredWidth: visible
                        ? root.theme.controlHeight : 0
                    Layout.preferredHeight: root.theme.controlHeight
                    iconName: "view_agenda"
                    iconSize: 17
                    toolTip: qsTr("Open quick task editor")
                    onClicked: tasksController.open_quick_workspace()
                }
                CompactIconButton {
                    id: clearTaskFiltersButton
                    objectName: "taskWorkspaceClearFiltersButton"
                    theme: root.theme
                    Layout.preferredWidth: root.theme.controlHeight
                    Layout.preferredHeight: root.theme.controlHeight
                    iconName: "filter_alt_off"
                    iconSize: 17
                    toolTip: qsTr("Clear task filters")
                    enabled: tasksController.advancedFiltersActive
                    onClicked: {
                        taskSearchField.clear()
                        tasksController.clear_filters()
                    }
                }
                CompactIconButton {
                    id: taskColumnsButton
                    objectName: "taskWorkspaceColumnsButton"
                    theme: root.theme
                    Layout.preferredWidth: root.theme.controlHeight
                    Layout.preferredHeight: root.theme.controlHeight
                    iconName: "view_column"
                    iconSize: 17
                    toolTip: qsTr("Choose visible task columns")
                    onPressed: taskColumnsMenu.sourceWasOpen
                        = taskColumnsMenu.opened
                    onClicked: taskColumnsMenu.toggleBelow(taskColumnsButton)
                }
                RefreshIconButton {
                    id: taskRefreshButton
                    objectName: "taskWorkspaceRefreshButton"
                    theme: root.theme
                    Layout.preferredWidth: 38
                    Layout.preferredHeight: 38
                    toolTip: qsTr("Refresh tasks")
                    enabled: !tasksController.advancedBusy
                        && !tasksController.advancedSaving
                        && tasksController.advancedDirtyCount === 0
                    onClicked: tasksController.refresh_advanced()
                }
                CompactIconButton {
                    id: taskWorkspaceMenuButton
                    objectName: "taskWorkspaceOverflowButton"
                    visible: root.workspaceOverflowRequired
                    theme: root.theme
                    iconName: "more_vert"
                    toolTip: qsTr("Task view, sorting and grouping")
                    onPressed: taskWorkspaceMenu.sourceWasOpen
                        = taskWorkspaceMenu.opened
                    onClicked: taskWorkspaceMenu.toggleBelow(
                        taskWorkspaceMenuButton
                    )
                }

            }

            Rectangle {
                visible: root.embedded
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 1
                color: root.theme.separator
            }
        }

        Rectangle {
            Layout.leftMargin: root.embedded ? 6 : 0
            Layout.rightMargin: root.embedded ? 6 : 0
            Layout.fillWidth: true
            Layout.preferredHeight: visible ? 34 : 0
            visible: tasksController.activeQuickFilterCount > 0
            radius: root.theme.itemRadius
            color: root.theme.surfaceContainerLow

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 9
                anchors.rightMargin: 5
                spacing: 7
                Label {
                    text: qsTr("ACTIVE FILTERS")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 8
                    font.weight: Font.DemiBold
                }
                Flickable {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    contentWidth: activeFilterRow.width
                    contentHeight: height
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds

                    Row {
                        id: activeFilterRow
                        height: parent.height
                        spacing: 5
                        Repeater {
                            model: tasksController.activeQuickFilters
                            delegate: QuickFilterChip {
                                required property var modelData
                                anchors.verticalCenter: parent.verticalCenter
                                theme: root.theme
                                height: 25
                                maximumChipWidth: 150
                                text: modelData.title
                                checked: true
                                accent: modelData.accent
                                    ? modelData.accent : root.theme.action
                                onClicked: tasksController.toggle_quick_filter(
                                    modelData.group, modelData.key
                                )
                            }
                        }
                    }
                }
                CompactIconButton {
                    theme: root.theme
                    iconName: "close"
                    toolTip: qsTr("Clear quick filters")
                    onClicked: tasksController.clear_quick_filters()
                }
            }
        }

        Rectangle {
            Layout.leftMargin: root.embedded ? 6 : 0
            Layout.rightMargin: root.embedded ? 6 : 0
            Layout.fillWidth: true
            Layout.preferredHeight: visible ? 42 : 0
            visible: tasksController.advancedDirtyCount > 0
            radius: root.theme.surfaceRadius
            color: root.theme.secondaryContainer

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 8
                spacing: 8
                MaterialIcon {
                    name: "edit"
                    size: 16
                    color: root.theme.action
                }
                Label {
                    Layout.fillWidth: true
                    text: tasksController.advancedDirtyCount
                        + (tasksController.advancedDirtyCount === 1
                            ? qsTr(" task has unsaved changes")
                            : qsTr(" tasks have unsaved changes"))
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 9
                }
                CompactIconButton {
                    id: ganttPreviewButton
                    visible: tasksController.viewMode === "gantt"
                        && tasksController.ganttChangePreview.length > 0
                    theme: root.theme
                    iconName: "visibility"
                    toolTip: qsTr("Preview Gantt changes")
                    onClicked: ganttPreviewMenu.toggleBelow(
                        ganttPreviewButton
                    )
                }
                Md3Button {
                    theme: root.theme
                    text: qsTr("DISCARD")
                    enabled: !tasksController.advancedSaving
                    onClicked: tasksController.discard_advanced_changes()
                }
                Md3Button {
                    theme: root.theme
                    text: tasksController.advancedSaving
                        ? qsTr("SAVING") : qsTr("SAVE")
                    icon.name: "save"
                    highlighted: true
                    enabled: !tasksController.advancedSaving
                    onClicked: tasksController.save_advanced_changes()
                }
            }
        }

        TaskBrowserTable {
            visible: tasksController.viewMode === "list"
            Layout.leftMargin: root.embedded ? 6 : 0
            Layout.rightMargin: root.embedded ? 6 : 0
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            Layout.fillHeight: visible
            theme: root.theme
            footerHorizontalOverflow: root.embedded ? 6 : 0
        }

        TaskGanttView {
            visible: tasksController.viewMode === "gantt"
            Layout.leftMargin: root.embedded ? 6 : 0
            Layout.rightMargin: root.embedded ? 6 : 0
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            Layout.fillHeight: visible
            theme: root.theme
            footerHorizontalOverflow: root.embedded ? 6 : 0
        }

        Rectangle {
            Layout.leftMargin: root.embedded ? 6 : 0
            Layout.rightMargin: root.embedded ? 6 : 0
            Layout.fillWidth: true
            Layout.preferredHeight: visible ? Math.max(34, errorLabel.implicitHeight + 14) : 0
            visible: tasksController.advancedError.length > 0
            radius: root.theme.itemRadius
            color: root.theme.errorContainer
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 6
                spacing: 7
                MaterialIcon {
                    name: "error"
                    size: 16
                    color: root.theme.error
                }
                Label {
                    id: errorLabel
                    Layout.fillWidth: true
                    text: tasksController.advancedError
                    color: root.theme.primaryText
                    wrapMode: Text.WordWrap
                    font.family: root.theme.fontFamily
                    font.pixelSize: 9
                }
                CompactIconButton {
                    theme: root.theme
                    iconName: "close"
                    toolTip: qsTr("Dismiss error")
                    onClicked: tasksController.clear_advanced_error()
                }
            }
        }
    }

    TaskQuickFilterPopup {
        id: quickFilterPopup
        theme: root.theme
    }

    ActionMenu {
        id: scopeMenu
        parent: Overlay.overlay
        theme: root.theme
        preferredWidth: 280
        actions: root.scopeMenuActions()
        onTriggered: command => {
            if (command === "object")
                tasksController.use_current_object()
            else if (command === "search_type")
                tasksController.use_current_search_type()
            else if (command === "my_tasks")
                tasksController.open_for_user("")
            else if (command === "project")
                tasksController.use_project()
            else if (command === "teams") {
                const anchor = embeddedScopeButton.visible
                    ? embeddedScopeButton : compactScopeButton
                teamScopeMenu.toggleBelow(anchor)
            }
            else if (command.indexOf("team:") === 0)
                tasksController.open_for_team(command.slice(5))
        }
    }

    TaskWorkspaceModeSwitcher {
        id: workspaceModeSwitcher
        objectName: "taskWorkspaceModeSwitcher"
        z: 50
        visible: root.width >= 380
            && (tasksController.viewMode === "list"
                || tasksController.viewMode === "gantt")
        anchors.right: parent.right
        anchors.rightMargin: root.embedded ? 8 : 18
        anchors.bottom: parent.bottom
        anchors.bottomMargin: (root.embedded ? 0 : 10)
            + Math.max(0,
                (root.theme.dockWorkspaceFooterHeight - height) / 2)
        theme: root.theme
    }

    ActionMenu {
        id: teamScopeMenu
        parent: Overlay.overlay
        theme: root.theme
        preferredWidth: 310
        actions: root.teamMenuActions()
        onTriggered: command => {
            if (command.indexOf("team:") === 0)
                tasksController.open_for_team(command.slice(5))
        }
    }

    ActionMenu {
        id: taskWorkspaceMenu
        parent: Overlay.overlay
        theme: root.theme
        preferredWidth: 250
        actions: root.workspaceMenuActions()
        onTriggered: command => {
            if (command === "quick")
                tasksController.open_quick_workspace()
            else if (command === "filters")
                quickFilterPopup.toggleBelow(taskWorkspaceMenuButton)
            else if (command.indexOf("sort:") === 0)
                tasksController.set_sort_mode(command.slice(5))
            else if (command.indexOf("group:") === 0)
                tasksController.set_group_mode(command.slice(6))
            else if (command === "clear") {
                taskSearchField.clear()
                tasksController.clear_filters()
            }
        }
    }

    ActionMenu {
        id: taskColumnsMenu
        parent: Overlay.overlay
        theme: root.theme
        preferredWidth: 270
        actions: root.columnMenuActions()
        onTriggered: command => {
            if (command.indexOf("column:") === 0)
                tasksController.toggle_task_column(command.slice(7))
            else if (command === "configure")
                appController.invoke("open_configuration")
        }
    }

    ActionMenu {
        id: ganttPreviewMenu
        parent: Overlay.overlay
        theme: root.theme
        preferredWidth: 340
        actions: root.ganttPreviewActions()
    }

    ContentLoadingOverlay {
        anchors.fill: parent
        z: 200
        visible: tasksController.advancedBusy
        theme: root.theme
        message: "Loading tasks…"
        cancellable: true
        onCancelRequested: tasksController.cancel_advanced_load()
    }

    Component.onCompleted: tasksController.set_advanced_visible(true)
    Component.onDestruction: tasksController.set_advanced_visible(false)
}

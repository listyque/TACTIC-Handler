import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    property bool embedded: false
    property bool presentationActive: true
    readonly property bool narrowToolbar: width < 900
    readonly property bool compactScopeControls: root.embedded && width < 1360
    readonly property bool condensedToolbar: width < 520
    readonly property bool minimalToolbar: width < 380
    readonly property bool compactHeaderActions: width < 800
    readonly property bool directGroupVisible:
        root.width >= 720
    readonly property bool directSortVisible:
        root.width >= 1180
    readonly property bool workspaceOverflowRequired:
        !root.directSortVisible || !root.directGroupVisible
            || root.compactHeaderActions || root.condensedToolbar
    readonly property bool hasTaskRows:
        tasksController.advancedVisibleCount > 0
    property bool ganttSurfaceRequested: false
    property string taskColumnContextKey: ""
    property string taskColumnContextLabel: ""
    property var taskColumnContextSource: null

    onHasTaskRowsChanged: {
        if (!hasTaskRows)
            ganttSurfaceRequested = false
    }

    Component.onCompleted: {
        ganttSurfaceRequested = tasksController.viewMode === "gantt"
    }

    Connections {
        target: tasksController
        enabled: root.presentationActive

        function onAdvancedChanged() {
            if (tasksController.viewMode === "gantt")
                root.ganttSurfaceRequested = true
        }
    }

    function ensurePopup(loader) {
        loader.active = true
        return loader.item
    }

    function togglePopupBelow(loader, sourceItem) {
        const popup = root.ensurePopup(loader)
        if (popup)
            popup.toggleBelow(sourceItem)
    }

    function openPopupBelow(loader, sourceItem) {
        const popup = root.ensurePopup(loader)
        if (popup)
            popup.openBelow(sourceItem)
    }

    function rememberPopupState(loader) {
        const popup = root.ensurePopup(loader)
        if (popup)
            popup.sourceWasOpen = popup.opened
    }
    function confirmTaskDelete(taskCode, checkedTasks) {
        if (checkedTasks)
            tasksController.delete_checked_advanced_tasks()
        else
            tasksController.delete_advanced_task(String(taskCode || ""))
    }

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
        const sortActions = tasksController.sortOptions.map(option => ({
            title: option.label, icon: option.icon,
            command: "sort:" + option.value,
            checked: tasksController.sortMode === option.value
        }))
        const groupActions = tasksController.groupOptions.map(option => ({
            title: option.label, icon: option.icon,
            command: "group:" + option.value,
            checked: tasksController.groupMode === option.value
        }))
        const dateSorts = sortActions.filter(action =>
            action.command === "sort:due" || action.command === "sort:recent")
        const otherSorts = sortActions.filter(action => dateSorts.indexOf(action) < 0)
        return [
            {title: "Task scope", status: root.scopeLabel(),
             statusTranslate: false, icon: root.scopeIcon(),
             children: root.scopeMenuActions()},
            {title: "Quick task editor", icon: "view_agenda", command: "quick"},
            {title: "Filters", icon: "filter_alt", children: [
                {title: "Quick filters", icon: "filter_alt", command: "filters"},
                {title: "Clear filters", icon: "filter_alt_off", command: "clear"}
            ]},
            {title: "Manage milestones", icon: "milestone", command: "milestones"},
            {separator: true},
            {title: "View", icon: "view_column", children: [
                {title: "Task table", icon: "table_view", command: "view:list",
                 checked: tasksController.viewMode === "list"},
                {title: "Gantt view", icon: "gantt", command: "view:gantt",
                 checked: tasksController.viewMode === "gantt"},
                {title: "Open task calendar", icon: "calendar_month", command: "calendar"},
                {separator: true},
                {title: "Choose visible columns", icon: "view_column", command: "columns"}
            ]},
            {title: "Sort", icon: "sort-ascending", children: [
                {title: "Date", icon: "schedule", children: dateSorts}
            ].concat(otherSorts)},
            {title: "Group", icon: "group-items", children: groupActions}
        ]
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

    function taskColumnRecord(key) {
        const columns = tasksController.taskColumns || []
        for (let index = 0; index < columns.length; ++index) {
            if (String(columns[index].key || "") === String(key || ""))
                return columns[index]
        }
        return null
    }

    function taskColumnContextActions() {
        const record = root.taskColumnRecord(root.taskColumnContextKey)
        if (!record)
            return []
        const actions = [{
            "header": true,
            "title": qsTr("Column:") + " "
                + root.taskColumnContextLabel,
            "translate": false
        }]
        const sortMode = String(record.sortMode || "")
        if (sortMode.length > 0) {
            const dateSort = String(record.sortKind || "") === "date"
            actions.push({
                "title": dateSort ? "Sort oldest first" : "Sort A to Z",
                "icon": "sort-ascending",
                "command": "sort:ascending",
                "checked": tasksController.sortMode === sortMode
                    && !tasksController.sortDescending
            })
            actions.push({
                "title": dateSort ? "Sort newest first" : "Sort Z to A",
                "icon": "sort-descending",
                "command": "sort:descending",
                "checked": tasksController.sortMode === sortMode
                    && tasksController.sortDescending
            })
        }
        const groupMode = String(record.groupMode || "")
        if (sortMode.length > 0)
            actions.push({"separator": true})
        if (groupMode.length > 0) {
            actions.push({
                "title": "Group by this column",
                "icon": "group-items",
                "command": "group",
                "checked": tasksController.groupMode === groupMode
            })
        }
        actions.push({
            "title": "Remove grouping",
            "icon": "ungroup-items",
            "command": "ungroup",
            "enabled": tasksController.groupMode !== "none"
        })
        actions.push({"separator": true})
        actions.push({
            "title": "Hide this column",
            "icon": "visibility-off",
            "command": "hide",
            "enabled": !Boolean(record.required),
            "status": record.required ? qsTr("Always visible") : ""
        })
        actions.push({
            "title": "Choose visible columns",
            "icon": "view-column",
            "command": "columns"
        })
        actions.push({
            "title": "Configure columns",
            "icon": "settings",
            "command": "configure"
        })
        return actions
    }

    function openTaskColumnContext(sourceItem, columnKey, columnLabel) {
        taskColumnContextSource = sourceItem
        taskColumnContextKey = columnKey
        taskColumnContextLabel = columnLabel
        root.openPopupBelow(taskColumnContextMenuLoader, sourceItem)
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

    Component {
        id: taskTableSurface

        TaskBrowserTable {
            theme: root.theme
            footerHorizontalOverflow: root.embedded ? 6 : 0
            onColumnContextRequested: function(
                    sourceItem, columnKey, columnLabel) {
                root.openTaskColumnContext(
                    sourceItem, columnKey, columnLabel
                )
            }
            onTaskDeleteRequested: function(taskCode, checkedTasks) {
                root.confirmTaskDelete(taskCode, checkedTasks)
            }
        }
    }

    Component {
        id: taskGanttSurface

        TaskGanttView {
            theme: root.theme
            footerHorizontalOverflow: root.embedded ? 6 : 0
            onDeleteTasksRequested: root.confirmTaskDelete("", true)
        }
    }

    Controls.DockWorkspaceFooter {
        objectName: "taskWorkspaceBackgroundSurface"
        anchors.fill: parent
        theme: root.theme
        topDividerVisible: false
        color: root.theme.workspace
    }

    Controls.DockWorkspaceFooter {
        id: persistentFooter
        objectName: "taskWorkspacePersistentFooter"
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.leftMargin: root.embedded ? 0 : 10
        anchors.rightMargin: root.embedded ? 0 : 10
        anchors.bottomMargin: root.embedded ? 0 : 10
        theme: root.theme
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

                Controls.MaterialIcon {
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
                        font.pointSize: Controls.Typography.bodyLarge
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                    }
                    Label {
                        Layout.fillWidth: true
                        text: tasksController.advancedLoadedCount
                            + qsTr(" loaded tasks")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                        elide: Text.ElideRight
                    }
                }
                Controls.Button {
                    theme: root.theme
                    text: root.objectScopeLabel()
                    icon.name: root.objectScopeIcon()
                    tonal: tasksController.advancedScope === "object"
                        || tasksController.advancedScope === "multiple"
                    onClicked: tasksController.use_current_object()
                }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("MY TASKS")
                    icon.name: "person"
                    tonal: tasksController.personalScope
                    onClicked: tasksController.open_for_user("")
                }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("PROJECT")
                    icon.name: "workspaces"
                    tonal: tasksController.advancedScope === "project"
                    onClicked: tasksController.use_project()
                }
                Controls.CompactIconButton {
                    id: teamScopeButton
                    theme: root.theme
                    iconName: "group"
                    toolTip: tasksController.teamOptions.length > 0
                        ? qsTr("Open a team task scope")
                        : qsTr("No team scopes are available from your TACTIC login groups")
                    elevated: tasksController.advancedScope === "team"
                    onClicked: root.togglePopupBelow(
                        teamScopeMenuLoader, teamScopeButton
                    )
                }
                RefreshIconButton {
                    theme: root.theme
                    toolTip: qsTr("Refresh tasks")
                    enabled: !tasksController.advancedBusy
                        && !tasksController.advancedSaving
                        && tasksController.advancedDirtyCount === 0
                    onClicked: tasksController.reload_advanced()
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
            id: taskWorkspaceToolbar
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
                id: taskWorkspacePrimaryActions
                objectName: "taskWorkspacePrimaryActions"
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.right: taskWorkspaceTrailingActions.left
                anchors.leftMargin: root.embedded ? 10 : 8
                anchors.rightMargin: 4
                anchors.bottomMargin: root.embedded ? 1 : 0
                spacing: root.embedded ? 4 : 6
                clip: true

                Controls.FilledActionButton {
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
                Controls.CompactIconButton {
                    id: compactScopeButton
                    objectName: "compactScopeButton"
                    visible: root.embedded && root.compactScopeControls
                        && !root.minimalToolbar
                        && (root.condensedToolbar
                            || root.compactHeaderActions)
                    theme: root.theme
                    Layout.preferredWidth: visible
                        ? root.theme.controlHeight : 0
                    Layout.minimumWidth: Layout.preferredWidth
                    Layout.maximumWidth: Layout.preferredWidth
                    Layout.preferredHeight: root.theme.controlHeight
                    iconName: root.scopeIcon()
                    elevated: true
                    toolTip: qsTr("Task scope: ") + root.scopeLabel()
                    onClicked: root.togglePopupBelow(
                        scopeMenuLoader, compactScopeButton
                    )
                }
                Controls.CompactIconButton {
                    id: milestoneManagerButton
                    objectName: "taskMilestoneManagerButton"
                    visible: !root.compactHeaderActions
                    theme: root.theme
                    Layout.preferredWidth: visible
                        ? root.theme.controlHeight : 0
                    Layout.minimumWidth: Layout.preferredWidth
                    Layout.maximumWidth: Layout.preferredWidth
                    Layout.preferredHeight: root.theme.controlHeight
                    iconName: "milestone"
                    iconColor: root.theme.action
                    backgroundColor: root.theme.surfaceContainerHigh
                    toolTip: qsTr("Manage milestones")
                    onClicked: milestoneController.open_manager()
                }
                Controls.SearchField {
                    id: taskSearchField
                    objectName: "taskWorkspaceSearchField"
                    visible: true
                    theme: root.theme
                    Layout.fillWidth: visible
                    Layout.minimumWidth: visible
                        ? root.condensedToolbar ? 52
                            : root.embedded ? 120 : 180
                        : 0
                    Layout.preferredWidth: visible ? Layout.minimumWidth : 0
                    Layout.preferredHeight: root.theme.controlHeight
                    placeholderText: qsTr("Search tasks")
                    onSearchEdited: query => tasksController.set_filter("text", query)
                }
                Controls.CompactIconButton {
                    id: quickFilterButton
                    objectName: "taskWorkspaceQuickFilterButton"
                    visible: !root.condensedToolbar
                    theme: root.theme
                    Layout.preferredWidth: visible
                        ? root.theme.controlHeight : 0
                    Layout.preferredHeight: root.theme.controlHeight
                    iconName: "filter_alt"
                    badgeCount: tasksController.activeQuickFilterCount
                    toolTip: qsTr("Quick task filters")
                    backgroundColor: root.theme.surfaceContainerHigh
                    onPressed: root.rememberPopupState(quickFilterPopupLoader)
                    onClicked: root.togglePopupBelow(
                        quickFilterPopupLoader, quickFilterButton
                    )
                }
                Controls.CompactIconButton {
                    id: clearTaskFiltersButton
                    objectName: "taskWorkspaceClearFiltersButton"
                    visible: !root.condensedToolbar
                    theme: root.theme
                    Layout.preferredWidth: visible
                        ? root.theme.controlHeight : 0
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
                Controls.SegmentedButton {
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
                            root.togglePopupBelow(
                                teamScopeMenuLoader, embeddedScopeSwitcher
                            )
                        else if (value === "my_tasks")
                            tasksController.open_for_user("")
                    }
                }
                Controls.Button {
                    id: embeddedScopeButton
                    objectName: "embeddedScopeButton"
                    visible: root.compactScopeControls
                        && !root.condensedToolbar
                        && !root.compactHeaderActions
                    theme: root.theme
                    text: root.scopeLabel()
                    icon.name: root.scopeIcon()
                    tonal: true
                    Layout.preferredHeight: root.theme.controlHeight
                    onClicked: root.togglePopupBelow(
                        scopeMenuLoader, embeddedScopeButton
                    )
                }
                Controls.ComboBox {
                    id: taskSortModeCombo
                    objectName: "taskSortModeCombo"
                    visible: root.directSortVisible
                    theme: root.theme
                    Layout.preferredWidth: visible ? 132 : 0
                    Layout.preferredHeight: root.theme.controlHeight
                    Layout.alignment: Qt.AlignVCenter
                    model: tasksController.sortOptions
                    textRole: "label"
                    iconRole: "icon"
                    displayText: currentIndex >= 0
                        ? qsTr("Sort: %1").arg(qsTr(currentText))
                        : qsTr("Sort tasks")
                    currentIndex: root.choiceIndex(
                        tasksController.sortOptions,
                        tasksController.sortMode
                    )
                    onActivated: tasksController.set_sort_mode(
                        tasksController.sortOptions[index].value
                    )
                }
                Controls.ComboBox {
                    id: taskGroupModeCombo
                    objectName: "taskGroupModeCombo"
                    visible: root.directGroupVisible
                    theme: root.theme
                    Layout.preferredWidth: visible ? 148 : 0
                    Layout.preferredHeight: root.theme.controlHeight
                    Layout.alignment: Qt.AlignVCenter
                    model: tasksController.groupOptions
                    textRole: "label"
                    iconRole: "icon"
                    currentIndex: root.choiceIndex(
                        tasksController.groupOptions,
                        tasksController.groupMode
                    )
                    onActivated: tasksController.set_group_mode(
                        tasksController.groupOptions[index].value
                    )
                }
                Controls.CompactIconButton {
                    id: taskColumnsButton
                    objectName: "taskWorkspaceColumnsButton"
                    visible: !root.compactHeaderActions
                    theme: root.theme
                    Layout.preferredWidth: visible
                        ? root.theme.controlHeight : 0
                    Layout.preferredHeight: root.theme.controlHeight
                    iconName: "view_column"
                    iconSize: 17
                    toolTip: qsTr("Choose visible task columns")
                    onPressed: root.rememberPopupState(taskColumnsMenuLoader)
                    onClicked: root.togglePopupBelow(
                        taskColumnsMenuLoader, taskColumnsButton
                    )
                }
            }

            RowLayout {
                id: taskWorkspaceTrailingActions
                objectName: "taskWorkspaceTrailingActions"
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.right: parent.right
                anchors.rightMargin: root.embedded ? 7 : 8
                anchors.bottomMargin: root.embedded ? 1 : 0
                spacing: root.embedded ? 4 : 6

                Item {
                    id: taskWorkspaceMenuSlot
                    Layout.minimumWidth: root.workspaceOverflowRequired
                        ? root.theme.controlHeight : 0
                    Layout.preferredWidth: Layout.minimumWidth
                    Layout.maximumWidth: Layout.minimumWidth
                    Layout.preferredHeight: root.theme.controlHeight

                    Controls.CompactIconButton {
                        id: taskWorkspaceMenuButton
                        objectName: "taskWorkspaceOverflowButton"
                        visible: root.workspaceOverflowRequired
                        anchors.fill: parent
                        theme: root.theme
                        iconName: "more_vert"
                        toolTip: qsTr("Task view, sorting and grouping")
                        onPressed: root.rememberPopupState(
                            taskWorkspaceMenuLoader
                        )
                        onClicked: root.togglePopupBelow(
                            taskWorkspaceMenuLoader,
                            taskWorkspaceMenuButton
                        )
                    }
                }
                TaskWorkspaceSurfaceSwitcher {
                    id: workspaceSurfaceSwitcher
                    objectName: "taskWorkspaceSurfaceSwitcher"
                    theme: root.theme
                    Layout.minimumWidth: implicitWidth
                    Layout.preferredWidth: implicitWidth
                    Layout.maximumWidth: implicitWidth
                    Layout.preferredHeight: root.theme.controlHeight
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
                    onClicked: tasksController.reload_advanced()
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
                    font.pointSize: Controls.Typography.caption
                    font.weight: Font.DemiBold
                }
                Flickable {
                    id: activeFiltersFlick
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    contentWidth: activeFilterRow.width
                    contentHeight: height
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds
                    ScrollBar.horizontal: Controls.ScrollBar {
                        theme: root.theme
                        flickableTarget: activeFiltersFlick
                    }

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
                Controls.CompactIconButton {
                    theme: root.theme
                    iconName: "close"
                    toolTip: qsTr("Clear quick filters")
                    onClicked: tasksController.clear_quick_filters()
                }
            }
        }

        Item {
            id: taskSurfaceSlot
            objectName: "taskWorkspaceSurfaceSlot"
            Layout.leftMargin: root.embedded ? 6 : 0
            Layout.rightMargin: root.embedded ? 6 : 0
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            Layout.minimumHeight: 0
            Layout.fillHeight: true

            Loader {
                id: taskSurfaceLoader
                objectName: "taskWorkspaceSurfaceLoader"
                anchors.fill: parent
                active: root.hasTaskRows
                asynchronous: true
                enabled: tasksController.viewMode === "list"
                opacity: !active ? 0
                    : tasksController.viewMode === "list" ? 1
                    : ganttSurfaceLoader.status === Loader.Ready ? 0 : 1
                visible: active && opacity > 0.001
                sourceComponent: taskTableSurface

                Behavior on opacity {
                    NumberAnimation {
                        duration: root.theme.motionFast
                        easing.type: Easing.OutCubic
                    }
                }
            }

            Loader {
                id: ganttSurfaceLoader
                objectName: "taskWorkspaceGanttSurfaceLoader"
                anchors.fill: parent
                active: root.hasTaskRows && root.ganttSurfaceRequested
                asynchronous: true
                enabled: tasksController.viewMode === "gantt"
                    && status === Loader.Ready
                opacity: enabled ? 1 : 0
                visible: active && opacity > 0.001
                sourceComponent: taskGanttSurface

                Behavior on opacity {
                    NumberAnimation {
                        duration: root.theme.motionFast
                        easing.type: Easing.OutCubic
                    }
                }
            }

            Loader {
                id: pendingChangesLoader
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                height: 0
                z: 80
                active: tasksController.advancedDirtyCount > 0
                sourceComponent: TaskPendingChangesBar {
                    theme: root.theme
                    onPreviewRequested: sourceItem =>
                        root.togglePopupBelow(
                            ganttPreviewMenuLoader, sourceItem
                        )
                }
            }

            Loader {
                anchors.fill: parent
                anchors.bottomMargin: root.theme.dockWorkspaceFooterHeight
                active: !tasksController.advancedBusy && !root.hasTaskRows
                sourceComponent: Item {
                    objectName: "taskWorkspaceEmptyState"
                    anchors.fill: parent

                    ColumnLayout {
                        id: emptyMessageBlock
                        objectName: "taskWorkspaceEmptyMessageBlock"
                        z: 1
                        anchors.centerIn: parent
                        width: Math.min(implicitWidth, parent.width - 40)
                        spacing: 6

                    Label {
                        objectName: "taskWorkspaceEmptyTitle"
                        Layout.alignment: Qt.AlignHCenter
                        text: qsTr("Create a task")
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.bodyLarge
                        font.weight: Font.DemiBold
                    }
                    Label {
                        objectName: "taskWorkspaceEmptyHint"
                        Layout.alignment: Qt.AlignHCenter
                        text: qsTr("Use the + button above")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                    }
                }

                    Canvas {
                        id: emptyCreateArrow
                        objectName: "taskWorkspaceEmptyArrow"
                    property color strokeColor: root.theme.action
                    readonly property real targetX:
                        taskWorkspaceToolbar.x
                            + taskWorkspacePrimaryActions.x
                            + taskCreateButton.x
                            + taskCreateButton.width / 2
                            - taskSurfaceSlot.x
                    readonly property real targetY: Math.max(
                        8,
                        taskWorkspaceToolbar.y
                            + taskWorkspacePrimaryActions.y
                            + taskCreateButton.y
                            + taskCreateButton.height
                            - taskSurfaceSlot.y
                            - emptyCreateArrow.y + 4
                    )
                    readonly property real sourceX:
                        emptyMessageBlock.x - 18
                    readonly property real sourceY:
                        emptyMessageBlock.y
                            + emptyMessageBlock.height / 2 + 8
                            - emptyCreateArrow.y
                    x: 0
                    y: taskWorkspaceToolbar.y - taskSurfaceSlot.y
                    width: parent.width
                    height: parent.height - y
                    antialiasing: true

                    onStrokeColorChanged: requestPaint()
                    onTargetXChanged: requestPaint()
                    onTargetYChanged: requestPaint()
                    onSourceXChanged: requestPaint()
                    onSourceYChanged: requestPaint()
                    onWidthChanged: requestPaint()
                    onHeightChanged: requestPaint()
                    onPaint: {
                        const context = getContext("2d")
                        context.reset()
                        context.strokeStyle = strokeColor
                        context.lineWidth = 2.5
                        context.lineCap = "round"
                        context.lineJoin = "round"
                        const horizontalDistance = Math.max(
                            1, sourceX - targetX
                        )
                        const verticalDistance = Math.max(
                            1, sourceY - targetY
                        )
                        const controlOneX = sourceX
                            - Math.max(34, horizontalDistance * 0.28)
                        const controlOneY = sourceY
                            - Math.max(24, verticalDistance * 0.12)
                        const controlTwoX = targetX
                            + Math.max(32, horizontalDistance * 0.20)
                        const controlTwoY = targetY
                            + Math.max(48, verticalDistance * 0.30)
                        context.beginPath()
                        context.moveTo(sourceX, sourceY)
                        context.bezierCurveTo(
                            controlOneX, controlOneY,
                            controlTwoX, controlTwoY,
                            targetX, targetY
                        )
                        context.stroke()
                        const angle = Math.atan2(
                            targetY - controlTwoY,
                            targetX - controlTwoX
                        )
                        const arrowLength = 13
                        const arrowSpread = 0.52
                        context.beginPath()
                        context.moveTo(targetX, targetY)
                        context.lineTo(
                            targetX - arrowLength
                                * Math.cos(angle - arrowSpread),
                            targetY - arrowLength
                                * Math.sin(angle - arrowSpread)
                        )
                        context.moveTo(targetX, targetY)
                        context.lineTo(
                            targetX - arrowLength
                                * Math.cos(angle + arrowSpread),
                            targetY - arrowLength
                                * Math.sin(angle + arrowSpread)
                        )
                        context.stroke()
                    }
                }
            }
        }
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
                Controls.MaterialIcon {
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
                    font.pointSize: Controls.Typography.label
                }
                Controls.CompactIconButton {
                    theme: root.theme
                    iconName: "close"
                    toolTip: qsTr("Dismiss error")
                    onClicked: tasksController.clear_advanced_error()
                }
            }
        }
    }

    TaskWorkspaceModeSwitcher {
        id: workspaceModeSwitcher
        objectName: "taskWorkspaceModeSwitcher"
        z: 50
        visible: root.width >= 380
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.rightMargin: root.embedded ? 8 : 18
        anchors.bottomMargin: (root.embedded ? 0 : 10)
            + Math.max(
                0,
                (root.theme.dockWorkspaceFooterHeight - height) / 2
            )
        theme: root.theme
    }

    Loader {
        id: quickFilterPopupLoader
        active: false
        sourceComponent: TaskQuickFilterPopup { theme: root.theme }
    }

    Loader {
        id: scopeMenuLoader
        active: false
        sourceComponent: ActionMenu {
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
                        ? embeddedScopeButton
                        : compactScopeButton.visible
                            ? compactScopeButton
                            : taskWorkspaceMenuButton
                    root.togglePopupBelow(teamScopeMenuLoader, anchor)
                }
                else if (command.indexOf("team:") === 0)
                    tasksController.open_for_team(command.slice(5))
            }
        }
    }

    Loader {
        id: teamScopeMenuLoader
        active: false
        sourceComponent: ActionMenu {
            parent: Overlay.overlay
            theme: root.theme
            preferredWidth: 310
            actions: root.teamMenuActions()
            onTriggered: command => {
                if (command.indexOf("team:") === 0)
                    tasksController.open_for_team(command.slice(5))
            }
        }
    }

    Loader {
        id: taskWorkspaceMenuLoader
        active: false
        sourceComponent: ActionMenu {
            objectName: "taskWorkspaceMenu"
            compact: true
            parent: Overlay.overlay
            theme: root.theme
            preferredWidth: 250
            actions: root.workspaceMenuActions()
            onTriggered: command => {
                if (command === "object")
                    tasksController.use_current_object()
                else if (command === "search_type")
                    tasksController.use_current_search_type()
                else if (command === "my_tasks")
                    tasksController.open_for_user("")
                else if (command === "project")
                    tasksController.use_project()
                else if (command === "teams")
                    root.togglePopupBelow(teamScopeMenuLoader, taskWorkspaceMenuButton)
                else if (command === "quick")
                    tasksController.open_quick_workspace()
                else if (command === "filters")
                    root.togglePopupBelow(
                        quickFilterPopupLoader, taskWorkspaceMenuButton
                    )
                else if (command === "milestones")
                    milestoneController.open_manager()
                else if (command === "columns")
                    Qt.callLater(function() {
                        root.openPopupBelow(
                            taskColumnsMenuLoader, taskWorkspaceMenuButton
                        )
                    })
                else if (command.indexOf("view:") === 0)
                    tasksController.set_view_mode(command.slice(5))
                else if (command === "calendar")
                    tasksController.open_calendar()
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
    }

    Loader {
        id: taskColumnsMenuLoader
        active: false
        sourceComponent: ActionMenu {
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
    }

    Loader {
        id: taskColumnContextMenuLoader
        active: false
        sourceComponent: ActionMenu {
            objectName: "taskColumnContextMenu"
            parent: Overlay.overlay
            theme: root.theme
            preferredWidth: 280
            actions: root.taskColumnContextActions()
            onTriggered: command => {
                if (command === "sort:ascending")
                    tasksController.set_task_column_sort(
                        root.taskColumnContextKey, false
                    )
                else if (command === "sort:descending")
                    tasksController.set_task_column_sort(
                        root.taskColumnContextKey, true
                    )
                else if (command === "group")
                    tasksController.group_by_task_column(
                        root.taskColumnContextKey
                    )
                else if (command === "ungroup")
                    tasksController.set_group_mode("none")
                else if (command === "hide")
                    tasksController.set_task_column_visible(
                        root.taskColumnContextKey, false
                    )
                else if (command === "columns") {
                    Qt.callLater(function() {
                        root.openPopupBelow(
                            taskColumnsMenuLoader,
                            root.taskColumnContextSource
                        )
                    })
                } else if (command === "configure") {
                    appController.invoke("open_configuration")
                }
            }
        }
    }

    Loader {
        id: ganttPreviewMenuLoader
        active: false
        sourceComponent: ActionMenu {
            parent: Overlay.overlay
            theme: root.theme
            preferredWidth: 340
            actions: root.ganttPreviewActions()
        }
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

    Component.onDestruction: tasksController.set_advanced_visible(false)
}

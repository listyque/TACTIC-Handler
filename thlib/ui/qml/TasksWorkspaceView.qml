import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls
import "features/tasks" as Tasks
import "tactic_frame" as Frame
import "tactic_frame/core/strings.mjs" as TaskStrings
import "tactic_frame/features/tasks/workspace.ui.mjs" as WorkspaceUI
import "tactic_frame/features/tasks/summary.ui.mjs" as SummaryUI
import "tactic_frame/features/tasks/menus.ui.mjs" as TaskMenus

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
    readonly property bool directGroupVisible: root.width >= 720
    readonly property bool directSortVisible: root.width >= 1180
    readonly property bool workspaceOverflowRequired: !root.directSortVisible || !root.directGroupVisible || root.compactHeaderActions || root.condensedToolbar
    readonly property bool hasTaskRows: tasksController.advancedVisibleCount > 0
    property bool ganttSurfaceRequested: false
    property var toolbarMenuSource: null
    property string taskColumnContextKey: ""
    property string taskColumnContextLabel: ""
    property var taskColumnContextSource: null

    onHasTaskRowsChanged: {
        if (!hasTaskRows)
            ganttSurfaceRequested = false;
    }

    Component.onCompleted: {
        ganttSurfaceRequested = tasksController.viewMode === "gantt";
    }

    Connections {
        target: tasksController
        enabled: root.presentationActive

        function onAdvancedChanged() {
            if (tasksController.viewMode === "gantt")
                root.ganttSurfaceRequested = true;
        }
    }

    function ensurePopup(loader) {
        loader.active = true;
        return loader.item;
    }

    function togglePopupBelow(loader, sourceItem) {
        const popup = root.ensurePopup(loader);
        if (popup)
            popup.toggleBelow(sourceItem);
    }

    function openPopupBelow(loader, sourceItem) {
        const popup = root.ensurePopup(loader);
        if (popup)
            popup.openBelow(sourceItem);
    }

    function rememberPopupState(loader) {
        const popup = root.ensurePopup(loader);
        if (popup)
            popup.sourceWasOpen = popup.opened;
    }
    function confirmTaskDelete(taskCode, checkedTasks) {
        if (checkedTasks)
            tasksController.delete_checked_advanced_tasks();
        else
            tasksController.delete_advanced_task(String(taskCode || ""));
    }

    function searchTypeScopeLabel() {
        const name = String(tasksController.searchTypeScopeName || "");
        return name.length > 0 ? qsTr("All") + " " + name : qsTr("Search Type");
    }

    function scopeLabel() {
        if (tasksController.advancedScope === "multiple")
            return TaskStrings.translate("Selected", typeof localizationController === "undefined" ? "en" : localizationController.current_language).toUpperCase();
        if (tasksController.advancedScope === "object")
            return TaskStrings.translate("Selected", typeof localizationController === "undefined" ? "en" : localizationController.current_language).toUpperCase();
        if (tasksController.advancedScope === "search_type")
            return root.searchTypeScopeLabel();
        if (tasksController.advancedScope === "user")
            return tasksController.personalScope ? qsTr("My Tasks").toUpperCase() : qsTr("User").toUpperCase();
        if (tasksController.advancedScope === "project")
            return qsTr("Project").toUpperCase();
        if (tasksController.advancedScope === "team")
            return qsTr("Team").toUpperCase();
        return qsTr("Object").toUpperCase();
    }

    function scopeIcon() {
        if (tasksController.advancedScope === "multiple")
            return "select_all";
        if (tasksController.advancedScope === "search_type")
            return "table_view";
        if (tasksController.advancedScope === "user")
            return "person";
        if (tasksController.advancedScope === "project")
            return "workspaces";
        if (tasksController.advancedScope === "team")
            return "group";
        return "inventory_2";
    }

    function objectScopeLabel() {
        return TaskStrings.translate("Selected", typeof localizationController === "undefined" ? "en" : localizationController.current_language).toUpperCase();
    }

    function objectScopeIcon() {
        return tasksController.advancedScope === "multiple" ? "select_all" : "inventory_2";
    }

    function choiceIndex(values, selected) {
        for (let index = 0; index < values.length; ++index) {
            if (String(values[index].value || "") === String(selected || ""))
                return index;
        }
        return -1;
    }

    function taskColumnRecord(key) {
        const columns = tasksController.taskColumns || [];
        for (let index = 0; index < columns.length; ++index) {
            if (String(columns[index].key || "") === String(key || ""))
                return columns[index];
        }
        return null;
    }

    function taskColumnContextActions() {
        const record = root.taskColumnRecord(root.taskColumnContextKey);
        if (!record)
            return [];
        return TaskMenus.column({
            column: record,
            label: root.taskColumnContextLabel,
            sort: tasksController.sortMode,
            descending: tasksController.sortDescending,
            group: tasksController.groupMode,
            busy: tasksController.advancedBusy,
            configure: true
        });
    }

    function openTaskColumnContext(sourceItem, columnKey, columnLabel) {
        taskColumnContextSource = sourceItem;
        taskColumnContextKey = columnKey;
        taskColumnContextLabel = columnLabel;
        root.openPopupBelow(taskColumnContextMenuLoader, sourceItem);
    }

    function ganttPreviewActions() {
        const actions = [
            {
                "header": true,
                "title": "Pending Gantt changes"
            }
        ];
        const changes = tasksController.ganttChangePreview;
        for (let index = 0; index < changes.length; ++index) {
            const change = changes[index];
            actions.push({
                "title": change.title + " · " + change.process,
                "status": change.start.slice(0, 10) + " — " + change.end.slice(0, 10) + " · " + change.progress + "%",
                "icon": "schedule",
                "enabled": false
            });
        }
        return actions;
    }

    Component {
        id: taskTableSurface

        TaskBrowserTable {
            theme: root.theme
            footerHorizontalOverflow: root.embedded ? 6 : 0
            onInitialPresentationReadyChanged: taskSurfaceLoader.firstBatchReady = initialPresentationReady
            Component.onCompleted: taskSurfaceLoader.firstBatchReady = initialPresentationReady
            onColumnContextRequested: function (sourceItem, columnKey, columnLabel) {
                root.openTaskColumnContext(sourceItem, columnKey, columnLabel);
            }
            onColumnsPressed: root.rememberPopupState(taskColumnsMenuLoader)
            onColumnsRequested: sourceItem => root.togglePopupBelow(taskColumnsMenuLoader, sourceItem)
            onTaskDeleteRequested: function (taskCode, checkedTasks) {
                root.confirmTaskDelete(taskCode, checkedTasks);
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
        Frame.FrameView {
            anchors.fill: parent
            theme: root.theme
            visible: !root.hasTaskRows
            scene: WorkspaceUI.footer({
                loaded: 0,
                total: tasksController.advancedTotalCount,
                visible: 0,
                filtered: tasksController.advancedFiltersActive,
                processes: 0,
                reserveModes: true
            }, width, typeof localizationController === "undefined" ? "en" : localizationController.current_language)
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.leftMargin: root.embedded ? 0 : 10
        anchors.rightMargin: root.embedded ? 0 : 10
        anchors.topMargin: root.embedded ? 0 : 10
        anchors.bottomMargin: root.embedded ? 0 : 10
        spacing: root.embedded ? 5 : 7

        Frame.FrameView {
            visible: !root.embedded
            Layout.fillWidth: true
            Layout.preferredHeight: visible ? scene.height : 0
            theme: root.theme
            scene: SummaryUI.heading({
                title: tasksController.advancedTitle,
                loaded: tasksController.advancedLoadedCount,
                scope: tasksController.advancedScope,
                personal: tasksController.personalScope,
                selectedIcon: root.objectScopeIcon(),
                canRefresh: !tasksController.advancedBusy && !tasksController.advancedSaving && tasksController.advancedDirtyCount === 0,
                controlHeight: root.theme.controlHeight
            }, width, typeof localizationController === "undefined" ? "en" : localizationController.current_language)
            onEvent: (action, source) => {
                if (action.type === "selected")
                    tasksController.use_current_object();
                else if (action.type === "user")
                    tasksController.open_for_user("");
                else if (action.type === "project")
                    tasksController.use_project();
                else if (action.type === "team")
                    root.ensurePopup(scopeMenuLoader).toggleTeamsBelow(source);
                else if (action.type === "refresh")
                    tasksController.reload_advanced();
            }
        }

        TaskWorkspaceSummary {
            visible: !root.embedded
            Layout.fillWidth: true
            Layout.preferredHeight: visible ? implicitHeight : 0
            theme: root.theme
        }

        Tasks.TaskWorkspaceToolbar {
            id: taskWorkspaceToolbar
            embedded: root.embedded
            Layout.fillWidth: true
            Layout.preferredHeight: implicitHeight
            theme: root.theme
            controller: tasksController
            scopeLabel: root.scopeLabel()
            scopeIcon: root.scopeIcon()
            searchTypeLabel: root.searchTypeScopeLabel()
            selectedIcon: root.objectScopeIcon()
            onCommand: (action, source) => {
                if (action.type === "scope") {
                    root.togglePopupBelow(scopeMenuLoader, source);
                } else if (action.type === "scope-press")
                    root.rememberPopupState(scopeMenuLoader);
                else if (action.type === "scope-choice")
                    root.ensurePopup(scopeMenuLoader).toggleTeamsBelow(source);
                else if (action.type === "filters-press")
                    root.rememberPopupState(quickFilterPopupLoader);
                else if (action.type === "filters")
                    root.togglePopupBelow(quickFilterPopupLoader, source);
                else if (action.type === "options-press")
                    root.rememberPopupState(taskWorkspaceMenuLoader);
                else if (action.type === "options") {
                    root.toolbarMenuSource = source;
                    root.togglePopupBelow(taskWorkspaceMenuLoader, source);
                } else if (action.type === "milestones")
                    milestoneController.open_manager();
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
                                accent: modelData.accent ? modelData.accent : root.theme.action
                                onClicked: tasksController.toggle_quick_filter(modelData.group, modelData.key)
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
                property bool firstBatchReady: false
                onActiveChanged: if (!active)
                    firstBatchReady = false
                enabled: tasksController.viewMode === "list"
                opacity: !active ? 0 : tasksController.viewMode === "list" ? 1 : ganttSurfaceLoader.status === Loader.Ready ? 0 : 1
                visible: active && status === Loader.Ready && firstBatchReady && opacity > 0.001
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
                enabled: tasksController.viewMode === "gantt" && status === Loader.Ready
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
                    onPreviewRequested: sourceItem => root.togglePopupBelow(ganttPreviewMenuLoader, sourceItem)
                }
            }

            Loader {
                anchors.fill: parent
                anchors.bottomMargin: root.theme.dockWorkspaceFooterHeight
                active: !tasksController.advancedBusy && !root.hasTaskRows
                sourceComponent: Tasks.TaskEmptyState {
                    anchors.fill: parent
                    theme: root.theme
                    controller: tasksController
                    createTarget: ({
                            x: taskWorkspaceToolbar.x + taskWorkspaceToolbar.createBounds.x + taskWorkspaceToolbar.createBounds.width / 2 - taskSurfaceSlot.x,
                            y: taskWorkspaceToolbar.y + taskWorkspaceToolbar.createBounds.y + taskWorkspaceToolbar.createBounds.height - taskSurfaceSlot.y + 4
                        })
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
                    text: qsTr(tasksController.advancedError)
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
        anchors.bottomMargin: (root.embedded ? 0 : 10) + Math.max(0, (root.theme.dockWorkspaceFooterHeight - height) / 2)
        theme: root.theme
    }

    Loader {
        id: quickFilterPopupLoader
        active: false
        sourceComponent: TaskQuickFilterPopup {
            theme: root.theme
        }
    }

    Loader {
        id: scopeMenuLoader
        active: false
        sourceComponent: Tasks.TaskScopePopup {
            theme: root.theme
            controller: tasksController
            users: userListModel
            selectedIcon: root.objectScopeIcon()
        }
    }

    Loader {
        id: taskWorkspaceMenuLoader
        active: false
        sourceComponent: Tasks.TaskOptionsPopup {
            objectName: "taskWorkspaceMenu"
            theme: root.theme
            controller: tasksController
            toolbarWidth: root.width
            scopeIcon: root.scopeIcon()
            onCommand: (action, source) => {
                const anchor = root.toolbarMenuSource || taskWorkspaceToolbar;
                if (action.type === "scope")
                    root.openPopupBelow(scopeMenuLoader, anchor);
                else if (action.type === "filters")
                    root.openPopupBelow(quickFilterPopupLoader, anchor);
                else if (action.type === "columns")
                    root.openPopupBelow(taskColumnsMenuLoader, anchor);
                else if (action.type === "milestones")
                    milestoneController.open_manager();
                else if (action.type === "quick")
                    tasksController.open_quick_workspace();
                else if (action.type === "calendar")
                    tasksController.open_calendar();
            }
        }
    }

    Loader {
        id: taskColumnsMenuLoader
        active: false
        sourceComponent: Tasks.TaskColumnsPopup {
            objectName: "taskColumnsMenu"
            theme: root.theme
            controller: tasksController
            onConfigureRequested: {
                configurationController.select_page("tasks_preferences");
                appController.invoke("open_configuration");
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
                    tasksController.set_task_column_sort(root.taskColumnContextKey, false);
                else if (command === "sort:descending")
                    tasksController.set_task_column_sort(root.taskColumnContextKey, true);
                else if (command === "group")
                    tasksController.group_by_task_column(root.taskColumnContextKey);
                else if (command === "ungroup")
                    tasksController.set_group_mode("none");
                else if (command === "hide")
                    tasksController.set_task_column_visible(root.taskColumnContextKey, false);
                else if (command === "columns") {
                    Qt.callLater(function () {
                        root.openPopupBelow(taskColumnsMenuLoader, root.taskColumnContextSource);
                    });
                } else if (command === "configure") {
                    configurationController.select_page("tasks_preferences");
                    appController.invoke("open_configuration");
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
        objectName: "taskWorkspaceLoadingOverlay"
        anchors.fill: parent
        z: 200
        visible: tasksController.advancedBusy || (root.hasTaskRows && tasksController.viewMode === "list" && (taskSurfaceLoader.status !== Loader.Ready || !taskSurfaceLoader.firstBatchReady))
        theme: root.theme
        message: "Loading tasks…"
        cancellable: tasksController.advancedBusy
        onCancelRequested: tasksController.cancel_advanced_load()
    }

    Component.onDestruction: tasksController.set_advanced_visible(false)
}

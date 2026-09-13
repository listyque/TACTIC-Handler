import QtQuick
import QtQuick.Controls
import "controls" as Controls

ActionMenu {
    id: root
    property var panelModel
    property var layoutPresetController: null
    property int panelRevision: 0
    signal resetLayoutRequested()

    compact: true
    preferredWidth: 280
    Component.onCompleted: root.addMenu(presetsMenu)
    actions: {
        const revision = panelRevision
        const browse = []
        const tasks = []
        const tools = []
        for (let index = 0; index < panels.count; ++index) {
            const panel = panels.objectAt(index)
            if (!panel)
                continue
            const action = {
                title: panel.kind === "tasks" ? qsTr("Task Manager") : qsTr(panel.title),
                translate: false,
                icon: panel.iconName, command: "panel:" + panel.panelId,
                checked: panel.panelVisible,
                enabled: panel.closable || !panel.panelVisible
            }
            if (["tasks", "notes", "task_calendar", "timesheet",
                 "work_reports", "cost_reports"].indexOf(panel.kind) >= 0)
                tasks.push(action)
            else if (["results", "snapshot", "description", "knowledge"].indexOf(panel.kind) >= 0)
                browse.push(action)
            else
                tools.push(action)
        }
        return [
            {title: "Browsing", icon: "view_kanban", children: browse,
             visible: browse.length > 0},
            {title: "Tasks and reports", icon: "task_alt", children: tasks,
             visible: tasks.length > 0},
            {title: "Tools", icon: "settings-suggest", children: tools,
             visible: tools.length > 0},
            {separator: true},
            {title: "Layout presets", icon: "dashboard_customize",
             submenuPopup: presetsMenu, visible: layoutPresetController !== null},
            {title: "Reset layout", icon: "sync", command: "reset"}
        ]
    }
    onTriggered: command => {
        if (command === "reset")
            root.resetLayoutRequested()
        else if (command.indexOf("panel:") === 0)
            root.panelModel.toggle_panel(command.slice(6))
    }

    Instantiator {
        id: panels
        model: root.panelModel
        onObjectAdded: ++root.panelRevision
        onObjectRemoved: ++root.panelRevision
        delegate: QtObject {
            required property string panelId
            required property string title
            required property string kind
            required property bool panelVisible
            required property bool closable
            readonly property string iconName: kind === "snapshot" ? "movie"
                : kind === "tasks" ? "task_alt"
                : kind === "task_calendar" ? "calendar_month"
                : kind === "drop_plate" ? "publish"
                : kind === "notes" ? "comment"
                : kind === "knowledge" ? "book-open"
                : kind === "description" ? "description"
                : kind === "advanced_search" ? "search"
                : kind === "repo_sync_queue" ? "repository-sync"
                : kind === "commit_queue" ? "publish"
                : kind === "watch_folders" ? "folder"
                : kind === "db_table" ? "table"
                : "view_kanban"
        }
    }

    Controls.Menu {
        id: presetsMenu
        objectName: "workspacePresetsMenu"
        parent: root.parent
        theme: root.theme
        width: Math.min(330, maximumAvailableWidth - 2 * effectiveShadowMargin)
            + 2 * effectiveShadowMargin
        implicitHeight: Math.min(presetSection.implicitHeight + topPadding + bottomPadding,
                         maximumAvailableHeight)
        height: implicitHeight
        modal: false
        dim: false
        focus: true
        onOpened: presetSection.focusFirstAction()
        onClosed: {
            if (root.opened && openingAnchorItem)
                openingAnchorItem.primaryTarget.forceActiveFocus(Qt.PopupFocusReason)
        }
        contentItem: Flickable {
            id: presetFlickable
            clip: true
            contentWidth: width
            contentHeight: presetSection.implicitHeight
            boundsBehavior: Flickable.StopAtBounds
            Keys.onLeftPressed: event => {
                event.accepted = true
                presetsMenu.close()
            }
            WorkspaceLayoutPresetMenuSection {
                id: presetSection
                width: Math.max(0, presetFlickable.width - (
                    presetScrollBar.hasOverflow ? presetScrollBar.reservedExtent + 4 : 0))
                theme: root.theme
                controller: root.layoutPresetController
                viewport: presetFlickable
                onCloseMenuRequested: root.close()
            }
            ScrollBar.vertical: Controls.ScrollBar {
                id: presetScrollBar
                theme: root.theme
                flickableTarget: presetFlickable
            }
        }
    }
}

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import QtQml.Models
import "controls" as Controls

Item {
    id: root
    objectName: "dockHost"
    required property var theme
    required property string projectTitle
    required property string pageTitle
    property var ownerWindow: Window.window
    signal notice(string message)
    signal requestDockMenu(var sourceItem)

    property bool dockDragActive: false
    property bool dockResizeActive: false
    property bool windowResizeActive: false
    property string draggingPanelId: ""
    property string activeSnapZone: ""
    property string activeSnapTargetId: ""
    property var activeSnapRect: ({ "x": 0, "y": 0, "width": 0, "height": 0 })
    property var activeTargetRect: ({ "x": 0, "y": 0, "width": 0, "height": 0 })
    readonly property string descriptionDockTitle: {
        const target = workspaceState
            ? String(workspaceState.descriptionTargetTitle || "").trim() : ""
        return target.length ? "Description · " + target : "Description"
    }

    function tasksDockTitle() {
        let subject = String(tasksController.advancedDockSubject || "")
        if (tasksController.advancedScope === "project")
            subject = qsTr("Project")
        else if (tasksController.advancedScope === "multiple")
            subject += " " + qsTr("selected objects")
        else if (subject.length === 0)
            subject = qsTr("Object")
        return qsTr("Tasks for:") + " " + subject
    }

    function rootSnapZoneAt(pointerX, pointerY) {
        const edge = 24
        if (pointerX <= edge) return "left"
        if (pointerX >= width - edge) return "right"
        if (pointerY <= edge) return "top"
        if (pointerY >= height - edge) return "bottom"
        return ""
    }

    function rootSnapRectFor(zone) {
        if (zone === "left") return ({ "x": 0, "y": 0, "width": width * 0.28, "height": height })
        if (zone === "right") return ({ "x": width * 0.66, "y": 0, "width": width * 0.34, "height": height })
        if (zone === "top") return ({ "x": 0, "y": 0, "width": width, "height": height * 0.28 })
        if (zone === "bottom") return ({ "x": 0, "y": height * 0.70, "width": width, "height": height * 0.30 })
        return ({ "x": 0, "y": 0, "width": 0, "height": 0 })
    }

    function targetAt(pointerX, pointerY, excludedPanelId) {
        for (let index = dockRepeater.count - 1; index >= 0; --index) {
            const item = dockRepeater.itemAt(index)
            if (!item || item.panelId === excludedPanelId
                    || !item.panelVisible || item.detached
                    || !item.stackActive || item.dockArea === "floating")
                continue
            const rect = {
                "x": item.panelX * width,
                "y": item.panelY * height,
                "width": item.panelWidth * width,
                "height": item.panelHeight * height
            }
            if (pointerX >= rect.x && pointerX <= rect.x + rect.width
                    && pointerY >= rect.y && pointerY <= rect.y + rect.height)
                return ({ "panelId": item.panelId, "kind": item.kind,
                    "rect": rect })
        }
        return null
    }

    function targetZoneAt(pointerX, pointerY, rect, allowCenter) {
        const localX = pointerX - rect.x
        const localY = pointerY - rect.y
        const horizontalEdge = Math.min(88, rect.width * 0.27)
        const verticalEdge = Math.min(76, rect.height * 0.27)
        const titleHeight = Math.min(root.theme.dockTitleHeight,
            rect.height * 0.18)
        if (allowCenter && localY <= titleHeight
                && localX > horizontalEdge
                && localX < rect.width - horizontalEdge)
            return "swap"
        const distances = [
            { "zone": "left", "value": localX / Math.max(1, horizontalEdge) },
            { "zone": "right", "value": (rect.width - localX) / Math.max(1, horizontalEdge) },
            { "zone": "top", "value": localY / Math.max(1, verticalEdge) },
            { "zone": "bottom", "value": (rect.height - localY) / Math.max(1, verticalEdge) }
        ]
        distances.sort((first, second) => first.value - second.value)
        return distances[0].value <= 1 || !allowCenter
            ? distances[0].zone : "center"
    }

    function targetSnapRectFor(zone, rect) {
        if (zone === "left")
            return ({ "x": rect.x, "y": rect.y, "width": rect.width * 0.5, "height": rect.height })
        if (zone === "right")
            return ({ "x": rect.x + rect.width * 0.5, "y": rect.y, "width": rect.width * 0.5, "height": rect.height })
        if (zone === "top")
            return ({ "x": rect.x, "y": rect.y, "width": rect.width, "height": rect.height * 0.5 })
        if (zone === "bottom")
            return ({ "x": rect.x, "y": rect.y + rect.height * 0.5, "width": rect.width, "height": rect.height * 0.5 })
        return rect
    }

    function beginDockDrag(panelId) {
        draggingPanelId = panelId
        activeSnapZone = ""
        activeSnapTargetId = ""
        dockDragActive = true
    }

    function beginDockResize() {
        dockResizeActive = true
    }

    function endDockResize() {
        dockResizeActive = false
    }

    function ensureDockMinimumSizes() {
        if (root.width > 1 && root.height > 1)
            dockModel.ensure_minimum_sizes(root.width, root.height)
    }

    onWidthChanged: {
        windowResizeActive = true
        windowResizeIdle.restart()
    }
    onHeightChanged: {
        windowResizeActive = true
        windowResizeIdle.restart()
    }
    Timer {
        id: windowResizeIdle
        interval: 90
        onTriggered: {
            root.ensureDockMinimumSizes()
            root.windowResizeActive = false
        }
    }

    Component.onCompleted: Qt.callLater(root.ensureDockMinimumSizes)
    Connections {
        target: dockModel
        function onPanelVisibilityChanged() {
            Qt.callLater(root.ensureDockMinimumSizes)
        }
    }

    function updateDockDrag(panelId, pointerX, pointerY) {
        if (!dockDragActive || draggingPanelId !== panelId) return
        const rootZone = rootSnapZoneAt(pointerX, pointerY)
        if (rootZone.length) {
            activeSnapZone = rootZone
            activeSnapTargetId = ""
            activeTargetRect = ({ "x": 0, "y": 0, "width": width, "height": height })
            activeSnapRect = rootSnapRectFor(rootZone)
            return
        }
        const target = targetAt(pointerX, pointerY, panelId)
        if (target) {
            activeSnapTargetId = target.panelId
            activeTargetRect = target.rect
            activeSnapZone = targetZoneAt(
                pointerX, pointerY, target.rect,
                target.kind !== "commit_queue")
            activeSnapRect = targetSnapRectFor(activeSnapZone, target.rect)
            return
        }
        activeSnapZone = ""
        activeSnapTargetId = ""
        activeTargetRect = ({ "x": 0, "y": 0, "width": 0, "height": 0 })
        activeSnapRect = ({ "x": 0, "y": 0, "width": 0, "height": 0 })
    }

    function finishDockDrag(panelId, panelX, panelY, panelWidth, panelHeight) {
        if (!dockDragActive || draggingPanelId !== panelId) return
        if (activeSnapZone.length && activeSnapTargetId.length)
            dockModel.place_panel(panelId, activeSnapTargetId, activeSnapZone)
        else if (activeSnapZone.length)
            dockModel.snap_panel(panelId, activeSnapZone)
        else
            dockModel.float_panel(
                panelId,
                panelX / Math.max(1, width),
                panelY / Math.max(1, height),
                panelWidth / Math.max(1, width),
                panelHeight / Math.max(1, height)
            )
        dockDragActive = false
        draggingPanelId = ""
        activeSnapZone = ""
        activeSnapTargetId = ""
        activeTargetRect = ({ "x": 0, "y": 0, "width": 0, "height": 0 })
        activeSnapRect = ({ "x": 0, "y": 0, "width": 0, "height": 0 })
    }

    Rectangle { anchors.fill: parent; color: root.theme.workspace }
    Item {
        id: dockCanvas
        anchors.fill: parent
        clip: true
        Repeater {
            id: dockRepeater
            model: visibleDockModel
            delegate: Item {
                id: dockDelegate
                objectName: "dockDelegate_" + panelId
                required property string panelId
                required property string title
                required property string kind
                required property real panelX
                required property real panelY
                required property real panelWidth
                required property real panelHeight
                required property bool panelVisible
                required property bool closable
                required property int stackOrder
                required property string dockArea
                required property bool canResizeLeft
                required property bool canResizeRight
                required property bool canResizeTop
                required property bool canResizeBottom
                required property bool detached
                required property bool stackActive
                required property var stackPanels
                required property int stackSize
                readonly property Component panelContentComponent:
                    kind === "results" ? dockContents.results
                    : kind === "snapshot" ? dockContents.snapshot
                    : kind === "tasks" ? dockContents.tasks
                    : kind === "task_calendar" ? dockContents.taskCalendar
                    : kind === "timesheet" ? dockContents.timesheet
                    : kind === "work_reports" ? dockContents.workReports
                    : kind === "cost_reports" ? dockContents.costReports
                    : kind === "notes" ? dockContents.notes
                    : kind === "drop_plate" ? dockContents.dropPlate
                    : kind === "advanced_search" ? dockContents.advancedSearch
                    : kind === "repo_sync_queue" ? dockContents.repoSync
                    : kind === "commit_queue" ? dockContents.commitQueue
                    : kind === "watch_folders" ? dockContents.watchFolders
                    : kind === "db_table" ? dockContents.databaseEditor
                    : kind === "knowledge" ? dockContents.knowledge
                    : dockContents.description
                DockPanel {
                    host: root
                    theme: root.theme
                    panelId: dockDelegate.panelId
                    title: dockDelegate.kind === "tasks"
                        ? (tasksController.workspaceSurface === "browser"
                            ? root.tasksDockTitle()
                            : (tasksController.hasTarget
                                ? qsTr("Tasks for:") + " "
                                    + tasksController.targetTitle
                                : qsTr("Tasks")))
                        : dockDelegate.kind === "description"
                            ? root.descriptionDockTitle
                        : dockDelegate.title
                    descriptionTitle: root.descriptionDockTitle
                    kind: dockDelegate.kind
                    panelX: dockDelegate.panelX
                    panelY: dockDelegate.panelY
                    panelWidth: dockDelegate.panelWidth
                    panelHeight: dockDelegate.panelHeight
                    modelVisible: dockDelegate.panelVisible
                        && dockDelegate.stackActive
                        && !dockDelegate.detached
                    panelOpen: dockDelegate.panelVisible
                        && dockDelegate.stackActive
                        && !dockDelegate.detached
                    stackActive: dockDelegate.stackActive
                    closable: dockDelegate.closable
                    stackOrder: dockDelegate.stackOrder
                    dockArea: dockDelegate.dockArea
                    canResizeLeft: dockDelegate.canResizeLeft
                    canResizeRight: dockDelegate.canResizeRight
                    canResizeTop: dockDelegate.canResizeTop
                    canResizeBottom: dockDelegate.canResizeBottom
                    stackPanels: dockDelegate.stackPanels
                    stackSize: dockDelegate.stackSize
                    contentComponent: dockDelegate.panelContentComponent
                }
            }
        }
    }

    Instantiator {
        model: detachedDockModel
        delegate: DetachedDockWindow {
            ownerWindow: root.ownerWindow
            theme: root.theme
            titleOverride: kind === "description"
                ? root.descriptionDockTitle : ""
            contentComponent: kind === "snapshot" ? dockContents.snapshot
                : kind === "tasks" ? dockContents.tasks
                : kind === "task_calendar" ? dockContents.taskCalendar
                : kind === "timesheet" ? dockContents.timesheet
                : kind === "work_reports" ? dockContents.workReports
                : kind === "cost_reports" ? dockContents.costReports
                : kind === "notes" ? dockContents.notes
                : kind === "drop_plate" ? dockContents.dropPlate
                : kind === "advanced_search" ? dockContents.advancedSearch
                : kind === "repo_sync_queue" ? dockContents.repoSync
                : kind === "commit_queue" ? dockContents.commitQueue
                : kind === "watch_folders" ? dockContents.watchFolders
                : kind === "db_table" ? dockContents.databaseEditor
                : kind === "knowledge" ? dockContents.knowledge
                : dockContents.description
        }
    }

    Rectangle {
        id: snapPreview
        z: 19000
        visible: root.dockDragActive && root.activeSnapZone.length > 0
        x: root.activeSnapRect.x
        y: root.activeSnapRect.y
        width: root.activeSnapRect.width
        height: root.activeSnapRect.height
        color: root.theme.action
        opacity: 0.20
        border.color: root.theme.action
        border.width: 2
        Behavior on x { NumberAnimation { duration: theme.motionFast; easing.type: Easing.OutCubic } }
        Behavior on y { NumberAnimation { duration: theme.motionFast; easing.type: Easing.OutCubic } }
        Behavior on width { NumberAnimation { duration: theme.motionFast; easing.type: Easing.OutCubic } }
        Behavior on height { NumberAnimation { duration: theme.motionFast; easing.type: Easing.OutCubic } }
    }

    Item {
        id: snapGuide
        z: 20000
        visible: root.dockDragActive && root.activeSnapZone !== "swap"
        x: Math.max(0, Math.min(root.width - width,
            (root.activeSnapTargetId.length
                ? root.activeTargetRect.x + root.activeTargetRect.width / 2
                : root.width / 2) - width / 2))
        y: Math.max(0, Math.min(root.height - height,
            (root.activeSnapTargetId.length
                ? root.activeTargetRect.y + root.activeTargetRect.height / 2
                : root.height / 2) - height / 2))
        width: 132
        height: 132

        component GuideTile: Rectangle {
            required property string zone
            property bool selected: root.activeSnapZone === zone
            width: 38
            height: 38
            radius: 4
            color: selected ? root.theme.action : root.theme.panelRaised
            border.color: selected ? root.theme.selectedText : root.theme.border
            border.width: 1
            opacity: 0.96
            Behavior on color { ColorAnimation { duration: theme.motionInstant } }
        }

        GuideTile {
            zone: "left"
            x: 5; y: 47
            Rectangle { anchors.left: parent.left; anchors.leftMargin: 9; anchors.verticalCenter: parent.verticalCenter; width: 7; height: 20; radius: 1; color: parent.selected ? root.theme.selectedText : root.theme.secondaryText }
        }
        GuideTile {
            zone: "right"
            x: 89; y: 47
            Rectangle { anchors.right: parent.right; anchors.rightMargin: 9; anchors.verticalCenter: parent.verticalCenter; width: 7; height: 20; radius: 1; color: parent.selected ? root.theme.selectedText : root.theme.secondaryText }
        }
        GuideTile {
            zone: "top"
            x: 47; y: 5
            Rectangle { anchors.top: parent.top; anchors.topMargin: 9; anchors.horizontalCenter: parent.horizontalCenter; width: 20; height: 7; radius: 1; color: parent.selected ? root.theme.selectedText : root.theme.secondaryText }
        }
        GuideTile {
            zone: "bottom"
            x: 47; y: 89
            Rectangle { anchors.bottom: parent.bottom; anchors.bottomMargin: 9; anchors.horizontalCenter: parent.horizontalCenter; width: 20; height: 7; radius: 1; color: parent.selected ? root.theme.selectedText : root.theme.secondaryText }
        }
        GuideTile {
            zone: "center"
            x: 47; y: 47
            Rectangle { anchors.centerIn: parent; width: 18; height: 18; radius: 2; color: parent.selected ? root.theme.selectedText : root.theme.secondaryText }
        }
    }

    Rectangle {
        z: 20010
        visible: root.dockDragActive && root.activeSnapZone === "swap"
        anchors.centerIn: snapPreview
        width: swapLabel.implicitWidth + 24
        height: 30
        radius: 15
        color: root.theme.surfaceContainerHigh
        border.color: root.theme.action
        border.width: 1
        Label {
            id: swapLabel
            anchors.centerIn: parent
            text: qsTr("Swap panels")
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
            font.weight: Font.DemiBold
        }
    }

    DockContentRegistry {
        id: dockContents
        theme: root.theme
        pageTitle: root.pageTitle
        onNotice: message => root.notice(message)
        onRequestDockMenu: sourceItem => root.requestDockMenu(sourceItem)
    }
}

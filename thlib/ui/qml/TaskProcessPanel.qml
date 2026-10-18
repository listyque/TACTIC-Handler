import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls
import "features/tasks" as Tasks
import "tactic_frame" as Frame
import "tactic_frame/features/tasks/workspace.ui.mjs" as WorkspaceUI
import "tactic_frame/features/tasks/process.ui.mjs" as UI

Item {
    id: root
    required property var theme
    property bool presentationActive: true
    property int contextRow: -1

    function choiceIndex(values, selected) {
        for (let index = 0; index < values.length; ++index) {
            if (values[index].value === selected)
                return index;
        }
        return -1;
    }

    function openTaskMenu(anchor, row, hasTask, currentTaskCode, taskChoices) {
        const actions = [
            {
                title: qsTr("Add task"),
                icon: "add_task",
                command: "add"
            }
        ];
        if (hasTask) {
            actions.push({
                title: qsTr("Edit task"),
                icon: "edit",
                command: "edit"
            });
            actions.push({
                title: qsTr("Delete task"),
                icon: "delete",
                command: "delete"
            });
        }
        if (taskChoices.length > 1) {
            actions.push({
                separator: true
            });
            actions.push({
                title: qsTr("Tasks"),
                header: true
            });
            for (let index = 0; index < taskChoices.length; ++index) {
                actions.push({
                    title: taskChoices[index].label,
                    icon: "task_alt",
                    checked: taskChoices[index].value === currentTaskCode,
                    command: "select:" + taskChoices[index].value
                });
            }
        }
        contextRow = row;
        taskMenu.actions = actions;
        taskMenu.openBelow(anchor);
    }

    Controls.DockWorkspaceFooter {
        objectName: "quickTaskBackgroundSurface"
        anchors.fill: parent
        theme: root.theme
        topDividerVisible: false
        color: root.theme.panelDeep
    }

    Tasks.TaskProcessToolbar {
        id: toolbar
        theme: root.theme
        controller: tasksController
        width: parent.width
        height: implicitHeight
    }

    Item {
        id: contentArea
        opacity: (!tasksController.hasTarget || initialQuickTaskPresentation.ready) ? 1 : 0
        anchors.top: toolbar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: footer.top

        GridView {
            id: cardGrid
            anchors.fill: parent
            anchors.margins: UI.metrics.inset
            visible: tasksController.quickViewMode === "cards"
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            model: taskProcessModel
            readonly property int columnCount: UI.columns(width)
            cellWidth: width / columnCount
            cellHeight: UI.metrics.cardPitch

            delegate: Item {
                id: taskCard
                required property int index
                required property string process
                required property string label
                required property string color
                required property int taskCount
                required property bool hasTask
                required property string currentTaskCode
                required property string status
                required property string statusColor
                required property string assigned
                required property int notes
                required property var statusChoices
                required property var userChoices
                required property var taskChoices
                required property bool dirty
                width: cardGrid.cellWidth - UI.metrics.gap
                height: UI.metrics.cardHeight

                Tasks.TaskProcessItem {
                    anchors.fill: parent
                    theme: root.theme
                    controller: tasksController
                    users: userListModel
                    record: taskCard
                    mode: "cards"
                    onMenuRequested: source => root.openTaskMenu(source, taskCard.index, taskCard.hasTask, taskCard.currentTaskCode, taskCard.taskChoices)
                }
            }
            ScrollBar.vertical: Controls.ScrollBar {
                theme: root.theme
                flickableTarget: cardGrid
            }
        }

        Controls.SmoothListView {
            id: compactList
            theme: root.theme
            contentWidth: Math.max(width, UI.minimumWidth({
                dirty: tasksController.dirtyProcessCount > 0
            }))
            flickableDirection: Flickable.AutoFlickDirection
            ScrollBar.horizontal: Controls.ScrollBar {
                theme: root.theme
                flickableTarget: compactList
            }
            anchors.fill: parent
            anchors.margins: UI.metrics.inset
            visible: tasksController.quickViewMode === "compact"
            clip: true
            spacing: UI.metrics.compactGap
            model: taskProcessModel

            delegate: Item {
                id: taskRow
                required property int index
                required property string process
                required property string label
                required property string color
                required property int taskCount
                required property bool hasTask
                required property string currentTaskCode
                required property string status
                required property string assigned
                required property int notes
                required property var statusChoices
                required property var userChoices
                required property var taskChoices
                required property bool dirty
                width: compactList.contentWidth
                height: UI.metrics.compactHeight

                Tasks.TaskProcessItem {
                    anchors.fill: parent
                    theme: root.theme
                    controller: tasksController
                    users: userListModel
                    record: taskRow
                    mode: "compact"
                    onMenuRequested: source => root.openTaskMenu(source, taskRow.index, taskRow.hasTask, taskRow.currentTaskCode, taskRow.taskChoices)
                }
            }
            ScrollBar.vertical: Controls.ScrollBar {
                theme: root.theme
                flickableTarget: compactList
            }
        }

        Label {
            anchors.centerIn: parent
            visible: !tasksController.hasTarget
            text: qsTr("Select an sObject to view its task processes")
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
        }
    }

    Controls.InitialBatchPresentation {
        id: initialQuickTaskPresentation
        objectName: "initialQuickTaskPresentation"
        view: tasksController.quickViewMode === "cards" ? cardGrid : compactList
    }

    Controls.DockWorkspaceFooter {
        id: footer
        objectName: "quickTaskFooter"
        theme: root.theme
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        Frame.FrameView {
            anchors.fill: parent
            theme: root.theme
            scene: WorkspaceUI.footer({
                quick: true,
                processes: cardGrid.count,
                dirty: tasksController.dirtyProcessCount,
                busy: tasksController.busy
            }, width, typeof localizationController === "undefined" ? "en" : localizationController.current_language)
            views: ({
                    busy: {
                        component: busyPort
                    }
                })
        }
        Component {
            id: busyPort
            Controls.BusyIndicator {
                uiTheme: root.theme
                running: tasksController.busy
            }
        }
    }

    ActionMenu {
        id: taskMenu
        parent: root
        theme: root.theme
        onTriggered: command => {
            if (command === "add")
                tasksController.begin_create_for_process(root.contextRow);
            else if (command === "edit")
                tasksController.begin_edit_for_process(root.contextRow);
            else if (command === "delete")
                tasksController.remove_process_task(root.contextRow);
            else if (command.indexOf("select:") === 0) {
                tasksController.activate_process_task(root.contextRow, command.substring(7));
            }
        }
    }
}

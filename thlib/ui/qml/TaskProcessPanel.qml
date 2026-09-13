import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root
    required property var theme
    property bool presentationActive: true
    property int contextRow: -1

    function choiceIndex(values, selected) {
        for (let index = 0; index < values.length; ++index) {
            if (values[index].value === selected)
                return index
        }
        return -1
    }

    function openTaskMenu(
        anchor, row, hasTask, currentTaskCode, taskChoices
    ) {
        const actions = [{
            title: qsTr("Add task"), icon: "add_task", command: "add"
        }]
        if (hasTask) {
            actions.push({
                title: qsTr("Edit task"), icon: "edit", command: "edit"
            })
            actions.push({
                title: qsTr("Delete task"), icon: "delete", command: "delete"
            })
        }
        if (taskChoices.length > 1) {
            actions.push({ separator: true })
            actions.push({ title: qsTr("Tasks"), header: true })
            for (let index = 0; index < taskChoices.length; ++index) {
                actions.push({
                    title: taskChoices[index].label,
                    icon: "task_alt",
                    checked: taskChoices[index].value === currentTaskCode,
                    command: "select:" + taskChoices[index].value
                })
            }
        }
        contextRow = row
        taskMenu.actions = actions
        taskMenu.openBelow(anchor)
    }

    Controls.DockWorkspaceFooter {
        objectName: "quickTaskBackgroundSurface"
        anchors.fill: parent
        theme: root.theme
        topDividerVisible: false
        color: root.theme.panelDeep
    }

    Rectangle {
        id: toolbar
        anchors.top: parent.top
        width: parent.width
        height: root.theme.dockWorkspaceHeaderHeight
            - root.theme.dockTitleHeight
        color: root.theme.toolBar
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 10
            anchors.rightMargin: 7
            spacing: 4
            Controls.MaterialIcon {
                name: "task_alt"; size: 17; color: root.theme.action
            }
            Label {
                Layout.fillWidth: true
                text: tasksController.hasTarget
                    ? tasksController.targetTitle : qsTr("Select an sObject")
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.bodyLarge
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }
            Controls.CompactIconButton {
                theme: root.theme
                iconName: "save"
                iconColor: tasksController.dirtyProcessCount > 0
                        && !tasksController.busy
                    ? root.theme.action : root.theme.disabledText
                toolTip: qsTr("Save all task changes")
                enabled: tasksController.dirtyProcessCount > 0
                    && !tasksController.busy
                onClicked: tasksController.save_all_process_changes()
            }
            Controls.CompactIconButton {
                theme: root.theme
                iconName: "undo"
                iconColor: tasksController.dirtyProcessCount > 0
                        && !tasksController.busy
                    ? root.theme.primaryText : root.theme.disabledText
                toolTip: qsTr("Reset all task changes")
                enabled: tasksController.dirtyProcessCount > 0
                    && !tasksController.busy
                onClicked: tasksController.discard_all_process_changes()
            }
            TaskWorkspaceSurfaceSwitcher {
                objectName: "quickTaskWorkspaceSurfaceSwitcher"
                theme: root.theme
                Layout.minimumWidth: implicitWidth
                Layout.preferredWidth: implicitWidth
                Layout.maximumWidth: implicitWidth
            }
            RefreshIconButton {
                objectName: "quickTaskRefreshButton"
                theme: root.theme
                Layout.minimumWidth: 38
                Layout.preferredWidth: 38
                Layout.maximumWidth: 38
                Layout.preferredHeight: 38
                toolTip: qsTr("Refresh tasks")
                enabled: tasksController.hasTarget && !tasksController.busy
                onClicked: tasksController.refresh()
            }
        }
    }

    Item {
        id: contentArea
        opacity: (
            !tasksController.hasTarget
            || initialQuickTaskPresentation.ready
        ) ? 1 : 0
        anchors.top: toolbar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: footer.top

        GridView {
            id: cardGrid
            anchors.fill: parent
            anchors.margins: 6
            visible: tasksController.quickViewMode === "cards"
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            model: taskProcessModel
            readonly property int columnCount: Math.max(1, Math.floor(width / 224))
            cellWidth: width / columnCount
            cellHeight: 126

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
                width: cardGrid.cellWidth - 7
                height: cardGrid.cellHeight - 7

                Rectangle {
                    anchors.fill: parent
                    radius: root.theme.surfaceRadius
                    color: taskCard.hasTask
                        ? root.theme.surfaceContainer
                        : root.theme.surfaceContainerLow
                    border.width: taskCard.dirty ? 1 : 0
                    border.color: root.theme.action
                }
                Rectangle {
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: 3
                    radius: 1.5
                    color: taskCard.color
                }
                ColumnLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 10
                    anchors.rightMargin: 8
                    anchors.topMargin: 8
                    anchors.bottomMargin: 8
                    spacing: 5
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 5
                        Rectangle {
                            Layout.preferredWidth: 12
                            Layout.preferredHeight: 12
                            radius: 6
                            color: taskCard.color
                        }
                        Label {
                            Layout.fillWidth: true
                            text: taskCard.taskCount > 1
                                ? taskCard.label + " | " + taskCard.taskCount
                                : taskCard.label
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.bodyLarge
                            font.weight: Font.DemiBold
                            elide: Text.ElideRight
                        }
                        Controls.CompactIconButton {
                            visible: taskCard.dirty
                            enabled: !tasksController.busy
                            theme: root.theme
                            iconName: "undo"
                            toolTip: qsTr("Reset task changes")
                            onClicked: tasksController.discard_process_changes(taskCard.index)
                        }
                        Controls.CompactIconButton {
                            visible: taskCard.dirty
                            enabled: !tasksController.busy
                            theme: root.theme
                            iconName: "save"
                            iconColor: root.theme.action
                            toolTip: taskCard.hasTask
                                ? qsTr("Save task changes") : qsTr("Create task")
                            onClicked: tasksController.save_process_changes(taskCard.index)
                        }
                        Controls.ItemCountActionButton {
                            theme: root.theme
                            iconName: "comment"
                            count: taskCard.notes
                            badgeColor: root.theme.error
                            enabled: tasksController.hasTarget
                            toolTip: qsTr("Open notes")
                            onClicked: tasksController.open_notes(
                                tasksController.targetSearchKey, taskCard.process,
                                taskCard.currentTaskCode
                            )
                        }
                        Controls.CompactIconButton {
                            id: cardMenuButton
                            theme: root.theme
                            iconName: "more_vert"
                            toolTip: qsTr("Task actions")
                            onClicked: root.openTaskMenu(
                                cardMenuButton, taskCard.index,
                                taskCard.hasTask, taskCard.currentTaskCode,
                                taskCard.taskChoices
                            )
                        }
                    }
                    Controls.ComboBox {
                        theme: root.theme
                        actionField: true
                        enabled: !tasksController.busy
                        Layout.fillWidth: true
                        Layout.preferredHeight: 28
                        model: taskCard.statusChoices
                        textRole: "label"
                        valueRole: "value"
                        colorRole: "color"
                        currentIndex: root.choiceIndex(
                            taskCard.statusChoices, taskCard.status
                        )
                        displayText: currentIndex >= 0
                            ? currentText : "Select status"
                        onActivated: tasksController.set_process_draft(
                            taskCard.index, "status", currentValue
                        )
                    }
                    UserComboBox {
                        theme: root.theme
                        actionField: true
                        enabled: !tasksController.busy
                        Layout.fillWidth: true
                        Layout.preferredHeight: 28
                        userModel: userListModel
                        model: taskCard.userChoices
                        textRole: "label"
                        valueRole: "value"
                        currentIndex: root.choiceIndex(
                            taskCard.userChoices, taskCard.assigned
                        )
                        onActivated: tasksController.set_process_draft(
                            taskCard.index, "assigned", currentValue
                        )
                    }
                }
            }
            ScrollBar.vertical: Controls.ScrollBar {
                theme: root.theme
                flickableTarget: cardGrid
            }
        }

        Controls.SmoothListView {
            theme: root.theme
            id: compactList
            anchors.fill: parent
            anchors.margins: 6
            visible: tasksController.quickViewMode === "compact"
            clip: true
            spacing: 5
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
                width: compactList.width
                height: 44

                Rectangle {
                    anchors.fill: parent
                    radius: root.theme.itemRadius
                    color: root.theme.surfaceContainer
                }
                Rectangle {
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    width: 3
                    height: parent.height - 12
                    radius: 1.5
                    color: taskRow.color
                }
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 11
                    anchors.rightMargin: 7
                    spacing: 7
                    Rectangle {
                        Layout.preferredWidth: 11
                        Layout.preferredHeight: 11
                        radius: 5.5
                        color: taskRow.color
                    }
                    Label {
                        Layout.preferredWidth: 100
                        text: taskRow.taskCount > 1
                            ? taskRow.label + " | " + taskRow.taskCount
                            : taskRow.label
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.body
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                    }
                    Controls.ComboBox {
                        theme: root.theme
                        actionField: true
                        enabled: !tasksController.busy
                        Layout.preferredWidth: 112
                        Layout.preferredHeight: 29
                        model: taskRow.statusChoices
                        textRole: "label"
                        valueRole: "value"
                        colorRole: "color"
                        currentIndex: root.choiceIndex(
                            taskRow.statusChoices, taskRow.status
                        )
                        displayText: currentIndex >= 0
                            ? currentText : "Status"
                        onActivated: tasksController.set_process_draft(
                            taskRow.index, "status", currentValue
                        )
                    }
                    UserComboBox {
                        theme: root.theme
                        actionField: true
                        enabled: !tasksController.busy
                        userModel: userListModel
                        Layout.fillWidth: true
                        Layout.minimumWidth: 110
                        Layout.preferredHeight: 29
                        model: taskRow.userChoices
                        textRole: "label"
                        valueRole: "value"
                        currentIndex: root.choiceIndex(
                            taskRow.userChoices, taskRow.assigned
                        )
                        onActivated: tasksController.set_process_draft(
                            taskRow.index, "assigned", currentValue
                        )
                    }
                    Controls.CompactIconButton {
                        visible: taskRow.dirty
                        enabled: !tasksController.busy
                        theme: root.theme
                        iconName: "undo"
                        toolTip: qsTr("Reset task changes")
                        onClicked: tasksController.discard_process_changes(taskRow.index)
                    }
                    Controls.CompactIconButton {
                        visible: taskRow.dirty
                        enabled: !tasksController.busy
                        theme: root.theme
                        iconName: "save"
                        iconColor: root.theme.action
                        toolTip: taskRow.hasTask
                            ? qsTr("Save task changes") : qsTr("Create task")
                        onClicked: tasksController.save_process_changes(taskRow.index)
                    }
                    Controls.ItemCountActionButton {
                        theme: root.theme
                        iconName: "comment"
                        count: taskRow.notes
                        badgeColor: root.theme.error
                        enabled: tasksController.hasTarget
                            toolTip: qsTr("Open notes")
                            onClicked: tasksController.open_notes(
                                tasksController.targetSearchKey, taskRow.process,
                                taskRow.currentTaskCode
                            )
                    }
                    Controls.CompactIconButton {
                        id: rowMenuButton
                        theme: root.theme
                        iconName: "more_vert"
                        toolTip: qsTr("Task actions")
                        onClicked: root.openTaskMenu(
                            rowMenuButton, taskRow.index,
                            taskRow.hasTask, taskRow.currentTaskCode,
                            taskRow.taskChoices
                        )
                    }
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
        view: tasksController.quickViewMode === "cards"
            ? cardGrid : compactList
    }

    Controls.DockWorkspaceFooter {
        id: footer
        objectName: "quickTaskFooter"
        theme: root.theme
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 12
            anchors.rightMargin: 10
            spacing: 8
            Controls.MaterialIcon {
                name: "task-alt"
                size: 16
                color: root.theme.secondaryText
            }
            Label {
                text: cardGrid.count + (
                    cardGrid.count === 1
                        ? qsTr(" process") : qsTr(" processes")
                )
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.body
                font.weight: Font.Medium
            }
            Item { Layout.fillWidth: true }
            Label {
                visible: tasksController.dirtyProcessCount > 0
                text: tasksController.dirtyProcessCount + qsTr(" unsaved")
                color: root.theme.action
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.label
                font.weight: Font.DemiBold
            }
            Controls.BusyIndicator {
                uiTheme: root.theme
                Layout.preferredWidth: 22
                Layout.preferredHeight: 22
                visible: tasksController.busy
                running: visible
            }
        }
    }

    ActionMenu {
        id: taskMenu
        parent: root
        theme: root.theme
        onTriggered: command => {
            if (command === "add")
                tasksController.begin_create_for_process(root.contextRow)
            else if (command === "edit")
                tasksController.begin_edit_for_process(root.contextRow)
            else if (command === "delete")
                tasksController.remove_process_task(root.contextRow)
            else if (command.indexOf("select:") === 0) {
                tasksController.activate_process_task(
                    root.contextRow, command.substring(7)
                )
            }
        }
    }
}

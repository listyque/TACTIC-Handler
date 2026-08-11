import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    required property var theme
    property int contextRow: -1
    property int pendingDeleteRow: -1

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

    Rectangle { anchors.fill: parent; color: root.theme.panelDeep }

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
            MaterialIcon {
                name: "task_alt"; size: 17; color: root.theme.action
            }
            Label {
                Layout.fillWidth: true
                text: tasksController.hasTarget
                    ? tasksController.targetTitle : qsTr("Select an sObject")
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 11
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }
            CompactIconButton {
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
            CompactIconButton {
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
            CompactIconButton {
                theme: root.theme
                iconName: "grid_view"
                iconColor: tasksController.quickViewMode === "cards"
                    ? root.theme.action : root.theme.secondaryText
                backgroundColor: tasksController.quickViewMode === "cards"
                    ? root.theme.secondaryContainer : "transparent"
                toolTip: qsTr("Task cards")
                onClicked: tasksController.set_quick_view_mode("cards")
            }
            CompactIconButton {
                theme: root.theme
                iconName: "view_list"
                iconColor: tasksController.quickViewMode === "compact"
                    ? root.theme.action : root.theme.secondaryText
                backgroundColor: tasksController.quickViewMode === "compact"
                    ? root.theme.secondaryContainer : "transparent"
                toolTip: qsTr("Compact task list")
                onClicked: tasksController.set_quick_view_mode("compact")
            }
            CompactIconButton {
                theme: root.theme
                iconName: "dashboard_customize"
                toolTip: qsTr("Open task workspace")
                onClicked: tasksController.open_workspace()
            }
            RefreshIconButton {
                theme: root.theme
                toolTip: qsTr("Refresh tasks")
                enabled: tasksController.hasTarget && !tasksController.busy
                onClicked: tasksController.refresh()
            }
        }
    }

    Item {
        id: contentArea
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
                            font.pixelSize: 11
                            font.weight: Font.DemiBold
                            elide: Text.ElideRight
                        }
                        CompactIconButton {
                            visible: taskCard.dirty
                            enabled: !tasksController.busy
                            theme: root.theme
                            iconName: "undo"
                            toolTip: qsTr("Reset task changes")
                            onClicked: tasksController.discard_process_changes(taskCard.index)
                        }
                        CompactIconButton {
                            visible: taskCard.dirty
                            enabled: !tasksController.busy
                            theme: root.theme
                            iconName: "save"
                            iconColor: root.theme.action
                            toolTip: taskCard.hasTask
                                ? qsTr("Save task changes") : qsTr("Create task")
                            onClicked: tasksController.save_process_changes(taskCard.index)
                        }
                        CompactIconButton {
                            theme: root.theme
                            iconName: "comment"
                            badgeCount: taskCard.notes
                            enabled: tasksController.hasTarget
                            toolTip: qsTr("Open notes")
                            onClicked: tasksController.open_notes(
                                tasksController.targetSearchKey, taskCard.process,
                                taskCard.currentTaskCode
                            )
                        }
                        CompactIconButton {
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
                    Md3ComboBox {
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
                    Md3UserComboBox {
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
            ScrollBar.vertical: Md3ScrollBar {
                theme: root.theme
                flickableTarget: cardGrid
            }
        }

        SmoothListView {
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
                        font.pixelSize: 10
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                    }
                    Md3ComboBox {
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
                    Md3UserComboBox {
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
                    CompactIconButton {
                        visible: taskRow.dirty
                        enabled: !tasksController.busy
                        theme: root.theme
                        iconName: "undo"
                        toolTip: qsTr("Reset task changes")
                        onClicked: tasksController.discard_process_changes(taskRow.index)
                    }
                    CompactIconButton {
                        visible: taskRow.dirty
                        enabled: !tasksController.busy
                        theme: root.theme
                        iconName: "save"
                        iconColor: root.theme.action
                        toolTip: taskRow.hasTask
                            ? qsTr("Save task changes") : qsTr("Create task")
                        onClicked: tasksController.save_process_changes(taskRow.index)
                    }
                    CompactIconButton {
                        theme: root.theme
                        iconName: "comment"
                        badgeCount: taskRow.notes
                        enabled: tasksController.hasTarget
                            toolTip: qsTr("Open notes")
                            onClicked: tasksController.open_notes(
                                tasksController.targetSearchKey, taskRow.process,
                                taskRow.currentTaskCode
                            )
                    }
                    CompactIconButton {
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
            ScrollBar.vertical: Md3ScrollBar {
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
            font.pixelSize: 10
        }
    }

    Rectangle {
        id: footer
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: root.theme.dockWorkspaceFooterHeight
        color: root.theme.surfaceContainerHigh

        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: 1
            color: root.theme.outlineVariant
        }
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 12
            anchors.rightMargin: 10
            spacing: 8
            MaterialIcon {
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
                font.pixelSize: 10
                font.weight: Font.Medium
            }
            Item { Layout.fillWidth: true }
            Label {
                visible: tasksController.dirtyProcessCount > 0
                text: tasksController.dirtyProcessCount + qsTr(" unsaved")
                color: root.theme.action
                font.family: root.theme.fontFamily
                font.pixelSize: 9
                font.weight: Font.DemiBold
            }
            Md3BusyIndicator {
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
            else if (command === "delete") {
                root.pendingDeleteRow = root.contextRow
                deleteDialog.open()
            } else if (command.indexOf("select:") === 0) {
                tasksController.activate_process_task(
                    root.contextRow, command.substring(7)
                )
            }
        }
    }

    Md3Dialog {
        id: deleteDialog
        parent: root
        theme: root.theme
        title: qsTr("Delete task?")
        anchors.centerIn: parent
        width: Math.min(390, root.width - 24)
        contentItem: Label {
            text: qsTr("This task and its dependent data will be removed.")
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pixelSize: 11
            wrapMode: Text.WordWrap
        }
        footer: DialogButtonBox {
            background: Item {}
            Md3Button {
                theme: root.theme
                text: qsTr("Cancel")
                onClicked: deleteDialog.close()
            }
            Md3Button {
                theme: root.theme
                text: qsTr("Delete")
                destructive: true
                onClicked: {
                    tasksController.remove_process_task(root.pendingDeleteRow)
                    deleteDialog.close()
                }
            }
        }
    }

    Component.onCompleted: tasksController.set_compact_visible(true)
    Component.onDestruction: tasksController.set_compact_visible(false)
}

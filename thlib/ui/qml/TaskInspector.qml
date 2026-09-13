import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Rectangle {
    id: root

    required property var theme
    required property var controller
    property var task: controller.currentTask
    property var objectInfo: controller.selectedObject
    readonly property bool hasTask: String(task.code || "").length > 0
    readonly property int processRow: task.processRow === undefined
        || task.processRow === null ? -1 : Number(task.processRow)
    readonly property bool expanded: controller.taskExpanded
    signal editRequested(string taskCode)

    visible: controller.hasTarget
    implicitHeight: !visible ? 0 : inspectorLayout.implicitHeight + 12
    color: theme.surfaceContainerLow
    clip: true

    function objectInitials() {
        const words = String(objectInfo.title || "")
            .trim().split(/\s+|_+/).filter(Boolean)
        if (!words.length)
            return ""
        return words.slice(0, 2).map(function(word) {
            return word.charAt(0).toUpperCase()
        }).join("")
    }

    function choiceIndex(values, selected) {
        const source = values || []
        for (let index = 0; index < source.length; ++index) {
            if (String(source[index].value || "") === String(selected || ""))
                return index
        }
        return -1
    }

    function processRecord() {
        const processes = controller.processChoices || []
        for (let index = 0; index < processes.length; ++index) {
            if (String(processes[index].value || "") === controller.process)
                return processes[index]
        }
        return {}
    }

    function taskTitle() {
        const context = String(task.context || "").trim()
        if (context && context !== controller.process)
            return context
        return controller.processLabel + qsTr(" task")
    }

    function processMenuActions() {
        const actions = [{"header": true, "title": "Process and note context"}]
        const processes = controller.processChoices
        for (let i = 0; i < processes.length; ++i) {
            const process = processes[i]
            const noteCount = Number(process.count || 0)
            const processType = String(process.type || "")
            const typeLabel = processType === "built-in"
                ? qsTr("Built-in") : processType
            const noteLabel = String(noteCount)
                + qsTr(noteCount === 1 ? " note" : " notes")
            actions.push({
                // Process labels are project data. Never translate them.
                "title": String(process.label || process.value || ""),
                "translate": false,
                "status": typeLabel.length
                    ? typeLabel + " · " + noteLabel : noteLabel,
                "statusTranslate": false,
                "accent": process.color || root.theme.action,
                "command": "process:" + process.value,
                "checked": process.value === controller.process
            })
        }
        return actions
    }

    function taskMenuActions() {
        const actions = [{"header": true, "title": "Tasks for this process"}]
        const choices = controller.taskChoices
        for (let i = 0; i < choices.length; ++i) {
            const choice = choices[i]
            actions.push({
                "title": choice.primaryBranch
                    ? choice.label + " · " + qsTr("Main") : choice.label,
                "status": choice.status,
                "translate": false,
                "statusTranslate": false,
                "icon": "task_alt",
                "avatarUrl": choice.avatarUrl || "",
                "avatarColor": choice.avatarColor || root.theme.action,
                "initials": choice.initials || "",
                "command": "task:" + choice.value,
                "badgeCount": Number(choice.noteCount || 0),
                "showZeroBadge": true,
                "checked": choice.selected === true
            })
        }
        return actions
    }

    GridLayout {
        id: inspectorLayout
        columns: 1
        anchors.fill: parent
        anchors.leftMargin: 8
        anchors.rightMargin: 8
        anchors.topMargin: 5
        anchors.bottomMargin: 7
        rowSpacing: 5
        columnSpacing: 0

        Rectangle {
            id: taskSurface
            objectName: "taskInspectorTaskSurface"
            Layout.row: 2
            Layout.column: 0
            visible: root.expanded
            Layout.fillWidth: true
            Layout.preferredHeight: visible ? 148 : 0
            radius: root.theme.itemRadius
            color: root.theme.panelDeep
            border.width: 1
            border.color: root.theme.outlineVariant
            clip: true

            ColumnLayout {
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 8
                anchors.topMargin: 7
                anchors.bottomMargin: 7
                spacing: 6

                RowLayout {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 28
                    spacing: 7

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 1
                        Label {
                            objectName: "taskInspectorTaskTitle"
                            Layout.fillWidth: true
                            text: root.processRow >= 0
                                ? root.taskTitle()
                                : qsTr("No task for ")
                                    + root.controller.processLabel
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.bodyLarge
                            font.weight: Font.DemiBold
                            elide: Text.ElideRight
                        }
                        Label {
                            visible: root.expanded && root.processRow >= 0
                                && String(root.task.assignedDisplay || "").length > 0
                            Layout.fillWidth: true
                            text: root.task.assignedDisplay
                                || qsTr("Not assigned")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
                            elide: Text.ElideRight
                        }
                    }

                    Controls.CompactIconButton {
                        objectName: "taskInspectorEditButton"
                        visible: root.hasTask
                        theme: root.theme
                        iconName: "edit"
                        toolTip: qsTr("Edit task in full editor")
                        onClicked: root.editRequested(String(root.task.code || ""))
                    }
                    Controls.CompactIconButton {
                        objectName: "taskInspectorFullCreateButton"
                        visible: root.processRow >= 0
                        theme: root.theme
                        iconName: "add"
                        toolTip: qsTr("Create another task in full editor")
                        enabled: !root.controller.busy
                        onClicked: root.controller.create_task_for_process()
                    }
                    Controls.CompactIconButton {
                        objectName: "taskInspectorDiscardButton"
                        visible: root.processRow >= 0
                            && root.task.dirty === true
                        theme: root.theme
                        iconName: "undo"
                        toolTip: qsTr("Discard task changes")
                        enabled: !tasksController.busy
                        onClicked: tasksController.discard_process_changes(
                            root.processRow
                        )
                    }
                    Controls.CompactIconButton {
                        objectName: "taskInspectorSaveButton"
                        visible: root.processRow >= 0
                            && (!root.hasTask || root.task.dirty === true)
                        theme: root.theme
                        iconName: "save"
                        iconColor: root.theme.action
                        toolTip: root.hasTask
                            ? qsTr("Save task changes") : qsTr("Save new task")
                        enabled: !tasksController.busy
                            && String(root.task.validationError || "").length === 0
                        onClicked: tasksController.save_process_changes(
                            root.processRow
                        )
                    }
                }

                GridLayout {
                    visible: root.expanded && root.processRow >= 0
                    Layout.fillWidth: true
                    columns: width < 430 ? 2 : 4
                    columnSpacing: 7
                    rowSpacing: 7

                    Controls.ComboBox {
                        objectName: "taskInspectorStatusField"
                        theme: root.theme
                        actionField: true
                        Layout.fillWidth: true
                        Layout.preferredHeight: root.theme.compactControlHeight
                        model: root.task.statusChoices || []
                        textRole: "label"
                        valueRole: "value"
                        colorRole: "color"
                        currentIndex: root.choiceIndex(
                            root.task.statusChoices, root.task.status
                        )
                        displayText: currentIndex >= 0
                            ? currentText : root.task.status || "Select status"
                        enabled: !tasksController.busy
                        onActivated: tasksController.set_process_draft(
                            root.processRow, "status", currentValue
                        )
                    }

                    UserComboBox {
                        objectName: "taskInspectorAssigneeField"
                        theme: root.theme
                        actionField: true
                        Layout.fillWidth: true
                        Layout.preferredHeight: root.theme.compactControlHeight
                        userModel: userListModel
                        model: root.task.userChoices || []
                        textRole: "label"
                        valueRole: "value"
                        currentIndex: root.choiceIndex(
                            root.task.userChoices, root.task.assigned
                        )
                        displayText: currentIndex >= 0
                            ? currentText : root.task.assignedDisplay
                        enabled: !tasksController.busy
                        onActivated: tasksController.set_process_draft(
                            root.processRow, "assigned", currentValue
                        )
                    }

                    Controls.DateField {
                        theme: root.theme
                        Layout.fillWidth: true
                        Layout.preferredHeight: root.theme.compactControlHeight
                        placeholderText: qsTr("Start date and time")
                        includeTime: true
                        text: String(root.task.start || "")
                        enabled: !tasksController.busy
                        errorState: String(root.task.validationError || "")
                            .indexOf("Start") >= 0
                        onAccepted: value => tasksController.set_process_draft(
                            root.processRow, "start", value
                        )
                        onEditingFinished: {
                            if (text !== String(root.task.start || ""))
                                tasksController.set_process_draft(
                                    root.processRow, "start", text
                                )
                        }
                    }

                    Controls.DateField {
                        theme: root.theme
                        Layout.fillWidth: true
                        Layout.preferredHeight: root.theme.compactControlHeight
                        placeholderText: qsTr("End date and time")
                        includeTime: true
                        text: String(root.task.end || "")
                        enabled: !tasksController.busy
                        errorState: String(root.task.validationError || "")
                            .indexOf("End") >= 0
                            || String(root.task.validationError || "")
                                .indexOf("Deadline") >= 0
                        onAccepted: value => tasksController.set_process_draft(
                            root.processRow, "end", value
                        )
                        onEditingFinished: {
                            if (text !== String(root.task.end || ""))
                                tasksController.set_process_draft(
                                    root.processRow, "end", text
                                )
                        }
                    }
                }

                RowLayout {
                    visible: root.expanded && root.processRow >= 0
                    Layout.fillWidth: true
                    spacing: 7

                    Label {
                        text: qsTr("PROGRESS")
                        color: tasksController.progressSupported
                            ? root.theme.secondaryText
                            : root.theme.disabledText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                        font.weight: Font.DemiBold
                    }
                    Controls.Slider {
                        id: progressSlider
                        Layout.fillWidth: true
                        Layout.preferredHeight: 24
                        theme: root.theme
                        from: 0
                        to: 100
                        stepSize: 5
                        snapMode: Slider.SnapAlways
                        value: Math.max(0, Math.min(100, Number(
                            root.task.progressInput !== undefined
                                ? root.task.progressInput
                                : root.task.progress || 0
                        )))
                        enabled: tasksController.progressSupported
                            && !tasksController.busy
                        onPressedChanged: {
                            if (!pressed && enabled
                                    && Math.round(value)
                                        !== Number(root.task.progress || 0)) {
                                tasksController.set_process_draft(
                                    root.processRow, "progress",
                                    String(Math.round(value))
                                )
                            }
                        }
                    }
                    Label {
                        Layout.preferredWidth: 34
                        text: Math.round(progressSlider.value) + "%"
                        color: progressSlider.enabled
                            ? root.theme.primaryText
                            : root.theme.disabledText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                        font.weight: Font.DemiBold
                        horizontalAlignment: Text.AlignRight
                    }
                }

                Label {
                    visible: root.expanded && root.processRow >= 0
                        && String(root.task.validationError || "").length > 0
                    Layout.fillWidth: true
                    text: String(root.task.validationError || "")
                    color: root.theme.error
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.caption
                    elide: Text.ElideRight
                }
            }
        }

        WorkHoursSummary {
            objectName: "taskInspectorWorkHours"
            Layout.row: 1
            Layout.column: 0
            visible: root.hasTask
            Layout.fillWidth: true
            Layout.preferredHeight: visible ? (root.expanded ? 80 : 32) : 0
            theme: root.theme
            controller: workHoursController
            compact: !root.expanded
        }

        Rectangle {
            id: contextHeader
            Layout.row: 0
            Layout.column: 0
            Layout.fillWidth: true
            Layout.preferredHeight: 46
            Layout.minimumHeight: 46
            Layout.maximumHeight: 46
            radius: root.theme.itemRadius
            color: root.theme.surfaceContainerHigh

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 7
                anchors.rightMargin: 6
                spacing: 7

                Controls.CompactIconButton {
                    Layout.preferredWidth: 24
                    Layout.preferredHeight: 24
                    Layout.alignment: Qt.AlignVCenter
                    theme: root.theme
                    iconName: root.expanded ? "expand_more" : "chevron-right"
                    iconSize: 13
                    toolTip: root.expanded
                        ? qsTr("Collapse Task Inspector")
                        : qsTr("Expand Task Inspector")
                    onClicked: root.controller.toggle_task_expanded()
                }

                Controls.ItemPreview {
                    Layout.preferredWidth: 32
                    Layout.preferredHeight: 32
                    theme: root.theme
                    source: root.objectInfo.previewUrl || ""
                    fallbackIcon: "inventory_2"
                    fallbackText: root.objectInitials()
                    previewSize: 32
                    round: true
                    outlined: true
                    accent: root.theme.action
                    animateAppearance: false
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 1
                    Label {
                        id: objectTitle
                        Layout.fillWidth: true
                        text: root.objectInfo.title || qsTr("Selected object")
                        color: objectTitleMouse.containsMouse
                            ? root.theme.action : root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                        MouseArea {
                            id: objectTitleMouse
                            anchors.fill: parent
                            enabled: String(root.objectInfo.searchKey || "").length > 0
                            hoverEnabled: true
                            cursorShape: enabled
                                ? Qt.PointingHandCursor : Qt.ArrowCursor
                            onClicked: root.controller.open_skey_preview(
                                String(root.objectInfo.searchKey || "")
                            )
                        }
                    }
                    Label {
                        Layout.fillWidth: true
                        text: root.objectInfo.type || "sObject"
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                        elide: Text.ElideRight
                    }
                }

                Rectangle {
                    id: processPicker
                    Layout.preferredWidth: Math.max(
                        112, Math.min(166, root.width * 0.34)
                    )
                    Layout.preferredHeight: root.theme.compactControlHeight
                    Layout.alignment: Qt.AlignVCenter
                    radius: root.theme.fieldRadius
                    color: processPickerMouse.containsMouse
                        ? root.theme.rowHover : root.theme.panelDeep
                    border.width: 1
                    border.color: processMenu.opened
                        ? root.theme.action : root.theme.outlineVariant

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 10
                        anchors.rightMargin: 8
                        spacing: 7
                        Rectangle {
                            Layout.preferredWidth: 8
                            Layout.preferredHeight: 8
                            radius: 4
                            color: root.processRecord().color || root.theme.action
                        }
                        Label {
                            Layout.fillWidth: true
                            text: root.controller.processLabel
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.label
                            font.weight: Font.DemiBold
                            elide: Text.ElideRight
                        }
                        Controls.MaterialIcon {
                            name: processMenu.opened
                                ? "expand_less" : "expand_more"
                            size: 15
                            color: root.theme.secondaryText
                        }
                    }
                    MouseArea {
                        id: processPickerMouse
                        anchors.fill: parent
                        enabled: root.controller.hasTarget && !root.controller.busy
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onPressed: processMenu.sourceWasOpen = processMenu.opened
                        onClicked: processMenu.toggleBelow(processPicker)
                    }
                }

                Controls.CompactIconButton {
                    id: taskSwitchButton
                    objectName: "taskInspectorTaskSwitchButton"
                    visible: root.hasTask
                        && root.controller.taskChoices.length > 1
                    Layout.preferredWidth: 28
                    Layout.preferredHeight: 28
                    Layout.alignment: Qt.AlignVCenter
                    theme: root.theme
                    iconName: "swap_horiz"
                    iconColor: taskMenu.opened
                        ? root.theme.action : root.theme.primaryText
                    toolTip: qsTr("Switch task for this process")
                    onPressed: taskMenu.sourceWasOpen = taskMenu.opened
                    onClicked: taskMenu.toggleBelow(taskSwitchButton)
                }

                RefreshIconButton {
                    theme: root.theme
                    toolTip: qsTr("Refresh notes and task")
                    enabled: root.controller.hasTarget && !root.controller.busy
                    onClicked: root.controller.refresh()
                }
            }
        }
    }

    ActionMenu {
        id: processMenu
        parent: Overlay.overlay
        theme: root.theme
        preferredWidth: 320
        actions: root.processMenuActions()
        onTriggered: command => {
            if (command.indexOf("process:") === 0)
                root.controller.set_process(command.slice(8))
        }
    }

    ActionMenu {
        id: taskMenu
        parent: Overlay.overlay
        theme: root.theme
        preferredWidth: 330
        actions: root.taskMenuActions()
        onTriggered: command => {
            if (command.indexOf("task:") === 0)
                root.controller.select_task(command.slice(5))
        }
    }
}

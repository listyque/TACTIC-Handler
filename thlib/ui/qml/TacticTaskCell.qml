pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    required property var controller
    required property var columnsController
    required property var userModel
    required property string nodeId
    property var records: []
    property var options: ({})
    property int taskCount: 0
    property bool scrolling: false
    readonly property int cardWidth: 100
    readonly property int fullCardCount: Math.max(
        0, Math.floor(width / cardWidth)
    )
    readonly property bool showMenuButton:
        !records || records.length === 0
        || records.length > fullCardCount
    readonly property int visibleCardCount: Math.max(
        0, Math.floor(
            (width - (showMenuButton ? 32 : 0)) / cardWidth
        )
    )
    readonly property int effectiveCount: Math.max(
        taskCount, records ? records.filter(
            record => Boolean(record.hasTask)
        ).length : 0
    )

    signal processPickerRequested(var anchorItem)

    function choiceIndex(choices, value) {
        const wanted = String(value || "")
        for (let index = 0; index < (choices || []).length; ++index) {
            if (String(choices[index].value || "") === wanted)
                return index
        }
        return -1
    }

    function openTask(record) {
        const process = String(record.process || "publish")
        const taskCode = String(record.taskCode || "")
        if (taskCode) {
            controller.open_process_task_details(
                nodeId, "tasks", process, taskCode
            )
        } else {
            controller.open_process_details(nodeId, "tasks", process)
        }
    }

    clip: true

    TaskEditorReleaseCoordinator {
        id: editorReleaseCoordinator
        theme: root.theme
    }

    Row {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        spacing: 4

        Repeater {
            model: (root.records || []).slice(0, root.visibleCardCount)

            delegate: Rectangle {
                id: taskCard

                required property int index
                required property var modelData
                readonly property color taskColor:
                    String(modelData.statusColor || "").length > 0
                        ? modelData.statusColor
                        : String(modelData.processColor || "").length > 0
                            ? modelData.processColor : root.theme.action
                readonly property string processLabel: String(
                    modelData.processLabel || modelData.process
                    || modelData.context || qsTr("Task")
                )
                readonly property real editorHeight: Math.max(
                    15, Math.min(22, (height - 18) / 2)
                )

                objectName: "tableTaskRecord_" + index
                anchors.verticalCenter: parent.verticalCenter
                width: root.cardWidth - 5
                height: Math.min(62, root.height - 2)
                radius: root.theme.itemRadius
                color: root.theme.overlay(
                    root.theme.surfaceContainerHigh, taskColor, 0.1
                )
                border.width: 1
                border.color: root.theme.overlay(
                    root.theme.outlineVariant, taskColor, 0.34
                )

                HoverHandler {
                    id: taskCardHover
                }

                Rectangle {
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: 3
                    radius: width / 2
                    color: taskCard.taskColor
                }

                ColumnLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 6
                    anchors.rightMargin: 2
                    anchors.topMargin: 2
                    anchors.bottomMargin: 2
                    spacing: 1

                    Item {
                        id: taskHeader
                        objectName: "tableTaskHeader_" + taskCard.index
                        Layout.fillWidth: true
                        Layout.preferredHeight: 12
                        Accessible.role: Accessible.Button
                        Accessible.name: qsTr("Open task") + ": "
                            + taskCard.processLabel

                        Label {
                            anchors.fill: parent
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            text: taskCard.processLabel.toUpperCase()
                            elide: Text.ElideRight
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.caption
                            font.weight: Font.DemiBold
                        }
                        HoverHandler {
                            cursorShape: Qt.PointingHandCursor
                        }
                        Controls.ActivationHandler {
                            onActivated: root.openTask(taskCard.modelData)
                        }
                    }

                    TaskTableEditorCell {
                        objectName: "tableTaskStatus_" + taskCard.index
                        Layout.fillWidth: true
                        Layout.preferredHeight: taskCard.editorHeight
                        theme: root.theme
                        releaseCoordinator: editorReleaseCoordinator
                        editorActive: taskCardHover.hovered
                        editingAllowed: !root.columnsController.busy
                        scrolling: root.scrolling
                        actionField: true
                        showAccent: true
                        accentColor: taskCard.taskColor
                        displayText: String(
                            taskCard.modelData.status || qsTr("Select status")
                        )
                        textPointSize: Controls.Typography.caption
                        editorComponent: Component {
                            Controls.ComboBox {
                                objectName: "tableTaskStatusEditor_"
                                    + taskCard.index
                                readonly property var editorRecord:
                                    root.columnsController.task_editor(
                                        root.nodeId,
                                        String(taskCard.modelData.process || ""),
                                        String(taskCard.modelData.status || ""),
                                        String(taskCard.modelData.assigned || "")
                                    )
                                theme: root.theme
                                actionField: true
                                font.pointSize: Controls.Typography.caption
                                model: editorRecord.statusChoices || []
                                textRole: "label"
                                valueRole: "value"
                                colorRole: "color"
                                currentIndex: root.choiceIndex(
                                    model,
                                    String(taskCard.modelData.status || "")
                                )
                                displayText: currentIndex >= 0
                                    ? currentText : qsTr("Select status")
                                onActivated:
                                    root.columnsController.set_task_value(
                                        root.nodeId,
                                        String(
                                            taskCard.modelData.taskSearchKey
                                            || ""
                                        ),
                                        String(taskCard.modelData.process || ""),
                                        "status", currentValue
                                    )
                            }
                        }
                    }

                    TaskTableEditorCell {
                        objectName: "tableTaskAssignee_" + taskCard.index
                        Layout.fillWidth: true
                        Layout.preferredHeight: taskCard.editorHeight
                        theme: root.theme
                        releaseCoordinator: editorReleaseCoordinator
                        editorActive: taskCardHover.hovered
                        editingAllowed: !root.columnsController.busy
                        scrolling: root.scrolling
                        actionField: true
                        displayText: String(
                            taskCard.modelData.assignedLabel
                            || taskCard.modelData.assigned
                            || qsTr("Select user")
                        )
                        showAvatar: true
                        userModel: root.userModel
                        avatarLogin: String(taskCard.modelData.assigned || "")
                        textPointSize: Controls.Typography.caption
                        editorComponent: Component {
                            UserComboBox {
                                objectName: "tableTaskAssigneeEditor_"
                                    + taskCard.index
                                readonly property var editorRecord:
                                    root.columnsController.task_editor(
                                        root.nodeId,
                                        String(taskCard.modelData.process || ""),
                                        String(taskCard.modelData.status || ""),
                                        String(taskCard.modelData.assigned || "")
                                    )
                                theme: root.theme
                                actionField: true
                                font.pointSize: Controls.Typography.caption
                                userModel: root.userModel
                                model: editorRecord.userChoices || []
                                textRole: "label"
                                valueRole: "value"
                                currentIndex: root.choiceIndex(
                                    model,
                                    String(taskCard.modelData.assigned || "")
                                )
                                displayText: currentIndex >= 0
                                    ? currentText : qsTr("Select user")
                                onActivated:
                                    root.columnsController.set_task_value(
                                        root.nodeId,
                                        String(
                                            taskCard.modelData.taskSearchKey
                                            || ""
                                        ),
                                        String(taskCard.modelData.process || ""),
                                        "assigned", currentValue
                                    )
                            }
                        }
                    }
                }
            }
        }
    }

    Controls.ItemCountActionButton {
        id: taskButton
        objectName: "tableCellTasks"
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        visible: root.showMenuButton
        width: 28
        height: 28
        theme: root.theme
        iconName: "task_alt"
        count: root.effectiveCount
        toolTip: count > 0
            ? qsTr("Open Tasks (") + count + ")" : qsTr("Add task")
        onClicked: root.processPickerRequested(taskButton)
    }
}

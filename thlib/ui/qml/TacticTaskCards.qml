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
    property real cardWidth: 107
    property real cardSpacing: 4
    property bool scrolling: false

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

    function editDates(record, sourceItem) {
        dateEditorLoader.active = true
        dateEditorLoader.item.openFor(record, sourceItem)
    }

    onNodeIdChanged: {
        if (dateEditorLoader && dateEditorLoader.item)
            dateEditorLoader.item.close()
    }

    TaskEditorReleaseCoordinator {
        id: editorReleaseCoordinator
        theme: root.theme
    }

    Row {
        anchors.fill: parent
        spacing: root.cardSpacing

        Repeater {
            // Keep card objects when a pooled table row receives another sObject.
            model: root.records ? root.records.length : 0

            delegate: Rectangle {
                id: taskCard

                required property int index
                readonly property var modelData: root.records[index] || ({})
                readonly property string taskIdentity: JSON.stringify([
                    root.nodeId, modelData.taskSearchKey || modelData.taskCode || "",
                    modelData.context || modelData.process || ""
                ])
                readonly property color taskColor:
                    String(modelData.statusColor || "").length > 0
                        ? modelData.statusColor
                        : String(modelData.processColor || "").length > 0
                            ? modelData.processColor : root.theme.action
                readonly property string processLabel: String(
                    modelData.processLabel || modelData.process
                    || modelData.context || qsTr("Task")
                )
                readonly property bool showDates: height >= 76
                readonly property real editorHeight: Math.max(
                    10, Math.min(
                        24, (height - (showDates ? 36 : 21)) / 2
                    )
                )

                objectName: "tableTaskRecord_" + index
                anchors.verticalCenter: parent.verticalCenter
                width: root.cardWidth
                height: Math.min(88, root.height - 2)
                radius: root.theme.itemRadius
                color: root.theme.overlay(
                    root.theme.surfaceContainerHigh, taskColor, 0.1
                )
                border.width: 1
                border.color: root.theme.overlay(
                    root.theme.outlineVariant, taskColor, 0.34
                )

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
                        Layout.preferredHeight: 15
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
                        editorIdentity: taskCard.taskIdentity
                        Layout.fillWidth: true
                        Layout.preferredHeight: taskCard.editorHeight
                        theme: root.theme
                        releaseCoordinator: editorReleaseCoordinator
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
                                instantHover: true
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
                                currentColorFallback: taskCard.taskColor
                                translateDisplayText: false
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
                        editorIdentity: taskCard.taskIdentity
                        Layout.fillWidth: true
                        Layout.preferredHeight: taskCard.editorHeight
                        theme: root.theme
                        releaseCoordinator: editorReleaseCoordinator
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
                                instantHover: true
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

                    Item {
                        id: taskDates
                        objectName: "tableTaskDates_" + taskCard.index
                        Layout.fillWidth: true
                        Layout.preferredHeight: visible ? 14 : 0
                        visible: taskCard.showDates
                        Accessible.role: Accessible.Button
                        Accessible.name: qsTr("Start date") + ": "
                            + String(
                                taskCard.modelData.bidStartFull || "—"
                            ) + "; " + qsTr("Deadline") + ": "
                            + String(taskCard.modelData.bidEndFull || "—")

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 7
                            anchors.rightMargin: 7
                            spacing: 4

                            Controls.MaterialIcon {
                                Layout.preferredWidth: 11
                                Layout.preferredHeight: 11
                                name: "calendar"
                                size: 11
                                color: datesHover.hovered
                                    ? root.theme.action
                                    : root.theme.secondaryText
                                Accessible.ignored: true
                            }
                            Label {
                                Layout.fillWidth: true
                                text: String(
                                    taskCard.modelData.bidStartLabel || "—"
                                ) + " – " + String(
                                    taskCard.modelData.bidEndLabel || "—"
                                )
                                color: datesHover.hovered
                                    ? root.theme.action
                                    : root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                                elide: Text.ElideRight
                                verticalAlignment: Text.AlignVCenter
                            }
                        }

                        HoverHandler {
                            id: datesHover
                            cursorShape: Qt.PointingHandCursor
                        }
                        Controls.ActivationHandler {
                            enabled: !root.columnsController.busy
                                && !root.scrolling
                            cursorShape: Qt.PointingHandCursor
                            onActivated: root.editDates(
                                taskCard.modelData, taskDates
                            )
                        }
                    }
                }
            }
        }
    }

    Loader {
        id: dateEditorLoader
        active: false

        sourceComponent: Controls.Popup {
            id: dateEditor
            objectName: "tableTaskDateEditor"
            parent: Overlay.overlay
            theme: root.theme
            usePopupWindow: false
            modal: false
            focus: true
            width: Math.min(340, maximumAvailableWidth)
            height: dateLayout.implicitHeight + topPadding + bottomPadding
            padding: 10
            settledClosePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
            property var taskRecord: ({})
            property string taskNodeId: ""
            property string startValue: ""
            property string endValue: ""

            onClosed: dateEditorLoader.active = false

            function openFor(record, sourceItem) {
                taskNodeId = root.nodeId
                taskRecord = record || ({})
                startValue = String(taskRecord.bidStart || "")
                endValue = String(taskRecord.bidEnd || "")
                startField.text = startValue
                endField.text = endValue
                openBelowItem(sourceItem, false, 4)
            }

            function stage(field, value) {
                const normalized = String(value || "")
                const current = field === "bid_start_date"
                    ? startValue : endValue
                if (normalized === current)
                    return
                if (root.columnsController.set_task_value(
                        taskNodeId,
                        String(taskRecord.taskSearchKey || ""),
                        String(taskRecord.process || ""),
                        field, normalized)) {
                    if (field === "bid_start_date")
                        startValue = normalized
                    else
                        endValue = normalized
                }
            }

            contentItem: ColumnLayout {
                id: dateLayout
                spacing: 6

                Label {
                    Layout.fillWidth: true
                    text: String(
                        dateEditor.taskRecord.processLabel
                        || dateEditor.taskRecord.process || qsTr("Task")
                    )
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }
                Label {
                    text: qsTr("Start date")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                }
                Controls.DateField {
                    id: startField
                    objectName: "tableTaskStartDateEditor"
                    Layout.fillWidth: true
                    theme: root.theme
                    includeTime: true
                    placeholderText: qsTr("Start date and time")
                    enabled: !root.columnsController.busy
                    errorState: text.length > 0 && parseValue(text) === null
                    onAccepted: value => dateEditor.stage("bid_start_date", value)
                    onEditingFinished:
                        dateEditor.stage("bid_start_date", text)
                }
                Label {
                    text: qsTr("Deadline")
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                }
                Controls.DateField {
                    id: endField
                    objectName: "tableTaskEndDateEditor"
                    Layout.fillWidth: true
                    theme: root.theme
                    includeTime: true
                    placeholderText: qsTr("Deadline and time")
                    enabled: !root.columnsController.busy
                    errorState: text.length > 0 && parseValue(text) === null
                    onAccepted: value => dateEditor.stage("bid_end_date", value)
                    onEditingFinished:
                        dateEditor.stage("bid_end_date", text)
                }
            }
        }
    }
}

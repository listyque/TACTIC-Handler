pragma ComponentBehavior: Bound

import QtQuick
import "tactic_frame/features/table/cells.ui.mjs" as Cells
import "tactic_frame/features/tasks/cells.ui.mjs" as Fields
import "tactic_frame" as Frame
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
    property real cardWidth: Cells.metrics.taskWidth
    property real cardSpacing: Cells.metrics.taskGap
    property bool scrolling: false
    property bool expanded: false
    property int columns: Math.max(1, records ? records.length : 0)
    readonly property var cardLayout: Cells.taskCardLayout(height, expanded, theme.style)
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language

    function choiceIndex(choices, value) {
        const wanted = String(value || "");
        for (let index = 0; index < (choices || []).length; ++index) {
            if (String(choices[index].value || "") === wanted)
                return index;
        }
        return -1;
    }

    function openTask(record) {
        const process = String(record.process || "publish");
        const taskCode = String(record.taskCode || "");
        if (taskCode) {
            controller.open_process_task_details(nodeId, "tasks", process, taskCode);
        } else {
            controller.open_process_details(nodeId, "tasks", process);
        }
    }

    function editDates(record, sourceItem) {
        dateEditorLoader.active = true;
        dateEditorLoader.item.openFor(record, sourceItem);
    }

    onNodeIdChanged: {
        if (dateEditorLoader && dateEditorLoader.item)
            dateEditorLoader.item.close();
    }

    TaskEditorReleaseCoordinator {
        id: editorReleaseCoordinator
        theme: root.theme
    }

    Item {
        anchors.fill: parent

        Repeater {
            // Keep card objects when a pooled table row receives another sObject.
            model: root.records ? root.records.length : 0

            delegate: Rectangle {
                id: taskCard

                required property int index
                readonly property var modelData: root.records[index] || ({})
                readonly property string taskIdentity: root.nodeId + ":" + (modelData.taskSearchKey || modelData.taskCode || "") + ":" + (modelData.context || modelData.process || "")
                readonly property color taskColor: String(modelData.statusColor || "").length > 0 ? modelData.statusColor : String(modelData.processColor || "").length > 0 ? modelData.processColor : root.theme.action
                readonly property string processLabel: String(modelData.processLabel || modelData.process || modelData.context || qsTr("Task"))
                readonly property var cardLayout: root.cardLayout
                readonly property bool showDates: cardLayout.dates
                readonly property real editorHeight: cardLayout.editorHeight

                objectName: "tableTaskRecord_" + index
                x: (index % root.columns) * (root.cardWidth + root.cardSpacing)
                y: root.expanded ? Math.floor(index / root.columns) * (height + root.cardSpacing) : (root.height - height) / 2
                width: root.cardWidth
                height: cardLayout.cardHeight
                radius: root.theme.fieldRadius
                color: root.theme.surfaceContainerHigh
                border.width: 1
                border.color: root.theme.outlineVariant

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
                    anchors.leftMargin: root.expanded ? root.cardLayout.padding : 6
                    anchors.rightMargin: root.cardLayout.padding
                    anchors.topMargin: root.cardLayout.padding
                    anchors.bottomMargin: root.cardLayout.padding
                    spacing: root.cardLayout.gap

                    Item {
                        id: taskHeader
                        objectName: "tableTaskHeader_" + taskCard.index
                        Layout.fillWidth: true
                        Layout.preferredHeight: root.cardLayout.headingHeight
                        Accessible.role: Accessible.Button
                        Accessible.name: qsTr("Open task") + ": " + taskCard.processLabel

                        Controls.MaterialIcon {
                            id: progressIcon
                            visible: taskCard.modelData.processType === "progress"
                            x: Fields.cardMetrics.inset
                            anchors.verticalCenter: parent.verticalCenter
                            width: Fields.cardMetrics.avatar
                            height: Fields.cardMetrics.avatar
                            name: visible ? "MDI_CHART_DONUT" : ""
                            size: Fields.cardMetrics.avatar
                            color: root.theme.primaryText
                            Accessible.ignored: true
                        }
                        Text {
                            anchors.left: parent.left
                            anchors.leftMargin: Fields.cardMetrics.inset + (progressIcon.visible ? Fields.cardMetrics.avatar + Fields.cardMetrics.gap : 0)
                            anchors.right: parent.right
                            anchors.rightMargin: Fields.cardMetrics.inset
                            anchors.top: parent.top
                            anchors.bottom: parent.bottom
                            verticalAlignment: Text.AlignVCenter
                            text: taskCard.processLabel
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
                        visible: taskCard.modelData.processType !== "progress"
                        editorIdentity: taskCard.taskIdentity
                        Layout.fillWidth: true
                        Layout.preferredHeight: taskCard.editorHeight
                        theme: root.theme
                        releaseCoordinator: editorReleaseCoordinator
                        editingAllowed: Cells.taskEditable(taskCard.modelData, "status", !root.columnsController.busy)
                        scrolling: root.scrolling
                        actionField: true
                        cardField: true
                        showAccent: true
                        accentColor: taskCard.taskColor
                        displayText: String(taskCard.modelData.status || qsTr("Select status"))
                        textPointSize: Controls.Typography.caption
                        editorComponent: Component {
                            Controls.ComboBox {
                                objectName: "tableTaskStatusEditor_" + taskCard.index
                                instantHover: true
                                readonly property var editorRecord: root.columnsController.task_editor(root.nodeId, String(taskCard.modelData.process || ""), String(taskCard.modelData.status || ""), String(taskCard.modelData.assigned || ""))
                                theme: root.theme
                                actionField: true
                                font.pointSize: Controls.Typography.caption
                                model: editorRecord.statusChoices || []
                                textRole: "label"
                                valueRole: "value"
                                colorRole: "color"
                                currentColorFallback: taskCard.taskColor
                                translateDisplayText: false
                                currentIndex: root.choiceIndex(model, String(taskCard.modelData.status || ""))
                                displayText: currentIndex >= 0 ? currentText : qsTr("Select status")
                                onActivated: root.columnsController.set_task_value(root.nodeId, String(taskCard.modelData.taskSearchKey || ""), String(taskCard.modelData.process || ""), "status", currentValue)
                            }
                        }
                    }

                    TaskTableEditorCell {
                        objectName: "tableTaskAssignee_" + taskCard.index
                        visible: taskCard.modelData.processType !== "progress"
                        editorIdentity: taskCard.taskIdentity
                        Layout.fillWidth: true
                        Layout.preferredHeight: taskCard.editorHeight
                        theme: root.theme
                        releaseCoordinator: editorReleaseCoordinator
                        editingAllowed: Cells.taskEditable(taskCard.modelData, "assigned", !root.columnsController.busy)
                        scrolling: root.scrolling
                        actionField: true
                        cardField: true
                        displayText: Cells.assigneeLabel(taskCard.modelData, root.language)
                        showAvatar: true
                        userModel: root.userModel
                        avatarLogin: String(taskCard.modelData.assigned || "")
                        textPointSize: Controls.Typography.caption
                        editorComponent: Component {
                            UserComboBox {
                                objectName: "tableTaskAssigneeEditor_" + taskCard.index
                                instantHover: true
                                readonly property var editorRecord: root.columnsController.task_editor(root.nodeId, String(taskCard.modelData.process || ""), String(taskCard.modelData.status || ""), String(taskCard.modelData.assigned || ""))
                                theme: root.theme
                                actionField: true
                                font.pointSize: Controls.Typography.caption
                                userModel: root.userModel
                                model: editorRecord.userChoices || []
                                textRole: "label"
                                valueRole: "value"
                                currentIndex: root.choiceIndex(model, String(taskCard.modelData.assigned || ""))
                                displayText: currentIndex >= 0 ? currentText : qsTr("Select user")
                                onActivated: root.columnsController.set_task_value(root.nodeId, String(taskCard.modelData.taskSearchKey || ""), String(taskCard.modelData.process || ""), "assigned", currentValue)
                            }
                        }
                    }

                    Loader {
                        id: taskDates
                        objectName: "tableTaskDates_" + taskCard.index
                        Layout.fillWidth: true
                        Layout.preferredHeight: visible ? root.cardLayout.datesHeight : 0
                        visible: taskCard.showDates && taskCard.modelData.processType !== "progress"
                        active: visible
                        Accessible.role: Accessible.Button
                        Accessible.name: qsTr("Start date") + ": " + String(taskCard.modelData.bidStartFull || "—") + "; " + qsTr("Deadline") + ": " + String(taskCard.modelData.bidEndFull || "—")

                        sourceComponent: Item {
                            objectName: "tableTaskDatesContent_" + taskCard.index
                            Controls.MaterialIcon {
                                x: Fields.cardMetrics.inset
                                anchors.verticalCenter: parent.verticalCenter
                                width: Fields.cardMetrics.avatar
                                height: Fields.cardMetrics.avatar
                                name: "calendar"
                                size: Fields.cardMetrics.avatar
                                color: root.theme.secondaryText
                                Accessible.ignored: true
                            }
                            Text {
                                anchors.left: parent.left
                                anchors.leftMargin: Fields.cardMetrics.inset + Fields.cardMetrics.avatar + Fields.cardMetrics.gap
                                anchors.right: parent.right
                                anchors.rightMargin: Fields.cardMetrics.inset
                                anchors.top: parent.top
                                anchors.bottom: parent.bottom
                                text: Cells.taskDateRange(taskCard.modelData, root.language)
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.caption
                                elide: Text.ElideRight
                                verticalAlignment: Text.AlignVCenter
                            }

                            HoverHandler {
                                id: datesHover
                                cursorShape: Qt.PointingHandCursor
                            }
                            Controls.ActivationHandler {
                                enabled: Cells.taskEditable(taskCard.modelData, "bid_start_date", !root.columnsController.busy) && !root.scrolling
                                cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                                onActivated: root.editDates(taskCard.modelData, taskDates)
                            }
                        }
                    }
                    Loader {
                        objectName: "tableProcessProgress_" + taskCard.index
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        visible: taskCard.modelData.processType === "progress"
                        active: visible
                        sourceComponent: Frame.FrameView {
                            theme: root.theme
                            scene: Cells.processProgress(taskCard.modelData, width, height, root.language)
                            onEvent: root.openTask(taskCard.modelData)
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
                taskNodeId = root.nodeId;
                taskRecord = record || ({});
                startValue = String(taskRecord.bidStart || "");
                endValue = String(taskRecord.bidEnd || "");
                startField.text = startValue;
                endField.text = endValue;
                openBelowItem(sourceItem, false, 4);
            }

            function stage(field, value) {
                const normalized = String(value || "");
                const current = field === "bid_start_date" ? startValue : endValue;
                if (normalized === current)
                    return;
                if (root.columnsController.set_task_value(taskNodeId, String(taskRecord.taskSearchKey || ""), String(taskRecord.process || ""), field, normalized)) {
                    if (field === "bid_start_date")
                        startValue = normalized;
                    else
                        endValue = normalized;
                }
            }

            contentItem: ColumnLayout {
                id: dateLayout
                spacing: 6

                Label {
                    Layout.fillWidth: true
                    text: String(dateEditor.taskRecord.processLabel || dateEditor.taskRecord.process || qsTr("Task"))
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
                    onEditingFinished: dateEditor.stage("bid_start_date", text)
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
                    onEditingFinished: dateEditor.stage("bid_end_date", text)
                }
            }
        }
    }
}

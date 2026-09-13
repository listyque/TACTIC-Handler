import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    required property var controller
    required property string taskCode
    required property string parentKey
    required property string process
    required property var processChoices
    required property bool isNew
    required property string status
    required property var statusChoices
    required property string assigned
    required property string assignedLabel
    required property string assignedAvatar
    required property var userChoices
    required property string supervisor
    required property string supervisorLabel
    required property var supervisorChoices
    required property string priority
    required property string priorityLabel
    required property var priorityChoices
    required property string milestoneCode
    required property string milestoneLabel
    required property var milestoneChoices
    required property string start
    required property string end
    required property int progress
    required property string description
    required property real plannedHours
    required property string processColor
    required property int notes
    property bool showStatus: false
    property bool showAssignee: false
    property bool showDates: false
    property bool showProgress: false
    property bool showHours: false
    property bool showNotes: false
    property bool showPriority: false
    property bool showMilestone: false
    property bool showSupervisor: false
    property bool showDescription: true
    property bool descriptionEditing: isNew
    property real contentLeftMargin: 12
    property real contentRightMargin: 12
    property bool showTopSeparator: true
    readonly property int detailColumnCount: width >= 1280 ? 5
        : width >= 960 ? 4
        : width >= 720 ? 3
        : width >= 440 ? 2 : 1
    readonly property real detailCellWidth: Math.max(
        0,
        (width - contentLeftMargin - contentRightMargin
            - Math.max(0, detailColumnCount - 1) * 8)
            / detailColumnCount
    )

    implicitHeight: descriptionSection.visible
        ? descriptionSection.y + descriptionSection.implicitHeight + 10
        : detailFlow.y + detailFlow.implicitHeight + 8

    function choiceIndex(values, selected) {
        const source = values || []
        for (let index = 0; index < source.length; ++index) {
            if (String(source[index].value || "") === String(selected || ""))
                return index
        }
        return -1
    }

    component DetailLabel: Label {
        color: root.theme.secondaryText
        font.family: root.theme.fontFamily
        font.pointSize: Controls.Typography.micro
        font.weight: Font.DemiBold
        font.letterSpacing: 0.35
    }

    component DetailColumn: Column {
        Layout.fillWidth: true
        Layout.minimumWidth: root.detailCellWidth
        Layout.preferredWidth: root.detailCellWidth
        Layout.maximumWidth: root.detailCellWidth
    }

    Rectangle {
        objectName: "taskDetailsBackground"
        anchors.fill: parent
        color: root.theme.panelDeep
        Rectangle {
            visible: root.showTopSeparator
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: 1
            color: root.theme.separator
        }
    }

    GridLayout {
        id: detailFlow
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.leftMargin: root.contentLeftMargin
        anchors.rightMargin: root.contentRightMargin
        anchors.topMargin: 8
        height: implicitHeight
        columns: root.detailColumnCount
        columnSpacing: 8
        rowSpacing: 8

        DetailColumn {
            visible: root.isNew
            Layout.fillWidth: true
            spacing: 3
            DetailLabel { text: qsTr("PROCESS") }
            Controls.ComboBox {
                width: parent.width
                height: root.theme.controlHeight
                theme: root.theme
                actionField: true
                enabled: !root.controller.advancedSaving
                    && !root.controller.advancedBusy
                model: root.processChoices
                textRole: "label"
                valueRole: "value"
                colorRole: "color"
                currentIndex: root.choiceIndex(
                    root.processChoices, root.process
                )
                displayText: currentIndex >= 0
                    ? currentText : qsTr("Select process")
                onActivated: root.controller.stage_advanced_process(
                    root.taskCode, currentValue
                )
            }
        }

        DetailColumn {
            visible: root.showStatus
            Layout.fillWidth: true
            spacing: 3
            DetailLabel { text: qsTr("STATUS") }
            Controls.ComboBox {
                width: parent.width
                height: root.theme.controlHeight
                theme: root.theme
                actionField: true
                enabled: !root.controller.advancedSaving
                    && !root.controller.advancedBusy
                model: root.statusChoices
                textRole: "label"
                valueRole: "value"
                colorRole: "color"
                currentIndex: root.choiceIndex(root.statusChoices, root.status)
                displayText: currentIndex >= 0
                    ? currentText : qsTr("No status")
                onActivated: root.controller.stage_advanced_value(
                    root.taskCode, "status", currentValue
                )
            }
        }

        DetailColumn {
            visible: root.showAssignee
            Layout.fillWidth: true
            spacing: 3
            DetailLabel { text: qsTr("ASSIGNEE") }
            UserComboBox {
                width: parent.width
                height: root.theme.controlHeight
                theme: root.theme
                actionField: true
                enabled: !root.controller.advancedSaving
                    && !root.controller.advancedBusy
                userModel: userListModel
                model: root.userChoices
                textRole: "label"
                valueRole: "value"
                currentIndex: root.choiceIndex(root.userChoices, root.assigned)
                currentAvatarUrl: root.assignedAvatar
                displayText: currentIndex >= 0
                    ? currentText : root.assignedLabel || "Not assigned"
                onActivated: root.controller.stage_advanced_value(
                    root.taskCode, "assigned", currentValue
                )
            }
        }

        DetailColumn {
            visible: root.showDates
            Layout.fillWidth: true
            spacing: 3
            DetailLabel { text: qsTr("START") }
            Controls.DateField {
                width: parent.width
                theme: root.theme
                includeTime: true
                text: root.start
                placeholderText: qsTr("Start date and time")
                onAccepted: value => root.controller.stage_advanced_value(
                    root.taskCode, "start", value
                )
            }
        }

        DetailColumn {
            visible: root.showDates
            Layout.fillWidth: true
            spacing: 3
            DetailLabel { text: qsTr("DEADLINE") }
            Controls.DateField {
                width: parent.width
                theme: root.theme
                includeTime: true
                text: root.end
                placeholderText: qsTr("Deadline and time")
                onAccepted: value => root.controller.stage_advanced_value(
                    root.taskCode, "end", value
                )
            }
        }

        DetailColumn {
            visible: root.showProgress
            Layout.fillWidth: true
            spacing: 3
            Row {
                width: parent.width
                DetailLabel { text: qsTr("PROGRESS") }
                Label {
                    width: parent.width - x
                    text: Math.round(progressSlider.value) + "%"
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.caption
                    font.weight: Font.DemiBold
                    horizontalAlignment: Text.AlignRight
                }
            }
            Controls.Slider {
                id: progressSlider
                width: parent.width
                height: 26
                theme: root.theme
                from: 0
                to: 100
                stepSize: 5
                snapMode: Slider.SnapAlways
                value: root.progress
                enabled: root.controller.progressSupported
                    && !root.controller.advancedSaving
                    && !root.controller.advancedBusy
                onPressedChanged: {
                    if (!pressed && enabled
                            && Math.round(value) !== root.progress) {
                        root.controller.stage_advanced_value(
                            root.taskCode, "progress", String(Math.round(value))
                        )
                    }
                }
            }
        }

        DetailColumn {
            visible: root.showHours
            Layout.fillWidth: true
            spacing: 3
            DetailLabel { text: qsTr("EXPECTED WORK HOURS") }
            Controls.SpinBox {
                objectName: "taskExpectedHoursEditor"
                width: parent.width
                height: root.theme.controlHeight
                theme: root.theme
                decimals: 2
                from: 0
                to: 100000 * valueScale
                stepSize: 50
                value: scaledValue(Math.max(0, root.plannedHours))
                enabled: !root.controller.advancedSaving
                    && !root.controller.advancedBusy
                onRealValueEdited: value => {
                    if (Math.abs(value - root.plannedHours) > 0.001) {
                        root.controller.stage_advanced_value(
                            root.taskCode, "plannedHours", value
                        )
                    }
                }
            }
        }

        DetailColumn {
            visible: root.showNotes
            Layout.fillWidth: true
            spacing: 3
            DetailLabel { text: qsTr("NOTES") }
            Controls.Button {
                width: parent.width
                height: root.theme.controlHeight
                theme: root.theme
                text: root.notes > 0
                    ? root.notes + qsTr(" notes") : qsTr("Open notes")
                icon.name: "comment"
                onClicked: root.controller.open_notes(
                    root.parentKey, root.process, root.taskCode
                )
            }
        }

        DetailColumn {
            visible: root.showPriority
            Layout.fillWidth: true
            spacing: 3
            DetailLabel { text: qsTr("PRIORITY") }
            Controls.ComboBox {
                objectName: "taskPriorityEditor"
                width: parent.width
                height: root.theme.controlHeight
                theme: root.theme
                actionField: false
                showIndicator: true
                model: root.priorityChoices
                textRole: "label"
                valueRole: "value"
                currentIndex: root.choiceIndex(root.priorityChoices, root.priority)
                displayText: currentIndex >= 0
                        && String(currentText).length > 0
                    ? currentText : root.priorityLabel || qsTr("No priority")
                onActivated: root.controller.stage_advanced_value(
                    root.taskCode, "priority", currentValue
                )
            }
        }

        DetailColumn {
            visible: root.showMilestone
            Layout.fillWidth: true
            spacing: 3
            DetailLabel { text: qsTr("MILESTONE") }
            Row {
                width: parent.width
                spacing: 5
                Controls.ComboBox {
                    objectName: "taskMilestoneEditor"
                    width: parent.width - manageMilestonesButton.width
                        - parent.spacing
                    height: root.theme.controlHeight
                    theme: root.theme
                    actionField: false
                    showIndicator: true
                    model: root.milestoneChoices
                    textRole: "label"
                    valueRole: "value"
                    currentIndex: root.choiceIndex(
                        root.milestoneChoices, root.milestoneCode
                    )
                    displayText: currentIndex >= 0
                        ? currentText : root.milestoneLabel
                    onActivated: root.controller.stage_advanced_value(
                        root.taskCode, "milestoneCode", currentValue
                    )
                }
                Controls.CompactIconButton {
                    id: manageMilestonesButton
                    width: root.theme.controlHeight
                    height: root.theme.controlHeight
                    theme: root.theme
                    iconName: "add"
                    toolTip: qsTr("Manage milestones")
                    onClicked: milestoneController.open_manager()
                }
            }
        }

        DetailColumn {
            visible: root.showSupervisor
            Layout.fillWidth: true
            spacing: 3
            DetailLabel { text: qsTr("SUPERVISOR") }
            UserComboBox {
                objectName: "taskSupervisorEditor"
                width: parent.width
                height: root.theme.controlHeight
                theme: root.theme
                actionField: true
                userModel: userListModel
                model: root.supervisorChoices
                textRole: "label"
                valueRole: "value"
                currentIndex: root.choiceIndex(
                    root.supervisorChoices, root.supervisor
                )
                displayText: currentIndex >= 0
                    ? currentText : root.supervisorLabel
                onActivated: root.controller.stage_advanced_value(
                    root.taskCode, "supervisor", currentValue
                )
            }
        }
    }

    Rectangle {
        id: descriptionSeparator
        visible: root.showDescription
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: detailFlow.bottom
        anchors.leftMargin: root.contentLeftMargin
        anchors.rightMargin: 18
        anchors.topMargin: 10
        height: 1
        color: root.theme.separator
        opacity: 0.75
    }

    Column {
        id: descriptionSection
        visible: root.showDescription
        x: root.contentLeftMargin
        y: descriptionSeparator.y + descriptionSeparator.height + 8
        width: Math.max(0, parent.width - x - 18)
        spacing: 4

        DetailLabel { text: qsTr("DESCRIPTION") }

        Item {
            width: parent.width
            height: 58

            Controls.TextArea {
                id: descriptionEditor
                objectName: "taskDescriptionEditor"
                anchors.fill: parent
                theme: root.theme
                readOnly: !root.isNew && !root.descriptionEditing
                placeholderText: qsTr("Add task description…")
                rightPadding: root.isNew ? 12 : 42
                font.pointSize: Controls.Typography.label

                function syncDescription() {
                    if (!activeFocus && text !== root.description)
                        text = root.description
                }

                Component.onCompleted: syncDescription()
                onActiveFocusChanged: {
                    if (activeFocus)
                        return
                    if (root.descriptionEditing) {
                        if (!root.isNew)
                            root.descriptionEditing = false
                        if (text !== root.description) {
                            root.controller.stage_advanced_value(
                                root.taskCode, "description", text
                            )
                        }
                    }
                }
                Keys.onEscapePressed: event => {
                    text = root.description
                    root.descriptionEditing = root.isNew
                    focus = false
                    event.accepted = true
                }
            }

            Connections {
                target: root
                function onDescriptionChanged() {
                    descriptionEditor.syncDescription()
                }
            }

            Controls.CompactIconButton {
                objectName: "taskDescriptionEditButton"
                visible: !root.isNew
                anchors.right: parent.right
                anchors.rightMargin: 5
                anchors.verticalCenter: parent.verticalCenter
                theme: root.theme
                iconName: root.descriptionEditing ? "check" : "edit"
                toolTip: root.descriptionEditing
                    ? qsTr("Finish editing description")
                    : qsTr("Edit task description")
                onClicked: {
                    if (root.descriptionEditing) {
                        descriptionEditor.focus = false
                        return
                    }
                    root.descriptionEditing = true
                    Qt.callLater(function() {
                        descriptionEditor.forceActiveFocus()
                        descriptionEditor.cursorPosition =
                            descriptionEditor.length
                    })
                }
            }
        }
    }
}

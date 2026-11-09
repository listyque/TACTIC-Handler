import QtQuick
import QtQuick.Controls
import "controls" as Controls
import "tactic_frame" as Frame
import "tactic_frame/features/tasks/details.ui.mjs" as UI

Frame.FrameView {
    id: root

    required property var controller
    required property string taskCode
    required property string parentKey
    required property string process
    property string context: ""
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
    property var descriptionControl: null
    property var progressControl: null
    readonly property int detailColumnCount: scene.columns
    readonly property real detailCellWidth: scene.cellWidth
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    implicitHeight: scene.height
    enabled: !root.controller.advancedSaving && !root.controller.advancedBusy
    scene: UI.describe({
        fields: [
            {
                name: "process",
                visible: root.isNew
            },
            {
                name: "context",
                visible: root.isNew
            },
            {
                name: "status",
                visible: root.showStatus
            },
            {
                name: "assigned",
                visible: root.showAssignee
            },
            {
                name: "bid_start_date",
                visible: root.showDates
            },
            {
                name: "bid_end_date",
                visible: root.showDates
            },
            {
                name: "progress",
                visible: root.showProgress
            },
            {
                name: "bid_duration",
                visible: root.showHours
            },
            {
                name: "notes",
                visible: root.showNotes
            },
            {
                name: "priority",
                visible: root.showPriority
            },
            {
                name: "milestone_code",
                visible: root.showMilestone
            },
            {
                name: "supervisor",
                visible: root.showSupervisor
            }
        ].filter(field => field.visible),
        progress: root.progressControl ? root.progressControl.value : root.progress,
        description: root.showDescription,
        creating: root.isNew,
        editingDescription: root.descriptionEditing,
        busy: !root.enabled,
        left: root.contentLeftMargin,
        right: root.contentRightMargin,
        topSeparator: root.showTopSeparator
    }, width, root.language)
    views: ({
            process: {
                component: field_process
            },
            context: {
                component: field_context
            },
            status: {
                component: field_status
            },
            assigned: {
                component: field_assigned
            },
            bid_start_date: {
                component: field_bid_start_date
            },
            bid_end_date: {
                component: field_bid_end_date
            },
            progress: {
                component: field_progress
            },
            bid_duration: {
                component: field_bid_duration
            },
            notes: {
                component: field_notes
            },
            priority: {
                component: field_priority
            },
            milestone_code: {
                component: field_milestone_code
            },
            supervisor: {
                component: field_supervisor
            },
            description: {
                component: field_description
            }
        })
    function choiceIndex(values, selected) {
        return (values || []).findIndex(option => String(option.value || "") === String(selected || ""));
    }
    onTaskCodeChanged: {
        if (root.descriptionControl) {
            root.descriptionControl.focus = false;
            root.descriptionControl.syncDescription();
        }
        root.descriptionEditing = root.isNew;
    }
    onEvent: action => {
        if (action.type !== "description" || !root.descriptionControl)
            return;
        if (root.descriptionEditing) {
            root.descriptionControl.focus = false;
            return;
        }
        root.descriptionEditing = true;
        Qt.callLater(function () {
            if (root.descriptionControl) {
                root.descriptionControl.forceActiveFocus();
                root.descriptionControl.cursorPosition = root.descriptionControl.length;
            }
        });
    }
    Connections {
        target: root
        function onDescriptionChanged() {
            if (root.descriptionControl)
                root.descriptionControl.syncDescription();
        }
    }

    Component {
        id: field_process
        Controls.ComboBox {
            width: parent.width
            height: root.theme.controlHeight
            theme: root.theme
            actionField: true
            enabled: !root.controller.advancedSaving && !root.controller.advancedBusy
            model: root.processChoices
            textRole: "label"
            valueRole: "value"
            colorRole: "color"
            currentIndex: root.choiceIndex(root.processChoices, root.process)
            displayText: currentIndex >= 0 ? currentText : qsTr("Select process")
            onActivated: root.controller.stage_advanced_process(root.taskCode, currentValue)
        }
    }

    Component {
        id: field_context
        Controls.TextField {
            objectName: "taskContextEditor"
            theme: root.theme
            text: root.context || root.process
            Accessible.name: qsTr("Context")
            onTextEdited: root.controller.stage_advanced_value(root.taskCode, "context", text)
        }
    }

    Component {
        id: field_status
        Controls.ComboBox {
            width: parent.width
            height: root.theme.controlHeight
            theme: root.theme
            actionField: true
            enabled: !root.controller.advancedSaving && !root.controller.advancedBusy
            model: root.statusChoices
            textRole: "label"
            valueRole: "value"
            colorRole: "color"
            translateDisplayText: false
            currentIndex: root.choiceIndex(root.statusChoices, root.status)
            displayText: currentIndex >= 0 ? currentText : qsTr("No status")
            onActivated: root.controller.stage_advanced_value(root.taskCode, "status", currentValue)
        }
    }

    Component {
        id: field_assigned
        UserComboBox {
            width: parent.width
            height: root.theme.controlHeight
            theme: root.theme
            actionField: true
            enabled: !root.controller.advancedSaving && !root.controller.advancedBusy
            userModel: userListModel
            model: root.userChoices
            textRole: "label"
            valueRole: "value"
            currentIndex: root.choiceIndex(root.userChoices, root.assigned)
            currentAvatarUrl: root.assignedAvatar
            displayText: currentIndex >= 0 ? currentText : root.assignedLabel || "Not assigned"
            onActivated: root.controller.stage_advanced_value(root.taskCode, "assigned", currentValue)
        }
    }

    Component {
        id: field_bid_start_date
        Controls.DateField {
            width: parent.width
            theme: root.theme
            includeTime: true
            text: root.start
            placeholderText: qsTr("Start date and time")
            onAccepted: value => root.controller.stage_advanced_value(root.taskCode, "start", value)
        }
    }

    Component {
        id: field_bid_end_date
        Controls.DateField {
            width: parent.width
            theme: root.theme
            includeTime: true
            text: root.end
            placeholderText: qsTr("Deadline and time")
            onAccepted: value => root.controller.stage_advanced_value(root.taskCode, "end", value)
        }
    }

    Component {
        id: field_progress
        Controls.Slider {
            id: progressSlider
            Component.onCompleted: root.progressControl = progressSlider
            Component.onDestruction: if (root && root.progressControl === progressSlider)
                root.progressControl = null
            width: parent.width
            height: 26
            theme: root.theme
            from: 0
            to: 100
            stepSize: 5
            snapMode: Slider.SnapAlways
            value: root.progress
            enabled: root.controller.progressSupported && !root.controller.advancedSaving && !root.controller.advancedBusy
            onPressedChanged: {
                if (!pressed && enabled && Math.round(value) !== root.progress) {
                    root.controller.stage_advanced_value(root.taskCode, "progress", String(Math.round(value)));
                }
            }
        }
    }

    Component {
        id: field_bid_duration
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
            enabled: !root.controller.advancedSaving && !root.controller.advancedBusy
            onRealValueEdited: value => {
                if (Math.abs(value - root.plannedHours) > 0.001) {
                    root.controller.stage_advanced_value(root.taskCode, "plannedHours", value);
                }
            }
        }
    }

    Component {
        id: field_notes
        Controls.Button {
            width: parent.width
            height: root.theme.controlHeight
            theme: root.theme
            text: root.notes > 0 ? root.notes + qsTr(" notes") : qsTr("Open notes")
            icon.name: "comment"
            onClicked: root.controller.open_notes(root.parentKey, root.process, root.taskCode)
        }
    }

    Component {
        id: field_priority
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
            displayText: currentIndex >= 0 && String(currentText).length > 0 ? currentText : root.priorityLabel || qsTr("No priority")
            onActivated: root.controller.stage_advanced_value(root.taskCode, "priority", currentValue)
        }
    }

    Component {
        id: field_milestone_code
        Row {
            width: parent.width
            spacing: 5
            Controls.ComboBox {
                objectName: "taskMilestoneEditor"
                width: parent.width - manageMilestonesButton.width - parent.spacing
                height: root.theme.controlHeight
                theme: root.theme
                actionField: false
                showIndicator: true
                model: root.milestoneChoices
                textRole: "label"
                valueRole: "value"
                currentIndex: root.choiceIndex(root.milestoneChoices, root.milestoneCode)
                displayText: currentIndex >= 0 ? currentText : root.milestoneLabel
                onActivated: root.controller.stage_advanced_value(root.taskCode, "milestoneCode", currentValue)
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

    Component {
        id: field_supervisor
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
            currentIndex: root.choiceIndex(root.supervisorChoices, root.supervisor)
            displayText: currentIndex >= 0 ? currentText : root.supervisorLabel
            onActivated: root.controller.stage_advanced_value(root.taskCode, "supervisor", currentValue)
        }
    }

    Component {
        id: field_description
        Controls.TextArea {
            id: descriptionEditor
            property string editingTaskCode: ""
            property string editingBaseline: ""
            objectName: "taskDescriptionEditor"
            anchors.fill: parent
            theme: root.theme
            readOnly: !root.isNew && !root.descriptionEditing
            placeholderText: qsTr("Add task description…")
            rightPadding: root.isNew ? 12 : 42
            font.pointSize: Controls.Typography.label

            function syncDescription() {
                if (!activeFocus && text !== root.description)
                    text = root.description;
            }

            Component.onCompleted: {
                root.descriptionControl = descriptionEditor;
                syncDescription();
            }
            Component.onDestruction: if (root && root.descriptionControl === descriptionEditor)
                root.descriptionControl = null
            onTextChanged: {
                if (activeFocus && root.descriptionEditing && editingTaskCode)
                    root.controller.stage_advanced_description_input(editingTaskCode, text);
            }
            onActiveFocusChanged: {
                if (activeFocus) {
                    editingTaskCode = root.taskCode;
                    editingBaseline = text;
                } else if (editingTaskCode) {
                    root.controller.stage_advanced_value(editingTaskCode, "description", text);
                    editingTaskCode = "";
                    root.descriptionEditing = root.isNew;
                    syncDescription();
                }
            }
            Keys.onEscapePressed: event => {
                text = editingBaseline;
                root.descriptionEditing = root.isNew;
                focus = false;
                event.accepted = true;
            }
        }
    }
}

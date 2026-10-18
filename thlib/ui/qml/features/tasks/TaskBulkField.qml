import QtQuick
import QtQuick.Controls
import "../.."
import "../../controls" as Controls

Loader {
    id: root
    required property var theme
    required property var controller
    property var frameNode: ({
            field: {}
        })
    readonly property string field: frameNode.field.name || ""
    readonly property string key: ({
            bid_start_date: "start",
            bid_end_date: "end",
            milestone_code: "milestoneCode"
        })[field] || field
    readonly property var editor: controller.bulkEditor
    readonly property bool mixed: !!editor[key + "Mixed"] && !editor[key + "Set"]
    readonly property string value: mixed ? "" : String(editor[key] ?? "")
    readonly property var options: field === "status" ? controller.bulkStatusOptions : field === "assigned" ? controller.bulkUserOptions : field === "priority" ? controller.bulkPriorityOptions : field === "milestone_code" ? controller.bulkMilestoneOptions : controller.bulkSupervisorOptions
    enabled: !!frameNode.enabled
    sourceComponent: field.endsWith("_date") ? datePort : field === "description" ? descriptionPort : field === "progress" ? progressPort : field === "assigned" ? userPort : choicePort
    Component {
        id: datePort
        Controls.DateField {
            theme: root.theme
            includeTime: true
            text: root.value
            placeholderText: root.mixed ? qsTr("Mixed") : ""
            onAccepted: value => root.controller.set_bulk_value(root.key, value)
            onEditingFinished: root.controller.set_bulk_value(root.key, text)
        }
    }
    Component {
        id: descriptionPort
        Controls.TextArea {
            theme: root.theme
            text: root.value
            placeholderText: root.mixed ? qsTr("Mixed descriptions") : ""
            wrapMode: TextEdit.Wrap
            onTextChanged: if (activeFocus)
                root.controller.set_bulk_value(root.key, text)
        }
    }
    Component {
        id: progressPort
        Controls.TextField {
            theme: root.theme
            text: root.value
            placeholderText: root.mixed ? qsTr("Mixed") : "0-100"
            validator: IntValidator {
                bottom: 0
                top: 100
            }
            onEditingFinished: root.controller.set_bulk_value(root.key, text)
        }
    }
    Component {
        id: choicePort
        Controls.ComboBox {
            theme: root.theme
            model: root.options
            textRole: "label"
            valueRole: "value"
            colorRole: "color"
            translateDisplayText: false
            currentIndex: root.mixed ? -1 : (model || []).findIndex(row => String(row.value) === root.value)
            displayText: root.mixed ? qsTr("Mixed") : currentIndex < 0 ? qsTr("Select status") : currentText
            onActivated: root.controller.set_bulk_value(root.key, currentValue)
        }
    }
    Component {
        id: userPort
        UserComboBox {
            theme: root.theme
            model: root.options
            userModel: userListModel
            textRole: "label"
            valueRole: "value"
            currentIndex: root.mixed ? -1 : (model || []).findIndex(row => String(row.value) === root.value)
            displayText: root.mixed ? qsTr("Mixed assignee") : currentIndex < 0 ? qsTr("Select assignee") : currentText
            onActivated: root.controller.set_bulk_value(root.key, currentValue)
        }
    }
}

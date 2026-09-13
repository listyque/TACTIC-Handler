import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

ColumnLayout {
    id: root
    required property var theme
    required property var controller
    readonly property var rule: controller.selectedRule
    readonly property string action: rule.action || ""
    readonly property var textFields: [
        {key: "targetStatus", title: qsTr("Destination status"), actions: ["parent_status"]},
        {key: "classPath", title: qsTr("Installed Python class"), actions: ["python_class"]},
        {key: "subject", title: qsTr("Subject"), actions: ["notification"]},
        {key: "mailTo", title: qsTr("Recipients"), actions: ["notification"]},
        {key: "mailCc", title: qsTr("Copy recipients"), actions: ["notification"]}
    ]
    spacing: 14

    ConfigurationSection {
        Layout.fillWidth: true
        visible: root.action === "task_status"
        theme: root.theme
        title: qsTr("Destination tasks")
        description: qsTr("Each process uses its own task status workflow.")
        Repeater {
            model: root.action === "task_status" ? root.controller.metadata.processes || [] : []
            delegate: RowLayout {
                id: destination
                required property var modelData
                readonly property var target: (root.rule.targets || []).find(row => row.process === modelData.identity)
                Layout.fillWidth: true
                Controls.CheckBox {
                    objectName: "adminRuleTarget_" + destination.modelData.identity
                    Layout.fillWidth: true
                    theme: root.theme
                    text: destination.modelData.label
                    checked: !!destination.target
                    onToggled: root.controller.set_target(destination.modelData.identity, statusChoice.currentText, checked)
                }
                Controls.ComboBox {
                    id: statusChoice
                    objectName: "adminRuleTargetStatus_" + destination.modelData.identity
                    Layout.preferredWidth: Math.min(200, root.width * 0.5)
                    theme: root.theme
                    enabled: !!destination.target
                    model: destination.modelData.statuses
                    translateDisplayText: false
                    currentIndex: destination.target ? model.indexOf(destination.target.status) : 0
                    onActivated: root.controller.set_target(destination.modelData.identity, currentText, true)
                }
            }
        }
    }
    ConfigurationSection {
        Layout.fillWidth: true
        visible: root.action === "task_create"
        theme: root.theme
        title: qsTr("Output processes")
        description: qsTr("Only connected output processes are available. Add connections on the canvas first.")
        Repeater {
            model: root.action === "task_create" ? root.controller.metadata.outputs || [] : []
            delegate: Controls.CheckBox {
                required property string modelData
                objectName: "adminRuleOutput_" + modelData
                Layout.fillWidth: true
                theme: root.theme
                text: modelData
                checked: (root.rule.outputs || []).includes(modelData)
                onToggled: root.controller.set_output(modelData, checked)
            }
        }
    }
    ConfigurationSection {
        Layout.fillWidth: true
        visible: root.action === "task_date"
        theme: root.theme
        title: qsTr("Actual date")
        Controls.SegmentedButton {
            objectName: "adminRuleDate"
            Layout.fillWidth: true
            theme: root.theme
            currentValue: root.rule.column || ""
            model: [
                {value: "actual_start_date", label: "Start", icon: "calendar"},
                {value: "actual_end_date", label: "End", icon: "calendar"}
            ]
            onActivated: value => root.controller.set_rule_field("column", value)
        }
    }
    ConfigurationSection {
        Layout.fillWidth: true
        visible: root.action === "custom_script"
        theme: root.theme
        title: qsTr("Server script")
        description: qsTr("Select an existing server script. Its source remains in the Script Editor.")
        Controls.ComboBox {
            objectName: "adminRuleScript"
            Layout.fillWidth: true
            theme: root.theme
            model: root.controller.metadata.scriptPaths || []
            translateDisplayText: false
            currentIndex: model.indexOf(root.rule.scriptPath || "")
            displayText: root.rule.scriptPath || qsTr("Not set")
            onActivated: root.controller.set_rule_field("scriptPath", currentText)
        }
    }
    Repeater {
        model: root.textFields.filter(field => field.actions.includes(root.action))
        delegate: ConfigurationSection {
            required property var modelData
            Layout.fillWidth: true
            theme: root.theme
            title: modelData.title
            Controls.TextField {
                objectName: "adminRule_" + modelData.key
                Layout.fillWidth: true
                theme: root.theme
                text: root.rule[modelData.key] || ""
                onTextEdited: root.controller.set_rule_field(modelData.key, text)
            }
        }
    }
    ConfigurationSection {
        Layout.fillWidth: true
        visible: root.action === "notification"
        theme: root.theme
        title: qsTr("Notification content")
        description: qsTr("TACTIC expressions are supported in recipients, subject and body. Saving does not send a notification.")
        Controls.CheckBox {
            objectName: "adminRuleTemplate"
            Layout.fillWidth: true
            theme: root.theme
            text: qsTr("Use the native event template on save")
            checked: root.rule.useTemplate === true
            onToggled: root.controller.set_rule_field("useTemplate", checked)
        }
        Controls.TextArea {
            objectName: "adminRule_body"
            Layout.fillWidth: true
            Layout.minimumHeight: 160
            theme: root.theme
            enabled: !root.rule.useTemplate
            wrapMode: TextEdit.Wrap
            text: root.rule.body || ""
            onTextChanged: if (activeFocus) root.controller.set_rule_field("body", text)
        }
        Controls.CheckBox {
            objectName: "adminRuleTicket"
            Layout.fillWidth: true
            theme: root.theme
            text: qsTr("Generate a temporary login ticket")
            checked: root.rule.loginTicket === true
            onToggled: root.controller.set_rule_field("loginTicket", checked)
        }
        Label {
            Layout.fillWidth: true
            text: qsTr("Additional conditions (native rules XML)")
            color: root.theme.secondaryText
            wrapMode: Text.Wrap
        }
        Controls.TextArea {
            objectName: "adminRule_rules"
            Layout.fillWidth: true
            Layout.minimumHeight: 100
            theme: root.theme
            wrapMode: TextEdit.Wrap
            text: root.rule.rules || ""
            onTextChanged: if (activeFocus) root.controller.set_rule_field("rules", text)
        }
    }
}

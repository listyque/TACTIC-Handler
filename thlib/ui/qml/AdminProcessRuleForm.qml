import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

ColumnLayout {
    id: root
    required property var theme
    required property var controller
    readonly property var rule: controller.selectedRule
    readonly property bool notification: rule.kind === "notification"
    readonly property var events: [
        {identity: "change|sthpw/task|status", label: qsTr("Task status changed")},
        {identity: "change|sthpw/task|assigned", label: qsTr("Task assignee changed")},
        {identity: "insert|sthpw/note", label: qsTr("Note created")},
        {identity: "change|sthpw/note", label: qsTr("Note created or modified")},
        {identity: "checkin|" + (controller.metadata.searchType || ""), label: qsTr("File checked in")}
    ]
    readonly property var actions: [
        {identity: "task_status", label: qsTr("Change task statuses")},
        {identity: "parent_status", label: qsTr("Change parent status")},
        {identity: "task_create", label: qsTr("Create output tasks")},
        {identity: "task_date", label: qsTr("Set actual task date")},
        {identity: "custom_script", label: qsTr("Server script")},
        {identity: "python_class", label: qsTr("Server command class")}
    ]
    spacing: 14
    enabled: controller.canWrite && !controller.busy && !rule.managed

    ConfigurationSection {
        Layout.fillWidth: true
        theme: root.theme
        title: qsTr("Name")
        Controls.TextField {
            objectName: "adminRule_title"
            Layout.fillWidth: true
            theme: root.theme
            text: root.rule.title || ""
            onTextEdited: root.controller.set_rule_field("title", text)
        }
    }
    ConfigurationSection {
        Layout.fillWidth: true
        theme: root.theme
        title: qsTr("Description")
        Controls.TextArea {
            objectName: "adminRule_description"
            Layout.fillWidth: true
            Layout.minimumHeight: 90
            theme: root.theme
            text: root.rule.description || ""
            wrapMode: TextEdit.Wrap
            onTextChanged: if (activeFocus) root.controller.set_rule_field("description", text)
        }
    }
    ConfigurationSection {
        Layout.fillWidth: true
        theme: root.theme
        title: qsTr("Scope")
        description: root.rule.scope === "global"
            ? qsTr("Applies to every process named %1 in this project, including other pipelines.").arg(root.controller.metadata.process || "")
            : qsTr("Applies only to this process in this pipeline.")
        Controls.SegmentedButton {
            objectName: "adminRuleScope"
            Layout.fillWidth: true
            theme: root.theme
            currentValue: root.rule.scope || "local"
            model: [
                {value: "local", label: "This pipeline", icon: "process"},
                {value: "global", label: "All matching processes", icon: "schema"}
            ]
            onActivated: value => root.controller.set_rule_field("scope", value)
        }
    }
    ConfigurationSection {
        Layout.fillWidth: true
        theme: root.theme
        title: qsTr("Event")
        Controls.ComboBox {
            objectName: "adminRuleEvent"
            Layout.fillWidth: true
            theme: root.theme
            model: root.events.concat([{identity: "", label: qsTr("Custom event")}])
            textRole: "label"
            valueRole: "identity"
            translateDisplayText: false
            currentIndex: Math.max(0, model.findIndex(row => row.identity === root.rule.event))
            displayText: root.events.some(row => row.identity === root.rule.event) ? currentText : qsTr("Custom event")
            onActivated: root.controller.set_rule_field("event", currentValue)
        }
        Controls.TextField {
            objectName: "adminRuleCustomEvent"
            Layout.fillWidth: true
            visible: !root.events.some(row => row.identity === root.rule.event)
            theme: root.theme
            placeholderText: qsTr("Native event identifier")
            text: root.rule.event || ""
            onTextEdited: root.controller.set_rule_field("event", text)
        }
        Controls.ComboBox {
            objectName: "adminRuleSourceStatus"
            Layout.fillWidth: true
            visible: root.rule.event === "change|sthpw/task|status" && root.rule.action !== "parent_status"
            theme: root.theme
            model: [{identity: "", label: qsTr("Any status")}].concat(
                (root.controller.metadata.sourceStatuses || []).map(value => ({identity: value, label: value})))
            textRole: "label"
            valueRole: "identity"
            translateDisplayText: false
            currentIndex: model.findIndex(row => row.identity === root.rule.srcStatus)
            displayText: currentIndex >= 0 ? currentText : root.rule.srcStatus || ""
            onActivated: root.controller.set_rule_field("srcStatus", currentValue)
        }
    }
    ConfigurationSection {
        Layout.fillWidth: true
        visible: !root.notification
        theme: root.theme
        title: qsTr("Action")
        description: qsTr("Saving configures the trigger. It does not run the action.")
        Controls.ComboBox {
            objectName: "adminRuleAction"
            Layout.fillWidth: true
            theme: root.theme
            model: root.actions
            textRole: "label"
            valueRole: "identity"
            translateDisplayText: false
            currentIndex: model.findIndex(row => row.identity === root.rule.action)
            onActivated: root.controller.set_rule_field("action", currentValue)
        }
    }
    AdminProcessRuleAction {
        Layout.fillWidth: true
        theme: root.theme
        controller: root.controller
    }
    ConfigurationSection {
        Layout.fillWidth: true
        visible: !root.notification
        theme: root.theme
        title: qsTr("Execution mode")
        Controls.ComboBox {
            objectName: "adminRuleMode"
            Layout.fillWidth: true
            theme: root.theme
            model: [
                {identity: "same process,same transaction", label: qsTr("Same transaction")},
                {identity: "separate process,blocking", label: qsTr("Separate process, wait")},
                {identity: "separate process,non-blocking", label: qsTr("Separate process, background")},
                {identity: "separate process,queued", label: qsTr("Queued")}
            ]
            textRole: "label"
            valueRole: "identity"
            translateDisplayText: false
            currentIndex: model.findIndex(row => row.identity === root.rule.mode)
            displayText: currentIndex >= 0 ? currentText : root.rule.mode || ""
            onActivated: root.controller.set_rule_field("mode", currentValue)
        }
    }
}

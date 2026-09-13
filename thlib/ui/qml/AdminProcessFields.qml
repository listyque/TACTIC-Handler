import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

ColumnLayout {
    id: root

    required property var theme
    required property var controller
    readonly property string kind: controller.processKind
    readonly property var properties: controller.processProperties
    readonly property var defaults: controller.processSettings.default || ({})
    readonly property var related: kind === "progress" ? controller.processSettings.progress || ({}) : defaults
    readonly property string relatedSearchType: related.related_search_type || ""
    readonly property string relatedPipeline: related.related_pipeline_code || ""
    readonly property var fieldGroups: [
        {title: qsTr("Appearance"), description: "", fields: [
            {section: "properties", key: "label", label: qsTr("Display label"), help: qsTr("Shown on the canvas without changing the process name."), editor: "text"},
            {section: "properties", key: "color", label: qsTr("Color"), help: qsTr("Used for this process on the canvas and in task views."), editor: "color"}
        ]},
        {title: qsTr("Task settings"), description: qsTr("Assignment choices and default estimates for this process."), kinds: ["manual", "node", "approval"], fields: [
            {section: "properties", key: "assigned_group", label: qsTr("Assigned group"), help: qsTr("Limits the available assignees to members of this group."), options: "groups"},
            {section: "properties", key: "supervisor_group", label: qsTr("Supervisor group"), help: qsTr("Limits the available supervisors to members of this group."), options: "groups"},
            {section: "properties", key: "duration", label: qsTr("Default duration, days"), help: qsTr("Initial interval between a task's start and end dates."), editor: "integer"},
            {section: "properties", key: "bid_duration", label: qsTr("Estimated work, hours"), help: qsTr("Default planned effort for a new task."), editor: "integer"},
            {section: "properties", key: "completion", label: qsTr("Completion, %"), help: qsTr("Completion level represented by this process or status."), editor: "integer", maximum: 100},
            {section: "properties", key: "task_creation", label: qsTr("Create tasks"), help: qsTr("Include this process when generating tasks."), editor: "boolean", initial: true},
            {section: "properties", key: "autocreate_task", label: qsTr("Create tasks automatically"), help: qsTr("Create a task when a workflow event reaches this process."), editor: "boolean"},
            {section: "", key: "task_number", label: qsTr("Number of tasks"), help: qsTr("How many tasks to create for this process."), editor: "integer", minimum: 1}
        ]},
        {title: qsTr("Approval"), description: qsTr("Default reviewer for approval tasks."), kinds: ["approval"], fields: [
            {section: "default", key: "assigned", label: qsTr("Assigned user"), help: qsTr("Choose an existing user to receive approval tasks."), options: "users"}
        ]},
        {title: qsTr("Related workflow"), description: qsTr("Choose which objects and processes this node signals or tracks."), kinds: ["dependency", "progress"], fields: [
            {key: "related_search_type", label: qsTr("Search Type"), help: qsTr("The related objects affected by this node."), options: "searchTypes"},
            {key: "related_pipeline_code", label: qsTr("Related pipeline"), help: qsTr("Only pipelines of the selected Search Type are listed."), options: "relatedPipelines"},
            {key: "related_process", label: qsTr("Related process"), help: qsTr("The process to signal or listen to; leave empty to use the native default."), options: "relatedProcesses"},
            {key: "related_scope", label: qsTr("Scope"), help: qsTr("Affect related objects only, or all objects of this Search Type."), choices: [{identity: "local", label: qsTr("Related objects")}, {identity: "global", label: qsTr("All objects")}], initial: "local"},
            {key: "related_status", label: qsTr("Signal"), help: qsTr("The native workflow signal sent to the related process."), choices: [{identity: "Pending", label: "Pending"}, {identity: "Action", label: "Action"}, {identity: "Complete", label: "Complete"}], kinds: ["dependency"]},
            {key: "related_wait", label: qsTr("Wait for completion"), help: qsTr("Wait for a completion signal instead of completing this node immediately."), editor: "boolean", kinds: ["dependency"]},
            {key: "expression", label: qsTr("Related object expression"), help: qsTr("Optional TACTIC search expression; it replaces selection by Search Type."), editor: "text"}
        ]},
        {title: qsTr("Status behavior"), description: qsTr("Map this status to a native behavior, or explicitly change a connected process."), kinds: ["status"], fields: [
            {section: "default", key: "mapping", label: qsTr("Behave as"), help: qsTr("Native task status behavior."), choices: ["Assignment", "Pending", "In Progress", "Waiting", "Need Assistance", "Revise", "Reject", "Complete", "Approved"].map(value => ({identity: value, label: value}))},
            {section: "default", key: "direction", label: qsTr("Change process"), help: qsTr("Used when no status mapping is selected."), choices: [{identity: "output", label: qsTr("Output process")}, {identity: "input", label: qsTr("Input process")}, {identity: "process", label: qsTr("This process")}]},
            {section: "default", key: "status", label: qsTr("Target status"), help: qsTr("Exact status name understood by the target process."), editor: "text"}
        ]}
    ]

    function section(field) {
        return field.section !== undefined ? field.section : (kind === "progress" ? "progress" : "default")
    }
    function values(field) {
        const name = section(field)
        return name === "properties" ? properties
            : name ? (controller.processSettings[name] || {}) : controller.processSettings
    }
    function value(field) {
        const current = values(field)[field.key]
        return current !== undefined ? current : (field.initial !== undefined ? field.initial : "")
    }
    function options(field) {
        const metadata = controller.processCatalog
        let result = field.choices || metadata[field.options] || []
        if (field.options === "relatedPipelines")
            result = (metadata.pipelines || []).filter(row => row.searchType === relatedSearchType)
        else if (field.options === "relatedProcesses")
            result = (metadata.processes || []).filter(row => row.pipeline === relatedPipeline)
                .map(row => ({identity: kind === "progress" ? row.identity : row.label, label: row.label}))
        return [{identity: "", label: qsTr("Not set")}].concat(result)
    }

    spacing: 16
    enabled: root.controller.canWrite
    Repeater {
        model: root.fieldGroups
        delegate: ConfigurationSection {
            required property var modelData
            Layout.fillWidth: true
            visible: !modelData.kinds || modelData.kinds.includes(root.kind)
            theme: root.theme
            title: modelData.title
            description: modelData.description
            Repeater {
                model: modelData.kinds && !modelData.kinds.includes(root.kind) ? []
                    : modelData.fields.filter(field => (!field.kinds || field.kinds.includes(root.kind))
                        && !(root.kind === "hierarchy" && field.key === "task_creation"))
                delegate: Controls.SettingsRow {
                    id: fieldRow
                    required property var modelData
                    Layout.fillWidth: true
                    visible: (!modelData.kinds || modelData.kinds.includes(root.kind))
                        && !(root.kind === "hierarchy" && modelData.key === "task_creation")
                    theme: root.theme
                    title: modelData.label
                    description: modelData.help
                    Loader {
                        Layout.preferredWidth: Math.max(80, Math.min(260, root.width - 48))
                        Layout.fillWidth: fieldRow.stackControl
                        // Different native field kinds create only their actual editor.
                        sourceComponent: fieldRow.modelData.editor === "color" ? colorEditor
                            : fieldRow.modelData.editor === "boolean" ? booleanEditor
                            : fieldRow.modelData.editor ? textEditor : choiceEditor
                        property var field: fieldRow.modelData
                    }
                }
            }
        }
    }
    Component {
        id: textEditor
        Controls.TextField {
            objectName: "adminProcessField_" + field.key
            theme: root.theme
            text: String(root.value(field))
            validator: field.editor === "integer" ? integerValidator : null
            IntValidator { id: integerValidator; bottom: field.minimum || 0; top: field.maximum || 1000000 }
            // Empty is an optional native value, but IntValidator treats it
            // as intermediate and therefore does not emit editingFinished.
            onTextEdited: if (field.editor === "integer" && !text.length)
                root.controller.set_process_setting(root.section(field), field.key, "")
            onEditingFinished: if (acceptableInput)
                root.controller.set_process_setting(root.section(field), field.key,
                    field.editor === "integer" && text.length ? Number(text) : text)
        }
    }
    Component {
        id: booleanEditor
        Controls.CheckBox {
            objectName: "adminProcessField_" + field.key
            theme: root.theme
            Accessible.name: field.label
            checked: root.value(field) === true || root.value(field) === "true"
            onToggled: root.controller.set_process_setting(root.section(field), field.key, checked)
        }
    }
    Component {
        id: choiceEditor
        Controls.ComboBox {
            objectName: "adminProcessField_" + field.key
            theme: root.theme
            model: root.options(field)
            textRole: "label"
            valueRole: "identity"
            translateDisplayText: false
            currentIndex: model.findIndex(row => row.identity === root.value(field))
            displayText: currentIndex >= 0 ? currentText : String(root.value(field))
            onActivated: root.controller.set_process_setting(root.section(field), field.key, currentValue)
        }
    }
    Component {
        id: colorEditor
        Controls.ColorField {
            objectName: "adminProcessField_color"
            theme: root.theme
            value: String(root.value(field))
            onColorChosen: value => root.controller.set_process_setting(root.section(field), field.key, value)
        }
    }
}

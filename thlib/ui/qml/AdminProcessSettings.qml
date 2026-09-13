import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

ColumnLayout {
    id: root

    required property var theme
    required property var controller
    property string page: "parameters"
    readonly property real fieldWidth: Math.max(80, Math.min(280, form.width - 48))
    readonly property string processIdentity: controller.selectedNode
    onProcessIdentityChanged: {
        page = "parameters"
        settingsScroll.contentY = 0
    }
    onPageChanged: settingsScroll.contentY = 0
    readonly property var settings: controller.processSettings
    readonly property var defaults: settings.default || ({})
    readonly property string kind: controller.processKind
    readonly property bool taskNode: kind === "manual" || kind === "node" || kind === "approval"
    readonly property bool actionNode: kind === "action" || kind === "condition"
    readonly property bool hasProcess: controller.mode === "workflow" && controller.selectedNode.length > 0
    readonly property bool editable: hasProcess && controller.canWrite

    spacing: 12

    Controls.EmptyState {
        Layout.fillWidth: true
        Layout.fillHeight: true
        visible: !root.hasProcess
        theme: root.theme
        iconName: "process"
        title: qsTr("Select a process on the canvas")
        message: qsTr("Its description, action and native settings will appear here.")
    }
    Controls.SegmentedButton {
        objectName: "adminProcessPages"
        Layout.fillWidth: true
        visible: root.hasProcess
        theme: root.theme
        currentValue: root.page
        model: [
            {value: "parameters", label: "Parameters", icon: "tune"},
            {value: "native_json", label: "Advanced JSON", icon: "code"}
        ]
        onActivated: value => {
            root.forceActiveFocus()
            root.page = value
        }
    }
    Flickable {
        id: settingsScroll
        objectName: "adminProcessSettingsViewport"
        Layout.fillWidth: true
        Layout.fillHeight: true
        visible: root.hasProcess
        clip: true
        contentWidth: width
        contentHeight: form.implicitHeight + 4
        boundsBehavior: Flickable.StopAtBounds

        ColumnLayout {
            id: form
            width: Math.max(0, settingsScroll.width - settingsBar.reservedExtent - 4)
            spacing: 16

            AdminXmlEditor {
                objectName: "adminProcessNativeSettingsEditor"
                Layout.fillWidth: true
                Layout.preferredHeight: 340
                Layout.minimumHeight: implicitHeight
                theme: root.theme
                visible: root.page === "native_json"
                title: qsTr("Native process settings")
                description: qsTr("Advanced access to native data, including parameters of installed custom nodes. Standard settings are available in Parameters.")
                sourceText: root.controller.settingsText
                readOnly: !root.editable
                onApplied: text => root.controller.apply_settings(text)
            }
            AdminXmlEditor {
                objectName: "adminSelectionAttributesEditor"
                Layout.fillWidth: true
                Layout.preferredHeight: 300
                Layout.minimumHeight: implicitHeight
                theme: root.theme
                visible: root.page === "native_json"
                title: qsTr("Attributes (JSON)")
                buttonText: qsTr("Apply")
                sourceText: root.controller.attributesText
                readOnly: !root.editable
                onApplied: text => root.controller.apply_attributes(text)
            }
            ColumnLayout {
                Layout.fillWidth: true
                visible: root.page === "parameters"
                spacing: 16
                ConfigurationSection {
                    Layout.fillWidth: true
                    theme: root.theme
                    title: root.controller.selectedNode
                    description: qsTr("Node type: %1").arg(root.kind)

                    Controls.SettingsRow {
                        theme: root.theme
                        title: qsTr("Description")
                        description: qsTr("Explain what happens at this stage of the workflow.")
                        showDivider: false
                        Controls.TextField {
                            objectName: "adminProcessDescription"
                            Layout.preferredWidth: root.fieldWidth
                            theme: root.theme
                            text: root.controller.processDescription
                            readOnly: !root.editable
                            onTextEdited: root.controller.set_process_description(text)
                        }
                    }
                }
                ConfigurationSection {
                    Layout.fillWidth: true
                    visible: root.taskNode
                    theme: root.theme
                    title: qsTr("Task status workflow")
                    description: qsTr("Defines statuses only for tasks of this process, not stages of the parent Search Object workflow.")
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        Controls.ComboBox {
                            objectName: "adminProcessField_task_pipeline"
                            Layout.fillWidth: true
                            theme: root.theme
                            enabled: root.editable
                            textRole: "label"
                            valueRole: "identity"
                            translateDisplayText: false
                            model: [{identity: "", label: qsTr("Use TACTIC default")}].concat(
                                (root.controller.processCatalog.pipelines || []).filter(row => row.searchType === "sthpw/task"))
                            currentIndex: model.findIndex(row => row.identity === (root.controller.processProperties.task_pipeline || ""))
                            displayText: currentIndex >= 0 ? currentText : root.controller.processProperties.task_pipeline || ""
                            onActivated: root.controller.set_process_setting("properties", "task_pipeline", currentValue)
                        }
                        Controls.Button {
                            objectName: "adminEditTaskWorkflow"
                            Layout.fillWidth: true
                            theme: root.theme
                            text: qsTr("Edit task status workflow")
                            icon.name: "edit"
                            enabled: !!root.controller.processProperties.task_pipeline
                            onClicked: {
                                root.forceActiveFocus()
                                root.controller.open_task_workflow()
                            }
                        }
                    }
                }
                AdminProcessFields {
                    Layout.fillWidth: true
                    theme: root.theme
                    controller: root.controller
                }
                ConfigurationSection {
                    Layout.fillWidth: true
                    theme: root.theme
                    title: qsTr("Process dependencies")
                    description: qsTr("Triggers, notifications, naming conventions and objects using this pipeline. Save node changes before editing dependencies.")
                    Controls.Button {
                        objectName: "adminOpenProcessDependencies"
                        Layout.fillWidth: true
                        theme: root.theme
                        text: qsTr("Open process dependencies")
                        icon.name: "schema"
                        onClicked: {
                            root.forceActiveFocus()
                            root.controller.rulesEditor.open()
                        }
                    }
                }
                ConfigurationSection {
                    Layout.fillWidth: true
                    visible: root.actionNode
                    theme: root.theme
                    title: qsTr("Process action")
                    description: qsTr("Action and condition nodes use a native process|action trigger. Script changes are saved, not executed by this editor.")

                    Controls.SettingsRow {
                        theme: root.theme
                        title: qsTr("Action")
                        description: qsTr("Use a script or an installed server command class.")
                        Controls.SegmentedButton {
                            objectName: "adminProcessActionMode"
                            Layout.preferredWidth: root.fieldWidth
                            theme: root.theme
                            enabled: root.editable
                            currentValue: root.defaults.action === "command" ? "command" : "create_new"
                            model: [
                                {value: "create_new", label: "Script", icon: "code"},
                                {value: "command", label: "Command class", icon: "process"}
                            ]
                            onActivated: value => root.controller.set_process_setting("default", "action", value)
                        }
                    }
                    Controls.SettingsRow {
                        visible: root.defaults.action === "command"
                        theme: root.theme
                        title: qsTr("Native command class")
                        description: qsTr("The installed Python command that handles this action.")
                        Controls.TextField {
                            objectName: "adminProcessCommandClass"
                            Layout.preferredWidth: root.fieldWidth
                            theme: root.theme
                            text: root.defaults.on_action_class || ""
                            readOnly: !root.editable
                            onTextEdited: root.controller.set_process_setting("default", "on_action_class", text)
                        }
                    }
                    Controls.SettingsRow {
                        visible: root.defaults.action !== "command"
                        theme: root.theme
                        title: qsTr("Script path (optional)")
                        description: qsTr("Use an existing server script, or provide a script body below.")
                        Controls.TextField {
                            objectName: "adminProcessScriptPath"
                            Layout.preferredWidth: root.fieldWidth
                            theme: root.theme
                            text: root.defaults.script_path || ""
                            readOnly: !root.editable
                            onTextEdited: root.controller.set_process_setting("default", "script_path", text)
                        }
                    }
                    Controls.SettingsRow {
                        visible: root.defaults.action !== "command"
                        theme: root.theme
                        title: qsTr("Script language")
                        description: qsTr("The language used by the native server handler.")
                        Controls.SegmentedButton {
                            objectName: "adminProcessScriptLanguage"
                            Layout.preferredWidth: root.fieldWidth
                            theme: root.theme
                            enabled: root.editable
                            currentValue: root.defaults.language === "server_js" ? "server_js" : "python"
                            model: [
                                {value: "python", label: "python", translate: false},
                                {value: "server_js", label: "server_js", translate: false}
                            ]
                            onActivated: value => root.controller.set_process_setting("default", "language", value)
                        }
                    }
                    Controls.SettingsRow {
                        theme: root.theme
                        title: qsTr("Trigger execution mode")
                        description: qsTr("Use the execution mode supported by the installed server handler.")
                        showDivider: false
                        Controls.ComboBox {
                            objectName: "adminProcessExecutionMode"
                            Layout.preferredWidth: root.fieldWidth
                            theme: root.theme
                            enabled: root.editable
                            textRole: "label"
                            valueRole: "identity"
                            translateDisplayText: false
                            model: [
                                {identity: "", label: qsTr("Not set")},
                                {identity: "same process,same transaction", label: qsTr("In process")},
                                {identity: "separate process,blocking", label: qsTr("Separate process, blocking")},
                                {identity: "separate process,non-blocking", label: qsTr("Separate process, non-blocking")},
                                {identity: "separate process,queued", label: qsTr("Queued")}
                            ]
                            currentIndex: model.findIndex(row => row.identity === (root.defaults.execute_mode || ""))
                            displayText: currentIndex >= 0 ? currentText : root.defaults.execute_mode || ""
                            onActivated: root.controller.set_process_setting("default", "execute_mode", currentValue)
                        }
                    }
                }
                AdminXmlEditor {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 340
                    visible: root.actionNode && root.defaults.action !== "command"
                    theme: root.theme
                    title: qsTr("Script body")
                    description: qsTr("The code is stored with this process. Applying the draft does not run it.")
                    sourceText: root.defaults.script || ""
                    readOnly: !root.editable
                    onApplied: text => root.controller.set_process_setting("default", "script", text)
                }
                Controls.EditorPanel {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 280
                    visible: root.kind === "hierarchy"
                    theme: root.theme
                    title: qsTr("Subpipeline")
                    description: qsTr("Choose the pipeline this hierarchy process opens.")
                    iconName: "schema"

                    Controls.TextField {
                        id: pipelineFilter
                        objectName: "adminSubpipelineFilter"
                        Layout.fillWidth: true
                        theme: root.theme
                        placeholderText: qsTr("Find a pipeline")
                    }
                    ListView {
                        id: pipelines
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        spacing: 4
                        boundsBehavior: Flickable.StopAtBounds
                        model: (root.controller.metadata.pipelines || []).filter(row =>
                            row.identity !== root.controller.identity && row.searchType === root.controller.document.searchType
                            && (String(row.label || "") + " " + row.identity).toLocaleLowerCase().includes(pipelineFilter.text.toLocaleLowerCase()))
                        delegate: Controls.EditorListItem {
                            required property var modelData
                            objectName: "adminSubpipeline_" + modelData.identity
                            width: Math.max(0, pipelines.width - pipelineBar.reservedExtent - 4)
                            theme: root.theme
                            text: modelData.label || modelData.identity
                            description: modelData.identity
                            iconName: "schema"
                            selected: (root.settings.hierarchy || {}).subpipeline === modelData.identity
                            enabled: root.editable
                            onClicked: root.controller.set_process_setting("hierarchy", "subpipeline", modelData.identity)
                        }
                        ScrollBar.vertical: Controls.ScrollBar {
                            id: pipelineBar
                            theme: root.theme
                            flickableTarget: pipelines
                        }
                    }
                    Controls.ComboBox {
                        objectName: "adminHierarchyTaskCreation"
                        Layout.fillWidth: true
                        theme: root.theme
                        textRole: "label"
                        valueRole: "identity"
                        translateDisplayText: false
                        model: [
                            {identity: "subtasks_only", label: qsTr("Create subtasks only")},
                            {identity: "top_only", label: qsTr("Create parent task only")},
                            {identity: "all", label: qsTr("Create parent task and subtasks")},
                            {identity: "none", label: qsTr("Do not create tasks")}
                        ]
                        currentIndex: model.findIndex(row => row.identity === (root.defaults.task_creation || "subtasks_only"))
                        onActivated: root.controller.set_process_setting("default", "task_creation", currentValue)
                    }
                }
                ConfigurationSection {
                    Layout.fillWidth: true
                    theme: root.theme
                    title: qsTr("Node type")
                    visible: root.controller.document.searchType !== "sthpw/task"
                    description: qsTr("Choose the native behavior of this process.")
                    Controls.ResponsiveFlow {
                        Layout.fillWidth: true
                        enabled: root.editable
                        spacing: 6
                        minimumCellWidth: 100
                        maximumColumns: 2
                        Repeater {
                            model: root.controller.metadata.nodeTypes || []
                            delegate: Controls.EditorListItem {
                                id: selectedKindOption
                                required property string modelData
                                objectName: "adminSelectedNodeType_" + modelData
                                width: parent.cellWidth()
                                theme: root.theme
                                text: modelData
                                selected: modelData === root.kind
                                onClicked: root.controller.set_attribute("type", modelData)
                                Controls.ToolTip {
                                    theme: root.theme
                                    text: selectedKindOption.modelData
                                    visible: selectedKindOption.hovered
                                }
                            }
                        }
                    }
                }
            }
        }
        ScrollBar.vertical: Controls.ScrollBar {
            id: settingsBar
            theme: root.theme
            flickableTarget: settingsScroll
        }
    }
}

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root
    required property var theme
    readonly property var controller: projectCreationController
    readonly property var draft: controller.draft
    readonly property var steps: [
        {title: qsTr("Details"), icon: "edit", description: qsTr("Choose a name and a unique code for the project.")},
        {title: qsTr("Preview Image"), icon: "image", description: qsTr("Optional image used to identify the project. TACTIC uploads it and creates its preview during project creation.")},
        {title: qsTr("Template"), icon: "layers", description: qsTr("Copy the template configuration, or create an empty project. Templates and themes are loaded from your TACTIC server.")},
        {title: qsTr("Review"), icon: "check-circle", description: qsTr("Check the details before creating your project.")}
    ]
    readonly property bool compactNavigation: width < 900
    readonly property int currentStep: controller.step
    readonly property var selectedTheme: controller.themes.find(row => row.value === draft.theme) || ({})
    readonly property var selectedTemplate: controller.templates.find(row => row.value === draft.source) || ({})
    readonly property bool emptyProject: draft.source === "_empty"

    component WizardField: Controls.SettingsRow {
        id: field
        required property string fieldKey
        Layout.fillWidth: true
        theme: root.theme
        Controls.TextField {
            objectName: "projectWizard_" + field.fieldKey
            Layout.preferredWidth: Math.min(320, field.width - 8)
            theme: root.theme
            text: root.draft[field.fieldKey] || ""
            Accessible.name: field.title
            onTextEdited: root.controller.set_value(field.fieldKey, text)
        }
    }
    component SummaryRow: Controls.SettingsRow {
        id: summary
        required property string value
        theme: root.theme
        Label {
            Layout.preferredWidth: Math.min(320, summary.width - 8)
            text: summary.value
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
            wrapMode: Text.WrapAnywhere
        }
    }
    component WizardLabel: Label {
        Layout.fillWidth: true
        color: root.theme.secondaryText
        wrapMode: Text.WordWrap
        font.family: root.theme.fontFamily
        font.pointSize: Controls.Typography.body
    }

    Connections {
        target: root.controller
        function onCompleted() { windowModel.close_window("project_wizard") }
    }
    onCurrentStepChanged: {
        if (scroll && scroll.contentItem)
            scroll.contentItem.contentY = 0
    }
    Rectangle { anchors.fill: parent; color: root.theme.workspace }
    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        RowLayout {
            Layout.fillWidth: true
            Layout.margins: 24
            spacing: 16
            ColumnLayout {
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                spacing: 6
                WizardLabel {
                    text: qsTr("Create project")
                    color: root.theme.primaryText
                    font.pointSize: Controls.Typography.title
                    font.weight: Font.DemiBold
                }
                WizardLabel {
                    text: root.steps[root.currentStep].description
                    font.pointSize: Controls.Typography.caption
                }
            }
            Label {
                objectName: "projectWizardStepCounter"
                text: qsTr("Step %1 of %2").arg(root.currentStep + 1).arg(root.steps.length)
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.caption
            }
            Controls.CompactIconButton {
                theme: root.theme
                iconName: "help"
                toolTip: qsTr("Project creation help")
                onClicked: windowModel.open_help("project_creation")
            }
        }
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: root.theme.outlineVariant
        }
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0
            Rectangle {
                Layout.preferredWidth: root.compactNavigation ? 80 : 232
                Layout.fillHeight: true
                color: root.theme.surfaceContainerLow
                ListView {
                    id: stepsList
                    objectName: "projectWizardSteps"
                    anchors.fill: parent
                    topMargin: 16
                    leftMargin: 12
                    rightMargin: stepsBar.reservedExtent + 12
                    bottomMargin: 16
                    spacing: 6
                    model: root.steps
                    clip: true
                    ScrollBar.vertical: Controls.ScrollBar {
                        id: stepsBar
                        theme: root.theme
                        flickableTarget: stepsList
                    }
                    delegate: Controls.SettingsNavigationItem {
                        required property int index
                        required property var modelData
                        objectName: "projectWizardStep_" + index
                        width: stepsList.width - stepsList.leftMargin - stepsList.rightMargin
                        theme: root.theme
                        text: (index + 1) + ". " + modelData.title
                        description: modelData.description
                        iconName: index < root.currentStep ? "check" : modelData.icon
                        compact: root.compactNavigation
                        selected: index === root.currentStep
                        enabled: index <= root.currentStep && !root.controller.busy && !root.controller.createdCode
                        onClicked: root.controller.select_step(index)
                    }
                }
            }
            ScrollView {
                id: scroll
                objectName: "projectWizardScroll"
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                contentWidth: availableWidth
                contentHeight: content.implicitHeight + 48
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                ScrollBar.vertical: Controls.ScrollBar {
                    id: contentBar
                    objectName: "projectWizardContentBar"
                    theme: root.theme
                    flickableTarget: scroll
                }
                ColumnLayout {
                    id: content
                    x: 24
                    y: 24
                    width: Math.max(0, scroll.availableWidth - 48 - contentBar.reservedExtent)
                    spacing: 16
                    ConfigurationSection {
                        Layout.fillWidth: true
                        visible: root.controller.step === 0
                        enabled: !root.controller.busy
                        theme: root.theme
                        title: qsTr("Project details")
                        WizardField {
                            fieldKey: "title"
                            title: qsTr("Project title")
                            description: qsTr("The title can contain spaces and special characters, up to 100 characters.")
                        }
                        WizardField {
                            fieldKey: "code"
                            title: qsTr("Project code")
                            description: qsTr("Use letters, numbers and underscores, up to 30 characters. The code cannot start with a number and must be unique, including retired projects.")
                        }
                        WizardField {
                            fieldKey: "category"
                            title: qsTr("Category")
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            Layout.topMargin: 12
                            Layout.bottomMargin: 16
                            spacing: 8
                            WizardLabel {
                                text: qsTr("Project description")
                                color: root.theme.primaryText
                            }
                            Controls.TextArea {
                                objectName: "projectWizard_description"
                                Layout.fillWidth: true
                                Layout.minimumHeight: 104
                                theme: root.theme
                                text: root.draft.description || ""
                                placeholderText: qsTr("What is this project about?")
                                Accessible.name: qsTr("Project description")
                                onTextChanged: {
                                    if (text !== root.draft.description)
                                        root.controller.set_value("description", text)
                                }
                            }
                        }
                        WizardField {
                            fieldKey: "namespace"
                            title: qsTr("Namespace")
                            enabled: root.emptyProject
                            description: qsTr("Prefix for new Search Types: studio gives studio/shot, for example. Leave empty to use the project code. Does not rename the project. The sthpw and prod namespaces are reserved.")
                        }
                        Controls.SettingsRow {
                            theme: root.theme
                            title: qsTr("Use this project as a template")
                            enabled: root.emptyProject
                            Controls.Switch {
                                objectName: "projectWizardIsTemplate"
                                theme: root.theme
                                text: ""
                                Accessible.name: qsTr("Use this project as a template")
                                checked: Boolean(root.draft.isTemplate)
                                onToggled: root.controller.set_value("isTemplate", checked)
                            }
                        }
                        Controls.SettingsRow {
                            theme: root.theme
                            title: qsTr("Main project")
                            enabled: root.emptyProject
                            description: qsTr("An empty project can become the default project at the TACTIC root URL. TACTIC may need a restart for this to take effect.")
                            showDivider: false
                            Controls.Switch {
                                objectName: "projectWizardMain"
                                theme: root.theme
                                text: ""
                                Accessible.name: qsTr("Set as main project")
                                checked: Boolean(root.draft.isMainProject)
                                onToggled: root.controller.set_value("isMainProject", checked)
                            }
                        }
                        WizardLabel {
                            text: qsTr("Current main project: %1 (%2)").arg(root.controller.catalog.defaultProject?.title || "—").arg(root.controller.catalog.defaultProject?.code || "—")
                            font.pointSize: Controls.Typography.caption
                        }
                    }
                    ConfigurationSection {
                        Layout.fillWidth: true
                        visible: root.controller.step === 1
                        enabled: !root.controller.busy
                        theme: root.theme
                        title: qsTr("Project image")
                        description: qsTr("Optional image used to identify the project. TACTIC uploads it and creates its preview during project creation.")
                        Controls.ImagePicker {
                            Layout.fillWidth: true
                            theme: root.theme
                            objectNamePrefix: "projectWizard"
                            previewSize: 140
                            stagedPath: root.draft.previewPath || ""
                            previewUrl: root.controller.previewUrl
                            fallbackText: (root.draft.code || "").slice(0, 2).toUpperCase()
                            statusText: stagedPath || qsTr("No image selected")
                            onSelectionRequested: image => root.controller.set_value("previewPath", image)
                        }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        visible: root.controller.step === 2
                        enabled: !root.controller.busy
                        spacing: 16
                        ConfigurationSection {
                            Layout.fillWidth: true
                            theme: root.theme
                            title: qsTr("Copy from template")
                            description: qsTr("Copy the template configuration, or create an empty project. Templates and themes are loaded from your TACTIC server.")
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 12
                                Controls.ComboBox {
                                    objectName: "projectWizardTemplate"
                                    Layout.fillWidth: true
                                    theme: root.theme
                                    model: root.controller.templates
                                    textRole: "label"
                                    valueRole: "value"
                                    translateDisplayText: false
                                    currentIndex: Math.max(0, indexOfValue(root.draft.source))
                                    Accessible.name: qsTr("Copy from template")
                                    onActivated: root.controller.set_value("source", currentValue)
                                }
                                RowLayout {
                                    objectName: "projectWizardTemplateActions"
                                    spacing: 8
                                    Controls.Button {
                                        theme: root.theme
                                        text: qsTr("Manage templates")
                                        icon.name: "settings"
                                        onClicked: windowModel.show_child_window("project_templates", "project_wizard")
                                    }
                                    Controls.CompactIconButton {
                                        theme: root.theme
                                        iconName: "refresh"
                                        toolTip: qsTr("Refresh templates")
                                        onClicked: root.controller.reload_catalog()
                                    }
                                }
                                WizardLabel {
                                    visible: !root.emptyProject
                                    text: qsTr("A template supplies its own namespace and configuration. Main-project, namespace, theme and template flags apply only to an empty project.")
                                }
                            }
                        }
                        ConfigurationSection {
                            Layout.fillWidth: true
                            visible: root.emptyProject
                            theme: root.theme
                            title: qsTr("Empty project settings")
                            Controls.SettingsRow {
                                objectName: "projectWizardThemeSetting"
                                theme: root.theme
                                title: qsTr("Theme")
                                description: qsTr("Only for the TACTIC web interface. Does not affect TACTIC-Handler's appearance.")
                                showDivider: false
                                Controls.ComboBox {
                                    objectName: "projectWizardTheme"
                                    Layout.preferredWidth: Math.min(320, content.width - 40)
                                    theme: root.theme
                                    model: root.controller.themes
                                    textRole: "label"
                                    valueRole: "value"
                                    translateDisplayText: false
                                    currentIndex: Math.max(0, indexOfValue(root.draft.theme))
                                    Accessible.name: qsTr("Theme")
                                    onActivated: root.controller.set_value("theme", currentValue)
                                }
                            }
                            Controls.ItemPreview {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 150
                                visible: Boolean(root.selectedTheme.preview)
                                theme: root.theme
                                source: root.selectedTheme.preview || ""
                                fillMode: Image.PreserveAspectFit
                                effectsEnabled: false
                            }
                            WizardLabel {
                                visible: text.length > 0
                                text: root.selectedTheme.description || ""
                            }
                        }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        visible: root.controller.step === 3
                        enabled: !root.controller.busy && !root.controller.createdCode
                        spacing: 16
                        ConfigurationSection {
                            Layout.fillWidth: true
                            theme: root.theme
                            title: qsTr("Project summary")
                            RowLayout {
                                Layout.fillWidth: true
                                Layout.bottomMargin: 20
                                spacing: 20
                                Controls.ItemPreview {
                                    objectName: "projectWizardReviewPreview"
                                    Layout.preferredWidth: root.compactNavigation ? 88 : 128
                                    Layout.preferredHeight: Layout.preferredWidth
                                    Layout.alignment: Qt.AlignTop
                                    theme: root.theme
                                    source: root.controller.previewUrl
                                    fallbackText: (root.draft.code || "").slice(0, 2).toUpperCase()
                                    cornerRadius: root.theme.surfaceRadius
                                    animateAppearance: false
                                }
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    Layout.alignment: Qt.AlignTop
                                    spacing: 8
                                    WizardLabel {
                                        text: root.draft.title
                                        color: root.theme.primaryText
                                        font.pointSize: Controls.Typography.title
                                        font.weight: Font.DemiBold
                                        wrapMode: Text.WrapAnywhere
                                    }
                                    WizardLabel {
                                        text: root.draft.code
                                        wrapMode: Text.WrapAnywhere
                                        font.pointSize: Controls.Typography.caption
                                    }
                                    WizardLabel {
                                        objectName: "projectWizardReviewDescription"
                                        visible: text.length > 0
                                        text: (root.draft.description || "").trim()
                                        wrapMode: Text.WrapAnywhere
                                    }
                                }
                            }
                            SummaryRow {
                                objectName: "projectWizardReviewCategory"
                                title: qsTr("Category")
                                value: root.draft.category || qsTr("Not set")
                            }
                            SummaryRow {
                                title: qsTr("Template")
                                value: root.selectedTemplate.label || ""
                                showDivider: root.emptyProject
                            }
                            SummaryRow {
                                visible: root.emptyProject
                                title: qsTr("Namespace")
                                value: root.draft.namespace || root.draft.code
                            }
                            SummaryRow {
                                visible: root.emptyProject
                                title: qsTr("Theme")
                                value: root.selectedTheme.label || ""
                            }
                            SummaryRow {
                                visible: root.emptyProject
                                title: qsTr("Main project")
                                value: root.draft.isMainProject ? qsTr("Yes") : qsTr("No")
                            }
                            SummaryRow {
                                visible: root.emptyProject
                                title: qsTr("Use this project as a template")
                                value: root.draft.isTemplate ? qsTr("Yes") : qsTr("No")
                                showDivider: false
                            }
                        }
                    }
                    WizardLabel {
                        objectName: "projectWizardError"
                        visible: root.controller.error.length > 0
                        text: root.controller.error
                        color: root.theme.error
                    }
                }
            }
        }
        Controls.DockWorkspaceFooter {
            Layout.fillWidth: true
            Layout.preferredHeight: 64
            theme: root.theme
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 24
                anchors.rightMargin: 24
                anchors.topMargin: 12
                anchors.bottomMargin: 12
                spacing: 8
                Controls.BusyIndicator {
                    uiTheme: root.theme
                    running: root.controller.busy
                    visible: running
                    Layout.preferredWidth: 24
                    Layout.preferredHeight: 24
                }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("Cancel")
                    flat: true
                    enabled: !root.controller.busy
                    onClicked: windowModel.close_window("project_wizard")
                }
                Item { Layout.fillWidth: true }
                Controls.Button {
                    objectName: "projectWizardBack"
                    theme: root.theme
                    text: qsTr("Back")
                    icon.name: "chevron-left"
                    flat: true
                    visible: root.controller.step > 0 && !root.controller.createdCode
                    enabled: !root.controller.busy && root.controller.step > 0 && !root.controller.createdCode
                    onClicked: root.controller.previous_step()
                }
                Controls.Button {
                    objectName: "projectWizardNext"
                    theme: root.theme
                    text: qsTr("Next")
                    icon.name: "chevron-right"
                    visible: root.controller.step < 3
                    enabled: !root.controller.busy && root.controller.ready
                    highlighted: true
                    onClicked: root.controller.next_step()
                }
                Controls.Button {
                    objectName: "projectWizardCreate"
                    theme: root.theme
                    text: root.controller.createdCode ? qsTr("Retry opening project") : qsTr("Create project")
                    icon.name: "check"
                    visible: root.controller.step === 3
                    enabled: !root.controller.busy && root.controller.ready
                    highlighted: true
                    onClicked: root.controller.submit()
                }
            }
        }
    }
}

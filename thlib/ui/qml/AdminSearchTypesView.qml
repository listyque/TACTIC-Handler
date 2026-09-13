import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

AdminDocumentShell {
    id: root
    property string page: "entity_summary"
    property bool creationOnly: false
    property var namingController: null
    property string projectCode: ""
    readonly property bool namingPage: page === "entity_naming"
    readonly property bool namingLocked: namingController && (namingController.busy || namingController.dirty)
    signal openWorkflowRequested(string identity)
    signal createWorkflowRequested()
    readonly property bool creatingType: controller.document.hasPipeline !== undefined
    readonly property bool compactCatalog: typeList.width < 280
    readonly property bool compactEditor: editorColumn.width < 480
    readonly property bool presentationVisible: visible && !!Window.window && Window.window.visible
    onCreatingTypeChanged: if (creatingType || creationOnly) {
        page = "entity_details"
        formScroll.contentY = 0
    }
    title: qsTr("Search Types")
    description: qsTr("Select a Search Type to edit its appearance and fields. Changes stay in your draft until you save.")
    iconName: "sobject"
    allowCreate: !creationOnly && !namingLocked
    allowReload: !creationOnly && !namingLocked
    allowSave: !creationOnly || page === "entity_review" || !!controller.identity

    function wizardPage(value) {
        if (!root.controller.identity && value !== "entity_details" && !root.controller.validate_creation_details()) return
        root.forceActiveFocus()
        root.page = value
        formScroll.contentY = 0
    }
    confirmationDetails: (controller.document.removedColumns || []).length
        ? qsTr("Delete columns from %1 (%2):")
            .arg(controller.document.title || controller.identity).arg(controller.identity)
            + "\n" + controller.document.removedColumns.map(name => "• " + name).join("\n")
            + "\n\n" + qsTr("All data in these columns will be lost. This editor cannot restore it after saving. Check any scripts, naming rules and saved searches that use these fields.")
        : ""
    showSelector: false
    showDocumentChrome: !namingPage
    onPresentationVisibleChanged: controller.set_presentation_visible(presentationVisible)
    Component.onCompleted: controller.set_presentation_visible(presentationVisible)
    Component.onDestruction: controller.set_presentation_visible(false)

    Connections {
        target: root.controller
        function onStateChanged() {
            if (root.namingPage && root.namingController
                && root.controller.identity !== root.namingController.currentObject.searchType)
                root.page = "entity_summary"
        }
    }
    Connections {
        target: root.namingController
        function onStateChanged() {
            if (root.namingPage && !root.namingController.typeMode)
                root.page = "entity_summary"
        }
    }

    editorContent: RowLayout {
        // The alias reparents this item into AdminDocumentShell's plain Item.
        anchors.fill: parent // qmllint disable Quick.layout-positioning
        spacing: 12
        Controls.EditorPanel {
            visible: !root.creationOnly && !root.namingPage
            Layout.preferredWidth: Math.max(220, Math.min(340, root.width * 0.34))
            Layout.fillHeight: true
            Layout.minimumWidth: 0
            theme: root.theme
            title: qsTr("Search Types")
            iconName: "view_list"
            Controls.TextField {
                id: catalogSearch
                objectName: "adminSearchTypeFilter"
                Layout.fillWidth: true
                theme: root.theme
                placeholderText: qsTr("Find a Search Type")
            }
            Controls.CheckBox {
                id: projectOnly
                objectName: "adminSearchTypesProjectOnly"
                checked: true
                Layout.fillWidth: true
                theme: root.theme
                compact: true
                text: qsTr("Only current project")
                Accessible.description: qsTr("Types stored in the selected project's database, regardless of their namespace. Turn off to include shared system types.")
                Controls.ToolTip {
                    theme: root.theme
                    visible: projectOnly.hovered
                    text: projectOnly.Accessible.description
                }
            }
            Controls.CheckBox {
                id: hideConfig
                objectName: "adminSearchTypesHideConfig"
                checked: true
                Layout.fillWidth: true
                theme: root.theme
                compact: true
                text: qsTr("Hide config types")
            }
            RowLayout {
                Layout.fillWidth: true
                Label {
                    Layout.fillWidth: true
                    text: qsTr("Name")
                    color: root.theme.secondaryText
                    font.pointSize: Controls.Typography.label
                }
                Label {
                    Layout.preferredWidth: 74
                    visible: !root.compactCatalog
                    text: qsTr("Table")
                    color: root.theme.secondaryText
                    font.pointSize: Controls.Typography.label
                }
            }
            ListView {
                id: typeList
                objectName: "adminSearchTypesList"
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 4
                boundsBehavior: Flickable.StopAtBounds
                model: root.controller.catalog.filter(row =>
                    (!projectOnly.checked || row.projectLocal)
                    && (!hideConfig.checked || row.namespace !== "config")
                    && (row.label + " " + row.identity).toLowerCase().includes(catalogSearch.text.toLowerCase()))
                delegate: Controls.PopupAction {
                    id: typeRow
                    required property var modelData
                    objectName: "adminSearchType_" + modelData.identity
                    width: typeList.width - typeBar.reservedExtent - 4
                    height: modelData.manyToMany || (modelData.relationships || []).length > 0 ? 84 : 68
                    padding: 10
                    enabled: !root.controller.busy && !root.controller.dirty && !root.namingLocked
                    Accessible.name: modelData.label
                    onClicked: root.controller.select(modelData.identity)
                    background: Controls.ItemSurface {
                        theme: root.theme
                        selected: typeRow.modelData.identity === root.controller.identity
                        hovered: typeRow.hovered
                        pressed: typeRow.down
                        accent: typeRow.modelData.color || root.theme.action
                        railVisible: true
                        normalColor: root.theme.surfaceContainer
                        selectedColor: root.theme.selected
                        cornerRadius: root.theme.itemRadius
                        separatorVisible: false
                        borderWidth: typeRow.visualFocus ? 1 : 0
                        borderColor: root.theme.action
                    }
                    contentItem: RowLayout {
                        spacing: 8
                        Controls.MaterialIcon {
                            name: typeRow.modelData.linkTable ? "link" : "sobject"
                            size: 22
                            color: typeRow.modelData.color || root.theme.action
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            Layout.minimumWidth: 0
                            spacing: 4
                            Label {
                                Layout.fillWidth: true
                                text: typeRow.modelData.label
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.body
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }
                            Label {
                                Layout.fillWidth: true
                                text: typeRow.modelData.identity
                                color: root.theme.secondaryText
                                font.pointSize: Controls.Typography.label
                                elide: Text.ElideRight
                            }
                            Label {
                                objectName: "adminSearchTypeRole_" + typeRow.modelData.identity
                                Layout.fillWidth: true
                                visible: !!typeRow.modelData.manyToMany
                                    || (typeRow.modelData.relationships || []).length > 0
                                text: typeRow.modelData.linkTable ? qsTr("Link table · M:N")
                                    : typeRow.modelData.manyToMany ? qsTr("Many-to-many · M:N")
                                    : qsTr("Schema relationships: %1").arg((typeRow.modelData.relationships || []).length)
                                color: typeRow.modelData.identity === root.controller.identity
                                    ? root.theme.selectedText : typeRow.modelData.color || root.theme.action
                                font.pointSize: Controls.Typography.caption
                                elide: Text.ElideRight
                            }
                        }
                        Label {
                            Layout.preferredWidth: 64
                            visible: !root.compactCatalog
                            text: typeRow.modelData.table || ""
                            color: root.theme.secondaryText
                            font.pointSize: Controls.Typography.label
                            elide: Text.ElideRight
                        }
                    }
                }
                Controls.EmptyState {
                    anchors.centerIn: parent
                    width: parent.width
                    theme: root.theme
                    visible: typeList.count === 0
                    iconName: "search"
                    title: qsTr("No Search Types found")
                }
                ScrollBar.vertical: Controls.ScrollBar { id: typeBar; theme: root.theme; flickableTarget: typeList }
            }
        }
        ColumnLayout {
            id: editorColumn
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumWidth: 0
            spacing: 12
            Controls.SegmentedButton {
                Layout.fillWidth: true
                theme: root.theme
                iconOnly: root.compactEditor
                currentValue: root.page
                model: root.creationOnly ? [
                    {value: "entity_details", label: "1. Details", icon: "edit"},
                    {value: "entity_fields", label: "2. Fields", icon: "view_list"},
                    {value: "entity_review", label: "3. Review", icon: "check"}
                ] : (root.creatingType ? [] : [
                    {value: "entity_summary", label: "Summary", icon: "info"},
                    {value: "entity_workflows", label: "Workflow", icon: "workflow"},
                    {value: "entity_naming", label: "Naming", icon: "drive_file_rename_outline"}
                ]).concat([
                    {value: "entity_details", label: "Details", icon: "edit"},
                    {value: "entity_fields", label: "Fields", icon: "view_list"}
                ])
                onActivated: value => {
                    if (root.creationOnly) {
                        root.wizardPage(value)
                        return
                    }
                    if (value === "entity_naming" && (!root.namingController
                        || !root.namingController.begin_search_type(root.projectCode,
                            root.controller.identity, root.controller.document.title || root.controller.identity)))
                        return
                    root.page = value
                    formScroll.contentY = 0
                }
            }
            ColumnLayout {
                Layout.fillWidth: true
                visible: root.page === "entity_workflows" && !root.creationOnly
                    && !!root.controller.identity
                spacing: 4
                Controls.Button {
                    objectName: "adminCreateTypeWorkflow"
                    Layout.alignment: Qt.AlignLeft
                    theme: root.theme
                    text: qsTr("Create workflow")
                    icon.name: "workflow"
                    enabled: !!root.controller.identity && root.controller.canWrite
                        && !root.controller.busy && !root.namingLocked
                        && (!root.creationOnly || !root.controller.dirty)
                    onClicked: root.createWorkflowRequested()
                }
            }
            Loader {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: root.namingPage
                active: visible
                sourceComponent: NamingEditorView { theme: root.theme; embedded: true }
            }
            Flickable {
                visible: !root.namingPage
                id: formScroll
                objectName: "adminSearchTypeForm"
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                contentWidth: width
                contentHeight: form.implicitHeight
                boundsBehavior: Flickable.StopAtBounds
                ColumnLayout {
                    id: form
                    width: Math.max(0, formScroll.width - formBar.reservedExtent - 4)
                    readonly property real fieldWidth: Math.max(100, Math.min(320, width - 48))
                    spacing: 16
                    enabled: root.controller.canWrite && Object.keys(root.controller.document).length > 0

                    Label {
                        objectName: "adminSearchTypeMissingTable"
                        Layout.fillWidth: true
                        visible: root.controller.metadata.tableAvailable === false
                        text: qsTr("This Search Type is registered, but its database table (%1.%2) is absent. Fields and Search Objects cannot be loaded. Editing is disabled; no table will be created automatically.")
                            .arg(root.controller.metadata.database || "—").arg(root.controller.metadata.table || "—")
                        textFormat: Text.PlainText
                        color: root.theme.error
                        font.pointSize: Controls.Typography.body
                        wrapMode: Text.Wrap
                    }
                    AdminSearchTypeSummary {
                        Layout.fillWidth: true
                        visible: root.page === "entity_summary" && !!root.controller.identity
                        theme: root.theme
                        controller: root.controller
                    }
                    AdminSearchTypeWorkflows {
                        Layout.fillWidth: true
                        visible: root.page === "entity_workflows" && !!root.controller.identity
                        theme: root.theme
                        metadata: root.controller.metadata
                        onOpenRequested: identity => root.openWorkflowRequested(identity)
                    }

                    ConfigurationSection {
                        Layout.fillWidth: true
                        visible: root.page === "entity_details"
                        theme: root.theme
                        title: root.controller.document.title || qsTr("New Search Type")
                        description: qsTr("How this Search Type appears in navigation and Search Object lists.")
                        Controls.SettingsRow {
                            theme: root.theme
                            title: qsTr("Title")
                            description: qsTr("A recognizable name for users.")
                            Controls.TextField {
                                objectName: "adminSearchTypeTitle"
                                Layout.preferredWidth: form.fieldWidth
                                theme: root.theme
                                text: root.controller.document.title || ""
                                onTextEdited: root.controller.set_field("title", text)
                            }
                        }
                        Controls.SettingsRow {
                            theme: root.theme
                            title: qsTr("Description")
                            description: qsTr("Explain what these Search Objects represent.")
                            Controls.TextField {
                                objectName: "adminSearchTypeDescription"
                                Layout.preferredWidth: form.fieldWidth
                                theme: root.theme
                                text: root.controller.document.description || ""
                                onTextEdited: root.controller.set_field("description", text)
                            }
                        }
                        Controls.SettingsRow {
                            theme: root.theme
                            title: qsTr("Accent color")
                            description: qsTr("Used in lists and the project schema. Reset to use the theme color.")
                            showDivider: !root.controller.identity
                            Controls.ColorField {
                                objectName: "adminSearchTypeColor"
                                Layout.preferredWidth: Math.max(100, form.fieldWidth - 44)
                                theme: root.theme
                                value: root.controller.document.color || ""
                                onColorChosen: value => root.controller.set_field("color", value)
                            }
                            Controls.Button {
                                objectName: "adminSearchTypeResetColor"
                                theme: root.theme
                                compact: true
                                text: qsTr("Reset color")
                                icon.name: "restart-alt"
                                enabled: !!root.controller.document.color
                                onClicked: root.controller.set_field("color", "")
                            }
                        }
                        Controls.SettingsRow {
                            visible: !root.controller.identity
                            theme: root.theme
                            title: qsTr("Objects use a pipeline")
                            description: qsTr("Allow processes and tasks for this Search Type.")
                            showDivider: false
                            Controls.CheckBox {
                                objectName: "adminSearchTypeHasPipeline"
                                theme: root.theme
                                Accessible.name: qsTr("Objects use a pipeline")
                                checked: !!root.controller.document.hasPipeline
                                onToggled: root.controller.set_field("hasPipeline", checked)
                            }
                        }
                    }
                    AdminSearchTypePreview {
                        Layout.fillWidth: true
                        visible: root.page === "entity_details" && (!!root.controller.identity || root.creatingType)
                        theme: root.theme
                        controller: root.controller
                    }
                    AdminSearchTypeFields {
                        id: typeFields
                        Layout.fillWidth: true
                        visible: root.page === "entity_fields"
                        theme: root.theme
                        controller: root.controller
                    }
                    ConfigurationSection {
                        objectName: "adminSearchTypeCreationReview"
                        Layout.fillWidth: true
                        visible: root.creationOnly && root.page === "entity_review"
                        theme: root.theme
                        title: qsTr("Ready to create")
                        description: qsTr("This is how the new Search Type will appear. Nothing has been created on the server yet.")
                        Item {
                            id: creationCard
                            Layout.fillWidth: true
                            readonly property bool compact: width < 520
                            implicitHeight: creationCardLayout.implicitHeight + 32

                            Controls.ItemSurface {
                                anchors.fill: parent
                                theme: root.theme
                                accent: root.controller.document.color || root.theme.action
                                railVisible: true
                                railWidth: 4
                                railTopMargin: 12
                                railBottomMargin: 12
                                normalColor: root.theme.surfaceContainer
                                cornerRadius: root.theme.itemRadius
                                borderWidth: 1
                                borderColor: root.theme.outlineVariant
                                separatorVisible: false
                                elevated: true
                                animateStateChanges: false
                            }
                            GridLayout {
                                id: creationCardLayout
                                anchors.fill: parent
                                anchors.margins: 16
                                columns: creationCard.compact ? 1 : 2
                                columnSpacing: 20
                                rowSpacing: 14

                                Controls.ItemPreview {
                                    objectName: "adminSearchTypeCreationPreview"
                                    Layout.preferredWidth: creationCard.compact ? 144 : 184
                                    Layout.preferredHeight: creationCard.compact ? 144 : 184
                                    Layout.alignment: creationCard.compact ? Qt.AlignHCenter : Qt.AlignTop
                                    theme: root.theme
                                    previewSize: 184
                                    decodeAtItemSize: true
                                    cornerRadius: root.theme.sectionRadius
                                    outlined: true
                                    effectsEnabled: false
                                    animateAppearance: false
                                    accent: root.controller.document.color || root.theme.action
                                    source: root.controller.previewUrl
                                    fallbackIcon: "sobject"
                                    fallbackText: (root.controller.document.title || "").slice(0, 2)
                                }
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    Layout.minimumWidth: 0
                                    Layout.alignment: Qt.AlignVCenter
                                    spacing: 10
                                    Label {
                                        objectName: "adminSearchTypeCreationTitle"
                                        Layout.fillWidth: true
                                        text: root.controller.document.title || qsTr("New Search Type")
                                        color: root.controller.document.color || root.theme.action
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Controls.Typography.bodyLarge * 1.45
                                        font.weight: Font.DemiBold
                                        wrapMode: Text.WordWrap
                                    }
                                    Label {
                                        objectName: "adminSearchTypeCreationDescription"
                                        Layout.fillWidth: true
                                        text: root.controller.document.description || qsTr("No description")
                                        color: root.theme.secondaryText
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Controls.Typography.body
                                        wrapMode: Text.WordWrap
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 8
                                        Controls.MaterialIcon {
                                            name: root.controller.document.hasPipeline ? "workflow" : "sobject"
                                            size: 18
                                            color: root.controller.document.color || root.theme.action
                                        }
                                        Label {
                                            objectName: "adminSearchTypeCreationWorkflow"
                                            Layout.fillWidth: true
                                            text: root.controller.document.hasPipeline
                                                ? qsTr("Processes and tasks are enabled")
                                                : qsTr("Search Objects without a workflow")
                                            color: root.theme.primaryText
                                            font.family: root.theme.fontFamily
                                            font.pointSize: Controls.Typography.label
                                            wrapMode: Text.WordWrap
                                        }
                                    }
                                    Label {
                                        Layout.fillWidth: true
                                        visible: !!root.controller.document.previewPath
                                        text: qsTr("The selected preview will be added through Commit Queue after creation.")
                                        color: root.theme.secondaryText
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Controls.Typography.caption
                                        wrapMode: Text.WordWrap
                                    }
                                }
                            }
                        }
                        Controls.SettingsRow {
                            objectName: "adminSearchTypeCreationStandardFields"
                            theme: root.theme
                            title: qsTr("Standard fields")
                            description: typeFields.automaticFields.join(", ")
                                + (root.controller.document.hasPipeline ? ", pipeline_code" : "")
                        }
                        Controls.SettingsRow {
                            objectName: "adminSearchTypeCreationAdditionalFields"
                            theme: root.theme
                            title: qsTr("Additional fields")
                            description: (root.controller.document.columns || [])
                                .map(row => row.name + " (" + row.type + ")").join(", ") || qsTr("No additional fields")
                            showDivider: false
                        }
                    }
                }
                ScrollBar.vertical: Controls.ScrollBar { id: formBar; theme: root.theme; flickableTarget: formScroll }
            }
            RowLayout {
                Layout.fillWidth: true
                visible: root.creationOnly && !root.controller.identity
                Controls.Button {
                    objectName: "adminTypeWizardBack"
                    theme: root.theme
                    text: qsTr("Back")
                    icon.name: "chevron-left"
                    visible: root.page !== "entity_details"
                    enabled: !root.controller.busy
                    onClicked: root.wizardPage(root.page === "entity_review" ? "entity_fields" : "entity_details")
                }
                Item { Layout.fillWidth: true }
                Controls.Button {
                    objectName: "adminTypeWizardNext"
                    theme: root.theme
                    text: qsTr("Next")
                    icon.name: "arrow-forward"
                    visible: root.page !== "entity_review"
                    enabled: !root.controller.busy
                    onClicked: root.wizardPage(root.page === "entity_details" ? "entity_fields" : "entity_review")
                }
            }
        }
    }
}

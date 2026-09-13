import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    required property var controller
    required property int selectedRow
    required property var selectedColumn
    required property int modelRevision
    property string target: "definition"
    property string editorMode: "simple"
    property var formData: ({})
    property string xmlText: ""
    signal targetRequested(string value)

    readonly property bool editTarget: target === "edit_definition"

    function optionIndex(options, value) {
        for (let index = 0; index < options.length; ++index) {
            if (String(options[index].value || "") === String(value || ""))
                return index
        }
        return -1
    }

    function reload() {
        const revision = modelRevision
        if (selectedRow < 0) {
            formData = ({})
            xmlText = ""
            return
        }
        formData = controller.element_form(selectedRow, target)
        xmlText = controller.element_xml(selectedRow, target)
    }

    onSelectedRowChanged: reload()
    onTargetChanged: reload()
    onModelRevisionChanged: reload()
    Component.onCompleted: reload()

    ColumnLayout {
        anchors.fill: parent
        spacing: 8

        RowLayout {
            Layout.fillWidth: true
            Label {
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                text: qsTr("ELEMENT DEFINITION")
                color: root.theme.secondaryText
                font.pointSize: Controls.Typography.label
                font.weight: Font.DemiBold
            }
            Controls.SegmentedButton {
                theme: root.theme
                currentValue: root.target
                segmentWidth: 112
                model: [
                    {value: "definition", label: "Table", icon: "table-view"},
                    {value: "edit_definition", label: "EditSObject", icon: "edit"}
                ]
                onActivated: value => root.targetRequested(value)
            }
        }

        Label {
            Layout.fillWidth: true
            text: String(root.selectedColumn.name || qsTr("Select a field"))
            color: root.theme.primaryText
            font.pixelSize: 14
            font.weight: Font.DemiBold
            elide: Text.ElideMiddle
        }

        Loader {
            Layout.fillWidth: true
            Layout.fillHeight: true
            sourceComponent: root.editorMode === "xml"
                ? xmlEditor : simpleEditor
        }
    }

    Component {
        id: simpleEditor

        Flickable {
            id: simpleViewport
            objectName: "tacticDefinitionSimpleEditor"
            clip: true
            contentWidth: width
            contentHeight: simpleSections.implicitHeight
            boundsBehavior: Flickable.StopAtBounds

            ColumnLayout {
                id: simpleSections
                width: Math.max(
                    0, simpleViewport.width
                        - simpleScrollBar.reservedExtent - 4
                )
                spacing: 12

                ConfigurationSection {
                    Layout.fillWidth: true
                    visible: !root.editTarget
                    theme: root.theme
                    title: qsTr("Table display")
                    description: qsTr("Configure how this field appears in the table. Column membership and order remain in the table view.")

                    Controls.SettingsRow {
                        theme: root.theme
                        title: qsTr("Title")
                        description: qsTr("The column heading shown to users.")
                        Controls.TextField {
                            id: titleField
                            objectName: "tacticDefinitionTitle"
                            Layout.preferredWidth: 230
                            theme: root.theme
                            text: String(root.formData.title || "")
                        }
                    }
                    Controls.SettingsRow {
                        theme: root.theme
                        title: qsTr("Width")
                        description: qsTr("Default width in the table view.")
                        Controls.SpinBox {
                            id: widthField
                            objectName: "tacticDefinitionWidth"
                            Layout.preferredWidth: 150
                            theme: root.theme
                            from: 48
                            to: 640
                            stepSize: 8
                            editable: true
                            value: Number(root.formData.width || 160)
                        }
                    }
                    Controls.SettingsRow {
                        theme: root.theme
                        title: qsTr("Display widget")
                        description: qsTr("Choose a supported TACTIC table widget.")
                        showDivider: false
                        Controls.ComboBox {
                            id: displayWidget
                            objectName: "tacticDisplayWidget"
                            Layout.preferredWidth: 230
                            theme: root.theme
                            model: root.controller.displayWidgetOptions
                            textRole: "label"
                            valueRole: "value"
                            translateDisplayText: false
                            currentIndex: root.optionIndex(
                                model, root.formData.widget
                            )
                        }
                    }
                }

                ConfigurationSection {
                    Layout.fillWidth: true
                    visible: root.editTarget
                    theme: root.theme
                    title: qsTr("EditSObject field")
                    description: qsTr("The same native input definition is used by EditSObject and inline table editing.")

                    Controls.SettingsRow {
                        theme: root.theme
                        title: qsTr("Show in EditSObject")
                        description: qsTr("Include this field in view=edit without changing its definition.")
                        Controls.Switch {
                            id: includedField
                            objectName: "tacticEditIncluded"
                            theme: root.theme
                            checked: Boolean(root.formData.included)
                            Accessible.name: qsTr("Show in EditSObject")
                        }
                    }
                    Controls.SettingsRow {
                        theme: root.theme
                        title: qsTr("Input widget")
                        description: qsTr("Choose the TACTIC widget used to edit this field.")
                        Controls.ComboBox {
                            id: inputWidget
                            objectName: "tacticInputWidget"
                            Layout.preferredWidth: 230
                            theme: root.theme
                            model: root.controller.inputWidgetOptions
                            textRole: "label"
                            valueRole: "value"
                            translateDisplayText: false
                            currentIndex: root.optionIndex(
                                model, root.formData.widget
                            )
                        }
                    }
                    Controls.SettingsRow {
                        theme: root.theme
                        title: qsTr("Required")
                        description: qsTr("Reject an empty value in EditSObject.")
                        Controls.Switch {
                            id: requiredField
                            objectName: "tacticEditRequired"
                            theme: root.theme
                            checked: Boolean(root.formData.required)
                            Accessible.name: qsTr("Required")
                        }
                    }
                    Controls.SettingsRow {
                        theme: root.theme
                        title: qsTr("Read only")
                        description: qsTr("Show the value without allowing changes.")
                        Controls.Switch {
                            id: readOnlyField
                            objectName: "tacticEditReadOnly"
                            theme: root.theme
                            checked: Boolean(root.formData.readOnly)
                            Accessible.name: qsTr("Read only")
                        }
                    }
                    Controls.SettingsRow {
                        theme: root.theme
                        title: qsTr("Allow empty choice")
                        description: qsTr("Add an empty entry to Select widgets.")
                        visible: String(inputWidget.currentValue || "")
                            .endsWith("SelectWdg")
                        Controls.Switch {
                            id: emptyField
                            objectName: "tacticEditEmpty"
                            theme: root.theme
                            checked: Boolean(root.formData.empty)
                            Accessible.name: qsTr("Allow empty choice")
                        }
                    }
                    Controls.SettingsRow {
                        theme: root.theme
                        title: qsTr("Description")
                        description: qsTr("Help text displayed with the field.")
                        Controls.TextField {
                            id: descriptionField
                            objectName: "tacticEditDescription"
                            Layout.preferredWidth: 230
                            theme: root.theme
                            text: String(root.formData.description || "")
                        }
                    }
                    Controls.SettingsRow {
                        theme: root.theme
                        title: qsTr("Default value")
                        description: qsTr("Initial value for a new object.")
                        Controls.TextField {
                            id: defaultField
                            objectName: "tacticEditDefault"
                            Layout.preferredWidth: 230
                            theme: root.theme
                            text: String(root.formData.defaultValue || "")
                        }
                    }
                    Controls.SettingsRow {
                        theme: root.theme
                        title: qsTr("Values")
                        description: qsTr("Select values separated by |.")
                        visible: String(inputWidget.currentValue || "")
                            .endsWith("SelectWdg")
                        Controls.TextField {
                            id: valuesField
                            objectName: "tacticEditValues"
                            Layout.preferredWidth: 230
                            theme: root.theme
                            text: String(root.formData.values || "")
                        }
                    }
                    Controls.SettingsRow {
                        theme: root.theme
                        title: qsTr("Labels")
                        description: qsTr("Optional labels separated by | in the same order.")
                        visible: String(inputWidget.currentValue || "")
                            .endsWith("SelectWdg")
                        showDivider: false
                        Controls.TextField {
                            id: labelsField
                            objectName: "tacticEditLabels"
                            Layout.preferredWidth: 230
                            theme: root.theme
                            text: String(root.formData.labels || "")
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.bottomMargin: 4
                    Label {
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        text: root.editTarget
                            ? qsTr("Saves view=edit_definition and view=edit")
                            : qsTr("Saves view=definition")
                        color: root.theme.secondaryText
                        wrapMode: Text.WordWrap
                        font.pointSize: Controls.Typography.label
                    }
                    Controls.Button {
                        objectName: "tacticSaveSimpleDefinition"
                        theme: root.theme
                        text: qsTr("SAVE")
                        highlighted: true
                        enabled: root.selectedRow >= 0
                        onClicked: {
                            const widgetControl = root.editTarget
                                ? inputWidget : displayWidget
                            const selectedWidget = widgetControl.currentIndex >= 0
                                ? widgetControl.currentValue
                                : root.formData.widget
                            root.controller.save_element_visual(
                                root.selectedRow,
                                root.target,
                                {
                                    title: titleField.text,
                                    width: widthField.value,
                                    widget: selectedWidget,
                                    included: includedField.checked,
                                    required: requiredField.checked,
                                    readOnly: readOnlyField.checked,
                                    empty: emptyField.checked,
                                    description: descriptionField.text,
                                    defaultValue: defaultField.text,
                                    values: valuesField.text,
                                    labels: labelsField.text
                                }
                            )
                        }
                    }
                }
            }
            ScrollBar.vertical: Controls.ScrollBar {
                id: simpleScrollBar
                theme: root.theme
                flickableTarget: simpleViewport
            }
        }
    }

    Component {
        id: xmlEditor

        ColumnLayout {
            objectName: "tacticDefinitionXmlEditor"
            spacing: 8

            Label {
                Layout.fillWidth: true
                text: qsTr("Technical XML preserves unknown, nested and custom widget options.")
                color: root.theme.secondaryText
                wrapMode: Text.WordWrap
                font.pointSize: Controls.Typography.label
            }
            Flickable {
                id: xmlViewport
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                contentWidth: width
                contentHeight: definitionXml.implicitHeight
                boundsBehavior: Flickable.StopAtBounds

                Controls.TextArea {
                    id: definitionXml
                    objectName: "tacticElementDefinitionXml"
                    width: Math.max(
                        0, xmlViewport.width - xmlScrollBar.reservedExtent - 4
                    )
                    height: Math.max(xmlViewport.height, implicitHeight)
                    theme: root.theme
                    enabled: root.selectedRow >= 0
                    text: root.xmlText
                    wrapMode: TextEdit.Wrap
                    font.family: "Consolas"
                }
                ScrollBar.vertical: Controls.ScrollBar {
                    id: xmlScrollBar
                    theme: root.theme
                    flickableTarget: xmlViewport
                }
            }
            RowLayout {
                Layout.fillWidth: true
                Label {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    text: root.editTarget
                        ? qsTr("Saves view=edit_definition and preserves view=edit membership")
                        : qsTr("Saves view=definition")
                    color: root.theme.secondaryText
                    wrapMode: Text.WordWrap
                    font.pointSize: Controls.Typography.label
                }
                Controls.Button {
                    objectName: "tacticSaveXmlDefinition"
                    theme: root.theme
                    text: qsTr("SAVE XML")
                    highlighted: true
                    enabled: root.selectedRow >= 0
                    onClicked: root.controller.save_element_xml(
                        root.selectedRow, root.target, definitionXml.text
                    )
                }
            }
        }
    }
}

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    required property var theme
    required property string windowId
    property int page: 0
    property string presetAction: "save"

    function columnIndex(value) {
        for (let row = 0; row < filterColumnModel.count(); ++row) {
            if (filterColumnModel.get(row).value === value)
                return row
        }
        return -1
    }

    function openPresetDialog(action) {
        presetAction = action
        presetName.text = action === "rename"
            ? filterEditorController.tab_title
            : action === "duplicate"
                ? filterEditorController.tab_title + " copy"
                : filterEditorController.tab_title
        presetDialog.open()
        presetName.forceActiveFocus()
        presetName.selectAll()
    }

    Rectangle {
        anchors.fill: parent
        color: root.theme.workspace
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 120
            color: root.theme.surfaceContainerLow

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 14
                spacing: 9

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Rectangle {
                        Layout.preferredWidth: 38
                        Layout.preferredHeight: 38
                        radius: 12
                        color: root.theme.secondaryContainer
                        MaterialIcon {
                            anchors.centerIn: parent
                            name: "filter_alt"
                            size: 19
                            color: root.theme.action
                        }
                    }
                    Md3ComboBox {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 38
                        theme: root.theme
                        model: filterPresetModel
                        textRole: "title"
                        currentIndex: filterEditorController.selected_preset
                        enabled: !filterEditorController.busy
                        displayText: currentIndex >= 0
                            ? currentText : "Saved filters"
                        onActivated:
                            filterEditorController.select_preset(currentIndex)
                    }
                    BusyIndicator {
                        Layout.preferredWidth: 28
                        Layout.preferredHeight: 28
                        running: filterEditorController.busy
                        visible: running
                    }
                    CompactIconButton {
                        theme: root.theme
                        iconName: "save"
                        toolTip: qsTr("Update selected preset")
                        enabled: filterEditorController.selected_preset >= 0
                            && !filterEditorController.busy
                        onClicked: filterEditorController.update_selected()
                    }
                    CompactIconButton {
                        theme: root.theme
                        iconName: "add"
                        toolTip: qsTr("Save as new preset")
                        enabled: !filterEditorController.busy
                        onClicked: root.openPresetDialog("save")
                    }
                    CompactIconButton {
                        theme: root.theme
                        iconName: "drive_file_rename_outline"
                        toolTip: qsTr("Rename preset")
                        enabled: filterEditorController.selected_preset >= 0
                            && !filterEditorController.busy
                        onClicked: root.openPresetDialog("rename")
                    }
                    CompactIconButton {
                        theme: root.theme
                        iconName: "content_copy"
                        toolTip: qsTr("Duplicate preset")
                        enabled: filterEditorController.selected_preset >= 0
                            && !filterEditorController.busy
                        onClicked: root.openPresetDialog("duplicate")
                    }
                    CompactIconButton {
                        theme: root.theme
                        iconName: "delete"
                        toolTip: qsTr("Delete preset")
                        enabled: filterEditorController.selected_preset >= 0
                            && !filterEditorController.busy
                        onClicked: deleteDialog.open()
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 6

                    Repeater {
                        model: ["Conditions", "Processes", "Search options"]
                        Md3Button {
                            theme: root.theme
                            required property int index
                            required property string modelData
                            text: modelData
                            flat: root.page !== index
                            highlighted: root.page === index
                            onClicked: root.page = index
                        }
                    }
                    Item { Layout.fillWidth: true }
                    Md3Button {
                        theme: root.theme
                        visible: root.page === 0
                        text: qsTr("Add condition")
                        icon.name: "add"
                        onClicked: filterEditorController.add_condition()
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: root.theme.outlineVariant
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: root.page

            ListView {
                id: conditionList
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.margins: 14
                clip: true
                spacing: 9
                model: filterEditorModel
                boundsBehavior: Flickable.StopAtBounds

                delegate: Rectangle {
                    id: conditionRow

                    required property int index
                    required property string column
                    required property var relation
                    required property var value
                    required property bool rowEnabled
                    required property string operator
                    required property bool isDefault
                    required property string dataType

                    readonly property var relationChoices:
                        filterEditorController.relations(column)
                    readonly property bool numericScalar:
                        ["integer", "float", "currency"].indexOf(dataType) >= 0
                        && relation !== "in" && relation !== "not in"
                    readonly property bool dateScalar:
                        ["date", "timestamp", "datetime", "datetime2"].indexOf(
                            dataType
                        ) >= 0
                        && relation !== null
                        && relation !== "in" && relation !== "not in"

                    function relationIndex(value) {
                        for (let row = 0; row < relationChoices.length; ++row) {
                            if (relationChoices[row].value === value)
                                return row
                        }
                        return -1
                    }

                    width: conditionList.width
                    height: 132
                    radius: 16
                    color: root.theme.surfaceContainerLow
                    border.width: 1
                    border.color: root.theme.outlineVariant
                    opacity: rowEnabled ? 1 : 0.62

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 7

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Md3CheckBox {
                                theme: root.theme
                                checked: conditionRow.rowEnabled
                                onToggled: filterEditorController.set_value(
                                    conditionRow.index, "rowEnabled", checked
                                )
                            }
                            Rectangle {
                                Layout.preferredWidth:
                                    conditionRow.isDefault ? 62 : 72
                                Layout.preferredHeight: 30
                                radius: 15
                                color: root.theme.secondaryContainer
                                Label {
                                    anchors.centerIn: parent
                                    text: conditionRow.isDefault
                                        ? "WHERE"
                                        : conditionRow.operator.toUpperCase()
                                    color: root.theme.action
                                    font.family: root.theme.fontFamily
                                    font.pixelSize: 9
                                    font.weight: Font.Bold
                                }
                                MouseArea {
                                    anchors.fill: parent
                                    enabled: !conditionRow.isDefault
                                    cursorShape: enabled
                                        ? Qt.PointingHandCursor : Qt.ArrowCursor
                                    onClicked:
                                        filterEditorController.set_value(
                                            conditionRow.index,
                                            "operator",
                                            conditionRow.operator === "or"
                                                ? "and" : "or"
                                        )
                                }
                            }
                            Label {
                                Layout.fillWidth: true
                                text: conditionRow.dataType.replace("_", " ")
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pixelSize: 9
                                horizontalAlignment: Text.AlignRight
                            }
                            CompactIconButton {
                                theme: root.theme
                                iconName: "close"
                                round: true
                                enabled: filterEditorModel.count() > 1
                                toolTip: qsTr("Remove condition")
                                onClicked:
                                    filterEditorController.remove_condition(
                                        conditionRow.index
                                    )
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 7

                            Md3ComboBox {
                                Layout.fillWidth: true
                                Layout.minimumWidth: 130
                                Layout.preferredHeight: 34
                                theme: root.theme
                                enabled: conditionRow.rowEnabled
                                model: filterColumnModel
                                textRole: "label"
                                valueRole: "value"
                                currentIndex: root.columnIndex(
                                    conditionRow.column
                                )
                                onActivated:
                                    filterEditorController.set_column(
                                        conditionRow.index, currentValue
                                    )
                            }
                            Md3ComboBox {
                                Layout.fillWidth: true
                                Layout.minimumWidth: 112
                                Layout.preferredHeight: 34
                                theme: root.theme
                                enabled: conditionRow.rowEnabled
                                model: conditionRow.relationChoices
                                textRole: "label"
                                valueRole: "value"
                                currentIndex: conditionRow.relationIndex(
                                    conditionRow.relation
                                )
                                onActivated: {
                                    filterEditorController.set_value(
                                        conditionRow.index,
                                        "relation",
                                        currentValue
                                    )
                                    if (currentValue === null)
                                        filterEditorController.set_value(
                                            conditionRow.index, "value", ""
                                        )
                                }
                            }
                            Loader {
                                Layout.fillWidth: true
                                Layout.minimumWidth: 120
                                Layout.preferredHeight: 34
                                sourceComponent:
                                    conditionRow.dataType === "boolean"
                                    && conditionRow.relation !== null
                                    ? booleanEditor
                                    : conditionRow.dateScalar
                                        ? dateEditor : valueEditor
                            }
                        }
                    }

                    Component {
                        id: booleanEditor
                        Md3ComboBox {
                            theme: root.theme
                            enabled: conditionRow.rowEnabled
                            model: ["true", "false"]
                            currentIndex:
                                String(conditionRow.value).toLowerCase()
                                === "false" ? 1 : 0
                            onActivated: filterEditorController.set_value(
                                conditionRow.index, "value", currentText
                            )
                        }
                    }
                    Component {
                        id: dateEditor
                        Md3DateField {
                            theme: root.theme
                            enabled: conditionRow.rowEnabled
                            includeTime: conditionRow.dataType !== "date"
                            text: conditionRow.value === null
                                || conditionRow.value === undefined
                                ? "" : String(conditionRow.value)
                            placeholderText: includeTime
                                ? qsTr("Date and time") : qsTr("Date")
                            onAccepted: value => filterEditorController.set_value(
                                conditionRow.index, "value", value
                            )
                            onTextEdited: filterEditorController.set_value(
                                conditionRow.index, "value", text
                            )
                        }
                    }
                    Component {
                        id: valueEditor
                        Md3TextField {
                            theme: root.theme
                            id: typedValue
                            enabled: conditionRow.rowEnabled
                                && conditionRow.relation !== null
                            text: conditionRow.value === null
                                || conditionRow.value === undefined
                                ? "" : String(conditionRow.value)
                            placeholderText:
                                conditionRow.relation === null ? qsTr("No value")
                                : conditionRow.dataType === "_expression"
                                    ? qsTr("TACTIC expression")
                                : ["time", "timestamp", "datetime2"].indexOf(
                                    conditionRow.dataType
                                ) >= 0 ? qsTr("YYYY-MM-DD")
                                : conditionRow.numericScalar ? qsTr("Number")
                                : conditionRow.relation === "in"
                                    || conditionRow.relation === "not in"
                                    ? qsTr("Comma-separated values") : qsTr("Value")
                            color: root.theme.primaryText
                            placeholderTextColor: root.theme.secondaryText
                            selectionColor: root.theme.action
                            validator: conditionRow.numericScalar
                                ? numberValidator : null
                            DoubleValidator {
                                id: numberValidator
                                notation: DoubleValidator.StandardNotation
                            }
                            onTextEdited:
                                filterEditorController.set_value(
                                    conditionRow.index, "value", text
                                )
                            background: Rectangle {
                                radius: 10
                                color: root.theme.surfaceContainerHigh
                                border.width: typedValue.activeFocus ? 2 : 1
                                border.color: typedValue.activeFocus
                                    ? root.theme.action : root.theme.outline
                            }
                        }
                    }
                }

                ScrollBar.vertical: Md3ScrollBar {
                    theme: root.theme
                    flickableTarget: conditionList
                }
            }

            ColumnLayout {
                Layout.margins: 18
                spacing: 10

                RowLayout {
                    Layout.fillWidth: true
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("Visible workspace branches")
                        color: root.theme.primaryText
                        font.pixelSize: 15
                        font.weight: Font.DemiBold
                    }
                    Md3Button {
                        theme: root.theme
                        text: qsTr("All")
                        flat: true
                        onClicked:
                            filterEditorController.toggle_process_kind("all")
                    }
                    Md3Button {
                        theme: root.theme
                        text: qsTr("Processes")
                        flat: true
                        onClicked:
                            filterEditorController.toggle_process_kind("process")
                    }
                    Md3Button {
                        theme: root.theme
                        text: qsTr("Builtins")
                        flat: true
                        onClicked:
                            filterEditorController.toggle_process_kind("builtin")
                    }
                    Md3Button {
                        theme: root.theme
                        text: qsTr("Children")
                        flat: true
                        onClicked:
                            filterEditorController.toggle_process_kind("child")
                    }
                }

                ListView {
                    id: processList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 5
                    model: filterProcessModel
                    delegate: Rectangle {
                        required property int index
                        required property string title
                        required property string kind
                        required property string group
                        required property int depth
                        required property bool itemEnabled

                        width: processList.width
                        height: 42
                        radius: 12
                        color: root.theme.surfaceContainerLow
                        border.width: 1
                        border.color: root.theme.outlineVariant
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 12 + depth * 18
                            anchors.rightMargin: 12
                            spacing: 9
                            Md3CheckBox {
                                theme: root.theme
                                checked: itemEnabled
                                onToggled:
                                    filterEditorController.set_process_enabled(
                                        index, checked
                                    )
                            }
                            MaterialIcon {
                                name: kind === "process" ? "account_tree"
                                    : kind === "child" ? "schema" : "settings"
                                size: 17
                                color: root.theme.action
                            }
                            Label {
                                Layout.fillWidth: true
                                text: title
                                color: root.theme.primaryText
                            }
                            Label {
                                text: group
                                visible: text.length > 0
                                color: root.theme.secondaryText
                                font.pixelSize: 9
                            }
                        }
                    }
                    ScrollBar.vertical: Md3ScrollBar {
                        theme: root.theme
                        flickableTarget: processList
                    }
                }
            }

            ColumnLayout {
                Layout.margins: 24
                spacing: 12
                Item { Layout.fillHeight: true }
                Label {
                    text: qsTr("Search tab title")
                    color: root.theme.primaryText
                    font.pixelSize: 15
                    font.weight: Font.DemiBold
                }
                Md3TextField {
                    theme: root.theme
                    id: tabTitle
                    Layout.fillWidth: true
                    text: filterEditorController.tab_title
                    color: root.theme.primaryText
                    selectionColor: root.theme.action
                    onTextEdited:
                        filterEditorController.set_title(text)
                    background: Rectangle {
                        radius: 12
                        color: root.theme.surfaceContainerHigh
                        border.width: tabTitle.activeFocus ? 2 : 1
                        border.color: tabTitle.activeFocus
                            ? root.theme.action : root.theme.outline
                    }
                }
                Label {
                    Layout.fillWidth: true
                    text: qsTr("The title is applied together with the filter.")
                    color: root.theme.secondaryText
                    wrapMode: Text.WordWrap
                }
                Item { Layout.fillHeight: true }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 72
            color: root.theme.surfaceContainerLow

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                height: 1
                color: root.theme.outlineVariant
            }
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 18
                anchors.rightMargin: 18
                spacing: 10
                Label {
                    Layout.fillWidth: true
                    text: filterEditorController.validation_error.length
                        ? filterEditorController.validation_error
                        : filterEditorController.preset_error
                    visible: text.length > 0
                    color: root.theme.red
                    font.pixelSize: 9
                    wrapMode: Text.WordWrap
                }
                Md3Button {
                    theme: root.theme
                    text: qsTr("Cancel")
                    flat: true
                    onClicked: {
                        filterEditorController.cancel()
                        windowModel.close_window(root.windowId)
                    }
                }
                Md3Button {
                    theme: root.theme
                    text: qsTr("Apply")
                    highlighted: true
                    enabled: filterEditorController.valid
                        && !filterEditorController.busy
                    onClicked: {
                        if (filterEditorController.apply())
                            windowModel.close_window(root.windowId)
                    }
                }
            }
        }
    }

    Md3Dialog {
        id: presetDialog
        theme: root.theme
        anchors.centerIn: parent
        width: 390
        modal: true
        title: root.presetAction === "rename" ? qsTr("Rename preset")
            : root.presetAction === "duplicate" ? qsTr("Duplicate preset")
            : qsTr("Save filter preset")
        onAccepted: {
            if (root.presetAction === "rename")
                filterEditorController.rename(presetName.text)
            else if (root.presetAction === "duplicate")
                filterEditorController.duplicate(presetName.text)
            else
                filterEditorController.save_as(presetName.text)
        }
        contentItem: Md3TextField {
            id: presetName
            theme: root.theme
            width: 342
            placeholderText: qsTr("Preset name")
            color: root.theme.primaryText
            selectionColor: root.theme.action
            background: Rectangle {
                radius: 10
                color: root.theme.surfaceContainerHigh
                border.width: presetName.activeFocus ? 2 : 1
                border.color: presetName.activeFocus
                    ? root.theme.action : root.theme.outline
            }
        }
        footer: DialogButtonBox {
            background: Item {}
            Md3Button {
                theme: root.theme
                text: qsTr("Save")
                highlighted: true
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            }
            Md3Button {
                theme: root.theme
                text: qsTr("Cancel")
                flat: true
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            }
        }
    }

    Md3Dialog {
        id: deleteDialog
        theme: root.theme
        anchors.centerIn: parent
        width: 390
        modal: true
        title: qsTr("Delete saved filter?")
        onAccepted: filterEditorController.delete_selected()
        contentItem: Label {
            width: 342
            text: qsTr("The preset will be removed from the TACTIC server.")
            color: root.theme.primaryText
            wrapMode: Text.WordWrap
        }
        footer: DialogButtonBox {
            background: Item {}
            Md3Button {
                theme: root.theme
                text: qsTr("Delete")
                destructive: true
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            }
            Md3Button {
                theme: root.theme
                text: qsTr("Cancel")
                flat: true
                DialogButtonBox.buttonRole: DialogButtonBox.RejectRole
            }
        }
    }
}

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    required property var theme
    property int selectedRow: -1
    property var selectedColumn: selectedRow >= 0
        ? columnsEditorModel.get(selectedRow) : ({})

    function selectedValue() {
        const nodeId = String(appController.selected_node_id || "")
        const fields = appController.editable_result_field_records(nodeId)
        for (let index = 0; index < fields.length; ++index) {
            if (fields[index].fieldName === selectedColumn.name)
                return String(fields[index].fieldValue || "")
        }
        return ""
    }

    Rectangle { anchors.fill: parent; color: root.theme.panelDeep }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        RowLayout {
            Layout.fillWidth: true
            Label {
                Layout.fillWidth: true
                text: qsTr("Columns · ") + columnsEditorController.title
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 15
                font.weight: Font.DemiBold
            }
            CompactIconButton {
                theme: root.theme
                iconName: "add"
                toolTip: qsTr("Show the first hidden schema column")
                onClicked: {
                    for (let row = 0; row < columnsEditorModel.count(); ++row) {
                        if (!columnsEditorModel.get(row).displayVisible) {
                            columnsEditorController.set_visible(row, true)
                            root.selectedRow = row
                            break
                        }
                    }
                }
            }
            RefreshIconButton {
                theme: root.theme
                toolTip: qsTr("Reload schema columns")
                onClicked: columnsEditorController.reload()
            }
        }

        SplitView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            orientation: Qt.Horizontal

            Rectangle {
                SplitView.fillWidth: true
                SplitView.minimumWidth: 360
                color: root.theme.panel
                radius: 14
                border.width: 1
                border.color: root.theme.border

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 5
                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            Layout.preferredWidth: 28
                            text: ""
                        }
                        Label {
                            Layout.fillWidth: true
                            text: qsTr("DISPLAY COLUMN")
                            color: root.theme.secondaryText
                            font.pixelSize: 9
                            font.weight: Font.DemiBold
                        }
                        Label {
                            Layout.preferredWidth: 82
                            text: qsTr("WIDTH")
                            color: root.theme.secondaryText
                            font.pixelSize: 9
                        }
                        Item { Layout.preferredWidth: 62 }
                    }
                    ListView {
                        id: columnsList
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        model: columnsEditorModel
                        clip: true
                        spacing: 3
                        delegate: Rectangle {
                            id: columnRow
                            required property int index
                            required property string name
                            required property string label
                            required property string dataType
                            required property bool displayVisible
                            required property int displayWidth
                            required property bool readOnly
                            width: columnsList.width
                            height: 46
                            radius: 10
                            color: root.selectedRow === index
                                ? root.theme.selected
                                : rowHover.hovered
                                  ? root.theme.rowHover : root.theme.row
                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 7
                                anchors.rightMargin: 5
                                spacing: 5
                                Md3CheckBox {
                                    theme: root.theme
                                    checked: columnRow.displayVisible
                                    onToggled: columnsEditorController
                                        .set_visible(columnRow.index, checked)
                                }
                                Md3TextField {
                                    theme: root.theme
                                    Layout.fillWidth: true
                                    text: columnRow.label
                                    placeholderText: columnRow.name
                                    onEditingFinished: columnsEditorController
                                        .set_label(columnRow.index, text)
                                }
                                Md3SpinBox {
                                    theme: root.theme
                                    Layout.preferredWidth: 82
                                    from: 48
                                    to: 640
                                    stepSize: 8
                                    editable: true
                                    value: columnRow.displayWidth
                                    onValueModified: columnsEditorController
                                        .set_width(columnRow.index, value)
                                }
                                CompactIconButton {
                                    theme: root.theme
                                    iconName: "arrow_upward"
                                    enabled: columnRow.index > 0
                                    onClicked: {
                                        columnsEditorController.move(
                                            columnRow.index, -1
                                        )
                                        root.selectedRow = columnRow.index - 1
                                    }
                                }
                                CompactIconButton {
                                    theme: root.theme
                                    iconName: "arrow_downward"
                                    enabled: columnRow.index
                                        < columnsEditorModel.count() - 1
                                    onClicked: {
                                        columnsEditorController.move(
                                            columnRow.index, 1
                                        )
                                        root.selectedRow = columnRow.index + 1
                                    }
                                }
                            }
                            HoverHandler {
                                id: rowHover
                                cursorShape: Qt.PointingHandCursor
                            }
                            TapHandler {
                                onTapped: {
                                    root.selectedRow = columnRow.index
                                    columnValue.text = root.selectedValue()
                                }
                            }
                        }
                        ScrollBar.vertical: Md3ScrollBar { theme: root.theme }
                    }
                }
            }

            Rectangle {
                SplitView.preferredWidth: 300
                SplitView.minimumWidth: 250
                color: root.theme.panel
                radius: 14
                border.width: 1
                border.color: root.theme.border

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 9
                    Label {
                        text: qsTr("TACTIC COLUMN")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 9
                        font.weight: Font.DemiBold
                    }
                    Label {
                        Layout.fillWidth: true
                        text: selectedColumn.label || qsTr("Select a column")
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 14
                        font.weight: Font.DemiBold
                        wrapMode: Text.WordWrap
                    }
                    Label {
                        Layout.fillWidth: true
                        text: selectedColumn.name
                            ? selectedColumn.name + " · "
                                + selectedColumn.dataType
                            : ""
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 9
                    }
                    Md3TextArea {
                        id: columnValue
                        theme: root.theme
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        enabled: root.selectedRow >= 0
                            && !selectedColumn.readOnly
                            && appController.selected_result_count === 1
                        placeholderText: appController.selected_result_count === 1
                            ? qsTr("Column value")
                            : qsTr("Select one sObject to edit a value")
                        wrapMode: TextEdit.Wrap
                    }
                    Label {
                        Layout.fillWidth: true
                        visible: selectedColumn.readOnly || false
                        text: qsTr("This schema column is read-only.")
                        color: root.theme.secondaryText
                        font.pixelSize: 9
                    }
                    Md3Button {
                        Layout.alignment: Qt.AlignRight
                        theme: root.theme
                        text: qsTr("SAVE VALUE")
                        highlighted: true
                        enabled: columnValue.enabled
                        onClicked: columnsEditorController.save_column_value(
                            String(selectedColumn.name || ""),
                            columnValue.text
                        )
                    }
                }
            }
        }

        Label {
            Layout.fillWidth: true
            visible: columnsEditorController.error.length > 0
            text: columnsEditorController.error
            color: root.theme.red
            wrapMode: Text.WordWrap
            font.family: root.theme.fontFamily
            font.pixelSize: 9
        }

        RowLayout {
            Layout.fillWidth: true
            Md3Button {
                theme: root.theme
                text: qsTr("RESET")
                onClicked: columnsEditorController.reset()
            }
            Item { Layout.fillWidth: true }
            Md3Button {
                theme: root.theme
                text: qsTr("CANCEL")
                enabled: columnsEditorController.dirty
                onClicked: columnsEditorController.cancel()
            }
            Md3Button {
                theme: root.theme
                text: qsTr("APPLY")
                highlighted: true
                enabled: columnsEditorController.dirty
                onClicked: columnsEditorController.apply()
            }
        }
    }
}

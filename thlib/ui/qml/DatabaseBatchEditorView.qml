import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root
    required property var theme

    Rectangle { anchors.fill: parent; color: root.theme.panelDeep }
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 8

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Controls.MaterialIcon {
                name: "edit"
                size: 18
                color: root.theme.accent
            }
            Label {
                text: appController.selected_result_count > 1
                    ? appController.selected_result_count
                        + qsTr(" compatible objects selected")
                    : qsTr("Selected object")
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 12
                font.weight: Font.DemiBold
            }
            Item { Layout.fillWidth: true }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 32
            color: root.theme.panelRaised
            radius: 4
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 12
                spacing: 10
                Label {
                    text: qsTr("Object")
                    Layout.fillWidth: true
                    color: root.theme.secondaryText
                    font.pointSize: Controls.Typography.label
                    font.weight: Font.DemiBold
                }
                Label {
                    text: qsTr("Code")
                    Layout.preferredWidth: 130
                    color: root.theme.secondaryText
                    font.pointSize: Controls.Typography.label
                    font.weight: Font.DemiBold
                }
                Label {
                    text: qsTr("Status")
                    Layout.preferredWidth: 100
                    color: root.theme.secondaryText
                    font.pointSize: Controls.Typography.label
                    font.weight: Font.DemiBold
                }
            }
        }

        ListView {
            id: selectedRows
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 1
            model: appController.selected_result_records
            delegate: Rectangle {
                required property var modelData
                required property int index
                width: ListView.view ? ListView.view.width : 0
                height: 42
                color: index % 2 ? root.theme.row : root.theme.panelRaised
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 12
                    spacing: 10
                    Label {
                        text: modelData.title || modelData.searchKey
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                        color: root.theme.primaryText
                        font.pointSize: Controls.Typography.body
                    }
                    Label {
                        text: modelData.code || "—"
                        Layout.preferredWidth: 130
                        elide: Text.ElideRight
                        color: root.theme.secondaryText
                        font.pointSize: Controls.Typography.label
                    }
                    Label {
                        text: modelData.status || "—"
                        Layout.preferredWidth: 100
                        elide: Text.ElideRight
                        color: root.theme.secondaryText
                        font.pointSize: Controls.Typography.label
                    }
                }
            }
            ScrollBar.vertical: Controls.ScrollBar { theme: root.theme }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 58
            radius: 8
            color: root.theme.panelRaised
            RowLayout {
                anchors.fill: parent
                anchors.margins: 8
                spacing: 8
                Controls.ComboBox {
                    id: databaseColumn
                    theme: root.theme
                    Layout.preferredWidth: 180
                    model: appController.selected_result_fields
                    enabled: count > 0
                    displayText: currentText || "Column"
                }
                Controls.TextField {
                    id: databaseValue
                    theme: root.theme
                    Layout.fillWidth: true
                    placeholderText: qsTr("Value for every selected item")
                    color: root.theme.primaryText
                    selectByMouse: true
                    onAccepted: databaseApply.clicked()
                }
                Controls.Button {
                    id: databaseApply
                    theme: root.theme
                    text: qsTr("Apply to selected")
                    enabled: databaseColumn.currentText.length > 0
                        && appController.selected_result_count > 0
                    onClicked: appController.update_selected_items(
                        databaseColumn.currentText,
                        databaseValue.text
                    )
                }
            }
        }
    }
}

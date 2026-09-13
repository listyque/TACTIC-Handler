import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    required property string windowId
    readonly property bool compact: width < 520

    Rectangle {
        anchors.fill: parent
        color: root.theme.panelDeep
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 6

        Rectangle {
            objectName: "processFilterHeader"
            Layout.fillWidth: true
            Layout.preferredHeight: 42
            radius: root.theme.itemRadius
            color: root.theme.surfaceContainerLow
            border.width: 1
            border.color: root.theme.outlineVariant

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 9
                anchors.rightMargin: 9
                spacing: 7

                Controls.MaterialIcon {
                    Layout.preferredWidth: 22
                    Layout.preferredHeight: 22
                    name: "filter-alt"
                    size: 17
                    color: root.theme.action
                }
                Label {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    text: qsTr("Pipeline for:") + " "
                        + processFilterEditorController.context_title
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }
            }
        }

        Controls.ProcessSelectionTree {
            Layout.fillWidth: true
            Layout.fillHeight: true
            theme: root.theme
            treeModel: processFilterModel
            treeController: processFilterEditorController
            validContext: processFilterEditorController.valid_context
            emptyText: qsTr("Select a Search Tab first")
            treeObjectName: "processFilterTree"
            rowObjectName: "processFilterRow"
        }

        Rectangle {
            objectName: "processFilterFooter"
            Layout.fillWidth: true
            Layout.preferredHeight: 48
            radius: root.theme.itemRadius
            color: root.theme.surfaceContainerLow
            border.width: 1
            border.color: root.theme.outlineVariant

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 8
                anchors.rightMargin: 8
                spacing: 6

                Label {
                    Layout.fillWidth: true
                    visible: !root.compact
                    text: processFilterEditorController.dirty
                        ? qsTr("Visibility has unsaved changes") : ""
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("Cancel")
                    flat: true
                    onClicked: {
                        processFilterEditorController.cancel()
                        windowModel.close_window(root.windowId)
                    }
                }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("Save")
                    icon.name: "save"
                    enabled: processFilterEditorController.valid_context
                    onClicked: processFilterEditorController.save()
                }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("Save and close")
                    icon.name: "done"
                    highlighted: true
                    enabled: processFilterEditorController.valid_context
                    onClicked: {
                        if (processFilterEditorController.save())
                            windowModel.close_window(root.windowId)
                    }
                }
            }
        }
    }
}

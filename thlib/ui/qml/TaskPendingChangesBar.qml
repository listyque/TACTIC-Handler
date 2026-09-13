import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    signal previewRequested(var sourceItem)

    objectName: "taskPendingChangesOverlaySlot"
    Layout.preferredHeight: 0
    Layout.minimumHeight: 0
    Layout.maximumHeight: 0
    z: 80

    Rectangle {
        objectName: "taskPendingChangesBar"
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: 42
        visible: tasksController.advancedDirtyCount > 0
        radius: root.theme.surfaceRadius
        color: root.theme.secondaryContainer

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 12
            anchors.rightMargin: 8
            spacing: 8

            Controls.MaterialIcon {
                name: "edit"
                size: 16
                color: root.theme.action
            }
            Label {
                Layout.fillWidth: true
                text: tasksController.advancedDirtyCount
                    + (tasksController.advancedDirtyCount === 1
                        ? qsTr(" task has unsaved changes")
                        : qsTr(" tasks have unsaved changes"))
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.label
            }
            Controls.CompactIconButton {
                id: ganttPreviewButton
                visible: tasksController.viewMode === "gantt"
                    && tasksController.ganttChangePreview.length > 0
                theme: root.theme
                iconName: "visibility"
                toolTip: qsTr("Preview Gantt changes")
                onClicked: root.previewRequested(ganttPreviewButton)
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("DISCARD")
                enabled: !tasksController.advancedSaving
                onClicked: tasksController.discard_advanced_changes()
            }
            Controls.Button {
                theme: root.theme
                text: tasksController.advancedSaving
                    ? qsTr("SAVING") : qsTr("SAVE")
                icon.name: "save"
                highlighted: true
                enabled: !tasksController.advancedSaving
                onClicked: tasksController.save_advanced_changes()
            }
        }
    }
}
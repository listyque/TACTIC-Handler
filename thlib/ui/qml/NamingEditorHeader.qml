import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Rectangle {
    id: root
    required property var theme
    required property var controller
    signal reloadRequested()

    implicitHeight: 66
    radius: root.theme.surfaceRadius
    color: root.theme.surfaceContainerLow
    border.width: 1
    border.color: root.theme.outlineVariant

    RowLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 9
        Rectangle {
            Layout.preferredWidth: 42
            Layout.preferredHeight: 42
            radius: 14
            color: root.theme.secondaryContainer
            Controls.MaterialIcon {
                anchors.centerIn: parent
                name: "drive_file_rename_outline"
                size: 21
                color: root.theme.action
            }
        }
        ColumnLayout {
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            spacing: 1
            Label {
                objectName: "namingTargetTitle"
                Layout.fillWidth: true
                text: root.controller.currentObject.title || qsTr("Select an sObject")
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.bodyLarge
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }
            Label {
                Layout.fillWidth: true
                text: (root.controller.currentObject.projectCode || qsTr("No project"))
                        + "  /  " + (root.controller.currentObject.searchType || qsTr("No search type"))
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.label
                elide: Text.ElideRight
            }
        }
        Label {
            visible: !root.controller.typeMode
            text: qsTr("Process")
            color: root.theme.secondaryText
            font.pointSize: Controls.Typography.label
        }
        Controls.ComboBox {
            visible: !root.controller.typeMode
            theme: root.theme
            Layout.preferredWidth: 130
            model: root.controller.processes
            translateDisplayText: false
            enabled: model.length > 0 && !root.controller.busy
            currentIndex: model.indexOf(root.controller.previewProcess)
            onActivated: root.controller.set_preview_process(currentText)
        }
        Label {
            text: qsTr("Preview context")
            color: root.theme.secondaryText
            font.pointSize: Controls.Typography.label
        }
        Controls.ComboBox {
            theme: root.theme
            Layout.preferredWidth: 160
            model: root.controller.contexts
            translateDisplayText: false
            editable: root.controller.typeMode
            enabled: !root.controller.busy
            currentIndex: model.indexOf(root.controller.previewContext)
            onActivated: root.controller.set_preview_context(currentText)
            onAccepted: root.controller.set_preview_context(editText)
        }
        RefreshIconButton {
            objectName: "namingReload"
            theme: root.theme
            toolTip: qsTr("Reload project naming rules")
            enabled: !root.controller.busy && Boolean(root.controller.currentObject.projectCode)
            onClicked: root.reloadRequested()
        }
    }
}

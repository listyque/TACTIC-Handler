import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import "controls" as Controls

Item {
    id: root
    required property var theme
    property string selectedCode: ""
    readonly property var controller: projectCreationController

    Rectangle { anchors.fill: parent; color: root.theme.workspace }
    ScrollView {
        id: scroll
        anchors.fill: parent
        contentWidth: availableWidth
        contentHeight: content.implicitHeight + 40
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        ScrollBar.vertical: Controls.ScrollBar {
            id: bar
            theme: root.theme
            flickableTarget: scroll
        }
        ColumnLayout {
            id: content
            x: 20
            y: 20
            width: Math.max(0, scroll.availableWidth - 40 - bar.reservedExtent)
            spacing: 14
            RowLayout {
                Layout.fillWidth: true
                Controls.Button {
                    objectName: "projectTemplateImport"
                    theme: root.theme
                    text: qsTr("Install template archive")
                    icon.name: "plus"
                    enabled: !root.controller.busy
                    onClicked: archiveDialog.open()
                }
                Item { Layout.fillWidth: true }
                Controls.CompactIconButton {
                    theme: root.theme
                    iconName: "refresh"
                    toolTip: qsTr("Refresh templates")
                    enabled: !root.controller.busy
                    onClicked: root.controller.reload_catalog()
                }
                Controls.CompactIconButton {
                    theme: root.theme
                    iconName: "help"
                    toolTip: qsTr("Project creation help")
                    onClicked: windowModel.open_help("project_creation")
                }
            }
            ConfigurationSection {
                Layout.fillWidth: true
                theme: root.theme
                title: qsTr("Installed templates")
                description: qsTr("Template packages installed on the TACTIC server. Select a package to download or remove it.")
                Repeater {
                    model: root.controller.catalog.installedTemplates || []
                    delegate: Controls.SettingsNavigationItem {
                        required property var modelData
                        Layout.fillWidth: true
                        theme: root.theme
                        text: modelData.code
                        description: modelData.path
                        iconName: "archive"
                        selected: root.selectedCode === modelData.code
                        enabled: !root.controller.busy
                        onClicked: root.selectedCode = modelData.code
                    }
                }
                RowLayout {
                    Controls.Button {
                        objectName: "projectTemplateDownload"
                        theme: root.theme
                        text: qsTr("Download archive")
                        icon.name: "download"
                        enabled: !root.controller.busy && root.selectedCode.length > 0
                        onClicked: root.controller.template_action("download", root.selectedCode)
                    }
                    Controls.Button {
                        objectName: "projectTemplateDelete"
                        theme: root.theme
                        text: qsTr("Delete")
                        destructive: true
                        enabled: !root.controller.busy && root.selectedCode.length > 0
                        onClicked: deleteConfirmation.open()
                    }
                }
            }
            Controls.BusyIndicator {
                uiTheme: root.theme
                running: root.controller.busy
                visible: running
                Layout.preferredWidth: 24
                Layout.preferredHeight: 24
            }
            Label {
                Layout.fillWidth: true
                visible: root.controller.error.length > 0
                text: root.controller.error
                color: root.theme.error
                wrapMode: Text.WordWrap
                font.family: root.theme.fontFamily
            }
        }
    }
    FileDialog {
        id: archiveDialog
        title: qsTr("Install template archive")
        nameFilters: [qsTr("Template archives") + " (*.zip)"]
        onAccepted: root.controller.template_action("install", selectedFile)
    }
    Controls.Dialog {
        id: deleteConfirmation
        theme: root.theme
        modal: true
        anchors.centerIn: parent
        title: qsTr("Delete template?")
        contentItem: Label {
            text: qsTr("Remove the installed template package %1? Existing projects are not removed.").arg(root.selectedCode)
            color: root.theme.primaryText
            font.family: root.theme.fontFamily
            wrapMode: Text.WordWrap
        }
        footer: RowLayout {
            Controls.Button {
                theme: root.theme
                text: qsTr("Cancel")
                onClicked: deleteConfirmation.close()
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Delete")
                destructive: true
                onClicked: {
                    deleteConfirmation.close()
                    root.controller.template_action("delete", root.selectedCode)
                    root.selectedCode = ""
                }
            }
        }
    }
}

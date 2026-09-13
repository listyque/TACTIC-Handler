import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme

    Connections {
        target: projectEditorController
        function onSaved(projectCode) {
            windowModel.close_window("project_editor")
        }
    }


    Rectangle {
        anchors.fill: parent
        color: root.theme.panelDeep
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 24
            Layout.rightMargin: 16
            Layout.topMargin: 16
            Layout.bottomMargin: 12
            spacing: 10

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Label {
                    Layout.fillWidth: true
                    text: qsTr("Edit project")
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pixelSize: 18
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }
                Label {
                    Layout.fillWidth: true
                    text: projectEditorController.code
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                    elide: Text.ElideMiddle
                }
            }

            Controls.CompactIconButton {
                theme: root.theme
                iconName: "help"
                round: true
                toolTip: qsTr("Project help")
                onClicked: windowModel.open_help("project_creation")
            }
        }

        ScrollView {
            id: formScroll
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: availableWidth
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            ScrollBar.vertical: Controls.ScrollBar {
                theme: root.theme
                flickableTarget: formScroll
            }

            ColumnLayout {
                width: Math.max(0, formScroll.availableWidth - 48)
                x: 24
                y: 4
                spacing: 14

                ConfigurationSection {
                    Layout.fillWidth: true
                    theme: root.theme
                    title: qsTr("Project image")
                    description: qsTr("The large web preview is used in project cards. Saving a new image adds it to the Commit Queue.")
                    iconName: "icon"

                    Controls.ImagePicker {
                        Layout.fillWidth: true
                        theme: root.theme
                        objectNamePrefix: "project"
                        previewSize: 160
                        previewUrl: projectEditorController.previewUrl
                        stagedPath: projectEditorController.previewPath
                        fallbackText: projectEditorController.code.slice(0, 2).toUpperCase()
                        dialogTitle: qsTr("Choose project preview")
                        enabled: !projectEditorController.busy
                        statusText: stagedPath.length > 0
                            ? qsTr("A new preview is ready to be queued")
                            : qsTr("Current project preview")
                        description: qsTr("Choose a large image; the repository web representation is used automatically when available.")
                        onSelectionRequested: image => projectEditorController.set_preview_path(image)
                    }
                }

                ConfigurationSection {
                    Layout.fillWidth: true
                    theme: root.theme
                    title: qsTr("Project details")
                    description: qsTr("Category and type describe how the project is organized; the project code is permanent.")
                    iconName: "description"

                    Controls.SettingsRow {
                        theme: root.theme
                        title: qsTr("Project code")
                        description: qsTr("Permanent TACTIC identifier. It cannot be changed here.")
                        Label {
                            text: projectEditorController.code
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.bodyLarge
                        }
                    }

                    Controls.SettingsRow {
                        theme: root.theme
                        title: qsTr("Name")
                        description: qsTr("Human-readable project title shown throughout the application.")
                        Controls.TextField {
                            theme: root.theme
                            Layout.preferredWidth: 300
                            text: projectEditorController.title
                            enabled: !projectEditorController.busy
                            errorState: text.trim().length === 0
                            onTextEdited: projectEditorController.set_title(text)
                        }
                    }

                    Controls.SettingsRow {
                        theme: root.theme
                        title: qsTr("Category")
                        description: qsTr("Groups related projects in the chooser.")
                        Controls.TextField {
                            theme: root.theme
                            Layout.preferredWidth: 300
                            text: projectEditorController.category
                            placeholderText: qsTr("Not set")
                            enabled: !projectEditorController.busy
                            onTextEdited: projectEditorController.set_category(text)
                        }
                    }

                    Controls.SettingsRow {
                        theme: root.theme
                        title: qsTr("Type")
                        description: qsTr("Project classification stored by TACTIC.")
                        showDivider: false
                        Controls.TextField {
                            theme: root.theme
                            Layout.preferredWidth: 300
                            text: projectEditorController.projectType
                            placeholderText: qsTr("Not set")
                            enabled: !projectEditorController.busy
                            onTextEdited: projectEditorController.set_project_type(text)
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.topMargin: 10
                        spacing: 5
                        Label {
                            text: qsTr("Description")
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.bodyLarge
                            font.weight: Font.DemiBold
                        }
                        Label {
                            Layout.fillWidth: true
                            text: qsTr("Explain the purpose of the project for people browsing the workspace.")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Controls.Typography.label
                            wrapMode: Text.WordWrap
                        }
                        Controls.TextArea {
                            theme: root.theme
                            Layout.fillWidth: true
                            Layout.preferredHeight: 96
                            text: projectEditorController.description
                            enabled: !projectEditorController.busy
                            placeholderText: qsTr("Project description")
                            onTextChanged: {
                                if (activeFocus)
                                    projectEditorController.set_description(text)
                            }
                        }
                    }
                }

                ConfigurationSection {
                    Layout.fillWidth: true
                    theme: root.theme
                    title: qsTr("Lifecycle")
                    description: qsTr("Archived projects stay on the server but are hidden by default. Templates are available for creating new projects.")
                    iconName: "inventory-2"

                    Controls.SettingsRow {
                        theme: root.theme
                        title: qsTr("Archive project")
                        description: qsTr("Hide this project from the default active-project list without deleting it.")
                        Controls.Switch {
                            theme: root.theme
                            text: ""
                            checked: projectEditorController.archived
                            enabled: !projectEditorController.busy
                            onToggled: projectEditorController.set_archived(checked)
                        }
                    }

                    Controls.SettingsRow {
                        theme: root.theme
                        title: qsTr("Use as template")
                        description: qsTr("Mark this project as a source template for future projects.")
                        showDivider: false
                        Controls.Switch {
                            theme: root.theme
                            text: ""
                            checked: projectEditorController.isTemplate
                            enabled: !projectEditorController.busy
                            onToggled: projectEditorController.set_template(checked)
                        }
                    }
                }

                Label {
                    Layout.fillWidth: true
                    visible: projectEditorController.error.length > 0
                    text: projectEditorController.error
                    color: root.theme.error
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.bodyLarge
                    wrapMode: Text.WordWrap
                }

                Item { Layout.preferredHeight: 12 }
            }
        }

        Controls.DockWorkspaceFooter {
            Layout.fillWidth: true
            Layout.preferredHeight: 64
            theme: root.theme

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 20
                anchors.rightMargin: 20
                spacing: 8

                Controls.BusyIndicator {
                    uiTheme: root.theme
                    Layout.preferredWidth: 24
                    Layout.preferredHeight: 24
                    running: projectEditorController.busy
                    visible: running
                }
                Label {
                    Layout.fillWidth: true
                    text: projectEditorController.busy
                        ? qsTr("Saving project...") : ""
                    color: root.theme.secondaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("Cancel")
                    flat: true
                    enabled: !projectEditorController.busy
                    onClicked: windowModel.close_window("project_editor")
                }
                Controls.Button {
                    theme: root.theme
                    text: qsTr("Save changes")
                    icon.name: "content-save"
                    highlighted: true
                    enabled: !projectEditorController.busy
                        && projectEditorController.title.trim().length > 0
                    onClicked: projectEditorController.submit()
                }
            }
        }
    }
}

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root

    required property var theme
    property int currentStep: 0
    readonly property var steps: [
        {
            "title": qsTr("Name and code"),
            "description": qsTr("Define the project title, code, and basic identity."),
            "icon": "edit"
        },
        {
            "title": qsTr("Template"),
            "description": qsTr("Choose the TACTIC project template to build from."),
            "icon": "control-point-duplicate"
        },
        {
            "title": qsTr("Preview"),
            "description": qsTr("Choose the image used to identify the project."),
            "icon": "image"
        },
        {
            "title": qsTr("Categories"),
            "description": qsTr("Assign project categories and organizational metadata."),
            "icon": "category"
        },
        {
            "title": qsTr("Review"),
            "description": qsTr("Review the collected values before creating the project."),
            "icon": "check-circle"
        }
    ]
    readonly property var step: steps[currentStep]

    Rectangle {
        anchors.fill: parent
        color: root.theme.workspace
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 72
            color: root.theme.surfaceContainerLow

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 22
                anchors.rightMargin: 22
                spacing: 12

                Rectangle {
                    Layout.preferredWidth: 40
                    Layout.preferredHeight: 40
                    radius: root.theme.itemRadius
                    color: root.theme.primaryContainer

                    Controls.MaterialIcon {
                        anchors.centerIn: parent
                        name: "create-new-folder"
                        size: 20
                        color: root.theme.action
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    Label {
                        text: qsTr("Create Project")
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 17
                        font.weight: Font.DemiBold
                    }
                    Label {
                        text: qsTr("Project creation wizard foundation")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                    }
                }

                Controls.CompactIconButton {
                    theme: root.theme
                    iconName: "help"
                    toolTip: qsTr("Project creation help")
                    onClicked: windowModel.open_help("project_creation")
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: root.theme.outlineVariant
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            Rectangle {
                Layout.preferredWidth: 220
                Layout.fillHeight: true
                color: root.theme.surfaceContainerLow

                ListView {
                    id: wizardStepsList
                    anchors.fill: parent
                    anchors.margins: 12
                    model: root.steps
                    spacing: 4
                    interactive: contentHeight > height
                    clip: true
                    ScrollBar.vertical: Controls.ScrollBar {
                        theme: root.theme
                        flickableTarget: wizardStepsList
                    }

                    delegate: Rectangle {
                        id: stepRow
                        required property var modelData
                        required property int index
                        width: ListView.view.width
                        height: 48
                        radius: root.theme.itemRadius
                        color: index === root.currentStep ? root.theme.selected : "transparent"

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 10
                            anchors.rightMargin: 10
                            spacing: 10

                            Rectangle {
                                Layout.preferredWidth: 26
                                Layout.preferredHeight: 26
                                radius: 13
                                color: index <= root.currentStep ? root.theme.primaryContainer : root.theme.surfaceContainerHigh

                                Label {
                                    anchors.centerIn: parent
                                    text: stepRow.index + 1
                                    color: stepRow.index <= root.currentStep ? root.theme.action : root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.label
                                    font.weight: Font.DemiBold
                                }
                            }

                            Label {
                                Layout.fillWidth: true
                                text: stepRow.modelData.title
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Controls.Typography.body
                                font.weight: stepRow.index === root.currentStep ? Font.DemiBold : Font.Normal
                                elide: Text.ElideRight
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.preferredWidth: 1
                Layout.fillHeight: true
                color: root.theme.outlineVariant
            }

            ScrollView {
                id: wizardScroll
                Layout.fillWidth: true
                Layout.fillHeight: true
                contentWidth: availableWidth
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                ScrollBar.vertical: Controls.ScrollBar {
                    theme: root.theme
                }

                ColumnLayout {
                    x: 22
                    y: 22
                    width: Math.max(0, wizardScroll.availableWidth - 44)
                    spacing: 14

                    ConfigurationSection {
                        Layout.fillWidth: true
                        theme: root.theme
                        title: root.step.title
                        description: root.step.description
                        iconName: root.step.icon

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 150
                            radius: root.theme.itemRadius
                            color: root.theme.surfaceContainerHigh
                            border.width: 1
                            border.color: root.theme.outlineVariant

                            ColumnLayout {
                                anchors.centerIn: parent
                                width: Math.min(parent.width - 40, 380)
                                spacing: 8

                                Controls.MaterialIcon {
                                    Layout.alignment: Qt.AlignHCenter
                                    name: root.step.icon
                                    size: 28
                                    color: root.theme.secondaryText
                                }
                                Label {
                                    Layout.fillWidth: true
                                    text: qsTr("This step is reserved for the project creation workflow.")
                                    color: root.theme.secondaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Controls.Typography.body
                                    horizontalAlignment: Text.AlignHCenter
                                    wrapMode: Text.WordWrap
                                }
                            }
                        }
                    }

                    Label {
                        Layout.fillWidth: true
                        text: qsTr("This is a UI foundation only. It does not create or modify TACTIC projects yet.")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                        wrapMode: Text.WordWrap
                    }
                }
            }
        }

        Controls.DockWorkspaceFooter {
            Layout.fillWidth: true
            Layout.preferredHeight: 64
            theme: root.theme

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 16
                anchors.rightMargin: 16
                spacing: 8

                Controls.Button {
                    theme: root.theme
                    text: qsTr("Cancel")
                    flat: true
                    onClicked: windowModel.close_window("project_wizard")
                }

                Item {
                    Layout.fillWidth: true
                }

                Controls.Button {
                    theme: root.theme
                    text: qsTr("Back")
                    icon.name: "chevron-left"
                    enabled: root.currentStep > 0
                    onClicked: root.currentStep--
                }

                Controls.Button {
                    theme: root.theme
                    visible: root.currentStep < root.steps.length - 1
                    text: qsTr("Next")
                    icon.name: "chevron-right"
                    highlighted: true
                    onClicked: root.currentStep++
                }

                Controls.Button {
                    theme: root.theme
                    visible: root.currentStep === root.steps.length - 1
                    text: qsTr("Create project")
                    icon.name: "plus-box"
                    highlighted: true
                    enabled: false
                    toolTip: qsTr("Project creation is not implemented yet")
                }
            }
        }
    }
}

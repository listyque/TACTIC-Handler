import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls
Item {
    id: root
    required property var theme
    objectName: "root"
    readonly property bool compactLayout: width < 900
    readonly property bool iconOnlyActions: width < 520
    property string selectedCode: ""
    property string selectedTitle: ""
    property string selectedStatus: ""
    property bool selectedBuiltin: false

    RowLayout {
        anchors.fill: parent
        objectName: "projectPageLayout"
        anchors.margins: 20
        spacing: 14

        ConfigurationSection {
            objectName: "projectCatalogSection"
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            Layout.fillHeight: true
            Layout.maximumWidth: root.compactLayout
                ? Math.max(0, root.width - 40) : 16777215
            theme: root.theme
            fillContentHeight: true
            title: qsTr("Available projects")
            description: qsTr("Select a project to make it active in the workspace.")
            iconName: "project-diagram"

            Controls.ProjectFilterToggles {
                Layout.minimumWidth: 0
                Layout.fillWidth: true
                theme: root.theme
                model: projectModel
                showSummary: true
            }

            ColumnLayout {
                Layout.minimumWidth: 0
                visible: root.compactLayout
                Layout.fillWidth: true
                spacing: 12

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 1

                    Label {
                        Layout.fillWidth: true
                        text: root.selectedTitle
                            || qsTr("Select a project")
                        color: root.selectedTitle.length
                            ? root.theme.primaryText
                            : root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.body
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                    }
                    Label {
                        Layout.fillWidth: true
                        visible: root.selectedCode.length > 0
                        text: root.selectedCode
                            + (root.selectedStatus.length
                                ? " · " + root.selectedStatus
                                : "")
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                        elide: Text.ElideRight
                    }
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Item {
                        Layout.fillWidth: true
                    }

                Controls.Button {
                    theme: root.theme
                    text: root.iconOnlyActions
                        ? "" : qsTr("Activate")
                    toolTip: qsTr("Activate selected project")
                    icon.name: "arrow_forward"
                    enabled: root.selectedCode.length > 0
                    onClicked: appController.select_project(
                        root.selectedCode)
                }
                Controls.Button {
                    theme: root.theme
                    tonal: true
                    text: root.iconOnlyActions
                        ? "" : qsTr("Edit")
                    toolTip: qsTr("Edit selected project")
                    icon.name: "edit"
                    enabled: root.selectedCode.length > 0
                        && !root.selectedBuiltin
                    onClicked: appController.edit_project(
                        root.selectedCode)
                }
                Controls.Button {
                    theme: root.theme
                    tonal: true
                    text: root.iconOnlyActions
                        ? "" : qsTr("New project")
                    toolTip: qsTr("Create new project")
                    icon.name: "plus-box"
                    onClicked:
                        windowModel.show_window("project_wizard")
                }
                }
            }

            ListView {
                id: projectList
                objectName: "configurationProjectList"
                Layout.minimumWidth: 0
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 4
                model: projectModel
                delegate: Controls.ProjectCard {
                    id: projectRow
                    required property var projectDetails
                    details: projectDetails || ({})
                    selected: root.selectedCode === details.code
                    width: projectList.width
                    theme: root.theme
                    compact: true
                    onClicked: {
                        root.selectedCode =
                            details.code || ""
                        root.selectedTitle =
                            details.title || ""
                        root.selectedStatus =
                            details.status || ""
                        root.selectedBuiltin =
                            Boolean(details.isBuiltin)
                    }
                    onDoubleClicked: {
                        root.selectedCode =
                            details.code || ""
                        appController.select_project(
                            details.code || "")
                    }
                }
                ScrollBar.vertical: Controls.ScrollBar {
                    theme: root.theme
                    flickableTarget: projectList
                }
            }
        }

        ConfigurationSection {
            visible: !root.compactLayout
            Layout.minimumWidth: 280
            Layout.preferredWidth: Math.min(
                360, Math.max(280, parent.width * .34))
            Layout.fillHeight: true
            theme: root.theme
            title: qsTr("Workspace project")
            fillContentHeight: true
            description: qsTr("Project selection is shared with the main project chooser.")
            iconName: "workspaces"

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6
                Label {
                    text: qsTr("CURRENT")
                    color: root.theme.secondaryText
                    font.pointSize: Controls.Typography.caption
                    font.weight: Font.DemiBold
                }
                Label {
                    Layout.fillWidth: true
                    text: appController.current_project_title
                        || qsTr("No active project")
                    color: root.theme.primaryText
                    font.pixelSize: 13
                    font.weight: Font.DemiBold
                    wrapMode: Text.WordWrap
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 92
                radius: 12
                color: root.theme.surfaceContainerHigh
                border.width: 1
                border.color: root.theme.outlineVariant

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 4
                    Label {
                        text: root.selectedCode.length
                            ? qsTr("SELECTED PROJECT")
                            : qsTr("SELECT A PROJECT")
                        color: root.theme.secondaryText
                        font.pointSize: Controls.Typography.caption
                        font.weight: Font.DemiBold
                    }
                    Label {
                        Layout.fillWidth: true
                        text: root.selectedTitle
                            || qsTr("Choose an item from the list")
                        color: root.selectedTitle.length
                            ? root.theme.primaryText
                            : root.theme.disabledText
                        font.pointSize: Controls.Typography.bodyLarge
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                    }
                    Label {
                        Layout.fillWidth: true
                        text: root.selectedCode
                            + (root.selectedStatus.length
                                ? " · " + root.selectedStatus : "")
                        color: root.theme.secondaryText
                        font.pointSize: Controls.Typography.label
                        elide: Text.ElideRight
                    }
                }
            }

            ColumnLayout {
                objectName: "projectWorkspaceActions"
                Layout.fillWidth: true
                spacing: 8

                Controls.Button {
                    objectName: "activateSelectedProjectButton"
                    theme: root.theme
                    highlighted: true
                    Layout.fillWidth: true
                    enabled: root.selectedCode.length > 0
                    text: qsTr("Activate selected project")
                    icon.name: "arrow_forward"
                    onClicked:
                        appController.select_project(root.selectedCode)
                }

                Controls.Button {
                    objectName: "editSelectedProjectButton"
                    theme: root.theme
                    tonal: true
                    Layout.fillWidth: true
                    enabled: root.selectedCode.length > 0
                        && !root.selectedBuiltin
                    text: qsTr("Edit selected project")
                    icon.name: "edit"
                    onClicked:
                        appController.edit_project(root.selectedCode)
                }
                Controls.Button {
                    objectName: "createProjectButton"
                    theme: root.theme
                    tonal: true
                    Layout.fillWidth: true
                    text: qsTr("Create new project")
                    icon.name: "plus-box"
                    onClicked: windowModel.show_window("project_wizard")
                }
            }

            Item {
                Layout.fillHeight: true
            }
        }
    }
}

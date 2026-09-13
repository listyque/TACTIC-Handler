import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root
    required property var theme
    readonly property var controller: administrationController
    readonly property bool workflowVisible: controller.section === "workflow"
    readonly property var sections: [
        {key: "types", title: qsTr("Search Types"), icon: "sobject", description: qsTr("Entities and fields")},
        {key: "schema", title: qsTr("Project schema"), icon: "schema", description: qsTr("Relationships between entities")},
        {key: "workflow", title: qsTr("Workflow"), icon: "workflow", description: qsTr("Processes, dependencies and scripts")},
        {key: "users", title: qsTr("Users"), icon: "person", description: qsTr("Profiles and accounts")},
        {key: "groups", title: qsTr("Groups"), icon: "groups", description: qsTr("Members and group management")},
        {key: "rules", title: qsTr("Access rules"), icon: "security", description: qsTr("Projects, entities, processes and interface")}
    ]

    Rectangle { anchors.fill: parent; color: root.theme.workspace }
    RowLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 12
        Controls.EditorPanel {
            Layout.preferredWidth: 224
            Layout.fillHeight: true
            theme: root.theme
            title: qsTr("Administration")
            description: qsTr("Server management")
            iconName: "security"

            Controls.SectionLabel {
                Layout.fillWidth: true
                theme: root.theme
                text: qsTr("Project")
            }
            Controls.ComboBox {
                id: projectSelector
                objectName: "administrationProjectSelector"
                Layout.fillWidth: true
                theme: root.theme
                model: projectModel.allProjects
                textRole: "title"
                valueRole: "projectCode"
                translateDisplayText: false
                currentIndex: projectSelector.model.findIndex(project => project.projectCode === root.controller.project)
                displayText: currentIndex < 0 ? (root.controller.project || qsTr("Select a project")) : currentText
                enabled: !root.controller.projectLocked
                onActivated: root.controller.select_project(String(currentValue))
            }
            Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: root.theme.outlineVariant }
            Controls.ResponsiveFlow {
                Layout.fillWidth: true
                visible: root.workflowVisible
                minimumCellWidth: root.theme.controlHeight
                preferredCellWidth: root.theme.controlHeight
                maximumColumns: 3
                spacing: 4
                Repeater {
                    model: root.sections
                    delegate: Controls.CompactIconButton {
                        required property var modelData
                        objectName: "adminSection_" + modelData.key
                        theme: root.theme
                        width: parent.cellWidth()
                        height: root.theme.controlHeight
                        iconName: modelData.icon
                        toolTip: modelData.title
                        backgroundColor: root.controller.section === modelData.key ? root.theme.selected : "transparent"
                        iconColor: root.controller.section === modelData.key ? root.theme.action : root.theme.primaryText
                        onClicked: root.controller.select_section(modelData.key)
                    }
                }
            }
            ListView {
                id: navigation
                objectName: "administrationNavigation"
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: !root.workflowVisible
                clip: true
                spacing: 4
                model: root.sections
                boundsBehavior: Flickable.StopAtBounds
                delegate: Controls.EditorListItem {
                    required property var modelData
                    objectName: "adminSection_" + modelData.key
                    width: navigation.width - navigationBar.reservedExtent - 4
                    theme: root.theme
                    text: modelData.title
                    description: modelData.description
                    iconName: modelData.icon
                    selected: root.controller.section === modelData.key
                    onClicked: root.controller.select_section(modelData.key)
                }
                ScrollBar.vertical: Controls.ScrollBar {
                    id: navigationBar
                    theme: root.theme
                    flickableTarget: navigation
                }
            }
            AdminWorkflowList {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: root.workflowVisible
                theme: root.theme
                controller: root.controller.workflowEditor
            }
            Label {
                Layout.fillWidth: true
                visible: root.controller.section !== "groups" && text.length > 0
                text: root.controller.busy ? qsTr("Refreshing server metadata…") : root.controller.error
                color: root.controller.error ? root.theme.error : root.theme.secondaryText
                font.pointSize: Controls.Typography.label
                wrapMode: Text.Wrap
            }
        }
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumWidth: 0
            SecurityGroupsView {
                anchors.fill: parent
                visible: root.controller.section === "groups"
                theme: root.theme
                controller: root.controller
                groupsModel: administrationGroupModel
                membersModel: administrationMemberModel
            }
            Loader {
                anchors.fill: parent
                visible: root.controller.section === "types"
                active: false
                onVisibleChanged: if (visible) active = true
                Component.onCompleted: if (visible) active = true
                sourceComponent: AdminSearchTypesView {
                    theme: root.theme
                    controller: root.controller.typesEditor
                    namingController: root.controller.namingEditor
                    projectCode: root.controller.project
                    onOpenWorkflowRequested: identity => root.controller.open_type_workflow(identity)
                    onCreateWorkflowRequested: root.controller.create_type_workflow(root.controller.typesEditor)
                }
            }
            Loader {
                anchors.fill: parent
                visible: root.controller.section === "schema"
                active: false
                onVisibleChanged: if (visible) active = true
                Component.onCompleted: if (visible) active = true
                sourceComponent: AdminGraphView {
                    id: schemaView
                    theme: root.theme
                    controller: root.controller.schemaEditor
                    onCreateSearchTypeRequested: (x, y) => root.controller.schemaTypeEditor.open(x, y)
                    onNodeWorkflowsRequested: root.controller.open_schema_node_workflows()
                    onDeleteSearchTypeRequested: identity => {
                        if (root.controller.prepare_schema_node_deletion(identity)) schemaView.showDeleteConfirmation()
                    }
                }
            }
            Loader {
                anchors.fill: parent
                visible: root.controller.section === "workflow"
                active: false
                onVisibleChanged: if (visible) active = true
                Component.onCompleted: if (visible) active = true
                sourceComponent: AdminGraphView { theme: root.theme; controller: root.controller.workflowEditor }
            }
            Loader {
                anchors.fill: parent
                visible: root.controller.section === "rules"
                active: false
                onVisibleChanged: if (visible) active = true
                Component.onCompleted: if (visible) active = true
                sourceComponent: AdminSecurityView { theme: root.theme; controller: root.controller.securityEditor }
            }
            Loader {
                anchors.fill: parent
                visible: root.controller.section === "users"
                active: false
                onVisibleChanged: if (visible) active = true
                Component.onCompleted: if (visible) active = true
                sourceComponent: AdminUsersView {
                    theme: root.theme
                    controller: root.controller.usersEditor
                }
            }
        }
    }
}

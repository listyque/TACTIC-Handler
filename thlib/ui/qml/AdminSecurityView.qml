import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

AdminDocumentShell {
    id: root

    property string scope: "project"
    readonly property bool matrixScope: ["project", "link", "gear_menu", "search_type", "process", "tasks"].indexOf(scope) >= 0
    readonly property var scopes: [
        {identity: "project", label: qsTr("Projects"), icon: "folder-special"},
        {identity: "link", label: qsTr("Sidebar links"), icon: "sidebar-link"},
        {identity: "gear_menu", label: qsTr("Menu actions"), icon: "more-vert"},
        {identity: "search_type", label: qsTr("Search Types"), icon: "deployed-code"},
        {identity: "process", label: qsTr("Processes"), icon: "account-tree"},
        {identity: "tasks", label: qsTr("Task statuses"), icon: "task"},
        {identity: "sobject", label: qsTr("Search Objects"), icon: "inventory-2"},
        {identity: "sobject_column", label: qsTr("Field access"), icon: "view-column"},
        {identity: "builtin", label: qsTr("Global permissions"), icon: "admin-panel-settings"},
        {identity: "search_filter", label: qsTr("Search restrictions"), icon: "filter-alt"},
        {identity: "technical", label: qsTr("Advanced rules"), icon: "code"}
    ]
    readonly property var currentScope: scopes.find(item => item.identity === scope) || scopes[0]

    title: qsTr("Access rules")
    description: qsTr("Find the permission row and the group column, then tick to allow access. Changes across groups are saved together.")
    iconName: "admin-panel-settings"
    showSelector: false

    editorContent: ColumnLayout {
        // The alias reparents this item into AdminDocumentShell's plain Item.
        anchors.fill: parent // qmllint disable Quick.layout-positioning
        spacing: 10

        Flow {
            id: categories
            objectName: "adminSecurityTabs"
            Layout.fillWidth: true
            spacing: 6

            Repeater {
                model: root.scopes
                delegate: Controls.TabButton {
                    required property var modelData
                    objectName: "adminSecurityTab_" + modelData.identity
                    width: implicitWidth
                    theme: root.theme
                    text: modelData.label
                    checked: root.scope === modelData.identity
                    onClicked: root.scope = modelData.identity
                }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            visible: !root.matrixScope
            Label {
                text: qsTr("Group")
                color: root.theme.secondaryText
            }
            Controls.ComboBox {
                objectName: "adminSecurityAdvancedGroup"
                Layout.fillWidth: true
                theme: root.theme
                model: root.controller.groupCatalog
                textRole: "label"
                valueRole: "identity"
                translateDisplayText: false
                currentIndex: root.controller.groupCatalog.findIndex(row => row.identity === root.controller.selectedGroup)
                onActivated: root.controller.select_group(String(currentValue))
            }
        }
        Loader {
            Layout.fillWidth: true
            Layout.fillHeight: true
            sourceComponent: root.matrixScope ? matrix : root.scope === "technical" ? technical : rules
        }
    }

    Component {
        id: matrix
        AdminSecurityMatrix {
            theme: root.theme
            controller: root.controller
            scope: root.scope
            title: root.currentScope.label
            iconName: root.currentScope.icon
        }
    }

    Component {
        id: rules
        AdminSecurityRules {
            theme: root.theme
            controller: root.controller
            scope: root.scope
            title: root.currentScope.label
            iconName: root.currentScope.icon
        }
    }
    Component {
        id: technical
        AdminSecurityTechnical {
            theme: root.theme
            controller: root.controller
        }
    }
}

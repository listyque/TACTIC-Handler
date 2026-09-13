import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Controls.EditorPanel {
    id: root

    required property var controller
    required property string scope
    property bool showBack: false
    property string targetQuery: ""
    readonly property var attributes: controller.selectedAttributes
    readonly property var fieldNames: ({
        project: ["code"], search_type: ["code"],
        process: ["process", "pipeline"], link: ["element"],
        sobject: ["key"], sobject_column: ["search_type", "column"],
        builtin: ["key"], gear_menu: ["submenu", "label"],
        search_filter: ["search_type", "column", "op", "value"]
    })[scope] || []
    readonly property var fieldLabels: ({
        code: scope === "project" ? qsTr("Project") : qsTr("Search Type"),
        process: qsTr("Process"), pipeline: qsTr("Pipeline"),
        element: qsTr("Sidebar link"), key: scope === "builtin" ? qsTr("Permission") : qsTr("Search Object or operation"),
        search_type: qsTr("Search Type"), column: qsTr("Field"),
        submenu: qsTr("Submenu"), label: qsTr("Menu action"),
        op: qsTr("Operator"), value: qsTr("Value")
    })
    readonly property var permissions: [
        {value: "deny", label: qsTr("Deny")}, {value: "view", label: qsTr("Read")},
        {value: "edit", label: qsTr("Modify")}, {value: "insert", label: qsTr("Create")},
        {value: "retire", label: qsTr("Archive")}, {value: "delete", label: qsTr("Delete")},
        {value: "allow", label: qsTr("Full access")}
    ]
    readonly property var targets: (scope === "builtin"
        ? (controller.metadata.builtinPermissions || []).map(item => ({
            label: item.title, attributes: {key: item.key}
        }))
        : (controller.metadata.targets || {})[scope] || []).filter(item =>
            !targetQuery || String(item.label).toLocaleLowerCase().indexOf(targetQuery.toLocaleLowerCase()) >= 0)
    signal backRequested()
    signal editStarted()
    signal editFinished()

    function setAttribute(name, value) {
        editStarted()
        controller.set_attribute(name, value)
        editFinished()
    }

    title: qsTr("Rule details")
    description: qsTr("Choose a server target or enter its identifier. An asterisk matches all targets.")
    iconName: "edit"
    onScopeChanged: targetQuery = ""
    actions: [
        Controls.CompactIconButton {
            objectName: "adminAccessRuleBack"
            theme: root.theme
            visible: root.showBack
            iconName: "chevron-left"
            toolTip: qsTr("Back to rules")
            onClicked: root.backRequested()
        },
        Controls.CompactIconButton {
            objectName: "adminRemoveAccessRule"
            theme: root.theme
            iconName: "delete"
            toolTip: qsTr("Remove rule")
            enabled: root.controller.canWrite && root.controller.selectedRule >= 0
            onClicked: {
                root.editStarted()
                root.controller.remove_rule()
                root.editFinished()
                root.backRequested()
            }
        }
    ]

    Flickable {
        id: viewport
        objectName: "adminSecurityRuleEditorViewport"
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        contentWidth: width
        contentHeight: fields.implicitHeight
        boundsBehavior: Flickable.StopAtBounds
        ColumnLayout {
            id: fields
            width: Math.max(0, viewport.width - editorBar.reservedExtent - 4)
            spacing: 12

            Label {
                Layout.fillWidth: true
                visible: root.scope !== "search_filter"
                text: qsTr("Access level")
                color: root.theme.secondaryText
                font.pointSize: Controls.Typography.label
            }
            Flow {
                Layout.fillWidth: true
                visible: root.scope !== "search_filter"
                spacing: 6
                Repeater {
                    model: root.permissions
                    delegate: Controls.Button {
                        required property var modelData
                        objectName: "adminAccessLevel_" + modelData.value
                        theme: root.theme
                        text: modelData.label
                        highlighted: root.attributes.access === modelData.value
                        enabled: root.controller.canWrite && root.controller.selectedRule >= 0
                        onClicked: root.setAttribute("access", modelData.value)
                    }
                }
            }
            Label {
                Layout.fillWidth: true
                visible: !!root.attributes.access && !root.permissions.some(item => item.value === root.attributes.access)
                text: qsTr("Native access value: %1. It is kept until you choose a different level.").arg(root.attributes.access || "")
                color: root.theme.secondaryText
                font.pointSize: Controls.Typography.label
                wrapMode: Text.WordWrap
            }
            Repeater {
                model: root.fieldNames
                delegate: ColumnLayout {
                    required property string modelData
                    Layout.fillWidth: true
                    spacing: 4
                    Label {
                        Layout.fillWidth: true
                        text: root.fieldLabels[modelData] || modelData
                        color: root.theme.secondaryText
                        font.pointSize: Controls.Typography.label
                    }
                    Controls.TextField {
                        objectName: "adminAccessField_" + modelData
                        Layout.fillWidth: true
                        theme: root.theme
                        enabled: root.controller.canWrite
                        text: String(root.attributes[modelData] || "")
                        onEditingFinished: {
                            if (text !== String(root.attributes[modelData] || ""))
                                root.setAttribute(modelData, text)
                        }
                    }
                }
            }
            ColumnLayout {
                Layout.fillWidth: true
                visible: Object.prototype.hasOwnProperty.call(root.attributes, "project")
                spacing: 4
                Label {
                    text: qsTr("Rule project")
                    color: root.theme.secondaryText
                    font.pointSize: Controls.Typography.label
                }
                Controls.TextField {
                    objectName: "adminAccessField_project"
                    Layout.fillWidth: true
                    theme: root.theme
                    enabled: root.controller.canWrite
                    text: String(root.attributes.project || "")
                    onEditingFinished: {
                        if (text !== String(root.attributes.project || ""))
                            root.setAttribute("project", text)
                    }
                }
            }
            Label {
                Layout.fillWidth: true
                text: qsTr("Available targets")
                color: root.theme.primaryText
                font.pointSize: Controls.Typography.body
                font.weight: Font.DemiBold
            }
            Controls.TextField {
                objectName: "adminSecurityTargetSearch"
                Layout.fillWidth: true
                theme: root.theme
                placeholderText: qsTr("Find a server target")
                text: root.targetQuery
                onTextEdited: root.targetQuery = text
            }
            ListView {
                id: targetsList
                objectName: "adminSecurityTargets"
                Layout.fillWidth: true
                Layout.preferredHeight: 190
                clip: true
                model: root.targets
                spacing: 4
                boundsBehavior: Flickable.StopAtBounds
                delegate: Controls.EditorListItem {
                    required property var modelData
                    required property int index
                    objectName: "adminSecurityTarget_" + index
                    width: Math.max(0, targetsList.width - targetBar.reservedExtent - 4)
                    theme: root.theme
                    text: modelData.label
                    description: Object.values(modelData.attributes).join(" · ")
                    selected: Object.keys(modelData.attributes).every(
                        key => String(modelData.attributes[key]) === String(root.attributes[key] || ""))
                    enabled: root.controller.canWrite
                    onClicked: {
                        root.editStarted()
                        root.controller.set_target(modelData.attributes)
                        root.editFinished()
                    }
                }
                Label {
                    anchors.fill: parent
                    visible: targetsList.count === 0
                    text: qsTr("No matching targets. You can enter an identifier above.")
                    color: root.theme.secondaryText
                    font.pointSize: Controls.Typography.label
                    wrapMode: Text.WordWrap
                }
                ScrollBar.vertical: Controls.ScrollBar {
                    id: targetBar
                    theme: root.theme
                    flickableTarget: targetsList
                }
            }
        }
        ScrollBar.vertical: Controls.ScrollBar {
            id: editorBar
            objectName: "adminSecurityRuleEditorScrollBar"
            theme: root.theme
            flickableTarget: viewport
        }
    }
}

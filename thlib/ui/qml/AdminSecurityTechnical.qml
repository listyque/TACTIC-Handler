import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

ColumnLayout {
    id: root

    required property var theme
    required property var controller
    property string page: "group"
    readonly property var customRules: controller.rules.filter(rule =>
        ["project", "search_type", "process", "sobject", "sobject_column", "link", "builtin", "gear_menu", "search_filter"]
            .indexOf(String(rule.group || rule.category || "")) < 0)

    spacing: 10
    Controls.SegmentedButton {
        Layout.fillWidth: true
        theme: root.theme
        currentValue: root.page
        model: [
            {value: "group", label: "Group defaults", icon: "groups"},
            {value: "xml", label: "Native XML", icon: "code"},
            {value: "rule", label: "Selected rule", icon: "edit", enabled: root.controller.selectedRule >= 0},
            {value: "inherited", label: "Inherited defaults", icon: "account-tree"}
        ]
        onActivated: value => root.page = value
    }

    Flickable {
        id: viewport
        objectName: "adminSecurityDefaultsViewport"
        Layout.fillWidth: true
        Layout.fillHeight: true
        visible: root.page === "group"
        clip: true
        contentWidth: width
        contentHeight: sections.implicitHeight
        boundsBehavior: Flickable.StopAtBounds
        ColumnLayout {
            id: sections
            width: Math.max(0, viewport.width - defaultsBar.reservedExtent - 4)
            spacing: 12

            Controls.EditorPanel {
                Layout.fillWidth: true
                theme: root.theme
                title: qsTr("Group defaults")
                description: qsTr("These native group settings participate in every access check, together with explicit rules and other memberships.")
                iconName: "groups"
                fillContentHeight: false
                Label {
                    text: qsTr("Access level")
                    color: root.theme.secondaryText
                    font.pointSize: Controls.Typography.label
                }
                Flow {
                    Layout.fillWidth: true
                    spacing: 6
                    Repeater {
                        model: root.controller.metadata.accessLevels || []
                        delegate: Controls.Button {
                            required property string modelData
                            objectName: "adminGroupAccessLevel_" + modelData
                            theme: root.theme
                            text: modelData
                            highlighted: root.controller.groupDocument.accessLevel === modelData
                            enabled: root.controller.canWrite
                            onClicked: root.controller.set_group_field("accessLevel", modelData)
                        }
                    }
                }
                Label {
                    text: qsTr("Group project (empty = global)")
                    color: root.theme.secondaryText
                    font.pointSize: Controls.Typography.label
                }
                Controls.TextField {
                    objectName: "adminGroupRuleProject"
                    Layout.fillWidth: true
                    theme: root.theme
                    enabled: root.controller.canWrite
                    text: root.controller.groupDocument.project || ""
                    onTextEdited: root.controller.set_group_field("project", text)
                }
                Label {
                    text: qsTr("Subgroups, separated by |")
                    color: root.theme.secondaryText
                    font.pointSize: Controls.Typography.label
                }
                Controls.TextField {
                    objectName: "adminGroupRuleSubgroups"
                    Layout.fillWidth: true
                    theme: root.theme
                    enabled: root.controller.canWrite
                    text: root.controller.groupDocument.subGroups || ""
                    onTextEdited: root.controller.set_group_field("subGroups", text)
                }
            }
            Controls.EditorPanel {
                Layout.fillWidth: true
                visible: root.customRules.length > 0
                theme: root.theme
                title: qsTr("Custom scopes")
                description: qsTr("Project-specific rules are preserved. Select a rule to edit its native attributes.")
                iconName: "code"
                fillContentHeight: false
                Repeater {
                    model: root.customRules
                    delegate: Controls.EditorListItem {
                        required property var modelData
                        objectName: "adminCustomAccessRule_" + modelData.ruleIndex
                        Layout.fillWidth: true
                        theme: root.theme
                        text: String(modelData.group || modelData.category || "")
                        description: String(modelData.key || modelData.code || "")
                        badgeText: String(modelData.access || "")
                        onClicked: {
                            root.controller.select_rule(modelData.ruleIndex)
                            root.page = "rule"
                        }
                    }
                }
            }
        }
        ScrollBar.vertical: Controls.ScrollBar {
            id: defaultsBar
            theme: root.theme
            flickableTarget: viewport
        }
    }
    AdminXmlEditor {
        Layout.fillWidth: true
        Layout.fillHeight: true
        visible: root.page !== "group"
        theme: root.theme
        title: root.page === "inherited" ? qsTr("Inherited access-level defaults (server)")
            : root.page === "rule" ? qsTr("Custom attributes (JSON)") : qsTr("Native access rules")
        sourceText: root.page === "inherited"
            ? ((root.controller.metadata.globalDefaultRulesByLevel || {})[root.controller.groupDocument.accessLevel] || "")
            : root.page === "rule" ? root.controller.ruleText : (root.controller.groupDocument.xml || "")
        readOnly: root.page === "inherited" || !root.controller.canWrite
            || (root.page === "rule" && root.controller.selectedRule < 0)
        onApplied: text => {
            if (root.page === "rule")
                root.controller.apply_rule(text)
            else if (root.page === "xml")
                root.controller.apply_xml(text)
        }
    }
}

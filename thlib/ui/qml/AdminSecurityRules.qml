import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

RowLayout {
    id: root

    required property var theme
    required property var controller
    required property string scope
    required property string title
    required property string iconName
    property string query: ""
    property bool editing: false
    property real scrollBeforeEditorChange: 0
    readonly property bool compact: width < 1040
    readonly property var records: controller.rules.filter(record => {
        if (String(record.group || record.category || "") !== scope)
            return false
        return !query || targetTitle(record).toLocaleLowerCase().indexOf(query.toLocaleLowerCase()) >= 0
            || targetDetail(record).toLocaleLowerCase().indexOf(query.toLocaleLowerCase()) >= 0
    })
    readonly property var levels: scope === "search_filter" ? []
        : [
            {value: "deny", label: qsTr("Deny")},
            {value: "view", label: qsTr("Read")},
            {value: "edit", label: qsTr("Modify")},
            {value: "allow", label: qsTr("Full access")}
        ]
    readonly property bool selectedInScope: String(controller.selectedAttributes.group
        || controller.selectedAttributes.category || "") === scope

    function targetTitle(record) {
        const targets = scope === "builtin"
            ? (controller.metadata.builtinPermissions || []).map(item => ({
                label: item.title, attributes: {key: item.key}
            }))
            : (controller.metadata.targets || {})[scope] || []
        const target = targets.find(item => Object.keys(item.attributes).every(
            key => String(item.attributes[key]) === String(record[key] || "")))
        if (target)
            return target.label
        const identity = record.code || record.process || record.element || record.key || record.search_type || record.label
        return !identity || identity === "*" ? qsTr("All targets") : String(identity)
    }

    function targetDetail(record) {
        const parts = [record.pipeline, record.search_type, record.column, record.submenu]
            .filter(value => !!value)
        if (record.group === "search_filter")
            parts.push(String(record.op || "=") + " " + String(record.value || ""))
        else if (record.project)
            parts.push(record.project)
        if (record.access && !levels.some(level => level.value === record.access))
            parts.push(qsTr("Access: %1").arg(record.access))
        return parts.join(" · ")
    }

    function editRule(index) {
        const scrollPosition = rulesList.contentY
        controller.select_rule(index)
        restoreScroll(scrollPosition)
        editing = true
    }

    function setAccess(index, access) {
        const scrollPosition = rulesList.contentY
        controller.set_rule_access(index, access)
        restoreScroll(scrollPosition)
    }

    function restoreScroll(position) {
        // The editor republishes its native rule list after an edit. Keep the
        // table's viewport stable while Qt replaces the affected delegates.
        rulesList.forceLayout()
        rulesList.contentY = Math.max(0, Math.min(position,
            rulesList.contentHeight - rulesList.height))
    }

    spacing: 12
    onScopeChanged: { query = ""; editing = false }

    Controls.EditorPanel {
        Layout.fillWidth: true
        Layout.fillHeight: true
        visible: !root.compact || !root.editing
        theme: root.theme
        title: root.title
        iconName: root.iconName
        description: root.scope === "search_filter"
            ? qsTr("Restrictions change which Search Objects are returned. They do not grant access.")
            : qsTr("One level per rule. Higher levels include lower ones; this is not a set of independent permissions.")
        actions: Controls.CompactIconButton {
            objectName: "adminAddAccessRule"
            theme: root.theme
            iconName: "add"
            toolTip: qsTr("Add rule")
            enabled: root.controller.canWrite && !!root.controller.identity
            onClicked: {
                root.controller.add_rule(root.scope)
                root.editing = true
            }
        }

        Controls.TextField {
            objectName: "adminSecurityRuleSearch"
            Layout.fillWidth: true
            theme: root.theme
            placeholderText: qsTr("Find a target or rule")
            text: root.query
            onTextEdited: root.query = text
        }
        RowLayout {
            Layout.fillWidth: true
            Layout.rightMargin: rulesBar.reservedExtent + 4
            spacing: 0
            Label {
                Layout.fillWidth: true
                Layout.leftMargin: 10
                text: qsTr("Target")
                color: root.theme.secondaryText
                font.pointSize: Controls.Typography.label
            }
            Repeater {
                model: root.levels
                delegate: Label {
                    required property var modelData
                    Layout.preferredWidth: 64
                    Layout.maximumWidth: 64
                    text: modelData.label
                    color: root.theme.secondaryText
                    font.pointSize: Controls.Typography.label
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.Wrap
                }
            }
            Item { Layout.preferredWidth: 32 }
        }
        ListView {
            id: rulesList
            objectName: "adminAccessRules"
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 4
            model: root.records
            boundsBehavior: Flickable.StopAtBounds
            delegate: Item {
                id: row
                required property var modelData
                objectName: "adminAccessRule_" + modelData.ruleIndex
                width: Math.max(0, rulesList.width - rulesBar.reservedExtent - 4)
                height: Math.max(62, rowContent.implicitHeight + 14)

                Controls.ItemSurface {
                    anchors.fill: parent
                    theme: root.theme
                    selected: root.controller.selectedRule === row.modelData.ruleIndex
                    railVisible: selected
                    cornerRadius: root.theme.itemRadius
                    separatorVisible: false
                }
                RowLayout {
                    id: rowContent
                    anchors.fill: parent
                    anchors.topMargin: 7
                    anchors.bottomMargin: 7
                    spacing: 0

                    Controls.EditorListItem {
                        objectName: "adminAccessTarget_" + row.modelData.ruleIndex
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        Layout.fillHeight: true
                        theme: root.theme
                        text: root.targetTitle(row.modelData)
                        description: root.targetDetail(row.modelData)
                        onClicked: root.editRule(row.modelData.ruleIndex)
                    }
                    Repeater {
                        model: root.levels
                        delegate: Item {
                            required property var modelData
                            Layout.preferredWidth: 64
                            Layout.fillHeight: true
                            Controls.CheckBox {
                                objectName: "adminPermission_" + row.modelData.ruleIndex + "_" + modelData.value
                                anchors.centerIn: parent
                                theme: root.theme
                                compact: true
                                text: ""
                                enabled: root.controller.canWrite
                                checkable: false
                                checked: row.modelData.access === modelData.value
                                Accessible.name: root.targetTitle(row.modelData) + ": " + modelData.label
                                onClicked: root.setAccess(row.modelData.ruleIndex, modelData.value)
                            }
                        }
                    }
                    Controls.CompactIconButton {
                        objectName: "adminEditAccessRule_" + row.modelData.ruleIndex
                        Layout.preferredWidth: 32
                        theme: root.theme
                        iconName: "edit"
                        toolTip: qsTr("Edit rule")
                        onClicked: root.editRule(row.modelData.ruleIndex)
                    }
                }
            }
            Controls.EmptyState {
                anchors.centerIn: parent
                width: Math.max(0, parent.width - rulesBar.reservedExtent - 16)
                theme: root.theme
                visible: rulesList.count === 0
                title: root.query ? qsTr("No matching rules") : qsTr("No explicit rules in this category")
                message: root.query ? "" : qsTr("Inherited defaults still apply. Add a rule to override them for a target.")
                iconName: "admin-panel-settings"
            }
            ScrollBar.vertical: Controls.ScrollBar {
                id: rulesBar
                objectName: "adminSecurityRulesScrollBar"
                theme: root.theme
                flickableTarget: rulesList
            }
        }
    }
    AdminSecurityRuleEditor {
        Layout.fillWidth: root.compact
        Layout.preferredWidth: root.compact ? -1 : 320
        Layout.fillHeight: true
        visible: root.compact ? root.editing : root.selectedInScope
        theme: root.theme
        controller: root.controller
        scope: root.scope
        showBack: root.compact
        onEditStarted: root.scrollBeforeEditorChange = rulesList.contentY
        onEditFinished: root.restoreScroll(root.scrollBeforeEditorChange)
        onBackRequested: root.editing = false
    }
}

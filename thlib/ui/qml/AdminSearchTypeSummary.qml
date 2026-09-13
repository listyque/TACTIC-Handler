pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

ColumnLayout {
    id: root

    required property var theme
    required property var controller
    readonly property var summary: controller.metadata.summary || {}
    readonly property bool compact: width < 420

    function typeLabel(identity) {
        const row = root.controller.catalog.find(item => item.identity === identity)
        return row ? row.label : identity
    }

    function relationshipDescription(edge) {
        let parts = []
        if (edge.manyToMany)
            parts.push(qsTr("Many-to-many (M:N): each side can be linked to several objects on the other side."))
        else if (edge.type === "hierarchy")
            parts.push(qsTr("Hierarchy: child → parent."))
        const kind = edge.relationship || edge.type
        if (kind) parts.push(qsTr("Relationship in schema: %1").arg(kind))
        if (edge.instanceType) parts.push(qsTr("Link table: %1").arg(edge.instanceType))
        if (edge.from_col || edge.to_col)
            parts.push(qsTr("Key fields: %1 → %2").arg(edge.from_col || "—").arg(edge.to_col || "—"))
        parts.push(qsTr("Schema: %1").arg(edge.schema))
        return parts.join("\n")
    }

    spacing: 16

    ConfigurationSection {
        Layout.fillWidth: true
        theme: root.theme
        title: root.controller.document.title || root.controller.identity
        description: root.controller.identity
        iconName: "sobject"
        GridLayout {
            Layout.fillWidth: true
            columns: root.compact ? 2 : 3
            columnSpacing: 16
            rowSpacing: 16
            Repeater {
                model: [
                    {key: "total", label: qsTr("Search Objects")},
                    {key: "active", label: qsTr("Active")},
                    {key: "retired", label: qsTr("Retired")},
                    {key: "fields", label: qsTr("Fields")},
                    {key: "pipelines", label: qsTr("Pipelines")},
                    {key: "processes", label: qsTr("Processes")}
                ]
                delegate: ColumnLayout {
                    id: metric
                    required property var modelData
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    spacing: 4
                    Label {
                        objectName: "adminSearchTypeCount_" + metric.modelData.key
                        Layout.fillWidth: true
                        text: root.summary[metric.modelData.key] === undefined
                            ? "—" : root.summary[metric.modelData.key]
                        color: root.theme.primaryText
                        font.pointSize: Controls.Typography.bodyLarge * 1.5
                        font.weight: Font.DemiBold
                    }
                    Label {
                        Layout.fillWidth: true
                        text: metric.modelData.label
                        color: root.theme.secondaryText
                        font.pointSize: Controls.Typography.label
                        wrapMode: Text.WordWrap
                    }
                }
            }
        }
        Label {
            Layout.fillWidth: true
            Layout.topMargin: 12
            text: qsTr("Totals include retired Search Objects. Shared system types are counted in their own database. Reload to update the summary.")
            color: root.theme.secondaryText
            font.pointSize: Controls.Typography.label
            wrapMode: Text.WordWrap
        }
    }
    AdminSearchTypeRelationshipMap {
        Layout.fillWidth: true
        theme: root.theme
        graphData: root.controller.relationshipGraph
    }
    ConfigurationSection {
        Layout.fillWidth: true
        theme: root.theme
        title: qsTr("Schema relationships")
        description: root.controller.metadata.linkTable
            ? qsTr("This is a link table for a many-to-many relationship, not a separate object category.")
            : qsTr("Relationships come from this project's schema and inherited schemas, not from table names.")
        Controls.SettingsRow {
            theme: root.theme
            title: qsTr("Data location")
            description: qsTr("Database: %1").arg(root.controller.metadata.database || "—")
                + "\n" + (root.controller.metadata.projectLocal
                    ? qsTr("Stored in the selected project") : qsTr("Shared data outside the selected project"))
        }
        Repeater {
            model: root.visible ? root.controller.metadata.relationships || [] : []
            delegate: Controls.SettingsRow {
                id: relationshipRow
                required property var modelData
                required property int index
                objectName: "adminSearchTypeRelation_" + index
                theme: root.theme
                title: root.typeLabel(relationshipRow.modelData.from) + " → "
                    + root.typeLabel(relationshipRow.modelData.to)
                description: root.relationshipDescription(relationshipRow.modelData)
            }
        }
        Label {
            Layout.fillWidth: true
            Layout.topMargin: 8
            visible: (root.controller.metadata.relationships || []).length === 0
            text: qsTr("No explicit relationships for this type in the loaded schemas.")
            wrapMode: Text.WordWrap
            color: root.theme.secondaryText
            font.pointSize: Controls.Typography.label
        }
    }
}

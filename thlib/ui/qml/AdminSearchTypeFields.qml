import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

ColumnLayout {
    id: root

    required property var theme
    required property var controller
    readonly property bool creatingType: controller.document.name !== undefined
    readonly property var automaticFields: ["id", "code", "name", "description", "keywords", "login", "timestamp", "data", "s_status", "relative_dir"]
    readonly property real fieldWidth: Math.max(100, Math.min(320, width - 48))
    readonly property var fieldTypes: [
        {value: "varchar(256)", label: qsTr("Short text"), name: "asset_title", example: qsTr("Firetruck"),
            help: qsTr("Names and short labels, up to 256 characters.")},
        {value: "text", label: qsTr("Long text"), name: "brief", example: qsTr("Describe the scene and what needs to be done."),
            help: qsTr("Descriptions and notes spanning several lines.")},
        {value: "integer", label: qsTr("Whole number"), name: "duration_minutes", example: "3",
            help: qsTr("Counts or durations in whole units, without a fractional part.")},
        {value: "numeric", label: qsTr("Decimal number"), name: "weight", example: "12.5",
            help: qsTr("Measurements that need a fractional part.")},
        {value: "boolean", label: qsTr("Yes / No"), name: "has_storyboard", example: qsTr("Yes / No"),
            help: qsTr("A flag with two values, stored as true or false.")},
        {value: "timestamp", label: qsTr("Date and time"), name: "deadline", example: qsTr("Today, 14:30"),
            help: qsTr("A deadline or another date with a time.")}
    ]
    readonly property var selectedType: fieldTypes[Math.max(0, columnType.currentIndex)]

    function typeInfo(sqlType) {
        const name = String(sqlType || "").toLowerCase().split("(")[0].trim()
        if (["varchar", "character varying", "character", "char"].includes(name)) return fieldTypes[0]
        if (name === "text") return fieldTypes[1]
        if (["integer", "bigint", "smallint", "int", "int4", "int8"].includes(name)) return fieldTypes[2]
        if (["numeric", "decimal", "real", "double precision"].includes(name)) return fieldTypes[3]
        if (["boolean", "bool"].includes(name)) return fieldTypes[4]
        if (name.startsWith("timestamp")) return fieldTypes[5]
        return null
    }

    function fieldDescription(info) {
        const type = typeInfo(info.data_type)
        let parts = [type ? type.label + " · " + info.data_type : info.data_type || ""]
        if (info.character_maximum_length)
            parts.push(qsTr("Up to %1 characters").arg(info.character_maximum_length))
        if (info.is_nullable === "NO" || info.is_nullable === false)
            parts.push(qsTr("Cannot be empty in the database"))
        if (type)
            parts.push(qsTr("Example value: %1").arg(type.example))
        return parts.join("\n")
    }

    function removalReason(name) {
        switch ((root.controller.metadata.columnRemovalBlocks || {})[name]) {
        case "identity": return qsTr("Object identifier. This field cannot be deleted.")
        case "tactic": return qsTr("Required by TACTIC. This field cannot be deleted.")
        case "schema": return qsTr("Used by a schema relationship. Change the relationship before deleting this field.")
        case "system_type": return qsTr("Columns of system and config Search Types cannot be deleted here.")
        default: return ""
        }
    }

    spacing: 16

    ConfigurationSection {
        objectName: "adminAutomaticFields"
        Layout.fillWidth: true
        visible: root.creatingType
        theme: root.theme
        title: qsTr("Default fields")
        description: qsTr("TACTIC creates these columns automatically when you save the new Search Type. Do not add them again below; the draft list is only for extra fields.")
        Label {
            objectName: "adminAutomaticFieldNames"
            Layout.fillWidth: true
            text: root.automaticFields.join(", ")
            color: root.theme.primaryText
            font.pointSize: Controls.Typography.body
            wrapMode: Text.Wrap
        }
        Label {
            objectName: "adminAutomaticPipelineField"
            Layout.fillWidth: true
            Layout.topMargin: 8
            text: root.controller.document.hasPipeline
                ? qsTr("pipeline_code will also be created: pipeline support is enabled.")
                : qsTr("pipeline_code will not be created: pipeline support is disabled.")
            color: root.theme.secondaryText
            font.pointSize: Controls.Typography.label
            wrapMode: Text.WordWrap
        }
    }
    ConfigurationSection {
        Layout.fillWidth: true
        theme: root.theme
        title: qsTr("Add a field")
        description: qsTr("A field stores one attribute of each Search Object. Define its name and type here; fill in actual values when editing the objects.")
        Controls.SettingsRow {
            theme: root.theme
            title: qsTr("Field name")
            description: qsTr("A technical name: lowercase Latin letters, numbers and underscores. For example, duration_minutes. No spaces; start with a letter.")
            Controls.TextField {
                id: columnName
                objectName: "adminNewColumnName"
                Layout.preferredWidth: root.fieldWidth
                theme: root.theme
                placeholderText: root.selectedType.name
                Accessible.name: qsTr("Field name")
            }
        }
        Controls.SettingsRow {
            theme: root.theme
            title: qsTr("Field type")
            description: root.selectedType.help
            Controls.ComboBox {
                id: columnType
                objectName: "adminNewColumnType"
                Layout.preferredWidth: root.fieldWidth
                theme: root.theme
                model: root.fieldTypes
                textRole: "label"
                valueRole: "value"
                translateDisplayText: false
                Accessible.name: qsTr("Field type")
            }
        }
        Label {
            objectName: "adminNewColumnExample"
            Layout.fillWidth: true
            Layout.topMargin: 12
            text: qsTr("Example: %1 = %2").arg(columnName.text.trim() || root.selectedType.name)
                .arg(root.selectedType.example) + "\n" + qsTr("Database type: %1").arg(root.selectedType.value)
            wrapMode: Text.Wrap
            color: root.theme.secondaryText
            font.pointSize: Controls.Typography.label
        }
        Controls.Button {
            objectName: "adminStageColumn"
            Layout.topMargin: 12
            theme: root.theme
            text: qsTr("Add to draft")
            icon.name: "add"
            onClicked: {
                if (root.controller.add_column(columnName.text, columnType.currentValue))
                    columnName.clear()
            }
        }
    }
    ConfigurationSection {
        Layout.fillWidth: true
        visible: (root.controller.document.columns || []).length > 0
        theme: root.theme
        title: (root.creatingType ? qsTr("Additional fields to create (%1)") : qsTr("Fields to create (%1)"))
            .arg((root.controller.document.columns || []).length)
        description: qsTr("These fields exist only in your draft. Save to server creates them; removing a draft field does not change the database.")
        Repeater {
            model: root.controller.document.columns || []
            delegate: Controls.SettingsRow {
                required property var modelData
                required property int index
                theme: root.theme
                title: modelData.name
                description: root.fieldDescription({data_type: modelData.type})
                Controls.CompactIconButton {
                    objectName: "adminRemoveColumn_" + modelData.name
                    theme: root.theme
                    iconName: "delete"
                    toolTip: qsTr("Remove staged field")
                    onClicked: root.controller.remove_column(index)
                }
            }
        }
    }
    ConfigurationSection {
        Layout.fillWidth: true
        visible: !!root.controller.identity
        theme: root.theme
        title: qsTr("Existing fields (%1)").arg(Object.keys(root.controller.metadata.columns || {}).length)
        description: qsTr("Delete marks a field for removal. You can undo the mark before saving. Confirming Save deletes the column and all its values; field types are not changed here.")
        Controls.TextField {
            id: fieldSearch
            objectName: "adminExistingFieldsFilter"
            Layout.fillWidth: true
            Layout.bottomMargin: 8
            theme: root.theme
            placeholderText: qsTr("Find a field")
        }
        Repeater {
            model: root.visible ? Object.keys(root.controller.metadata.columns || {}).filter(
                name => name.toLowerCase().includes(fieldSearch.text.toLowerCase())) : []
            delegate: Controls.SettingsRow {
                id: existingField
                required property string modelData
                readonly property bool marked: (root.controller.document.removedColumns || []).includes(modelData)
                readonly property string protectedReason: root.removalReason(modelData)
                objectName: "adminExistingField_" + modelData
                theme: root.theme
                title: modelData
                description: marked
                    ? qsTr("Marked for deletion. The column and its data will be deleted when you save.")
                    : root.fieldDescription(root.controller.metadata.columns[modelData])
                        + (protectedReason ? "\n" + protectedReason : "")
                Controls.Button {
                    objectName: "adminDeleteColumn_" + existingField.modelData
                    theme: root.theme
                    compact: true
                    flat: true
                    destructive: !existingField.marked && !existingField.protectedReason
                    icon.name: existingField.marked ? "undo" : existingField.protectedReason ? "lock" : "delete"
                    text: existingField.marked ? qsTr("Undo field deletion") : qsTr("Delete field")
                    toolTip: existingField.protectedReason || text
                    enabled: !root.controller.busy && root.controller.canWrite
                        && (existingField.marked || !existingField.protectedReason)
                    onClicked: root.controller.set_column_removed(existingField.modelData, !existingField.marked)
                }
            }
        }
    }
}

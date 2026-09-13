pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

ColumnLayout {
    id: root

    required property var theme
    required property var controller
    readonly property var editor: controller.connectionEditor
    readonly property var edge: editor.edge
    readonly property bool hasEdge: controller.selectedEdge >= 0
    readonly property bool pendingInstance: editor.instance.length > 0
    readonly property bool narrow: width < root.theme.controlHeight * 9 + 10

    spacing: 10
    enabled: controller.canWrite && !controller.busy
    onVisibleChanged: if (visible) editor.load_columns()
    Component.onCompleted: if (visible) editor.load_columns()

    Connections {
        target: root.editor
        function onChanged() { if (root.visible) root.editor.load_columns() }
    }
    Controls.SectionLabel {
        Layout.fillWidth: true
        theme: root.theme
        text: root.pendingInstance ? qsTr("Many-to-many · new Search Type") : qsTr("Relationship type")
        wrapMode: Text.WordWrap
    }
    Controls.SegmentedButton {
        objectName: "schemaRelationshipType"
        Layout.fillWidth: true
        visible: root.hasEdge && !root.pendingInstance
        theme: root.theme
        currentValue: root.edge.relationship || "code"
        model: [
            {value: "code", label: "code"},
            {value: "many_to_many", label: "many_to_many", enabled: root.edge.from !== "*" && root.edge.to !== "*"}
        ]
        onActivated: value => {
            root.forceActiveFocus()
            if (value === "many_to_many") root.editor.make_many_to_many()
            else root.controller.set_attribute("relationship", value)
        }
    }
    Label {
        Layout.fillWidth: true
        visible: root.pendingInstance
        text: qsTr("This is a draft. The instance table and its key columns will be created only when you save the schema.")
        color: root.theme.secondaryText
        font.family: root.theme.fontFamily
        font.pointSize: Controls.Typography.label
        wrapMode: Text.WordWrap
    }
    Controls.TextField {
        objectName: "schemaInstanceTableName"
        Layout.fillWidth: true
        visible: root.pendingInstance
        theme: root.theme
        text: root.editor.instance.split("/").pop()
        placeholderText: qsTr("Instance table name")
        Accessible.name: qsTr("Instance table name")
        onEditingFinished: if (text !== root.editor.instance.split("/").pop()) root.editor.rename_instance(text)
    }
    Repeater {
        model: root.pendingInstance && !root.hasEdge ? root.editor.instanceLinks : []
        delegate: Controls.EditorListItem {
            required property var modelData
            objectName: "schemaInstanceLink_" + modelData.to
            Layout.fillWidth: true
            theme: root.theme
            text: modelData.to
            description: modelData.from_col + " → " + modelData.to_col
            iconName: "link"
            onClicked: {
                root.forceActiveFocus()
                root.controller.select_edge(modelData.edgeIndex)
            }
        }
    }
    Controls.Button {
        objectName: "schemaRestoreDirect"
        Layout.fillWidth: true
        visible: root.pendingInstance
        theme: root.theme
        text: qsTr("Restore direct connection")
        icon.name: "undo"
        onClicked: { root.forceActiveFocus(); root.editor.restore_direct() }
    }
    Controls.CheckBox {
        objectName: "schemaCreateColumns"
        Layout.fillWidth: true
        visible: root.hasEdge
        theme: root.theme
        text: qsTr("Create missing columns")
        checked: root.editor.createColumns
        onToggled: root.editor.set_create_columns(checked)
    }
    Label {
        Layout.fillWidth: true
        visible: root.hasEdge
        text: qsTr("Choose existing columns below, or enter a new key column name. New columns are created on schema save, using the opposite key's type.")
        color: root.theme.secondaryText
        font.family: root.theme.fontFamily
        font.pointSize: Controls.Typography.label
        wrapMode: Text.WordWrap
    }
    RowLayout {
        Layout.fillWidth: true
        visible: root.hasEdge
        Controls.Button {
            objectName: "schemaReverseConnection"
            Layout.fillWidth: true
            theme: root.theme
            text: qsTr("Reverse connection")
            icon.name: "swap-horiz"
            enabled: !root.pendingInstance
            onClicked: { root.forceActiveFocus(); root.editor.reverse() }
        }
        Controls.CompactIconButton {
            objectName: "schemaRefreshColumns"
            theme: root.theme
            iconName: "refresh"
            toolTip: qsTr("Reload columns from server")
            enabled: !root.editor.loading
            onClicked: root.editor.refresh_columns()
        }
    }
    Label {
        Layout.fillWidth: true
        visible: root.editor.loading || root.editor.error.length > 0
        text: root.editor.error || qsTr("Loading columns…")
        color: root.editor.error ? root.theme.error : root.theme.secondaryText
        font.family: root.theme.fontFamily
        font.pointSize: Controls.Typography.label
        wrapMode: Text.WordWrap
    }
    GridLayout {
        Layout.fillWidth: true
        visible: root.hasEdge
        columns: root.narrow ? 1 : 2
        columnSpacing: 10
        rowSpacing: 10
        Repeater {
            model: root.hasEdge ? ["from", "to"] : []
            delegate: ColumnLayout {
                id: endpoint

                required property string modelData
                readonly property string identity: root.edge[modelData] || ""
                readonly property string field: modelData + "_col"
                readonly property string selectedColumn: root.edge[field] || ""
                readonly property var info: (root.controller.metadata.searchTypes || []).find(row => row.identity === identity) || ({})
                readonly property var columns: root.editor.columns[identity] || []
                readonly property var tableInfo: root.editor.columnCatalog[identity] || ({})

                Layout.fillWidth: true
                Layout.minimumWidth: 0
                Layout.preferredWidth: 0
                Layout.alignment: Qt.AlignTop
                spacing: 6

                Controls.SectionLabel {
                    Layout.fillWidth: true
                    theme: root.theme
                    text: endpoint.modelData === "from" ? qsTr("From (child)") : qsTr("To (parent)")
                }
                Label {
                    Layout.fillWidth: true
                    text: endpoint.info.label ? endpoint.info.label + " · " + endpoint.identity : endpoint.identity
                    textFormat: Text.PlainText
                    color: endpoint.info.color || root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.body
                    wrapMode: Text.Wrap
                }
                Controls.TextField {
                    objectName: "schemaColumn_" + endpoint.modelData
                    Layout.fillWidth: true
                    theme: root.theme
                    text: endpoint.selectedColumn
                    Accessible.name: endpoint.modelData === "from" ? qsTr("Child key column") : qsTr("Parent key column")
                    onEditingFinished: if (text !== endpoint.selectedColumn) root.editor.set_column(endpoint.field, text)
                }
                Label {
                    objectName: "schemaMissingTable_" + endpoint.modelData
                    Layout.fillWidth: true
                    visible: endpoint.tableInfo.tableAvailable === false
                    text: qsTr("Table %1.%2 is missing. This Search Type is still referenced by the schema. Check the table on the server or correct the connection, then reload columns. No table is created automatically.")
                        .arg(endpoint.tableInfo.database || "").arg(endpoint.tableInfo.table || "")
                    textFormat: Text.PlainText
                    color: root.theme.error
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.label
                    wrapMode: Text.Wrap
                }
                ListView {
                    id: columnList
                    objectName: "schemaColumnList_" + endpoint.modelData
                    Layout.fillWidth: true
                    Layout.preferredHeight: Math.min(180, contentHeight)
                    clip: true
                    spacing: 2
                    boundsBehavior: Flickable.StopAtBounds
                    model: endpoint.columns
                    delegate: Controls.EditorListItem {
                        required property var modelData
                        objectName: "schemaColumnChoice_" + endpoint.modelData + "_" + modelData.name
                        width: Math.max(0, columnList.width - columnBar.reservedExtent - 4)
                        theme: root.theme
                        text: modelData.name
                        description: modelData.pending ? qsTr("Created on save") : modelData.type
                        selected: modelData.name === endpoint.selectedColumn
                        padding: 8
                        onClicked: {
                            root.forceActiveFocus()
                            root.editor.set_column(endpoint.field, modelData.name)
                        }
                        Controls.ToolTip {
                            theme: root.theme
                            visible: parent.hovered
                            text: parent.text + " · " + parent.description
                        }
                    }
                    ScrollBar.vertical: Controls.ScrollBar {
                        id: columnBar
                        theme: root.theme
                        flickableTarget: columnList
                    }
                }
            }
        }
    }
}

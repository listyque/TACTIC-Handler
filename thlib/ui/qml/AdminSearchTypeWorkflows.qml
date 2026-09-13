import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

ConfigurationSection {
    id: root

    required property var metadata
    signal openRequested(string identity)

    title: qsTr("Pipelines and workflow")
    description: qsTr("These pipelines are linked to this Search Type on the server. Open one to edit its processes, task settings, groups, dependencies and scripts.")
    iconName: "workflow"

    Label {
        Layout.fillWidth: true
        text: root.metadata.hasPipeline
            ? qsTr("Each Search Object selects its pipeline through the pipeline_code field.")
            : qsTr("This Search Type has no pipeline_code field. A pipeline association alone does not add it.")
        color: root.theme.secondaryText
        font.pointSize: Controls.Typography.label
        wrapMode: Text.WordWrap
    }
    Repeater {
        model: root.metadata.pipelines || []
        delegate: Controls.SettingsRow {
            required property var modelData
            theme: root.theme
            title: modelData.label
            description: (modelData.description ? modelData.description + "\n" : "")
                + qsTr("Processes: %1").arg(modelData.processCount)
                + (modelData.shared ? " · " + qsTr("Shared · read-only") : "")
            Controls.MaterialIcon {
                name: "workflow"
                size: 22
                color: modelData.color || root.theme.action
            }
            Controls.Button {
                objectName: "adminSearchTypeWorkflow_" + modelData.identity
                theme: root.theme
                text: qsTr("Open workflow")
                icon.name: "open-in-new"
                onClicked: root.openRequested(modelData.identity)
            }
        }
    }
    Controls.EmptyState {
        Layout.fillWidth: true
        visible: !(root.metadata.pipelines || []).length
        theme: root.theme
        iconName: "workflow"
        title: qsTr("No pipelines are linked to this Search Type")
        message: qsTr("Use Create workflow above. The new pipeline will already be linked to this Search Type.")
    }
}

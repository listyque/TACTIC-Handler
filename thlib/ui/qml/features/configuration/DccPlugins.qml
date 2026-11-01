import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../controls" as Controls
import "../../tactic_frame/core/foundation.mjs" as Foundation

Item {
    id: root
    required property var theme
    required property var controller

    ColumnLayout {
        anchors.fill: parent
        spacing: Foundation.spacing.compact
        Controls.SectionLabel {
            Layout.fillWidth: true
            theme: root.theme
            text: qsTr("Choose the DCC integrations used by this Handler installation.")
            wrapMode: Text.Wrap
        }
        ListView {
            id: plugins
            objectName: "dccPluginsList"
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: root.controller.rows
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            delegate: RowLayout {
                required property var modelData
                width: plugins.width - Foundation.controls.scrollBar.extent
                spacing: Foundation.spacing.compact
                Controls.EditorListItem {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    theme: root.theme
                    text: modelData.title + (modelData.version ? " · " + modelData.version : "")
                    description: modelData.error || qsTr(modelData.description)
                    onClicked: root.controller.set_enabled(modelData.id, !modelData.enabled)
                }
                Controls.CheckBox {
                    objectName: "dccPluginToggle_" + modelData.id
                    theme: root.theme
                    text: qsTr("Enabled")
                    checked: modelData.enabled
                    onToggled: root.controller.set_enabled(modelData.id, checked)
                }
            }
            ScrollBar.vertical: Controls.ScrollBar {
                theme: root.theme
            }
            Controls.SectionLabel {
                anchors.centerIn: parent
                theme: root.theme
                visible: plugins.count === 0
                text: qsTr("No DCC plugins available")
            }
        }
        Controls.SelectableText {
            Layout.fillWidth: true
            theme: root.theme
            text: root.controller.error || (root.controller.restartRequired
                  ? qsTr("Restart Handler to apply plugin changes. Active operations are preserved.")
                  : qsTr("Plugin changes apply after restarting Handler. Maya registrations are managed on the plugin page."))
        }
    }
}

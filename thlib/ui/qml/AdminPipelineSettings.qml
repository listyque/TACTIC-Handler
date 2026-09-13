import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Flickable {
    id: root

    required property var theme
    required property var controller
    readonly property real fieldWidth: Math.max(80, Math.min(280, form.width - 48))

    objectName: "adminPipelineViewport"
    clip: true
    contentWidth: width
    contentHeight: form.implicitHeight + 4
    boundsBehavior: Flickable.StopAtBounds

    ColumnLayout {
        id: form
        width: Math.max(0, root.width - scrollBar.reservedExtent - 4)

        ConfigurationSection {
            Layout.fillWidth: true
            theme: root.theme
            title: qsTr("Pipeline details")
            description: qsTr("These settings belong to the whole pipeline. Select a node on the canvas to configure that process and its task statuses.")

            Controls.SettingsRow {
                theme: root.theme
                title: qsTr("Title")
                description: qsTr("The pipeline name shown to other users.")
                Controls.TextField {
                    objectName: "adminPipelineTitle"
                    Layout.preferredWidth: root.fieldWidth
                    theme: root.theme
                    text: root.controller.document.name || ""
                    readOnly: !root.controller.canWrite
                    onTextEdited: root.controller.set_field("name", text)
                }
            }
            Controls.SettingsRow {
                theme: root.theme
                title: qsTr("Description")
                description: qsTr("Explain what this pipeline is used for.")
                Controls.TextField {
                    objectName: "adminPipelineDescription"
                    Layout.preferredWidth: root.fieldWidth
                    theme: root.theme
                    text: root.controller.document.description || ""
                    readOnly: !root.controller.canWrite
                    onTextEdited: root.controller.set_field("description", text)
                }
            }
            Controls.SettingsRow {
                theme: root.theme
                title: qsTr("Color")
                description: qsTr("The color of the entire pipeline, independent of its process colors.")
                showDivider: false
                Controls.ColorField {
                    objectName: "adminPipelineColor"
                    Layout.preferredWidth: root.fieldWidth
                    theme: root.theme
                    enabled: root.controller.canWrite
                    value: root.controller.document.color || ""
                    onColorChosen: value => root.controller.set_field("color", value)
                }
            }
        }
    }
    ScrollBar.vertical: Controls.ScrollBar {
        id: scrollBar
        theme: root.theme
        flickableTarget: root
    }
}

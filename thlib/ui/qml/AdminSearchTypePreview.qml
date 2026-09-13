import QtQuick
import QtQuick.Layouts
import "controls" as Controls

ConfigurationSection {
    id: root

    required property var controller
    title: qsTr("Search Type image")
    description: root.controller.identity
        ? qsTr("The image belongs to the Search Type itself, not to one of its Search Objects. Saving adds the replacement to Commit Queue.")
        : qsTr("You can choose an image now. After the Search Type is created, its preview will be sent through Commit Queue.")
    iconName: "icon"

    Controls.ImagePicker {
        Layout.fillWidth: true
        theme: root.theme
        objectNamePrefix: "adminSearchType"
        previewUrl: root.controller.previewUrl
        stagedPath: root.controller.document.previewPath || ""
        accent: root.controller.document.color || root.theme.action
        fallbackText: (root.controller.document.title || "").slice(0, 2)
        dialogTitle: qsTr("Choose Search Type preview")
        statusText: stagedPath.length > 0
            ? qsTr("A new preview is ready to be queued")
            : root.controller.previewQueued
            ? qsTr("Image sent to Commit Queue; track upload progress there")
            : root.controller.identity
            ? qsTr("Current Search Type preview") : qsTr("Preview is optional")
        onSelectionRequested: image => root.controller.set_preview_path(image)
    }
}

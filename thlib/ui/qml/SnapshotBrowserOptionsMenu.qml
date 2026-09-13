import QtQuick

ActionMenu {
    id: root
    required property var controller

    readonly property string contentMode:
        controller.snapshot_browser_content_mode
    readonly property bool showPreviewPanel: contentMode !== "files"
    readonly property bool showFilesPanel: contentMode !== "preview"

    actions: controller.snapshot_browser_actions()

    function refreshAndToggleBelow(sourceItem) {
        actions = controller.snapshot_browser_actions()
        toggleBelow(sourceItem)
    }

    onTriggered: command => {
        if (command === "show_all")
            controller.toggle_snapshot_browser_option("all")
        else if (command === "show_more")
            controller.toggle_snapshot_browser_option("more")
        else if (command === "content_both")
            controller.set_snapshot_browser_content_mode("both")
        else if (command === "content_preview")
            controller.set_snapshot_browser_content_mode("preview")
        else if (command === "content_files")
            controller.set_snapshot_browser_content_mode("files")
        else if (command === "horizontal")
            controller.set_snapshot_browser_orientation("horizontal")
        else if (command === "vertical")
            controller.set_snapshot_browser_orientation("vertical")
    }
}

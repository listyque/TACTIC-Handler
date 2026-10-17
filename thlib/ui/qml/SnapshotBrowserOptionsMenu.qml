import QtQuick
import "tactic_frame/features/objects/snapshot.ui.mjs" as UI

ActionMenu {
    id: root
    required property var controller

    readonly property string contentMode: controller.snapshot_browser_content_mode
    readonly property bool showPreviewPanel: contentMode !== "files"
    readonly property bool showFilesPanel: contentMode !== "preview"

    function currentActions() {
        return UI.optionActions({
            contentMode: controller.snapshot_browser_content_mode,
            imageMode: controller.snapshot_browser_image_mode,
            orientation: controller.snapshot_browser_orientation,
            showAll: controller.snapshot_browser_show_all,
            showMore: controller.snapshot_browser_show_more
        });
    }
    actions: currentActions()

    function refreshAndToggleBelow(sourceItem) {
        actions = currentActions();
        toggleBelow(sourceItem);
    }

    onTriggered: command => {
        if (command === "show_all")
            controller.toggle_snapshot_browser_option("all");
        else if (command === "show_more")
            controller.toggle_snapshot_browser_option("more");
        else if (command === "content_both")
            controller.set_snapshot_browser_content_mode("both");
        else if (command === "content_preview")
            controller.set_snapshot_browser_content_mode("preview");
        else if (command === "content_files")
            controller.set_snapshot_browser_content_mode("files");
        else if (command === "horizontal")
            controller.set_snapshot_browser_orientation("horizontal");
        else if (command === "vertical")
            controller.set_snapshot_browser_orientation("vertical");
    }
}

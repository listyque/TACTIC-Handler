import QtQuick
import QtQuick.Controls

Item {
    id: root

    required property var theme
    required property var commitQueue
    required property var screenshot
    required property var windows
    required property var selectedRecord

    signal choosePreviewRequested()
    signal managePreviewRequested()

    function openPreviewBelow(sourceItem) {
        previewActionsMenu.toggleBelow(sourceItem)
    }

    function openSendBelow(sourceItem) {
        sendActionsMenu.toggleBelow(sourceItem)
    }

    ActionMenu {
        id: previewActionsMenu
        parent: Overlay.overlay
        theme: root.theme
        actions: [
            {
                "title": "Capture screenshot", "command": "capture",
                "icon": "photo_camera",
                "enabled": Boolean(root.selectedRecord.canEdit)
            },
            {
                "title": "Choose preview images", "command": "choose",
                "icon": "add-photo-alternate",
                "enabled": Boolean(root.selectedRecord.canEdit)
            },
            {
                "title": "Paste preview image from clipboard",
                "command": "paste", "icon": "content-paste",
                "enabled": Boolean(root.selectedRecord.canEdit)
                    && root.screenshot.clipboardHasImage
            },
            {
                "title": "Manage selected previews", "command": "manage",
                "icon": "collections",
                "enabled": Number(root.selectedRecord.previewCount || 0) > 0
            },
            {"separator": true},
            {
                "title": "Clear operation previews", "command": "clear",
                "icon": "delete_sweep",
                "enabled": Boolean(root.selectedRecord.canEdit)
                    && Number(root.selectedRecord.previewCount || 0) > 0
            }
        ]
        onTriggered: function(command) {
            if (command === "capture") {
                root.screenshot.prepare_for_operation(root.commitQueue.selectedId)
                root.windows.show_child_window(
                    "screenshot_maker", "commit_queue")
            } else if (command === "choose") {
                root.choosePreviewRequested()
            } else if (command === "paste") {
                root.screenshot.paste_preview_from_clipboard(
                    root.commitQueue.selectedId)
            } else if (command === "manage") {
                root.managePreviewRequested()
            } else if (command === "clear") {
                root.commitQueue.clear_selected_previews()
            }
        }
    }

    ActionMenu {
        id: sendActionsMenu
        parent: Overlay.overlay
        theme: root.theme
        actions: [
            {
                "title": "Commit current", "command": "current",
                "icon": "publish",
                "enabled": root.commitQueue.selectedRow >= 0
                    && root.selectedRecord.status !== "Completed"
                    && Boolean(root.selectedRecord.canCommit)
            },
            {
                "title": "Commit selected", "command": "selected",
                "icon": "done_all",
                "enabled": root.commitQueue.hasCheckedReady
            }
        ]
        onTriggered: function(command) {
            if (command === "current")
                root.commitQueue.commit_current()
            else if (command === "selected")
                root.commitQueue.commit_selected()
        }
    }
}

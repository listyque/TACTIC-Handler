import QtQuick
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/knowledge/commands.ui.mjs" as UI

Frame.FrameView {
    id: root
    required property var controller
    required property bool article
    required property bool back
    required property int step
    required property bool metadataExpanded
    required property bool contentDirty
    signal command(var action)
    readonly property var presentation: ({
            kind: root.article ? "article" : "section",
            back: root.back,
            creating: controller.creating,
            step: root.step,
            metadataExpanded: root.metadataExpanded,
            selectionCount: controller.linkableSelectedObjects.length,
            busy: controller.busy,
            draft: controller.draft,
            localDraft: controller.localDraft,
            dirty: controller.dirty || root.contentDirty
        })
    scene: UI.editor(root.presentation, width, (typeof localizationController !== "undefined" ? localizationController.current_language : "en"))
    onEvent: action => root.command(action)
}

import QtQuick
import "../../../controls" as Controls
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/files/workspace/forms.ui.mjs" as UI

Controls.Dialog {
    id: root
    readonly property string language: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language

    objectName: "workspaceReviewDialog"
    required property var controller
    property string operation: "shelve"
    property var paths: []
    property var request: ({})
    readonly property var review: controller.view_data.review || ({})
    title: operation === "compare_shelf" ? qsTr("Compare pending with shelf") : ["merge_begin", "rebase_begin", "unshelve_begin"].indexOf(operation) >= 0 ? qsTr("Review integration") : qsTr("Review shelving")
    modal: true
    width: Math.max(240, Math.min(700, parent ? parent.width - 24 : 700))
    height: Math.max(180, Math.min(560, parent ? parent.height - 24 : 560))
    x: (parent.width - width) / 2
    y: (parent.height - height) / 2
    contentItem: Frame.FrameView {
        id: form
        theme: root.theme
        scene: UI.review({
            review: root.review,
            operation: root.operation,
            description: root.controller.view_data.description,
            busy: root.controller.busy
        }, width, height, root.language)
        models: ({
                reviewFiles: root.review.items || []
            })
        describeRow: (list, record) => UI.reviewFile(record, list.width - 16, root.language)
        onEvent: action => {
            if (action.type === "reject")
                root.close();
            else if (action.type === "more")
                root.controller.action("review_more", {});
            else if (action.type === "accept") {
                root.controller.action(root.operation, Object.assign({}, root.request, {
                    review_revision: String(root.review.edit_revision)
                }, root.paths.length ? {
                    paths: root.paths
                } : {}, root.review.preview_head_revision !== undefined ? {
                    preview_head_revision: String(root.review.preview_head_revision),
                    preview_source_root: root.review.preview_source_root
                } : {}));
                root.close();
            }
        }
    }
    footer: null
}

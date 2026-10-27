import QtQuick
import QtQuick.Controls
import "../../controls" as Controls
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/search/branch_filter.ui.mjs" as Filter

Frame.FrameView {
    id: root
    required property var controller
    required property string nodeId
    property string query: controller.child_filter_text(nodeId)
    onNodeIdChanged: {
        popup.close();
        query = controller.child_filter_text(nodeId);
    }
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    scene: Filter.trigger(query, language)
    onEvent: {
        query = controller.child_filter_text(nodeId);
        popup.preparePositionAtItem(root, 0, root.height + 4);
        popup.open();
    }
    function apply(value) {
        query = value;
        controller.filter_result_children(nodeId, query, Filter.matching(controller.child_filter_records(nodeId), query));
    }
    Controls.Popup {
        id: popup
        parent: Overlay.overlay
        theme: root.theme
        usePopupWindow: false
        width: 296
        height: (root.query ? 68 : 44) + 16
        padding: 8
        onOpened: Qt.callLater(() => panel.focusControl("branchSearchText"))
        contentItem: Frame.FrameView {
            id: panel
            theme: root.theme
            scene: Filter.panel({
                query: root.query,
                count: Filter.matching(root.controller.child_filter_records(root.nodeId), root.query).length
            }, width, root.language)
            onEvent: action => {
                if (action.type === "close")
                    popup.close();
                else
                    root.apply(action.type === "clear" ? "" : String(action.value));
            }
        }
    }
}

import QtQuick
import QtQuick.Controls
import "../../controls" as Controls
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/tasks/workspace.ui.mjs" as UI

Controls.ScrollablePopup {
    id: root
    required property var controller
    property real toolbarWidth: 0
    property string scopeIcon: "inventory-2"
    signal command(var action, var source)
    parent: Overlay.overlay
    preferredSurfaceWidth: 280
    minimumSurfaceWidth: 240
    maximumSurfaceHeight: 500
    contentSpacing: 0
    function openBelow(source) {
        openBelowItem(source, true, 6);
    }
    function toggleBelow(source) {
        toggleBelowItem(source, true, 6);
    }
    Frame.FrameView {
        objectName: "taskWorkspaceOptionsFrame"
        width: parent.width
        height: scene.height
        theme: root.theme
        scene: UI.options({
            toolbarWidth: root.toolbarWidth,
            view: root.controller.viewMode === "list" ? "table" : "gantt",
            sort: root.controller.sortMode,
            sortOptions: root.controller.sortOptions,
            descending: root.controller.sortDescending,
            group: root.controller.groupMode,
            groupOptions: root.controller.groupOptions,
            pageSize: root.controller.advancedPageSize,
            scopeIcon: root.scopeIcon,
            busy: root.controller.advancedBusy || root.controller.advancedSaving,
            blocked: root.controller.advancedBusy || root.controller.advancedSaving,
            filtersActive: root.controller.advancedFiltersActive
        }, width, typeof localizationController === "undefined" ? "en" : localizationController.current_language)
        onEvent: (action, source) => {
            if (action.type === "mode")
                root.controller.set_view_mode(action.value === "table" ? "list" : action.value);
            else if (action.type === "sort")
                root.controller.set_sort_mode(action.value);
            else if (action.type === "descending")
                root.controller.set_sort_descending(action.value);
            else if (action.type === "group")
                root.controller.set_group_mode(action.value);
            else if (action.type === "page-size")
                root.controller.set_advanced_page_size(Number(action.value));
            else if (action.type === "clear-filters")
                root.controller.reset_filters();
            else {
                root.close();
                root.command(action, source);
            }
        }
    }
}

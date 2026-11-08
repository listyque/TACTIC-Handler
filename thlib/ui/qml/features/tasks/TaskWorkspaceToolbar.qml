import QtQuick
import "../.."
import "../../controls" as Controls
import "../../tactic_frame" as Frame
import "../../tactic_frame/core/foundation.mjs" as Foundation
import "../../tactic_frame/features/tasks/workspace.ui.mjs" as UI

Frame.FrameView {
    id: root
    property bool embedded: false
    required property var controller
    required property string scopeLabel
    required property string scopeIcon
    required property string searchTypeLabel
    required property string selectedIcon
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var createBounds: scene.createBounds
    signal command(var action, var source)
    objectName: "taskWorkspaceToolbar"
    implicitHeight: scene.height
    scene: UI.toolbar({
        embedded: root.embedded,
        controlHeight: root.theme.controlHeight,
        scopeTextWidth: scopeMetrics.advanceWidth(root.scopeLabel),
        scope: controller.personalScope ? "user" : ["object", "multiple"].includes(controller.advancedScope) ? "selected" : controller.advancedScope,
        scopeLabel: root.scopeLabel,
        scopeIcon: root.scopeIcon,
        personal: controller.personalScope,
        searchTypeTitle: controller.searchTypeScopeName,
        searchTypeAvailable: controller.searchTypeScopeAvailable,
        selectedIcon: root.selectedIcon,
        blocked: controller.advancedBusy || controller.advancedSaving,
        busy: controller.advancedBusy || controller.advancedSaving,
        canCreate: controller.canCreateAdvancedTask && !controller.advancedBusy && !controller.advancedSaving,
        canManageMilestones: typeof appController === "undefined" || appController.can_manage_tools,
        canRefresh: !controller.advancedBusy && !controller.advancedSaving && controller.advancedDirtyCount === 0,
        filtersActive: controller.advancedFiltersActive,
        sort: controller.sortMode,
        sortOptions: controller.sortOptions,
        group: controller.groupMode,
        groupOptions: controller.groupOptions
    }, width, language)
    views: ({
            search: {
                component: searchPort
            },
            surfaces: {
                component: surfacePort
            }
        })
    onEvent: (action, source) => {
        if (action.type === "create")
            controller.create_advanced_task_draft();
        else if (action.type === "refresh")
            controller.reload_advanced();
        else if (action.type === "clear-filters")
            controller.reset_filters();
        else if (action.type === "sort")
            controller.set_sort_mode(action.value);
        else if (action.type === "group")
            controller.set_group_mode(action.value);
        else if (action.type === "scope-choice" && action.value !== "team") {
            if (action.value === "selected")
                controller.use_current_object();
            else if (action.value === "search_type")
                controller.use_current_search_type();
            else if (action.value === "project")
                controller.use_project();
            else if (action.value === "user")
                controller.open_for_user("");
        } else
            root.command(action, source);
    }
    FontMetrics {
        id: scopeMetrics
        font.family: root.theme.fontFamily
        font.pixelSize: Foundation.textStyles.body
        font.weight: Font.DemiBold
        font.hintingPreference: Font.PreferVerticalHinting
    }
    Component {
        id: searchPort
        Controls.SearchField {
            theme: root.theme
            placeholderText: qsTr("Search tasks")
            text: String(root.controller.advancedFilters.text || "")
            onSearchEdited: query => root.controller.set_filter("text", query)
        }
    }
    Component {
        id: surfacePort
        TaskWorkspaceSurfaceSwitcher {
            theme: root.theme
            enabled: !root.controller.advancedSaving
        }
    }
}

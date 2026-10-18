import QtQuick
import QtQuick.Controls
import "controls" as Controls
import "tactic_frame" as Frame
import "tactic_frame/features/tasks/filters.ui.mjs" as UI
import "tactic_frame/core/foundation.mjs" as Foundation

Controls.ScrollablePopup {
    id: root
    property bool advanced: false
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    parent: Overlay.overlay
    preferredSurfaceWidth: 440
    minimumSurfaceWidth: 280
    maximumSurfaceHeight: 400
    contentSpacing: 0
    function openBelow(sourceItem) {
        root.openBelowItem(sourceItem, true, 6);
    }
    function toggleBelow(sourceItem) {
        root.toggleBelowItem(sourceItem, true, 6);
    }
    function command(action) {
        if (action.type === "clear") {
            tasksController.reset_filters();
            root.close();
        } else if (action.type === "quick")
            tasksController.toggle_quick_filter(action.group, action.value);
        else if (action.type === "clear-group")
            tasksController.clear_quick_filter_group(action.group);
        else if (action.type === "advanced")
            root.advanced = !root.advanced;
        else if (action.type === "filter")
            tasksController.set_filter(action.field, action.value);
    }
    FontMetrics {
        id: chipMetrics
        font.family: root.theme.fontFamily
        font.pixelSize: Foundation.textStyles.body
        font.weight: Font.DemiBold
    }
    Frame.FrameView {
        width: parent.width
        height: scene.height
        theme: root.theme
        scene: UI.describe({
            groups: tasksController.quickFilterGroups,
            filters: tasksController.advancedFilters,
            active: tasksController.advancedFiltersActive,
            busy: tasksController.advancedBusy || tasksController.advancedSaving,
            advanced: root.advanced
        }, width, root.language, text => chipMetrics.advanceWidth(text))
        views: ({
                chip: {
                    component: chipPort,
                    nodeProps: true
                }
            })
        onEvent: action => root.command(action)
    }
    Component {
        id: chipPort
        QuickFilterChip {
            property var frameNode: ({
                    record: {},
                    action: {}
                })
            theme: root.theme
            objectName: frameNode.id || ""
            text: frameNode.record.text || ""
            checked: !!frameNode.record.selected
            accent: frameNode.record.accent || root.theme.action
            showAccentMarker: !!frameNode.marker
            subtle: showAccentMarker
            enabled: !!frameNode.enabled
            maximumChipWidth: width
            onClicked: root.command(frameNode.action)
        }
    }
}

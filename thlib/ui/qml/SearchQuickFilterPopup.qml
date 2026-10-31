import QtQuick
import "tactic_frame" as Frame
import "tactic_frame/features/search/popups.ui.mjs" as UI
import QtQuick.Controls
import "controls" as Controls

Controls.ScrollablePopup {
    id: root

    required property var controller
    required property var editorController
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    property var groups: []
    property string groupKey: ""
    property var availableGroups: null
    property bool layoutReady: false
    readonly property real rowWidth: Math.max(0, viewport.width - verticalScrollBar.reservedExtent)

    signal editRequested
    signal assigneesRequested

    function toggleBelow(sourceItem, key = "") {
        if (opened && groupKey !== key)
            close();
        groupKey = key;
        editorController.ensure_current();
        toggleBelowItem(sourceItem, !key, 6);
    }

    function updateGroups() {
        layoutReady = false;
        const source = availableGroups === null ? controller.quick_filter_groups : availableGroups;
        groups = source.filter(group => !groupKey || group.key === groupKey);
        // Set group positions before creating viewport chips. Otherwise all
        // groups initially sit at y=0 and appear to intersect the viewport.
        for (let i = 0; i < groupSlots.count; ++i)
            groupSlots.itemAt(i).forceLayout();
        filterColumn.forceLayout();
        layoutReady = true;
    }

    function optionsForGroup(group) {
        const all = {
            key: "",
            title: qsTr("ALL"),
            accent: group.accent,
            selected: group.allSelected
        };
        if (!group.userPicker)
            return [all].concat(group.options);
        return [all,
            {
                key: "myTasks",
                title: qsTr("MY TASKS"),
                iconName: "person",
                accent: group.accent,
                selected: group.myTasksSelected
            },
            {
                key: "users",
                title: group.selectedUserCount > 0 ? qsTr("USERS") + " / " + group.selectedUserCount : qsTr("SELECT USERS"),
                iconName: "group",
                accent: group.accent,
                selected: group.selectedUserCount > 0
            }
        ];
    }

    function focusGroup(index, direction) {
        if (index < 0 || index >= groups.length) {
            if (direction < 0 && groups.length > 0) {
                if (!root.controller.quick_filter_catalog_loading) {
                    viewport.contentY = viewport.originY;
                    header.focusControl("editQuickFiltersButton");
                } else {
                    groupSlots.itemAt(groups.length - 1).focusOptions(-1);
                }
                return;
            }
            viewport.contentY = viewport.originY;
            header.forceActiveFocus(Qt.TabFocusReason);
            header.focusControl("editQuickFiltersButton");
            return;
        }
        groupSlots.itemAt(index).focusOptions(direction);
    }

    parent: Overlay.overlay
    preferredSurfaceWidth: UI.popup.width
    minimumSurfaceWidth: UI.popup.minimumWidth
    maximumSurfaceHeight: UI.popup.maximumHeight
    contentSpacing: 0
    enter: null
    exit: null

    onAvailableGroupsChanged: if (visible)
        updateGroups()

    onAboutToShow: updateGroups()
    onClosed: {
        viewport.cancelFlick();
        layoutReady = false;
    }

    Connections {
        target: root.controller
        enabled: root.visible && root.availableGroups === null
        function onQuick_filters_changed() {
            root.updateGroups();
        }
    }

    QuickFilterChip {
        id: chipMetrics
        theme: root.theme
        visible: false
    }

    Column {
        id: filterColumn
        width: root.rowWidth
        spacing: UI.popup.groupGap

        Frame.FrameView {
            id: header
            width: parent.width
            height: scene.contentHeight
            theme: root.theme
            scene: UI.quickHeader({
                busy: root.controller.quick_filter_catalog_loading,
                loaded: true,
                count: root.controller.active_quick_filter_count,
                personalized: root.controller.quick_filter_is_personalized
            }, width, root.language)
            onEvent: action => {
                if (action.type === "reset")
                    root.controller.reset_quick_filters_to_standard();
                else if (action.type === "clear")
                    root.controller.clear_quick_filters();
                else if (action.type === "lastGroup")
                    root.focusGroup(root.groups.length - 1, -1);
                else if (action.type === "edit") {
                    root.close();
                    root.editRequested();
                }
            }
        }

        Label {
            width: parent.width
            visible: root.controller.quick_filter_catalog_loading || root.controller.quick_filter_catalog_error.length > 0
            text: root.controller.quick_filter_catalog_loading ? qsTr("Loading filters…") : qsTr(root.controller.quick_filter_catalog_error)
            color: root.controller.quick_filter_catalog_error.length > 0 ? root.theme.error : root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
            wrapMode: Text.Wrap
        }

        Repeater {
            id: groupSlots
            objectName: "quickFilterGroups"
            // Keep current group/viewport controls when the popup closes or
            // selection changes. Hidden updates never read the catalog.
            model: root.groups.length
            delegate: Column {
                id: groupColumn
                required property int index
                readonly property var group: root.groups[index]
                width: filterColumn.width
                spacing: UI.popup.optionGap

                function focusOptions(direction) {
                    optionsFlow.focusOption(direction > 0 ? 0 : optionsFlow.options.length - 1);
                }

                Frame.FrameView {
                    width: parent.width
                    height: UI.popup.titleHeight
                    theme: root.theme
                    scene: UI.groupHeader(groupColumn.group.source === "task" ? qsTr(String(groupColumn.group.title)) : String(groupColumn.group.title), width)
                }
                QuickFilterOptions {
                    id: optionsFlow
                    width: parent.width
                    theme: root.theme
                    options: root.optionsForGroup(groupColumn.group)
                    viewport: root.viewport
                    contentTop: filterColumn.y + groupColumn.y + y
                    sizingChip: chipMetrics
                    presentationActive: root.visible
                    viewportReady: root.layoutReady
                    onFocusAdjacent: direction => root.focusGroup(groupColumn.index + direction, direction)
                    onActivated: optionIndex => {
                        const key = options[optionIndex].key;
                        if (groupColumn.group.userPicker && key === "users") {
                            root.close();
                            root.assigneesRequested();
                        } else if (groupColumn.group.userPicker && key === "myTasks") {
                            root.controller.toggle_my_tasks_filter();
                        } else {
                            root.controller.toggle_quick_filter(groupColumn.group.key, key);
                        }
                    }
                }
            }
        }
    }
}

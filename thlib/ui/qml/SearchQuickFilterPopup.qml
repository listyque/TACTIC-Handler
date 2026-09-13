import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Controls.ScrollablePopup {
    id: root

    required property var controller
    required property var editorController
    property var groups: []
    property bool layoutReady: false
    readonly property real rowWidth: Math.max(
        0, viewport.width - verticalScrollBar.reservedExtent
    )

    signal editRequested()
    signal assigneesRequested()

    function toggleBelow(sourceItem) {
        editorController.ensure_current()
        toggleBelowItem(sourceItem, true, 6)
    }

    function updateGroups() {
        layoutReady = false
        groups = controller.quick_filter_groups
        // Set group positions before creating viewport chips. Otherwise all
        // groups initially sit at y=0 and appear to intersect the viewport.
        for (let i = 0; i < groupSlots.count; ++i)
            groupSlots.itemAt(i).forceLayout()
        filterColumn.forceLayout()
        layoutReady = true
    }

    function optionsForGroup(group) {
        const all = {key: "", title: qsTr("ALL"), accent: group.accent,
            selected: group.allSelected}
        if (!group.userPicker)
            return [all].concat(group.options)
        return [all, {
            key: "myTasks", title: qsTr("MY TASKS"), iconName: "person",
            accent: group.accent, selected: group.myTasksSelected,
        }, {
            key: "users", title: group.selectedUserCount > 0
                ? qsTr("USERS") + " / " + group.selectedUserCount : qsTr("SELECT USERS"),
            iconName: "group", accent: group.accent, selected: group.selectedUserCount > 0,
        }]
    }

    function focusGroup(index, direction) {
        if (index < 0 || index >= groups.length) {
            if (direction < 0 && groups.length > 0) {
                if (editButton.visible && editButton.enabled) {
                    viewport.contentY = viewport.originY
                    editButton.forceActiveFocus(Qt.BacktabFocusReason)
                } else {
                    groupSlots.itemAt(groups.length - 1).focusOptions(-1)
                }
                return
            }
            viewport.contentY = viewport.originY
            header.forceActiveFocus(Qt.TabFocusReason)
            header.nextItemInFocusChain(direction > 0).forceActiveFocus(Qt.TabFocusReason)
            return
        }
        groupSlots.itemAt(index).focusOptions(direction)
    }

    parent: Overlay.overlay
    preferredSurfaceWidth: 440
    minimumSurfaceWidth: 280
    maximumSurfaceHeight: 400
    contentSpacing: 0
    enter: null
    exit: null

    onAboutToShow: updateGroups()
    onClosed: {
        viewport.cancelFlick()
        layoutReady = false
    }

    Connections {
        target: root.controller
        enabled: root.visible
        function onQuick_filters_changed() {
            root.updateGroups()
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
        spacing: 16

        RowLayout {
            id: header
            width: parent.width
            height: root.theme.controlHeight
            spacing: 8
            Label {
                Layout.fillWidth: true
                text: qsTr("QUICK FILTERS")
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pixelSize: 12
                font.weight: Font.DemiBold
                wrapMode: Text.Wrap
            }
            Controls.CompactIconButton {
                objectName: "restoreStandardQuickFiltersButton"
                visible: root.controller.quick_filter_is_personalized
                theme: root.theme
                iconName: "restart_alt"
                iconSize: 16
                toolTip: qsTr("Apply the shared default to this tab")
                onClicked: root.controller.reset_quick_filters_to_standard()
            }
            Controls.CompactIconButton {
                objectName: "resetSearchQuickFiltersButton"
                visible: root.controller.active_quick_filter_count > 0
                theme: root.theme
                iconName: "close"
                iconSize: 14
                toolTip: qsTr("Clear quick filters")
                onClicked: root.controller.clear_quick_filters()
            }
            Controls.Button {
                id: editButton
                objectName: "editQuickFiltersButton"
                theme: root.theme
                text: qsTr("Edit")
                icon.name: "edit"
                tonal: true
                Keys.onBacktabPressed: event => {
                    root.focusGroup(root.groups.length - 1, -1)
                    event.accepted = true
                }
                onClicked: {
                    root.close()
                    root.editRequested()
                }
            }
        }

        Label {
            width: parent.width
            visible: root.controller.quick_filter_catalog_loading
                || root.controller.quick_filter_catalog_error.length > 0
            text: root.controller.quick_filter_catalog_loading ? qsTr("Loading filters…")
                : qsTr(root.controller.quick_filter_catalog_error)
            color: root.controller.quick_filter_catalog_error.length > 0
                ? root.theme.error : root.theme.secondaryText
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
                spacing: 9

                function focusOptions(direction) {
                    optionsFlow.focusOption(direction > 0 ? 0 : optionsFlow.options.length - 1)
                }

                Label {
                    width: parent.width
                    text: groupColumn.group.source === "task"
                        ? qsTr(String(groupColumn.group.title)) : String(groupColumn.group.title)
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.bodyLarge
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
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
                        const key = options[optionIndex].key
                        if (groupColumn.group.userPicker && key === "users") {
                            root.close()
                            root.assigneesRequested()
                        } else if (groupColumn.group.userPicker && key === "myTasks") {
                            root.controller.toggle_my_tasks_filter()
                        } else {
                            root.controller.toggle_quick_filter(groupColumn.group.key, key)
                        }
                    }
                }
            }
        }
    }
}

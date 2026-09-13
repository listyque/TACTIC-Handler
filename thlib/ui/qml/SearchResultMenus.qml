import QtQuick
import QtQuick.Controls

Item {
    id: root

    required property var theme
    required property var application
    required property var filterController
    required property var presets
    property int presetRevision: 0
    readonly property bool sortOpened: sortMenu.opened
    readonly property bool groupOpened: groupMenu.opened

    signal processFilterRequested()
    signal searchEditorRequested()

    function openFilters(sourceItem) {
        root.filterController.sync_search_session()
        ++root.presetRevision
        filtersMenu.openBelow(sourceItem)
    }

    function openSort(sourceItem) {
        sortMenu.openBelow(sourceItem)
    }

    function openGroup(sourceItem) {
        groupMenu.openBelow(sourceItem)
    }

    function resultFilterMenuActions() {
        const revision = root.presetRevision
        const source = root.application.menu_actions("result_filters")
        const actions = []
        for (let index = 0; index < source.length; ++index)
            actions.push(source[index])
        actions.push({ "separator": true })
        actions.push({ "title": "Saved searches", "header": true })
        const count = root.presets.count()
        if (count === 0) {
            actions.push({
                "title": root.filterController.busy
                    ? "Loading saved searches..." : "No saved searches",
                "icon": root.filterController.busy ? "hourglass_empty" : "save",
                "command": "",
                "enabled": false
            })
        } else {
            for (let row = 0; row < count; ++row) {
                const preset = root.presets.get(row)
                actions.push({
                    "title": preset.title || "Saved search",
                    "translate": false,
                    "icon": "save",
                    "command": "preset:" + row,
                    "checked": row === root.filterController.selected_preset
                })
            }
        }
        actions.push({ "separator": true })
        actions.push({
            "title": "Refresh saved searches",
            "icon": "refresh",
            "command": "refresh_presets",
            "enabled": !root.filterController.busy
        })
        return actions
    }

    Connections {
        target: root.presets
        enabled: filtersMenu.opened
        function onContentReplaced() { ++root.presetRevision }
    }
    Connections {
        target: root.filterController
        enabled: filtersMenu.opened
        function onStateChanged() { ++root.presetRevision }
    }
    ActionMenu {
        id: filtersMenu
        objectName: "searchResultFiltersMenu"
        parent: Overlay.overlay
        theme: root.theme
        preferredWidth: 300
        actions: root.resultFilterMenuActions()
        onTriggered: command => {
            if (command === "filter_processes")
                root.processFilterRequested()
            else if (command === "advanced_search")
                root.searchEditorRequested()
            else if (command === "refresh_presets")
                root.filterController.load_presets()
            else if (command.indexOf("preset:") === 0) {
                const row = Number(command.slice("preset:".length))
                root.filterController.select_preset_for_current_search(row)
                root.application.apply_search_filters()
            }
        }
    }
    ActionMenu {
        id: sortMenu
        objectName: "searchResultSortMenu"
        parent: Overlay.overlay
        theme: root.theme
        actions: root.application.result_sort_actions
        onTriggered: command => root.application.set_result_sort_mode(command)
    }
    ActionMenu {
        id: groupMenu
        objectName: "searchResultGroupMenu"
        parent: Overlay.overlay
        theme: root.theme
        preferredWidth: 280
        actions: root.application.result_group_actions
        onTriggered: command => root.application.set_result_group_mode(command)
    }
}

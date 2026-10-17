import QtQuick
import QtQuick.Controls
import "controls" as Controls
import "tactic_frame" as Frame
import "tactic_frame/features/search/menus.ui.mjs" as UI

Item {
    id: root

    required property var theme
    required property var application
    required property var filterController
    required property var presets
    property var columnsModel: null
    property int presetRevision: 0
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    readonly property var sortActions: UI.sortActions({
        mode: root.application.result_sort_mode,
        busy: root.application.search_state === "loading"
    })
    readonly property var groupActions: {
        const processes = [];
        for (const action of root.application.result_group_actions)
            if (action.command && action.command.indexOf("task_status:") === 0)
                processes.push({
                    key: action.command.slice(12),
                    title: action.title,
                    accent: action.accent
                });
        const selected = root.application.result_group_actions.find(action => action.checked);
        return UI.groupActions({
            mode: selected ? selected.command : "none",
            processes: processes,
            busy: root.application.search_state === "loading"
        });
    }
    readonly property bool sortOpened: sortMenu.opened
    readonly property bool groupOpened: groupMenu.opened

    signal processFilterRequested
    signal searchEditorRequested

    function openFilters(sourceItem) {
        root.filterController.sync_search_session();
        ++root.presetRevision;
        filtersMenu.openBelow(sourceItem);
    }

    function openSort(sourceItem) {
        sortMenu.openBelow(sourceItem);
    }

    function openGroup(sourceItem) {
        groupMenu.openBelow(sourceItem);
    }

    function resultFilterMenuActions() {
        const revision = root.presetRevision;
        const presets = [];
        for (let index = 0; index < root.presets.count(); index++)
            presets.push(root.presets.get(index));
        return UI.filterActions({
            base: root.application.menu_actions("result_filters"),
            presets: presets,
            selected: presets[root.filterController.selected_preset] ? presets[root.filterController.selected_preset].view : "",
            busy: root.filterController.busy
        });
    }

    function sortCommand(command, source) {
        if (command !== "column") {
            root.application.set_result_sort_mode(command);
            return;
        }
        const match = /^column:([A-Za-z_][A-Za-z0-9_]*):(asc|desc)$/.exec(root.application.result_sort_mode);
        const standard = UI.sorts.find(item => item.value === root.application.result_sort_mode);
        sortColumn.column = match ? match[1] : standard ? standard.column : "name";
        sortColumn.direction = match ? match[2] : standard ? standard.direction : "asc";
        sortColumn.openBelowItem(source, false, 4);
    }
    Controls.ScrollablePopup {
        id: sortColumn
        objectName: "searchSortColumnPopup"
        parent: Overlay.overlay
        theme: root.theme
        property string column: "name"
        property string direction: "asc"
        readonly property var columnOptions: {
            const options = [];
            for (let index = 0; index < (root.columnsModel ? root.columnsModel.count() : 0); index++) {
                const option = root.columnsModel.get(index);
                if (option.value && option.value.charAt(0) !== "_")
                    options.push(option);
            }
            return options;
        }
        preferredSurfaceWidth: 280
        minimumSurfaceWidth: 240
        maximumSurfaceHeight: 240
        Frame.FrameView {
            id: sortColumnContent
            theme: root.theme
            width: parent.width
            height: 156
            scene: UI.sortColumn({
                column: sortColumn.column,
                direction: sortColumn.direction,
                columns: sortColumn.columnOptions,
                busy: root.application.search_state === "loading"
            }, width, root.language)
            onEvent: action => {
                if (action.type === "column")
                    sortColumn.column = action.value;
                else if (action.type === "direction")
                    sortColumn.direction = sortColumn.direction === "asc" ? "desc" : "asc";
                else if (action.type === "apply" && sortColumn.column) {
                    root.application.set_result_sort_mode("column:" + sortColumn.column + ":" + sortColumn.direction);
                    sortColumn.close();
                }
            }
        }
        onOpened: sortColumnContent.focusControl("searchSortColumn")
    }
    Connections {
        target: root.presets
        enabled: filtersMenu.opened
        function onContentReplaced() {
            ++root.presetRevision;
        }
    }
    Connections {
        target: root.filterController
        enabled: filtersMenu.opened
        function onStateChanged() {
            ++root.presetRevision;
        }
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
                root.processFilterRequested();
            else if (command === "advanced_search")
                root.searchEditorRequested();
            else if (command === "refresh_presets")
                root.filterController.load_presets();
            else if (command.indexOf("preset:") === 0) {
                const view = command.slice("preset:".length);
                for (let index = 0; index < root.presets.count(); index++)
                    if (root.presets.get(index).view === view) {
                        root.filterController.select_preset_for_current_search(index);
                        root.application.apply_search_filters();
                        break;
                    }
            }
        }
    }
    ActionMenu {
        id: sortMenu
        objectName: "searchResultSortMenu"
        parent: Overlay.overlay
        theme: root.theme
        actions: root.sortActions
        onTriggered: command => root.sortCommand(command, sortMenu.lastSourceItem)
    }
    ActionMenu {
        id: groupMenu
        objectName: "searchResultGroupMenu"
        parent: Overlay.overlay
        theme: root.theme
        preferredWidth: 280
        actions: root.groupActions
        onTriggered: command => root.application.set_result_group_mode(command)
    }
}

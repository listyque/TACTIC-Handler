import QtQuick
import QtQuick.Controls
import "controls" as Controls
import "tactic_frame" as Frame
import "features/search" as Search
import "tactic_frame/features/search/conditions.ui.mjs" as UI
import "tactic_frame/features/search/editors.ui.mjs" as Editors

Item {
    id: root

    required property var theme
    readonly property bool presentationActive: parent ? parent.visible : visible
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    property bool filtersExpanded: true
    readonly property bool compactLayout: width < 560

    function columnIndex(value) {
        for (let row = 0; row < filterColumnModel.count(); ++row) {
            if (filterColumnModel.get(row).value === value)
                return row;
        }
        return -1;
    }

    function reloadPresetsForCurrentSearch() {
        if (!root.presentationActive)
            return;
        Qt.callLater(function () {
            if (!root.presentationActive)
                return;
            filterEditorController.sync_search_session();
        });
    }

    Component.onCompleted: reloadPresetsForCurrentSearch()

    onPresentationActiveChanged: reloadPresetsForCurrentSearch()

    Connections {
        target: appController
        enabled: root.presentationActive
        function onProject_changed() {
            root.reloadPresetsForCurrentSearch();
        }
        function onSection_state_changed() {
            root.reloadPresetsForCurrentSearch();
        }
    }

    Controls.DockWorkspaceFooter {
        anchors.fill: parent
        theme: root.theme
        topDividerVisible: false
        color: root.theme.surfaceContainerLow
    }

    Flickable {
        id: searchFlickable
        anchors.fill: parent
        clip: true
        contentWidth: width
        contentHeight: searchCards.implicitHeight + 20
        boundsBehavior: Flickable.StopAtBounds

        Column {
            id: searchCards
            x: 10
            y: 10
            width: Math.max(0, searchFlickable.width - 20 - searchScrollBar.reservedExtent)
            spacing: 10

            SearchPresetBar {
                width: parent.width
                theme: root.theme
                controller: filterEditorController
                application: appController
                presets: filterPresetModel
            }

            Column {
                width: parent.width
                spacing: 0
                Frame.FrameView {
                    width: parent.width
                    height: 57
                    theme: root.theme
                    scene: ({
                            nodes: UI.describe({
                                rows: [],
                                expanded: root.filtersExpanded,
                                busy: appController.search_state === "loading"
                            }, width, root.language).nodes.filter(node => node.y < 50)
                        })
                    onEvent: action => {
                        if (action.type === "expand")
                            root.filtersExpanded = !root.filtersExpanded;
                        else if (action.type === "apply")
                            appController.apply_search_filters();
                        else if (action.type === "add")
                            appController.add_search_filter();
                        else if (action.type === "reset")
                            appController.clear_search_filters();
                    }
                }
                Column {
                    width: parent.width
                    visible: root.filtersExpanded
                    height: visible ? implicitHeight + 7 : 0
                    spacing: 7
                    Repeater {
                        model: filterModel
                        delegate: Search.ConditionRow {
                            width: parent.width
                            theme: root.theme
                            application: appController
                            recordsModel: filterModel
                            columnsModel: filterColumnModel
                            suggestions: advancedFilterSuggestionModel
                            presentationActive: root.presentationActive
                        }
                    }
                }
            }
            Frame.FrameView {
                width: parent.width
                height: 68
                theme: root.theme
                scene: Editors.tabName({
                    title: appController.current_search_tab_title,
                    busy: appController.search_state === "loading"
                }, width, root.language)
                onEvent: action => {
                    if (action.type === "rename")
                        appController.set_search_tab_title(action.value);
                }
            }
        }

        ScrollBar.vertical: Controls.ScrollBar {
            id: searchScrollBar
            theme: root.theme
            flickableTarget: searchFlickable
        }
    }
}

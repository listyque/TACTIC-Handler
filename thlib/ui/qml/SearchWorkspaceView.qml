import QtQuick
import "tactic_frame" as Frame
import "tactic_frame/features/search/footer.ui.mjs" as Footer
import "tactic_frame/features/search/header.ui.mjs" as Header
import "tactic_frame/features/search/menus.ui.mjs" as SearchMenus
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "controls" as Controls
import "tactic_frame/controls/tabs/tab_layout.mjs" as TabLayout

Item {
    id: root
    required property var theme
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    required property string pageTitle
    property var columnsController: typeof columnsEditorController !== "undefined" ? columnsEditorController : null
    property var shelfController: sidebarEditorController.scriptShelf
    property var searchInput
    property var quickFilterAnchor
    property var headerMoreAnchor
    property bool shelfOpen: false
    signal requestDockMenu(var sourceItem)
    readonly property bool presentationActive: parent ? parent.visible : visible
    readonly property bool compactTabActions: width < 720
    readonly property bool inlineResultViews: !compactTabActions && SearchMenus.inlineViews(width, searchTabsView.naturalContentWidth, tabHistoryControl.visible ? 42 : 0)
    onInlineResultViewsChanged: if (resultsViewMenu)
        resultsViewMenu.close()
    readonly property var activeResultSurface: resultsArea.activeResultSurface
    property var lastTabTiming: ({})
    property bool tabTimingVisible: false
    property bool tabTimingMeasuring: false

    Component.onCompleted: appController.restore_current_result_viewport()

    Connections {
        target: appController

        function onResult_viewport_capture_requested() {
            const surface = root.activeResultSurface;
            // Reading retained coordinates is also needed after the window
            // hides, just before teardown; it does not render hidden content.
            if (surface) {
                appController.capture_current_result_viewport(surface.listContentY, surface.tileContentY);
            }
        }

        function onResult_viewport_restore_requested(listContentY, tileContentY, listValid, tileValid) {
            const surface = root.activeResultSurface;
            if (surface) {
                surface.restoreContentY(listContentY, tileContentY, listValid, tileValid);
            }
        }

        function onResult_node_reveal_requested(nodeId) {
            const surface = root.activeResultSurface;
            if (surface)
                surface.revealNode(nodeId);
        }
    }

    Connections {
        target: appController.search_tab_switch_monitor
        enabled: root.presentationActive && target.recording

        function onChanged() {
            const monitor = appController.search_tab_switch_monitor;
            const metrics = monitor.metrics || {};
            if (monitor.switching) {
                root.lastTabTiming = metrics;
                root.tabTimingMeasuring = true;
                root.tabTimingVisible = true;
                tabTimingHideTimer.stop();
                return;
            }
            if (metrics.firstFrameMs === undefined) {
                root.tabTimingVisible = false;
                return;
            }
            root.lastTabTiming = metrics;
            root.tabTimingMeasuring = false;
            root.tabTimingVisible = true;
            tabTimingHideTimer.restart();
        }
    }

    Timer {
        id: tabTimingHideTimer
        interval: 8000
        repeat: false
        onTriggered: root.tabTimingVisible = false
    }

    function timingMs(name) {
        const value = Number(root.lastTabTiming[name] || 0);
        return (Math.round(value * 10) / 10).toFixed(1);
    }

    function resultViewIcon(mode) {
        if (mode === "tiles")
            return "dashboard";
        if (mode === "compact")
            return "view-list";
        if (mode === "table")
            return "table";
        if (mode === "splitted_vertical")
            return "columns";
        if (mode === "splitted_horizontal")
            return "align-justify";
        return "list-alt";
    }

    Controls.ActivationHandler {
        onPressedChanged: {
            if (!pressed || !root.activeResultSurface)
                return;
            root.activeResultSurface.handleOutsidePress(root, point.position.x, point.position.y);
        }
    }

    Rectangle {
        id: searchHeader
        anchors.top: parent.top
        width: parent.width
        height: Header.height
        radius: Math.max(0, root.theme.surfaceRadius - 1)
        color: root.theme.panelDeep
        antialiasing: true
        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: parent.radius
            color: parent.color
        }
        Frame.FrameView {
            anchors.fill: parent
            theme: root.theme
            scene: Header.describe({
                compact: root.compactTabActions,
                shelf: Boolean(root.shelfController),
                shelfOpen: root.shelfOpen
            }, width, root.language)
            views: ({
                    field: fieldComponent,
                    tags: tagsComponent,
                    quick: quickComponent,
                    panels: panelsComponent
                })
            onEvent: action => {
                if (action.type === "refresh")
                    appController.refresh_current();
                else if (action.type === "help")
                    windowModel.open_help("search");
                else if (action.type === "shelf") {
                    root.shelfOpen = !root.shelfOpen;
                    quickFilterPopup.close();
                    tagCloudPopup.close();
                }
            }
        }
        Component {
            id: fieldComponent
            TacticSearchField {
                id: searchField
                objectName: "searchField"
                height: parent.height
                anchors.fill: parent
                Component.onCompleted: root.searchInput = this
                theme: root.theme
                suggestionModel: searchSuggestionModel
                controller: appController
                openSuggestionsInNewTab: true
                placeholderText: {
                    var scope = root.pageTitle.split("/")[0].trim();
                    return scope.length > 0 ? qsTr("Search ") + qsTr(scope).toLowerCase() : qsTr("Search");
                }
            }
        }
        Component {
            id: tagsComponent
            Controls.CompactIconButton {
                id: tagCloudButton
                objectName: "searchTagButton"
                width: parent.width
                height: parent.height
                visible: !root.compactTabActions
                theme: root.theme
                iconName: "tags"
                iconColor: tagCloudPopup.opened || appController.active_tag_count > 0 ? root.theme.action : root.theme.primaryText
                backgroundColor: tagCloudPopup.opened ? root.theme.secondaryContainer : "transparent"
                round: true
                toolTip: qsTr("Tags")
                onPressed: tagCloudPopup.sourceWasOpen = tagCloudPopup.opened
                onClicked: {
                    const opening = !tagCloudPopup.sourceWasOpen && !tagCloudPopup.opened;
                    quickFilterPopup.close();
                    if (opening)
                        appController.request_tag_cloud(false);
                    tagCloudPopup.toggleBelow(tagCloudButton);
                }

                Rectangle {
                    visible: appController.active_tag_count > 0
                    anchors.right: parent.right
                    anchors.top: parent.top
                    width: Math.max(16, tagFilterCount.implicitWidth + 8)
                    height: 16
                    radius: 8
                    color: root.theme.action
                    border.width: 2
                    border.color: root.theme.panelDeep
                    Label {
                        id: tagFilterCount
                        anchors.centerIn: parent
                        text: appController.active_tag_count
                        color: root.theme.selectedText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                        font.weight: Font.Bold
                    }
                }
            }
        }
        Component {
            id: quickComponent
            Controls.CompactIconButton {
                id: quickFilterButton
                objectName: "searchQuickFilterButton"
                width: parent.width
                height: parent.height
                visible: true
                enabled: true
                theme: root.theme
                iconName: "filter"
                iconColor: quickFilterPopup.opened || appController.active_quick_filter_count > 0 ? root.theme.action : root.theme.primaryText
                backgroundColor: quickFilterPopup.opened ? root.theme.secondaryContainer : "transparent"
                round: true
                toolTip: qsTr("Quick filters")
                onPressed: quickFilterPopup.sourceWasOpen = quickFilterPopup.opened
                Component.onCompleted: root.quickFilterAnchor = this
                onClicked: {
                    const opening = !quickFilterPopup.sourceWasOpen && !quickFilterPopup.opened;
                    tagCloudPopup.close();
                    if (opening)
                        appController.request_quick_filter_data(false);
                    quickFilterPopup.toggleBelow(quickFilterButton);
                }

                Rectangle {
                    visible: appController.active_quick_filter_count > 0
                    anchors.right: parent.right
                    anchors.top: parent.top
                    width: Math.max(16, quickFilterCount.implicitWidth + 8)
                    height: 16
                    radius: 8
                    color: root.theme.action
                    border.width: 2
                    border.color: root.theme.panelDeep
                    Label {
                        id: quickFilterCount
                        anchors.centerIn: parent
                        text: appController.active_quick_filter_count
                        color: root.theme.selectedText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.caption
                        font.weight: Font.Bold
                    }
                }
            }
        }
        Component {
            id: panelsComponent
            Controls.CompactIconButton {
                id: searchGear
                objectName: "searchHeaderOverflowButton"
                width: parent.width
                height: parent.height
                theme: root.theme
                iconName: "more-vert"
                round: true
                toolTip: root.compactTabActions ? qsTr("More search actions") : qsTr("Workspace panels")
                Component.onCompleted: root.headerMoreAnchor = this
                onPressed: searchHeaderOverflowMenu.sourceWasOpen = searchHeaderOverflowMenu.opened
                onClicked: {
                    if (!root.compactTabActions) {
                        root.requestDockMenu(root.headerMoreAnchor);
                        return;
                    }
                    quickFilterPopup.close();
                    tagCloudPopup.close();
                    searchHeaderOverflowMenu.toggleBelow(searchGear);
                }
            }
        }
    }
    ActionMenu {
        id: searchHeaderOverflowMenu
        objectName: "searchHeaderOverflowMenu"
        parent: Overlay.overlay
        theme: root.theme
        actions: [
            {
                "title": "Refresh current results",
                "icon": "refresh",
                "command": "refresh"
            },
            {
                "title": "Script shelf",
                "icon": "code",
                "command": "shelf",
                "visible": Boolean(root.shelfController),
                "checked": root.shelfOpen
            },
            {
                "title": "Tags",
                "icon": "tags",
                "command": "tags",
                "badgeCount": appController.active_tag_count
            },
            {
                "title": "Help",
                "icon": "help",
                "command": "help"
            },
            {
                "title": "Workspace panels",
                "icon": "more-vert",
                "command": "panels"
            }
        ]
        onTriggered: function (command) {
            if (command === "refresh")
                appController.refresh_current();
            else if (command === "shelf") {
                root.shelfOpen = !root.shelfOpen;
                quickFilterPopup.close();
                tagCloudPopup.close();
            } else if (command === "tags") {
                quickFilterPopup.close();
                appController.request_tag_cloud(false);
                tagCloudPopup.openBelow(root.headerMoreAnchor);
            } else if (command === "help")
                windowModel.open_help("search");
            else if (command === "panels")
                root.requestDockMenu(root.headerMoreAnchor);
        }
    }
    SearchQuickFilterPopup {
        id: quickFilterPopup
        objectName: "searchQuickFilterPopup"
        theme: root.theme
        controller: appController
        editorController: quickFilterEditorController
        onEditRequested: windowModel.show_window("quick_filter_editor")
        onAssigneesRequested: assigneeFilterPopup.openBelow(root.quickFilterAnchor)
    }
    SearchAssigneeFilterPopup {
        id: assigneeFilterPopup
        theme: root.theme
        controller: appController
    }
    TagCloudPopup {
        id: tagCloudPopup
        objectName: "searchTagCloudPopup"
        theme: root.theme
        controller: appController
        parent: Overlay.overlay
    }
    Loader {
        id: scriptShelfLoader
        objectName: "scriptShelfLoader"
        anchors.top: searchHeader.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        height: active ? 48 : 0
        active: root.shelfOpen && Boolean(root.shelfController)

        sourceComponent: Component {
            ScriptShelfBar {
                theme: root.theme
                controller: root.shelfController
            }
        }
    }
    Rectangle {
        id: searchTabs
        anchors.top: scriptShelfLoader.bottom
        width: parent.width
        height: root.theme.dockWorkspaceHeaderHeight / 2
        color: root.theme.toolBar
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 4
            anchors.rightMargin: 4
            spacing: 2

            Controls.CompactIconButton {
                id: addSearchTabButton
                Layout.preferredWidth: 40
                Layout.preferredHeight: 40
                theme: root.theme
                iconName: "add"
                round: false
                toolTip: qsTr("Add new search tab")
                onClicked: {
                    workspaceState.add_search_tab();
                    root.searchInput.beginSearchInput();
                }
            }
            Controls.CompactIconButton {
                id: tabFilterButton
                visible: !root.compactTabActions
                Layout.preferredWidth: visible ? 40 : 0
                Layout.preferredHeight: 40
                theme: root.theme
                iconName: "advanced-search"
                round: false
                toolTip: qsTr("Search filters and presets")
                onClicked: resultMenus.openFilters(tabFilterButton)
            }

            ListView {
                id: searchTabsView
                property int dragSourceIndex: -1
                property int dragTargetIndex: -1
                property real draggedTabWidth: 0
                property var naturalWidths: ({})
                property int nextNaturalWidthToken: 0
                readonly property real naturalContentWidth: {
                    let total = 0;
                    const keys = Object.keys(naturalWidths);
                    for (let i = 0; i < keys.length; ++i)
                        total += Number(naturalWidths[keys[i]].width) || 0;
                    return total;
                }
                readonly property real activeNaturalWidth: {
                    const keys = Object.keys(naturalWidths);
                    for (let i = 0; i < keys.length; ++i) {
                        const entry = naturalWidths[keys[i]];
                        if (entry.current)
                            return Number(entry.width) || 0;
                    }
                    return 0;
                }
                function allocateNaturalWidthToken() {
                    nextNaturalWidthToken += 1;
                    return nextNaturalWidthToken;
                }
                function registerNaturalWidth(key, value, token, current) {
                    const widths = Object.assign({}, naturalWidths);
                    widths[key] = {
                        "width": value,
                        "token": token,
                        "current": current
                    };
                    naturalWidths = widths;
                }
                function unregisterNaturalWidth(key, token) {
                    if (naturalWidths[key] === undefined || naturalWidths[key].token !== token)
                        return;
                    const widths = Object.assign({}, naturalWidths);
                    delete widths[key];
                    naturalWidths = widths;
                }
                function schedulePositionAtIndex(row) {
                    const stableRow = Number(row);
                    if (stableRow >= 0 && stableRow < count)
                        positionViewAtIndex(stableRow, ListView.Contain);
                }
                function allTabActions() {
                    const actions = [
                        {
                            "title": "Open search tabs",
                            "header": true
                        }
                    ];
                    for (let i = 0; i < count; ++i) {
                        const record = workspaceTabsModel.get(i);
                        actions.push({
                            "title": record.title || "Search tab",
                            "icon": "tab",
                            "command": "tab:" + i,
                            "checked": !!record.current,
                            "secondaryCommand": record.closable ? "close-tab:" + i : "",
                            "secondaryIcon": "close",
                            "secondaryToolTip": "Close search tab"
                        });
                    }
                    return actions;
                }
                function revealTab(index) {
                    const record = workspaceTabsModel.get(index);
                    if (!record || !record.entryKey)
                        return;
                    workspaceState.activate_tab(record.entryKey, record.title || "");
                    positionViewAtIndex(index, ListView.Contain);
                }
                Layout.fillWidth: true
                Layout.fillHeight: true
                orientation: ListView.Horizontal
                // ui-scrollbar: external-horizontal
                boundsBehavior: Flickable.StopAtBounds
                clip: true
                spacing: 0
                cacheBuffer: 10000
                model: workspaceTabsModel

                delegate: WorkspaceSearchTabInput {
                    id: searchTab
                    objectName: "searchTabDelegate_" + entryKey
                    identity: entryKey
                    label: title
                    selected: current
                    owner: workspaceState
                    tabsModel: workspaceTabsModel
                    tabHost: searchTabsView
                    rowIndex: index
                    required property int index
                    required property string entryKey
                    required property string title
                    required property bool closable
                    required property bool current
                    property int dragTargetIndex: index
                    property int naturalWidthToken: 0
                    readonly property real minimumTabWidth: root.compactTabActions ? 84 : 96
                    readonly property bool showClose: closable && (!root.compactTabActions || current)
                    readonly property real idealTabWidth: tabVisual.labelImplicitWidth + (showClose ? 64 : 32)
                    readonly property real naturalTabWidth: Math.max(minimumTabWidth, root.compactTabActions ? Math.min(180, idealTabWidth) : idealTabWidth)
                    readonly property real fittedTabWidth: TabLayout.fitTabWidth(naturalTabWidth, current, {
                        available: searchTabsView.width,
                        total: searchTabsView.naturalContentWidth,
                        count: searchTabsView.count,
                        activeWidth: searchTabsView.activeNaturalWidth,
                        activeCount: 1,
                        minimum: minimumTabWidth
                    })
                    property real displacedX: TabLayout.displacedTabOffset(index, searchTabsView.dragSourceIndex, searchTabsView.dragTargetIndex, searchTabsView.draggedTabWidth)

                    width: fittedTabWidth
                    height: searchTabsView.height
                    z: tabDrag.active ? 100 : 1
                    scale: tabDrag.active ? 1.03 : 1
                    opacity: 1
                    transform: Translate {
                        x: tabDrag.active ? tabDrag.translation.x : searchTab.displacedX
                        Behavior on x {
                            enabled: !tabDrag.active && searchTabsView.dragSourceIndex >= 0
                            NumberAnimation {
                                duration: theme.motionMedium
                                easing.type: Easing.OutCubic
                            }
                        }
                    }
                    Behavior on scale {
                        NumberAnimation {
                            duration: theme.motionFast
                        }
                    }

                    Component.onCompleted: {
                        naturalWidthToken = searchTabsView.allocateNaturalWidthToken();
                        searchTabsView.registerNaturalWidth(entryKey, naturalTabWidth, naturalWidthToken, current);
                    }
                    Component.onDestruction: searchTabsView.unregisterNaturalWidth(entryKey, naturalWidthToken)
                    onNaturalTabWidthChanged: searchTabsView.registerNaturalWidth(entryKey, naturalTabWidth, naturalWidthToken, current)
                    onCurrentChanged: {
                        searchTabsView.registerNaturalWidth(entryKey, naturalTabWidth, naturalWidthToken, current);
                        if (current)
                            searchTabsView.schedulePositionAtIndex(index);
                    }

                    DragHandler {
                        id: tabDrag
                        target: null
                        acceptedButtons: Qt.LeftButton
                        yAxis.enabled: false
                        onTranslationChanged: {
                            if (!active)
                                return;
                            var center = searchTab.x + searchTab.width / 2 + translation.x;
                            var target = searchTabsView.indexAt(center, searchTab.height / 2);
                            if (target < 0)
                                target = center < 0 ? 0 : searchTabsView.count - 1;
                            searchTab.dragTargetIndex = target;
                            searchTabsView.dragTargetIndex = target;
                        }
                        onActiveChanged: {
                            if (active) {
                                searchTab.dragTargetIndex = searchTab.index;
                                searchTabsView.dragSourceIndex = searchTab.index;
                                searchTabsView.dragTargetIndex = searchTab.index;
                                searchTabsView.draggedTabWidth = searchTab.width;
                            } else {
                                const sourceIndex = searchTabsView.dragSourceIndex;
                                const targetIndex = searchTabsView.dragTargetIndex;
                                searchTabsView.dragSourceIndex = -1;
                                searchTabsView.dragTargetIndex = -1;
                                searchTabsView.draggedTabWidth = 0;
                                searchTab.dragTargetIndex = searchTab.index;
                                if (sourceIndex >= 0 && targetIndex >= 0 && sourceIndex !== targetIndex)
                                    workspaceState.reorder_tab(sourceIndex, targetIndex);
                            }
                        }
                    }

                    Rectangle {
                        anchors.fill: parent
                        visible: tabDrag.active
                        color: root.theme.panelRaised
                    }
                    Controls.WorkspaceTabVisual {
                        id: tabVisual
                        z: 2
                        anchors.fill: parent
                        theme: root.theme
                        title: searchTab.title
                        current: searchTab.current
                        animateSelection: false
                        closable: searchTab.showClose
                        hovered: tabMouse.containsMouse
                        pressed: tabMouse.pressed
                        onCloseRequested: workspaceState.close_tab(searchTab.index)
                    }
                    MouseArea {
                        id: tabMouse
                        z: 1
                        anchors.fill: parent
                        acceptedButtons: Qt.LeftButton | Qt.MiddleButton
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onPressed: mouse => tabVisual.burst(mouse.x, mouse.y)
                        onClicked: mouse => {
                            searchTab.forceActiveFocus(Qt.MouseFocusReason);
                            if (mouse.button === Qt.MiddleButton) {
                                if (searchTab.closable)
                                    workspaceState.close_tab(searchTab.index);
                                return;
                            }
                            workspaceState.activate_tab(searchTab.entryKey, searchTab.title);
                        }
                        Controls.ToolTip {
                            theme: root.theme
                            visible: tabMouse.containsMouse && !root.theme.suppressToolTips
                            delay: 500
                            text: searchTab.title
                        }
                    }
                }
            }

            Controls.CompactIconButton {
                id: tabOverflowButton
                objectName: "searchTabsOverflowButton"
                visible: searchTabsView.contentWidth > searchTabsView.width + 1
                Layout.preferredWidth: visible ? 40 : 0
                Layout.preferredHeight: 40
                theme: root.theme
                iconName: "keyboard_arrow_down"
                round: false
                toolTip: qsTr("All search tabs")
                onPressed: tabOverflowMenu.sourceWasOpen = tabOverflowMenu.opened
                onClicked: {
                    tabOverflowMenu.actions = searchTabsView.allTabActions();
                    tabOverflowMenu.toggleBelow(tabOverflowButton);
                }
            }

            Rectangle {
                visible: !root.compactTabActions
                Layout.preferredWidth: 1
                Layout.preferredHeight: 24
                color: root.theme.separator
            }

            Controls.CompactIconButton {
                id: resultSortButton
                objectName: "searchResultSortButton"
                visible: !root.compactTabActions
                Layout.preferredWidth: visible ? 40 : 0
                Layout.preferredHeight: 40
                theme: root.theme
                iconName: "sort-items"
                iconColor: resultMenus.sortOpened || appController.result_sort_mode !== "name_asc" ? root.theme.action : root.theme.primaryText
                backgroundColor: resultMenus.sortOpened ? root.theme.secondaryContainer : "transparent"
                round: false
                toolTip: qsTr("Sort items")
                onClicked: resultMenus.openSort(resultSortButton)
            }
            Controls.CompactIconButton {
                id: resultGroupButton
                visible: !root.compactTabActions
                Layout.preferredWidth: visible ? 40 : 0
                Layout.preferredHeight: 40
                theme: root.theme
                iconName: "group-items"
                iconColor: resultMenus.groupOpened || appController.result_group_mode !== "none" ? root.theme.action : root.theme.primaryText
                backgroundColor: resultMenus.groupOpened ? root.theme.secondaryContainer : "transparent"
                round: false
                toolTip: qsTr("Group items")
                onClicked: resultMenus.openGroup(resultGroupButton)
            }
            Frame.FrameView {
                objectName: "searchResultsViewsInline"
                visible: root.inlineResultViews
                Layout.preferredWidth: visible ? SearchMenus.viewPicker.width : 0
                Layout.preferredHeight: SearchMenus.viewPicker.height
                theme: root.theme
                scene: SearchMenus.describeViewPicker({
                    mode: appController.results_view_mode,
                    busy: appController.search_state === "loading"
                }, root.language)
                onEvent: action => {
                    if (action.type === "view" && appController.search_state !== "loading")
                        appController.set_results_view_mode(action.value);
                }
            }
            Controls.CompactIconButton {
                id: resultsViewButton
                objectName: "searchResultsViewMenuButton"
                visible: !root.compactTabActions
                Layout.preferredWidth: visible ? 40 : 0
                Layout.preferredHeight: 40
                theme: root.theme
                iconName: root.inlineResultViews && ["continious", "tiles", "table"].indexOf(appController.results_view_mode) >= 0 ? "expand-more" : root.resultViewIcon(appController.results_view_mode)
                iconColor: root.inlineResultViews && ["continious", "tiles", "table"].indexOf(appController.results_view_mode) < 0 ? root.theme.action : root.theme.primaryText
                round: false
                toolTip: qsTr("Change search results view")
                onClicked: resultsViewMenu.openBelow(resultsViewButton)
            }

            Controls.CompactIconButton {
                id: searchTabActionsOverflowButton
                objectName: "searchTabActionsOverflowButton"
                visible: root.compactTabActions
                Layout.preferredWidth: visible ? 40 : 0
                Layout.preferredHeight: 40
                theme: root.theme
                iconName: "more-vert"
                round: false
                toolTip: qsTr("Result actions")
                onPressed: searchTabActionsMenu.sourceWasOpen = searchTabActionsMenu.opened
                onClicked: searchTabActionsMenu.toggleBelow(searchTabActionsOverflowButton)
            }

            Item {
                id: tabHistoryControl
                readonly property int closedTabCount: Math.max(0, appController.closed_search_tabs.length - 2)
                visible: closedTabCount > 0
                Layout.preferredWidth: visible ? 40 : 0
                Layout.preferredHeight: 40

                Controls.CompactIconButton {
                    id: tabHistoryButton
                    anchors.fill: parent
                    enabled: tabHistoryControl.closedTabCount > 0
                    opacity: enabled ? 1 : 0.38
                    theme: root.theme
                    iconName: "history"
                    round: false
                    toolTip: enabled ? tabHistoryControl.closedTabCount + (tabHistoryControl.closedTabCount === 1 ? qsTr(" recently closed search tab") : qsTr(" recently closed search tabs")) : qsTr("No recently closed search tabs")
                    onPressed: tabHistoryMenu.sourceWasOpen = tabHistoryMenu.opened
                    onClicked: tabHistoryMenu.toggleBelow(tabHistoryButton)
                    Behavior on opacity {
                        NumberAnimation {
                            duration: theme.motionFast
                        }
                    }
                }
                Rectangle {
                    visible: tabHistoryControl.closedTabCount > 0
                    anchors.right: parent.right
                    anchors.rightMargin: 1
                    anchors.top: parent.top
                    anchors.topMargin: 1
                    width: Math.max(16, badgeText.implicitWidth + 8)
                    height: 16
                    radius: 8
                    color: root.theme.action
                    border.width: 2
                    border.color: root.theme.toolBar
                    scale: visible ? 1 : 0.6
                    opacity: visible ? 1 : 0
                    Label {
                        id: badgeText
                        anchors.centerIn: parent
                        text: tabHistoryControl.closedTabCount > 99 ? "99+" : tabHistoryControl.closedTabCount
                        color: root.theme.selectedText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                        font.weight: Font.Bold
                    }
                    Behavior on scale {
                        NumberAnimation {
                            duration: theme.motionMedium
                            easing.type: Easing.OutBack
                        }
                    }
                    Behavior on opacity {
                        NumberAnimation {
                            duration: theme.motionFast
                        }
                    }
                }
            }
        }
        Rectangle {
            anchors.bottom: parent.bottom
            width: parent.width
            height: 1
            color: root.theme.separator
        }
    }
    Controls.DockWorkspaceFooter {
        id: resultsToolbar
        objectName: "searchResultsFooter"
        theme: root.theme
        // Switch before the expanded pagination controls reach the
        // edge.  The previous 840px threshold ignored page buttons,
        // translated labels and fractional Windows DPI, so the final
        // actions could be laid out beyond the dock.
        property bool compact: width < 1200
        property bool narrow: width < 520
        property bool ultraNarrow: width < 340
        anchors.bottom: parent.bottom
        width: parent.width
        z: 4

        property var frameModel: ({
                mode: appController.loading_mode,
                busy: appController.search_state === "loading",
                page: appController.current_page,
                pageCount: appController.page_count,
                pageSize: appController.page_size,
                pageNumbers: appController.page_numbers,
                hasNext: appController.current_page < appController.page_count,
                count: appController.result_count,
                total: appController.result_count,
                range: appController.first_result + "–" + appController.last_result,
                localSync: true,
                canCreate: true
            })
        TextMetrics {
            id: footerCountMetrics
            font.hintingPreference: Font.PreferVerticalHinting
            font.family: root.theme.fontFamily
            font.pixelSize: 14
            text: Footer.countText(resultsToolbar.frameModel, resultsToolbar.width, root.language)
        }
        Frame.FrameView {
            anchors.fill: parent
            theme: root.theme
            scene: Footer.describe(Object.assign({}, resultsToolbar.frameModel, {
                countWidth: footerCountMetrics.advanceWidth
            }), width, height, root.language)
            onEvent: (action, source) => {
                const menu = action.menu === "size" ? pageSizeMenu : action.menu === "mode" ? loadModeMenu : pagePicker;
                if (action.type === "press")
                    menu.sourceWasOpen = menu.opened;
                else if (action.type === "size")
                    pageSizeMenu.toggleBelow(source);
                else if (action.type === "mode")
                    loadModeMenu.toggleBelow(source);
                else if (action.type === "pagePicker") {
                    pagePicker.pageDraft = String(appController.current_page);
                    pagePicker.toggleBelowItem(source, true, 6);
                } else if (action.type === "page")
                    appController.go_to_page(action.value);
                else if (action.type === "previous")
                    appController.previous_page();
                else if (action.type === "next")
                    appController.next_page();
                else if (action.type === "sync")
                    appController.open_search_type_repository_sync();
                else if (action.type === "create")
                    appController.open_window("add_sobject");
            }
        }
        Rectangle {
            anchors.top: parent.top
            width: parent.width
            height: 1
            color: root.theme.separator
        }
    }
    SearchResultsPane {
        id: resultsArea
        anchors.top: searchTabs.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: resultsToolbar.top
        theme: root.theme
        controller: appController
        columnsController: root.columnsController
        userModel: userListModel
        surfacesModel: workspaceResultSurfacesModel
        versionResultsModel: versionsModel
        presentationActive: root.presentationActive
    }
    Rectangle {
        id: searchTabTimingBadge
        objectName: "searchTabTimingBadge"
        anchors.top: resultsArea.top
        anchors.right: resultsArea.right
        anchors.topMargin: 10
        anchors.rightMargin: 14
        width: Math.min(implicitWidth, Math.max(0, root.width - 28))
        implicitWidth: Math.max(timingTitle.implicitWidth, timingDetails.implicitWidth) + 24
        height: root.tabTimingMeasuring ? 36 : 52
        radius: 10
        color: root.theme.panelRaised
        border.width: 1
        border.color: root.theme.outlineVariant
        visible: appController.search_tab_switch_monitor.recording && root.tabTimingVisible
        z: 1000

        Column {
            anchors.fill: parent
            anchors.leftMargin: 12
            anchors.rightMargin: 12
            anchors.topMargin: 7
            spacing: 2

            Label {
                id: timingTitle
                width: parent.width
                text: String(root.lastTabTiming.tab || qsTr("Search tab")) + " · " + (root.tabTimingMeasuring ? qsTr("Measuring...") : root.timingMs("firstFrameMs") + " " + qsTr("ms"))
                color: root.theme.primaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.body
                font.weight: Font.DemiBold
                elide: Text.ElideRight
            }
            Label {
                id: timingDetails
                width: parent.width
                visible: !root.tabTimingMeasuring
                text: qsTr("capture") + " " + root.timingMs("captureMs") + " · " + qsTr("sync") + " " + root.timingMs("syncMs") + " · " + qsTr("projection") + " " + root.timingMs("projectionMs") + " · " + qsTr("frame") + " " + root.timingMs("afterPythonMs")
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.label
                elide: Text.ElideRight
            }
        }

        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: root.tabTimingVisible = false
        }
    }
    Rectangle {
        id: pageNavigation
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: 0
        color: root.theme.toolBar
        visible: false
        Behavior on height {
            NumberAnimation {
                duration: theme.motionMedium
                easing.type: Easing.OutCubic
            }
        }
        Rectangle {
            anchors.top: parent.top
            width: parent.width
            height: 1
            color: root.theme.separator
        }
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 7
            anchors.rightMargin: 7
            spacing: 5
            Label {
                text: qsTr("Showing ") + appController.first_result + "–" + appController.last_result + " of " + appController.result_count
                color: root.theme.secondaryText
                font.family: root.theme.fontFamily
                font.pointSize: Controls.Typography.label
            }
            Item {
                Layout.fillWidth: true
            }
            Controls.CompactIconButton {
                visible: appController.loading_mode === "pages"
                enabled: appController.current_page > 1 && appController.search_state !== "loading"
                theme: root.theme
                iconName: "chevron_right"
                rotation: 180
                onClicked: appController.previous_page()
            }
            Repeater {
                model: appController.loading_mode === "pages" ? appController.page_numbers : []
                delegate: Rectangle {
                    required property var modelData
                    Layout.preferredWidth: 24
                    Layout.preferredHeight: 24
                    radius: 12
                    color: Number(modelData) === appController.current_page ? root.theme.action : pageMouse.containsMouse ? root.theme.rowHover : "transparent"
                    Label {
                        anchors.centerIn: parent
                        text: modelData
                        color: Number(modelData) === appController.current_page ? root.theme.selectedText : root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Controls.Typography.label
                        font.weight: Font.DemiBold
                    }
                    MouseArea {
                        id: pageMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        enabled: appController.search_state !== "loading"
                        cursorShape: Qt.PointingHandCursor
                        onClicked: appController.go_to_page(Number(modelData))
                    }
                }
            }
            Controls.CompactIconButton {
                visible: appController.loading_mode === "pages"
                enabled: appController.current_page < appController.page_count && appController.search_state !== "loading"
                theme: root.theme
                iconName: "chevron_right"
                onClicked: appController.next_page()
            }
            Controls.ComboBox {
                theme: root.theme
                visible: appController.loading_mode === "pages"
                Layout.preferredWidth: 66
                Layout.preferredHeight: 25
                model: [20, 25, 50, 100]
                currentIndex: appController.page_size === 20 ? 0 : appController.page_size === 50 ? 2 : appController.page_size === 100 ? 3 : 1
                font.pointSize: Controls.Typography.label
                onActivated: appController.set_page_size(Number(currentText))
            }
        }
    }
    SearchResultMenus {
        id: resultMenus
        theme: root.theme
        application: appController
        filterController: filterEditorController
        presets: filterPresetModel
        columnsModel: typeof filterColumnModel === "undefined" ? null : filterColumnModel
        onProcessFilterRequested: appController.open_window("process_filter_editor")
        onSearchEditorRequested: dockModel.show_panel("advanced_search")
    }
    ActionMenu {
        id: searchTabActionsMenu
        objectName: "searchTabActionsMenu"
        parent: Overlay.overlay
        theme: root.theme
        preferredWidth: 272
        actions: [
            {
                "title": "Result actions",
                "header": true
            },
            {
                "title": "Search filters and presets",
                "icon": "advanced-search",
                "command": "filters"
            },
            {
                "title": "Sort items",
                "icon": "sort-items",
                "children": resultMenus.sortActions
            },
            {
                "title": "Group items",
                "icon": "group-items",
                "children": resultMenus.groupActions
            },
            {
                "title": "Change search results view",
                "icon": root.resultViewIcon(appController.results_view_mode),
                "children": resultsViewMenu.actions
            }
        ]
        onTriggered: function (command) {
            if (command === "filters")
                resultMenus.openFilters(searchTabActionsOverflowButton);
            else if (resultMenus.sortActions.some(action => action.command === command))
                resultMenus.sortCommand(command, searchTabActionsOverflowButton);
            else if (appController.result_group_actions.some(action => action.command === command))
                appController.set_result_group_mode(command);
            else if (resultsViewMenu.actions.some(action => action.command === command))
                appController.set_results_view_mode(command);
        }
    }
    ActionMenu {
        id: resultsViewMenu
        objectName: "searchResultViewsMenu"
        parent: Overlay.overlay
        theme: root.theme
        actions: SearchMenus.viewActions(appController.results_view_mode, appController.search_state === "loading")
        onTriggered: function (command) {
            appController.set_results_view_mode(command);
        }
    }
    ActionMenu {
        id: loadModeMenu
        parent: Overlay.overlay
        theme: root.theme
        actions: Footer.menu("mode", resultsToolbar.frameModel)
        onTriggered: command => appController.set_loading_mode(command)
    }
    ActionMenu {
        id: pageSizeMenu
        parent: Overlay.overlay
        theme: root.theme
        actions: Footer.menu("size", resultsToolbar.frameModel)
        onTriggered: command => appController.set_page_size(Number(command))
    }
    Controls.ScrollablePopup {
        id: pagePicker
        theme: root.theme
        parent: Overlay.overlay
        preferredSurfaceWidth: 224
        minimumSurfaceWidth: 200
        property string pageDraft: ""
        Frame.FrameView {
            width: 200
            height: 80
            theme: root.theme
            scene: Footer.pagePicker(pagePicker.pageDraft, width, root.language)
            onEvent: action => {
                if (action.type === "pageDraft")
                    pagePicker.pageDraft = action.value;
                else if (action.type === "go" && /^\d+$/.test(pagePicker.pageDraft)) {
                    const page = Number(pagePicker.pageDraft);
                    if (page > 0 && page <= appController.page_count) {
                        appController.go_to_page(page);
                        pagePicker.close();
                    }
                }
            }
        }
    }

    ActionMenu {
        id: tabOverflowMenu
        objectName: "searchTabsOverflowMenu"
        parent: Overlay.overlay
        theme: root.theme
        onTriggered: command => {
            if (command.indexOf("tab:") !== 0)
                return;
            searchTabsView.revealTab(Number(command.slice(4)));
        }
        onSecondaryTriggered: command => {
            if (command.indexOf("close-tab:") === 0)
                appController.close_search_tab(Number(command.slice(10)));
        }
    }
    ActionMenu {
        id: tabHistoryMenu
        parent: Overlay.overlay
        theme: root.theme
        actions: appController.closed_search_tabs
        onTriggered: command => {
            if (command === "clear_history") {
                appController.clear_search_tab_history();
                return;
            }
            if (command.indexOf("restore_tab:") === 0)
                appController.restore_closed_search_tab(Number(command.slice(12)));
        }
    }
}

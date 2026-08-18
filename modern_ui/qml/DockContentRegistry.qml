import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import QtQml.Models
import Qt5Compat.GraphicalEffects

Item {
    id: root
    required property var theme
    required property string pageTitle
    signal notice(string message)
    signal requestDockMenu(var sourceItem)

    readonly property Component results: resultsContent
    readonly property Component snapshot: snapshotContentV2
    readonly property Component tasks: tasksContent
    readonly property Component taskCalendar: taskCalendarContent
    readonly property Component timesheet: timesheetContent
    readonly property Component workReports: workReportsContent
    readonly property Component costReports: costReportsContent
    readonly property Component description: descriptionContent
    readonly property Component notes: notesContent
    readonly property Component dropPlate: dropPlateContent
    readonly property Component advancedSearch: advancedSearchContent
    readonly property Component fastControls: fastControlsContent
    readonly property Component repoSync: repoSyncContent
    readonly property Component commitQueue: commitQueueContent
    readonly property Component databaseEditor: databaseEditorContent
    readonly property Component watchFolders: watchFoldersContent

    Component {
        id: resultsContent
        Item {
            id: resultsPane
            readonly property bool autoCompact: width < 445
            readonly property bool compactRows:
                autoCompact || appController.results_view_mode === "compact"
            readonly property bool narrowHeader: autoCompact
            readonly property bool splitRight:
                !compactRows
                && appController.results_view_mode === "splitted_vertical"
            readonly property bool splitBottom:
                !compactRows
                && appController.results_view_mode === "splitted_horizontal"
            readonly property bool splitView: splitRight || splitBottom

            TapHandler {
                acceptedButtons: Qt.LeftButton
                gesturePolicy: TapHandler.DragThreshold
                onPressedChanged: {
                    if (!pressed || !resultTiles.expandedCard)
                        return
                    const cardPoint = resultTiles.expandedCard.mapFromItem(
                        resultsPane, point.position.x, point.position.y)
                    if (
                        cardPoint.x < 0 || cardPoint.y < 0
                        || cardPoint.x > resultTiles.expandedCard.width
                        || cardPoint.y > resultTiles.expandedCard.height
                    )
                        appController.clear_result_selection()
                }
            }

            Rectangle {
                id: searchHeader
                anchors.top: parent.top
                width: parent.width
                height: root.theme.dockWorkspaceHeaderHeight / 2
                color: root.theme.panelDeep
                TacticSearchField {
                    id: searchField
                    anchors.left: parent.left
                    anchors.right: resultsPane.narrowHeader
                        ? searchOverflowButton.left : tagCloudButton.left
                    anchors.top: parent.top
                    anchors.leftMargin: 38
                    anchors.rightMargin: 8
                    anchors.topMargin: 5
                    height: 38
                    theme: root.theme
                    suggestionModel: searchSuggestionModel
                    controller: appController
                    placeholderText: {
                        var scope = root.pageTitle.split("/")[0].trim()
                        return scope.length > 0
                            ? qsTr("Search ") + qsTr(scope).toLowerCase()
                            : qsTr("Search")
                    }
                }
                CompactIconButton {
                    id: tagCloudButton
                    anchors.right: quickFilterButton.left
                    anchors.rightMargin: 3
                    anchors.verticalCenter: parent.verticalCenter
                    width: visible ? 38 : 0
                    height: 38
                    visible: !resultsPane.narrowHeader
                    theme: root.theme
                    iconName: "tags"
                    iconColor: tagCloudPopup.opened
                        || appController.active_tag_count > 0
                        ? root.theme.action : root.theme.primaryText
                    backgroundColor: tagCloudPopup.opened
                        ? root.theme.secondaryContainer : "transparent"
                    round: true
                    toolTip: qsTr("Tags")
                    onPressed:
                        tagCloudPopup.sourceWasOpen = tagCloudPopup.opened
                    onClicked: {
                        const opening = !tagCloudPopup.sourceWasOpen
                            && !tagCloudPopup.opened
                        quickFilterPopup.close()
                        tagCloudPopup.toggleBelow(tagCloudButton)
                        if (opening)
                            appController.request_tag_cloud()
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
                            font.pointSize: Typography.caption
                            font.weight: Font.Bold
                        }
                    }
                }
                CompactIconButton {
                    id: quickFilterButton
                    anchors.right: searchRefresh.left
                    anchors.rightMargin: 3
                    anchors.verticalCenter: parent.verticalCenter
                    width: visible ? 38 : 0
                    height: 38
                    visible: !resultsPane.narrowHeader
                        && appController.quick_filter_groups.length > 0
                    enabled: visible
                    theme: root.theme
                    iconName: "filter"
                    iconColor: quickFilterPopup.opened
                        || appController.active_quick_filter_count > 0
                        ? root.theme.action : root.theme.primaryText
                    backgroundColor: quickFilterPopup.opened
                        ? root.theme.secondaryContainer : "transparent"
                    round: true
                    toolTip: qsTr("Quick filters")
                    onPressed:
                        quickFilterPopup.sourceWasOpen
                            = quickFilterPopup.opened
                    onClicked: {
                        tagCloudPopup.close()
                        appController.request_quick_filter_data()
                        quickFilterPopup.toggleBelow(quickFilterButton)
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
                            font.pointSize: Typography.caption
                            font.weight: Font.Bold
                        }
                    }
                }
                RefreshIconButton {
                    id: searchRefresh
                    anchors.right: resultsViewButton.left
                    anchors.rightMargin: 3
                    anchors.verticalCenter: parent.verticalCenter
                    width: visible ? 38 : 0
                    visible: !resultsPane.narrowHeader
                    theme: root.theme
                    toolTip: qsTr("Refresh current results")
                    onClicked: appController.refresh_current()
                }
                CompactIconButton {
                    id: resultsViewButton
                    anchors.right: searchGear.left
                    anchors.rightMargin: 3
                    anchors.verticalCenter: parent.verticalCenter
                    width: visible ? 38 : 0
                    height: 38
                    visible: !resultsPane.narrowHeader
                    theme: root.theme
                    iconName: resultsPane.compactRows ? "view-list"
                        : resultsPane.splitRight ? "columns"
                        : resultsPane.splitBottom ? "align-justify" : "list-alt"
                    round: true
                    toolTip: qsTr("Change search results view")
                    onClicked: resultsViewMenu.openBelow(resultsViewButton)
                }
                CompactIconButton {
                    id: searchOverflowButton
                    anchors.right: searchGear.left
                    anchors.rightMargin: 3
                    anchors.verticalCenter: parent.verticalCenter
                    width: visible ? 38 : 0
                    height: 38
                    visible: resultsPane.narrowHeader
                    theme: root.theme
                    iconName: "more-horiz"
                    round: true
                    toolTip: qsTr("Search actions")
                    onPressed: searchOverflowMenu.sourceWasOpen
                        = searchOverflowMenu.opened
                    onClicked: searchOverflowMenu.toggleBelow(
                        searchOverflowButton
                    )
                }
                CompactIconButton {
                    id: searchGear
                    anchors.right: parent.right
                    anchors.rightMargin: 7
                    anchors.verticalCenter: parent.verticalCenter
                    width: 38
                    height: 38
                    theme: root.theme
                    iconName: "more-vert"
                    round: true
                    toolTip: qsTr("Workspace panels")
                    onClicked: root.requestDockMenu(searchGear)
                }
            }
            ActionMenu {
                id: searchOverflowMenu
                parent: Overlay.overlay
                theme: root.theme
                preferredWidth: 268
                actions: [
                    {
                        "title": "Search filters",
                        "header": true
                    },
                    {
                        "title": "Tags",
                        "icon": "tags",
                        "command": "tags",
                        "badgeCount": appController.active_tag_count
                    },
                    {
                        "title": "Quick filters",
                        "icon": "filter",
                        "command": "quick_filters",
                        "enabled": appController.quick_filter_groups.length > 0,
                        "badgeCount": appController.active_quick_filter_count
                    },
                    {
                        "title": "Refresh results",
                        "icon": "refresh",
                        "command": "refresh"
                    },
                    { "separator": true },
                    {
                        "title": "Result view",
                        "header": true
                    },
                    {
                        "title": "Continuous tree",
                        "icon": "list-alt",
                        "command": "view:continious",
                        "checked": appController.results_view_mode
                            === "continious"
                    },
                    {
                        "title": "Cards",
                        "icon": "dashboard",
                        "command": "view:tiles",
                        "checked": appController.results_view_mode === "tiles"
                    },
                    {
                        "title": "Compact rows",
                        "icon": "view-list",
                        "command": "view:compact",
                        "checked": appController.results_view_mode === "compact"
                    },
                    {
                        "title": "Versions on the right",
                        "icon": "columns",
                        "command": "view:splitted_vertical",
                        "checked": appController.results_view_mode
                            === "splitted_vertical"
                    },
                    {
                        "title": "Versions at the bottom",
                        "icon": "align-justify",
                        "command": "view:splitted_horizontal",
                        "checked": appController.results_view_mode
                            === "splitted_horizontal"
                    }
                ]
                onTriggered: function(command) {
                    if (command === "tags") {
                        Qt.callLater(function() {
                            quickFilterPopup.close()
                            tagCloudPopup.openBelow(searchOverflowButton)
                            appController.request_tag_cloud()
                        })
                    } else if (command === "quick_filters") {
                        Qt.callLater(function() {
                            tagCloudPopup.close()
                            appController.request_quick_filter_data()
                            quickFilterPopup.openBelow(searchOverflowButton)
                        })
                    } else if (command === "refresh") {
                        appController.refresh_current()
                    } else if (command.indexOf("view:") === 0) {
                        appController.set_results_view_mode(
                            command.slice("view:".length)
                        )
                    }
                }
            }
            Md3Popup {
                id: quickFilterPopup
                theme: root.theme
                parent: Overlay.overlay
                property bool sourceWasOpen: false
                width: Math.min(520, Math.max(280, parent.width - 16))
                height: Math.min(
                    implicitHeight,
                    Math.max(120, parent.height - 16)
                )
                implicitHeight: quickFilterColumn.implicitHeight + 24
                padding: 12
                modal: false
                focus: true
                closePolicy:
                    Popup.CloseOnEscape | Popup.CloseOnReleaseOutside

                function openBelow(sourceItem) {
                    if (!sourceItem || !parent)
                        return
                    quickFilterEditorController.ensure_current()
                    const point = sourceItem.mapToItem(
                        parent, sourceItem.width - width, sourceItem.height + 6
                    )
                    x = Math.max(8, Math.min(parent.width - width - 8, point.x))
                    y = Math.max(8, Math.min(parent.height - height - 8, point.y))
                    open()
                }

                function toggleBelow(sourceItem) {
                    if (sourceWasOpen || opened)
                        close()
                    else
                        openBelow(sourceItem)
                    sourceWasOpen = false
                }

                contentItem: Flickable {
                    id: quickFilterFlickable
                    clip: true
                    contentWidth: width
                    contentHeight: quickFilterColumn.implicitHeight
                    boundsBehavior: Flickable.StopAtBounds

                    Column {
                        id: quickFilterColumn
                        width: quickFilterFlickable.width
                        spacing: 20

                        RowLayout {
                            width: parent.width
                            spacing: 8

                            Label {
                                Layout.fillWidth: true
                                text: qsTr("QUICK FILTERS")
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pixelSize: 12
                                font.weight: Font.DemiBold
                            }
                            Md3Button {
                                visible:
                                    quickFilterEditorController.canEdit
                                theme: root.theme
                                text: qsTr("Edit")
                                icon.name: "edit"
                                tonal: true
                                onClicked: {
                                    quickFilterPopup.close()
                                    quickFilterEditorController.begin_session()
                                    quickFilterEditorDialog.open()
                                }
                            }
                        }

                        Repeater {
                            model: appController.quick_filter_groups
                            delegate: Column {
                                id: quickFilterGroup
                                required property var modelData
                                width: quickFilterColumn.width
                                spacing: 9

                                Label {
                                    width: parent.width
                                    text: qsTr(String(
                                        quickFilterGroup.modelData.title
                                    ))
                                    color: root.theme.primaryText
                                    font.family: root.theme.fontFamily
                                    font.pointSize: Typography.bodyLarge
                                    font.weight: Font.DemiBold
                                }

                                Flow {
                                    width: parent.width
                                    spacing: 8

                                    QuickFilterChip {
                                        theme: root.theme
                                        text: qsTr("ALL")
                                        accent:
                                            quickFilterGroup.modelData.accent
                                        checked:
                                            quickFilterGroup.modelData.allSelected
                                        onClicked:
                                            appController.toggle_quick_filter(
                                                quickFilterGroup.modelData.key,
                                                ""
                                            )
                                    }
                                    Repeater {
                                        model:
                                            quickFilterGroup.modelData.options
                                        delegate: QuickFilterChip {
                                            required property var modelData
                                            theme: root.theme
                                            // Search Type/workflow values come
                                            // from the project configuration.
                                            text: String(modelData.title || "")
                                            accent: modelData.accent
                                            showAccentMarker:
                                                modelData.showAccentMarker
                                            checked: modelData.selected
                                            onClicked:
                                                appController.toggle_quick_filter(
                                                    quickFilterGroup.modelData.key,
                                                    modelData.key
                                                )
                                        }
                                    }
                                }
                            }
                        }
                    }

                    ScrollBar.vertical: Md3ScrollBar {
                        theme: root.theme
                        flickableTarget: quickFilterFlickable
                    }
                }
            }
            QuickFilterEditorDialog {
                id: quickFilterEditorDialog
                theme: root.theme
                controller: quickFilterEditorController
            }
            Md3Popup {
                id: tagCloudPopup
                theme: root.theme
                parent: Overlay.overlay
                property bool sourceWasOpen: false
                property var anchorItem: null
                width: Math.min(520, Math.max(280, parent.width - 16))
                height: Math.min(
                    implicitHeight,
                    Math.max(
                        160,
                        Math.min(400, parent.height * 0.52)
                    )
                )
                implicitHeight: Math.max(
                    112, tagCloudColumn.implicitHeight + 24
                )
                padding: 12
                modal: false
                focus: true
                closePolicy:
                    Popup.CloseOnEscape | Popup.CloseOnReleaseOutside

                function openBelow(sourceItem) {
                    if (!sourceItem || !parent)
                        return
                    anchorItem = sourceItem
                    reposition()
                    open()
                }

                function reposition() {
                    if (!anchorItem || !parent)
                        return
                    const point = anchorItem.mapToItem(
                        parent,
                        anchorItem.width - width,
                        anchorItem.height + 6
                    )
                    x = Math.max(8, Math.min(parent.width - width - 8, point.x))
                    y = Math.max(8, Math.min(parent.height - height - 8, point.y))
                }

                function toggleBelow(sourceItem) {
                    if (sourceWasOpen || opened)
                        close()
                    else
                        openBelow(sourceItem)
                    sourceWasOpen = false
                }

                onHeightChanged: {
                    if (opened)
                        Qt.callLater(reposition)
                }
                onWidthChanged: {
                    if (opened)
                        Qt.callLater(reposition)
                }

                contentItem: Flickable {
                    id: tagCloudFlickable
                    clip: true
                    contentWidth: width
                    contentHeight: tagCloudColumn.implicitHeight
                    boundsBehavior: Flickable.StopAtBounds

                    Column {
                        id: tagCloudColumn
                        width: tagCloudFlickable.width
                        spacing: 10

                        RowLayout {
                            width: parent.width
                            Label {
                                Layout.fillWidth: true
                                text: qsTr("TAGS")
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Typography.bodyLarge
                                font.weight: Font.DemiBold
                            }
                            Md3BusyIndicator {
                                uiTheme: root.theme
                                Layout.preferredWidth: 24
                                Layout.preferredHeight: 24
                                running: appController.tag_cloud_loading
                                visible: running
                            }
                            RefreshIconButton {
                                theme: root.theme
                                toolTip: qsTr("Reload tags")
                                enabled: !appController.tag_cloud_loading
                                onClicked: appController.request_tag_cloud()
                            }
                        }

                        Label {
                            width: parent.width
                            visible: text.length > 0
                                && !appController.tag_cloud_loading
                            text: appController.tag_cloud_error
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Typography.body
                            wrapMode: Text.WordWrap
                        }

                        Flow {
                            width: parent.width
                            spacing: 8
                            visible: !appController.tag_cloud_loading
                                && appController.tag_cloud.length > 0

                            QuickFilterChip {
                                theme: root.theme
                                text: qsTr("ALL")
                                checked: appController.active_tag_count === 0
                                onClicked: appController.toggle_tag("")
                            }
                            Repeater {
                                model: appController.tag_cloud
                                delegate: QuickFilterChip {
                                    required property var modelData
                                    theme: root.theme
                                    text: modelData.tag
                                    checked: modelData.selected
                                    emphasis: modelData.weight
                                    maximumChipWidth:
                                        Math.min(260, tagCloudFlickable.width)
                                    onClicked:
                                        appController.toggle_tag(modelData.tag)
                                }
                            }
                        }
                    }

                    ScrollBar.vertical: Md3ScrollBar {
                        theme: root.theme
                        flickableTarget: tagCloudFlickable
                    }
                }
            }
            Rectangle {
                id: searchTabs
                anchors.top: searchHeader.bottom
                width: parent.width
                height: root.theme.dockWorkspaceHeaderHeight / 2
                color: root.theme.toolBar
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 4
                    anchors.rightMargin: 4
                    spacing: 2


                    CompactIconButton {
                        id: addSearchTabButton
                        Layout.preferredWidth: 40
                        Layout.preferredHeight: 40
                        theme: root.theme
                        iconName: "add"
                        round: true
                        toolTip: qsTr("Add new search tab")
                        onClicked: {
                            workspaceState.add_search_tab()
                            Qt.callLater(function() {
                                searchField.beginSearchInput()
                            })
                        }
                    }
                    CompactIconButton {
                        id: tabFilterButton
                        Layout.preferredWidth: 40
                        Layout.preferredHeight: 40
                        theme: root.theme
                        iconName: "filter_alt"
                        round: true
                        toolTip: qsTr("Add filter to current tab")
                        onClicked: resultFilters.openBelow(tabFilterButton)
                    }

                    ListView {
                        id: searchTabsView
                        property int dragSourceIndex: -1
                        property int dragTargetIndex: -1
                        property real draggedTabWidth: 0
                        property var naturalWidths: ({})
                        property int nextNaturalWidthToken: 0
                        readonly property real naturalContentWidth: {
                            let total = 0
                            const keys = Object.keys(naturalWidths)
                            for (let i = 0; i < keys.length; ++i)
                                total += Number(naturalWidths[keys[i]].width) || 0
                            return total
                        }
                        readonly property real activeNaturalWidth: {
                            const keys = Object.keys(naturalWidths)
                            for (let i = 0; i < keys.length; ++i) {
                                const entry = naturalWidths[keys[i]]
                                if (entry.current)
                                    return Number(entry.width) || 0
                            }
                            return 0
                        }
                        function allocateNaturalWidthToken() {
                            nextNaturalWidthToken += 1
                            return nextNaturalWidthToken
                        }
                        function registerNaturalWidth(key, value, token, current) {
                            const widths = Object.assign({}, naturalWidths)
                            widths[key] = {
                                "width": value,
                                "token": token,
                                "current": current
                            }
                            naturalWidths = widths
                        }
                        function unregisterNaturalWidth(key, token) {
                            if (naturalWidths[key] === undefined
                                    || naturalWidths[key].token !== token)
                                return
                            const widths = Object.assign({}, naturalWidths)
                            delete widths[key]
                            naturalWidths = widths
                        }
                        function allTabActions() {
                            const actions = [
                                { "title": "Open search tabs", "header": true }
                            ]
                            for (let i = 0; i < count; ++i) {
                                const record = workspaceTabsModel.get(i)
                                actions.push({
                                    "title": record.title || "Search tab",
                                    "icon": "tab",
                                    "command": "tab:" + i,
                                    "checked": !!record.current
                                })
                            }
                            return actions
                        }
                        function revealTab(index) {
                            const record = workspaceTabsModel.get(index)
                            if (!record || !record.entryKey)
                                return
                            workspaceState.activate_tab(record.entryKey, record.title || "")
                            positionViewAtIndex(index, ListView.Contain)
                        }
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        orientation: ListView.Horizontal
                        boundsBehavior: Flickable.StopAtBounds
                        clip: true
                        spacing: 0
                        cacheBuffer: 10000
                        model: workspaceTabsModel

                        delegate: Item {
                            id: searchTab
                            required property int index
                            required property string entryKey
                            required property string title
                            required property bool closable
                            required property bool current
                            property int dragTargetIndex: index
                            property int naturalWidthToken: 0
                            readonly property real minimumTabWidth: 96
                            readonly property real naturalTabWidth: Math.max(
                                minimumTabWidth,
                                tabVisual.labelImplicitWidth + (closable ? 64 : 32)
                            )
                            readonly property real fittedTabWidth: {
                                const available = searchTabsView.width
                                const naturalTotal = searchTabsView.naturalContentWidth
                                const minimumTotal = searchTabsView.count * minimumTabWidth
                                if (naturalTotal <= available || naturalTotal <= minimumTotal)
                                    return naturalTabWidth
                                if (current)
                                    return naturalTabWidth
                                const activeWidth = searchTabsView.activeNaturalWidth
                                const inactiveCount = Math.max(0, searchTabsView.count - 1)
                                const inactiveMinimumTotal = inactiveCount * minimumTabWidth
                                const inactiveNaturalTotal = Math.max(
                                    inactiveMinimumTotal,
                                    naturalTotal - activeWidth
                                )
                                const inactiveAvailable = available - activeWidth
                                if (inactiveAvailable <= inactiveMinimumTotal)
                                    return minimumTabWidth
                                const ratio = (inactiveAvailable - inactiveMinimumTotal)
                                    / (inactiveNaturalTotal - inactiveMinimumTotal)
                                return minimumTabWidth
                                    + (naturalTabWidth - minimumTabWidth) * ratio
                            }
                            property real displacedX: {
                                if (searchTabsView.dragSourceIndex < 0
                                        || searchTabsView.dragTargetIndex < 0)
                                    return 0
                                if (searchTabsView.dragSourceIndex < searchTabsView.dragTargetIndex
                                        && index > searchTabsView.dragSourceIndex
                                        && index <= searchTabsView.dragTargetIndex)
                                    return -searchTabsView.draggedTabWidth
                                if (searchTabsView.dragSourceIndex > searchTabsView.dragTargetIndex
                                        && index >= searchTabsView.dragTargetIndex
                                        && index < searchTabsView.dragSourceIndex)
                                    return searchTabsView.draggedTabWidth
                                return 0
                            }

                            width: fittedTabWidth
                            height: searchTabsView.height
                            z: tabDrag.active ? 100 : 1
                            scale: tabDrag.active ? 1.03 : 1
                            opacity: 1
                            transform: Translate {
                                x: tabDrag.active ? tabDrag.translation.x : searchTab.displacedX
                                Behavior on x {
                                    enabled: !tabDrag.active
                                        && searchTabsView.dragSourceIndex >= 0
                                    NumberAnimation { duration: 170; easing.type: Easing.OutCubic }
                                }
                            }
                            Behavior on scale { NumberAnimation { duration: 100 } }
                            Behavior on width {
                                enabled: !tabDrag.active
                                NumberAnimation { duration: 150; easing.type: Easing.OutCubic }
                            }

                            Component.onCompleted: {
                                naturalWidthToken = searchTabsView.allocateNaturalWidthToken()
                                searchTabsView.registerNaturalWidth(
                                    entryKey, naturalTabWidth, naturalWidthToken, current
                                )
                            }
                            Component.onDestruction: searchTabsView.unregisterNaturalWidth(
                                entryKey, naturalWidthToken
                            )
                            onNaturalTabWidthChanged: searchTabsView.registerNaturalWidth(
                                entryKey, naturalTabWidth, naturalWidthToken, current
                            )
                            onCurrentChanged: {
                                searchTabsView.registerNaturalWidth(
                                    entryKey, naturalTabWidth, naturalWidthToken, current
                                )
                                if (current)
                                    Qt.callLater(function() {
                                        searchTabsView.positionViewAtIndex(
                                            searchTab.index, ListView.Contain
                                        )
                                    })
                            }

                            DragHandler {
                                id: tabDrag
                                target: null
                                acceptedButtons: Qt.LeftButton
                                yAxis.enabled: false
                                onTranslationChanged: {
                                    if (!active)
                                        return
                                    var center = searchTab.x + searchTab.width / 2 + translation.x
                                    var target = searchTabsView.indexAt(center, searchTab.height / 2)
                                    if (target < 0)
                                        target = center < 0 ? 0 : searchTabsView.count - 1
                                    searchTab.dragTargetIndex = target
                                    searchTabsView.dragTargetIndex = target
                                }
                                onActiveChanged: {
                                    if (active) {
                                        searchTab.dragTargetIndex = searchTab.index
                                        searchTabsView.dragSourceIndex = searchTab.index
                                        searchTabsView.dragTargetIndex = searchTab.index
                                        searchTabsView.draggedTabWidth = searchTab.width
                                    } else {
                                        const sourceIndex = searchTabsView.dragSourceIndex
                                        const targetIndex = searchTabsView.dragTargetIndex
                                        searchTabsView.dragSourceIndex = -1
                                        searchTabsView.dragTargetIndex = -1
                                        searchTabsView.draggedTabWidth = 0
                                        searchTab.dragTargetIndex = searchTab.index
                                        if (sourceIndex >= 0 && targetIndex >= 0
                                                && sourceIndex !== targetIndex)
                                            workspaceState.reorder_tab(sourceIndex, targetIndex)
                                    }
                                }
                            }

                            Rectangle {
                                anchors.fill: parent
                                visible: tabDrag.active
                                color: root.theme.panelRaised
                            }
                            WorkspaceTabVisual {
                                id: tabVisual
                                z: 2
                                anchors.fill: parent
                                theme: root.theme
                                title: searchTab.title
                                current: searchTab.current
                                closable: searchTab.closable
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
                                    if (mouse.button === Qt.MiddleButton) {
                                        if (searchTab.closable)
                                            workspaceState.close_tab(searchTab.index)
                                        return
                                    }
                                    workspaceState.activate_tab(
                                        searchTab.entryKey, searchTab.title
                                    )
                                }
                            }
                        }
                        ScrollBar.horizontal: Md3ScrollBar {
                            theme: root.theme
                            policy: ScrollBar.AlwaysOff
                        }
                    }

                    CompactIconButton {
                        id: tabOverflowButton
                        visible: searchTabsView.contentWidth > searchTabsView.width + 1
                        Layout.preferredWidth: visible ? 40 : 0
                        Layout.preferredHeight: 40
                        theme: root.theme
                        iconName: "keyboard_arrow_down"
                        round: true
                        toolTip: qsTr("All search tabs")
                        onPressed: tabOverflowMenu.sourceWasOpen = tabOverflowMenu.opened
                        onClicked: {
                            tabOverflowMenu.actions = searchTabsView.allTabActions()
                            tabOverflowMenu.toggleBelow(tabOverflowButton)
                        }
                    }

                    Item {
                        id: tabHistoryControl
                        readonly property int closedTabCount: Math.max(
                            0, appController.closed_search_tabs.length - 2
                        )
                        Layout.preferredWidth: 40
                        Layout.preferredHeight: 40

                        CompactIconButton {
                            id: tabHistoryButton
                            anchors.fill: parent
                            enabled: tabHistoryControl.closedTabCount > 0
                            opacity: enabled ? 1 : 0.38
                            theme: root.theme
                            iconName: "history"
                            round: true
                            toolTip: enabled
                                ? tabHistoryControl.closedTabCount
                                    + (tabHistoryControl.closedTabCount === 1
                                        ? qsTr(" recently closed search tab")
                                        : qsTr(" recently closed search tabs"))
                                : qsTr("No recently closed search tabs")
                            onPressed: tabHistoryMenu.sourceWasOpen = tabHistoryMenu.opened
                            onClicked: tabHistoryMenu.toggleBelow(tabHistoryButton)
                            Behavior on opacity { NumberAnimation { duration: 120 } }
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
                                text: tabHistoryControl.closedTabCount > 99
                                    ? "99+" : tabHistoryControl.closedTabCount
                                color: root.theme.selectedText
                                font.family: root.theme.fontFamily
                                font.pointSize: Typography.label
                                font.weight: Font.Bold
                            }
                            Behavior on scale {
                                NumberAnimation { duration: 160; easing.type: Easing.OutBack }
                            }
                            Behavior on opacity { NumberAnimation { duration: 100 } }
                        }
                    }


                }
                Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: root.theme.separator }
            }
            Rectangle {
                id: resultsToolbar
                // Switch before the expanded pagination controls reach the
                // edge.  The previous 840px threshold ignored page buttons,
                // translated labels and fractional Windows DPI, so the final
                // actions could be laid out beyond the dock.
                property bool compact: width < 1160
                anchors.bottom: parent.bottom
                width: parent.width
                height: root.theme.dockWorkspaceFooterHeight
                color: root.theme.panelRaised
                z: 4

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 8
                    spacing: 8

                    Label {
                        visible: !resultsToolbar.compact
                        text: qsTr("Showing")
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 14
                        font.weight: Font.DemiBold
                    }
                    Rectangle {
                        Layout.preferredHeight: 24
                        Layout.preferredWidth: showingValue.implicitWidth + 16
                        radius: 12
                        color: root.theme.rowHover
                        Label {
                            id: showingValue
                            anchors.centerIn: parent
                            text: appController.loading_mode === "pages"
                                ? appController.first_result + "–"
                                    + appController.last_result + qsTr(" of ")
                                    + appController.result_count
                                : appController.result_count + qsTr(" results")
                            color: root.theme.secondaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Typography.bodyLarge
                            font.weight: Font.Medium
                        }
                    }

                    Item { Layout.fillWidth: true }

                    CompactIconButton {
                        visible: appController.loading_mode === "pages"
                        enabled: appController.current_page > 1
                            && appController.search_state !== "loading"
                        Layout.preferredWidth: 36
                        Layout.preferredHeight: 36
                        theme: root.theme
                        iconName: "chevron_right"
                        rotation: 180
                        round: true
                        toolTip: qsTr("Previous page")
                        onClicked: appController.previous_page()
                    }
                    Row {
                        visible: appController.loading_mode === "pages" && !resultsToolbar.compact
                        spacing: 2
                        Repeater {
                            model: appController.page_numbers
                            delegate: Item {
                                required property var modelData
                                width: 34
                                height: 36
                                Rectangle {
                                    id: bottomPageButton
                                    anchors.centerIn: parent
                                    width: 32
                                    height: 32
                                    radius: 16
                                    color: Number(modelData) === appController.current_page
                                        ? root.theme.action
                                        : bottomPageMouse.containsMouse ? root.theme.rowHover : "transparent"
                                    Label {
                                        anchors.centerIn: parent
                                        text: modelData
                                        color: Number(modelData) === appController.current_page
                                            ? root.theme.selectedText : root.theme.primaryText
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Typography.bodyLarge
                                        font.weight: Font.DemiBold
                                    }
                                    MaterialRipple {
                                        id: bottomPageRipple
                                        shapeRadius: 16
                                        color: root.theme.rippleStrong
                                    }
                                }
                                MouseArea {
                                    id: bottomPageMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    enabled: appController.search_state !== "loading"
                                    cursorShape: Qt.PointingHandCursor
                                    onPressed: mouse => bottomPageRipple.burst(
                                        mouse.x - bottomPageButton.x,
                                        mouse.y - bottomPageButton.y
                                    )
                                    onClicked: appController.go_to_page(Number(modelData))
                                }
                            }
                        }
                    }
                    Label {
                        visible: appController.loading_mode === "pages" && resultsToolbar.compact
                        text: appController.current_page + " / " + appController.page_count
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Typography.bodyLarge
                        font.weight: Font.Medium
                    }
                    CompactIconButton {
                        visible: appController.loading_mode === "pages"
                        enabled: appController.current_page < appController.page_count
                            && appController.search_state !== "loading"
                        Layout.preferredWidth: 36
                        Layout.preferredHeight: 36
                        theme: root.theme
                        iconName: "chevron_right"
                        round: true
                        toolTip: qsTr("Next page")
                        onClicked: appController.next_page()
                    }
                    Item {
                        id: pageSizeButton
                        visible: appController.loading_mode === "pages" && !resultsToolbar.compact
                        Layout.preferredWidth: visible ? 106 : 0
                        Layout.preferredHeight: 40

                        Rectangle {
                            anchors.fill: parent
                            radius: 20
                            color: "transparent"
                            border.width: 1
                            border.color: pageSizeMenu.opened
                                ? root.theme.action : root.theme.outline
                            Behavior on border.color { ColorAnimation { duration: 120 } }
                            Rectangle {
                                anchors.fill: parent
                                radius: parent.radius
                                color: root.theme.primaryText
                                opacity: pageSizeMouse.pressed ? 0.12
                                    : pageSizeMouse.containsMouse ? 0.08 : 0
                                Behavior on opacity {
                                    NumberAnimation {
                                        duration: pageSizeMouse.containsMouse ? 100 : 140
                                        easing.type: Easing.OutCubic
                                    }
                                }
                            }
                        }
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 13
                            anchors.rightMargin: 10
                            spacing: 7
                            Label {
                                Layout.fillWidth: true
                                text: appController.page_size + qsTr(" / page")
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Typography.bodyLarge
                                font.weight: Font.Medium
                            }
                            MaterialIcon {
                                name: "keyboard_arrow_down"
                                size: 16
                                color: root.theme.secondaryText
                                rotation: pageSizeMenu.opened ? 180 : 0
                                Behavior on rotation {
                                    NumberAnimation {
                                        duration: 160
                                        easing.type: Easing.OutCubic
                                    }
                                }
                            }
                        }
                        MaterialRipple {
                            id: pageSizeRipple
                            shapeRadius: 20
                            color: root.theme.ripple
                        }
                        MouseArea {
                            id: pageSizeMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onPressed: mouse => {
                                pageSizeMenu.sourceWasOpen = pageSizeMenu.opened
                                pageSizeRipple.burst(mouse.x, mouse.y)
                            }
                            onClicked: pageSizeMenu.toggleBelow(pageSizeButton)
                        }
                    }

                    Item {
                        id: loadModeButton
                        Layout.preferredWidth: resultsToolbar.compact ? 40 : 164
                        Layout.maximumWidth: resultsToolbar.compact ? 40 : 164
                        Layout.preferredHeight: 40

                        Rectangle {
                            anchors.fill: parent
                            radius: 20
                            color: "transparent"
                            border.width: 1
                            border.color: loadModeMenu.opened ? root.theme.action : root.theme.outline
                            Behavior on border.color { ColorAnimation { duration: 120 } }
                            Rectangle {
                                anchors.fill: parent
                                radius: parent.radius
                                color: root.theme.primaryText
                                opacity: loadModeMouse.pressed ? 0.12
                                    : loadModeMouse.containsMouse ? 0.08 : 0
                                Behavior on opacity {
                                    NumberAnimation {
                                        duration: loadModeMouse.containsMouse ? 100 : 140
                                        easing.type: Easing.OutCubic
                                    }
                                }
                            }
                        }
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: resultsToolbar.compact ? 0 : 14
                            anchors.rightMargin: resultsToolbar.compact ? 0 : 14
                            spacing: resultsToolbar.compact ? 0 : 14
                            MaterialIcon {
                                Layout.fillWidth: resultsToolbar.compact
                                Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
                                name: appController.loading_mode === "pages"
                                    ? "view_kanban" : "layers"
                                size: 18
                                color: loadModeMenu.opened ? root.theme.action : root.theme.secondaryText
                            }
                            Label {
                                visible: !resultsToolbar.compact
                                Layout.fillWidth: true
                                text: appController.loading_mode === "pages"
                                    ? qsTr("Pages") : qsTr("Continuous")
                                color: root.theme.primaryText
                                font.family: root.theme.fontFamily
                                font.pixelSize: 12
                                font.weight: Font.Medium
                            }
                            MaterialIcon {
                                visible: !resultsToolbar.compact
                                name: "keyboard_arrow_down"
                                size: 18
                                color: root.theme.secondaryText
                                rotation: loadModeMenu.opened ? 180 : 0
                                Behavior on rotation {
                                    NumberAnimation { duration: 160; easing.type: Easing.OutCubic }
                                }
                            }
                        }
                        MaterialRipple {
                            id: loadModeRipple
                            shapeRadius: 20
                            color: root.theme.ripple
                        }
                        MouseArea {
                            id: loadModeMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onPressed: mouse => {
                                loadModeMenu.sourceWasOpen = loadModeMenu.opened
                                loadModeRipple.burst(mouse.x, mouse.y)
                            }
                            onClicked: loadModeMenu.toggleBelow(loadModeButton)
                            Md3ToolTip {
                                theme: root.theme
                                visible: resultsToolbar.compact
                                    && loadModeMouse.containsMouse
                                    && !root.theme.suppressToolTips
                                delay: 450
                                text: appController.loading_mode === "pages"
                                    ? qsTr("Pages") : qsTr("Continuous")
                            }
                        }
                    }

                    Rectangle {
                        Layout.preferredWidth: 1
                        Layout.preferredHeight: 24
                        color: root.theme.separator
                    }

                    CompactIconButton {
                        Layout.preferredWidth: 40
                        Layout.preferredHeight: 40
                        theme: root.theme
                        iconName: "repository-sync"
                        round: true
                        toolTip: qsTr("Sync current Search Type")
                        onClicked: appController.open_search_type_repository_sync()
                    }

                    Md3FilledActionButton {
                        Layout.preferredWidth: resultsToolbar.compact
                            ? 40 : implicitWidth
                        Layout.maximumWidth: resultsToolbar.compact ? 40 : 160
                        Layout.preferredHeight: 40
                        theme: root.theme
                        compact: resultsToolbar.compact
                        iconName: "add"
                        text: qsTr("New item")
                        toolTip: resultsToolbar.compact
                            ? qsTr("New item") : ""
                        onClicked: appController.open_window("add_sobject")
                    }
                }
                Rectangle { anchors.top: parent.top; width: parent.width; height: 1; color: root.theme.separator }
            }
            Item {
                id: resultsArea
                anchors.top: searchTabs.bottom
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: resultsToolbar.top
                clip: true
            }
            ListView {
                id: results
                visible: resultsPane.compactRows
                    || appController.results_view_mode !== "tiles"
                readonly property bool interactionMoving:
                    moving || flicking || wheelScroll.running
                property real preservedTreeContentY: 0
                property int remainingScrollRestorePasses: 0
                property real wheelTargetY: contentY
                parent: resultsArea
                x: 8
                y: 8
                width: resultsPane.splitRight
                    ? Math.max(220, Math.round(
                        (resultsArea.width - splitDivider.thickness)
                        * splitDivider.currentRatio
                    )) - 12 : Math.max(0, resultsArea.width - 16)
                height: resultsPane.splitBottom
                    ? Math.max(150, Math.round(
                        (resultsArea.height - splitDivider.thickness)
                        * splitDivider.currentRatio
                    )) - 12 : Math.max(0, resultsArea.height - 16)
                clip: false
                spacing: 3
                model: workspaceModel
                focus: true
                activeFocusOnTab: true
                boundsBehavior: Flickable.StopAtBounds
                flickDeceleration: 3600
                maximumFlickVelocity: 4800
                pixelAligned: false
                // During a live window resize the anchored area can briefly
                // report a negative intermediate height.
                // A height-dependent cache was rebuilt for every native
                // resize tick. Keep enough delegates warm without forcing
                // ListView to recalculate its cache continuously.
                cacheBuffer: 900
                reuseItems: true
                onInteractionMovingChanged: {
                    if (interactionMoving && resultsActionMenu.visible)
                        resultsActionMenu.close()
                }
                Keys.onPressed: function(event) {
                    if (
                        event.key === Qt.Key_A
                        && (event.modifiers & Qt.ControlModifier)
                    ) {
                        appController.select_all_result_siblings()
                        event.accepted = true
                    }
                }
                function toggleResultNodePreservingScroll(
                    nodeId, recursive
                ) {
                    cancelWheelScroll()
                    preservedTreeContentY = contentY
                    remainingScrollRestorePasses = 4
                    appController.toggle_result_node_recursive(
                        nodeId, recursive
                    )
                    treeScrollRestore.restart()
                }

                function revealRestoredSelection() {
                    cancelWheelScroll()
                    const row = workspaceModel.row_for_node(
                        appController.selected_node_id
                    )
                    if (row >= 0)
                        positionViewAtIndex(row, ListView.Contain)
                }

                function cancelWheelScroll() {
                    wheelScroll.stop()
                    wheelTargetY = contentY
                }

                function scrollWithWheel(pixelDelta, angleDelta) {
                    const rawDelta = pixelDelta !== 0
                        ? pixelDelta * 1.65
                        : (angleDelta / 120) * 148
                    if (rawDelta === 0)
                        return
                    const minimumY = originY
                    const maximumY = Math.max(
                        minimumY,
                        minimumY + contentHeight - height
                    )
                    const baseY = wheelScroll.running
                        ? wheelTargetY : contentY
                    wheelTargetY = Math.max(
                        minimumY,
                        Math.min(maximumY, baseY - rawDelta)
                    )
                    wheelScroll.stop()
                    wheelScroll.to = wheelTargetY
                    wheelScroll.start()
                }

                NumberAnimation {
                    id: wheelScroll
                    target: results
                    property: "contentY"
                    duration: 115
                    easing.type: Easing.OutCubic
                }

                WheelHandler {
                    id: resultWheelHandler
                    target: null
                    blocking: true
                    onWheel: function(event) {
                        results.scrollWithWheel(
                            event.pixelDelta.y,
                            event.angleDelta.y
                        )
                        event.accepted = true
                    }
                }

                onFlickStarted: cancelWheelScroll()

                Connections {
                    target: appController
                    function onSection_state_changed() {
                        Qt.callLater(results.revealRestoredSelection)
                    }
                    function onSearch_state_changed() {
                        if (
                            appController.search_state !== "loading"
                            && appController.loading_mode === "infinite"
                            && appController.has_more
                            && results.atYEnd
                            && results.contentHeight <= results.height + 1
                        )
                            Qt.callLater(function() {
                                appController.load_more()
                            })
                    }
                }

                Timer {
                    id: treeScrollRestore
                    interval: 0
                    repeat: true
                    onTriggered: {
                        results.forceLayout()
                        const minimumY = results.originY
                        const maximumY = Math.max(
                            minimumY,
                            minimumY + results.contentHeight - results.height
                        )
                        results.contentY = Math.max(
                            minimumY,
                            Math.min(results.preservedTreeContentY, maximumY)
                        )
                        results.remainingScrollRestorePasses -= 1
                        if (results.remainingScrollRestorePasses <= 0)
                            treeScrollRestore.stop()
                    }
                }

                onAtYEndChanged: {
                    if (
                        atYEnd
                        && !appController.card_can_go_back
                        && appController.loading_mode === "infinite"
                    )
                        appController.load_more()
                }
                delegate: WorkspaceResultItem {
                    theme: root.theme
                    compactMode: resultsPane.compactRows
                    hideVersionSnapshots: resultsPane.splitView
                    externalMenuVisible: resultsActionMenu.visible
                        && resultsActionMenuNodeId === nodeId
                    selected: appController.selected_result_node_ids.indexOf(
                        nodeId
                    ) >= 0
                    onActionMenuRequested: function(
                        selectedNodeId, menuActions, anchorItem,
                        localX, localY, below
                    ) {
                        resultsActionMenuNodeId = selectedNodeId
                        resultsActionMenu.actions = menuActions
                        if (below)
                            resultsActionMenu.openBelow(anchorItem)
                        else
                            resultsActionMenu.openAt(
                                anchorItem, localX, localY
                            )
                    }
                    onSelectedRequested: function(
                        selectedId, selectedKey, selectedType,
                        modifiers, preserveSelection
                    ) {
                        appController.select_result_node(
                            selectedId, selectedKey, selectedType,
                            modifiers, preserveSelection
                        )
                    }
                }
                ScrollBar.vertical: Md3ScrollBar {
                    id: resultsScrollBar
                    theme: root.theme
                    flickableTarget: results

                    onPressedChanged: {
                        if (pressed)
                            results.cancelWheelScroll()
                    }
                }
            }
            property string resultsActionMenuNodeId: ""
            ActionMenu {
                id: resultsActionMenu
                parent: Overlay.overlay
                theme: root.theme
                actions: []
                onTriggered: function(command) {
                    appController.invoke_item_action(
                        command, resultsActionMenuNodeId
                    )
                }
                onSecondaryTriggered: function(command) {
                    appController.invoke_item_action(
                        command, resultsActionMenuNodeId
                    )
                }
            }
            Item {
                id: tileViewport
                parent: resultsArea
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: cardNavigation.bottom
                anchors.bottom: parent.bottom
                visible: !resultsPane.compactRows
                    && appController.results_view_mode === "tiles"
                clip: true
            }
            GridView {
                id: resultTiles
                property real wheelTargetY: contentY
                property var expandedCard: null
                readonly property bool interactionMoving:
                    moving || flicking || tileWheelScroll.running
                parent: tileViewport
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.leftMargin: 14
                anchors.rightMargin: 14
                anchors.topMargin: 12
                anchors.bottomMargin: 8
                visible: tileViewport.visible
                clip: false
                model: workspaceModel
                cellWidth: 230
                cellHeight: appController.card_compact_level ? 178 : 258
                cacheBuffer: 900
                reuseItems: true
                boundsBehavior: Flickable.StopAtBounds
                flickDeceleration: 3600
                maximumFlickVelocity: 4800
                function cancelWheelScroll() {
                    tileWheelScroll.stop()
                    wheelTargetY = contentY
                }
                function scrollWithWheel(pixelDelta, angleDelta) {
                    const delta = pixelDelta !== 0
                        ? pixelDelta * 1.65
                        : (angleDelta / 120) * 148
                    if (delta === 0)
                        return
                    const minimumY = originY
                    const maximumY = Math.max(
                        minimumY, minimumY + contentHeight - height)
                    const baseY = tileWheelScroll.running
                        ? wheelTargetY : contentY
                    wheelTargetY = Math.max(
                        minimumY, Math.min(maximumY, baseY - delta))
                    tileWheelScroll.stop()
                    tileWheelScroll.to = wheelTargetY
                    tileWheelScroll.start()
                }
                NumberAnimation {
                    id: tileWheelScroll
                    target: resultTiles
                    property: "contentY"
                    duration: 115
                    easing.type: Easing.OutCubic
                }
                WheelHandler {
                    target: null
                    blocking: true
                    onWheel: function(event) {
                        resultTiles.scrollWithWheel(
                            event.pixelDelta.y,
                            event.angleDelta.y
                        )
                        event.accepted = true
                    }
                }
                onFlickStarted: cancelWheelScroll()
                onInteractionMovingChanged: {
                    if (interactionMoving && resultsActionMenu.visible)
                        resultsActionMenu.close()
                }
                TapHandler {
                    acceptedButtons: Qt.LeftButton
                    gesturePolicy: TapHandler.ReleaseWithinBounds
                    onTapped: function(eventPoint) {
                        const viewPoint = eventPoint.position
                        const contentPoint = Qt.point(
                            viewPoint.x + resultTiles.contentX,
                            viewPoint.y + resultTiles.contentY
                        )
                        const itemIndex = resultTiles.indexAt(
                            contentPoint.x, contentPoint.y)
                        const item = itemIndex >= 0
                            ? resultTiles.itemAtIndex(itemIndex) : null
                        if (!item) {
                            appController.clear_result_selection()
                            return
                        }
                        const localPoint = item.mapFromItem(
                            resultTiles, viewPoint.x, viewPoint.y)
                        if (
                            localPoint.x < 0 || localPoint.y < 0
                            || localPoint.x > item.width
                            || localPoint.y > item.height
                        )
                            appController.clear_result_selection()
                    }
                }
                delegate: WorkspaceCard {
                    width: resultTiles.cellWidth - 18
                    height: (
                        nodeType === "process" || nodeType === "relation"
                            ? 160 : resultTiles.cellHeight - 14
                    )
                    z: 1
                    theme: root.theme
                    externalMenuVisible: resultsActionMenu.visible
                        && resultsActionMenuNodeId === nodeId
                    selected: appController.selected_result_node_ids.indexOf(
                        nodeId
                    ) >= 0
                    onActionMenuRequested: function(
                        selectedNodeId, menuActions, anchorItem,
                        localX, localY, below
                    ) {
                        resultsActionMenuNodeId = selectedNodeId
                        resultsActionMenu.actions = menuActions
                        if (below)
                            resultsActionMenu.openBelow(anchorItem)
                        else
                            resultsActionMenu.openAt(
                                anchorItem, localX, localY
                            )
                    }
                    onExpandedChanged: {
                        if (expanded)
                            resultTiles.expandedCard = this
                        else if (resultTiles.expandedCard === this)
                            resultTiles.expandedCard = null
                    }
                    Component.onDestruction: {
                        if (resultTiles.expandedCard === this)
                            resultTiles.expandedCard = null
                    }
                }
                onAtYEndChanged: {
                    if (
                        atYEnd
                        && !appController.card_can_go_back
                        && appController.loading_mode === "infinite"
                    )
                        appController.load_more()
                }
                ScrollBar.vertical: Md3ScrollBar {
                    theme: root.theme
                    flickableTarget: resultTiles
                    onPressedChanged: {
                        if (pressed)
                            resultTiles.cancelWheelScroll()
                    }
                }
            }
            Rectangle {
                id: cardNavigation
                parent: resultsArea
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.right: parent.right
                height: visible ? 38 : 0
                visible: !resultsPane.compactRows
                    && appController.results_view_mode === "tiles"
                color: root.theme.panel
                border.color: root.theme.separator
                Row {
                    anchors.fill: parent
                    anchors.leftMargin: 8
                    spacing: 6
                    CompactIconButton {
                        anchors.verticalCenter: parent.verticalCenter
                        visible: appController.card_can_go_back
                        width: 30
                        height: 30
                        theme: root.theme
                        iconName: "arrow-left"
                        round: true
                        backgroundColor: root.theme.panelRaised
                        toolTip: qsTr("Back one level")
                        onClicked: appController.leave_card_level()
                    }
                    Repeater {
                        model: appController.card_breadcrumb
                        delegate: Row {
                            required property var modelData
                            height: cardNavigation.height
                            spacing: 6
                            MaterialIcon {
                                anchors.verticalCenter: parent.verticalCenter
                                visible: modelData.depth > 0
                                name: "chevron-right"
                                size: 11
                                color: root.theme.secondaryText
                            }
                            Rectangle {
                                anchors.verticalCenter: parent.verticalCenter
                                width: crumbRow.implicitWidth + 12
                                height: 26
                                radius: 13
                                color: crumbMouse.containsMouse
                                    && modelData.depth
                                        < appController.card_breadcrumb.length - 1
                                    ? root.theme.panelRaised : "transparent"
                                Row {
                                    id: crumbRow
                                    anchors.centerIn: parent
                                    spacing: 5
                                    MaterialIcon {
                                        name: modelData.icon
                                        size: 13
                                        color: root.theme.action
                                    }
                                    Label {
                                        text: modelData.title
                                        color: root.theme.primaryText
                                        font.family: root.theme.fontFamily
                                        font.pointSize: Typography.body
                                        font.weight: Font.DemiBold
                                    }
                                }
                                MouseArea {
                                    id: crumbMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    enabled: modelData.depth
                                        < appController.card_breadcrumb.length - 1
                                    cursorShape: enabled
                                        ? Qt.PointingHandCursor : Qt.ArrowCursor
                                    onClicked: appController.open_card_breadcrumb(
                                        modelData.depth)
                                }
                            }
                        }
                    }
                }
            }
            ContentLoadingOverlay {
                parent: resultsArea
                anchors.fill: parent
                z: 100
                visible: results.count === 0
                    && appController.search_state === "loading"
                theme: root.theme
                message: "Loading results…"
                cancellable: true
                onCancelRequested: appController.cancel_search()
            }
            Rectangle {
                parent: resultsArea
                anchors.horizontalCenter: results.horizontalCenter
                anchors.bottom: results.bottom
                anchors.bottomMargin: 12
                width: loadingMoreRow.implicitWidth + 28
                height: 36
                radius: 18
                z: 20
                visible: appController.search_state === "loading"
                    && appController.loading_mode === "infinite"
                    && results.count > 0
                color: root.theme.panelRaised
                border.width: 1
                border.color: root.theme.border
                opacity: visible ? 1 : 0
                Behavior on opacity {
                    NumberAnimation {
                        duration: 140
                        easing.type: Easing.OutCubic
                    }
                }
                Row {
                    id: loadingMoreRow
                    anchors.centerIn: parent
                    spacing: 8
                    Md3BusyIndicator {
                        uiTheme: root.theme
                        width: 18
                        height: 18
                        running: parent.parent.visible
                    }
                    Label {
                        anchors.verticalCenter: parent.verticalCenter
                        text: qsTr("Loading more results\u2026")
                        color: root.theme.primaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Typography.body
                        font.weight: Font.DemiBold
                    }
                    CompactIconButton {
                        anchors.verticalCenter: parent.verticalCenter
                        width: 24
                        height: 24
                        theme: root.theme
                        iconName: "close"
                        round: true
                        toolTip: qsTr("Cancel search")
                        onClicked: appController.cancel_search()
                    }
                }
            }
            Rectangle {
                id: versionsPane
                parent: resultsArea
                visible: resultsPane.splitView
                x: resultsPane.splitRight
                    ? results.width + splitDivider.thickness : 0
                y: resultsPane.splitBottom
                    ? results.height + splitDivider.thickness : 0
                width: resultsPane.splitRight
                    ? Math.max(0, resultsArea.width - x) : resultsArea.width
                height: resultsPane.splitBottom
                    ? Math.max(0, resultsArea.height - y) : resultsArea.height
                color: root.theme.panelDeep

                Rectangle {
                    id: versionsHeader
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    height: 36
                    color: root.theme.panelRaised
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 8
                        spacing: 8
                        MaterialIcon {
                            name: "history"
                            size: 16
                            color: root.theme.secondaryText
                        }
                        Label {
                            text: qsTr("Versions")
                            color: root.theme.primaryText
                            font.family: root.theme.fontFamily
                            font.pointSize: Typography.bodyLarge
                            font.weight: Font.DemiBold
                        }
                        Rectangle {
                            Layout.preferredWidth: Math.max(
                                24, versionsCount.implicitWidth + 12
                            )
                            Layout.preferredHeight: 22
                            radius: 11
                            color: root.theme.rowHover
                            Label {
                                id: versionsCount
                                anchors.centerIn: parent
                                text: versionsList.count
                                color: root.theme.secondaryText
                                font.family: root.theme.fontFamily
                                font.pointSize: Typography.body
                                font.weight: Font.DemiBold
                            }
                        }
                        Item { Layout.fillWidth: true }
                    }
                    Rectangle {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        height: 1
                        color: root.theme.separator
                    }
                }

                ListView {
                    id: versionsList
                    readonly property bool interactionMoving: moving || flicking
                    anchors.top: versionsHeader.bottom
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    clip: true
                    spacing: 0
                    model: versionsModel
                    boundsBehavior: Flickable.StopAtBounds
                    reuseItems: true
                    onInteractionMovingChanged: {
                        if (interactionMoving && versionsActionMenu.visible)
                            versionsActionMenu.close()
                    }
                    delegate: WorkspaceResultItem {
                        theme: root.theme
                        externalMenuVisible: versionsActionMenu.visible
                            && versionsPane.menuNodeId === nodeId
                        selected: versionsPane.selectedVersionId === nodeId
                        onActionMenuRequested: function(
                            id, actions, anchorItem, localX, localY, below
                        ) {
                            versionsPane.menuNodeId = id
                            versionsActionMenu.actions = actions
                            if (below)
                                versionsActionMenu.openBelow(anchorItem)
                            else
                                versionsActionMenu.openAt(
                                    anchorItem, localX, localY
                                )
                        }
                        onSelectedRequested: function(
                            selectedId, selectedKey, selectedType,
                            modifiers, preserveSelection
                        ) {
                            versionsPane.selectedVersionId = selectedId
                            appController.select_version_node(selectedId)
                        }
                    }
                    ScrollBar.vertical: Md3ScrollBar {
                        id: versionsScrollBar
                        theme: root.theme
                    }
                }
                property string selectedVersionId: ""
                property string menuNodeId: ""
                ActionMenu {
                    id: versionsActionMenu
                    parent: Overlay.overlay
                    theme: root.theme
                    actions: []
                    onTriggered: function(command) {
                        appController.invoke_item_action(
                            command, versionsPane.menuNodeId
                        )
                    }
                    onSecondaryTriggered: function(command) {
                        appController.invoke_item_action(
                            command, versionsPane.menuNodeId
                        )
                    }
                }
            }
            Rectangle {
                id: splitDivider
                parent: resultsArea
                property real dragRatio: appController.results_splitter_ratio
                property int thickness: resultsPane.splitView ? 7 : 0
                readonly property real currentRatio: dividerMouse.pressed
                    ? dragRatio : appController.results_splitter_ratio
                visible: resultsPane.splitView
                z: 20
                x: resultsPane.splitRight ? results.width : 0
                y: resultsPane.splitBottom ? results.height : 0
                width: resultsPane.splitRight ? thickness : resultsArea.width
                height: resultsPane.splitBottom ? thickness : resultsArea.height
                color: dividerMouse.containsMouse || dividerMouse.pressed
                    ? root.theme.action : root.theme.separator
                opacity: dividerMouse.containsMouse || dividerMouse.pressed
                    ? 0.72 : 0.55
                Behavior on color { ColorAnimation { duration: 110 } }
                Behavior on opacity { NumberAnimation { duration: 110 } }

                MouseArea {
                    id: dividerMouse
                    anchors.fill: parent
                    anchors.margins: -3
                    hoverEnabled: true
                    preventStealing: true
                    cursorShape: resultsPane.splitRight
                        ? Qt.SizeHorCursor : Qt.SizeVerCursor
                    onPressed: splitDivider.dragRatio =
                        appController.results_splitter_ratio
                    onPositionChanged: function(mouse) {
                        if (!pressed)
                            return
                        const point = splitDivider.mapToItem(
                            resultsArea, mouse.x, mouse.y
                        )
                        const extent = resultsPane.splitRight
                            ? resultsArea.width : resultsArea.height
                        const position = resultsPane.splitRight
                            ? point.x : point.y
                        splitDivider.dragRatio = Math.max(
                            0.25, Math.min(0.75, position / Math.max(1, extent))
                        )
                    }
                    onReleased: appController.set_results_splitter_ratio(
                        splitDivider.dragRatio
                    )
                }
            }
            Rectangle {
                id: pageNavigation
                anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom
                height: 0
                color: root.theme.toolBar
                visible: false
                Behavior on height { NumberAnimation { duration: 140; easing.type: Easing.OutCubic } }
                Rectangle { anchors.top: parent.top; width: parent.width; height: 1; color: root.theme.separator }
                RowLayout {
                    anchors.fill: parent; anchors.leftMargin: 7; anchors.rightMargin: 7; spacing: 5
                    Label { text: qsTr("Showing ") + appController.first_result + "–" + appController.last_result + " of " + appController.result_count; color: root.theme.secondaryText; font.family: root.theme.fontFamily; font.pointSize: Typography.label }
                    Item { Layout.fillWidth: true }
                    CompactIconButton { visible: appController.loading_mode === "pages"; enabled: appController.current_page > 1 && appController.search_state !== "loading"; theme: root.theme; iconName: "chevron_right"; rotation: 180; onClicked: appController.previous_page() }
                    Repeater {
                        model: appController.loading_mode === "pages" ? appController.page_numbers : []
                        delegate: Rectangle {
                            required property var modelData
                            Layout.preferredWidth: 24; Layout.preferredHeight: 24
                            radius: 12
                            color: Number(modelData) === appController.current_page ? root.theme.action : pageMouse.containsMouse ? root.theme.rowHover : "transparent"
                            Label { anchors.centerIn: parent; text: modelData; color: Number(modelData) === appController.current_page ? root.theme.selectedText : root.theme.primaryText; font.family: root.theme.fontFamily; font.pointSize: Typography.label; font.weight: Font.DemiBold }
                            MouseArea { id: pageMouse; anchors.fill: parent; hoverEnabled: true; enabled: appController.search_state !== "loading"; cursorShape: Qt.PointingHandCursor; onClicked: appController.go_to_page(Number(modelData)) }
                        }
                    }
                    CompactIconButton { visible: appController.loading_mode === "pages"; enabled: appController.current_page < appController.page_count && appController.search_state !== "loading"; theme: root.theme; iconName: "chevron_right"; onClicked: appController.next_page() }
                    Md3ComboBox {
                        theme: root.theme
                        visible: appController.loading_mode === "pages"
                        Layout.preferredWidth: 66; Layout.preferredHeight: 25
                        model: [20, 25, 50, 100]
                        currentIndex: appController.page_size === 20 ? 0 : appController.page_size === 50 ? 2 : appController.page_size === 100 ? 3 : 1
                        font.pointSize: Typography.label
                        onActivated: appController.set_page_size(Number(currentText))
                    }
                }
            }
            Rectangle {
                parent: resultsArea
                anchors.fill: parent
                z: 100
                visible: results.count === 0
                    && appController.search_state !== "idle"
                    && appController.search_state !== "ready"
                    && appController.search_state !== "loading"
                color: root.theme.workspace
                opacity: visible ? 0.88 : 0
                Behavior on opacity { NumberAnimation { duration: 160 } }
                Column {
                    anchors.centerIn: parent
                    spacing: 10
                    Label {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: appController.search_state === "error"
                            ? appController.search_error
                            : appController.search_state === "cancelled"
                                ? qsTr("Search cancelled")
                                : appController.search_state === "empty"
                                    ? qsTr("No results found")
                                    : qsTr("No results found")
                        color: appController.search_state === "error"
                            ? root.theme.red : root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pixelSize: 12
                        wrapMode: Text.WordWrap
                        horizontalAlignment: Text.AlignHCenter
                        width: Math.min(420, resultsArea.width - 40)
                    }
                    Md3Button {
                        theme: root.theme
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: qsTr("Retry")
                        visible: appController.search_state !== "empty"
                        onClicked: {
                            appController.retry_search()
                        }
                    }
                }
            }
            ActionMenu {
                id: resultFilters; parent: Overlay.overlay; theme: root.theme
                actions: appController.menu_actions("result_filters")
                onTriggered: command => {
                    if (command === "filter_processes")
                        appController.open_window("process_filter_editor")
                    else if (command === "advanced_search")
                        dockModel.show_panel("advanced_search")
                }
            }
            ActionMenu {
                id: resultsViewMenu
                parent: Overlay.overlay
                theme: root.theme
                actions: [
                    {
                        "title": "Continuous tree",
                        "icon": "list-alt",
                        "command": "continious",
                        "checked": appController.results_view_mode
                            === "continious"
                    },
                    {
                        "title": "Cards",
                        "icon": "dashboard",
                        "command": "tiles",
                        "checked": appController.results_view_mode === "tiles"
                    },
                    {
                        "title": "Compact rows",
                        "icon": "view-list",
                        "command": "compact",
                        "checked": appController.results_view_mode
                            === "compact"
                    },
                    {
                        "title": "Versions on the right",
                        "icon": "columns",
                        "command": "splitted_vertical",
                        "checked": appController.results_view_mode
                            === "splitted_vertical"
                    },
                    {
                        "title": "Versions at the bottom",
                        "icon": "align-justify",
                        "command": "splitted_horizontal",
                        "checked": appController.results_view_mode
                            === "splitted_horizontal"
                    }
                ]
                onTriggered: function(command) {
                    appController.set_results_view_mode(command)
                }
            }
            ActionMenu {
                id: loadModeMenu
                parent: Overlay.overlay
                theme: root.theme
                actions: [
                    { "title": "Result loading", "header": true },
                    {
                        "title": "Pages",
                        "icon": "view_kanban",
                        "command": "pages",
                        "checked": appController.loading_mode === "pages"
                    },
                    {
                        "title": "Continuous",
                        "icon": "layers",
                        "command": "infinite",
                        "checked": appController.loading_mode === "infinite"
                    }
                ]
                onTriggered: command => appController.set_loading_mode(command)
            }
            ActionMenu {
                id: pageSizeMenu
                parent: Overlay.overlay
                theme: root.theme
                actions: [
                    { "title": "Items per page", "header": true },
                    {
                        "title": "20 items",
                        "icon": "list",
                        "command": "page_size:20",
                        "checked": appController.page_size === 20
                    },
                    {
                        "title": "25 items",
                        "icon": "list",
                        "command": "page_size:25",
                        "checked": appController.page_size === 25
                    },
                    {
                        "title": "50 items",
                        "icon": "list",
                        "command": "page_size:50",
                        "checked": appController.page_size === 50
                    },
                    {
                        "title": "100 items",
                        "icon": "list",
                        "command": "page_size:100",
                        "checked": appController.page_size === 100
                    }
                ]
                onTriggered: command => {
                    if (command.indexOf("page_size:") === 0)
                        appController.set_page_size(Number(command.slice(10)))
                }
            }
            ActionMenu {
                id: tabOverflowMenu
                parent: Overlay.overlay
                theme: root.theme
                onTriggered: command => {
                    if (command.indexOf("tab:") !== 0)
                        return
                    searchTabsView.revealTab(Number(command.slice(4)))
                }
            }
            ActionMenu {
                id: tabHistoryMenu
                parent: Overlay.overlay
                theme: root.theme
                actions: appController.closed_search_tabs
                onTriggered: command => {
                    if (command === "clear_history") {
                        appController.clear_search_tab_history()
                        return
                    }
                    if (command.indexOf("restore_tab:") === 0)
                        appController.restore_closed_search_tab(
                            Number(command.slice(12))
                        )
                }
            }
        }
    }
    Component {
        id: snapshotContentV2
        SnapshotBrowser {
            theme: root.theme
            onNotice: message => root.notice(message)
        }
    }
    Component {
        id: snapshotContent
        Item {
            id: snapshotPane
            property string contextNodeId: ""
            property bool showAllFiles: false
            property bool showMoreInfo: false
            property bool horizontalFiles: false
            Rectangle { anchors.fill: parent; color: root.theme.workspace }
            Rectangle {
                id: snapshotToolbar
                anchors.top: parent.top; width: parent.width; height: 28; color: root.theme.toolBar
                RowLayout { anchors.fill: parent; anchors.leftMargin: 7; anchors.rightMargin: 5; spacing: 3
                    CompactIconButton { theme: root.theme; iconName: "visibility"; toolTip: qsTr("Show all files"); onClicked: snapshotPane.showAllFiles = !snapshotPane.showAllFiles }
                    CompactIconButton {
                        id: snapshotSettingsButton
                        theme: root.theme
                        iconName: "tune"
                        toolTip: qsTr("Browser settings")
                        onClicked: snapshotSettings.openBelow(snapshotSettingsButton)
                    }
                    Item { Layout.fillWidth: true }
                    RefreshIconButton { theme: root.theme; toolTip: qsTr("Refresh snapshots"); onClicked: root.notice("Refreshing snapshots") }
                }
                Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: root.theme.separator }
            }
            Rectangle {
                id: previewArea
                property string currentPreview: ""
                property string currentTitle: "Preview"
                property string currentContext: ""
                property var currentItems: []
                property var currentFiles: []
                property int currentIndex: 0
                anchors.top: snapshotToolbar.bottom; anchors.left: parent.left; anchors.right: parent.right
                anchors.margins: 7; height: Math.max(100, parent.height * 0.40)
                color: "#1d1d1d"; border.color: root.theme.border; border.width: 1
                Column { anchors.centerIn: parent; spacing: 7
                    ItemPreview {
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: 96; height: 64
                        theme: root.theme
                        source: previewArea.currentPreview
                        fallbackIcon: "movie"
                        accent: "#34515d"
                        round: false
                    }
                    Label {
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: Math.min(220, previewArea.width - 20)
                        horizontalAlignment: Text.AlignHCenter
                        text: previewArea.currentTitle
                        color: root.theme.secondaryText
                        font.family: root.theme.fontFamily
                        font.pointSize: Typography.body
                        elide: Text.ElideMiddle
                    }
                }
                PreviewNavigationButton {
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    theme: root.theme
                    iconName: "chevron_left"
                    toolTip: qsTr("Previous preview")
                    opacity: previewMouse.containsMouse && previewArea.currentItems.length > 1 ? 1 : 0
                    Behavior on opacity { NumberAnimation { duration: 180 } }
                    onClicked: previewArea.currentIndex
                        = (previewArea.currentIndex - 1
                            + previewArea.currentItems.length)
                            % previewArea.currentItems.length
                }
                PreviewNavigationButton {
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    theme: root.theme
                    iconName: "chevron_right"
                    toolTip: qsTr("Next preview")
                    opacity: previewMouse.containsMouse && previewArea.currentItems.length > 1 ? 1 : 0
                    Behavior on opacity { NumberAnimation { duration: 180 } }
                    onClicked: previewArea.currentIndex
                        = (previewArea.currentIndex + 1)
                            % previewArea.currentItems.length
                }
                MouseArea { id: previewMouse; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.RightButton
                    onWheel: wheel => { if (previewArea.currentItems.length > 1) previewArea.currentIndex = (previewArea.currentIndex + (wheel.angleDelta.y < 0 ? 1 : -1) + previewArea.currentItems.length) % previewArea.currentItems.length }
                    onClicked: mouse => { if (mouse.button === Qt.RightButton) { snapshotContext.actions = appController.item_menu_actions(snapshotPane.contextNodeId); snapshotContext.openAt(previewArea, mouse.x, mouse.y) } }
                }
                Row { anchors.horizontalCenter: parent.horizontalCenter; anchors.bottom: parent.bottom; anchors.bottomMargin: 5; spacing: 4
                    Repeater { model: previewArea.currentItems.length
                        delegate: Rectangle { width: 6; height: 6; radius: 3; color: index === previewArea.currentIndex ? root.theme.accent : "#88ffffff" }
                    }
                }
                onCurrentIndexChanged: {
                    if (currentItems.length > 0) {
                        var item = currentItems[currentIndex % currentItems.length]
                        currentPreview = item.url || ""
                        currentTitle = item.title || "Preview"
                    }
                }
            }
            ListView {
                id: snapshots
                anchors.top: previewArea.bottom; anchors.topMargin: 3
                anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: filesPanel.top
                clip: true; model: snapshotModel
                delegate: Item {
                    id: snapshotRow
                    required property int index
                    required property string title
                    required property string path
                    required property string version
                    required property string context
                    required property string kind
                    required property bool selected
                    required property string nodeId
                    required property string previewUrl
                    required property string accent
                    required property bool fileExists
                    required property bool isLatest
                    required property var previewItems
                    required property var files
                    width: snapshots.width; height: 56
                    Component.onCompleted: {
                        if (snapshotRow.index === 0) {
                            previewArea.currentPreview = snapshotRow.previewUrl
                            previewArea.currentTitle = snapshotRow.title
                            previewArea.currentContext = snapshotRow.context
                            previewArea.currentItems = snapshotRow.previewItems || []
                            previewArea.currentFiles = snapshotRow.files || []
                            previewArea.currentIndex = 0
                        }
                    }
                    ItemSurface {
                        anchors.fill: parent
                        theme: root.theme
                        selected: snapshotRow.selected
                        selectedColor: root.theme.contentSelection
                        hovered: snapshotMouse.containsMouse || snapshotPane.contextNodeId === snapshotRow.nodeId
                        accent: snapshotRow.accent
                    }
                    RowLayout { anchors.fill: parent; anchors.leftMargin: 9; anchors.rightMargin: 7; spacing: 7
                        ItemPreview {
                            Layout.preferredWidth: 38; Layout.preferredHeight: 38
                            theme: root.theme
                            source: snapshotRow.previewUrl
                            fallbackIcon: snapshotRow.kind === "image" ? "image" : "movie"
                            accent: snapshotRow.accent
                            round: false
                            selected: snapshotRow.selected
                        }
                        ColumnLayout { Layout.fillWidth: true; spacing: 0
                            Label { text: title; color: snapshotRow.selected ? root.theme.selectedText : root.theme.primaryText; font.family: root.theme.fontFamily; font.pointSize: Typography.body; elide: Text.ElideRight; Layout.fillWidth: true }
                            Label { text: context + " · " + path; color: selected ? "#e2edf3" : root.theme.secondaryText; font.family: root.theme.fontFamily; font.pointSize: Typography.label; elide: Text.ElideRight; Layout.fillWidth: true }
                        }
                        MaterialIcon { visible: snapshotRow.isLatest; name: "verified"; size: 13; color: snapshotRow.selected ? root.theme.selectedText : root.theme.accent }
                        Label { text: version; color: snapshotRow.selected ? root.theme.selectedText : root.theme.secondaryText; font.family: root.theme.fontFamily; font.pointSize: Typography.body }
                    }
                    MouseArea {
                        id: snapshotMouse; anchors.fill: parent; hoverEnabled: true
                        acceptedButtons: Qt.LeftButton | Qt.RightButton
                        cursorShape: Qt.PointingHandCursor
                        onClicked: mouse => {
                            snapshotModel.select_row(snapshotRow.index)
                            previewArea.currentPreview = snapshotRow.previewUrl
                            previewArea.currentTitle = snapshotRow.title
                            previewArea.currentContext = snapshotRow.context
                            previewArea.currentItems = snapshotRow.previewItems || []
                            previewArea.currentFiles = snapshotRow.files || []
                            previewArea.currentIndex = 0
                            if (mouse.button === Qt.RightButton) {
                                snapshotPane.contextNodeId = snapshotRow.nodeId
                                snapshotContext.actions = appController.item_menu_actions(snapshotRow.nodeId)
                                snapshotContext.openAt(snapshotRow, mouse.x, mouse.y)
                            }
                            else root.notice("Selected snapshot: " + snapshotRow.title)
                        }
                    }
                }
                ScrollBar.vertical: Md3ScrollBar { theme: root.theme }
            }
            Rectangle {
                id: filesPanel
                anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom
                height: Math.max(80, Math.min(180, parent.height * 0.25)); color: root.theme.panelDeep
                border.color: root.theme.separator; border.width: 1
                ColumnLayout { anchors.fill: parent; spacing: 0
                    RowLayout { Layout.fillWidth: true; Layout.preferredHeight: 25; spacing: 5
                        Label { text: snapshotPane.showAllFiles ? "Files (all)" : "Preview files"; color: root.theme.secondaryText; font.pointSize: Typography.body; Layout.fillWidth: true; leftPadding: 8 }
                        Label { text: previewArea.currentFiles.length + " files"; color: root.theme.secondaryText; font.pointSize: Typography.label }
                    }
                    ListView { Layout.fillWidth: true; Layout.fillHeight: true; clip: true; model: previewArea.currentFiles
                        delegate: Item { width: ListView.view.width; height: 24
                            RowLayout { anchors.fill: parent; anchors.leftMargin: 8; anchors.rightMargin: 8; spacing: 6
                                MaterialIcon { name: modelData.type === "image" || modelData.type === "icon" ? "image" : "insert_drive_file"; size: 14; color: modelData.exists ? root.theme.accent : root.theme.secondaryText }
                                Label { text: modelData.name || "Unnamed file"; color: root.theme.primaryText; font.pointSize: Typography.label; elide: Text.ElideMiddle; Layout.fillWidth: true }
                                Label { visible: snapshotPane.showMoreInfo; text: modelData.size || ""; color: root.theme.secondaryText; font.pointSize: Typography.label }
                                Label { visible: snapshotPane.showMoreInfo; text: modelData.type || ""; color: root.theme.secondaryText; font.pointSize: Typography.label }
                            }
                            MouseArea { anchors.fill: parent; acceptedButtons: Qt.RightButton; onClicked: mouse => { snapshotContext.actions = appController.item_menu_actions(snapshotPane.contextNodeId); snapshotContext.openAt(parent, mouse.x, mouse.y) } }
                        }
                    }
                }
            }
            ActionMenu {
                id: snapshotSettings; parent: Overlay.overlay; theme: root.theme
                actions: appController.menu_actions("snapshot_settings")
                onTriggered: command => {
                    if (command === "show_all") snapshotPane.showAllFiles = !snapshotPane.showAllFiles
                    else if (command === "show_more") snapshotPane.showMoreInfo = !snapshotPane.showMoreInfo
                    else if (command === "horizontal") snapshotPane.horizontalFiles = true
                    else if (command === "vertical") snapshotPane.horizontalFiles = false
                    else root.notice("Snapshot Browser: " + command)
                }
            }
            ActionMenu {
                id: snapshotContext; parent: Overlay.overlay; theme: root.theme
                actions: []
                onClosed: snapshotPane.contextNodeId = ""
                onTriggered: command => {
                    if (snapshotPane.contextNodeId !== "")
                        appController.invoke_item_action(command, snapshotPane.contextNodeId)
                }
            }
        }
    }
    Component {
        id: tasksContent
        TaskDockView { theme: root.theme }
    }
    Component {
        id: taskCalendarContent
        TaskCalendarView { theme: root.theme }
    }
    Component {
        id: timesheetContent
        TimesheetView { theme: root.theme }
    }
    Component {
        id: workReportsContent
        WorkReportsView { theme: root.theme }
    }
    Component {
        id: costReportsContent
        CostReportsView { theme: root.theme }
    }
    Component {
        id: descriptionContent
        DescriptionEditor {
            theme: root.theme
            anchors.fill: parent
            showTargetHeader: false
            value: workspaceState ? workspaceState.description : ""
            targetTitle: workspaceState
                ? workspaceState.descriptionTargetTitle : ""
            targetKind: workspaceState
                ? workspaceState.descriptionTargetKind : ""
            editing: Boolean(workspaceState && workspaceState.descriptionEditing)
            pinned: Boolean(workspaceState && workspaceState.descriptionPinned)
            dirty: Boolean(workspaceState && workspaceState.descriptionDirty)
            saving: Boolean(workspaceState && workspaceState.descriptionSaving)
            canSave: Boolean(workspaceState && workspaceState.descriptionCanSave)
            editorEnabled: Boolean(workspaceState && workspaceState.descriptionTargetTitle.length)
            errorText: workspaceState ? workspaceState.descriptionError : ""
            onEditRequested: workspaceState.begin_description_edit()
            onValueEdited: value => workspaceState.set_description(value)
            onSaveRequested: workspaceState.commit_description()
            onCancelRequested: workspaceState.cancel_description_edit()
            onPinRequested: workspaceState.freeze_description()
            onUnpinRequested: workspaceState.unfreeze_description()
        }
    }
    Component {
        id: notesContent
        CommunicationView { theme: root.theme; compact: true }
    }
    Component {
        id: dropPlateContent
        DropPlateView { theme: root.theme }
    }
    Component {
        id: advancedSearchContent
        AdvancedSearchView { theme: root.theme }
    }
    Component {
        id: fastControlsContent
        Item {
            Rectangle { anchors.fill: parent; color: root.theme.panelDeep }
            Flow {
                anchors.fill: parent; anchors.margins: 8; spacing: 9
                Repeater {
                    model: fastControlModel
                    delegate: Column {
                        required property string label
                        required property string value
                        required property string choices
                        width: Math.max(110, Math.min(165, parent.width / 4 - 11)); spacing: 3
                        Label { text: label; color: root.theme.secondaryText; font.family: root.theme.fontFamily; font.pointSize: Typography.label }
                        Md3ComboBox { theme: root.theme; width: parent.width; height: 27; model: choices.split(","); currentIndex: Math.max(0, model.indexOf(value)); font.family: root.theme.fontFamily; font.pointSize: Typography.label }
                    }
                }
            }
        }
    }
    Component {
        id: repoSyncContent
        RepositorySyncView {
            theme: root.theme
        }
    }
    Component {
        id: legacyRepoSyncContent
        Item {
            Rectangle { anchors.fill: parent; color: root.theme.panelDeep }
            Rectangle {
                id: syncToolbar
                anchors.top: parent.top; width: parent.width; height: 31; color: root.theme.toolBar
                RowLayout { anchors.fill: parent; anchors.leftMargin: 7; anchors.rightMargin: 5; spacing: 4
                    Md3ComboBox { theme: root.theme; Layout.preferredWidth: 130; Layout.preferredHeight: 25; model: syncPresetModel; textRole: "label"; font.pointSize: Typography.label }
                    Item { Layout.fillWidth: true }
                    CompactIconButton { theme: root.theme; iconName: "repository-sync"; onClicked: root.notice("Starting repository synchronization") }
                    CompactIconButton { theme: root.theme; iconName: "close"; onClicked: repoSyncModel.clear() }
                }
            }
            ListView {
                id: syncList
                anchors.top: syncToolbar.bottom; anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: syncFooter.top
                clip: true; model: repoSyncModel
                delegate: Item {
                    id: syncRow
                    required property int index
                    required property string title
                    required property string process
                    required property string progress
                    required property string status
                    required property bool checked
                    width: syncList.width; height: 46
                    ItemSurface { anchors.fill: parent; theme: root.theme; hovered: syncMouse.containsMouse; accent: root.theme.cyan }
                    RowLayout { anchors.fill: parent; anchors.leftMargin: 7; anchors.rightMargin: 7; spacing: 6
                        Md3CheckBox { theme: root.theme; checked: syncRow.checked; onToggled: repoSyncModel.toggle_checked(syncRow.index) }
                        MaterialIcon { name: "sync"; size: 15; color: root.theme.cyan }
                        ColumnLayout { Layout.fillWidth: true; spacing: 1
                            Label { text: title; color: root.theme.primaryText; font.family: root.theme.fontFamily; font.pointSize: Typography.body; Layout.fillWidth: true; elide: Text.ElideRight }
                            Label { text: process + " · " + status; color: root.theme.secondaryText; font.family: root.theme.fontFamily; font.pointSize: Typography.label; Layout.fillWidth: true; elide: Text.ElideRight }
                        }
                        Label { text: progress; color: root.theme.secondaryText; font.family: root.theme.fontFamily; font.pointSize: Typography.label }
                    }
                    MouseArea {
                        id: syncMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        acceptedButtons: Qt.RightButton
                        onClicked: function(mouse) { syncContext.openAt(syncRow, mouse.x, mouse.y) }
                    }
                }
                ScrollBar.vertical: Md3ScrollBar { theme: root.theme }
            }
            Rectangle {
                id: syncFooter
                anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom; height: 28; color: root.theme.toolBar
                RowLayout { anchors.fill: parent; anchors.leftMargin: 8; anchors.rightMargin: 6
                    Label { text: qsTr("Repository sync queue"); color: root.theme.secondaryText; font.family: root.theme.fontFamily; font.pointSize: Typography.body; Layout.fillWidth: true }
                    CompactIconButton { theme: root.theme; iconName: "sync"; onClicked: root.notice("Sync selected") }
                }
            }
            ActionMenu {
                id: syncContext; parent: Overlay.overlay; theme: root.theme
                actions: appController.menu_actions("repo_sync")
                onTriggered: command => root.notice("Repository Sync: " + command)
            }
        }
    }
    Component {
        id: commitQueueContent
        CommitQueueView { theme: root.theme }
    }
    Component {
        id: databaseEditorContent
        DatabaseEditorView { theme: root.theme }
    }

    Component {
        id: watchFoldersContent
        WatchFoldersView { theme: root.theme }
    }
}

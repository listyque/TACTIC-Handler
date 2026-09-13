import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Item {
    id: root
    required property var theme
    property var columnsController: typeof columnsEditorController !== "undefined"
        ? columnsEditorController : null

    Rectangle { anchors.fill: parent; color: root.theme.workspace }
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 12
        RowLayout {
            Layout.fillWidth: true
            ColumnLayout {
                Layout.fillWidth: true
                Label {
                    Layout.fillWidth: true
                    text: String(sidebarEditorController.selectedEntry.title || "")
                    color: root.theme.primaryText
                    font.family: root.theme.fontFamily
                    font.pointSize: Controls.Typography.bodyLarge
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }
                Label {
                    Layout.fillWidth: true
                    text: qsTr("Saved searches and quick filters for this sidebar item")
                    color: root.theme.secondaryText
                    wrapMode: Text.WordWrap
                }
            }
            Controls.Button {
                id: quickFiltersButton
                objectName: "previewQuickFiltersButton"
                theme: root.theme
                text: qsTr("Quick filters")
                icon.name: "filter-alt"
                onPressed: quickFilters.sourceWasOpen = quickFilters.opened
                onClicked: {
                    if (!quickFilters.sourceWasOpen && !quickFilters.opened)
                        appController.request_quick_filter_data(false)
                    quickFilters.toggleBelow(quickFiltersButton)
                }
            }
            Controls.Button {
                theme: root.theme
                text: qsTr("Close")
                onClicked: windowModel.close_window("sidebar_search_preview")
            }
        }
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 12
            AdvancedSearchView {
                id: searchEditor
                objectName: "previewSearchEditor"
                Layout.preferredWidth: 430
                Layout.fillHeight: true
                theme: root.theme
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: root.theme.surfaceContainerLow
                radius: root.theme.sectionRadius
                border.color: root.theme.outlineVariant
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 8
                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            Layout.fillWidth: true
                            text: qsTr("Results: %1").arg(appController.result_count)
                            color: root.theme.primaryText
                            font.pointSize: Controls.Typography.bodyLarge
                        }
                        Controls.ComboBox {
                            objectName: "previewResultViewMode"
                            Layout.preferredWidth: 240
                            theme: root.theme
                            textRole: "label"
                            valueRole: "value"
                            iconRole: "icon"
                            translateDisplayText: false
                            model: sidebarEditorController.resultViewOptions
                            currentIndex: {
                                for (let row = 0; row < model.length; ++row) {
                                    if (model[row].value === appController.results_view_mode)
                                        return row
                                }
                                return -1
                            }
                            onActivated: sidebarEditorController.set_preview_view_mode(currentValue)
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        Controls.Button {
                            id: searchFiltersButton
                            objectName: "previewSearchFiltersButton"
                            theme: root.theme
                            text: qsTr("Search filters and presets")
                            icon.name: "advanced-search"
                            onClicked: resultMenus.openFilters(searchFiltersButton)
                        }
                        Item { Layout.fillWidth: true }
                        Controls.CompactIconButton {
                            id: sortButton
                            objectName: "previewSortButton"
                            Layout.preferredWidth: 40
                            Layout.preferredHeight: 40
                            theme: root.theme
                            iconName: "sort-items"
                            iconColor: resultMenus.sortOpened || appController.result_sort_mode !== "name_asc"
                                ? root.theme.action : root.theme.primaryText
                            backgroundColor: resultMenus.sortOpened
                                ? root.theme.secondaryContainer : "transparent"
                            round: true
                            toolTip: qsTr("Sort items")
                            onClicked: resultMenus.openSort(sortButton)
                        }
                        Controls.CompactIconButton {
                            id: groupButton
                            objectName: "previewGroupButton"
                            Layout.preferredWidth: 40
                            Layout.preferredHeight: 40
                            theme: root.theme
                            iconName: "group-items"
                            iconColor: resultMenus.groupOpened || appController.result_group_mode !== "none"
                                ? root.theme.action : root.theme.primaryText
                            backgroundColor: resultMenus.groupOpened
                                ? root.theme.secondaryContainer : "transparent"
                            round: true
                            toolTip: qsTr("Group items")
                            onClicked: resultMenus.openGroup(groupButton)
                        }
                    }
                    SearchResultsPane {
                        id: results
                        objectName: "sidebarPreviewResults"
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        theme: root.theme
                        controller: appController
                        columnsController: root.columnsController
                        userModel: userListModel
                        surfacesModel: sidebarEditorController.previewSurfaces
                        versionResultsModel: versionsModel
                    }
                    Label {
                        Layout.fillWidth: true
                        text: qsTr("View changes become this item's default when you save Sidebar Editor.")
                        color: root.theme.secondaryText
                        font.pointSize: Controls.Typography.label
                        wrapMode: Text.WordWrap
                    }
                    RowLayout {
                        Layout.alignment: Qt.AlignHCenter
                        visible: appController.loading_mode === "pages" || appController.has_more
                        enabled: appController.search_state !== "loading"
                        Controls.CompactIconButton {
                            theme: root.theme
                            visible: appController.loading_mode === "pages"
                            iconName: "chevron_left"
                            toolTip: qsTr("Previous page")
                            enabled: appController.current_page > 1
                            onClicked: appController.previous_page()
                        }
                        Label {
                            visible: appController.loading_mode === "pages"
                            text: appController.current_page + " / " + appController.page_count
                            color: root.theme.secondaryText
                        }
                        Controls.Button {
                            objectName: "previewNextPage"
                            theme: root.theme
                            text: appController.loading_mode === "pages" ? qsTr("Next page") : qsTr("Load more")
                            enabled: appController.loading_mode === "pages"
                                ? appController.current_page < appController.page_count : appController.has_more
                            onClicked: {
                                if (appController.loading_mode === "pages")
                                    appController.next_page()
                                else
                                    appController.load_more()
                            }
                        }
                    }
                }
            }
        }
    }
    SearchResultMenus {
        id: resultMenus
        theme: root.theme
        application: appController
        filterController: filterEditorController
        presets: filterPresetModel
        onProcessFilterRequested: {
            processFilterEditorController.begin_session()
            windowModel.show_child_window("process_filter_editor", "sidebar_search_preview")
        }
        onSearchEditorRequested: {
            searchEditor.filtersExpanded = true
            searchEditor.forceActiveFocus()
        }
    }
    SearchQuickFilterPopup {
        id: quickFilters
        objectName: "previewQuickFiltersPopup"
        theme: root.theme
        controller: appController
        editorController: quickFilterEditorController
        onEditRequested: windowModel.show_child_window("quick_filter_editor", "sidebar_search_preview")
        onAssigneesRequested: assignees.openBelow(quickFiltersButton)
    }
    SearchAssigneeFilterPopup {
        id: assignees
        theme: root.theme
        controller: appController
    }
}

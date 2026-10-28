import QtQuick
import "../.." as Shell
import "../../controls" as Controls
import "../../tactic_frame" as Frame
import "../../tactic_frame/features/table/items.ui.mjs" as Items

Frame.FrameView {
    id: root
    required property var controller
    required property var owner
    required property var columnsController
    required property var users
    required property var surfacesModel
    required property var versionsModel
    property var previewItems: null
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    scene: Items.describe({
        busy: !previewItems && controller.search_state === "loading",
        error: previewItems ? "" : controller.search_error,
        hasMore: !previewItems && controller.has_more
    }, width, height, language)
    views: ({
            itemSearch: previewItems ? previewSearchComponent : searchComponent,
            itemResults: {
                component: previewItems ? previewComponent : resultsComponent
            }
        })
    onEvent: action => {
        if (action.type === "more")
            owner.load_item_page();
        else
            owner.reload_item_results();
    }
    Component {
        id: previewSearchComponent
        Controls.SearchField {
            anchors.fill: parent
            theme: root.theme
            enabled: false
            placeholderText: qsTr("Search objects")
        }
    }
    Component {
        id: previewComponent
        Shell.SearchResultSurface {
            enabled: false
            theme: root.theme
            controller: root.controller
            expansionOwner: root.previewItems
            resultModel: root.previewItems.previewModel
            configuredLayout: root.previewItems.model.liveInterface?.table?.item_layout || null
            viewMode: "continious"
            layoutEditing: true
            current: true
            presentationActive: visible
        }
    }
    Component {
        id: searchComponent
        Shell.TacticSearchField {
            anchors.fill: parent
            theme: root.theme
            controller: root.controller
            suggestionModel: root.controller.searchSuggestions
            placeholderText: qsTr("Search objects")
        }
    }
    Component {
        id: resultsComponent
        Shell.SearchResultsPane {
            theme: root.theme
            controller: root.controller
            columnsController: root.columnsController
            userModel: root.users
            surfacesModel: root.surfacesModel
            versionResultsModel: root.versionsModel
            presentationActive: visible
        }
    }
}

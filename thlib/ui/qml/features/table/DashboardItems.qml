import QtQuick
import "../.." as Shell
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
    readonly property string language: typeof localizationController === "undefined" ? "en" : localizationController.current_language
    scene: Items.describe({
        busy: controller.search_state === "loading",
        error: controller.search_error,
        hasMore: controller.has_more
    }, width, height, language)
    views: ({
            itemResults: {
                component: resultsComponent
            }
        })
    onEvent: action => {
        if (action.type === "more")
            owner.load_item_page();
        else
            owner.reload_item_results();
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

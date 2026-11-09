import QtQuick
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/core/foundation.mjs" as Foundation
import "../../../tactic_frame/controls/buttons/metrics.mjs" as ButtonMetrics
import "../../../tactic_frame/features/files/workspace/catalog.ui.mjs" as UI

Item {
    id: root
    required property var theme
    required property var controller
    readonly property var workspaceState: controller.view_data
    readonly property string language: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language
    property real desktopExtent: -1
    property real mobileExtent: -1
    FontMetrics {
        id: fontMetrics
        font: Qt.font({
            family: root.theme.fontFamily,
            pixelSize: Foundation.textStyles.body,
            weight: Font.DemiBold,
            hintingPreference: Font.PreferVerticalHinting
        })
    }
    readonly property var frameModel: ({
            native: true,
            source: workspaceState.catalog_source,
            selected: workspaceState.catalog_detail,
            count: controller.catalog_model.count(),
            busy: controller.busy,
            workspace: workspaceState.workspace,
            after: workspaceState.catalog_after,
            buttonWidths: UI.workspaceActions({}, language).map(action => ButtonMetrics.buttonWidth(fontMetrics.advanceWidth(action.text), true)),
            extent: width < 600 ? (mobileExtent < 0 ? undefined : mobileExtent) : (desktopExtent < 0 ? undefined : desktopExtent)
        })
    FileWorkspaceDepots {
        anchors.fill: parent
        theme: root.theme
        controller: root.controller
        visible: root.workspaceState.catalog_source === "depots"
    }
    FileWorkspaceStorage {
        anchors.fill: parent
        theme: root.theme
        controller: root.controller
        visible: root.workspaceState.catalog_source === "storage"
    }
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        visible: !["depots", "storage"].includes(root.workspaceState.catalog_source)
        scene: UI.describe(root.frameModel, width, height, root.language)
        models: ({
                catalog: root.controller.catalog_model
            })
        describeRow: (list, record) => UI.row(root.frameModel, record, list.width - 16, root.language)
        onEvent: action => {
            if (action.type === "split") {
                if (root.width < 600)
                    root.mobileExtent = action.value;
                else
                    root.desktopExtent = action.value;
            } else if (action.type === "select") {
                const record = root.controller.catalog_model.records().find(row => row.id === action.key);
                if (record)
                    root.controller.set_value("catalog_detail", record.node);
            } else if (action.type === "refresh")
                root.controller.action("catalog_page", {});
            else if (action.type === "more")
                root.controller.action("catalog_page", {
                    more: true
                });
            else if (action.type === "switch")
                root.controller.action("preview_workspace_switch", {
                    workspace: root.workspaceState.catalog_detail.code
                });
            else if (action.type === "edit")
                root.controller.action("edit_workspace", {});
            else if (action.type === "setup")
                root.controller.set_value("setup", true);
        }
    }
}

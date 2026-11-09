import QtQuick
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/core/foundation.mjs" as Foundation
import "../../../tactic_frame/controls/buttons/metrics.mjs" as ButtonMetrics
import "../../../tactic_frame/features/files/workspace/navigation.ui.mjs" as UI

Item {
    id: root
    required property var theme
    required property var controller
    readonly property var workspaceState: controller.view_data
    readonly property string language: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language
    signal menuRequested(string kind, var anchor)
    property var pathDraft: null
    readonly property string currentPath: "//" + workspaceState.stream + "/" + workspaceState.prefix
    onCurrentPathChanged: pathDraft = null
    FontMetrics {
        id: fontMetrics
        font: Qt.font({
            family: root.theme.fontFamily,
            pixelSize: Foundation.textStyles.body,
            weight: Font.DemiBold,
            hintingPreference: Font.PreferVerticalHinting
        })
    }
    readonly property var presentation: UI.describe({
        style: theme.style,
        workspaces: workspaceState.workspaces,
        workspace: workspaceState.workspace,
        busy: controller.busy,
        navigationIndex: workspaceState.navigation_index,
        navigationCount: workspaceState.navigation.length,
        path: pathDraft === null ? currentPath : pathDraft,
        recovery: workspaceState.recovery.available || workspaceState.recovery.action,
        connectionState: workspaceState.connection_state,
        actionWidths: [ButtonMetrics.buttonWidth(fontMetrics.advanceWidth(qsTr("Actions")), true), ButtonMetrics.buttonWidth(fontMetrics.advanceWidth(qsTr("Tools")), true)]
    }, width, language)
    implicitHeight: presentation.height
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: ({
                nodes: root.presentation.nodes
            })
        onEvent: (action, source) => {
            if (action.type === "menu")
                root.menuRequested(action.kind, source);
            else if (action.type === "workspace")
                root.controller.action("preview_workspace_switch", {
                    workspace: action.value
                });
            else if (action.type === "back" || action.type === "forward")
                root.controller.set_navigation(action.type === "back" ? -1 : 1);
            else if (action.type === "parent")
                root.controller.action("navigate", {
                    path: "//" + root.workspaceState.stream + "/" + root.workspaceState.prefix.replace(/\/?[^/]+\/?$/, "")
                });
            else if (action.type === "path")
                root.pathDraft = action.value;
            else if (action.type === "navigate")
                root.controller.action("navigate", {
                    path: action.value
                });
            else if (action.type === "resume")
                root.controller.action("resume_operation", {});
        }
    }
}

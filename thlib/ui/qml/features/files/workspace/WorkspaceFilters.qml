import QtQuick
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/core/foundation.mjs" as Foundation
import "../../../tactic_frame/controls/buttons/metrics.mjs" as ButtonMetrics
import "../../../tactic_frame/features/files/workspace/toolbar.ui.mjs" as UI

Item {
    id: root
    required property var workspace
    readonly property var theme: workspace.theme
    readonly property var workspaceState: workspace.state
    readonly property string language: workspace.language
    FontMetrics {
        id: fontMetrics
        font: Qt.font({
            family: root.theme.fontFamily,
            pixelSize: Foundation.textStyles.body,
            weight: Font.DemiBold,
            hintingPreference: Font.PreferVerticalHinting
        })
    }
    readonly property var presentation: UI.filters({
        style: theme.style,
        kind: workspace.activeTab.kind,
        narrow: workspace.narrow,
        localDirty: workspaceState.local_dirty,
        prefix: workspaceState.prefix,
        busy: workspace.busy,
        nameFilter: workspaceState.name_filter,
        statusFilter: workspaceState.status_filter,
        local: workspaceState.view === "local",
        selectedCount: workspaceState.selected.length,
        selectionScope: workspaceState.selection_scope,
        change: workspaceState.change.code,
        reconcileWidth: ButtonMetrics.buttonWidth(fontMetrics.advanceWidth(qsTr("Add to changelist…")), true)
    }, width, language)
    implicitHeight: presentation.height
    Frame.FrameView {
        anchors.fill: parent
        theme: root.theme
        scene: ({
                nodes: root.presentation.nodes
            })
        onEvent: (action, source) => {
            if (action.type === "field")
                workspace.set(action.key, action.value);
            else if (action.type === "files")
                workspace.act("files");
            else if (action.type === "reconcile")
                workspace.pickTarget("apply_reconcile");
            else if (action.type === "menu")
                workspace.menu(action.kind, source);
        }
    }
}

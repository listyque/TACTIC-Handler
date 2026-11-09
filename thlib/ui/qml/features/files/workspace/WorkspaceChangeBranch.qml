import QtQuick
import "../../../FileWorkspaceMenus.js" as Menus
import "../../../tactic_frame/features/files/workspace/rows.ui.mjs" as Rows

FileWorkspaceTreeRow {
    required property var workspace
    readonly property var modelData: parent.node
    theme: workspace.theme
    row: modelData
    caption: workspace.treeTitle(modelData)
    subtitle: Rows.treeSubtitle(modelData, workspace.language)
    selected: workspace.workspaceState.selection_scope === "changes" && workspace.workspaceState.selection_ids.indexOf(modelData.id) >= 0
    focused: workspace.workspaceState.focus_id === modelData.id
    onSelectedByUser: modifiers => workspace.controller.select_row("changes", modelData.id, modifiers)
    onMenuRequested: (source, x, y) => workspace.contextMenu("changes", modelData, source, x, y)
    onDragRequested: dragData = workspace.controller.drag_payload("changes", modelData.id)
    acceptsDrop: modelData.kind === "change"
    dropReason: (payload, urls) => Menus.dropReason(workspace, modelData, payload, urls)
    dropCaption: (payload, urls) => Menus.dropCaption(modelData, payload, urls)
    onDropped: (payload, urls) => workspace.stageDrop(modelData.code, payload, urls)
    onDisclosure: workspace.act("toggle_change", {
        change: modelData.code
    })
    onActivated: workspace.changeActivated(modelData)
    onDoubleActivated: workspace.controller.open_changelist_details()
}

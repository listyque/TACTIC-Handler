import QtQuick

FileWorkspaceFileRow {
    required property var workspace
    readonly property var modelData: parent.node
    theme: workspace.theme
    row: modelData
    narrow: workspace.narrow
    leftPadding: 24
    objectName: "workspaceChangeFile:" + modelData.parent + "/" + modelData.path
    columns: workspace.state.columns
    selected: workspace.state.selection_scope === "changes" && workspace.state.selection_ids.indexOf(modelData.id) >= 0
    focused: workspace.state.focus_id === modelData.id
    onSelectedByUser: modifiers => workspace.controller.select_row("changes", modelData.id, modifiers)
    onDragRequested: dragData = workspace.controller.drag_payload("changes", modelData.id)
    localLabel: workspace.localStatus(modelData.local_status)
    serverLabel: modelData.change_state === "submitted" ? qsTr("Submitted") : modelData.change_state === "shelved" ? qsTr("Shelved") : workspace.serverStatus(modelData.server_status || modelData.action)
    checkoutLabel: workspace.holders(modelData)
    currentUser: workspace.controller.current_user
    checkoutHolders: workspace.state.locks[(modelData.stream || workspace.state.change.stream || workspace.state.stream) + "\0" + (modelData.source_path || modelData.path)] || []
    onSelectedChangedByUser: checked => workspace.controller.select_file_row("changes", modelData.id, checked)
    onActivated: {
        if (modelData.change_state === "pending") {
            workspace.controller.select_row("changes", modelData.id, 0);
            workspace.act("open_local");
        } else {
            workspace.controller.select_row("changes", modelData.id, 0);
            workspace.controller.open_view("history");
            workspace.detail = {};
        }
    }
    onMenuRequested: (source, x, y) => workspace.contextMenu("changes", modelData, source, x, y)
}

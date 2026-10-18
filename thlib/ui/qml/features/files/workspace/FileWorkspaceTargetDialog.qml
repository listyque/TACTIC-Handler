import QtQuick
import QtQuick.Controls
import "../../../controls" as Controls
import "../../../tactic_frame" as Frame
import "../../../tactic_frame/features/files/workspace/forms.ui.mjs" as UI

Controls.Dialog {
    id: root
    readonly property string language: typeof localizationController === "undefined" ? (Qt.uiLanguage || "en") : localizationController.current_language

    objectName: "workspaceTargetDialog"
    required property var controller
    property string operation: ""
    property string sourceChange: ""
    property string mode: "ordinary"
    property string target: ""
    property bool creating: false
    property string description: ""
    property var revision: ({})
    readonly property string targetStream: visible ? selectionStream() : ""
    function selectionStream() {
        const state = controller.view_data;
        if (["move_files", "bulk_move", "unshelve_begin"].includes(operation))
            return state.change.stream || "";
        const first = (state.selection_records || {})[state.selection_ids[0]] || {};
        return first.stream || state.stream;
    }
    function changelists() {
        const state = controller.view_data;
        const current = state.change;
        const stream = targetStream;
        const workspace = state.workspace;
        const owner = controller.current_user;
        const rows = state.targets.concat(current.state === "pending" && !state.targets.some(row => row.code === current.code) ? [current] : []);
        return rows.filter(row => row.code !== sourceChange && row.state === "pending" && row.depot_writable !== false && row.stream === stream && row.owner === owner && row.workspace === workspace && !row.active_transfer && !row.active_bulk && !row.integration);
    }
    function selectedFiles() {
        // Read the Python projection once; per-row reads block the GUI on large selections.
        const state = controller.view_data;
        const paths = new Set(state.selected);
        return Object.values(state.selection_records || {}).filter(row => paths.has(row.path));
    }
    signal unshelveRequested(string shelf)
    title: qsTr("Choose target changelist")
    parent: Overlay.overlay
    modal: true
    draggable: true
    closePolicy: Popup.CloseOnEscape
    width: Math.min(560, parent ? parent.width - 24 : 560)
    onAboutToShow: {
        x = Qt.binding(() => Math.max(0, (parent.width - width) / 2));
        y = Qt.binding(() => Math.max(0, (parent.height - height) / 2));
    }
    footer: null
    contentItem: Frame.FrameView {
        id: form
        theme: root.theme
        implicitHeight: Math.min(root.operation === "apply_reconcile" ? 460 : 300, Math.max(160, (root.parent ? root.parent.height : 700) - 138))
        scene: UI.target({
            operation: root.operation,
            target: root.target,
            creating: root.creating,
            description: root.description,
            busy: root.controller.busy,
            options: (root.visible ? root.changelists() : []).map(row => ({
                        value: row.code,
                        label: String(row.number)
                    }))
        }, width, height, root.language)
        models: ({
                targetFiles: root.visible && root.operation === "apply_reconcile" ? root.selectedFiles() : []
            })
        describeRow: (list, record) => UI.targetFile(record, list.width - 16)
        onEvent: action => {
            if (action.type === "target")
                root.target = action.value;
            else if (action.type === "creating")
                root.creating = action.value;
            else if (action.type === "description")
                root.description = action.value;
            else if (action.type === "reject")
                root.reject();
            else if (action.type === "accept" && !root.controller.busy && (root.creating || root.target))
                root.accept();
        }
    }
    onAccepted: {
        if (operation === "unshelve_begin") {
            controller.action("prepare_unshelve", {
                target: creating ? "" : target,
                creating: creating,
                description: description
            });
            unshelveRequested(sourceChange);
        } else if (operation === "bulk_checkout" || operation === "bulk_move")
            controller.action("bulk_target", {
                operation: operation === "bulk_move" ? "move_files" : "checkout",
                target: creating ? "" : target,
                creating: creating,
                description: description,
                mode: mode
            });
        else
            controller.action("target_files", {
                operation: operation,
                target: creating ? "" : target,
                creating: creating,
                description: description,
                mode: mode,
                revision: revision
            });
    }
}

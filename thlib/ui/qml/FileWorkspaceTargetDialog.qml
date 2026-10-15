import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "controls" as Controls

Controls.Dialog {
    id:root
    objectName:"workspaceTargetDialog"
    required property var controller
    property string operation:""
    property string sourceChange:""
    property string mode:"ordinary"
    property string target:""
    property bool creating:false
    property string description:""
    property var revision:({})
    readonly property string targetStream:visible ? selectionStream() : ""
    function selectionStream() {
        const state=controller.view_data
        if(["move_files","bulk_move","unshelve_begin"].includes(operation))return state.change.stream || ""
        const first=(state.selection_records || {})[state.selection_ids[0]] || {}
        return first.stream || state.stream
    }
    function changelists() {
        const state=controller.view_data
        const current=state.change
        const stream=targetStream
        const workspace=state.workspace
        const owner=controller.current_user
        const rows=state.targets.concat(current.state==="pending" && !state.targets.some(row=>row.code===current.code) ? [current] : [])
        return rows.filter(row=>row.code!==sourceChange && row.state==="pending" && row.depot_writable!==false && row.stream===stream && row.owner===owner && row.workspace===workspace && !row.active_transfer && !row.active_bulk && !row.integration)
    }
    function selectedFiles() {
        // Read the Python projection once; per-row reads block the GUI on large selections.
        const state=controller.view_data
        const paths=new Set(state.selected)
        return Object.values(state.selection_records || {}).filter(row=>paths.has(row.path))
    }
    signal unshelveRequested(string shelf)
    title:qsTr("Choose target changelist")
    parent: Overlay.overlay
    modal: true
    draggable: true
    closePolicy: Popup.CloseOnEscape
    width: Math.min(560,parent ? parent.width-24 : 560)
    onAboutToShow: { x=Qt.binding(()=>Math.max(0,(parent.width-width)/2)); y=Qt.binding(()=>Math.max(0,(parent.height-height)/2)) }
    footer: Controls.DialogActions {
        theme:root.theme
        Controls.Button {theme:root.theme;text:qsTr("Cancel");onClicked:root.reject()}
        Controls.Button {
            objectName:"workspaceTargetAccept"
            theme:root.theme
            text:root.operation==="apply_reconcile" ? qsTr("Add to changelist") : root.operation==="checkout" || root.operation==="bulk_checkout" ? qsTr("Checkout") : qsTr("Continue")
            icon.name:"check"
            highlighted:true
            enabled:!root.controller.busy && (root.creating || Boolean(root.target))
            onClicked:root.accept()
        }
    }
    contentItem:ColumnLayout {
        Controls.ComboBox {
            theme:root.theme;Layout.fillWidth:true;Accessible.name:qsTr("Target changelist")
            model:root.visible ? root.changelists() : []
            textRole:"number";valueRole:"code";translateDisplayText:false;enabled:!root.creating
            currentIndex:model.findIndex(change=>change.code===root.target)
            onActivated:root.target=currentValue
        }
        Label {Layout.fillWidth:true;visible:root.operation==="apply_reconcile";text:qsTr("Review selected add, edit, delete and rename operations. Local files are kept.");color:root.theme.secondaryText;wrapMode:Text.Wrap}
        ListView {id:preview;objectName:"workspaceTargetPreview";Layout.fillWidth:true;Layout.preferredHeight:160;visible:root.operation==="apply_reconcile";clip:true
            model:root.visible && root.operation==="apply_reconcile" ? root.selectedFiles() : []
            ScrollBar.vertical:Controls.ScrollBar {id:bar;theme:root.theme;flickableTarget:preview}
            delegate:Controls.EditorListItem {required property var modelData;theme:root.theme;width:preview.width-bar.reservedExtent;text:(modelData.rename_from ? modelData.rename_from+" → " : "")+modelData.path+" · "+(modelData.reconcile_action || modelData.local_status);implicitHeight:32}
        }
        Controls.CheckBox {theme:root.theme;text:qsTr("Create a new changelist");checked:root.creating;onToggled:root.creating=checked}
        Controls.TextField {theme:root.theme;Layout.fillWidth:true;visible:root.creating;placeholderText:qsTr("Changelist description");Accessible.name:qsTr("Changelist description");text:root.description;onTextEdited:root.description=text}
    }
    onAccepted:{
        if(operation==="unshelve_begin"){
            controller.action("prepare_unshelve",{target:creating ? "" : target,creating:creating,description:description})
            unshelveRequested(sourceChange)
        }else if(operation==="bulk_checkout" || operation==="bulk_move")controller.action("bulk_target",{operation:operation==="bulk_move" ? "move_files" : "checkout",target:creating ? "" : target,creating:creating,description:description,mode:mode})
        else controller.action("target_files",{operation:operation,target:creating ? "" : target,creating:creating,description:description,mode:mode,revision:revision})
    }
}

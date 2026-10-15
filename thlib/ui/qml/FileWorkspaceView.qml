import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import "controls" as Controls
import "FileWorkspacePresentation.js" as Presentation
import "FileWorkspaceMenus.js" as Menus

Item {
    id: root
    objectName: "fileWorkspaceView"
    required property var theme
    required property var controller
    readonly property var state:controller.view_data
    readonly property bool busy: controller.busy
    readonly property bool pending: root.state.change.state === "pending"
    readonly property bool transferring: Boolean(root.state.change.active_transfer)
    readonly property bool integrating: Boolean(root.state.change.integration)
    readonly property bool narrow: width < 800
    readonly property var activeTab:(root.state.tabs || []).find(tab=>tab.id===root.state.active_tab) || ({kind:"",title:""})
    readonly property string detailsView:["history","conflicts","tasks"].indexOf(activeTab.kind)>=0 ? activeTab.kind : "history"
    property var tabDraft:({})
    property string historyIdentity:""
    property var detail: ({})
    property bool showResolved:false
    property string comparisonToken:""
    property string switchToken:""
    property string previewPath:""
    property var pendingFileMenu: null
    property string confirmationAction: ""
    property var downloadValues: ({})
    property string mergePath: ""
    property var contextRow:({})
    property string contextScope:""
    property var dropDraft:({})
    property bool movingWholeChange:false
    function pickTarget(operation,mode) {
        targetDialog.operation=operation;targetDialog.mode=mode || "ordinary"
        targetDialog.sourceChange=["move_files","bulk_move","unshelve_begin"].indexOf(operation)>=0 ? root.state.change.code : ""
        targetDialog.target=["move_files","bulk_move","bulk_checkout"].indexOf(operation)>=0 ? "" : root.state.change.state==="pending" ? root.state.change.code : ""
        targetDialog.creating=!targetDialog.target && !root.state.targets.length;targetDialog.open()
    }
    function contextMenu(scope,row,item,x,y) {
        contextRow=row;contextScope=scope
        controller.select_row(scope,scope==="files" ? controller.row_identity(row) : row.id || row.code,0,true)
        actionMenu.actions=actions(row.kind==="change" ? "change" : row.kind==="file" || !row.kind && row.path ? "files" : "tree")
        actionMenu.openAt(item,x,y)
    }
    function stageDrop(target,payload,urls) {
        const targetRow=root.state.changes.find(row=>row.code===target)
        if(!targetRow || Menus.dropReason(root,Object.assign({kind:"change"},targetRow),payload,urls))return
        let count=(urls || []).length,origin="explorer"
        if(payload){try{const data=JSON.parse(payload);count=data.rows.length
            origin=data.scope==="workspace" || data.scope==="files" && data.source==="local" ? "local" : data.rows.every(row=>row.parent && (!row.change_state || row.change_state==="pending")) ? "move" : data.rows.length===1 && data.rows[0].state==="shelved" ? "shelf" : "depot"
        }catch(error){return}}
        const change=root.state.changes.find(row=>row.code===target)
        dropDraft={target:target,number:change ? change.number : target,count:count,origin:origin,payload:payload || "",urls:urls || [],project:"",prefix:root.state.view==="local" ? root.state.prefix : ""}
        if(origin==="local" || origin==="explorer")root.act("drop_files",dropDraft)
        else dropConfirm.open()
    }
    function openRevert(operation) {
        revertDialog.operation=operation
        if(operation==="revert") {
            revertDialog.request={change:root.state.change.code,edit_revision:root.state.change.edit_revision}
            revertDialog.caption=qsTr("Changelist #%1").arg(root.state.change.number || root.state.change.code)
        } else {
            const rows=Object.values(root.state.selection_records || {})
            revertDialog.request={files:rows.map(row=>Object.assign({stream:row.stream || root.state.stream,path:row.source_path || row.path},row.parent ? {change:row.parent} : {}))}
            revertDialog.caption=qsTr("Selected items: %1").arg(rows.length)
        }
        revertDialog.open()
    }
    function fileKey(event,scope) {
        if(event.key===Qt.Key_A && (event.modifiers & Qt.ControlModifier) && (event.modifiers & Qt.ShiftModifier)){root.act("select_query");event.accepted=true;return}
        if(event.key===Qt.Key_A && (event.modifiers & Qt.ControlModifier)){controller.select_loaded(scope,true);event.accepted=true}
        else if(event.key===Qt.Key_Escape){controller.select_loaded(scope,false);event.accepted=true}
        else if(event.key===Qt.Key_Up || event.key===Qt.Key_Down){controller.step_selection(scope,event.key===Qt.Key_Up ? -1 : 1,event.modifiers)
            const views={files:files,changes:changes,depot:depotTree,workspace:workspaceTree,history:historyView.listView}
            const rows=scope==="files" ? root.state.rows.filter(row=>Presentation.matches(row,root.state.name_filter,root.state.status_filter)) : root.state.history
            const model=scope==="changes" ? root.controller.change_model : scope==="depot" ? root.controller.depot_model : scope==="workspace" ? root.controller.workspace_model : null
            let index=-1
            if(model){for(let i=0;i<model.count();i++){if(model.get(i).id===root.state.focus_id){index=i;break}}}
            else index=rows.findIndex(row=>(scope==="files" ? root.controller.row_identity(row) : row.id || row.code)===root.state.focus_id)
            if(index>=0){views[scope].currentIndex=index;views[scope].positionViewAtIndex(index,ListView.Contain)}
            event.accepted=true}
        else if(event.key===Qt.Key_Delete){
            const headers=scope==="changes" && Object.values(root.state.selection_records || {}).length>0 && Object.values(root.state.selection_records).every(row=>row.kind==="change")
            const action=headers ? "delete_change" : "mark_delete"
            if(!Menus.selectionReason(root,action))command(action)
            event.accepted=true
        }
        else if(event.key===Qt.Key_C && (event.modifiers & Qt.ControlModifier)){controller.copy_selection("depot");event.accepted=true}
    }

    readonly property real columnWidth:root.state.columns.filter(column=>column.visible).reduce((sum,column)=>sum+column.width,81+6*root.state.columns.filter(column=>column.visible).length+(root.activeTab.kind==="changes" ? 24 : 0))
    readonly property bool editable: root.state.change.owner===root.controller.current_user && root.state.change.workspace===root.state.workspace && pending && root.state.change.depot_writable!==false && !transferring && !integrating && !root.state.change.active_bulk && !busy
    property bool treeOpen: false
    property string editKind: ""
    property string draft: ""


    function act(name, values) { controller.action(name, values || {}) }
    function set(name, value) { controller.set_value(name, value) }
    function changeState(value) {
        return value === "pending" ? qsTr("Pending") : value === "submitted" ? qsTr("Submitted") : value === "shelved" ? qsTr("Shelved") : qsTr("Reverted")
    }
    function treeTitle(row) {
        if (row.kind === "more") return qsTr("Load more")
        if (row.kind === "change") return qsTr("Changelist #%1").arg(row.number || row.code) + " · " + (row.description || qsTr("No description"))
        return row.name || row.path || ""
    }
    function depotActivated(row) {
        if (row.kind === "more") act("more_depot",{id:row.parent})
        else if (row.kind === "depot") act("toggle_depot",{id:row.id})
        else if (row.kind === "file") return
        else if(root.state.tree_selection!==row.id || root.state.selection_scope!=="depot")controller.select_row("depot",row.id,0)
    }
    function changeActivated(row) {
        if (row.kind === "more") act("more_change",{change:row.parent})
        else if (row.kind === "change") return
        else {controller.open_view("history");act("history",{stream:row.stream,path:row.path}) }
    }
    function selectTab(tab) { detail={};controller.activate_tab(tab.id) }
    function editTab(creating) {
        const current=creating ? controller.view_presets[0] : activeTab
        const preset=controller.view_presets.find(row=>row.kind===current.kind && (row.kind!=="changes" || row.state===current.state)) || controller.view_presets[0]
        tabDraft={id:creating ? "" : current.id,title:creating ? "" : current.title,preset:preset.id,source:current.source || "depot",prefix:current.prefix || "",scope:current.scope || "mine",pinned:current.pinned || false}
        tabDialog.open()
    }
    function workspaceActivated(row) {
        if(row.kind==="more")act("more_workspace_tree",{id:row.parent})
        else if(row.kind==="file")return
        else if(root.state.tree_selection!==row.id || root.state.selection_scope!=="workspace")controller.select_row("workspace",row.id,0)
    }
    function integration() { return { change:root.state.change.code, edit_revision:root.state.change.edit_revision, integration:root.state.change.integration.code } }
    Component {id:catalogView;FileWorkspaceCatalog {theme:root.theme;controller:root.controller}}
    Component {id:graphView;FileWorkspaceStreamGraph {theme:root.theme;controller:root.controller;onEditStream:(row,child)=>streamEditor.openSpec(row,child)}}
    Component {id:streamsView;FileWorkspaceStreams {theme:root.theme;controller:root.controller;onEditStream:(row,child)=>streamEditor.openSpec(row,child)}}
    FileWorkspaceStreamEditor {id:streamEditor;theme:root.theme;controller:root.controller}
    function holders(row) {
        const stream = row.stream || root.state.change.stream || root.state.stream
        const paths = root.state.locks[stream + "\0" + (row.source_path || row.path)] || []
        return paths.map(h => h.owner + " · " + (h.mode === "exclusive" ? qsTr("Exclusive checkout") : qsTr("Ordinary checkout"))).join("; ") || qsTr("No active checkout")
    }
    function localStatus(value) {
        return value === "modified" ? qsTr("Modified") : value === "missing" ? qsTr("Missing") : value === "added" ? qsTr("Added") : value === "clean" ? qsTr("Clean") : value === "unmapped" ? qsTr("Not mapped to workspace") : qsTr("Not inspected")
    }
    function serverStatus(value) {
        return value === "modified_after_upload" ? qsTr("Modified after upload") : value === "newer" ? qsTr("Newer on server") : value === "current" ? qsTr("Current") : value === "write" ? qsTr("Uploaded") : value === "delete" || value === "deleted" ? qsTr("Deleted") : value === "checkout" ? qsTr("Checked out") : value === "untracked" ? qsTr("Untracked") : value === "unmapped" ? qsTr("Not mapped to workspace") : value === "move/add" || value === "move/delete" ? qsTr("Renamed / moved") : qsTr("Published")
    }
    function phase(value) {
        return value === "manifest" ? qsTr("Preparing manifest") : value === "offline" ? qsTr("Connection lost; work retained") : value === "preparing" ? qsTr("Preparing local changes") : value === "applying" ? qsTr("Applying atomic batch") : value === "submitting" ? qsTr("Submitting changelist") : value === "recovering" ? qsTr("Recovering submit result") : value === "verifying" ? qsTr("Verifying files") : value === "staging" ? qsTr("Staging files") : value === "unavailable" ? qsTr("Unavailable locally") : value === "indexing_history" ? qsTr("Indexing revision history") : value === "blocked" ? qsTr("Sync stopped") : value === "cancelled" ? qsTr("Cancelled") : value === "waiting" ? qsTr("Waiting for server") : value === "discovering" ? qsTr("Discovering files") : value === "reconciling" ? qsTr("Reconciling workspace") : value === "collecting" || value === "uploading" ? qsTr("Uploading files") : value === "queued" ? qsTr("Queued on server") : value === "running" ? qsTr("Verifying and staging") : value === "downloading" || value === "streaming" ? qsTr("Downloading files") : value === "resolving" ? qsTr("Resolving conflicts") : value === "error" ? qsTr("Failed") : value === "submitted" ? qsTr("Submitted") : value === "ready" ? qsTr("Ready to submit") : value === "complete" ? qsTr("Finished") : qsTr("Ready")
    }
    function command(name) {
        if(name==="preview_revision" && root.activeTab.kind==="history"){historyView.previewSelected();return}
        if(name==="submit"){submitDialog.open();root.act("review_change",{operation:"submit"});return}
        if(name==="revert" || name==="revert_files"){openRevert(name);return}
        if (["revision_workspace", "revision_folder", "revision_selected", "revision_history"].indexOf(name) >= 0) {
            revisionDialog.scope = name === "revision_folder" ? "folder" : name === "revision_workspace" ? "workspace" : "selection"
            revisionDialog.selector = name === "revision_history" ? "file_revision" : ""
            revisionDialog.value = name === "revision_history" ? String(detail.number) : ""
            revisionDialog.force = false
            revisionDialog.request = name === "revision_history" ? {history:{path:root.state.history_path,stream:root.state.history_stream}} : ({})
            const row = root.state.context_row
            revisionDialog.target = name === "revision_history" ? root.state.history_path : revisionDialog.scope === "workspace" ? root.state.workspace : revisionDialog.scope === "folder" ? row.directory || row.name || root.state.workspace : qsTr("Selected files: %1").arg(root.state.selected.length)
            revisionDialog.open(); return
        }
        if(name.indexOf("view_")===0){controller.open_view(name.slice(5));return}
        if(name==="depot_tree" || name==="workspace_tree"){set("tree_view",name==="depot_tree" ? "depot" : "workspace");return}
        if(name==="new_tab" || name==="edit_tab"){editTab(name==="new_tab");return}
        if(name==="close_tab"){controller.close_tab(root.state.active_tab);return}
        if(name==="tab_left" || name==="tab_right"){controller.move_tab(name==="tab_left" ? -1 : 1);return}
        if(name==="copy_change_code"){controller.copy_change_code();return}
        if(name==="copy_change_link"){root.controller.copy_change_link();return}
        if(name==="goto_change"){root.editKind=name;root.draft="";editor.open();return}
        if(name.indexOf("copy_")===0){controller.copy_selection(name.slice(5));return}
        if(name==="move_all_files"){root.movingWholeChange=true;root.act("select_query",{whole_change:true});return}
        if(name==="delete_change") {
            const targets=Menus.deletionTargets(root)
            if(targets.length===1 && targets[0].state==="pending" && targets[0].opened_files!==0){nonemptyDelete.open();return}
            confirmation.deleteTargets=targets.map(row=>({change:row.code,edit_revision:row.edit_revision,number:row.number}))
        }
        if(["mark_delete","delete_local","delete_change","delete_shelf_files","remove_files"].indexOf(name)>=0){confirmationAction=name;confirmation.open();return}
        if(name==="query_checkout_ordinary" || name==="query_checkout_exclusive"){pickTarget("bulk_checkout",name.endsWith("exclusive") ? "exclusive" : "ordinary");return}
        if(name==="query_move"){pickTarget("bulk_move");return}
        if(name==="query_revert" || name==="query_delete"){confirmationAction=name;confirmation.open();return}
        if(name==="bulk_resume"){act(name,{task:detail.task,bulk:detail.kind==="mutation"});return}
        if(name==="apply_reconcile"){pickTarget("apply_reconcile");return}
        if(name==="undo_resolution"){act("undo_resolve",{paths:detail.rename_partner ? [detail.path,detail.rename_partner] : [detail.path]});return}
        if(name==="compare_shelf" || name==="replace_shelf"){shelfDialog.operation=name==="replace_shelf" ? "update_shelf" : "compare_shelf";shelfDialog.shelf=({});root.act("shelf_targets");shelfDialog.open();return}
        if(name==="unshelve_begin"){
            if(root.state.change.state==="shelved")pickTarget(name)
            else {shelfDialog.operation=name;shelfDialog.shelf=({});root.act("shelf_targets");shelfDialog.open()}
            return
        }
        if(name==="rebase_begin"){reviewDialog.operation=name;reviewDialog.paths=[];reviewDialog.request=({});root.act("review_change",{operation:name});reviewDialog.open();return}
        if(name==="offer_change"){root.editKind=name;root.draft="";editor.open();return}
        if(name==="accept_change"){root.act(name,{workspace:root.state.workspace,handoff:root.state.change.handoff.code});return}
        if(name==="restore_revision"){targetDialog.revision=detail;pickTarget("restore_file");return}
        if(name.indexOf("filter_state/")===0){set("status_filter",name.slice(13));return}
        if(name==="toggle_log"){set("log_visible",!root.state.log_visible);return}
        if(name==="change_details"){root.controller.open_changelist_details();return}
        if(name==="columns"){columnsDialog.open();return}
        if(name==="export_query"){manifestSave.open();return}
        if(name==="diff_local" || name==="diff_have"){root.act("compare",{mode:name==="diff_have" ? "local_have" : "local_head"});return}
        if(name==="diff_revisions"){root.act("compare",{mode:"revisions"});return}
        if(name==="diff_shelf"){shelfDialog.operation=name;shelfDialog.shelf=({});root.act("shelf_targets");shelfDialog.open();return}
        if(name==="diff_base_ours" || name==="diff_ours_theirs"){root.act("compare",{mode:"conflict",path:root.detail.path,left:name==="diff_base_ours" ? "base" : "ours",right:name==="diff_base_ours" ? "ours" : "theirs"});return}
        if(name==="file_history") {
            const row=root.state.context_row
            controller.open_view("history");return
        }
        if(name==="rename_file"){root.editKind=name;root.draft=root.state.context_row.source_path || root.state.context_row.path;editor.open();return}
        if (["shelve","shelve_selected","shelve_revert"].indexOf(name)>=0) {
            reviewDialog.operation=name
            reviewDialog.paths=name==="shelve_selected" ? root.state.selected.slice() : []
            reviewDialog.request=({})
            root.act("review_change",Object.assign({operation:name},reviewDialog.paths.length ? {paths:reviewDialog.paths} : {}))
            reviewDialog.open();return
        }
        if (name==="move_files") pickTarget("move_files")
        else if (["unshelve_begin", "merge_begin", "local_root"].indexOf(name) >= 0) {
            editKind = name
            draft = name === "local_root" ? root.state.root : ""
            editor.open()
        } else if (name === "workspace_setup") {
            set("editing_workspace", false)
            set("setup", true)
        } else if (name === "choose_folder") folderDialog.open()
        else if (name === "checkout_ordinary" || name === "checkout_exclusive") pickTarget("checkout",name.slice(9))
        else if (name === "help") windowModel.open_help("file_workspace")
        else if (name === "save_revision") {
            downloadValues = {path:detail.path,stream:detail.stream,published_change:detail.change}
            saveDialog.open()
        } else if (name === "merged_file") { mergePath = detail.path; mergedDialog.open() }
        else if (name === "ours" || name === "theirs") {
            const selected=root.state.conflict_selected.length && !root.showResolved ? root.state.conflict_selected : [detail.path]
            const paths=new Set(selected)
            for(const path of selected){const row=root.state.conflicts.find(row=>row.path===path);if(row?.rename_partner)paths.add(row.rename_partner)}
            act("resolve",{resolutions:[...paths].map(path=>({path:path,choice:name}))})
        }
        else if (name.indexOf("preview_") === 0) {
            const side = name.slice(8)
            act("preview", side === "revision" ? {path:detail.path,stream:detail.stream,published_change:detail.change} : Object.assign(integration(),{path:detail.path,conflict_side:side}))
        } else if (name === "transfer_status" || name === "transfer_cancel") act(name,{task:detail.task,bulk:detail.kind==="mutation"})
        else act(name)
    }
    function entry(title, command, icon, enabled) {
        const invalid=Menus.selectionReason(root,command)
        enabled=enabled && !invalid
        const reason=invalid || (enabled ? "" : busy ? qsTr("An operation is running") : !root.state.selected.length && kindForCommand(command)==="files" ? qsTr("Select files first") : !editable ? qsTr("Choose an owned pending changelist") : qsTr("Unavailable for this selection"))
        return {title:title,command:command,icon:icon,enabled:enabled,status:reason}
    }
    function kindForCommand(command){return ["checkout_ordinary","checkout_exclusive","move_files","remove_files","revert_files","rename_file","mark_delete","delete_local","open_local","reveal_local"].indexOf(command)>=0 ? "files" : ""}
    function actions(kind){return Menus.actions(root,kind)}
    function menu(kind, source) { actionMenu.actions = actions(kind); actionMenu.toggleBelowItem(source) }
    function saveEditor() {
        if(editKind === "goto_change")act("goto_change",{change:draft})
        else if(editKind === "rename_file")act("rename_file",{target:draft})
        else if (editKind === "local_root") set("root",draft)
        else if (editKind === "move_files") {set("target",draft);act("move_files")}
        else if(editKind==="offer_change")act(editKind,{recipient:draft})
        else {reviewDialog.operation=editKind;reviewDialog.paths=[];reviewDialog.request=editKind==="merge_begin" ? {source_stream:draft} : {shelf:draft};act("review_change",Object.assign({operation:editKind},reviewDialog.request));reviewDialog.open()}
    }

    FileWorkspaceReviewDialog { id:reviewDialog;theme:root.theme;controller:root.controller }
    FileWorkspaceSubmitDialog { id:submitDialog;theme:root.theme;controller:root.controller }
    FileWorkspaceComparisonDialog {id:comparisonDialog;theme:root.theme;controller:root.controller;onExternalRequested:comparisonApp.open()}
    FileDialog {id:comparisonApp;title:qsTr("Choose comparison application");nameFilters:[qsTr("Applications (*.exe)"),qsTr("All files (*)")];onAccepted:root.act("external_compare",{application:selectedFile.toString()})}
    Connections {target:root.controller
        function onStateChanged(){
            const historyIdentity=root.state.history_stream+"/"+root.state.history_path
            if(historyIdentity!==root.historyIdentity){root.historyIdentity=historyIdentity;if(root.detailsView==="history")root.detail={}}
            if(root.activeTab.kind==="history")root.detail=root.state.history.find(row=>row.code===root.state.focus_id) || root.state.history.find(row=>row.code===root.detail.code) || root.state.history[0] || ({})
            if(root.detailsView==="conflicts"){
                const rows=root.showResolved ? root.state.resolved_conflicts : root.state.conflicts
                root.detail=rows.find(row=>row.path===root.detail.path) || rows[0] || ({})
            }
            const switching=root.state.switch_preview.token;if(switching && switching!==root.switchToken){root.switchToken=switching;switchDialog.open()}
            const token=root.state.comparison.token;if(token && token!==root.comparisonToken){root.comparisonToken=token;comparisonDialog.open()}}
    }
    FileWorkspaceShelfDialog {id:shelfDialog;theme:root.theme;controller:root.controller
        onChosen:values=>{if(shelfDialog.operation==="diff_shelf"){root.act("compare",{mode:"pending_shelf",shelf:values.shelf});return}reviewDialog.operation=shelfDialog.operation;reviewDialog.paths=shelfDialog.operation==="update_shelf" ? root.state.selected.slice() : [];reviewDialog.request=values;root.act("review_change",Object.assign({operation:shelfDialog.operation},values,reviewDialog.paths.length ? {paths:reviewDialog.paths} : {}));reviewDialog.open()}
    }

    Component {
        id:changeBranch
        FileWorkspaceTreeRow {
            readonly property var modelData:parent.node
            theme:root.theme;row:modelData
            caption:root.treeTitle(modelData)
            subtitle:modelData.kind==="change" ? [root.changeState(modelData.state),modelData.owner,modelData.workspace,
                modelData.opened_files!==undefined ? modelData.opened_files+" "+qsTr("files") : "",
                modelData.conflict_files ? modelData.conflict_files+" "+qsTr("conflicts") : "",
                modelData.state==="pending" && modelData.local_counts?.files ? modelData.local_counts.files+" "+qsTr("local unstaged") : ""].filter(Boolean).join(" · ") : ""
            selected:root.state.selection_scope==="changes" && root.state.selection_ids.indexOf(modelData.id)>=0
            focused:root.state.focus_id===modelData.id
            onSelectedByUser:modifiers=>root.controller.select_row("changes",modelData.id,modifiers)
            onMenuRequested:(source,x,y)=>root.contextMenu("changes",modelData,source,x,y)
            onDragRequested:dragData=root.controller.drag_payload("changes",modelData.id)
            acceptsDrop:modelData.kind==="change"
            dropReason:(payload,urls)=>Menus.dropReason(root,modelData,payload,urls)
            dropCaption:(payload,urls)=>Menus.dropCaption(modelData,payload,urls)
            onDropped:(payload,urls)=>root.stageDrop(modelData.code,payload,urls)
            onDisclosure:root.act("toggle_change",{change:modelData.code})
            onActivated:root.changeActivated(modelData)
            onDoubleActivated:root.controller.open_changelist_details()
        }
    }
    Component {
        id:changeFile
        FileWorkspaceFileRow {
            readonly property var modelData:parent.node
            theme:root.theme;row:modelData;narrow:root.narrow
            leftPadding:24
            objectName:"workspaceChangeFile:"+modelData.parent+"/"+modelData.path
            columns:root.state.columns
            selected:root.state.selection_scope==="changes" && root.state.selection_ids.indexOf(modelData.id)>=0
            focused:root.state.focus_id===modelData.id
            onSelectedByUser:modifiers=>root.controller.select_row("changes",modelData.id,modifiers)
            onDragRequested:dragData=root.controller.drag_payload("changes",modelData.id)
            localLabel:root.localStatus(modelData.local_status);serverLabel:modelData.change_state==="submitted" ? qsTr("Submitted") : modelData.change_state==="shelved" ? qsTr("Shelved") : root.serverStatus(modelData.server_status || modelData.action);checkoutLabel:root.holders(modelData);currentUser:root.controller.current_user;checkoutHolders:root.state.locks[(modelData.stream || root.state.change.stream || root.state.stream)+"\0"+(modelData.source_path || modelData.path)] || []
            onSelectedChangedByUser:checked=>root.controller.select_file_row("changes",modelData.id,checked)
            onActivated:{if(modelData.change_state==="pending"){root.controller.select_row("changes",modelData.id,0);root.act("open_local");}else{root.controller.select_row("changes",modelData.id,0);root.controller.open_view("history");root.detail={}}}
            onMenuRequested:(source,x,y)=>root.contextMenu("changes",modelData,source,x,y)
        }
    }

    Controls.Dialog {
        id: dropBlocked
        objectName: "workspaceDropBlocked"
        property string message: ""
        theme: root.theme
        modal: true
        anchors.centerIn: parent
        width: Math.min(480,root.width-32)
        title: qsTr("Files outside workspace")
        contentItem: Label {
            text: dropBlocked.message
            textFormat: Text.PlainText
            wrapMode: Text.Wrap
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
        }
        footer: Controls.DialogActions {
            theme: root.theme
            Controls.Button {
                id: dropBlockedOk
                objectName: "workspaceDropBlockedOk"
                theme: root.theme
                text: qsTr("OK")
                highlighted: true
                onClicked: dropBlocked.accept()
            }
        }
        onOpened: dropBlockedOk.forceActiveFocus()
    }
    Controls.Dialog {
        id:dropConfirm;objectName:"workspaceDropConfirm";theme:root.theme;modal:true;anchors.centerIn:parent;width:Math.min(560,root.width-24)
        title:qsTr("Add to changelist #%1").arg(root.dropDraft.number || "")
        contentItem:ColumnLayout {
            spacing:8
            Label {Layout.fillWidth:true;text:qsTr("Selected items: %1").arg(root.dropDraft.count || 0);color:root.theme.secondaryText}
            Label {objectName:"workspaceDropDescription";Layout.fillWidth:true;textFormat:Text.PlainText;wrapMode:Text.Wrap;color:root.theme.primaryText
                text:root.dropDraft.origin==="move" ? qsTr("Move selected files between pending changelists. Local files are kept.") : root.dropDraft.origin==="shelf" ? qsTr("Restore shelved files into this changelist. Review conflicts before Submit.") : qsTr("Open selected files for editing in this changelist. Missing local copies will be downloaded; existing local files are kept.")
            }
        }
        footer:Controls.DialogActions {theme:root.theme
            Controls.Button {theme:root.theme;icon.name:"close";text:qsTr("Cancel");onClicked:dropConfirm.reject()}
            Controls.Button {objectName:"workspaceDropAddButton";theme:root.theme;icon.name:"add";text:qsTr("Add");highlighted:true;onClicked:dropConfirm.accept()}
        }
        onAccepted:{
            if(root.dropDraft.origin==="shelf"){
                const shelf=JSON.parse(root.dropDraft.payload).rows[0].code
                reviewDialog.operation="unshelve_begin";reviewDialog.paths=[];reviewDialog.request={shelf:shelf}
                root.act("prepare_unshelve",{shelf:shelf,target:root.dropDraft.target});reviewDialog.open()
            }else root.act("drop_files",root.dropDraft)
        }
    }
    Controls.Dialog {
        id:nonemptyDelete;objectName:"workspaceNonemptyDelete";theme:root.theme;modal:true;anchors.centerIn:parent;width:Math.min(560,root.width-24)
        title:qsTr("This changelist contains files")
        contentItem:Label {text:qsTr("Move all files to another changelist, then delete the empty changelist. Or revert this changelist; it will appear in Reverted. Local files are kept.");textFormat:Text.PlainText;wrapMode:Text.Wrap;color:root.theme.primaryText}
        footer:Controls.DialogActions {theme:root.theme
            GridLayout {columns:root.narrow ? 1 : 3;Layout.preferredWidth:Math.max(0,nonemptyDelete.width-28)
                Controls.Button {theme:root.theme;Layout.fillWidth:true;text:qsTr("Cancel");icon.name:"close";onClicked:nonemptyDelete.reject()}
                Controls.Button {objectName:"workspaceMoveAllFiles";theme:root.theme;Layout.fillWidth:true;text:qsTr("Move files…");icon.name:"swap-horizontal";onClicked:{nonemptyDelete.close();root.command("move_all_files")}}
                Controls.Button {objectName:"workspaceRevertAllFiles";theme:root.theme;Layout.fillWidth:true;text:qsTr("Revert changelist");icon.name:"undo";onClicked:{nonemptyDelete.close();root.command("revert")}}
            }
        }
    }

    Controls.Dialog {
        id:columnsDialog;objectName:"workspaceColumnsDialog";theme:root.theme;title:qsTr("File columns");standardButtons:Dialog.Close
        ColumnLayout {Repeater {model:root.state.columns
            delegate:RowLayout {required property var modelData
                Controls.CheckBox {theme:root.theme;text:qsTr(({path:"File",local_status:"Local changes",server_status:"Server state",checkout:"Checkout / locks",number:"Version",local_number:"Local revision",have_number:"Have",head_number:"Head",size:"Size",type:"Type"})[modelData.key]);checked:modelData.visible;enabled:modelData.key!=="path";onToggled:root.controller.configure_column(modelData.key,modelData.width,checked)}
                Controls.TextField {theme:root.theme;Layout.preferredWidth:70;text:String(modelData.width);Accessible.name:qsTr("Column width");onAccepted:root.controller.configure_column(modelData.key,Number(text),modelData.visible)}
                Controls.CompactIconButton {theme:root.theme;iconName:"arrow-up";toolTip:qsTr("Move column left");onClicked:root.controller.move_column(modelData.key,-1)}
                Controls.CompactIconButton {theme:root.theme;iconName:"arrow-down";toolTip:qsTr("Move column right");onClicked:root.controller.move_column(modelData.key,1)}
            }
        }}
    }
    FileDialog {id:manifestSave;title:qsTr("Export selected file manifest");fileMode:FileDialog.SaveFile;onAccepted:root.act("export_query",{destination:String(selectedFile)})}
    FileWorkspaceTargetDialog {id:targetDialog;theme:root.theme;controller:root.controller
        onUnshelveRequested:shelf=>{reviewDialog.operation="unshelve_begin";reviewDialog.paths=[];reviewDialog.request={shelf:shelf};reviewDialog.open()}
    }
    FileWorkspaceGetRevisionDialog {id:revisionDialog;theme:root.theme;controller:root.controller}
    ActionMenu { id: actionMenu; objectName:"workspaceActionMenu"; theme:root.theme; onTriggered: command => root.command(command) }
    FolderDialog { id: folderDialog; title: qsTr("Choose local workspace folder"); onAccepted: root.controller.choose_root(String(selectedFolder)) }
    FileDialog { id: saveDialog; title: qsTr("Save revision"); fileMode: FileDialog.SaveFile; onAccepted: root.act("save_revision", Object.assign({}, root.downloadValues, {destination:String(selectedFile)})) }
    FileDialog { id: mergedDialog; title: qsTr("Choose merged file"); fileMode: FileDialog.OpenFile; onAccepted: root.act("merged_file", {file:String(selectedFile),path:root.mergePath}) }
    FileWorkspaceRevertDialog {
        id: revertDialog
        theme: root.theme
        busy: root.busy
        anchors.centerIn: parent
        width: Math.min(480,root.width-32)
        onConfirmed: (operation,values)=>root.act(operation,values)
    }
    Controls.Dialog {
        id: confirmation
        objectName: "workspaceConfirmation"
        property var deleteTargets: []
        theme: root.theme
        modal: true
        anchors.centerIn: parent
        width: Math.min(480, root.width - 32)
        readonly property string actionLabel: root.confirmationAction === "revert" ? qsTr("Revert changelist")
            : ["query_revert", "remove_files"].indexOf(root.confirmationAction) >= 0 ? qsTr("Remove files")
            : root.confirmationAction === "delete_local" ? qsTr("Move to Trash")
            : ["mark_delete", "query_delete"].indexOf(root.confirmationAction) >= 0 ? qsTr("Mark for deletion")
            : qsTr("Delete")
        title: confirmation.actionLabel
        contentItem: Label {
            objectName: "workspaceConfirmationMessage"
            text: root.confirmationAction === "delete_change" ? qsTr("Delete %1 changelist(s) / shelf(s)? Local files are kept. Shelved contents will no longer be available. The whole selection is deleted together.").arg(confirmation.deleteTargets.length) + "\n" + confirmation.deleteTargets.slice(0,10).map(row=>"#"+row.number).join(", ") + (confirmation.deleteTargets.length>10 ? "…" : "") : ["query_delete","query_revert"].indexOf(root.confirmationAction)>=0 ? qsTr("Apply the pinned query to all matching server files? The batch is atomic; local files are kept.") : ["mark_delete","delete_local","delete_change","delete_shelf_files","remove_files"].indexOf(root.confirmationAction)>=0 ? qsTr("Confirm %1 for the selected items? Local changes may be affected.").arg(root.confirmationAction === "mark_delete" ? qsTr("depot deletion on submit") : root.confirmationAction === "delete_local" ? qsTr("moving local copies to Trash") : root.confirmationAction === "delete_change" ? qsTr("deleting the empty changelist or shelf") : qsTr("removing files from the changelist")) : qsTr("Revert the changelist? Local files will be kept.")
            textFormat: Text.PlainText
            wrapMode: Text.Wrap
            color: root.theme.secondaryText
            font.family: root.theme.fontFamily
            font.pointSize: Controls.Typography.body
        }
        footer: Controls.DialogActions {
            theme: root.theme
            Controls.Button {
                id: confirmationCancel
                objectName: "workspaceConfirmationCancel"
                theme: root.theme
                text: qsTr("Cancel")
                onClicked: confirmation.reject()
            }
            Controls.Button {
                objectName: "workspaceConfirmationAccept"
                theme: root.theme
                text: root.confirmationAction === "revert" ? qsTr("Revert") : confirmation.actionLabel
                icon.name: root.confirmationAction === "revert" ? "undo" : "delete"
                destructive: true
                enabled: !root.busy
                onClicked: confirmation.accept()
            }
        }
        onOpened: confirmationCancel.forceActiveFocus()
        onAccepted:["query_delete","query_revert"].indexOf(root.confirmationAction)>=0 ? root.act("bulk_query",{operation:root.confirmationAction==="query_delete" ? "mark_delete" : "remove_files"}) : root.confirmationAction === "mark_delete" ? root.pickTarget("mark_delete") : root.act(root.confirmationAction,root.confirmationAction === "delete_change" ? {changes:confirmation.deleteTargets.map(row=>({change:row.change,edit_revision:row.edit_revision}))} : {})
    }
    Controls.Dialog {
        id:editor; objectName:"workspaceEditor"; theme:root.theme; modal:true; anchors.centerIn:parent; width:Math.min(560,root.width-24)
        title:root.editKind === "offer_change" ? qsTr("Recipient login") : root.editKind === "goto_change" ? qsTr("Changelist number") : root.editKind === "local_root" ? qsTr("Local workspace root") : root.editKind === "rename_file" ? qsTr("New depot path") : root.editKind === "move_files" ? qsTr("Target changelist") : root.editKind === "merge_begin" ? qsTr("Merge source stream") : qsTr("Shelf changelist")
        standardButtons:Dialog.Save | Dialog.Cancel
        onAccepted:root.saveEditor()
        contentItem:Controls.TextArea {theme:root.theme;implicitHeight:60;text:root.draft;placeholderText:root.editKind === "move_files" || root.editKind === "unshelve_begin" ? qsTr("Changelist number, e.g. #42") : "";Accessible.name:editor.title;onTextChanged:if(activeFocus)root.draft=text}
    }
    Controls.Dialog {
        id:tabDialog;objectName:"workspaceTabEditor";theme:root.theme;modal:true;anchors.centerIn:parent;width:Math.min(560,root.width-24)
        title:qsTr("Edit view tab");standardButtons:Dialog.Save | Dialog.Cancel
        onAccepted:root.controller.configure_tab(root.tabDraft)
        contentItem:ColumnLayout {
            Controls.TextField {objectName:"workspaceTabTitle";theme:root.theme;Layout.fillWidth:true;Accessible.name:qsTr("Tab title");placeholderText:qsTr("Tab title");text:root.tabDraft.title || "";onTextEdited:root.tabDraft.title=text}
            Controls.ComboBox {objectName:"workspaceTabPreset";theme:root.theme;Layout.fillWidth:true;model:root.controller.view_presets;textRole:"title";valueRole:"id";Accessible.name:qsTr("View");currentIndex:root.controller.view_presets.findIndex(row=>row.id===root.tabDraft.preset);onActivated:root.tabDraft.preset=currentValue}
            Controls.ComboBox {theme:root.theme;Layout.fillWidth:true;model:[qsTr("Selected tree"),qsTr("Depot files"),qsTr("Have"),qsTr("Local changes"),qsTr("Changelist files")];Accessible.name:qsTr("File source");currentIndex:["selection","depot","have","local","change"].indexOf(root.tabDraft.source);onActivated:root.tabDraft.source=["selection","depot","have","local","change"][currentIndex]}
            Controls.CheckBox {theme:root.theme;text:qsTr("Pin file history");visible:root.tabDraft.preset==="history";checked:Boolean(root.tabDraft.pinned);onToggled:root.tabDraft.pinned=checked}
            Controls.ComboBox {theme:root.theme;Layout.fillWidth:true;visible:root.tabDraft.preset!=="files";Accessible.name:qsTr("Changelist scope");model:[qsTr("My changes"),qsTr("This workspace"),qsTr("This stream"),qsTr("All permitted changes")];currentIndex:["mine","workspace","stream","all"].indexOf(root.tabDraft.scope);onActivated:root.tabDraft.scope=["mine","workspace","stream","all"][currentIndex]}
            Controls.TextField {theme:root.theme;Layout.fillWidth:true;Accessible.name:qsTr("Path prefix");placeholderText:qsTr("Path prefix");text:root.tabDraft.prefix || "";onTextEdited:root.tabDraft.prefix=text}
        }
    }
    Connections {
        target:root.controller
        function onDropRejected(message) {dropBlocked.message=message;dropBlocked.open()}
        function onDetailsCommandRequested(command) {root.command(command)}
        function onStateChanged() {
            if(root.movingWholeChange && !root.busy){root.movingWholeChange=false;if(!root.state.error && root.state.selection_query)root.pickTarget("bulk_move")}
            if(root.pendingFileMenu && !root.busy){
                const pending=root.pendingFileMenu;root.pendingFileMenu=null
                if(!root.state.error && root.state.change.code === pending.change){actionMenu.actions=root.actions("files");actionMenu.openAt(root,pending.x,pending.y)}
            }
            if (root.state.setup && !root.busy && !setupDialog.opened) setupDialog.open()
            if (!root.state.setup && setupDialog.opened) setupDialog.close()

        }
    }
    Controls.Dialog {
        id:switchDialog;objectName:"workspaceSwitchDialog";theme:root.theme;modal:true;anchors.centerIn:parent;width:Math.min(520,root.width-24)
        title:qsTr("Switch workspace?");standardButtons:Dialog.Ok | Dialog.Cancel
        contentItem:Label {text:qsTr("Pending changes and server tasks remain in the previous workspace. Local files are kept.")+"\n"+(root.state.switch_preview.previous || "")+" → "+(root.state.switch_preview.workspace || "");wrapMode:Text.Wrap;color:root.theme.primaryText}
        onAccepted:root.act("choose_workspace",{workspace:root.state.switch_preview.workspace,revision:root.state.switch_preview.revision})
    }
    Controls.Dialog {
        id:setupDialog; theme:root.theme; modal:true; anchors.centerIn:parent
        width:Math.min(620,root.width-24); height:Math.min(580,root.height-24)
        title:root.state.editing_workspace ? qsTr("Edit workspace") : qsTr("Workspace setup")
        onRejected:root.set("setup",false)
        footer:Controls.DialogActions {theme:root.theme
            Controls.Button {theme:root.theme;icon.name:"close";text:root.busy ? qsTr("Stop waiting") : qsTr("Cancel");onClicked:{if(root.busy)root.controller.stop();else{root.set("setup",false);setupDialog.close()}}}
            Controls.Button {theme:root.theme;icon.name:root.state.editing_workspace ? "content-save" : "add";text:root.state.editing_workspace ? qsTr("Save workspace") : qsTr("Create");highlighted:true;enabled:!root.busy && root.state.code.length>0;onClicked:root.act(root.state.editing_workspace ? "update_workspace" : "create_"+root.state.setup_kind)}
        }
        contentItem:Flickable {
            id:setupScroll;clip:true;contentWidth:width;contentHeight:setupFields.implicitHeight
            ScrollBar.vertical:Controls.ScrollBar {id:setupBar;theme:root.theme;flickableTarget:setupScroll}
            ColumnLayout {id:setupFields;width:setupScroll.width-setupBar.reservedExtent;spacing:10
                Controls.ComboBox {theme:root.theme;Layout.fillWidth:true;model:[qsTr("Workspace"),qsTr("Stream"),qsTr("Depot")];enabled:!root.state.editing_workspace && !root.busy;currentIndex:["workspace","stream","depot"].indexOf(root.state.setup_kind);Accessible.name:qsTr("Create");onActivated:{if(currentIndex===2){root.set("setup",false);root.controller.open_view("depots");root.controller.action("depot_editor",{})}else root.set("setup_kind",["workspace","stream","depot"][currentIndex])}}
                Controls.TextField {theme:root.theme;Layout.fillWidth:true;text:root.state.code;enabled:!root.state.editing_workspace && !root.busy;placeholderText:qsTr("Code");Accessible.name:qsTr("Code");onTextEdited:root.set("code",text)}
                Controls.TextField {theme:root.theme;Layout.fillWidth:true;enabled:!root.busy;text:root.state.stream;visible:root.state.setup_kind === "workspace";placeholderText:qsTr("Stream");Accessible.name:qsTr("Stream");onTextEdited:root.set("stream",text)}
                Controls.TextField {theme:root.theme;Layout.fillWidth:true;enabled:!root.busy;text:root.state.root;visible:root.state.setup_kind === "workspace";placeholderText:qsTr("Local workspace root");Accessible.name:qsTr("Local workspace root");onTextEdited:root.set("root",text)}
                Controls.CheckBox {theme:root.theme;visible:root.state.setup_kind==="workspace";text:qsTr("Case-sensitive local paths");checked:root.state.case_sensitive;enabled:!root.busy;onToggled:{root.set("case_sensitive",checked);root.set("mapping_preview",{})}}
                FileWorkspaceMappings {theme:root.theme;Layout.fillWidth:true;visible:root.state.setup_kind==="workspace";value:root.state.mappings;primaryStream:root.state.stream;enabledEditing:!root.busy;onEdited:value=>{root.set("mappings",value);root.set("mapping_preview",{})}}
                Controls.TextField {theme:root.theme;Layout.fillWidth:true;visible:root.state.setup_kind==="workspace";placeholderText:qsTr("Sample depot path");Accessible.name:qsTr("Sample depot path");text:root.previewPath;onTextEdited:root.previewPath=text}
                Controls.Button {theme:root.theme;visible:root.state.setup_kind==="workspace";icon.name:"visibility";text:qsTr("Preview mappings");enabled:!root.busy && root.state.stream.length>0;onClicked:root.act("workspace_preview",{paths:root.previewPath ? [{stream:root.state.stream,path:root.previewPath}] : []})}
                Repeater {model:root.state.mapping_preview.items || [];delegate:Label {required property var modelData;Layout.fillWidth:true;wrapMode:Text.Wrap;color:modelData.collision ? root.theme.error : root.theme.secondaryText;text:modelData.source_path+" → "+(modelData.excluded ? qsTr("Excluded by workspace mapping") : modelData.local_path)+" · "+(modelData.writable ? qsTr("Writable") : qsTr("Read-only"))}}

                Controls.TextField {theme:root.theme;Layout.fillWidth:true;enabled:!root.busy;text:root.state.depot;visible:root.state.setup_kind === "stream";placeholderText:qsTr("Depot");Accessible.name:qsTr("Depot");onTextEdited:root.set("depot",text)}
                Controls.TextField {theme:root.theme;Layout.fillWidth:true;enabled:!root.busy;text:root.state.source;visible:root.state.setup_kind === "stream";placeholderText:qsTr("Parent stream");Accessible.name:qsTr("Parent stream");onTextEdited:root.set("source",text)}
                Label {Layout.fillWidth:true;visible:root.busy;text:root.phase(root.state.progress.phase || root.state.progress.state);color:root.theme.secondaryText;wrapMode:Text.Wrap}
                Label {Layout.fillWidth:true;visible:Boolean(root.state.error);text:root.state.error;color:root.theme.error;wrapMode:Text.Wrap}
            }
        }
    }

    ColumnLayout {
        anchors.fill:parent;spacing:0
        SplitView {
            id:logSplit;objectName:"fileWorkspaceLogSplit"
            Layout.fillWidth:true;Layout.fillHeight:true
            Layout.leftMargin:8;Layout.rightMargin:8;Layout.topMargin:8
            orientation:Qt.Vertical
            handle:Controls.SplitterHandle {objectName:"fileWorkspaceLogSplitter";theme:root.theme;vertical:false}
            onResizingChanged:if(!resizing && workspaceLog.visible)root.set("log_height",workspaceLog.height)
        SplitView {
            id:mainSplit;objectName:"fileWorkspaceMainSplit";SplitView.fillHeight:true;SplitView.minimumHeight:Math.min(240,logSplit.height*0.65)
            orientation:root.narrow ? Qt.Vertical : Qt.Horizontal
            handle: Controls.SplitterHandle { theme:root.theme;vertical:!root.narrow }
            onResizingChanged:if(!resizing && !root.narrow)root.set("tree_width",tree.width)
            Rectangle {
                id:tree;visible:!root.narrow || root.treeOpen
                SplitView.preferredWidth:root.state.tree_width;SplitView.minimumWidth:root.narrow ? 0 : 200;SplitView.maximumWidth:root.narrow ? root.width : root.width*0.5
                SplitView.preferredHeight:240;SplitView.minimumHeight:160
                color:root.theme.panelDeep;radius:root.theme.surfaceRadius;border.color:root.theme.outlineVariant;clip:true
                ColumnLayout {anchors.fill:parent;anchors.margins:8;spacing:4
                    FileWorkspaceNavigation {theme:root.theme;controller:root.controller;Layout.fillWidth:true;onMenuRequested:(kind,anchor)=>root.menu(kind,anchor)}
                    Controls.SegmentedButton {
                        theme:root.theme;Layout.fillWidth:true;segmentWidth:110;currentValue:root.state.tree_view
                        model:[{value:"depot",label:"Depot",icon:"database"},{value:"workspace",label:"Workspace",icon:"desktop"}]
                        onActivated:value=>root.set("tree_view",value)
                    }
                    ListView {
                        id:workspaceTree;Keys.onPressed:event=>root.fileKey(event,"workspace");objectName:"workspaceWorkspaceTree";Layout.fillWidth:true;Layout.fillHeight:true;clip:true;visible:root.state.tree_view==="workspace";model:root.controller.workspace_model
                        ScrollBar.vertical:Controls.ScrollBar {id:workspaceBar;theme:root.theme;flickableTarget:workspaceTree}
                        MouseArea {z:-1;anchors.fill:parent;acceptedButtons:Qt.RightButton;onClicked:mouse=>{actionMenu.actions=root.actions("tree");actionMenu.openAt(parent,mouse.x,mouse.y)}}
                        delegate:FileWorkspaceTreeRow {
                            required property var node
                            width:workspaceTree.width-workspaceBar.reservedExtent;theme:root.theme;row:node;enabled:true
                            caption:root.treeTitle(node);selected:root.state.selection_scope==="workspace" && root.state.selection_ids.indexOf(node.id)>=0
                            onSelectedByUser:modifiers=>root.controller.select_row("workspace",node.id,modifiers)
                            onMenuRequested:(source,x,y)=>root.contextMenu("workspace",node,source,x,y)
                            onDragRequested:dragData=root.controller.drag_payload("workspace",node.id)
                            onDisclosure:root.act("toggle_workspace_tree",{id:node.id})
                            onActivated:root.workspaceActivated(node)
                        }
                    }
                    ListView {
                        id:depotTree;Keys.onPressed:event=>root.fileKey(event,"depot");objectName:"workspaceDepotTree";visible:root.state.tree_view==="depot";Layout.fillWidth:true;Layout.fillHeight:true;clip:true;model:root.controller.depot_model
                        ScrollBar.vertical:Controls.ScrollBar {id:depotBar;theme:root.theme;flickableTarget:depotTree}
                        MouseArea {z:-1;anchors.fill:parent;acceptedButtons:Qt.RightButton;onClicked:mouse=>{actionMenu.actions=root.actions("tree");actionMenu.openAt(parent,mouse.x,mouse.y)}}
                        delegate:FileWorkspaceTreeRow {
                            required property var node
                            readonly property var modelData:node
                            width:depotTree.width-depotBar.reservedExtent;theme:root.theme;row:modelData;enabled:true
                            caption:root.treeTitle(modelData);selected:root.state.selection_scope==="depot" && root.state.selection_ids.indexOf(modelData.id)>=0
                            onSelectedByUser:modifiers=>root.controller.select_row("depot",modelData.id,modifiers)
                            onMenuRequested:(source,x,y)=>root.contextMenu("depot",modelData,source,x,y)
                            onDragRequested:dragData=root.controller.drag_payload("depot",modelData.id)
                            onDisclosure:root.act("toggle_depot",{id:modelData.id})
                            onActivated:root.depotActivated(modelData)
                        }
                        Label {anchors.centerIn:parent;visible:depotTree.count===0;text:qsTr("No depots");color:root.theme.secondaryText}
                    }
                }
            }
            ColumnLayout {
                objectName:"fileWorkspaceWorkingPane"
                SplitView.fillWidth:true;SplitView.fillHeight:true;SplitView.minimumWidth:0;spacing:4
                RowLayout {
                    id:viewToolbar
                    readonly property real scrollGutter:tabBar.hasOverflow ? tabBar.reservedExtent : 0
                    Layout.fillWidth:true;spacing:4
                    Controls.CompactIconButton {Layout.bottomMargin:viewToolbar.scrollGutter;theme:root.theme;visible:root.narrow;iconName:"account-tree";toolTip:qsTr("Depots");Accessible.name:toolTip;onClicked:root.treeOpen=!root.treeOpen}
                    Controls.CompactIconButton {Layout.bottomMargin:viewToolbar.scrollGutter;id:viewMenuButton;objectName:"workspaceViewsButton";theme:root.theme;implicitWidth:root.theme.controlHeight;implicitHeight:implicitWidth;round:true;backgroundColor:root.theme.surfaceContainerHigh;iconName:"view-column";toolTip:qsTr("View");Accessible.name:toolTip;onClicked:root.menu("views",viewMenuButton)}
                Flickable {
                    id:viewTabs;objectName:"workspaceViewTabs";Layout.fillWidth:true;Layout.minimumWidth:0;Layout.preferredHeight:root.theme.controlHeight+viewToolbar.scrollGutter
                    contentWidth:tabsRow.implicitWidth;contentHeight:height;clip:true
                    ScrollBar.horizontal:Controls.ScrollBar {id:tabBar;theme:root.theme;flickableTarget:viewTabs}
                    RowLayout {id:tabsRow;spacing:4;width:implicitWidth
                        Repeater {model:root.state.tabs
                            delegate:Item {
                                id:tabItem
                                required property var modelData
                                implicitWidth:Math.max(140,tabVisual.labelImplicitWidth+96);implicitHeight:root.theme.controlHeight
                                Layout.minimumWidth:implicitWidth;Layout.preferredWidth:implicitWidth
                                objectName:"workspaceViewTab:"+modelData.id
                                activeFocusOnTab:true;Accessible.role:Accessible.PageTab;Accessible.name:tabVisual.title
                                Keys.onReturnPressed:root.selectTab(modelData)
                                Keys.onSpacePressed:root.selectTab(modelData)
                                Controls.WorkspaceTabVisual {
                                    id:tabVisual;anchors.fill:parent;theme:root.theme
                                    title:tabItem.modelData.custom ? tabItem.modelData.title : qsTr(tabItem.modelData.title)
                                    iconName:tabItem.modelData.icon;current:root.state.active_tab===tabItem.modelData.id;closable:true
                                    hovered:tabHover.hovered;pressed:tabActivate.pressed
                                    onCloseRequested:root.controller.close_tab(tabItem.modelData.id)
                                }
                                HoverHandler {id:tabHover}
                                Controls.ActivationHandler {id:tabActivate;anchors.rightMargin:36;enabled:true;onActivated:root.selectTab(tabItem.modelData)}
                            }
                        }
                    }
                }
                    Controls.CompactIconButton {Layout.bottomMargin:viewToolbar.scrollGutter;theme:root.theme;objectName:"newChangelistButton";iconName:"add";toolTip:qsTr("New changelist");Accessible.name:toolTip;enabled:!root.busy && Boolean(root.state.workspace);onClicked:root.act("create_change")}
                    Controls.CompactIconButton {Layout.bottomMargin:viewToolbar.scrollGutter;theme:root.theme;visible:typeof dockModel!=="undefined";objectName:"fileWorkspaceMaximize";iconName:typeof dockModel!=="undefined" && dockModel.maximizedPanelId==="commit_queue" ? "window-restore" : "open-in-full";toolTip:typeof dockModel!=="undefined" && dockModel.maximizedPanelId==="commit_queue" ? qsTr("Restore panel") : qsTr("Maximize panel");Accessible.name:toolTip;onClicked:dockModel.maximize_panel("commit_queue")}
                    Controls.CompactIconButton {Layout.bottomMargin:viewToolbar.scrollGutter;id:workspaceMenuButton;theme:root.theme;iconName:"more_vert";toolTip:qsTr("Workspace actions");Accessible.name:toolTip;onClicked:root.menu("workspace",workspaceMenuButton)}
                }
                Label {Layout.fillWidth:true;visible:!root.state.active_tab;text:qsTr("Open a view from the View menu");color:root.theme.secondaryText}
                SplitView {
                id:rightSplit;Layout.fillWidth:true;Layout.fillHeight:true;Layout.minimumWidth:0;orientation:Qt.Vertical
                handle: Controls.SplitterHandle { theme:root.theme;vertical:false }
                onResizingChanged:if(!resizing)root.set("details_height",root.activeTab.kind==="files" ? fileInspector.height : detailsPanel.height)
                Rectangle {
                    visible:["changes","files"].indexOf(root.activeTab.kind)>=0;SplitView.fillHeight:true;SplitView.minimumHeight:root.activeTab.kind==="files" ? Math.min(140,rightSplit.height*0.55) : 180
                    color:root.theme.panelDeep;radius:root.theme.surfaceRadius;border.color:root.theme.outlineVariant;clip:true
                    ColumnLayout {anchors.fill:parent;anchors.margins:8;spacing:4
                        Label {Layout.fillWidth:true;visible:root.activeTab.kind==="files" && root.state.local_dirty;text:qsTr("Local changes detected. Reconcile to review them.");color:root.theme.yellow;wrapMode:Text.Wrap}
                        RowLayout {Layout.fillWidth:true;spacing:4;visible:root.activeTab.kind === "files"
                            Controls.TextField {theme:root.theme;Layout.fillWidth:true;Layout.minimumWidth:0;text:root.state.prefix;placeholderText:qsTr("Path prefix");Accessible.name:qsTr("Path prefix");enabled:!root.busy;onTextEdited:root.set("prefix",text);onAccepted:root.act("files")}
                            Controls.CompactIconButton {theme:root.theme;iconName:"filter";toolTip:qsTr("Filter");Accessible.name:toolTip;enabled:!root.busy;onClicked:root.act("files")}
                        }
                        RowLayout {Layout.fillWidth:true;spacing:4
                            Controls.TextField {theme:root.theme;Layout.fillWidth:true;Layout.minimumWidth:0;placeholderText:qsTr("Filter loaded files");text:root.state.name_filter;onTextEdited:root.set("name_filter",text)}
                            Controls.ComboBox {theme:root.theme;visible:!root.narrow;Layout.preferredWidth:150;model:[qsTr("All states"),qsTr("Modified"),qsTr("Added"),qsTr("Missing"),qsTr("Uploaded"),qsTr("Marked for delete")];currentIndex:["","Modified","Added","Missing","Uploaded","Marked for delete"].indexOf(root.state.status_filter);Accessible.name:qsTr("File state");onActivated:root.set("status_filter",["","Modified","Added","Missing","Uploaded","Marked for delete"][currentIndex])}

                            Controls.Button {objectName:"reconcileAddFiles";theme:root.theme;text:qsTr("Add to changelist…");icon.name:"add";visible:root.activeTab.kind==="files" && root.state.view==="local";enabled:!root.busy && root.state.selection_scope==="files" && root.state.selected.length>0;onClicked:root.pickTarget("apply_reconcile")}
                            Controls.CompactIconButton {id:changeMenuButton;objectName:"changelistActionsButton";theme:root.theme;iconName:"more_vert";toolTip:qsTr("Changelist actions");Accessible.name:toolTip;visible:root.activeTab.kind==="changes";enabled:Boolean(root.state.change.code);onClicked:root.menu("change",changeMenuButton)}
                            Controls.CompactIconButton {id:fileMenuButton;objectName:"fileActionsButton";theme:root.theme;iconName:"more_vert";toolTip:qsTr("File actions");Accessible.name:toolTip;visible:root.activeTab.kind==="files" || root.state.selected.length>0;onClicked:root.menu("files",fileMenuButton)}
                        }
                        Item {Layout.fillWidth:true;Layout.preferredHeight:28;clip:true
                            Row {x:4+(root.activeTab.kind==="changes" ? 24-changes.contentX : -files.contentX);spacing:6
                                Item {width:47;height:28}
                                Repeater {model:root.state.columns.filter(column=>column.visible)
                                    delegate:Controls.PopupAction {required property var modelData;property var theme:root.theme;width:modelData.width;height:28;hoverEnabled:true
                                        Accessible.name:qsTr(({path:"File",local_status:"Local changes",server_status:"Server state",checkout:"Checkout / locks",number:"Version",local_number:"Local revision",have_number:"Have",head_number:"Head",size:"Size",type:"Type"})[modelData.key])
                                        background:Controls.ItemSurface {theme:root.theme;hovered:parent.hovered;normalColor:"transparent";railVisible:false}
                                        contentItem:Label {text:parent.Accessible.name+(root.state.sort_column===modelData.key ? (root.state.sort_desc ? " ↓" : " ↑") : "");color:root.theme.secondaryText;elide:Text.ElideRight;verticalAlignment:Text.AlignVCenter;font.family:root.theme.fontFamily;font.pointSize:Controls.Typography.label}
                                        onClicked:root.controller.sort_files(modelData.key)}
                                }
                            }
                        }
                        ListView {
                            id:changes;contentWidth:Math.max(width,root.columnWidth+(root.activeTab.kind==="changes" ? changeBar.reservedExtent : fileBar.reservedExtent));flickableDirection:Flickable.HorizontalAndVerticalFlick;Keys.onPressed:event=>root.fileKey(event,"changes");objectName:"workspaceChangelistTree";Layout.fillWidth:true;Layout.fillHeight:true;visible:root.activeTab.kind === "changes";clip:true;onContentYChanged:if(moving || changeBar.pressed)root.controller.remember_scroll("changes",contentY);onModelChanged:Qt.callLater(()=>contentY=root.state.scroll.changes || 0);model:root.controller.change_model
                            ScrollBar.vertical:Controls.ScrollBar {id:changeBar;theme:root.theme;flickableTarget:changes}
                        TapHandler {parent:changes;acceptedButtons:Qt.RightButton;onTapped:point=>{if(!changes.itemAt(point.position.x+changes.contentX,point.position.y+changes.contentY)){actionMenu.actions=root.actions("changes_background");actionMenu.openAt(changes,point.position.x,point.position.y)}}}
                            ScrollBar.horizontal:Controls.ScrollBar {theme:root.theme;flickableTarget:changes}
                            delegate:Loader {
                                required property var node
                                readonly property var modelData:node
                                width:changes.contentWidth-changeBar.reservedExtent;enabled:true
                                sourceComponent:node.kind === "file" ? changeFile : changeBranch
                                height:item ? item.implicitHeight : 0
                            }
                            Label {anchors.centerIn:parent;visible:changes.count===0;text:qsTr("No changelists on this page");color:root.theme.secondaryText}
                        }
                        ListView {id:files;contentWidth:Math.max(width,root.columnWidth+(root.activeTab.kind==="changes" ? changeBar.reservedExtent : fileBar.reservedExtent));flickableDirection:Flickable.HorizontalAndVerticalFlick;Keys.onPressed:event=>root.fileKey(event,"files");visible:root.activeTab.kind === "files";objectName:"workspaceFiles";Layout.fillWidth:true;Layout.fillHeight:true;clip:true;onContentYChanged:if(moving || fileBar.pressed)root.controller.remember_scroll("files",contentY);onModelChanged:Qt.callLater(()=>{contentY=root.state.scroll.files || 0;revealTreeSelection()});model:{const state=root.state;const name=state.name_filter;const status=state.status_filter;return state.rows.filter(row=>Presentation.matches(row,name,status))}
                            function revealTreeSelection() {
                                if(!visible || root.activeTab.source!=="selection" || ["depot","workspace"].indexOf(root.state.selection_scope)<0)return
                                const index=model.findIndex(row=>(row.stream || root.state.stream)===root.state.file_focus.stream && (row.source_path || row.path)===root.state.file_focus.path)
                                if(index>=0){currentIndex=index;positionViewAtIndex(index,ListView.Contain)}
                            }
                            Connections {target:root.controller;function onStateChanged(){Qt.callLater(files.revealTreeSelection)}}
                            ScrollBar.vertical:Controls.ScrollBar {id:fileBar;theme:root.theme;flickableTarget:files}
                        MouseArea {z:-1;anchors.fill:parent;acceptedButtons:Qt.RightButton;onClicked:mouse=>{actionMenu.actions=root.actions("files");actionMenu.openAt(parent,mouse.x,mouse.y)}}
                            ScrollBar.horizontal:Controls.ScrollBar {theme:root.theme;flickableTarget:files}
                            delegate:FileWorkspaceFileRow {
                                required property var modelData
                                width:files.contentWidth-fileBar.reservedExtent;theme:root.theme;row:modelData;narrow:root.narrow;selected:root.state.selection_scope==="files" ? root.state.selection_ids.indexOf(root.controller.row_identity(modelData))>=0 : root.activeTab.source==="selection" && ["depot","workspace"].indexOf(root.state.selection_scope)>=0 && root.state.files_selection.some(item=>root.controller.row_identity(item)===root.controller.row_identity(modelData));enabled:true
                                objectName:"workspaceFile_"+modelData.path
                                localLabel:root.localStatus(modelData.local_status);serverLabel:modelData.change_state==="submitted" ? qsTr("Submitted") : modelData.change_state==="shelved" ? qsTr("Shelved") : root.serverStatus(modelData.server_status || modelData.action);checkoutLabel:root.holders(modelData);currentUser:root.controller.current_user;checkoutHolders:root.state.locks[(modelData.stream || root.state.change.stream || root.state.stream)+"\0"+(modelData.source_path || modelData.path)] || []
                                columns:root.state.columns
                                onSelectedByUser:modifiers=>root.controller.select_row("files",root.controller.row_identity(modelData),modifiers)
                                onDragRequested:dragData=root.controller.drag_payload("files",root.controller.row_identity(modelData))
                                onSelectedChangedByUser:checked => root.controller.select_file(modelData.path,checked)
                                onActivated:root.command("open_local")
                                onMenuRequested:(source,x,y)=>root.contextMenu("files",modelData,source,x,y)
                            }
                            Label {anchors.centerIn:parent;visible:files.count===0;text:qsTr("No files on this page");color:root.theme.secondaryText;font.family:root.theme.fontFamily}
                        }
                        RowLayout {Layout.fillWidth:true;Layout.preferredHeight:28
                            Label {Layout.fillWidth:true;Layout.minimumWidth:0;text:(root.state.view === "change" ? root.state.change_file_count : root.state.rows.length) + " " + qsTr("files");color:root.theme.secondaryText;font.family:root.theme.fontFamily}
                            Controls.CompactIconButton {theme:root.theme;iconName:"chevron-right";toolTip:qsTr("Next changelists");Accessible.name:toolTip;visible:root.activeTab.kind==="changes" && Boolean(root.state.changes_after);enabled:!root.busy;onClicked:root.act("next_changes")}
                            Controls.CompactIconButton {theme:root.theme;iconName:"chevron-left";toolTip:qsTr("Previous page");Accessible.name:toolTip;visible:root.state.view !== "change";enabled:!root.busy && root.state.cursors.length>0;onClicked:root.act("previous_files")}
                            Controls.CompactIconButton {theme:root.theme;iconName:"chevron-right";toolTip:qsTr("Next page");Accessible.name:toolTip;visible:root.state.view !== "change";enabled:!root.busy && Boolean(root.state.after);onClicked:root.act("next_files")}
                        }
                    }
                }
                Loader {
                    active:root.activeTab.kind==="catalog" || root.activeTab.kind==="graph"
                    visible:active;SplitView.fillHeight:true;SplitView.minimumHeight:120
                    sourceComponent:root.activeTab.kind==="graph" ? graphView : root.activeTab.source==="streams" ? streamsView : catalogView
                }
                FileWorkspaceInspector {
                    id:fileInspector;theme:root.theme;info:root.state.inspection || ({});preview:root.state.inspection.preview || ({});currentTab:root.state.inspector_tab;busy:root.state.inspection_busy;error:root.state.inspection_error;onTabSelected:tab=>root.controller.set_value("inspector_tab",tab);visible:root.activeTab.kind==="files"
                    SplitView.preferredHeight:Math.min(root.state.details_height,rightSplit.height*0.4);SplitView.minimumHeight:Math.min(100,rightSplit.height*0.35)
                }
                FileWorkspaceHistory {
                    id:historyView;theme:root.theme;controller:root.controller;revision:root.detail
                    visible:root.activeTab.kind==="history";SplitView.fillHeight:true;SplitView.minimumHeight:120
                    onSelected:(row,modifiers,context)=>{root.detail=row;root.controller.select_row("history",row.code,modifiers,context)}
                    onContextRequested:(item,x,y)=>{actionMenu.actions=root.actions("details");actionMenu.openAt(item,x,y)}
                    onKeyPressed:event=>root.fileKey(event,"history")
                }
                Rectangle {
                    id:detailsPanel;visible:["conflicts","tasks"].indexOf(root.activeTab.kind)>=0;SplitView.fillHeight:true;SplitView.preferredHeight:root.state.details_height;SplitView.minimumHeight:120;SplitView.maximumHeight:rightSplit.height
                    color:root.theme.panelDeep;radius:root.theme.surfaceRadius;border.color:root.theme.outlineVariant;clip:true
                    ColumnLayout {anchors.fill:parent;anchors.margins:8;spacing:4
                        RowLayout {Layout.fillWidth:true
                            Label {Layout.fillWidth:true;text:(root.activeTab.custom ? root.activeTab.title : qsTr(root.activeTab.title));color:root.theme.primaryText;elide:Text.ElideMiddle}
                            Item {Layout.fillWidth:true;visible:!root.narrow}
                            Controls.CompactIconButton {id:detailMenuButton;theme:root.theme;iconName:"more_vert";toolTip:qsTr("Detail actions");Accessible.name:toolTip;onClicked:root.menu("details",detailMenuButton)}
                        }
                        RowLayout {Layout.fillWidth:true;visible:root.detailsView==="conflicts"
                            Controls.TabButton {theme:root.theme;text:qsTr("Unresolved");checked:!root.showResolved;onClicked:root.showResolved=false}
                            Controls.TabButton {theme:root.theme;text:qsTr("Resolved");checked:root.showResolved;onClicked:root.showResolved=true}
                        }
                        RowLayout {Layout.fillWidth:true;Layout.fillHeight:true;spacing:8
                            ListView {id:details;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;model:root.detailsView === "conflicts" ? (root.showResolved ? root.state.resolved_conflicts : root.state.conflicts) : root.state.tasks;spacing:2
                                ScrollBar.vertical:Controls.ScrollBar {id:detailsBar;theme:root.theme;flickableTarget:details}
                                delegate:Controls.EditorListItem {required property var modelData;theme:root.theme;width:details.width-detailsBar.reservedExtent;implicitHeight:36;padding:6
                                    iconName:root.detailsView==="conflicts" ? "warning" : "cloud-upload"
                                    text:root.detailsView === "conflicts" ? modelData.path : root.phase(modelData.phase || modelData.state)+" · "+(modelData.files_done || 0)+" · "+(modelData.change || modelData.workspace || modelData.task)
                                    selected:root.detail===modelData;enabled:true;onClicked:{root.detail=modelData;if(root.detailsView==="tasks")root.act("task_files",{task:modelData.task})}
                                    MouseArea {anchors.fill:parent;acceptedButtons:Qt.LeftButton | Qt.RightButton;onClicked:mouse=>{root.detail=modelData;if(root.detailsView==="tasks")root.act("task_files",{task:modelData.task});if(root.detailsView==="conflicts" && !root.showResolved){let selected=root.state.conflict_selected;if(mouse.button!==Qt.RightButton || selected.indexOf(modelData.path)<0)root.set("conflict_selected",mouse.modifiers & Qt.ControlModifier ? (selected.indexOf(modelData.path)>=0 ? selected.filter(path=>path!==modelData.path) : [...selected,modelData.path]) : [modelData.path]);}if(mouse.button===Qt.RightButton){actionMenu.actions=root.actions("details");actionMenu.openAt(parent,mouse.x,mouse.y)}}}
                                }
                                Label {anchors.centerIn:parent;visible:details.count===0;text:root.detailsView === "conflicts" ? qsTr("No conflicts") : qsTr("No transfers");color:root.theme.secondaryText;font.family:root.theme.fontFamily;elide:Text.ElideRight;width:parent.width;horizontalAlignment:Text.AlignHCenter}
                            }
                            ColumnLayout {Layout.fillWidth:true;Layout.fillHeight:true;visible:root.detailsView==="tasks"
                                Label {Layout.fillWidth:true;visible:Boolean(root.state.task_info.error);text:root.state.task_info.error || "";color:root.theme.error;wrapMode:Text.Wrap;textFormat:Text.PlainText}
                                ListView {id:taskFiles;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;model:root.state.task_files
                                    ScrollBar.vertical:Controls.ScrollBar {id:taskBar;theme:root.theme;flickableTarget:taskFiles}
                                    delegate:Controls.EditorListItem {required property var modelData;theme:root.theme;width:taskFiles.width-taskBar.reservedExtent;implicitHeight:32;text:modelData.path+" · "+qsTr(modelData.state)+" · "+((modelData.received || 0)/1048576).toFixed(1)+" / "+((modelData.size || 0)/1048576).toFixed(1)+" MB"}
                                }
                                Controls.Button {theme:root.theme;icon.name:"chevron-right";text:qsTr("Next files");visible:Boolean(root.state.task_files_after);onClicked:root.act("next_task_files")}
                            }
                            Controls.TextArea {theme:root.theme;Layout.fillWidth:true;Layout.fillHeight:true;Layout.preferredWidth:detailsPanel.width*0.5;visible:root.state.preview.length>0;text:root.state.preview;readOnly:true;Accessible.name:qsTr("File preview")}
                        }
                    }
                }
            }
            }
        }
        FileWorkspaceLog {
            id:workspaceLog;theme:root.theme;controller:root.controller
            visible:root.state.log_visible
            SplitView.preferredHeight:Math.min(root.state.log_height,logSplit.height*0.45)
            SplitView.minimumHeight:Math.min(80,logSplit.height*0.2)
            SplitView.maximumHeight:logSplit.height*0.6
        }
        }
        Controls.DockWorkspaceFooter {objectName:"fileWorkspaceFooter";theme:root.theme;color:root.theme.panelDeep;Layout.fillWidth:true;Layout.preferredHeight:root.theme.controlHeight
            RowLayout {anchors.fill:parent;anchors.leftMargin:8;anchors.rightMargin:8;spacing:8
                Controls.BusyIndicator {uiTheme:root.theme;running:root.busy;visible:root.busy}
                Label {Layout.fillWidth:true;Layout.minimumWidth:0;objectName:"fileWorkspaceStatus";text:!root.busy && !root.state.progress.phase && !root.state.progress.state ? qsTr("Ready")+(root.state.workspace ? " · "+root.state.workspace : "")+(root.state.selected.length ? " · "+root.state.selected.length+" "+qsTr("selected") : "") : (root.state.progress.operation_stage ? qsTr("Step %1 of %2").arg(root.state.progress.operation_stage).arg(root.state.progress.operation_stages)+" · " : "")+root.phase(root.state.progress.phase || root.state.progress.state)+" · "+(root.state.progress.phase_files_done ?? root.state.progress.files_done ?? 0)+(root.state.progress.total_known ? " / "+(root.state.progress.files_total || 0) : "")+" "+qsTr("files")+" · "+((root.state.progress.phase_bytes_done ?? root.state.progress.bytes_done ?? 0)/1048576).toFixed(1)+(root.state.progress.total_known ? " / "+((root.state.progress.bytes_total || 0)/1048576).toFixed(1) : "")+" MB";color:root.theme.secondaryText;font.family:root.theme.fontFamily;elide:Text.ElideRight}
                ProgressBar {Layout.preferredWidth:root.narrow ? 60 : 120;visible:root.busy;indeterminate:!root.state.progress.total_known;value:["staging","verifying","running"].indexOf(root.state.progress.phase || root.state.progress.state)>=0 ? (root.state.progress.phase_files_done ?? root.state.progress.files_done ?? 0)/Math.max(1,root.state.progress.files_total || 0) : root.state.progress.bytes_total>0 ? (root.state.progress.phase_bytes_done ?? root.state.progress.bytes_done ?? 0)/root.state.progress.bytes_total : 0;Accessible.name:qsTr("Transfer progress")}
                Label {visible:!root.narrow && root.state.progress.bytes_per_second>0;text:((root.state.progress.bytes_per_second || 0)/1048576).toFixed(1)+" MB/s"+(root.state.progress.eta_seconds>0 ? " · ~"+Math.ceil(root.state.progress.eta_seconds)+" "+qsTr("seconds") : "");color:root.theme.secondaryText}
                Label {Layout.fillWidth:true;Layout.minimumWidth:0;visible:!root.narrow;text:root.state.progress.path || "";color:root.theme.secondaryText;elide:Text.ElideMiddle}
                Controls.CompactIconButton {objectName:"fileWorkspaceToggleLog";theme:root.theme;iconName:"terminal";toolTip:root.state.log_visible ? qsTr("Hide log") : qsTr("Show log");Accessible.name:toolTip;onClicked:root.set("log_visible",!root.state.log_visible)}
                Controls.CompactIconButton {theme:root.theme;iconName:"close";toolTip:qsTr("Stop waiting");Accessible.name:toolTip;visible:root.busy;onClicked:root.controller.stop()}
            }
        }
    }
}

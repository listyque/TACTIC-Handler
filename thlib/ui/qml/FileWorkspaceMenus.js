.pragma library

function deletionTargets(ctx) {
    const rows=Object.values(ctx.state.selection_records || {})
    return ctx.state.selection_scope==="changes" && rows.length ? rows : (ctx.state.change.code ? [ctx.state.change] : [])
}

function selectionReason(ctx,command) {
    const rows=Object.values(ctx.state.selection_records || {})
    if(command==="delete_change") {
        const targets=deletionTargets(ctx)
        if(ctx.busy)return qsTr("An operation is running")
        if(!targets.length || targets.some(row=>row.path || !row.code))return qsTr("Select changelist headers")
        if(targets.some(row=>row.owner!==ctx.controller.current_user || ["pending","shelved"].indexOf(row.state)<0))return qsTr("Select your pending changelists or shelves")
        if(targets.some(row=>row.depot_writable===false || ctx.state.streams.some(stream=>stream.code===row.stream && stream.writable===false)))return qsTr("Depot write access is required")
        if(targets.some(row=>row.active_transfer || row.active_bulk || row.integration || row.indexing))return qsTr("Finish the active changelist operation first")
        if(targets.length>1 && targets.some(row=>row.state==="pending" && row.opened_files!==0))return qsTr("Move or revert files before deleting these changelists")
        return ""
    }
    if(command==="revert_files") {
        if(!rows.length || rows.some(row=>(row.kind || "file")!=="file" || !row.path))return qsTr("Select files first")
        if(ctx.busy)return qsTr("An operation is running")
        if(rows.some(row=>!(row.parent && row.change_state==="pending" && row.owner===ctx.controller.current_user && row.workspace===ctx.state.workspace)
            && !(ctx.state.locks[(row.stream || ctx.state.stream)+"\0"+(row.source_path || row.path)] || []).some(holder=>holder.owner===ctx.controller.current_user && holder.workspace===ctx.state.workspace)))
            return qsTr("The selected file is not opened in this workspace")
        return ""
    }
    const files=["checkout_ordinary","checkout_exclusive","move_files","remove_files","rename_file","mark_delete","stage_deletions","revert_unchanged","shelve_selected","replace_shelf","delete_shelf_files","apply_reconcile","open_local","reveal_local","delete_local","diff_local","diff_have","diff_shelf","file_history","sync_selected","revision_selected","reveal_tree"]
    if(files.indexOf(command)<0){
        const mutations=["submit","submit_task_status","description","shelve","shelve_revert","compare_shelf","offer_change","revert","revert_unchanged_change","delete_change","unshelve_begin","rebase_begin","merge_begin","resume_upload","index_change","move_all_files"]
        if(mutations.indexOf(command)>=0){
            if(ctx.state.change.depot_writable===false || ctx.state.streams.some(stream=>stream.code===ctx.state.change.stream && stream.writable===false))return qsTr("Depot write access is required")
            if(ctx.state.selection_scope==="changes" && new Set(rows.map(row=>row.parent || row.code)).size>1)return qsTr("Select one changelist")
            if(ctx.state.change.active_transfer || ctx.state.change.active_bulk)return qsTr("Finish the active changelist operation first")
            if(ctx.state.change.integration)return qsTr("Resolve the integration first")
        }
        return ""
    }
    if(!rows.length)return qsTr("Select files first")
    if(rows.some(row=>(row.kind || "file")!=="file" || !row.path))return qsTr("Select files without folders or changelists")
    if(ctx.state.selection_query)return qsTr("Use the actions for the selected server query")
    const writes=["checkout_ordinary","checkout_exclusive","move_files","remove_files","rename_file","mark_delete","stage_deletions","revert_unchanged","shelve_selected","replace_shelf","delete_shelf_files","apply_reconcile"]
    if(writes.indexOf(command)>=0){
        if(rows.some(row=>row.depot_writable===false || ctx.state.streams.some(stream=>stream.code===(row.stream || ctx.state.stream) && stream.writable===false)))return qsTr("Depot write access is required")
        if(rows.some(row=>row.writable===false))return qsTr("Selection includes a read-only mapping")
        if(new Set(rows.map(row=>row.stream || ctx.state.stream)).size>1)return qsTr("Select files from one stream")
        if(rows.some(row=>(ctx.state.locks[(row.stream || ctx.state.stream)+"\0"+(row.source_path || row.path)] || []).some(holder=>(holder.mode==="exclusive" || command==="checkout_exclusive") && (holder.owner!==ctx.controller.current_user || holder.workspace!==ctx.state.workspace))))return qsTr("The selected checkout conflicts with another changelist or workspace")
    }
    const pending=["move_files","remove_files","rename_file","revert_unchanged","shelve_selected","replace_shelf","diff_shelf"]
    if(pending.indexOf(command)>=0 && (ctx.state.view!=="change" && ctx.state.selection_scope!=="changes" || rows.some(row=>row.parent && row.parent!==ctx.state.change.code || row.change_state && row.change_state!=="pending" || row.owner && row.owner!==ctx.controller.current_user || row.workspace && row.workspace!==ctx.state.workspace)))return qsTr("Select files from the current owned pending changelist")
    if(command==="delete_shelf_files" && rows.some(row=>row.parent && row.parent!==ctx.state.change.code || row.change_state && row.change_state!=="shelved"))return qsTr("Select files from the current shelf")
    if(["rename_file","diff_local","diff_have","diff_shelf","file_history","reveal_tree"].indexOf(command)>=0 && rows.length!==1)return qsTr("Select one file")
    if(["open_local","delete_local","diff_local","diff_have","rename_file"].indexOf(command)>=0 && rows.some(row=>["missing","unmapped"].indexOf(row.local_status)>=0))return qsTr("A local copy is missing or not mapped")
    if(command==="reveal_local" && rows.some(row=>row.local_status==="unmapped"))return qsTr("A local copy is missing or not mapped")
    if(command==="stage_deletions" && rows.some(row=>row.local_status!=="missing"))return qsTr("Select missing local files")
    if(command==="apply_reconcile" && rows.some(row=>["added","modified","missing"].indexOf(row.local_status)<0))return qsTr("Select local changes")
    return ""
}

function dropReason(ctx,target,payload,urls) {
    if(ctx.busy)return qsTr("An operation is running")
    if(target.kind!=="change" || target.state!=="pending")return qsTr("Choose a pending target changelist")
    if(target.owner!==ctx.controller.current_user || target.workspace!==ctx.state.workspace)return qsTr("Choose an owned pending changelist")
    if(target.depot_writable===false || ctx.state.streams.some(stream=>stream.code===target.stream && stream.writable===false))return qsTr("Depot write access is required")
    if(target.active_transfer || target.active_bulk || target.integration)return qsTr("Finish the active changelist operation first")
    if(!payload)return (urls || []).length>0 && urls.length<=1000 ? "" : qsTr("Drop 1..1000 selected file or folder roots.")
    let data
    try{data=JSON.parse(payload)}catch(error){return qsTr("Invalid file drag payload.")}
    if(!data || typeof data!=="object" || Array.isArray(data))return qsTr("Invalid file drag payload.")
    if(data.project!==ctx.controller.application_project || data.workspace!==ctx.state.workspace)return qsTr("Drag files within the current project and workspace.")
    if(!Array.isArray(data.rows) || !data.rows.length || data.rows.length>1000)return qsTr("Drop 1..1000 selected file or folder roots.")
    const rows=data.rows
    if(rows.some(row=>!row || typeof row!=="object" || (row.kind || "file")==="file" && (typeof row.path!=="string" || !row.path)))return qsTr("Invalid file drag payload.")
    if(rows.some(row=>row.writable===false || row.stream && row.stream!==target.stream))return qsTr("Select writable files from one changelist stream.")
    if(rows.length===1 && rows[0].state==="shelved")return ""
    if(rows.some(row=>["file","directory","stream","workspace"].indexOf(row.kind || "file")<0))return qsTr("Drop files, folders or one stream into a pending changelist.")
    const parents=new Set(rows.filter(row=>row.parent && row.change_state==="pending").map(row=>row.parent))
    if(parents.has(target.code))return qsTr("The files are already in this changelist")
    if(parents.size>1 || parents.size && rows.some(row=>!row.parent || row.change_state!=="pending"))return qsTr("Select files from one changelist.")
    return ""
}

function dropCaption(target,payload,urls) {
    let rows=[],count=(urls || []).length
    if(payload){try{rows=JSON.parse(payload).rows;count=rows.length}catch(error){return ""}}
    if(rows.length===1 && rows[0].state==="shelved")return qsTr("Restore shelf into changelist #%1").arg(target.number)
    if(rows.length && rows.every(row=>row.parent && row.change_state==="pending"))return qsTr("Move %1 files to changelist #%2").arg(count).arg(target.number)
    return rows.some(row=>["directory","stream","workspace"].indexOf(row.kind)>=0) || !rows.length ? qsTr("Add %1 file or folder roots to changelist #%2").arg(count).arg(target.number) : qsTr("Add %1 files to changelist #%2").arg(count).arg(target.number)
}

function actions(ctx,kind) {
        const selected = !ctx.busy && ctx.state.selected.length > 0
        if(kind==="actions")return [
            ctx.entry(qsTr("New changelist"),"create_change","add",!ctx.busy && Boolean(ctx.state.workspace)),
            ctx.entry(qsTr("Go to changelist"),"goto_change","search",!ctx.busy),
            {title:qsTr("File actions"),icon:"file",children:actions(ctx,"files")},
            {title:qsTr("Changelist actions"),icon:"archive",children:actions(ctx,"change")},
            ctx.entry(qsTr("Submit"),"submit","check",ctx.editable)]
        if(kind==="tools")return [
            ctx.entry(qsTr("Refresh"),"refresh","refresh",!ctx.busy),
            ctx.entry(qsTr("Reconcile"),"reconcile","sync",!ctx.busy && Boolean(ctx.state.workspace)),
            {title:qsTr("Recovery"),icon:"play-arrow",children:[
                ctx.entry(qsTr("Resume local moves"),"resume_local_moves","swap-horizontal",!ctx.busy && Boolean(ctx.state.workspace)),
                ctx.entry(qsTr("Resume interrupted operation"),"resume_operation","play-arrow",!ctx.busy && Boolean(ctx.state.recovery?.action || ctx.state.recovery?.available))]},
            {title:qsTr("Sync"),icon:"cloud-download",children:[
                ctx.entry(qsTr("Get latest workspace"),"get_latest","cloud-download",!ctx.busy && Boolean(ctx.state.workspace)),
                ctx.entry(qsTr("Get Revision…"),"revision_workspace","history",!ctx.busy && Boolean(ctx.state.workspace))]},
            ctx.entry(qsTr("Columns"),"columns","table",true),
            {title:qsTr("File state"),icon:"filter",children:[
                    [qsTr("All states"),""],[qsTr("Modified"),"Modified"],[qsTr("Added"),"Added"],
                    [qsTr("Missing"),"Missing"],[qsTr("Uploaded"),"Uploaded"],[qsTr("Marked for delete"),"Marked for delete"]
                ].map(row=>ctx.entry(row[0],"filter_state/"+row[1],"filter",true))},
            {title:qsTr("Selected server query"),icon:"check-all",children:[
                ctx.entry(qsTr("Select all matching server files"),"select_query","check-all",!ctx.busy && ["depot","have","change"].indexOf(ctx.state.view)>=0),
                ctx.entry(qsTr("Checkout query (ordinary)"),"query_checkout_ordinary","edit",!ctx.busy && Boolean(ctx.state.selection_query)),
                ctx.entry(qsTr("Checkout query (exclusive)"),"query_checkout_exclusive","lock",!ctx.busy && Boolean(ctx.state.selection_query)),
                ctx.entry(qsTr("Move query files…"),"query_move","swap-horizontal",ctx.editable && ctx.state.view==="change" && Boolean(ctx.state.selection_query)),
                ctx.entry(qsTr("Revert query files"),"query_revert","undo",ctx.editable && ctx.state.view==="change" && Boolean(ctx.state.selection_query)),
                ctx.entry(qsTr("Mark query files for delete"),"query_delete","delete",ctx.editable && ctx.state.view==="change" && Boolean(ctx.state.selection_query)),
                ctx.entry(qsTr("Export selected file manifest"),"export_query","download",!ctx.busy && Boolean(ctx.state.selection_query))]},
            ctx.entry(qsTr("Help"),"help","help",true)]
        if(kind==="views")return [
            ctx.entry(ctx.state.log_visible ? qsTr("Hide log") : qsTr("Show log"),"toggle_log","terminal",true),
            ctx.entry(qsTr("Depot Tree"),"depot_tree","database",true),
            ctx.entry(qsTr("Workspace Tree"),"workspace_tree","desktop",true),
            {separator:true},
            ...ctx.controller.view_presets.filter(view=>!view.admin_only || ctx.state.administrator).map(view=>ctx.entry(qsTr(view.title),"view_"+view.id,view.icon,true)),
            {separator:true},
            ctx.entry(qsTr("New view tab"),"new_tab","add",!ctx.busy),
            ctx.entry(qsTr("Edit view tab"),"edit_tab","edit",!ctx.busy && Boolean(ctx.state.active_tab)),
            ctx.entry(qsTr("Move tab left"),"tab_left","chevron-left",!ctx.busy && Boolean(ctx.state.active_tab)),
            ctx.entry(qsTr("Move tab right"),"tab_right","chevron-right",!ctx.busy && Boolean(ctx.state.active_tab)),
            ctx.entry(qsTr("Close tab"),"close_tab","close",!ctx.busy && Boolean(ctx.state.active_tab))]
        if(kind==="tree")return [
            ctx.entry(qsTr("Get latest"),"sync_folder","cloud-download",!ctx.busy && Boolean(ctx.state.workspace)),
            ctx.entry(qsTr("Get Revision…"),"revision_folder","history",!ctx.busy && Boolean(ctx.state.workspace)),
            ctx.entry(qsTr("Reconcile"),"reconcile","sync",!ctx.busy && Boolean(ctx.state.workspace)),
            ctx.entry(qsTr("Copy depot path"),"copy_depot","copy",true),
            ctx.entry(qsTr("Open Files view"),"view_files","file",!ctx.busy),
            ctx.entry(qsTr("Workspace setup"),"workspace_setup","settings",!ctx.busy)]
        if (kind === "workspace") return [
            {title:qsTr("Actions"),icon:"play-arrow",children:actions(ctx,"actions")},
            {title:qsTr("Tools"),icon:"settings",children:actions(ctx,"tools")},
            ctx.entry(qsTr("Choose local folder"),"choose_folder","folder-open",!ctx.busy),
            ctx.entry(qsTr("Local workspace root"),"local_root","folder",!ctx.busy),
            ctx.entry(qsTr("Edit workspace"),"edit_workspace","edit",!ctx.busy && Boolean(ctx.state.workspace)),
            ctx.entry(qsTr("Workspace setup"),"workspace_setup","settings",!ctx.busy),
            ctx.entry(qsTr("Next workspaces"),"next_workspaces","chevron-right",!ctx.busy && Boolean(ctx.state.workspaces_after)),
            ctx.entry(qsTr("Next streams"),"next_streams","chevron-right",!ctx.busy && Boolean(ctx.state.streams_after)),
            ctx.entry(qsTr("Next depots"),"next_depots","chevron-right",!ctx.busy && Boolean(ctx.state.depots_after)),
            ctx.entry(qsTr("Help"),"help","help",true)]
        if (kind === "changes_background") return [
            ctx.entry(qsTr("New changelist"),"create_change","add",!ctx.busy && Boolean(ctx.state.workspace)),
            ctx.entry(qsTr("Refresh"),"refresh","refresh",!ctx.busy)]
        if (kind === "change") return [
            ctx.entry(qsTr("View changelist"),"change_details","info",Boolean(ctx.state.change.code) && !ctx.busy),
            ctx.entry(qsTr("Submit"),"submit","publish",ctx.editable),
            ...(ctx.state.change.state==="submitted" && ctx.state.change.owner===ctx.controller.current_user && (ctx.state.change.task_status_updates || []).length ? [ctx.entry(qsTr("Update linked task statuses"),"submit_task_status","task",!ctx.busy)] : []),
            {title:qsTr("Shelving"),icon:"archive",children:[
                ctx.entry(qsTr("Shelve"),"shelve","archive",ctx.editable),
                ctx.entry(qsTr("Shelve and revert"),"shelve_revert","undo",ctx.editable),
                ctx.entry(qsTr("Compare pending with shelf"),"compare_shelf","compare",ctx.editable),
                ctx.entry(qsTr("Unshelve"),"unshelve_begin","archive",ctx.editable || !ctx.busy && ctx.state.change.state==="shelved")]},
            {title:qsTr("Changelist edits"),icon:"edit",children:[
                ctx.entry(qsTr("Move all files…"),"move_all_files","swap-horizontal",ctx.editable && ctx.state.change.opened_files!==0),
                ctx.entry(qsTr("Rebase / resolve"),"rebase_begin","source-branch",ctx.editable),
                ctx.entry(qsTr("Merge stream"),"merge_begin","source-branch",ctx.editable),
                ctx.entry(qsTr("Resume upload"),"resume_upload","cloud-upload",!ctx.busy && ctx.pending && ctx.state.change.owner===ctx.controller.current_user && ctx.state.change.workspace===ctx.state.workspace && !ctx.integrating),
                ctx.entry(qsTr("Index pending metadata"),"index_change","refresh",!ctx.busy && ctx.pending && ctx.state.change.owner===ctx.controller.current_user)]},
            {title:qsTr("Ownership"),icon:"account",children:[
                ctx.entry(qsTr("Offer changelist ownership"),"offer_change","account",ctx.editable),
                ctx.entry(qsTr("Accept changelist ownership"),"accept_change","check",!ctx.busy && ctx.state.change.handoff?.recipient===ctx.controller.current_user)]},
            {title:qsTr("Copy"),icon:"copy",children:[
                ctx.entry(qsTr("Copy changelist number"),"copy_change_code","copy",Boolean(ctx.state.change.code)),
                ctx.entry(qsTr("Copy changelist link"),"copy_change_link","link",Boolean(ctx.state.change.code))]},
            ctx.entry(qsTr("Revert unchanged files"),"revert_unchanged_change","undo",ctx.editable),
            ctx.entry(qsTr("Revert changelist"),"revert","undo",ctx.editable),
            ctx.entry(qsTr("Delete changelist / shelf…"),"delete_change","delete",!ctx.busy && deletionTargets(ctx).length>0)]
        if (kind === "files") return [
            ctx.entry(qsTr("Open local file"),"open_local","file",selected),
            ctx.entry(qsTr("Show in Explorer"),"reveal_local","folder-open",selected),
            ctx.entry(qsTr("Revert"),"revert_files","undo",selected && !ctx.busy),
            {title:qsTr("Inspect / revisions"),icon:"history",children:[
                ctx.entry(qsTr("Reveal in other tree"),"reveal_tree","account-tree",selected && ctx.state.selected.length===1),
                ctx.entry(qsTr("Get latest selected files"),"sync_selected","cloud-download",selected),
                ctx.entry(qsTr("Get Revision…"),"revision_selected","history",selected),
                ctx.entry(qsTr("Diff local against Head"),"diff_local","compare",selected && ctx.state.selected.length===1),
                ctx.entry(qsTr("Diff local against Have"),"diff_have","compare",selected && ctx.state.selected.length===1),
                ctx.entry(qsTr("Diff pending against shelf"),"diff_shelf","compare",ctx.editable && selected && ctx.state.selected.length===1),
                ctx.entry(qsTr("File history"),"file_history","history",selected)]},
            {title:qsTr("Checkout"),icon:"lock-open-variant",children:[
                ctx.entry(qsTr("Ordinary checkout"),"checkout_ordinary","lock-open-variant",selected),
                ctx.entry(qsTr("Exclusive checkout"),"checkout_exclusive","lock",selected)]},
            {title:qsTr("Changelist edits"),icon:"edit",children:[
                ctx.entry(qsTr("Rename file"),"rename_file","edit",ctx.editable && selected && ctx.state.selected.length===1),
                ctx.entry(qsTr("Move files"),"move_files","swap-horizontal",ctx.editable && selected && ctx.state.view==="change"),
                ctx.entry(qsTr("Remove selected from changelist"),"remove_files","close",ctx.editable && selected && ctx.state.view==="change"),
                ctx.entry(qsTr("Revert unchanged selected files"),"revert_unchanged","undo",ctx.editable && selected)]},
            {title:qsTr("Delete"),icon:"delete",children:[
                ctx.entry(qsTr("Mark for depot deletion"),"mark_delete","delete",selected),
                ctx.entry(qsTr("Move local copies to Trash"),"delete_local","delete",selected)]},
            {title:qsTr("Shelving"),icon:"archive",children:[
                ctx.entry(qsTr("Shelve selected files"),"shelve_selected","archive",ctx.editable && selected && ctx.state.view==="change"),
                ctx.entry(qsTr("Replace selected files in shelf"),"replace_shelf","archive",ctx.editable && selected && ctx.state.view==="change"),
                ctx.entry(qsTr("Delete selected shelved files"),"delete_shelf_files","delete",selected && ctx.state.change.state==="shelved" && ctx.state.change.owner===ctx.controller.current_user),
                ctx.entry(qsTr("Apply selected local changes…"),"apply_reconcile","check",selected && ctx.state.view==="local"),
                ctx.entry(qsTr("Stage selected deletions"),"stage_deletions","delete",ctx.editable && selected && ctx.state.view==="local")]},
            {title:qsTr("Copy"),icon:"copy",children:[ctx.entry(qsTr("Depot path"),"copy_depot","copy",selected),ctx.entry(qsTr("Local path"),"copy_local","copy",selected)]},
            ctx.entry(qsTr("Columns"),"columns","table",!ctx.busy)]
        if (ctx.detailsView === "history") return [
            ctx.entry(qsTr("Compare selected revisions"),"diff_revisions","compare",ctx.state.selection_scope==="history" && ctx.state.selection_ids.length===2),
            ctx.entry(qsTr("Get this revision"),"revision_history","cloud-download",!ctx.busy && Boolean(ctx.detail.code)),
            ctx.entry(qsTr("Preview revision"),"preview_revision","visibility",!ctx.busy && Boolean(ctx.detail.code) && !ctx.detail.deleted),
            ctx.entry(qsTr("Save revision"),"save_revision","download",!ctx.busy && Boolean(ctx.detail.code) && !ctx.detail.deleted),
            ctx.entry(qsTr("Restore revision in changelist"),"restore_revision","undo",!ctx.busy && Boolean(ctx.detail.code) && !ctx.detail.deleted && ctx.state.selection_ids.length<=1)]
        if (ctx.detailsView === "tasks") return [
            ctx.entry(qsTr("Resume waiting for batch"),"bulk_resume","play-arrow",!ctx.busy && ctx.detail.kind==="mutation" && ["queued","running"].indexOf(ctx.detail.state)>=0),
            ctx.entry(qsTr("Transfer status"),"transfer_status","refresh",!ctx.busy && Boolean(ctx.detail.task)),
            ctx.entry(qsTr("Clear completed transfers"),"clear_completed_tasks","close",!ctx.busy),
            ctx.entry(qsTr("Cancel transfer"),"transfer_cancel","cancel",!ctx.busy && Boolean(ctx.detail.task) && ["ready","submitted","complete","cancelled","expired"].indexOf(ctx.detail.state) < 0),
            ctx.entry(qsTr("Next transfers"),"next_tasks","chevron-right",!ctx.busy && Boolean(ctx.state.tasks_after))]
        return [
            {title:qsTr("Preview"),icon:"visibility",children:["base","ours","theirs"].map(side => ctx.entry(side === "base" ? qsTr("Preview base") : side === "ours" ? qsTr("Preview ours") : qsTr("Preview theirs"),"preview_"+side,"visibility",!ctx.busy && ctx.integrating && Boolean(ctx.detail[side]) && !ctx.detail[side].deleted))},
            ctx.entry(qsTr("Compare Base / Ours"),"diff_base_ours","compare",ctx.integrating && !ctx.showResolved && Boolean(ctx.detail.path)),
            ctx.entry(qsTr("Compare Ours / Theirs"),"diff_ours_theirs","compare",ctx.integrating && !ctx.showResolved && Boolean(ctx.detail.path)),
            ctx.entry(qsTr("Undo resolution"),"undo_resolution","undo",!ctx.busy && ctx.integrating && ctx.showResolved && Boolean(ctx.detail.path)),
            ctx.entry(qsTr("Use ours"),"ours","check",!ctx.busy && ctx.integrating && !ctx.showResolved && Boolean(ctx.detail.path)),
            ctx.entry(qsTr("Use theirs"),"theirs","check",!ctx.busy && ctx.integrating && !ctx.showResolved && Boolean(ctx.detail.path)),
            ctx.entry(qsTr("Upload merged file"),"merged_file","upload",!ctx.busy && ctx.integrating && !ctx.showResolved && Boolean(ctx.detail.path) && !(ctx.detail.rename_partner && ctx.detail.ours?.deleted)),
            ctx.entry(qsTr("Continue integration"),"continue_integration","play-arrow",!ctx.busy && ctx.integrating),
            ctx.entry(qsTr("Finish integration"),"integration_finish","check",!ctx.busy && ctx.integrating && ctx.state.conflicts.length === 0 && Boolean(ctx.state.change.integration?.complete)),
            ctx.entry(qsTr("Cancel integration"),"integration_cancel","cancel",!ctx.busy && ctx.integrating),
            ctx.entry(qsTr("Next conflicts"),"next_conflicts","chevron-right",!ctx.busy && Boolean(ctx.state.conflicts_after))]
    }

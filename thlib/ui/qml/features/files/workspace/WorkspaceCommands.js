.pragma library
.import "../../../FileWorkspaceMenus.js" as Menus
.import "../../../tactic_frame/features/files/workspace/presentation.mjs" as Presentation

function command(ctx, name, ui) {
    if (name === 'preview_revision' && ctx.activeTab.kind === 'history') {
        ui.historyView.previewSelected();
        return;
    }
    if (name === 'submit') {
        ui.submitDialog.open();
        ctx.act('review_change', { operation: 'submit' });
        return;
    }
    if (name === 'revert' || name === 'revert_files') {
        ctx.openRevert(name);
        return;
    }
    if (
        [
            'revision_workspace',
            'revision_folder',
            'revision_selected',
            'revision_history'
        ].indexOf(name) >= 0
    ) {
        ui.revisionDialog.scope =
            name === 'revision_folder'
                ? 'folder'
                : name === 'revision_workspace'
                  ? 'workspace'
                  : 'selection';
        ui.revisionDialog.selector =
            name === 'revision_history' ? 'file_revision' : '';
        ui.revisionDialog.value =
            name === 'revision_history' ? String(ctx.detail.number) : '';
        ui.revisionDialog.force = false;
        ui.revisionDialog.request =
            name === 'revision_history'
                ? {
                      history: {
                          path: ctx.workspaceState.history_path,
                          stream: ctx.workspaceState.history_stream
                      }
                  }
                : {};
        const row = ctx.workspaceState.context_row;
        ui.revisionDialog.target =
            name === 'revision_history'
                ? ctx.workspaceState.history_path
                : ui.revisionDialog.scope === 'workspace'
                  ? ctx.workspaceState.workspace
                  : ui.revisionDialog.scope === 'folder'
                    ? row.directory || row.name || ctx.workspaceState.workspace
                    : qsTr('Selected files: %1').arg(
                          ctx.workspaceState.selected.length
                      );
        ui.revisionDialog.open();
        return;
    }
    if (name.indexOf('view_') === 0) {
        ctx.controller.open_view(name.slice(5));
        return;
    }
    if (name === 'depot_tree' || name === 'workspace_tree') {
        ctx.set('tree_view', name === 'depot_tree' ? 'depot' : 'workspace');
        return;
    }
    if (name === 'new_tab' || name === 'edit_tab') {
        ctx.editTab(name === 'new_tab');
        return;
    }
    if (name === 'close_tab') {
        ctx.controller.close_tab(ctx.workspaceState.active_tab);
        return;
    }
    if (name === 'tab_left' || name === 'tab_right') {
        ctx.controller.move_tab(name === 'tab_left' ? -1 : 1);
        return;
    }
    if (name === 'copy_change_code') {
        ctx.controller.copy_change_code();
        return;
    }
    if (name === 'copy_change_link') {
        ctx.controller.copy_change_link();
        return;
    }
    if (name === 'goto_change') {
        ctx.editKind = name;
        ctx.draft = '';
        ui.editor.open();
        return;
    }
    if (name.indexOf('copy_') === 0) {
        ctx.controller.copy_selection(name.slice(5));
        return;
    }
    if (name === 'move_all_files') {
        ctx.movingWholeChange = true;
        ctx.act('select_query', { whole_change: true });
        return;
    }
    if (name === 'delete_change') {
        const targets = Menus.deletionTargets(ctx);
        if (
            targets.length === 1 &&
            targets[0].state === 'pending' &&
            targets[0].opened_files !== 0
        ) {
            ui.nonemptyDelete.open();
            return;
        }
        ui.confirmation.deleteTargets = targets.map((row) => ({
            change: row.code,
            edit_revision: row.edit_revision,
            number: row.number
        }));
    }
    if (
        [
            'mark_delete',
            'delete_local',
            'delete_change',
            'delete_shelf_files',
            'remove_files'
        ].indexOf(name) >= 0
    ) {
        ctx.confirmationAction = name;
        ui.confirmation.open();
        return;
    }
    if (
        name === 'query_checkout_ordinary' ||
        name === 'query_checkout_exclusive'
    ) {
        ctx.pickTarget(
            'bulk_checkout',
            name.endsWith('exclusive') ? 'exclusive' : 'ordinary'
        );
        return;
    }
    if (name === 'query_move') {
        ctx.pickTarget('bulk_move');
        return;
    }
    if (name === 'query_revert' || name === 'query_delete') {
        ctx.confirmationAction = name;
        ui.confirmation.open();
        return;
    }
    if (name === 'bulk_resume') {
        ctx.act(name, {
            task: ctx.detail.task,
            bulk: ctx.detail.kind === 'mutation'
        });
        return;
    }
    if (name === 'apply_reconcile') {
        ctx.pickTarget('apply_reconcile');
        return;
    }
    if (name === 'undo_resolution') {
        ctx.act('undo_resolve', {
            paths: ctx.detail.rename_partner
                ? [ctx.detail.path, ctx.detail.rename_partner]
                : [ctx.detail.path]
        });
        return;
    }
    if (name === 'compare_shelf' || name === 'replace_shelf') {
        ui.shelfDialog.operation =
            name === 'replace_shelf' ? 'update_shelf' : 'compare_shelf';
        ui.shelfDialog.shelf = {};
        ctx.act('shelf_targets');
        ui.shelfDialog.open();
        return;
    }
    if (name === 'unshelve_begin') {
        if (ctx.workspaceState.change.state === 'shelved') ctx.pickTarget(name);
        else {
            ui.shelfDialog.operation = name;
            ui.shelfDialog.shelf = {};
            ctx.act('shelf_targets');
            ui.shelfDialog.open();
        }
        return;
    }
    if (name === 'rebase_begin') {
        ui.reviewDialog.operation = name;
        ui.reviewDialog.paths = [];
        ui.reviewDialog.request = {};
        ctx.act('review_change', { operation: name });
        ui.reviewDialog.open();
        return;
    }
    if (name === 'offer_change') {
        ctx.editKind = name;
        ctx.draft = '';
        ui.editor.open();
        return;
    }
    if (name === 'accept_change') {
        ctx.act(name, {
            workspace: ctx.workspaceState.workspace,
            handoff: ctx.workspaceState.change.handoff.code
        });
        return;
    }
    if (name === 'restore_revision') {
        ui.targetDialog.revision = ctx.detail;
        ctx.pickTarget('restore_file');
        return;
    }
    if (name.indexOf('filter_state/') === 0) {
        ctx.set('status_filter', name.slice(13));
        return;
    }
    if (name === 'toggle_log') {
        ctx.set('log_visible', !ctx.workspaceState.log_visible);
        return;
    }
    if (name === 'change_details') {
        ctx.controller.open_changelist_details();
        return;
    }
    if (name === 'columns') {
        ui.columnsDialog.open();
        return;
    }
    if (name === 'export_query') {
        ui.manifestSave.open();
        return;
    }
    if (name === 'diff_local' || name === 'diff_have') {
        ctx.act('compare', {
            mode: name === 'diff_have' ? 'local_have' : 'local_head'
        });
        return;
    }
    if (name === 'diff_revisions') {
        ctx.act('compare', { mode: 'revisions' });
        return;
    }
    if (name === 'diff_shelf') {
        ui.shelfDialog.operation = name;
        ui.shelfDialog.shelf = {};
        ctx.act('shelf_targets');
        ui.shelfDialog.open();
        return;
    }
    if (name === 'diff_base_ours' || name === 'diff_ours_theirs') {
        ctx.act('compare', {
            mode: 'conflict',
            path: ctx.detail.path,
            left: name === 'diff_base_ours' ? 'base' : 'ours',
            right: name === 'diff_base_ours' ? 'ours' : 'theirs'
        });
        return;
    }
    if (name === 'file_history') {
        const row = ctx.workspaceState.context_row;
        ctx.controller.open_view('history');
        return;
    }
    if (name === 'rename_file') {
        ctx.editKind = name;
        ctx.draft =
            ctx.workspaceState.context_row.source_path ||
            ctx.workspaceState.context_row.path;
        ui.editor.open();
        return;
    }
    if (['shelve', 'shelve_selected', 'shelve_revert'].indexOf(name) >= 0) {
        ui.reviewDialog.operation = name;
        ui.reviewDialog.paths =
            name === 'shelve_selected'
                ? ctx.workspaceState.selected.slice()
                : [];
        ui.reviewDialog.request = {};
        ctx.act(
            'review_change',
            Object.assign(
                { operation: name },
                ui.reviewDialog.paths.length
                    ? { paths: ui.reviewDialog.paths }
                    : {}
            )
        );
        ui.reviewDialog.open();
        return;
    }
    if (name === 'move_files') ctx.pickTarget('move_files');
    else if (
        ['unshelve_begin', 'merge_begin', 'local_root'].indexOf(name) >= 0
    ) {
        ctx.editKind = name;
        ctx.draft = name === 'local_root' ? ctx.workspaceState.root : '';
        ui.editor.open();
    } else if (name === 'workspace_setup') {
        ctx.set('editing_workspace', false);
        ctx.set('setup', true);
    } else if (name === 'choose_folder') ui.folderDialog.open();
    else if (name === 'checkout_ordinary' || name === 'checkout_exclusive')
        ctx.pickTarget('checkout', name.slice(9));
    else if (name === 'help') ui.windowModel.open_help('file_workspace');
    else if (name === 'save_revision') {
        ctx.downloadValues = {
            path: ctx.detail.path,
            stream: ctx.detail.stream,
            published_change: ctx.detail.change
        };
        ui.saveDialog.open();
    } else if (name === 'merged_file') {
        ctx.mergePath = ctx.detail.path;
        ui.mergedDialog.open();
    } else if (name === 'ours' || name === 'theirs') {
        const selected =
            ctx.workspaceState.conflict_selected.length && !ctx.showResolved
                ? ctx.workspaceState.conflict_selected
                : [ctx.detail.path];
        const paths = new Set(selected);
        for (const path of selected) {
            const row = ctx.workspaceState.conflicts.find(
                (row) => row.path === path
            );
            if (row?.rename_partner) paths.add(row.rename_partner);
        }
        ctx.act('resolve', {
            resolutions: [...paths].map((path) => ({
                path: path,
                choice: name
            }))
        });
    } else if (name.indexOf('preview_') === 0) {
        const side = name.slice(8);
        ctx.act(
            'preview',
            side === 'revision'
                ? {
                      path: ctx.detail.path,
                      stream: ctx.detail.stream,
                      published_change: ctx.detail.change
                  }
                : Object.assign(ctx.integration(), {
                      path: ctx.detail.path,
                      conflict_side: side
                  })
        );
    } else if (name === 'transfer_status' || name === 'transfer_cancel')
        ctx.act(name, {
            task: ctx.detail.task,
            bulk: ctx.detail.kind === 'mutation'
        });
    else ctx.act(name);
}

function fileKey(ctx, event, scope, views, contain) {
    if (
        event.key === Qt.Key_A &&
        event.modifiers & Qt.ControlModifier &&
        event.modifiers & Qt.ShiftModifier
    ) {
        ctx.act('select_query');
        event.accepted = true;
        return;
    }
    if (event.key === Qt.Key_A && event.modifiers & Qt.ControlModifier) {
        ctx.controller.select_loaded(scope, true);
        event.accepted = true;
    } else if (event.key === Qt.Key_Escape) {
        ctx.controller.select_loaded(scope, false);
        event.accepted = true;
    } else if (event.key === Qt.Key_Up || event.key === Qt.Key_Down) {
        ctx.controller.step_selection(
            scope,
            event.key === Qt.Key_Up ? -1 : 1,
            event.modifiers
        );
        const rows =
            scope === 'files'
                ? ctx.workspaceState.rows.filter((row) =>
                      Presentation.matches(
                          row,
                          ctx.workspaceState.name_filter,
                          ctx.workspaceState.status_filter
                      )
                  )
                : ctx.workspaceState.history;
        const model =
            scope === 'changes'
                ? ctx.controller.change_model
                : scope === 'depot'
                  ? ctx.controller.depot_model
                  : scope === 'workspace'
                    ? ctx.controller.workspace_model
                    : null;
        let index = -1;
        if (model) {
            for (let i = 0; i < model.count(); i++) {
                if (model.get(i).id === ctx.workspaceState.focus_id) {
                    index = i;
                    break;
                }
            }
        } else
            index = rows.findIndex(
                (row) =>
                    (scope === 'files'
                        ? ctx.controller.row_identity(row)
                        : row.id || row.code) === ctx.workspaceState.focus_id
            );
        if (index >= 0) {
            views[scope].currentIndex = index;
            views[scope].positionViewAtIndex(index, contain);
        }
        event.accepted = true;
    } else if (event.key === Qt.Key_Delete) {
        const headers =
            scope === 'changes' &&
            Object.values(ctx.workspaceState.selection_records || {}).length >
                0 &&
            Object.values(ctx.workspaceState.selection_records).every(
                (row) => row.kind === 'change'
            );
        const action = headers ? 'delete_change' : 'mark_delete';
        if (!Menus.selectionReason(ctx, action)) ctx.command(action);
        event.accepted = true;
    } else if (event.key === Qt.Key_C && event.modifiers & Qt.ControlModifier) {
        ctx.controller.copy_selection('depot');
        event.accepted = true;
    }
}

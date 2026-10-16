// MenuRegistry supplies native actions, including runtime replacements/extensions.
// Stream supplies the independent shipped catalog. Owners execute commands.
export function compose(actions, context) {
    const result = [];
    let separator = false;
    const blocked = {
        open_configuration: context.busy || context.openingLink,
        show_administration: context.busy,
        save_preferences: context.reloadingCache,
        reload_cache: context.busy || context.reloadingCache,
        apply_view_to_all_tabs: context.hasSearch === false,
        open_script_editor: context.scriptLoading,
        ping_now: context.pingBusy,
        sign_out: context.busy
    };
    for (const record of actions || []) {
        if (
            record.visible === false ||
            (record.platform && record.platform !== context.platform) ||
            (record.admin && !context.canAdminister) ||
            (record.desktop && context.compact) ||
            (record.phone && !context.compact)
        )
            continue;
        if (record.separator) {
            separator = result.length > 0;
            continue;
        }
        const command = record.command || '';
        if (command.indexOf('updates_') === 0 && context.updateMode !== 'poll')
            continue;
        if (
            command === 'schema_notice' &&
            context.messagesInitialized !== false
        )
            continue;
        const action = Object.assign({}, record, {
            enabled: record.enabled !== false && !blocked[command]
        });
        if (command === 'show_messages')
            action.badgeCount = context.unread || 0;
        if (command === 'show_commit_queue' && context.fileProject)
            action.title = 'Changelists';
        if (command === 'update_summary')
            action.status =
                context.updateMode === 'sse'
                    ? 'Server push (SSE)'
                    : 'One batched server request';
        if (command.indexOf('update_mode_') === 0)
            action.checked = context.updateMode === command.slice(12);
        if (command.indexOf('updates_') === 0)
            action.checked = Number(command.slice(8)) === context.pollInterval;
        if (separator) result.push({ separator: true });
        separator = false;
        result.push(action);
    }
    return result;
}

// Legacy scripts return commands; each engine opens its existing feature owner.
export function route(command) {
    if (['refresh', 'message', 'log', 'url'].includes(command.type)) {
        return command;
    }
    if (command.type !== 'open') {
        throw new Error('Unsupported table action: ' + command.type);
    }
    const owners = {
        'tactic.ui.panel.EditWdg': 'edit',
        'pyasm.widget.DiscussionWdg': 'notes',
        'tactic.ui.widget.DiscussionWdg': 'notes',
        'tactic.ui.tools.ScheduleUserToolWdg': 'schedule',
        'tactic.ui.startup.GroupAssignWdg': 'users',
        'tactic.ui.startup.UserAssignWdg': 'groups',
        'tactic.ui.startup.GroupSummaryWdg': 'security-summary',
        'tactic.ui.tools.PipelineToolWdg': 'workflow',
        'tactic.ui.tools.SchemaToolWdg': 'schema',
        'tactic.ui.app.ShelfEditWdg': 'script',
        'tactic.ui.panel.CustomLayoutWdg': 'custom-layout'
    };
    const owner = owners[command.className];
    if (!owner) {
        throw new Error('Unsupported table window: ' + command.className);
    }
    return Object.assign({}, command, { type: owner });
}

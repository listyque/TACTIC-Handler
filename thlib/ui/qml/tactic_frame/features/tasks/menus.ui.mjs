export function column(model) {
    const source = model.column;
    if (!source) return [];
    const sort = source.sortMode || source.sort,
        group = source.groupMode || source.group;
    const actions = [
        { header: true, title: model.label || source.label, translate: false }
    ];
    if (sort)
        actions.push(
            {
                title: 'Sort ascending',
                icon: 'sort-ascending',
                command: 'sort:ascending',
                checked: model.sort === sort && !model.descending,
                enabled: !model.busy
            },
            {
                title: 'Sort descending',
                icon: 'sort-descending',
                command: 'sort:descending',
                checked: model.sort === sort && model.descending,
                enabled: !model.busy
            }
        );
    if (group)
        actions.push({
            title: 'Group by column',
            icon: 'group-items',
            command: 'group',
            checked: model.group === group,
            enabled: !model.busy
        });
    actions.push({
        title: 'No grouping',
        icon: 'ungroup-items',
        command: 'ungroup',
        enabled: !model.busy && model.group !== 'none'
    });
    actions.push(
        { separator: true },
        {
            title: 'Hide column',
            icon: 'visibility-off',
            command: 'hide',
            enabled: !source.required && source.key !== 'object'
        },
        { title: 'Task columns', icon: 'view-column', command: 'columns' }
    );
    if (model.configure)
        actions.push({
            title: 'Configure columns',
            icon: 'settings',
            command: 'configure'
        });
    return actions;
}

export function row(model) {
    const actions = [
        {
            title: model.recordEditor ? 'Edit sObject' : 'Edit task',
            icon: 'edit',
            command: 'edit',
            enabled: !model.busy && !model.deleting
        }
    ];
    if (model.inspector)
        actions.push({
            title: 'Task Inspector',
            icon: 'assignment',
            command: 'inspect',
            enabled: model.hasTask && !model.deleting
        });
    if (model.timesheet)
        actions.push({
            title: 'Task timesheet',
            icon: 'schedule',
            command: 'timesheet',
            enabled: model.hasTask && !model.deleting
        });
    actions.push({
        title: 'Open object',
        icon: 'open-in-new',
        command: 'open',
        enabled: !model.busy && !model.pending && model.hasParent !== false
    });
    if (model.notes)
        actions.push({
            title: 'Open notes',
            icon: 'comment',
            command: 'notes',
            enabled: !model.busy && !model.pending
        });
    if (model.dirty)
        actions.push({
            title: 'Discard task changes',
            icon: 'undo',
            command: 'discard',
            enabled: !model.busy
        });
    if (model.conflict)
        actions.push(
            {
                title: 'Use server version',
                icon: 'cloud-download',
                command: 'server-version'
            },
            {
                title: 'Keep my changes',
                icon: 'edit-note',
                command: 'keep-mine'
            }
        );
    actions.push(
        { separator: true },
        {
            title: 'Delete task',
            icon: 'delete',
            command: 'delete',
            enabled: !model.busy && !model.pending && !model.creating
        }
    );
    if (model.checked)
        actions.push({
            title: 'Delete selected tasks',
            icon: 'delete-sweep',
            command: 'delete-checked',
            enabled: !model.busy && !model.pending
        });
    return actions;
}

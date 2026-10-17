import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { captionHeight } from '../../controls/forms/sections.ui.mjs';

export function context(model, width, language) {
    const tr = (text) => translate(text, language),
        narrow = width < 430,
        height = narrow ? 86 : 46;
    const processWidth = Math.max(112, Math.min(166, width * 0.34)),
        taskWidth = model.taskCount > 1 ? 35 : 0,
        actionsWidth = model.hasActions ? 35 : 0,
        refreshWidth = model.phone ? 0 : 35;
    const right =
        processWidth +
        taskWidth +
        actionsWidth +
        refreshWidth +
        (model.phone ? 35 : 0) +
        6;
    const titleWidth = Math.max(0, width - 84 - (narrow ? 6 : right + 7));
    const nodes = [
        node('Box', 'taskInspectorContext', rect(0, 0, width, height), {
            background: 'surfaceContainerHigh'
        }),
        button(
            'taskInspectorToggle',
            rect(7, 11, 24, 24),
            tr(
                model.phone
                    ? 'Back'
                    : model.expanded
                      ? 'Collapse Task Inspector'
                      : 'Expand Task Inspector'
            ),
            model.phone
                ? 'arrow-back'
                : model.expanded
                  ? 'expand-more'
                  : 'chevron-right',
            { type: model.phone ? 'back' : 'toggle' },
            !model.busy || model.phone,
            { iconOnly: true, iconAction: true, iconSize: 13 }
        ),
        node('Preview', 'taskInspectorObjectPreview', rect(38, 7, 32, 32), {
            source: model.previewUrl || '',
            initials: model.initials || '',
            icon: 'sobject',
            round: true,
            outlined: true,
            accent: 'action'
        }),
        node('Action', 'taskInspectorObject', rect(77, 5, titleWidth, 36), {
            text: tr('Object preview'),
            normalColor: 'transparent',
            radius: 0,
            action: { type: 'preview' },
            children: [
                label(
                    'taskInspectorObjectTitle',
                    rect(0, 0, titleWidth, 19),
                    model.title || tr('Selected object'),
                    { fontRole: 'secondary', weight: 600 }
                ),
                label(
                    'taskInspectorObjectType',
                    rect(0, 20, titleWidth, 15),
                    model.typeTitle || 'sObject',
                    { fontRole: 'caption', color: 'secondaryText' }
                )
            ]
        })
    ];
    let x = narrow ? Math.max(7, width - right) : width - right,
        y = narrow ? 48 : 9;
    nodes.push(
        node(
            'Box',
            'taskInspectorProcessSurface',
            rect(x, y, processWidth, 28),
            {
                background: 'panelDeep',
                border: 'outlineVariant',
                radius: 8,
                children: [
                    node(
                        'Action',
                        'taskInspectorProcess',
                        rect(0, 0, processWidth, 28),
                        {
                            text: tr('Process'),
                            normalColor: 'transparent',
                            radius: 8,
                            enabled: !model.busy,
                            action: { type: 'process-menu' },
                            children: [
                                node(
                                    model.isProgress ? 'Icon' : 'Box',
                                    'processAccent',
                                    rect(
                                        10,
                                        model.isProgress ? 6 : 10,
                                        model.isProgress ? 15 : 8,
                                        model.isProgress ? 15 : 8
                                    ),
                                    {
                                        icon: model.isProgress
                                            ? 'donut-small'
                                            : undefined,
                                        color: model.processColor || 'action',
                                        background:
                                            model.processColor || 'action',
                                        radius: 4
                                    }
                                ),
                                label(
                                    'processLabel',
                                    rect(
                                        32,
                                        4,
                                        Math.max(0, processWidth - 57),
                                        20
                                    ),
                                    model.processLabel || model.process || '',
                                    { fontRole: 'secondary', weight: 600 }
                                )
                            ]
                        }
                    ),
                    node(
                        'Icon',
                        'processIndicator',
                        rect(processWidth - 21, 7, 15, 15),
                        { icon: 'expand-more', color: 'secondaryText' }
                    )
                ]
            }
        )
    );
    x += processWidth + 7;
    if (model.taskCount > 1) {
        nodes.push(
            button(
                'taskInspectorTaskSwitchButton',
                rect(x, y, 28, 28),
                tr('Switch task for this process'),
                'swap-horiz',
                { type: 'task-menu' },
                !model.busy,
                { iconOnly: true, iconAction: true, iconSize: 16 }
            )
        );
        x += 35;
    }
    if (model.hasActions) {
        nodes.push(
            button(
                'taskInspectorActions',
                rect(x, y, 28, 28),
                tr('Task actions'),
                'more',
                { type: 'task-actions' },
                !model.busy,
                { iconOnly: true, iconAction: true, iconSize: 16 }
            )
        );
        x += 35;
    }
    if (model.phone)
        nodes.push(
            button(
                'taskInspectorHelp',
                rect(x, y, 28, 28),
                tr('Help'),
                'help',
                { type: 'help' },
                true,
                { iconOnly: true, iconAction: true, iconSize: 16 }
            )
        );
    if (!model.phone)
        nodes.push(
            button(
                'taskInspectorRefresh',
                rect(x, y, 28, 28),
                tr('Refresh notes and task'),
                'refresh',
                { type: 'refresh' },
                !model.busy,
                { iconOnly: true, iconAction: true, iconSize: 16 }
            )
        );
    return { height, nodes };
}

export function quick(model, width, language) {
    const tr = (text) => translate(text, language),
        nodes = [],
        actions = [];
    if (model.hasTask)
        actions.push(['edit', 'Edit task in full editor', 'edit']);
    if (model.canCreate)
        actions.push(['create', 'Create another task in full editor', 'add']);
    if (model.dirty) actions.push(['discard', 'Discard task changes', 'undo']);
    if (model.canEdit && (model.dirty || !model.hasTask))
        actions.push([
            'save',
            model.hasTask ? 'Save task changes' : 'Create task',
            'save'
        ]);
    const titleWidth = Math.max(
        0,
        width - 18 - (actions.length ? actions.length * 35 : 0)
    );
    nodes.push(
        node('Box', 'taskInspectorTaskSurface', rect(0, 0, width, 148), {
            radiusRole: 'itemRadius',
            background: 'panelDeep',
            border: 'outlineVariant'
        }),
        label(
            'taskInspectorTaskTitle',
            rect(10, 7, titleWidth, 17),
            model.title ||
                translate('No task for {process}', language, {
                    process: model.processLabel || ''
                }),
            { fontRole: 'body', weight: 600 }
        ),
        label(
            'taskInspectorTaskSubtitle',
            rect(10, 25, titleWidth, 15),
            model.assignedLabel || '',
            { fontRole: 'caption', color: 'secondaryText' }
        )
    );
    actions.forEach(([type, text, icon], i) =>
        nodes.push(
            button(
                'taskInspector_' + type,
                rect(
                    width -
                        8 -
                        actions.length * 28 -
                        (actions.length - 1) * 7 +
                        i * 35,
                    9,
                    28,
                    28
                ),
                tr(text),
                icon,
                { type },
                !model.busy &&
                    (!['edit', 'create'].includes(type) || !model.dirty),
                { iconOnly: true, iconAction: true, iconSize: 16 }
            )
        )
    );
    if (!model.canEdit) return { height: 148, nodes };
    const wide = width - 18 >= 430;
    const cell = Math.max(0, (width - 25) / 2),
        base = Math.max(0, Math.floor((width - 39) / 4)),
        enabled = !model.busy;
    const firstWidth = Math.max(0, base - 26),
        dateWidth = base + 26;
    const fieldY = wide ? 64 : 41;
    if (wide) {
        nodes.find((n) => n.id === 'taskInspectorTaskTitle').y += 7;
        nodes.find((n) => n.id === 'taskInspectorTaskSubtitle').y += 7;
        nodes
            .filter((n) => n.id.startsWith('taskInspector_'))
            .forEach((n) => (n.y = 14));
    }
    const statuses = (model.statuses || []).map((row) =>
        Object.assign({}, row, {
            label: row.label || row.value || tr('Select status'),
            disabled: row.disabled || (row.value === '' && !row.label)
        })
    );
    if (!statuses.some((row) => row.value === ''))
        statuses.unshift({
            value: '',
            label: tr('Select status'),
            disabled: true
        });
    nodes.push(
        node(
            'View',
            'taskInspectorStatusField',
            rect(10, fieldY, wide ? firstWidth : cell, 32),
            {
                view: 'status',
                label: tr('Status'),
                value: model.status || '',
                options: statuses,
                actionField: true,
                swatchMode: 'color',
                enabled: enabled && model.statusEditable !== false,
                action: { type: 'change', field: 'status' }
            }
        ),
        node(
            'UserChoice',
            'taskInspectorAssigneeField',
            rect(
                17 + (wide ? firstWidth : cell),
                fieldY,
                wide ? firstWidth : cell,
                32
            ),
            {
                label: tr('Assigned to'),
                value: model.assigned || '',
                options: model.users || [],
                actionField: true,
                enabled: enabled && model.assignedEditable !== false,
                action: { type: 'change', field: 'assigned' }
            }
        )
    );
    [
        ['start', 'Start date and time'],
        ['end', 'End date and time']
    ].forEach(([field, title], index) =>
        nodes.push(
            node(
                'DateChoice',
                'taskInspectorDate_' + field,
                rect(
                    wide
                        ? 24 + firstWidth * 2 + index * (dateWidth + 7)
                        : 10 + index * (cell + 7),
                    wide ? fieldY : 80,
                    wide
                        ? index
                            ? Math.max(
                                  0,
                                  width - 8 - (31 + firstWidth * 2 + dateWidth)
                              )
                            : dateWidth
                        : cell,
                    32
                ),
                {
                    label: tr(title),
                    text: model[field] || '',
                    includeTime: true,
                    enabled: enabled && model[field + 'Editable'] !== false,
                    error: !!model[field + 'Error'],
                    action: { type: 'change', field },
                    commitAction: { type: 'change', field }
                }
            )
        )
    );
    nodes.push(
        label(
            'taskInspectorProgressLabel',
            rect(10, 118, 55, 24),
            tr('PROGRESS'),
            { fontRole: 'caption', color: 'secondaryText' }
        ),
        node(
            'View',
            'taskInspectorProgress',
            rect(75, 117, Math.max(0, width - 118), 24),
            {
                view: 'progress',
                minimum: 0,
                maximum: 100,
                step: 5,
                value: Number(model.progress || 0),
                enabled: enabled && model.progressEditable !== false,
                action: { type: 'change', field: 'progress' }
            }
        ),
        label(
            'taskInspectorProgressValue',
            rect(Math.max(0, width - 33), 118, 25, 24),
            Math.round(Number(model.progress) || 0) + '%',
            { align: 'right', fontRole: 'caption', weight: 600 }
        )
    );
    const errorHeight = model.validationError
        ? captionHeight(model.validationError, Math.max(1, width - 16)) + 12
        : 0;
    if (errorHeight) {
        nodes[0].height += errorHeight;
        nodes.push(
            label(
                'taskInspectorValidationError',
                rect(8, 148, width - 16, errorHeight - 4),
                model.validationError,
                {
                    fontRole: 'caption',
                    color: 'error',
                    wrap: true,
                    role: 'alert'
                }
            )
        );
    }
    return { height: 148 + errorHeight, nodes };
}

export function related(model, width, language) {
    const tr = (text) => translate(text, language),
        warning = model.summaryAvailable === false;
    const height = 148 + (warning ? 36 : 0);
    const nodes = [
        node('Box', 'taskInspectorRelatedTasks', rect(0, 0, width, height), {
            background: 'panelDeep',
            border: 'outlineVariant'
        }),
        node('Icon', 'relatedTasksIcon', rect(8, 12, 17, 17), {
            icon: 'donut-small',
            color: model.accent || 'action'
        }),
        label(
            'relatedTasksTitle',
            rect(32, 8, Math.max(0, width - 146), 25),
            tr('Related object tasks'),
            { fontRole: 'secondary', weight: 600 }
        ),
        node(
            'StatusChip',
            'relatedTasksCount',
            rect(Math.max(0, width - 108), 10, 100, 20),
            {
                text:
                    Number(model.approved || 0) +
                    ' / ' +
                    Number(model.total || 0),
                icon: 'donut-small',
                dense: true,
                accent: model.accent || 'action'
            }
        )
    ];
    if (warning)
        nodes.push(
            label(
                'relatedTasksWarning',
                rect(8, 39, width - 16, 30),
                tr(
                    'Task process or status pipeline is not configured for this progress count.'
                ),
                { wrap: true, fontRole: 'caption', color: 'secondaryText' }
            )
        );
    const top = 39 + (warning ? 36 : 0);
    if (model.state === 'ready' && model.count > 0)
        nodes.push(
            node(
                'List',
                'taskInspectorRelatedTaskList',
                rect(
                    8,
                    top,
                    Math.max(0, width - 16),
                    Math.max(0, height - top - 8)
                ),
                {
                    source: 'items',
                    keyField: 'key',
                    rowHeight: 31,
                    rowGap: 3,
                    label: tr('Related object tasks')
                }
            )
        );
    else {
        const states = {
            loading: 'Loading related tasks…',
            unconfigured: 'No related Search Type configured for this progress',
            missingType: 'Search Type is unavailable',
            unrelated: 'No schema relationship to this Search Type',
            error: 'Could not load related tasks. Refresh to retry.'
        };
        let text = tr(
            states[model.state] ||
                (model.objectCount
                    ? 'No tasks on related objects'
                    : 'No related objects')
        );
        if (
            ['missingType', 'unrelated'].includes(model.state) &&
            model.searchType
        )
            text += ': ' + model.searchType;
        nodes.push(
            label(
                'taskInspectorRelatedEmpty',
                rect(8, top, width - 16, height - top - 8),
                text,
                { wrap: true, fontRole: 'caption', color: 'secondaryText' }
            )
        );
    }
    return { height, nodes };
}

export function relatedRow(record, width, language) {
    const clickable = !!record.clickable,
        right = clickable ? 26 : 0;
    const nodes = [
        label(
            'relatedTaskTitle',
            rect(0, 3, Math.max(0, width - 160 - right), 22),
            (record.parentTitle || '') + ' · ' + (record.process || ''),
            { fontRole: 'caption' }
        ),
        label(
            'relatedTaskAssignee',
            rect(Math.max(0, width - 153 - right), 3, 70, 22),
            record.assigned || '',
            { fontRole: 'caption', color: 'secondaryText' }
        ),
        node(
            'StatusChip',
            'relatedTaskStatus',
            rect(Math.max(0, width - 78 - right), 4, 78, 20),
            {
                text: record.status || translate('No status', language),
                dense: true,
                accent: record.accent || 'action'
            }
        )
    ];
    if (clickable)
        nodes.push(
            button(
                'relatedTaskOpen',
                rect(width - 24, 2, 24, 24),
                translate('Open related task', language),
                'chevron-right',
                { type: 'related', index: record.index },
                !record.busy,
                { iconOnly: true, iconAction: true, iconSize: 14 }
            )
        );
    return { nodes };
}

export function workHours(model, width, language) {
    const tr = (text) => translate(text, language),
        summary = model.summary || {},
        compact = !model.expanded,
        height = compact ? 32 : 80;
    const hours = (value) => String(Math.round(Number(value || 0) * 100) / 100);
    const nodes = [
        node('Box', 'workHoursSurface', rect(0, 0, width, height), {
            background: 'surfaceContainerHigh',
            border: 'outlineVariant'
        }),
        node('Icon', 'workHoursIcon', rect(9, 8, 15, 15), {
            icon: 'schedule',
            color: Number(summary.overPlan) > 0 ? 'error' : 'action'
        }),
        label('workHoursTitle', rect(31, 3, 91, 26), tr('WORK HOURS'), {
            fontRole: 'caption',
            weight: 600
        }),
        button(
            'workHoursLog',
            rect(Math.max(0, width - 59), 3, 25, 25),
            tr('Log time'),
            'add-alarm',
            { type: 'log' },
            !model.busy && model.hasTask !== false,
            { iconOnly: true, iconAction: true, iconSize: 16 }
        ),
        button(
            'workHoursTimesheet',
            rect(Math.max(0, width - 32), 3, 25, 25),
            tr('Open timesheet'),
            'calendar-month',
            { type: 'timesheet' },
            !model.busy,
            { iconOnly: true, iconAction: true, iconSize: 16 }
        )
    ];
    if (compact || Number(summary.pending) > 0)
        nodes.push(
            label(
                'workHoursState',
                rect(128, 3, Math.max(0, width - 193), 26),
                compact
                    ? hours(summary.approved) +
                          ' / ' +
                          hours(summary.planned) +
                          ' ' +
                          tr('h')
                    : hours(summary.pending) +
                          ' ' +
                          tr('h') +
                          ' ' +
                          tr('Pending'),
                {
                    fontRole: compact ? 'secondary' : 'caption',
                    color: compact ? 'secondaryText' : 'yellow'
                }
            )
        );
    if (!compact) {
        const cell = Math.max(0, (width - 46) / 4);
        [
            ['planned', 'Planned'],
            ['approved', 'Approved'],
            ['remaining', 'Remaining'],
            ['overPlan', 'Over plan']
        ].forEach(([key, title], index) =>
            nodes.push(
                label(
                    'workHoursValue_' + key,
                    rect(9 + index * (cell + 10), 34, cell, 16),
                    hours(summary[key]) + ' ' + tr('h'),
                    {
                        align: 'center',
                        fontRole: 'secondary',
                        weight: 600,
                        color:
                            key === 'overPlan' && Number(summary[key]) > 0
                                ? 'error'
                                : 'primaryText'
                    }
                ),
                label(
                    'workHoursLabel_' + key,
                    rect(9 + index * (cell + 10), 50, cell, 14),
                    tr(title),
                    {
                        align: 'center',
                        fontRole: 'caption',
                        color: 'secondaryText'
                    }
                )
            )
        );
        const progress =
            Math.max(0, Math.min(100, Number(summary.progress) || 0)) / 100;
        nodes.push(
            node(
                'Box',
                'workHoursTrack',
                rect(9, 67, Math.max(0, width - 16), 3),
                { background: 'surfaceContainerHighest', radius: 1.5 }
            ),
            node(
                'Box',
                'workHoursProgress',
                rect(9, 67, Math.max(0, width - 16) * progress, 3),
                {
                    background:
                        Number(summary.overPlan) > 0 ? 'error' : 'action',
                    radius: 1.5
                }
            )
        );
    }
    return { height, nodes };
}

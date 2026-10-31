import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

// Task data, selection and saved column preferences stay with their existing owners.
export const metrics = {
    header: 34,
    headerGap: 3,
    row: 58,
    group: 28,
    margin: 5,
    leading: 56,
    actions: 37,
    preview: 34
};

const aliases = {
    assigned: 'assignee',
    bid_duration: 'hours',
    milestone_code: 'milestone'
};

export function group(model, width) {
    const count = String(model.count || 0),
        badgeWidth = Math.max(20, count.length * 7 + 10);
    return {
        height: metrics.group,
        nodes: [
            node('Box', 'taskGroupSurface', rect(0, 0, width, 28), {
                background: 'workspace'
            }),
            node('Icon', 'taskGroupChevron', rect(4, 7, 14, 14), {
                icon: model.collapsed ? 'chevron-right' : 'expand-more',
                color: 'secondaryText'
            }),
            node('Box', 'taskGroupColor', rect(24, 10, 8, 8), {
                background: model.color || 'action',
                radius: 4
            }),
            label(
                'taskGroupLabel',
                rect(38, 6, Math.max(0, width - 54 - badgeWidth), 16),
                String(model.label || '').toUpperCase(),
                { fontRole: 'secondary', weight: 600 }
            ),
            node(
                'Box',
                'taskGroupCountSurface',
                rect(width - 8 - badgeWidth, 5, badgeWidth, 18),
                { background: 'surfaceContainerHigh', radius: 9 }
            ),
            label(
                'taskGroupCount',
                rect(width - 8 - badgeWidth, 6.5, badgeWidth, 15),
                count,
                {
                    fontRole: 'caption',
                    color: 'secondaryText',
                    weight: 600,
                    align: 'center'
                }
            ),
            node('Action', 'taskGroupToggle', rect(0, 0, width, 28), {
                label: String(model.label || ''),
                role: 'button',
                expanded: !model.collapsed,
                action: { type: 'collapse', value: model.key }
            })
        ]
    };
}
const minimums = {
    assignee: 520,
    dates: 700,
    progress: 800,
    hours: 900,
    notes: 480,
    priority: 980,
    milestone: 1180,
    supervisor: 1380
};
const defaults = {
    object: 210,
    status: 138,
    assignee: 154,
    dates: 112,
    progress: 94,
    hours: 86,
    notes: 48,
    priority: 96,
    milestone: 132,
    supervisor: 154
};
const dense = {
    process: 92,
    status: 105,
    assignee: 118,
    dates: 90,
    progress: 72,
    hours: 72,
    notes: 38,
    priority: 80,
    milestone: 105,
    supervisor: 118
};

export function key(value) {
    return aliases[value] || value;
}

export function column(columns, name) {
    return (
        (columns || []).find((record) => key(record.key) === key(name)) || null
    );
}

export function columnWidth(columns, name, fallback, viewportWidth) {
    const record = column(columns, name);
    const configured = record ? Number(record.width || fallback) : fallback;
    const canonical = key(name);
    if (configured !== defaults[canonical]) return configured;
    if (
        viewportWidth < 420 &&
        (canonical === 'object' || canonical === 'status')
    )
        return Math.min(configured, 88);
    if (viewportWidth < 1100 && dense[canonical] !== undefined)
        return Math.min(configured, dense[canonical]);
    return configured;
}

export function visible(columns, name, width) {
    const record = column(columns, name);
    return (
        (!record || record.visible !== false) &&
        width >= (minimums[key(name)] || 0)
    );
}

export function spacing(width) {
    return width < 420 ? 3 : width < 1100 ? 5 : 7;
}

export function layout(columns, width) {
    const gap = spacing(width);
    const shown = (columns || []).filter(
        (record) =>
            key(record.key) !== 'process' && visible(columns, record.key, width)
    );
    const ordered = shown
        .map((record, index) => ({
            record,
            order: record.order === undefined ? index : Number(record.order)
        }))
        .sort((left, right) => left.order - right.order);
    const cells = ordered.map(({ record }) => {
        const canonical = key(record.key);
        const configured = columnWidth(columns, canonical, record.width, width);
        const extent =
            canonical === 'object' && configured === defaults.object
                ? Math.max(132, Math.min(configured, width * 0.25, 210))
                : configured;
        return {
            key: canonical,
            sourceKey: record.key,
            width: extent,
            label: record.label || '',
            sort: record.sort || '',
            group: record.group || ''
        };
    });
    const intrinsic =
        metrics.margin +
        metrics.leading +
        gap +
        metrics.actions +
        cells.reduce((sum, cell) => sum + cell.width + gap, 0);
    const tableWidth = Math.max(width, intrinsic);
    const flexible = cells.filter((cell) =>
        ['status', 'assignee'].includes(cell.key)
    );
    const totalFlexible = flexible.reduce((sum, cell) => sum + cell.width, 0);
    for (const cell of flexible)
        cell.width += ((tableWidth - intrinsic) * cell.width) / totalFlexible;
    let left = metrics.margin + metrics.leading + gap;
    for (const cell of cells) {
        cell.x = left;
        left += cell.width + gap;
    }
    return {
        cells,
        width: tableWidth,
        spacing: gap,
        headerHeight: metrics.header,
        rowHeight: metrics.row
    };
}

const headings = {
    object: 'OBJECT',
    status: 'STATUS',
    assignee: 'ASSIGNEE',
    dates: 'START / DEADLINE',
    progress: 'PROGRESS',
    hours: 'HOURS',
    notes: 'NOTES',
    priority: 'PRIORITY',
    milestone: 'MILESTONE',
    supervisor: 'SUPERVISOR'
};

export function header(model, geometry, language) {
    const tr = (text) => translate(text, language);
    const nodes = [
        node(
            'Box',
            'taskHeaderSurface',
            rect(0, 0, geometry.width, metrics.header),
            {
                background: 'surfaceContainer',
                radiusRole: 'itemRadius'
            }
        ),
        node('CheckBox', 'taskSelectAll', rect(33, 3, 28, 28), {
            label: tr('Select all tasks'),
            indicatorX: 4,
            checked: !!model.allSelected,
            mixed: !!model.someSelected && !model.allSelected,
            enabled: !model.busy,
            action: { type: 'select-all' }
        }),
        button(
            'taskTableColumnsButton',
            rect(geometry.width - 35, 3, 28, 28),
            tr('Task columns'),
            'view-column',
            { type: 'columns' },
            true,
            {
                iconOnly: true,
                iconAction: true,
                iconSize: 16,
                pressAction: { type: 'columns-press' }
            }
        )
    ];
    for (const cell of geometry.cells) {
        nodes.push(
            label(
                {
                    status: 'taskStatusHeader',
                    assignee: 'taskAssigneeHeader',
                    progress: 'taskProgressHeader'
                }[cell.key] || 'taskHeader_' + cell.key,
                rect(cell.x, 7, cell.width, 20),
                tr(headings[cell.key] || cell.label.toUpperCase()),
                {
                    fontRole: 'caption',
                    weight: 600,
                    color: 'secondaryText',
                    align: cell.key === 'notes' ? 'center' : 'left'
                }
            )
        );
        // Engine input ports add sorting, context menus and resize handles to these bounds.
        nodes.push(
            node(
                'View',
                'taskHeaderInput_' + cell.key,
                rect(cell.x, 0, cell.width, metrics.header),
                { view: 'header_' + cell.key, column: cell }
            )
        );
    }
    return { nodes, height: metrics.header };
}

export function row(model, geometry, language) {
    const tr = (text) => translate(text, language);
    const width = geometry.width,
        height = metrics.row;
    const nodes = [
        node(
            'Box',
            'taskRowSurface_' + (model.code || ''),
            rect(0, 0, width, height),
            {
                background: model.active
                    ? 'contentSelection'
                    : model.checked
                      ? 'secondaryContainer'
                      : model.creating
                        ? 'panelDeep'
                        : model.hovered
                          ? 'rowHover'
                          : 'surfaceContainerLow',
                opacity: model.checked && !model.active ? 0.72 : 1,
                radius: 0
            }
        ),
        node('Box', 'taskRowRail', rect(0, 7, 3, height - 14), {
            background: model.processColor || 'action',
            radius: 1.5,
            opacity: model.active || model.expanded ? 1 : 0.82
        }),
        button(
            'taskDetailsExpander_' + (model.code || ''),
            rect(5, 15, 28, 28),
            tr(
                model.expanded ? 'Collapse task details' : 'Expand task details'
            ),
            model.expanded ? 'chevron-down' : 'chevron-right',
            { type: 'expand' },
            !model.busy,
            { iconOnly: true, iconAction: true, iconSize: 16 }
        ),
        node('CheckBox', 'taskRowCheck', rect(33, 15, 28, 28), {
            label: model.title + ': ' + model.processLabel,
            indicatorX: 4,
            checked: !!model.checked,
            enabled: !model.busy,
            action: { type: 'select' }
        })
    ];
    if (!model.expanded)
        nodes.push(
            node('Box', 'taskRowSeparator', rect(0, height - 1, width, 1), {
                background: 'separator',
                radius: 0
            })
        );
    const object = geometry.cells.find((cell) => cell.key === 'object');
    if (object) {
        const x = model.expanded ? 68 : object.x;
        nodes.push(
            node('View', 'taskObjectPreview', rect(x, 12, 34, 34), {
                view: 'preview'
            }),
            label(
                'taskObjectTitle',
                rect(x + 41, 11, object.width - 41, 20),
                model.title,
                {
                    fontRole: 'body',
                    weight: 600
                }
            ),
            label(
                'taskObjectProcess',
                rect(x + 41, 31, object.width - 41, 16),
                model.processLabel +
                    (model.context && model.context !== model.process
                        ? ' · ' + model.context
                        : ''),
                { fontRole: 'caption', color: 'secondaryText' }
            )
        );
    }
    for (const cell of geometry.cells) {
        if (model.expanded || cell.key === 'object') continue;
        const x = cell.x,
            w = cell.width;
        if (cell.key === 'dates') {
            nodes.push(
                label(
                    'taskStart',
                    rect(x, 13, w, 15),
                    String(model.start || '').slice(0, 10) || '—',
                    { fontRole: 'caption', color: 'secondaryText' }
                ),
                label(
                    'taskDeadline',
                    rect(x, 28, w, 18),
                    String(model.end || '').slice(0, 10) || '—',
                    {
                        fontRole: 'secondary',
                        color: model.overdue ? 'error' : 'primaryText'
                    }
                )
            );
        } else if (cell.key === 'progress') {
            const value = Math.max(
                0,
                Math.min(100, Number(model.progress) || 0)
            );
            nodes.push(
                label('taskProgress', rect(x, 18, w, 16), value + '%', {
                    fontRole: 'caption'
                }),
                node('Box', 'taskProgressTrack', rect(x, 36, w, 3), {
                    background: 'surfaceContainerHighest',
                    radius: 1.5
                }),
                node(
                    'Box',
                    'taskProgressFill',
                    rect(x, 36, (w * value) / 100, 3),
                    { background: model.processColor || 'action', radius: 1.5 }
                )
            );
        } else if (cell.key === 'hours') {
            nodes.push(
                label(
                    'taskHours',
                    rect(x, 19, w, 20),
                    model.hoursLabel || '—',
                    {
                        fontRole: 'secondary',
                        weight: 600,
                        color: model.overPlan
                            ? 'red'
                            : model.pendingHours
                              ? 'yellow'
                              : 'primaryText'
                    }
                )
            );
        } else if (cell.key === 'notes') {
            nodes.push(
                button(
                    'taskNotes',
                    rect(x, 14, w, 30),
                    tr('Open notes') + ': ' + model.title,
                    'comment',
                    { type: 'notes' },
                    model.hasTask !== false,
                    {
                        iconOnly: true,
                        iconAction: true,
                        iconSize: 17,
                        round: false,
                        iconColor: model.notes ? 'action' : 'secondaryText',
                        badgeCount: model.notes || 0
                    }
                )
            );
        } else {
            nodes.push(
                node('View', 'taskCell_' + cell.key, rect(x, 14.5, w, 29), {
                    view: cell.key
                })
            );
        }
        if (
            model.editableCells &&
            ['dates', 'progress', 'hours'].includes(cell.key)
        )
            nodes.push(
                node(
                    'View',
                    'taskCellInput_' + cell.key,
                    rect(x, 0, w, height),
                    { view: cell.key }
                )
            );
    }
    nodes.push(
        node('View', 'taskRowAction', rect(width - 35, 14, 30, 30), {
            view: 'actions',
            opacity:
                model.hovered ||
                model.active ||
                model.dirty ||
                model.busy ||
                model.actionAlert
                    ? 1
                    : 0.35
        })
    );
    if (model.expanded)
        nodes.push(
            button(
                'taskExpandedNotes',
                rect(width - 71, 14, 30, 30),
                tr('Open notes') + ': ' + model.title,
                'comment',
                { type: 'notes' },
                model.hasTask !== false,
                {
                    iconOnly: true,
                    iconAction: true,
                    iconSize: 17,
                    round: false,
                    iconColor: model.notes ? 'action' : 'secondaryText',
                    badgeCount: model.notes || 0
                }
            )
        );
    return { nodes, height };
}

// HTML keeps real table cells; Qt renders the same scene as one lightweight row.
export function segments(geometry, expanded) {
    const leading = geometry.cells.length ? geometry.cells[0].x : 68;
    const result = [{ key: 'leading', x: 0, width: leading }];
    if (expanded)
        result.push({
            key: 'object',
            sourceKey: 'object',
            x: leading,
            width: geometry.width - leading - metrics.actions,
            colspan: geometry.cells.length
        });
    else
        for (const cell of geometry.cells)
            result.push(
                Object.assign({}, cell, {
                    width: cell.width + geometry.spacing
                })
            );
    result.push({
        key: 'actions',
        x: geometry.width - metrics.actions,
        width: metrics.actions
    });
    return result;
}

export function slice(scene, segment) {
    const nodes = [];
    for (const original of scene.nodes) {
        if (
            original.id.startsWith('taskRowSurface_') ||
            ['taskRowSeparator', 'taskHeaderSurface'].includes(original.id)
        ) {
            nodes.push(
                Object.assign({}, original, {
                    x: 0,
                    width: segment.width,
                    radius: 0,
                    radiusRole: undefined
                })
            );
        } else if (
            original.x >= segment.x &&
            original.x < segment.x + segment.width
        ) {
            nodes.push(
                Object.assign({}, original, { x: original.x - segment.x })
            );
        }
    }
    return { nodes, height: scene.height };
}

export function mobileRow(model, width, language) {
    const tr = (text) => translate(text, language),
        nodes = [],
        titleWidth = Math.max(0, width - 126),
        height = 180 + (model.pending ? 20 : 0);
    nodes.push(
        node('Box', 'taskPhoneSurface', rect(0, 0, width, height), {
            background: model.checked ? 'selected' : 'row',
            border: 'outlineVariant',
            borderWidth: 1,
            radiusRole: 'surfaceRadius'
        })
    );
    nodes.push(
        node('Box', 'taskPhoneRail', rect(0, 12, 1, height - 24), {
            background: model.accent || 'action'
        })
    );
    nodes.push(
        node('View', 'taskPhonePreview', rect(12, 12, 42, 42), {
            view: 'preview'
        })
    );
    nodes.push(
        button(
            'taskPhoneTitle',
            rect(62, 10, titleWidth, 30),
            model.title || '',
            '',
            { type: 'enter' },
            !model.busy && !model.deleting,
            {
                label: model.title || '',
                fontRole: 'bodyLarge',
                weight: 600,
                align: 'left'
            }
        )
    );
    nodes.push(
        label(
            'taskPhoneProcess',
            rect(62, 42, Math.max(0, width - 74), 18),
            model.processLabel || model.process || '',
            { fontRole: 'caption', color: 'secondaryText' }
        )
    );
    nodes.push(
        node('CheckBox', 'taskPhoneCheck', rect(width - 44, 12, 28, 28), {
            label: (model.title || '') + ': ' + (model.process || ''),
            checked: !!model.checked,
            enabled: !model.busy,
            action: { type: 'select' }
        })
    );
    nodes.push(
        node('Box', 'taskPhoneStatusDot', rect(62, 72, 8, 8), {
            background: model.statusColor || 'action',
            radius: 4
        })
    );
    nodes.push(
        label(
            'taskPhoneStatus',
            rect(75, 66, Math.max(0, width - 87), 18),
            model.statusLabel || tr('No status'),
            { fontRole: 'caption', color: 'secondaryText' }
        )
    );
    nodes.push(
        label(
            'taskPhoneAssignee',
            rect(62, 88, Math.max(0, width - 74), 18),
            model.assignedLabel || tr('Not assigned'),
            { fontRole: 'caption', color: 'secondaryText' }
        )
    );
    if (model.deadline) {
        nodes.push(
            node('Icon', 'taskPhoneDateIcon', rect(62, 112, 14, 14), {
                icon: 'calendar-month',
                color: 'secondaryText'
            })
        );
        nodes.push(
            label(
                'taskPhoneDate',
                rect(81, 110, Math.max(0, width - 93), 18),
                model.deadline,
                { fontRole: 'caption', color: 'secondaryText' }
            )
        );
    }
    if (model.pending)
        nodes.push(
            label(
                'taskPhonePending',
                rect(62, 134, Math.max(0, width - 74), 18),
                tr('Pending task changes'),
                { fontRole: 'caption', color: 'action' }
            )
        );
    const bottom = height - 40,
        progress = Math.max(0, Math.min(100, Number(model.progress) || 0));
    nodes.push(
        node('Box', 'taskPhoneProgressTrack', rect(62, bottom + 12, 60, 4), {
            background: 'outlineVariant',
            radius: 2
        })
    );
    nodes.push(
        node(
            'Box',
            'taskPhoneProgress',
            rect(62, bottom + 12, (60 * progress) / 100, 4),
            { background: 'action', radius: 2 }
        )
    );
    nodes.push(
        label(
            'taskPhoneProgressText',
            rect(130, bottom + 4, Math.max(0, width - 214), 20),
            String(progress) + '%',
            { fontRole: 'caption', color: 'secondaryText' }
        )
    );
    nodes.push(
        button(
            'taskPhoneNotes',
            rect(width - 80, bottom, 28, 28),
            tr('Open notes'),
            'comment',
            { type: 'notes' },
            !model.busy && !model.pending && !model.deleting && model.hasTask,
            {
                iconOnly: true,
                iconAction: true,
                iconSize: 17,
                badgeCount: model.notes || 0
            }
        )
    );
    nodes.push(
        button(
            'taskPhoneMenu',
            rect(width - 44, bottom, 28, 28),
            tr('Task actions'),
            'more',
            { type: 'menu' },
            !model.busy,
            { iconOnly: true, iconAction: true, iconSize: 17 }
        )
    );
    return { nodes, height };
}

import { node, rect, label, button } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { date, size, fileType } from './inspector.ui.mjs';
import { badges } from './presentation.mjs';
import { toneRole } from './rows.ui.mjs';

export function columns(view, width) {
    const definitions = {
        changelistFiles: [
            ['File', 200],
            ['In folder', Math.max(250, width - 624)],
            ['Resolve status', 130],
            ['Type', 120],
            ['Action', 150]
        ],
        changelistTasks: [
            ['Task', 180],
            ['Status', 140],
            ['Description', Math.max(420, width - 344)]
        ],
        history: [
            ['Revision', 100],
            ['Changelist', 120],
            ['Date submitted', 190],
            ['Submitted by', 150],
            ['Type', 100],
            ['Size', 110],
            ['Description', Math.max(280, width - 790)]
        ],
        streams: [
            ['Stream', 260],
            ['Stream root', 240],
            ['Parent', 160],
            ['Type', 120],
            ['Description', Math.max(260, width - 780)]
        ],
        workspaces: [
            ['Workspace', 200],
            ['Stream', 180],
            ['Owner', 140],
            ['Workspace location', Math.max(280, width - 520)]
        ],
        tasks: [
            ['Task', 180],
            ['State', 140],
            ['File', Math.max(280, width - 440)],
            ['Progress', 120]
        ],
        files: [
            ['File', Math.max(300, width - 320)],
            ['State', 200],
            ['File size', 120]
        ]
    };
    return (definitions[view] || definitions.files).map(([title, width]) => ({
        title,
        width
    }));
}

export function cells(view, row, language = 'en') {
    const tr = (text) => translate(text, language);
    if (view === 'changelistTasks')
        return [row.code, row.status, row.description];
    if (view === 'changelistFiles') {
        const parts = row.path.split('/'),
            name = parts.pop(),
            action = row.action || '';
        return [
            name,
            parts.join('/') || '/',
            row.conflict
                ? tr('Conflict')
                : row.resolved_sha256 !== undefined
                  ? tr('Resolved')
                  : '—',
            name.lastIndexOf('.') > 0
                ? name.slice(name.lastIndexOf('.') + 1).toUpperCase()
                : '—',
            tr(
                ['delete', 'move/delete'].includes(action)
                    ? 'Delete'
                    : action === 'move/add'
                      ? 'Rename'
                      : action === 'baseline'
                        ? 'Published'
                        : row.base
                          ? 'Edit'
                          : 'Add'
            )
        ];
    }
    if (view === 'history')
        return [
            '#' + row.number,
            '#' + (row.change_number || '—'),
            date(row.submitted_at),
            row.author || '—',
            fileType(row),
            size(row.size || 0),
            row.description || ''
        ];
    if (view === 'streams')
        return [
            row.title || row.code,
            '//' + row.depot + '/' + row.code,
            row.parent || '—',
            row.stream_type || '',
            row.description || ''
        ];
    if (view === 'workspaces')
        return [
            row.code,
            row.stream || '—',
            row.owner || '—',
            row.local_root || '—'
        ];
    if (view === 'tasks')
        return [
            row.task || row.code,
            row.state || '—',
            row.path || row.prefix || '—',
            (row.bytes_done || 0) + ' / ' + (row.bytes_total || 0)
        ];
    return [
        row.path || row.code || '',
        row.state || row.action || '—',
        size(row.size || row.bytes_total || 0)
    ];
}

export function header(view, width, language) {
    let x = 0;
    const nodes = columns(view, width).map((column, index) => {
        const inset = view.startsWith('changelist') ? 6 : 8;
        const item = label(
            'workspaceTableHeading' + index,
            rect(x + inset, 0, column.width - inset - 8, 28),
            translate(column.title, language),
            { color: 'secondaryText', fontRole: 'secondary' }
        );
        x += column.width;
        return item;
    });
    return { nodes };
}

export function row(model, width, language) {
    const data = model.row,
        view = model.view,
        values = cells(view, data, language),
        definitions = columns(view, width),
        height = view === 'streams' ? 34 : 32;
    const children = [];
    let x = 0;
    for (const [index, column] of definitions.entries()) {
        let inset = view.startsWith('changelist') ? 6 : 8;
        if (index === 0 && view.startsWith('changelist')) {
            const badge =
                view === 'changelistTasks'
                    ? { icon: 'task', tone: 'action' }
                    : badges(data)[0];
            inset = 28;
            children.push(
                node('Icon', 'workspaceTableFileIcon', rect(5, 8, 16, 16), {
                    icon: badge.icon,
                    color: toneRole(badge.tone)
                })
            );
        }
        if (index === 0 && view === 'history') {
            inset = 32;
            children.push(
                node('Icon', 'workspaceTableHistoryIcon', rect(8, 8, 16, 16), {
                    icon: ['delete', 'move/delete'].includes(data.action)
                        ? 'delete'
                        : data.action === 'add'
                          ? 'add'
                          : data.action === 'move/add'
                            ? 'swap-horizontal'
                            : 'edit',
                    color: data.deleted ? 'error' : 'action'
                })
            );
        }
        if (index === 0 && view === 'streams') {
            const indent = model.treeMode
                ? Math.min((data.depth || 0) * 20, 160)
                : 8;
            if (model.treeMode)
                children.push(
                    button(
                        'streamToggle_' + data.code,
                        rect(indent, 3, 28, 28),
                        translate('Expand or collapse', language),
                        model.expanded ? 'chevron-down' : 'chevron-right',
                        { type: 'toggle', key: data.code },
                        !!data.children,
                        { iconOnly: true, iconAction: true }
                    )
                );
            const iconX = indent + (model.treeMode ? 31 : 0);
            children.push(
                node(
                    'Icon',
                    'workspaceTableStreamIcon',
                    rect(iconX, 8, 18, 18),
                    {
                        icon: 'source-branch',
                        color:
                            data.stream_type === 'release' ? 'yellow' : 'action'
                    }
                )
            );
            inset = iconX + 22;
        }
        children.push(
            label(
                'workspaceTableCell' + index,
                rect(
                    x + inset,
                    0,
                    Math.max(0, column.width - inset - 8),
                    height
                ),
                String(values[index] ?? ''),
                {
                    elideMiddle: index === 0,
                    fontRole: 'secondary',
                    toolTip: String(values[index] ?? '')
                }
            )
        );
        x += column.width;
    }
    return {
        nodes: [
            node('Box', 'workspaceTableRow', rect(0, 0, x, height), {
                background: model.selected
                    ? 'selected'
                    : model.hovered
                      ? 'rowHover'
                      : 'transparent',
                children
            })
        ]
    };
}

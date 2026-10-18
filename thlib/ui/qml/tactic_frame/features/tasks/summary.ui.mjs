import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

// The separate native Task Manager window exposes this management summary.
export function heading(model, width, language) {
    const tr = (text, values) => translate(text, language, values),
        height = 48;
    const size = model.controlHeight || 36,
        y = (height - size) / 2;
    let right = width - 8;
    const nodes = [
        node('Box', 'taskWindowHeading', rect(0, 0, width, height), {
            background: 'surfaceContainerLow',
            radiusRole: 'surfaceRadius'
        })
    ];
    for (const [type, title, icon, w, checked, enabled] of [
        ['refresh', 'Refresh tasks', 'refresh', 32, false, model.canRefresh],
        ['team', 'Teams', 'groups', 32, model.scope === 'team', true],
        [
            'project',
            'PROJECT',
            'workspaces',
            width < 650 ? 32 : 100,
            model.scope === 'project',
            true
        ],
        [
            'user',
            'MY TASKS',
            'person',
            width < 650 ? 32 : 112,
            model.personal,
            true
        ],
        [
            'selected',
            'Selected',
            model.selectedIcon || 'inventory-2',
            width < 650 ? 32 : 112,
            ['object', 'multiple'].includes(model.scope),
            true
        ]
    ]) {
        right -= w;
        nodes.push(
            button(
                'taskWindow_' + type,
                rect(Math.max(0, right), y, w, size),
                tr(title),
                icon,
                { type },
                enabled !== false,
                {
                    tonal: checked,
                    iconOnly: w === 32,
                    iconAction: w === 32,
                    iconSize: 17,
                    label: tr(title)
                }
            )
        );
        right -= 7;
    }
    nodes.push(
        node('Icon', 'taskWindowIcon', rect(12, 14.5, 19, 19), {
            icon: 'tasks',
            color: 'action'
        })
    );
    nodes.push(
        label(
            'taskWindowTitle',
            rect(38, 6, Math.max(0, right - 38), 19),
            model.title || '',
            { fontRole: 'bodyLarge', weight: 600 }
        )
    );
    nodes.push(
        label(
            'taskWindowCount',
            rect(38, 26, Math.max(0, right - 38), 15),
            tr('{count} loaded tasks', { count: model.loaded || 0 }),
            { fontRole: 'caption', color: 'secondaryText' }
        )
    );
    return { height, nodes };
}

export function describe(model, width, language) {
    const tr = (text, values) => translate(text, language, values),
        height = model.management ? 108 : 52;
    const count = model.complete
        ? tr('{count} tasks loaded', { count: model.loaded })
        : model.total >= 0
          ? tr('{loaded} of {total} tasks loaded', {
                loaded: model.loaded,
                total: model.total
            })
          : tr('{count} tasks loaded | partial scope', { count: model.loaded });
    const nodes = [
        node('Box', 'taskSummarySurface', rect(0, 0, width, height), {
            background: 'surfaceContainerLow',
            radiusRole: 'surfaceRadius'
        }),
        label('taskSummaryHeading', rect(10, 6, 132, 15), tr('SCOPE SUMMARY'), {
            fontRole: 'caption',
            weight: 600,
            color: 'secondaryText'
        }),
        label('taskSummaryCount', rect(10, 21, 132, 15), count, {
            fontRole: 'caption',
            color: model.complete ? 'primaryText' : 'yellow'
        }),
        node(
            'View',
            'taskSummaryPresets',
            rect(148, 6, Math.max(0, width - 156), 34),
            { view: 'presets' }
        )
    ];
    if (model.management) {
        const statusWidth = Math.min(360, width * 0.32),
            statusX = width - 8 - statusWidth;
        nodes.push(
            label('taskWorkloadHeading', rect(10, 64, 64, 15), tr('WORKLOAD'), {
                fontRole: 'caption',
                weight: 600,
                color: 'secondaryText'
            })
        );
        nodes.push(
            node(
                'View',
                'taskSummaryWorkload',
                rect(81, 45, Math.max(0, statusX - 66 - 7 - 81), 57),
                { view: 'workload' }
            )
        );
        nodes.push(
            label(
                'taskStatusesHeading',
                rect(statusX - 66, 64, 59, 15),
                tr('STATUSES'),
                { fontRole: 'caption', weight: 600, color: 'secondaryText' }
            )
        );
        nodes.push(
            node(
                'View',
                'taskSummaryStatuses',
                rect(statusX, 45, statusWidth, 57),
                { view: 'statuses' }
            )
        );
    }
    return { height, nodes };
}

export function chips(model, language, measure) {
    const tr = (text) => translate(text, language);
    let x = 0;
    const rows = model.statuses || [
        { key: '', text: tr('ALL'), selected: !model.active },
        ...['today', 'overdue', 'unassigned', 'review', 'recent']
            .filter((key) => key !== 'unassigned' || model.management)
            .map((key) => ({
                key,
                text: tr(key.toUpperCase()) + '  ' + (model[key] || 0),
                selected: (model.selected || []).includes(key),
                accent: key === 'overdue' ? 'error' : 'action'
            }))
    ];
    const nodes = rows.map((record) => {
        const width = Math.min(132, Math.ceil(measure(record.text)) + 24);
        const result = node(
            'View',
            'taskSummaryChip_' + record.key,
            rect(x, (model.height - 28) / 2, width, 28),
            {
                view: 'chip',
                record,
                action: {
                    type: model.statuses ? 'status' : 'preset',
                    value: record.key
                }
            }
        );
        x += width + (model.statuses ? 5 : 6);
        return result;
    });
    return {
        height: model.height,
        width: Math.max(0, x - (model.statuses ? 5 : 6)),
        nodes
    };
}

export function workload(model, height, language) {
    const tr = (text, values) => translate(text, language, values),
        width = 148,
        y = (height - 30) / 2;
    return {
        height,
        nodes: [
            node('Box', 'taskWorkloadSurface', rect(0, 0, width, height), {
                background: model.hovered
                    ? 'surfaceContainerHighest'
                    : 'surfaceContainerHigh',
                radiusRole: 'itemRadius'
            }),
            node(
                'Preview',
                'taskWorkloadAvatar',
                rect(7, (height - 26) / 2, 26, 26),
                {
                    source: model.avatarUrl || '',
                    fallbackIcon: 'person',
                    fallbackText: String(model.label || '?')
                        .slice(0, 2)
                        .toUpperCase(),
                    previewSize: 26,
                    round: true
                }
            ),
            label('taskWorkloadUser', rect(39, y, 102, 15), model.label || '', {
                fontRole: 'caption',
                weight: 600
            }),
            label(
                'taskWorkloadCount',
                rect(39, y + 15, 102, 15),
                tr('{count} tasks', { count: model.count }) +
                    (model.overdue
                        ? ' | ' +
                          tr('{count} overdue', { count: model.overdue })
                        : ''),
                {
                    fontRole: 'caption',
                    color: model.overdue ? 'error' : 'secondaryText'
                }
            ),
            node('Action', 'taskWorkloadChoose', rect(0, 0, width, height), {
                label: model.label || '',
                action: {
                    type: model.login ? 'assigned' : 'unassigned',
                    value: model.login || ''
                }
            })
        ]
    };
}

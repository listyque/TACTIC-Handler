import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { packTagRows } from '../../controls/lists/chips.mjs';

export const groups = [
    ['preset', 'QUICK VIEW'],
    ['process', 'PROCESSES'],
    ['status', 'STATUSES'],
    ['priority', 'PRIORITIES'],
    ['milestone', 'MILESTONES'],
    ['supervisor', 'SUPERVISORS'],
    ['assigned', 'ASSIGNEES']
];
export const presets = {
    mine: 'My Tasks',
    unassigned: 'Unassigned',
    overdue: 'Overdue',
    today: 'Today',
    recent: 'Recently Updated',
    review: 'Review'
};
export const exactFields = {
    process: 'Process',
    status: 'Status',
    assigned: 'Assigned to',
    supervisor: 'Supervisor',
    priority: 'Priority',
    milestone: 'Milestone'
};

export function fromFacets(facets, quick, scope) {
    return groups
        .map(([key]) => {
            let options =
                key === 'preset'
                    ? Object.keys(presets)
                          .filter(
                              (value) =>
                                  value !== 'review' ||
                                  facets?.preset?.review ||
                                  quick.preset?.includes(value)
                          )
                          .map((value) => ({
                              key: value,
                              title: presets[value],
                              count: facets?.preset?.[value] || 0
                          }))
                    : (facets?.[key] || [])
                          .filter((row) => row.key)
                          .map((row) => Object.assign({}, row));
            if (
                key === 'assigned' &&
                !['project', 'team', 'multiple'].includes(scope)
            )
                options = [];
            const selected = quick[key] || [];
            for (const value of selected)
                if (!options.some((row) => row.key === value))
                    options.push({ key: value, title: value, count: 0 });
            return {
                key,
                allSelected: !selected.length,
                options: options.map((row) =>
                    Object.assign({}, row, {
                        selected: selected.includes(row.key)
                    })
                )
            };
        })
        .filter((group) => group.options.length);
}

export function describe(model, width, language, measure) {
    const tr = (text) => translate(text, language),
        nodes = [],
        options = model.groups || [];
    const chip = (id, bounds, record, action, marker) =>
        node('View', id, bounds, {
            view: 'chip',
            record,
            action,
            marker,
            enabled: !model.busy
        });
    const all = tr('ALL'),
        allWidth = Math.min(width, measure(all) + 24);
    nodes.push(
        label(
            'taskFiltersTitle',
            rect(0, 4, Math.max(0, width - allWidth - 8), 24),
            tr('QUICK FILTERS'),
            { fontRole: 'bodyLarge', weight: 600 }
        )
    );
    nodes.push(
        chip(
            'taskQuickFilterAllChip',
            rect(width - allWidth, 0, allWidth, 28),
            { text: all, selected: !model.active },
            { type: 'clear' },
            false
        )
    );
    let y = 44;
    for (const [key, title] of groups) {
        const group = options.find((row) => row.key === key);
        if (!group?.options.length) continue;
        nodes.push(
            label(
                'taskFilterTitle_' + key,
                rect(0, y, width - 28, 24),
                tr(title),
                { fontRole: 'caption', weight: 600, color: 'secondaryText' }
            )
        );
        if (!group.allSelected)
            nodes.push(
                button(
                    'taskFilterClear_' + key,
                    rect(width - 24, y, 24, 24),
                    tr('Clear this filter group'),
                    'close',
                    { type: 'clear-group', group: key },
                    !model.busy,
                    { iconOnly: true, iconAction: true, iconSize: 13 }
                )
            );
        y += 31;
        const marker = key === 'process' || key === 'status';
        const records = group.options.map((row) =>
            Object.assign({}, row, {
                text:
                    (key === 'preset'
                        ? tr(presets[row.key] || row.title)
                        : row.title) +
                    '  ' +
                    row.count
            })
        );
        const rows = packTagRows(
            records,
            width,
            (_text, _weight, row) => measure(row.text) + (marker ? 13 : 0),
            undefined,
            width,
            { rowHeight: 29, gap: 7 }
        );
        for (const row of rows) {
            let x = 0;
            for (const cell of row.cells) {
                const record = records[cell.index];
                nodes.push(
                    chip(
                        'taskFilter_' + key + '_' + record.key,
                        rect(x, y + row.top, cell.width, 29),
                        record,
                        {
                            type: 'quick',
                            group: key,
                            value: record.key,
                            checked: !record.selected
                        },
                        marker
                    )
                );
                x += cell.width + 7;
            }
        }
        const last = rows[rows.length - 1];
        y += (last ? last.top + last.height : 0) + 16;
    }
    nodes.push(
        button(
            'taskFilterAdvanced',
            rect(0, y, width, 32),
            tr('Advanced filters'),
            model.advanced ? 'expand-less' : 'expand-more',
            { type: 'advanced' },
            true,
            { tonal: true }
        )
    );
    y += 40;
    if (model.advanced) {
        for (const key of Object.keys(exactFields).concat(['due'])) {
            const title = key === 'due' ? 'Deadline' : exactFields[key];
            const group = options.find((row) => row.key === key);
            const rows =
                key === 'due'
                    ? [
                          ['overdue', 'Overdue'],
                          ['today', 'Today'],
                          ['soon', 'Next three days'],
                          ['scheduled', 'Later']
                      ].map(([value, label]) => ({ value, label: tr(label) }))
                    : (group?.options || []).map((row) => ({
                          value: row.key,
                          label: row.title
                      }));
            nodes.push(
                label(
                    'taskExactTitle_' + key,
                    rect(0, y, width, 16),
                    tr(title),
                    { fontRole: 'caption', color: 'secondaryText' }
                )
            );
            nodes.push(
                node('Choice', 'taskExact_' + key, rect(0, y + 20, width, 32), {
                    label: tr(title),
                    value: model.filters?.[key] || '',
                    options: [{ value: '', label: tr('All') }].concat(rows),
                    enabled: !model.busy,
                    action: { type: 'filter', field: key }
                })
            );
            y += 60;
        }
        nodes.push(
            node('Switch', 'taskFilterNotes', rect(width - 48, y, 48, 32), {
                text: tr('Has notes'),
                label: tr('Has notes'),
                checked: !!model.filters?.hasNotes,
                enabled: !model.busy,
                action: { type: 'filter', field: 'hasNotes' }
            })
        );
        nodes.push(
            label(
                'taskFilterNotesTitle',
                rect(0, y, width - 56, 32),
                tr('Has notes')
            )
        );
        y += 40;
    }
    return { nodes, height: y };
}

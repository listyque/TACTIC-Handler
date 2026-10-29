import { node, label, rect } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export function projects(model, query = '') {
    const words = String(query)
        .trim()
        .toLocaleLowerCase()
        .split(/\s+/)
        .filter(Boolean);
    return (model.projects || []).filter((row) =>
        words.every((word) =>
            [row.label, row.value, row.category]
                .join(' ')
                .toLocaleLowerCase()
                .includes(word)
        )
    );
}
export function size(width, height, count) {
    return {
        width: Math.max(1, Math.min(360, width - 40)),
        height: Math.max(
            100,
            Math.min(430, height - 100, 88 + Math.max(1, count) * 58)
        )
    };
}
function initials(row) {
    return String(row.label || row.value || '')
        .replace(/_/g, ' ')
        .split(/\s+/)
        .filter(Boolean)
        .slice(0, 2)
        .map((word) => word[0])
        .join('')
        .toUpperCase();
}
function preview(id, row, x, y) {
    return node('Preview', id, rect(x, y, 28, 28), {
        source: row.preview || '',
        initials: initials(row),
        radius: 4,
        accent: 'toolBar',
        outlined: true
    });
}
export function trigger(model, width, height, language) {
    const current = (model.projects || []).find(
        (row) => row.value === model.project
    ) || {
        value: model.project,
        label: model.project || translate('Project', language)
    };
    return {
        nodes: [
            node(
                'Action',
                'administrationProjectSelector',
                rect(0, 0, width, height),
                {
                    text: current.label,
                    description: translate('Administration project', language),
                    toolTip: current.label + ' · ' + current.value,
                    enabled: !model.locked,
                    normalColor: 'surfaceContainerLow',
                    border: 'outlineVariant',
                    radius: 8,
                    action: { type: 'open' },
                    children: [
                        preview(
                            'administrationProjectPreview',
                            current,
                            6,
                            (height - 28) / 2
                        ),
                        label(
                            'administrationProjectTitle',
                            rect(44, 0, Math.max(1, width - 72), height),
                            current.label,
                            { weight: 600 }
                        ),
                        node(
                            'Icon',
                            'administrationProjectChevron',
                            rect(width - 24, (height - 16) / 2, 16, 16),
                            { icon: 'chevron-down', color: 'secondaryText' }
                        )
                    ]
                }
            )
        ]
    };
}
export function panel(model, query, width, height, language) {
    const rows = projects(model, query),
        tr = (text) => translate(text, language);
    const nodes = [
        node(
            'Field',
            'administrationProjectSearch',
            rect(8, 8, width - 16, 38),
            {
                text: query,
                placeholder: tr('Find a project by name or code'),
                label: tr('Find a project by name or code'),
                enabled: !model.locked,
                action: { type: 'query' },
                keys: rows.length
                    ? {
                          ArrowDown: { type: 'focus', index: 0 },
                          ArrowUp: { type: 'focus', index: rows.length - 1 }
                      }
                    : {}
            }
        ),
        node(
            'List',
            'administrationProjectList',
            rect(0, 54, width, Math.max(1, height - 84)),
            {
                source: 'projects',
                rowHeight: 58,
                rowGap: 0,
                keyField: 'value',
                fields: [],
                scrollbarId: 'administrationProjectScrollBar'
            }
        ),
        node(
            'Box',
            'administrationProjectDivider',
            rect(8, height - 28, width - 16, 1),
            { background: 'outlineVariant' }
        ),
        label(
            'administrationProjectCount',
            rect(8, height - 25, width - 16, 22),
            tr('{visible} of {total} projects shown')
                .replace('{visible}', rows.length)
                .replace('{total}', (model.projects || []).length),
            { fontRole: 'caption', color: 'secondaryText' }
        )
    ];
    if (!rows.length)
        nodes.push(
            label(
                'administrationProjectsEmpty',
                rect(12, 58, width - 24, height - 90),
                tr('No projects match the current filters'),
                { wrap: true, color: 'secondaryText' }
            )
        );
    return { nodes };
}
export function row(list, record, model, query, language) {
    const rows = projects(model, query),
        index = rows.findIndex((row) => row.value === record.value),
        width = list.width - 16,
        tr = (text) => translate(text, language),
        kind = record.kind ? tr(record.kind) : record.category || '';
    return {
        nodes: [
            node(
                'Action',
                'administrationProjectOption_' + record.value,
                rect(0, 0, width, 56),
                {
                    text: record.label,
                    description: record.value,
                    toolTip: record.label + ' · ' + record.value,
                    enabled: !model.locked,
                    selected: record.value === model.project,
                    normalColor: 'transparent',
                    selectedColor: 'selected',
                    radius: 4,
                    action: { type: 'select', value: record.value },
                    keys: {
                        ArrowDown: {
                            type: 'focus',
                            index: (index + 1) % rows.length
                        },
                        ArrowUp: {
                            type: 'focus',
                            index: (index + rows.length - 1) % rows.length
                        },
                        Home: { type: 'focus', index: 0 },
                        End: { type: 'focus', index: rows.length - 1 }
                    },
                    children: [
                        preview(
                            'administrationProjectOptionPreview_' +
                                record.value,
                            record,
                            8,
                            13
                        ),
                        label(
                            'administrationProjectOptionTitle_' + record.value,
                            rect(46, 4, width - 76, 30),
                            record.label,
                            { weight: 600, wrap: true, fontRole: 'secondary' }
                        ),
                        label(
                            'administrationProjectOptionCode_' + record.value,
                            rect(46, 34, width - 76, 18),
                            [record.value, kind].filter(Boolean).join(' · '),
                            {
                                fontRole: 'caption',
                                weight: 400,
                                color:
                                    record.value === model.project
                                        ? 'selectedText'
                                        : 'secondaryText'
                            }
                        ),
                        ...(record.value === model.project
                            ? [
                                  node(
                                      'Icon',
                                      'administrationProjectCheck',
                                      rect(width - 24, 18, 18, 18),
                                      { icon: 'check', color: 'selectedText' }
                                  )
                              ]
                            : [])
                    ]
                }
            )
        ]
    };
}

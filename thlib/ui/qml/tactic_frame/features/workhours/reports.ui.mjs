import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export const titles = {
    my_hours: 'My Work Hours',
    bid_actual: 'Bid vs Actual',
    approval: 'Approval',
    team: 'Team Hours',
    process: 'Process Hours',
    labor_cost: 'Labor Cost'
};
export const descriptions = {
    my_hours: 'Daily logged time',
    bid_actual: 'Planned and approved hours',
    approval: 'Approved and pending time',
    team: 'Hours by user',
    process: 'Hours by process',
    labor_cost: 'Authorized wage-based cost'
};

export function allowed(record, model) {
    return (
        !record.permission ||
        record.permission === 'user' ||
        (record.permission === 'supervisor' && !!model.canManage) ||
        (record.permission === 'finance' && !!model.canViewCosts)
    );
}

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language),
        compact = width < 640;
    const nav = compact ? 0 : Math.min(230, Math.max(170, width * 0.28));
    const x = compact ? 8 : nav + 9,
        y = compact ? 50 : 9,
        main = Math.max(0, width - x - 9);
    const nodes = [
        node('Box', 'workReportBackground', rect(0, 0, width, height), {
            background: 'workspace'
        })
    ];
    if (compact)
        nodes.push(
            node(
                'Choice',
                'workReportChoice',
                rect(8, 8, Math.max(0, width - 16), 34),
                {
                    label: tr('Report'),
                    value: model.report,
                    options: (model.options || [])
                        .filter((record) => allowed(record, model))
                        .map((record) => ({
                            value: record.key || record.value,
                            label: tr(
                                titles[record.key || record.value] ||
                                    record.title ||
                                    record.label
                            )
                        })),
                    enabled: !model.busy,
                    action: { type: 'report' }
                }
            )
        );
    else
        nodes.push(
            node(
                'List',
                'workReportTypes',
                rect(7, 7, Math.max(0, nav - 14), Math.max(0, height - 14)),
                {
                    source: 'reports',
                    keyField: 'key',
                    fields: [
                        'key',
                        'title',
                        'description',
                        'icon',
                        'permission',
                        'selected'
                    ],
                    rowHeight: 54,
                    rowGap: 4
                }
            )
        );
    nodes.push(
        label(
            'workReportTitle',
            rect(x, y, Math.max(0, main - 37), 28),
            tr(titles[model.report] || 'Work reports'),
            { fontRole: 'title', weight: 600, role: 'heading' }
        )
    );
    nodes.push(
        button(
            'workReportRefresh',
            rect(x + Math.max(0, main - 30), y, 30, 30),
            tr('Refresh report'),
            'refresh',
            { type: 'refresh' },
            !model.busy,
            { iconOnly: true }
        )
    );
    nodes.push(
        label(
            'workReportDates',
            rect(x, y + 31, main, 22),
            (model.weekStart || '') + ' — ' + (model.weekEnd || ''),
            { fontRole: 'caption', color: 'secondaryText' }
        )
    );
    const message = model.error || model.message || '';
    if (message)
        nodes.push(
            label('workReportMessage', rect(x, y + 58, main, 38), tr(message), {
                maxLines: 2,
                color: model.error ? 'error' : 'secondaryText'
            })
        );
    const top = y + (message ? 103 : 60);
    nodes.push(
        node(
            'List',
            'workReportValues',
            rect(x, top, main, Math.max(0, height - top - 9)),
            {
                source: 'values',
                keyField: 'label',
                fields: ['label', 'value', 'valueLabel', 'share'],
                rowHeight: 52,
                rowGap: 6
            }
        )
    );
    if (!model.count && !model.busy)
        nodes.push(
            label(
                'workReportEmpty',
                rect(x, top, main, 44),
                tr('No report data for this week'),
                { color: 'secondaryText', wrap: true }
            )
        );
    return { nodes };
}

export function descriptor(record, model, width, language) {
    const key = record.key || record.value;
    const permitted = allowed(record, model);
    return {
        nodes: [
            node('Action', 'workReport-' + key, rect(0, 0, width, 54), {
                text: translate(
                    titles[key] || record.title || record.label,
                    language
                ),
                enabled: !!permitted && !model.busy,
                selected: key === model.report,
                normalColor: 'transparent',
                selectedColor: 'contentSelection',
                action: { type: 'report', value: key },
                children: [
                    node('Icon', 'workReportTypeIcon', rect(8, 18, 18, 18), {
                        icon: record.icon || 'bar-chart',
                        color: key === model.report ? 'action' : 'secondaryText'
                    }),
                    label(
                        'workReportTypeTitle',
                        rect(34, 5, Math.max(0, width - 42), 22),
                        translate(
                            titles[key] || record.title || record.label,
                            language
                        ),
                        { weight: 600 }
                    ),
                    label(
                        'workReportTypeDescription',
                        rect(34, 28, Math.max(0, width - 42), 18),
                        translate(
                            descriptions[key] || record.description || '',
                            language
                        ),
                        { fontRole: 'caption', color: 'secondaryText' }
                    )
                ]
            })
        ]
    };
}

export function valueRow(record, width, language) {
    const tr = (text) => translate(text, language),
        name = record.localized ? tr(record.label) : record.label;
    const labelWidth = Math.min(180, width * 0.34),
        barX = 20 + labelWidth,
        barWidth = Math.max(0, width - barX - 90);
    const share = Math.max(0, Math.min(1, Number(record.share) || 0));
    return {
        nodes: [
            node('Box', 'workReportValueSurface', rect(0, 0, width, 52), {
                background: 'surfaceContainerLow',
                radius: 8
            }),
            label(
                'workReportValueLabel',
                rect(10, 12, labelWidth, 28),
                name || ''
            ),
            node('Box', 'workReportValueTrack', rect(barX, 23, barWidth, 6), {
                background: 'surfaceContainerHighest',
                radius: 3
            }),
            node(
                'Box',
                'workReportValueFill',
                rect(barX, 23, barWidth * share, 6),
                { background: 'action', radius: 3 }
            ),
            label(
                'workReportValueNumber',
                rect(Math.max(0, width - 80), 12, 70, 28),
                String(record.valueLabel || '').replace(/ h$/, tr(' h')),
                { weight: 600, align: 'right' }
            )
        ]
    };
}

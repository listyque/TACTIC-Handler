import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { type, value } from '../administration/layouts/page.data.mjs';
import { buttonWidth } from '../../controls/buttons/metrics.mjs';

export function initial(definitions = []) {
    const result = {};
    for (const item of definitions || [])
        result[item.name] = {
            enabled: item.enabled,
            value: item.value ?? null
        };
    return result;
}
export function change(draft, event) {
    const result = Object.assign({}, draft);
    result[event.name] = Object.assign({}, draft[event.name]);
    result[event.name][event.field] = event.value;
    return result;
}
export function values(definitions, draft) {
    const result = {};
    for (const item of definitions) {
        const row = draft[item.name] || item;
        const raw =
            row.enabled && item.value != null
                ? value({ dataType: item.dataType }, row.value)
                : row.value;
        result[item.name] = { enabled: row.enabled, value: raw ?? null };
    }
    return result;
}
export function describe(definitions, draft, width, language, enabled = true) {
    if (!definitions?.length) return { height: 0, nodes: [] };
    const tr = (text) => translate(text, language),
        nodes = [],
        gap = 12;
    const columns = Math.max(1, Math.floor((width + gap) / 240)),
        size = (width - gap * (columns - 1)) / columns;
    definitions.forEach((item, index) => {
        const x = (index % columns) * (size + gap),
            y = Math.floor(index / columns) * 76,
            row = draft[item.name] || item;
        nodes.push(
            node(
                'CheckBox',
                'pageRuntime_' + item.name + '_enabled',
                rect(x, y, 24, 24),
                {
                    checked: row.enabled,
                    enabled,
                    label: item.title,
                    action: {
                        type: 'page-filter',
                        name: item.name,
                        field: 'enabled'
                    }
                }
            )
        );
        nodes.push(
            label(
                'pageRuntime_' + item.name + '_title',
                rect(x + 30, y, size - 30, 24),
                item.title,
                { weight: 600 }
            )
        );
        const action = { type: 'page-filter', name: item.name, field: 'value' },
            field = type({ dataType: item.dataType });
        if (item.value == null && ['=', '!='].includes(item.relation))
            nodes.push(
                label(
                    'pageRuntime_' + item.name + '_value',
                    rect(x + 30, y + 30, size - 30, 34),
                    tr(item.relation === '=' ? 'Is empty' : 'Is not empty'),
                    { color: 'secondaryText' }
                )
            );
        else
            nodes.push(
                node(
                    field === 'boolean'
                        ? 'Choice'
                        : field === 'date'
                          ? 'DateChoice'
                          : 'Field',
                    'pageRuntime_' + item.name + '_value',
                    rect(x, y + 30, size, 34),
                    {
                        label: item.title,
                        text: String(row.value ?? ''),
                        value: String(row.value),
                        enabled: enabled && row.enabled,
                        inputMode: field === 'number' ? 'decimal' : 'text',
                        includeTime: /time/i.test(item.dataType),
                        action,
                        options:
                            field === 'boolean'
                                ? [
                                      { value: 'true', label: tr('Yes') },
                                      { value: 'false', label: tr('No') }
                                  ]
                                : undefined
                    }
                )
            );
    });
    const y = Math.ceil(definitions.length / columns) * 76;
    const applyWidth = Math.min(
            width,
            buttonWidth(tr('Apply filters').length * 7, true)
        ),
        resetWidth = Math.min(
            width,
            buttonWidth(tr('Reset filters').length * 7, true)
        ),
        stacked = applyWidth + resetWidth + 8 > width;
    nodes.push(
        button(
            'pageRuntimeApply',
            rect(0, y, applyWidth, 32),
            tr('Apply filters'),
            'filter',
            { type: 'page-filter-apply' },
            enabled
        )
    );
    nodes.push(
        button(
            'pageRuntimeReset',
            rect(
                stacked ? 0 : applyWidth + 8,
                y + (stacked ? 40 : 0),
                resetWidth,
                32
            ),
            tr('Reset filters'),
            'restore',
            { type: 'page-filter-reset' },
            enabled
        )
    );
    return { height: y + (stacked ? 84 : 44), nodes };
}

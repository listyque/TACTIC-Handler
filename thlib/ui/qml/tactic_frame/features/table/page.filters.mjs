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
    const applyWidth = Math.min(
            width,
            buttonWidth(tr('Apply').length * 8, true)
        ),
        resetWidth = Math.min(width, buttonWidth(tr('Reset').length * 8, true)),
        actionsWidth = applyWidth + resetWidth + 8,
        inline = width >= definitions.length * 250 + actionsWidth + gap,
        fieldsWidth = inline ? width - actionsWidth - gap : width;
    const maximum = Math.max(1, Math.floor((fieldsWidth + gap) / 260)),
        columns = Math.ceil(
            definitions.length / Math.ceil(definitions.length / maximum)
        ),
        size = (fieldsWidth - gap * (columns - 1)) / columns;
    definitions.forEach((item, index) => {
        const x = (index % columns) * (size + gap),
            y = Math.floor(index / columns) * 44,
            row = draft[item.name] || item;
        nodes.push(
            node(
                'CheckBox',
                'pageRuntime_' + item.name + '_enabled',
                rect(x, y + 5, 24, 24),
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
                rect(x + 28, y, Math.min(88, size * 0.28), 34),
                item.title,
                { weight: 500, maxLines: 1 }
            )
        );
        const action = { type: 'page-filter', name: item.name, field: 'value' },
            field = type({ dataType: item.dataType });
        if (item.value == null && ['=', '!='].includes(item.relation))
            nodes.push(
                label(
                    'pageRuntime_' + item.name + '_value',
                    rect(x + 120, y, Math.max(0, size - 120), 34),
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
                    rect(x + 120, y, Math.max(0, size - 120), 34),
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
    const y = inline ? 1 : Math.ceil(definitions.length / columns) * 44;
    const actionX = inline ? width - actionsWidth : 0;
    const stacked = actionsWidth > width;
    nodes.push(
        button(
            'pageRuntimeApply',
            rect(actionX, y, applyWidth, 32),
            tr('Apply'),
            'filter',
            { type: 'page-filter-apply' },
            enabled
        )
    );
    nodes.push(
        button(
            'pageRuntimeReset',
            rect(
                stacked ? 0 : actionX + applyWidth + 8,
                y + (stacked ? 40 : 0),
                resetWidth,
                32
            ),
            tr('Reset'),
            'restore',
            { type: 'page-filter-reset' },
            enabled
        )
    );
    return { height: inline ? 40 : y + (stacked ? 84 : 40), nodes };
}

import { node, rect, button, label } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export function matching(records, query) {
    const text = query.trim().toLowerCase();
    return records
        .filter((row) => row.text.toLowerCase().includes(text))
        .map((row) => row.id);
}

export function trigger(query, language) {
    return {
        nodes: [
            button(
                'branchSearchToggle',
                rect(0, 0, 24, 24),
                translate('Search in this branch', language),
                'search',
                { type: 'open' },
                true,
                {
                    iconOnly: true,
                    iconSize: 15,
                    normalColor: 'transparent',
                    highlighted: !!query
                }
            )
        ]
    };
}

export function panel(model, width, language) {
    const tr = (text) => translate(text, language),
        nodes = [
            node('Field', 'branchSearchText', rect(8, 8, width - 48, 28), {
                text: model.query,
                label: tr('Search in this branch'),
                placeholder: tr('Search in this branch'),
                enabled: true,
                maxLength: 256,
                action: { type: 'change' },
                keys: { Escape: { type: 'close' }, Enter: { type: 'close' } }
            }),
            button(
                'branchSearchClear',
                rect(width - 36, 8, 28, 28),
                tr('Clear filter'),
                'close',
                { type: 'clear' },
                !!model.query,
                { iconOnly: true }
            )
        ];
    if (model.query)
        nodes.push(
            label(
                'branchSearchCount',
                rect(8, 40, width - 16, 20),
                model.busy
                    ? tr('Loading data…')
                    : model.count
                      ? tr('Found: {count}').replace(
                            '{count}',
                            String(model.count) + (model.more ? '+' : '')
                        )
                      : tr('No results found'),
                { color: 'secondaryText', fontRole: 'caption' }
            )
        );
    return { nodes };
}

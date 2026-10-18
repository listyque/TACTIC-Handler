import { node, rect, label, button } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';

export function describe(model, width, language) {
    const tr = (text) => translate(text, language);
    const nodes = [
        label(
            'journalTitle',
            rect(0, 0, Math.max(0, width - 74), 32),
            tr('Transaction XML'),
            { weight: 600 }
        ),
        button(
            'journalCopy',
            rect(Math.max(0, width - 67), 1, 30, 30),
            tr('Copy transaction XML'),
            'copy',
            { type: 'copy' },
            !model.busy && !!model.xml,
            { iconOnly: true }
        ),
        button(
            'journalRefresh',
            rect(Math.max(0, width - 30), 1, 30, 30),
            tr('Refresh transaction details'),
            'refresh',
            { type: 'load' },
            !model.busy,
            { iconOnly: true }
        )
    ];
    let top = 39;
    for (const entry of [
        ['journalBusy', model.busy ? tr('Loading data…') : '', 'secondaryText'],
        ['journalError', model.error ? tr(model.error) : '', 'error'],
        [
            'journalMessage',
            model.message ? tr(model.message) : '',
            'secondaryText'
        ],
        [
            'journalHidden',
            model.hidden
                ? tr(
                      '{count} journal operations are hidden by access rules.'
                  ).replace('{count}', model.hidden)
                : '',
            'secondaryText'
        ]
    ])
        if (entry[1]) {
            nodes.push(
                label(entry[0], rect(0, top, width, 40), entry[1], {
                    color: entry[2],
                    maxLines: 2,
                    fontRole: 'caption',
                    role: entry[2] === 'error' ? 'alert' : 'status'
                })
            );
            top += 44;
        }
    if (model.error) {
        nodes.push(
            button(
                'journalRetry',
                rect(0, top, 100, 32),
                tr('Retry'),
                'refresh',
                { type: 'load' },
                !model.busy
            )
        );
        top += 39;
    }
    return { nodes, height: top };
}

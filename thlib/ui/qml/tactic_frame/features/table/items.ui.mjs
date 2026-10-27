import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

// Dashboard host geometry only. Item cards, branches and actions use the existing result surface.
export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language),
        status = model.error || (model.busy ? tr('Loading data…') : ''),
        top = status ? 36 : 0,
        footer = model.hasMore ? 40 : 0;
    const nodes = [
        node(
            'View',
            'dashboardItemResults',
            rect(0, top, width, Math.max(0, height - top - footer)),
            { view: 'itemResults' }
        )
    ];
    if (status)
        nodes.push(
            label(
                'dashboardItemStatus',
                rect(0, 0, Math.max(0, width - 40), 32),
                status,
                { color: model.error ? 'error' : 'secondaryText' }
            )
        );
    if (model.error)
        nodes.push(
            button(
                'dashboardItemRetry',
                rect(width - 36, 0, 32, 32),
                tr('Retry'),
                'refresh',
                { type: 'reload' },
                !model.busy,
                { iconOnly: true }
            )
        );
    if (model.hasMore)
        nodes.push(
            button(
                'dashboardItemMore',
                rect(0, height - 36, 140, 32),
                tr('Load more'),
                'chevron-down',
                { type: 'more' },
                !model.busy
            )
        );
    return { nodes };
}

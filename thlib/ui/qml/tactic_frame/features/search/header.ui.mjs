import { node, rect, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { spacing } from '../../core/foundation.mjs';

export const height = 48;

export function describe(model, width, language) {
    const text = (key) => translate(key, language),
        compact = !!model.compact,
        nodes = [];
    let right = width - spacing.compact;
    const view = (id, name, show) => {
        if (show) right -= 38;
        nodes.push(
            node('View', id, rect(right, 5, 38, 38), {
                view: name,
                visible: show
            })
        );
        if (show) right -= spacing.tight;
    };
    view('searchHeaderPanels', 'panels', model.panels !== false);
    if (!compact) right -= 38;
    nodes.push(
        button(
            'searchWorkspaceHelpButton',
            rect(right, 5, 38, 38),
            text('Search help'),
            'help',
            { type: 'help' },
            true,
            { iconOnly: true, visible: !compact }
        )
    );
    if (!compact) right -= spacing.tight;
    view(
        'searchHeaderQuick',
        'quick',
        model.quick !== false && (!compact || !model.collapseSearch)
    );
    view('searchHeaderTags', 'tags', !compact && model.tags !== false);
    right -= !compact && model.shelf !== false ? 38 : 0;
    nodes.push(
        button(
            'scriptShelfButton',
            rect(right, 5, 38, 38),
            text('Script shelf'),
            'code',
            { type: 'shelf' },
            true,
            {
                iconOnly: true,
                visible: !compact && model.shelf !== false,
                iconAction: true,
                round: true,
                iconColor: model.shelfOpen ? 'action' : 'secondaryText'
            }
        )
    );
    if (!compact && model.shelf !== false) right -= spacing.tight;
    const refreshLeft = model.reserveGrip === false ? spacing.compact : 38;
    const left = refreshLeft + 38 + spacing.tight;
    nodes.push(
        node(
            'View',
            'searchHeaderField',
            rect(left, 5, right - left - spacing.compact, 38),
            {
                view: 'field',
                visible: !compact || !model.collapseSearch || !!model.searchOpen
            }
        )
    );
    nodes.push(
        button(
            'searchRefreshButton',
            rect(refreshLeft, 5, 38, 38),
            text('Refresh'),
            'refresh',
            { type: 'refresh' },
            !model.busy,
            {
                iconOnly: true,
                visible: !compact || !model.collapseSearch || !!model.searchOpen
            }
        )
    );
    return { nodes };
}

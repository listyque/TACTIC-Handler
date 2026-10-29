import { node, rect, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export const height = 48;

export function describe(model, width, language) {
    const text = (key) => translate(key, language),
        compact = !!model.compact,
        nodes = [];
    let right = width - 7;
    const view = (id, name, show) => {
        if (show) right -= 38;
        nodes.push(
            node('View', id, rect(right, 5, 38, 38), {
                view: name,
                visible: show
            })
        );
        if (show) right -= 3;
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
    if (!compact) right -= 3;
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
    if (!compact && model.shelf !== false) right -= 3;
    const refreshLeft = model.reserveGrip === false ? 8 : 38;
    const left = refreshLeft + 42;
    nodes.push(
        node('View', 'searchHeaderField', rect(left, 5, right - left - 8, 38), {
            view: 'field',
            visible: !compact || !model.collapseSearch || !!model.searchOpen
        })
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

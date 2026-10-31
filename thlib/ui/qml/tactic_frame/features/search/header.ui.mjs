import { node, rect, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { spacing } from '../../core/foundation.mjs';

export const height = 48;

export function quickBudget(model, width) {
    if (model.compact || model.quick === false || width < 1000) return 0;
    const actions = [model.panels, true, model.tags, model.shelf].filter(
        (visible) => visible !== false
    ).length;
    const left = (model.reserveGrip === false ? spacing.compact : 38) + 44;
    return Math.max(
        0,
        width -
            left -
            actions * 44 -
            54 -
            Math.max(360, Math.min(640, width * 0.42))
    );
}

export function quickLabel(group, language) {
    const names = {
        status: 'Status',
        assigned: 'Assignee',
        process: 'Process'
    };
    const title =
        group.source === 'task'
            ? translate(names[group.key] || group.title, language)
            : group.title;
    return title + (group.count ? ' · ' + group.count : '');
}

export function quickStrip(groups, budget, language) {
    const nodes = [];
    let left = 0;
    for (const group of groups.slice(0, 3)) {
        const width = Math.max(104, Math.ceil(group.textWidth) + 56);
        if (left + width + spacing.tight > budget) break;
        nodes.push(
            button(
                'searchQuickGroup_' + group.key,
                rect(left, 0, width, 38),
                quickLabel(group, language),
                'expand-more',
                { type: 'quickGroup', key: group.key },
                !group.disabled,
                { iconAtEnd: true, tonal: !!group.count }
            )
        );
        left += width + spacing.tight;
    }
    return { nodes, width: left + 38, contentHeight: 38 };
}

export function describe(model, width, language) {
    const text = (key) => translate(key, language),
        compact = !!model.compact,
        nodes = [];
    let right = width - spacing.compact;
    const view = (id, name, show, extent = 38) => {
        if (show) right -= extent;
        nodes.push(
            node('View', id, rect(right, 5, extent, 38), {
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
            { iconOnly: true, round: true, visible: !compact }
        )
    );
    if (!compact) right -= spacing.tight;
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
    view(
        'searchHeaderQuick',
        'quick',
        model.quick !== false && (!compact || !model.collapseSearch),
        compact ? 38 : model.quickWidth || 38
    );
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
                round: true,
                visible: !compact || !model.collapseSearch || !!model.searchOpen
            }
        )
    );
    return { nodes };
}

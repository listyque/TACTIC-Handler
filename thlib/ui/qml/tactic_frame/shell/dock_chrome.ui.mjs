import { node, rect } from '../core/frame.mjs';
import { layout } from '../core/foundation.mjs';

export const dimensions = {
    actionExtent: 30,
    actionIcon: 14,
    gripHeight: 34,
    spacing: 8,
    leftInset: 12,
    rightInset: 6,
    iconExtent: 16,
    surfaceInset: 5,
    floatingSurfaceInset: 6,
    surfaceBorder: 1
};

export function describe(model) {
    const width = Math.max(0, model.width);
    const capabilities = model.capabilities || {};
    const stacked = model.stackSize > 1;
    const results = model.kind === 'results';
    const ownChrome =
        (results && !(model.floating && capabilities.floatingResultsTitle)) ||
        (model.kind === 'commit_queue' && capabilities.queueOwnChrome);
    const height = !stacked && ownChrome ? 0 : layout.dockTitleHeight;
    const resultsActions = !results || capabilities.resultsActions;
    const actions = [
        ['dockGrip', !!resultsActions, dimensions.gripHeight],
        ['dockHelp', !!resultsActions, dimensions.actionExtent],
        [
            'dockMaximize',
            !!resultsActions && !!capabilities.maximize,
            dimensions.actionExtent
        ],
        [
            'dockPosition',
            !!resultsActions && !!capabilities.positionMenu,
            dimensions.actionExtent
        ],
        [
            'dockDetach',
            !!resultsActions && !!capabilities.separateWindow,
            dimensions.actionExtent
        ],
        ['dockClose', !!model.closable, dimensions.actionExtent]
    ];
    const actionCount = actions.filter((item) => item[1]).length;
    const actionsWidth =
        actionCount * dimensions.actionExtent +
        Math.max(0, actionCount - 1) * dimensions.spacing;
    let position = Math.max(0, width - dimensions.rightInset - actionsWidth);
    const titleRight = position - (actionCount ? dimensions.spacing : 0);
    const titleLeft =
        dimensions.leftInset + dimensions.iconExtent + dimensions.spacing;
    const tabsLeft = model.leadingStackInset || dimensions.rightInset;
    const nodes = [
        node(
            'View',
            'dockIcon',
            rect(
                dimensions.leftInset,
                (height - dimensions.iconExtent) / 2,
                dimensions.iconExtent,
                dimensions.iconExtent
            ),
            { view: 'icon', visible: !stacked }
        ),
        node(
            'View',
            'dockTitle',
            rect(titleLeft, 0, Math.max(0, titleRight - titleLeft), height),
            { view: 'title', visible: !stacked }
        ),
        node(
            'View',
            'dockTabs',
            rect(tabsLeft, 0, Math.max(0, titleRight - tabsLeft), height),
            { view: 'tabs', visible: stacked }
        )
    ];
    for (const [id, visible, itemHeight] of actions) {
        nodes.push(
            node(
                'View',
                id,
                rect(
                    position,
                    (height - itemHeight) / 2,
                    dimensions.actionExtent,
                    itemHeight
                ),
                { view: id.slice(4), visible }
            )
        );
        if (visible) position += dimensions.actionExtent + dimensions.spacing;
    }
    return { width, height, nodes, dimensions };
}

export function positions(scene) {
    const result = {};
    for (const item of scene.nodes) result[item.id] = item;
    return result;
}

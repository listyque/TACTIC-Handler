import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export const metrics = {
    cardHeight: 119,
    cardPitch: 126,
    columnMinimum: 224,
    compactHeight: 44,
    gap: 7,
    compactGap: 5,
    inset: 6
};

export function columns(width) {
    return Math.max(1, Math.floor(width / metrics.columnMinimum));
}

export function minimumWidth(model) {
    return 442 + (model.dirty ? 70 : 0);
}

export function describe(model, width, mode, language) {
    const tr = (text) => translate(text, language);
    const compact = mode === 'compact';
    const height = compact ? metrics.compactHeight : metrics.cardHeight;
    const nodes = [
        node('Box', 'taskProcessSurface', rect(0, 0, width, height), {
            background:
                compact || model.hasTask
                    ? 'surfaceContainer'
                    : 'surfaceContainerLow',
            radiusRole: compact ? 'itemRadius' : 'surfaceRadius',
            border: model.dirty ? 'action' : undefined
        }),
        node(
            'Box',
            'taskProcessRail',
            rect(0, compact ? 6 : 0, 3, compact ? height - 12 : height),
            {
                background: model.color || 'action',
                radius: 1.5
            }
        ),
        node(
            'Box',
            'taskProcessDot',
            rect(
                compact ? 11 : 10,
                compact ? 16.5 : 18,
                compact ? 11 : 12,
                compact ? 11 : 12
            ),
            {
                background: model.color || 'action',
                radius: 6
            }
        )
    ];
    const actions = [];
    if (model.dirty)
        actions.push(
            ['discard', 'Reset task changes', 'undo', 28],
            [
                'save',
                model.hasTask ? 'Save task changes' : 'Create task',
                'save',
                28
            ]
        );
    actions.push(
        ['notes', 'Task notes', 'comment', 30],
        ['menu', 'Task actions', 'more', 28]
    );
    const gap = compact ? 7 : 5;
    const actionsWidth =
        actions.reduce((sum, action) => sum + action[3], 0) +
        (actions.length - 1) * gap;
    const actionLeft = width - (compact ? 7 : 8) - actionsWidth;
    let x = actionLeft;
    for (const [type, title, icon, extent] of actions) {
        nodes.push(
            button(
                'taskProcess_' + type,
                rect(x, compact ? (height - extent) / 2 : 8, extent, extent),
                tr(title),
                icon,
                { type },
                !model.blocked &&
                    (type !== 'notes' ||
                        (model.hasTarget !== false && !model.deleting)),
                {
                    iconOnly: true,
                    iconAction: true,
                    iconSize: 17,
                    badgeCount: type === 'notes' ? model.notes || 0 : 0,
                    iconColor:
                        type === 'save' || (type === 'notes' && model.notes)
                            ? 'action'
                            : 'primaryText'
                }
            )
        );
        x += extent + gap;
    }
    nodes.push(
        label(
            'taskProcessTitle',
            rect(
                compact ? 29 : 27,
                compact ? 12 : 14,
                compact ? 100 : Math.max(0, actionLeft - 32),
                20
            ),
            model.label + (model.count > 1 ? ' | ' + model.count : ''),
            {
                fontRole: compact ? 'body' : 'bodyLarge',
                weight: 600
            }
        )
    );
    const statusX = compact ? 136 : 10,
        userX = compact ? 255 : 10;
    nodes.push(
        node(
            'View',
            'taskProcessStatus',
            rect(
                statusX,
                compact ? 7.5 : 47,
                compact ? 112 : width - 18,
                compact ? 29 : 28
            ),
            { view: 'status' }
        ),
        node(
            'View',
            'taskProcessAssignee',
            rect(
                userX,
                compact ? 7.5 : 82,
                compact ? Math.max(0, actionLeft - 7 - userX) : width - 18,
                compact ? 29 : 28
            ),
            { view: 'assigned' }
        )
    );
    return { nodes, height };
}

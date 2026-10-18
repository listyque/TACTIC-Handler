import { node, rect, label } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { fontMetricHeight, lineHeights } from '../../core/foundation.mjs';

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language);
    const title = model.busy
        ? 'Loading data…'
        : model.filtered
          ? 'No tasks match the current filters'
          : 'Create a task';
    const hint = model.filtered
        ? 'Clear filters to see all tasks'
        : model.canCreate
          ? 'Use the + button above'
          : 'Select a parent object before creating a task.';
    const titleWrap = width < 520 && model.filtered;
    const hintWrap = width < 520 && (model.filtered || !model.canCreate);
    const titleHeight = titleWrap
            ? lineHeights.bodyLarge * 2
            : fontMetricHeight(14),
        hintHeight = hintWrap
            ? lineHeights.secondary * 2
            : fontMetricHeight(12);
    const blockHeight = titleHeight + (model.busy ? 0 : 6 + hintHeight);
    const y = (height - blockHeight) / 2;
    const messageWidth = Math.min(width - 40, 240);
    const nodes = [
        node(
            'Box',
            'taskWorkspaceEmptyMessageBlock',
            rect((width - messageWidth) / 2, y, messageWidth, blockHeight)
        ),
        label(
            'taskWorkspaceEmptyTitle',
            rect(20, y, width - 40, titleHeight),
            tr(title),
            {
                fontRole: 'bodyLarge',
                weight: 600,
                align: 'center',
                wrap: !!titleWrap
            }
        )
    ];
    if (!model.busy)
        nodes.push(
            label(
                'taskWorkspaceEmptyHint',
                rect(20, y + titleHeight + 6, width - 40, hintHeight),
                tr(hint),
                {
                    fontRole: 'secondary',
                    color: 'secondaryText',
                    align: 'center',
                    wrap: !!hintWrap
                }
            )
        );
    if (!model.busy && !model.filtered && model.canCreate && model.target) {
        const sourceX = (width - messageWidth) / 2 - 18;
        const sourceY = y + blockHeight / 2 + 8;
        const targetX = model.target.x,
            targetY = model.target.y;
        const dx = Math.max(1, sourceX - targetX),
            dy = Math.max(1, sourceY - targetY);
        const first = [
            sourceX - Math.max(34, dx * 0.28),
            sourceY - Math.max(24, dy * 0.12)
        ];
        const second = [
            targetX + Math.max(32, dx * 0.2),
            targetY + Math.max(48, dy * 0.3)
        ];
        const angle = Math.atan2(targetY - second[1], targetX - second[0]);
        const tips = [-0.52, 0.52].map((spread) => [
            targetX - 13 * Math.cos(angle + spread),
            targetY - 13 * Math.sin(angle + spread)
        ]);
        const top = Math.min(0, targetY - 16);
        nodes.push(
            node(
                'View',
                'taskWorkspaceEmptyArrow',
                rect(
                    0,
                    top,
                    Math.min(width, Math.max(sourceX, targetX) + 48),
                    Math.min(
                        height - top,
                        Math.max(sourceY, targetY) - top + 52
                    )
                ),
                {
                    view: 'arrow',
                    source: [sourceX, sourceY],
                    first,
                    second,
                    target: [targetX, targetY],
                    tips
                }
            )
        );
    }
    return { height, nodes };
}

import { node, rect, label } from '../../core/frame.mjs';

export const dimensions = {
    railWidth: 48,
    rowHeight: 42,
    rowSpacing: 3,
    revealDelay: 350,
    dragThreshold: 10
};

export function tab(width, height, record, state = {}) {
    const selected = !!record.current,
        color = selected ? 'action' : 'secondaryText';
    const textWidth = Math.max(
        0,
        width - (record.closable ? 58 : 24) - (record.icon ? 24 : 0)
    );
    const nodes = [
        node('Box', 'workspaceTabOverlay', rect(0, 0, width, height), {
            background: selected ? 'action' : 'primaryText',
            opacity: state.pressed
                ? 0.12
                : state.hovered || state.focused
                  ? 0.08
                  : 0
        }),
        node(
            'Box',
            'workspaceTabSelectionIndicator',
            rect(
                selected ? 12 : width / 2,
                height - 3,
                selected ? Math.max(0, width - 24) : 0,
                3
            ),
            {
                background: 'action',
                radius: 1.5,
                opacity: selected && record.indicatorVisible !== false ? 1 : 0
            }
        ),
        label(
            'workspaceTabSelectionLabel',
            rect((width - textWidth) / 2, (height - 19) / 2 - 1, textWidth, 19),
            record.title,
            { fontRole: 'bodyLarge', weight: 400, color, align: 'center' }
        )
    ];
    if (record.icon)
        nodes.push(
            node(
                'Icon',
                'workspaceTabIcon',
                rect(10, (height - 18) / 2, 18, 18),
                { icon: record.icon, color }
            )
        );
    if (record.dirty)
        nodes.push(
            node('Box', 'workspaceTabDirty', rect(10, (height - 6) / 2, 6, 6), {
                background: 'yellow',
                radius: 3
            })
        );
    if (record.closable) {
        const opacity = selected || state.hovered ? 1 : 0.58;
        nodes.push(
            node(
                'Box',
                'workspaceTabCloseSurface',
                rect(width - 34, (height - 28) / 2, 28, 28),
                {
                    background: selected ? 'action' : 'primaryText',
                    radius: 14,
                    opacity: state.closePressed
                        ? 0.12
                        : state.closeHovered
                          ? 0.08
                          : 0
                }
            ),
            node(
                'Icon',
                'workspaceTabCloseIcon',
                rect(width - 28, (height - 16) / 2, 16, 16),
                { icon: 'close', color, opacity }
            )
        );
    }
    for (const item of nodes) {
        if (
            item.id === 'workspaceTabSelectionIndicator' &&
            state.animateSelection !== false
        )
            item.motion = {
                x: 'clickMotionSlow',
                width: 'clickMotionSlow',
                opacity: 'clickMotionFast'
            };
        else if (
            item.id === 'workspaceTabSelectionLabel' &&
            state.animateSelection !== false
        )
            item.motion = { color: 'clickMotionFast' };
        else if (
            item.id === 'workspaceTabOverlay' ||
            item.id === 'workspaceTabCloseSurface'
        )
            item.motion = {
                opacity:
                    state.pressed || state.closePressed
                        ? 'clickMotionFast'
                        : 'hoverMotionFast'
            };
        else if (
            item.id === 'workspaceTabCloseIcon' &&
            state.animateSelection !== false
        )
            item.motion = { opacity: 'hoverMotionFast' };
    }
    return { width, height, nodes };
}

export function sectionWidth(labelWidth, available = 320) {
    return Math.min(available, 320, Math.max(260, labelWidth + 112));
}

// Input adapters retain focus/grabs and execute these decisions through the owner.
export function key(tabs, id, pressed, vertical = false, reorder = false) {
    const index = tabs.findIndex((tab) => tab.id === id);
    if (index < 0) return null;
    const before = vertical ? 'ArrowUp' : 'ArrowLeft',
        after = vertical ? 'ArrowDown' : 'ArrowRight';
    if (reorder && (pressed === before || pressed === after)) {
        const target = index + (pressed === before ? -1 : 1);
        return target < 0 || target >= tabs.length
            ? null
            : { type: 'reorder', source: index, target };
    }
    if (pressed === 'Delete')
        return tabs[index].closable === false ? null : { type: 'close', id };
    let target = index;
    if (pressed === before) target = (index + tabs.length - 1) % tabs.length;
    else if (pressed === after) target = (index + 1) % tabs.length;
    else if (pressed === 'Home') target = 0;
    else if (pressed === 'End') target = tabs.length - 1;
    else return null;
    return { type: 'select', id: tabs[target].id };
}

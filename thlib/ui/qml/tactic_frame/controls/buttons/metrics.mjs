import { controls } from '../../core/foundation.mjs';

// Hosts supply native font advances; padding and icon geometry stay shared.
export function buttonWidth(advance, icon = false) {
    const metrics = controls.button;
    return Math.max(
        metrics.minimumWidth,
        Math.ceil(advance) +
            metrics.padding +
            (icon
                ? metrics.iconPadding + metrics.iconSize + metrics.spacing
                : metrics.padding)
    );
}

export function actionLayout(actions, width, measuredWidths = []) {
    const widths = actions.map((action, index) =>
        Math.min(
            width,
            measuredWidths[index] ||
                buttonWidth(action.text.length * 7, !!action.icon)
        )
    );
    const total =
            widths.reduce((sum, value) => sum + value, 0) +
            Math.max(0, widths.length - 1) * 8,
        stacked = total > width;
    let x = Math.max(0, width - total);
    const positions = widths.map((item, index) => {
        const bounds = {
            x: stacked ? width - item : x,
            y: stacked ? index * 44 : 0,
            width: item,
            height: 38
        };
        x += item + 8;
        return bounds;
    });
    return {
        widths,
        total,
        stacked,
        height: (stacked ? actions.length : 1) * 44,
        positions
    };
}

import {
    controls,
    textStyles,
    fontLineHeight
} from '../../core/foundation.mjs';

export function filterGeometry(emphasis = 0) {
    const value = Number(emphasis);
    const amount = isFinite(value) ? Math.max(0, Math.min(1, value)) : 0;
    const metrics = controls.filterChip;
    const fontSize =
        textStyles.body + Math.round(amount * metrics.emphasisFontSize);
    return {
        height: metrics.height + Math.round(amount * metrics.emphasisHeight),
        iconSize:
            metrics.iconSize + Math.round(amount * metrics.emphasisIconSize),
        fontSize,
        lineHeight: fontLineHeight(fontSize)
    };
}

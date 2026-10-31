import { spacing } from '../../core/foundation.mjs';
import { rect } from '../../core/frame.mjs';
export const metrics = {
    minimum: 44,
    maximum: 124,
    paddingTop: 8,
    paddingBottom: 8,
    paddingLeft: 12,
    paddingRight: 42,
    inset: 2,
    emoji: 28,
    emojiRight: 7,
    gap: spacing.compact,
    compactBreakpoint: 620,
    sendWidth: 92,
    sendSize: 38
};
export function field(contentHeight) {
    return Math.min(
        metrics.maximum,
        Math.max(
            metrics.minimum,
            Math.ceil(
                contentHeight +
                    metrics.paddingTop +
                    metrics.paddingBottom +
                    metrics.inset * 2
            )
        )
    );
}
export function layout(width, fieldHeight, iconOnly = false, phone = false) {
    const compact = iconOnly || phone || width < metrics.compactBreakpoint,
        gap = phone ? 4 : metrics.gap,
        sendWidth = compact ? metrics.sendSize : metrics.sendWidth,
        height = Math.max(metrics.minimum, fieldHeight);
    return {
        height,
        compact,
        field: rect(0, 0, Math.max(0, width - sendWidth - gap), height),
        send: rect(
            Math.max(0, width - sendWidth),
            (height - metrics.sendSize) / 2,
            sendWidth,
            metrics.sendSize
        )
    };
}

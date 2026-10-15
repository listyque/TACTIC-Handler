import { layout } from '../../core/foundation.mjs';

export const dockTab = {
    minimumWidth: 112,
    maximumWidth: 260,
    labelAllowance: 44,
    spacing: 2,
    dragThreshold: 8,
    selectedOpacity: 0.1,
    hoveredOpacity: 0.07,
    draggingOpacity: 0.14,
    indicatorThickness: 3,
    indicatorInset: 10,
    indicatorMinimum: 48
};

// Handler SearchWorkspaceView: preserve the active tab, compress its neighbors.
export function fitTabWidth(naturalWidth, current, layout) {
    const minimumTotal = layout.count * layout.minimum;
    if (
        layout.total <= layout.available ||
        layout.total <= minimumTotal ||
        current
    )
        return naturalWidth;
    const inactiveMinimum =
        (layout.count - layout.activeCount) * layout.minimum;
    const inactiveNatural = Math.max(
        inactiveMinimum,
        layout.total - layout.activeWidth
    );
    const remaining = layout.available - layout.activeWidth;
    if (remaining <= inactiveMinimum) return layout.minimum;
    const ratio =
        (remaining - inactiveMinimum) / (inactiveNatural - inactiveMinimum);
    return layout.minimum + (naturalWidth - layout.minimum) * ratio;
}

export function fitTabWidths(natural, current, available, minimum) {
    const layout = {
        available,
        minimum,
        total: natural.reduce((sum, width) => sum + width, 0),
        count: natural.length,
        activeWidth: natural[current] || 0,
        activeCount: current >= 0 ? 1 : 0
    };
    return natural.map((width, index) =>
        fitTabWidth(width, index === current, layout)
    );
}

// Handler DockPanel uses equal available shares, with a scrollable minimum.
export function dockTabWidth(labelWidth, available, count) {
    const natural = Math.min(
        dockTab.maximumWidth,
        Math.max(dockTab.minimumWidth, labelWidth + dockTab.labelAllowance)
    );
    return Math.max(
        dockTab.minimumWidth,
        Math.min(natural, available / Math.max(1, count))
    );
}

export function dockTabHeight(height, overflow) {
    return Math.max(0, height - (overflow ? layout.scrollbarExtent : 0));
}

export function displacedTabOffset(index, source, target, extent) {
    if (source < 0 || target < 0) return 0;
    if (source < target && index > source && index <= target) return -extent;
    if (source > target && index >= target && index < source) return extent;
    return 0;
}

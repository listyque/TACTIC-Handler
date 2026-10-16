// Neutral single-choice input; hosts keep real focus and dispatch.
export function selectable(option) {
    return option.enabled !== false && option.disabled !== true;
}

export function entry(options, value) {
    const selected = options.findIndex(
        (option) => selectable(option) && option.value === value
    );
    return selected >= 0 ? selected : options.findIndex(selectable);
}

export function target(options, value, key) {
    if (['ArrowLeft', 'ArrowRight', 'Home', 'End'].indexOf(key) < 0) return -1;
    const indices = options
        .map((option, index) => (selectable(option) ? index : -1))
        .filter((index) => index >= 0);
    if (!indices.length) return -1;
    if (key === 'Home') return indices[0];
    if (key === 'End') return indices[indices.length - 1];
    const current = indices.indexOf(
        options.findIndex((option) => option.value === value)
    );
    if (current < 0)
        return indices[key === 'ArrowLeft' ? indices.length - 1 : 0];
    return indices[
        (current + (key === 'ArrowRight' ? 1 : indices.length - 1)) %
            indices.length
    ];
}

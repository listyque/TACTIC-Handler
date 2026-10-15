// Geometry is shared; native window managers still own their OS decorations.
const finite = (value, fallback) => (Number.isFinite(value) ? value : fallback);

export function fit(rectangle, bounds, minimum, sizeMargin) {
    if (
        ![bounds.x, bounds.y, bounds.width, bounds.height].every(
            Number.isFinite
        ) ||
        bounds.width <= 0 ||
        bounds.height <= 0
    ) {
        throw Error(
            'Window bounds must be finite and have positive dimensions'
        );
    }
    const limit = minimum || { width: 1, height: 1 };
    const margin = Math.max(0, finite(sizeMargin, 0));
    const width = Math.max(
        limit.width,
        Math.min(
            finite(rectangle.width, 280),
            Math.max(1, bounds.width - margin)
        )
    );
    const height = Math.max(
        limit.height,
        Math.min(
            finite(rectangle.height, 180),
            Math.max(1, bounds.height - margin)
        )
    );
    return {
        x: Math.max(
            bounds.x,
            Math.min(
                finite(rectangle.x, bounds.x),
                bounds.x + bounds.width - width
            )
        ),
        y: Math.max(
            bounds.y,
            Math.min(
                finite(rectangle.y, bounds.y),
                bounds.y + bounds.height - height
            )
        ),
        width,
        height
    };
}

export function moved(rectangle, delta) {
    return Object.assign({}, rectangle, {
        x: rectangle.x + delta.x,
        y: rectangle.y + delta.y
    });
}

export function resized(rectangle, edge, delta, bounds, minimum) {
    if (
        [
            'left',
            'right',
            'top',
            'bottom',
            'top-left',
            'top-right',
            'bottom-left',
            'bottom-right'
        ].indexOf(edge) < 0
    ) {
        throw Error('Unknown window resize edge: ' + edge);
    }
    const result = Object.assign({}, rectangle);
    const minimumWidth = Math.min(minimum.width, bounds.width);
    const minimumHeight = Math.min(minimum.height, bounds.height);
    if (edge.indexOf('right') >= 0)
        result.width = Math.max(
            minimumWidth,
            Math.min(bounds.x + bounds.width - result.x, result.width + delta.x)
        );
    if (edge.indexOf('bottom') >= 0)
        result.height = Math.max(
            minimumHeight,
            Math.min(
                bounds.y + bounds.height - result.y,
                result.height + delta.y
            )
        );
    if (edge.indexOf('left') >= 0) {
        result.x = Math.max(
            bounds.x,
            Math.min(result.x + delta.x, result.x + result.width - minimumWidth)
        );
        result.width += rectangle.x - result.x;
    }
    if (edge.indexOf('top') >= 0) {
        result.y = Math.max(
            bounds.y,
            Math.min(
                result.y + delta.y,
                result.y + result.height - minimumHeight
            )
        );
        result.height += rectangle.y - result.y;
    }
    return result;
}

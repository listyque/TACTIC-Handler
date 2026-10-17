// Port of Handler SearchTableColumnLayout.js.
export function baseWidth(column, overrides) {
    const name = String(column.name || '');
    const override = overrides ? overrides[name] : undefined;
    return Math.max(
        48,
        Math.min(
            640,
            Number(override !== undefined ? override : column.width || 160)
        )
    );
}

export function resolvedWidth(column, overrides, fittedWidths) {
    const fitted = fittedWidths[String(column.name || '')];
    return fitted !== undefined ? Number(fitted) : baseWidth(column, overrides);
}

export function hasKind(columns, kind) {
    return columns.some(function (column) {
        return String(column.kind || '') === kind;
    });
}

export function widthForKind(columns, kind, overrides, fittedWidths) {
    for (let index = 0; index < columns.length; ++index) {
        if (String(columns[index].kind || '') === kind)
            return resolvedWidth(columns[index], overrides, fittedWidths);
    }
    return 0;
}

export function totalWidth(columns, overrides, fittedWidths) {
    return columns.reduce(function (total, column) {
        return total + resolvedWidth(column, overrides, fittedWidths);
    }, 0);
}

export function hideOrder(column, index, count) {
    if (column.hideOrder !== undefined && column.hideOrder !== null)
        return Math.max(0, Number(column.hideOrder) || 0);
    const name = String(column.name || '');
    return ['code', 'name', 'title'].indexOf(name) >= 0
        ? 0
        : Math.max(1, count - index);
}

export function visibleColumns(columns, availableWidth, overrides) {
    const source = Array.prototype.slice.call(columns || []);
    let total = 0;
    const candidates = [];
    for (let index = 0; index < source.length; ++index) {
        total += baseWidth(source[index], overrides);
        const order = hideOrder(source[index], index, source.length);
        if (order > 0) candidates.push({ index: index, order: order });
    }
    candidates.sort(function (left, right) {
        return left.order - right.order || right.index - left.index;
    });
    const retained = source.map(function () {
        return true;
    });
    for (
        let index = 0;
        index < candidates.length && total > availableWidth;
        ++index
    ) {
        const sourceIndex = candidates[index].index;
        retained[sourceIndex] = false;
        total -= baseWidth(source[sourceIndex], overrides);
    }
    return source.filter(function (_column, index) {
        return retained[index];
    });
}

export function fittedWidths(columns, availableWidth, overrides) {
    const widths = [];
    let total = 0;
    for (let index = 0; index < columns.length; ++index) {
        const width = baseWidth(columns[index], overrides);
        widths.push(width);
        total += width;
    }
    if (!columns.length || availableWidth <= 0) return {};

    let remainingWidth = availableWidth;
    let remainingBase = total;
    let pending = widths.map(function (_width, index) {
        return index;
    });
    const result = {};
    while (pending.length) {
        const scale = remainingBase > 0 ? remainingWidth / remainingBase : 1;
        const next = [];
        let capped = false;
        for (let index = 0; index < pending.length; ++index) {
            const columnIndex = pending[index];
            const target = widths[columnIndex] * scale;
            if (target >= 48 && target <= 640) {
                next.push(columnIndex);
                continue;
            }
            const bounded = target < 48 ? 48 : 640;
            result[String(columns[columnIndex].name || '')] = bounded;
            remainingWidth -= bounded;
            remainingBase -= widths[columnIndex];
            capped = true;
        }
        if (!capped) {
            for (let index = 0; index < next.length; ++index) {
                const columnIndex = next[index];
                result[String(columns[columnIndex].name || '')] =
                    widths[columnIndex] * scale;
            }
            break;
        }
        pending = next;
    }
    return result;
}

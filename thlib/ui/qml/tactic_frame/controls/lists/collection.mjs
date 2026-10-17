// Geometry only. Owners retain selection, expansion, drafts and loaded records.
export function layout(items, width, options = {}) {
    const columns = Math.max(
            1,
            Math.floor(
                (width + (options.columnGap || 0)) /
                    ((options.cellWidth || width || 1) +
                        (options.columnGap || 0))
            )
        ),
        cellWidth = options.cellWidth
            ? Math.min(width, options.cellWidth)
            : width,
        rows = [],
        rowByKey = Object.create(null);
    let top = 0;
    for (let index = 0; index < items.length; index += columns) {
        const cells = items.slice(index, index + columns),
            height = Math.max(1, ...cells.map((item) => item.height));
        rows.push({
            top,
            height,
            entries: cells.map((item, column) => ({
                key: item.key,
                index: index + column,
                data: item.data,
                left: column * (cellWidth + (options.columnGap || 0)),
                width: cellWidth
            }))
        });
        for (const item of cells) rowByKey[item.key] = rows.length - 1;
        top += height + (options.rowGap || 0);
    }
    return {
        rows,
        rowByKey,
        height: rows.length ? top - (options.rowGap || 0) : 0
    };
}

export function range(rows, top, height, overscan = 240) {
    function firstAfter(value) {
        let low = 0,
            high = rows.length;
        while (low < high) {
            const middle = (low + high) >> 1;
            if (rows[middle].top + rows[middle].height < value)
                low = middle + 1;
            else high = middle;
        }
        return low;
    }
    return [
        firstAfter(top - overscan),
        Math.min(rows.length, firstAfter(top + height + overscan) + 1)
    ];
}

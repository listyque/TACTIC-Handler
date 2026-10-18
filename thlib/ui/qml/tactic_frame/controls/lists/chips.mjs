// TagCloudPopup.qml / QuickFilterOptions.qml row packing; views supply font metrics.
export function packTagRows(
    records,
    width,
    measure,
    allLabel,
    maximumChipWidth = 260,
    metrics = {}
) {
    if (!records.length || width <= 0) return [];
    const rows = [],
        gapSize = metrics.gap === undefined ? 8 : metrics.gap,
        rowHeight = metrics.rowHeight || 32;
    let row = { top: 0, height: 0, cells: [], width: 0 };
    for (
        let index = allLabel === undefined ? 0 : -1;
        index < records.length;
        index++
    ) {
        const record = records[index],
            emphasis = record?.weight || 0;
        const cellWidth = Math.min(
            maximumChipWidth,
            width,
            measure(record?.tag || allLabel, emphasis, record) + 24
        );
        const gap = row.cells.length ? gapSize : 0;
        if (row.cells.length && row.width + gap + cellWidth > width) {
            rows.push(row);
            row = {
                top: row.top + row.height + gapSize,
                height: 0,
                cells: [],
                width: 0
            };
        }
        row.width += (row.cells.length ? gapSize : 0) + cellWidth;
        row.height = Math.max(
            row.height,
            rowHeight + Math.round(emphasis * 12)
        );
        row.cells.push({ index, width: cellWidth });
    }
    if (row.cells.length) rows.push(row);
    return rows;
}

export function tagRowAt(rows, y) {
    let low = 0,
        high = rows.length;
    while (low < high) {
        const middle = Math.floor((low + high) / 2);
        if (rows[middle].top + rows[middle].height + 8 <= y) low = middle + 1;
        else high = middle;
    }
    return Math.min(low, Math.max(0, rows.length - 1));
}

import * as Columns from './columns.mjs';

// Native ListView and browser virtualization consume the same row/column skeleton.
export const metrics = {
    margin: 8,
    header: 37,
    selection: 40,
    actions: 64,
    group: 38,
    minimumColumn: 48,
    maximumColumn: 640,
    resizeHandle: 12,
    dragThreshold: 6,
    firstPadding: 14,
    padding: 10,
    heights: [52, 68, 84]
};

export const paint = {
    header: 'surfaceContainer',
    headerText: 'secondaryText',
    row: 'surfaceContainerLow',
    selected: 'contentSelection',
    group: 'surfaceContainerHigh'
};

export function describe(model, width) {
    const available = Math.max(0, width - metrics.selection - metrics.actions);
    const columns = Columns.visibleColumns(
        model.columns || [],
        available,
        model.overrides
    );
    const fitted = model.autoFit
        ? Columns.fittedWidths(columns, available, model.overrides)
        : {};
    const cells = [];
    let left = metrics.selection;
    for (let index = 0; index < columns.length; index++) {
        const column = columns[index];
        const extent = Columns.resolvedWidth(column, model.overrides, fitted);
        cells.push({
            name: column.name,
            x: left,
            width: extent,
            padding: index === 0 ? metrics.firstPadding : metrics.padding
        });
        left += extent;
    }
    return {
        columns,
        cells,
        fitted,
        width: Math.max(width, left + metrics.actions),
        rowHeight: model.automaticRowHeight
            ? Math.max(
                  model.rowHeight || 58,
                  Columns.widthForKind(
                      columns,
                      'thumbnail',
                      model.overrides,
                      fitted
                  )
              )
            : model.rowHeight || 58
    };
}

export function boundedWidth(width) {
    return Math.max(
        metrics.minimumColumn,
        Math.min(metrics.maximumColumn, width)
    );
}

export function dropIndex(cells, contentX) {
    for (let index = 0; index < cells.length; index++) {
        if (contentX < cells[index].x + cells[index].width / 2) return index;
    }
    return Math.max(0, cells.length - 1);
}

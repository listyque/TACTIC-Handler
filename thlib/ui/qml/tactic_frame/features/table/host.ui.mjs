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
    header: 'tableHeader',
    headerText: 'primaryText',
    row: 'surfaceContainerLowest',
    alternateRow: 'tableAlternateRow',
    divider: 'tableDivider',
    selected: 'contentSelection',
    group: 'surfaceContainerHigh'
};

export function headerAction(column) {
    const className = column.resolvedClass || column.display?.handler || '';
    const options = column.displayOptions || column.display?.options || {};
    if (
        className.split('.').pop() === 'PublishTableElement' &&
        ![undefined, null, '', false, 'false'].includes(options.multi_publish)
    )
        return {
            type: 'publish',
            view: 'multi_publish',
            label: 'Multi Publish',
            icon: 'publish'
        };
    if (
        [
            'UpdateWdg',
            'pyasm.widget.UpdateWdg',
            'pyasm.widget.table_element_wdg.UpdateWdg'
        ].includes(className) &&
        ![false, 'false'].includes(options.insert)
    )
        return { type: 'insert', view: options.insert_view || 'insert' };
    return null;
}

function serviceHeight(columns) {
    return columns.reduce((height, column) => {
        const className = column.resolvedClass || column.display?.handler || '';
        const options = column.displayOptions || column.display?.options || {};
        if (
            className.split('.').pop() === 'GeneralPublishElementWdg' &&
            ![false, 'false'].includes(options.preview)
        )
            return Math.max(height, 98);
        if (className.split('.').pop() === 'SObjectSummaryElementWdg')
            return Math.max(height, 118);
        if (className.split('.').pop() !== 'SObjectConnectionElement')
            return height;
        return Math.max(
            height,
            Math.max(64, Number(options.icon_size) || 60) + 32
        );
    }, 0);
}

export function describe(model, width) {
    const available = Math.max(0, width - metrics.selection - metrics.actions);
    const columns =
        model.scrollColumns || model.autoFit
            ? model.columns || []
            : Columns.visibleColumns(
                  model.columns || [],
                  available,
                  model.overrides
              );
    const fitted =
        model.autoFit && !model.scrollColumns
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
                  serviceHeight(columns),
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

function numericCellValue(record, cell, field) {
    if (cell?.time && typeof cell.time.total === 'number')
        return cell.time.total;
    const raw = record?.[field] ?? cell?.text;
    if (raw === undefined || raw === null || raw === '') return null;
    const value = Number(String(raw).replace(/[^0-9.+-]/g, ''));
    return Number.isFinite(value) ? value : null;
}

export function summarize(columns, records, cells = {}, mode = 'bottom') {
    const values = {};
    let hasSummary = false;
    const list = records || [];
    for (const column of columns || []) {
        const className = (
            column.resolvedClass ||
            column.display?.handler ||
            ''
        )
            .split('.')
            .pop();
        const options = column.displayOptions || column.display?.options || {};
        const field = column.cell?.field || column.name;
        const summary =
            column.cell?.summary ||
            options.total_summary ||
            (['WorkHoursElementWdg', 'WeekTableElement'].includes(className)
                ? 'total'
                : '');
        const expression =
            mode === 'group_bottom'
                ? column.cell?.group_bottom || options.group_bottom || ''
                : column.cell?.bottom || options.bottom || '';
        const calc = expression
            ? /^\s*@COUNT\b/i.test(expression)
                ? 'count'
                : /^\s*@AVG\b/i.test(expression)
                  ? 'average'
                  : 'total'
            : summary;
        if (!['count', 'total', 'average'].includes(calc)) continue;
        hasSummary = true;
        if (calc === 'count') {
            values[column.name] = String(list.length);
            continue;
        }
        let total = 0;
        let count = 0;
        for (const record of list) {
            const key = record?.__search_key__ || record?.key || '';
            const rowCells = record?.cells || cells[key] || {};
            const number = numericCellValue(
                record?.record || record,
                rowCells[column.name],
                field
            );
            if (number !== null) {
                total += number;
                count += 1;
            }
        }
        if (calc === 'average') total = count ? total / count : 0;
        const rounded = Math.round(total * 100) / 100;
        values[column.name] = String(rounded);
    }
    return { hasSummary, values };
}

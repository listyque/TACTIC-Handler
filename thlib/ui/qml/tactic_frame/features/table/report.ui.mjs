import { node, rect, label } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import * as Chart from '../../controls/charts/chart.ui.mjs';

export function reports(document) {
    const result = {};
    function walk(items, prefix) {
        for (const [index, item] of (items || []).entries()) {
            const key = prefix + '_' + index;
            if (item.kind === 'summary') result[key] = item.report;
            walk(item.children, key);
        }
    }
    walk(document.layoutNodes, 'customLayout');
    walk(document.layoutDetail?.layoutNodes, 'customLayoutDetails');
    return result;
}
export function models(document) {
    const result = {};
    for (const [key, report] of Object.entries(reports(document)))
        result[key] = report.rows.map((row) =>
            report.columns.map((column) => ({ value: row[column.key] }))
        );
    return result;
}
export function cell(grid, value, row, column) {
    const data = grid.report.rows[row]?.[grid.report.columns[column].key];
    return {
        nodes: [
            label(
                grid.id + '_cell_' + row + '_' + column,
                rect(8, 0, grid.cellWidth - 16, grid.rowHeight),
                data == null ? '—' : String(data),
                {
                    align:
                        grid.report.columns[column].kind === 'measure'
                            ? 'right'
                            : 'left'
                }
            )
        ]
    };
}
export function describe(item, id, width, height, language) {
    const tr = (text) => translate(text, language),
        report = item.report,
        nodes = [];
    const bodyHeight = Math.max(40, height - 38 - (report.truncated ? 28 : 0));
    nodes.push(
        label(id + '_title', rect(0, 0, width, 28), item.text, {
            fontRole: 'title',
            weight: 600
        })
    );
    if (!report.rows.length)
        nodes.push(
            label(
                id + '_empty',
                rect(0, 38, width, 40),
                tr('No matching report data'),
                { color: 'secondaryText' }
            )
        );
    else if (item.kind === 'summary') {
        nodes.push(
            node('Grid', id + '_grid', rect(0, 36, width, bodyHeight), {
                report,
                source: id,
                caption: '',
                labelWidth: 0,
                headerHeight: 34,
                rowHeight: 32,
                cellWidth: Math.max(
                    140,
                    Math.min(
                        240,
                        (width - 16) / Math.max(1, report.columns.length)
                    )
                ),
                rowHeaders: report.rows.map(() => ''),
                columnHeaders: report.columns.map((column) => column.title),
                text: item.text
            })
        );
    } else {
        const groups = report.columns.filter(
            (column) => column.kind === 'group'
        );
        const data = {
            type: item.chartType || item.chart_type || 'bar',
            values: report.rows.map((row) => row[report.measure]),
            labels: report.rows.map((row) =>
                groups.length
                    ? groups
                          .map((column) =>
                              row[column.key] == null
                                  ? tr('No value')
                                  : String(row[column.key])
                          )
                          .join(' · ')
                    : tr('Total')
            )
        };
        nodes.push(
            node('Box', id + '_chart', rect(0, 36, width, bodyHeight), {
                children: Chart.describe(data, id, width, bodyHeight, language)
                    .nodes
            })
        );
    }

    if (report.truncated)
        nodes.push(
            label(
                id + '_truncated',
                rect(0, height - 26, width, 26),
                tr(
                    'Group limit reached. Refine filters or increase the limit.'
                ),
                { color: 'secondaryText', maxLines: 1 }
            )
        );
    return { nodes };
}

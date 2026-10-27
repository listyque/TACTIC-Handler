import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { metrics, paint } from './host.ui.mjs';

export const height = 320;
export const rowHeight = 68;

export function quickLayout(model, width) {
    const columns = Math.max(1, Math.floor(Math.max(0, width - 16) / 180));
    const rows = Math.ceil((model.simpleFilters || []).length / columns);
    return { columns, height: rows * 66 };
}

export function identity(scope = {}, project = '') {
    return JSON.stringify([
        scope.projectCode || project,
        scope.searchType,
        scope.view || 'table',
        scope.parentKey,
        scope.expression || ''
    ]);
}

export function rows(model) {
    return (model.rows || []).map((record) =>
        Object.assign({}, record, {
            detailOpen: !!model.children?.[record.key]?.open,
            extent:
                rowHeight + (model.children?.[record.key]?.open ? height : 0)
        })
    );
}

export function columns(model) {
    let left = model.selection === false ? 0 : metrics.selection + 36;
    return (model.columns || []).map((column, index) => {
        const titleWidth = String(column.title || column.name).length * 8 + 20;
        const minimum = column.cell?.kind === 'text' ? 160 : 48;
        const width = Math.min(
            640,
            Math.max(
                minimum,
                titleWidth,
                Number.parseFloat(column.width) || 160
            )
        );
        const result = Object.assign({}, column, { index, x: left, width });
        left += width;
        return result;
    });
}

export function describe(model, width, extent, language) {
    const t = (value) => translate(value, language);
    const toolOffset = model.embedded ? 36 : 0;
    const quick = quickLayout(model, width),
        quickColumns = quick.columns,
        quickHeight = quick.height;
    const fields = columns(model);
    const contentWidth = Math.max(
        width - 16,
        (model.selection === false ? 0 : metrics.selection + 36) +
            fields.reduce((sum, field) => sum + field.width, 0) +
            40
    );
    const nodes = [
        node(
            'Field',
            'nestedFilter',
            rect(
                0,
                0,
                Math.max(0, width - (model.gear ? 156 : 120) + toolOffset),
                36
            ),
            {
                text: model.filter || '',
                placeholder: t('Filter'),
                action: { type: 'filter' }
            }
        ),
        button(
            'nestedReload',
            rect(
                Math.max(0, width - (model.gear ? 148 : 112) + toolOffset),
                0,
                32,
                32
            ),
            model.busy ? t('Loading data…') : t('Refresh'),
            model.busy ? 'loading' : 'refresh',
            { type: 'reload' },
            !model.busy,
            { iconOnly: true }
        ),
        button(
            'nestedColumns',
            rect(Math.max(0, width - 112 + toolOffset), 0, 32, 32),
            t('Columns'),
            'view-column',
            { type: 'columns' },
            !model.busy,
            { iconOnly: true }
        ),
        button(
            'nestedCreate',
            rect(Math.max(0, width - 76 + toolOffset), 0, 32, 32),
            t('Create'),
            'add',
            { type: 'create' },
            !model.busy && model.insert !== false,
            { iconOnly: true }
        ),
        button(
            'nestedClose',
            rect(Math.max(0, width - 40), 0, 32, 32),
            t('Close'),
            'close',
            { type: 'close' },
            true,
            { iconOnly: true }
        ),
        label(
            'nestedState',
            rect(0, extent - 32, Math.max(0, width - 120), 28),
            model.error ? t(model.error) : String((model.rows || []).length),
            { color: model.error ? 'error' : 'secondaryText' }
        ),
        button(
            'nestedClearSelection',
            rect(Math.max(0, width - 112), extent - 32, 32, 32),
            t('Clear selection'),
            'close',
            { type: 'clear-selection' },
            !!model.selected?.length,
            { iconOnly: true }
        ),
        button(
            'nestedPrevious',
            rect(Math.max(0, width - 76), extent - 32, 32, 32),
            t('Previous page'),
            'chevron-left',
            { type: 'page', value: -1 },
            !model.busy && model.offset > 0,
            { iconOnly: true }
        ),
        button(
            'nestedNext',
            rect(Math.max(0, width - 40), extent - 32, 32, 32),
            t('Next page'),
            'chevron-right',
            { type: 'page', value: 1 },
            !model.busy && !!model.hasNext,
            { iconOnly: true }
        )
    ];
    const children = [
        node(
            'Box',
            'nestedHeaderSurface',
            rect(0, 0, contentWidth, metrics.header),
            { background: paint.header, radius: 0 }
        )
    ];
    for (const field of fields) {
        children.push(
            field.sortable
                ? node(
                      'Action',
                      'nestedHeader_' + field.name,
                      rect(field.x, 0, field.width, metrics.header),
                      {
                          text: field.title || field.name,
                          action: { type: 'sort', value: field.name },
                          enabled: !model.busy,
                          children: [
                              label(
                                  'nestedHeaderText_' + field.name,
                                  rect(10, 0, field.width - 20, metrics.header),
                                  field.title || field.name,
                                  { color: paint.headerText }
                              )
                          ]
                      }
                  )
                : label(
                      'nestedHeader_' + field.name,
                      rect(field.x + 10, 0, field.width - 20, metrics.header),
                      field.title || field.name,
                      { color: paint.headerText }
                  )
        );
    }
    children.push(
        node(
            'List',
            'nestedRows',
            rect(
                0,
                metrics.header + 3,
                contentWidth,
                Math.max(0, extent - metrics.header - 86 - quickHeight)
            ),
            {
                source: 'rows',
                keyField: 'key',
                fields: [
                    'key',
                    'nodeId',
                    'record',
                    'cells',
                    'detailOpen',
                    'extent'
                ],
                rowHeight,
                rowHeightField: 'extent',
                rowGap: 0,
                label: t('Table View'),
                role: 'list'
            }
        )
    );
    nodes.push(
        node(
            'Scroll',
            'nestedHorizontal',
            rect(
                0,
                42 + quickHeight,
                width,
                Math.max(0, extent - 80 - quickHeight)
            ),
            {
                contentWidth,
                contentHeight: Math.max(0, extent - 96 - quickHeight),
                scrollbarId: 'nestedHorizontalBar',
                children
            }
        )
    );
    (model.simpleFilters || []).forEach((filter, index) => {
        const part = Math.max(0, (width - 24) / quickColumns),
            x = (index % quickColumns) * part,
            y = 42 + Math.floor(index / quickColumns) * 66;
        nodes.push(
            label(
                'nestedQuickLabel_' + filter.name,
                rect(x, y, Math.max(0, part - 8), 22),
                filter.title,
                { color: 'secondaryText' }
            )
        );
        nodes.push(
            node(
                'Choice',
                'nestedQuick_' + filter.name,
                rect(x, y + 24, Math.max(0, part - 8), 36),
                {
                    value: model.simpleValues?.[filter.name] || '',
                    options: [
                        { value: '', label: t('All') },
                        ...filter.options
                    ],
                    enabled: !model.busy,
                    action: { type: 'simple-filter', field: filter.name }
                }
            )
        );
    });
    return {
        nodes: nodes.filter((item) => {
            if (item.id === 'nestedClose' && model.embedded) return false;
            if (
                [
                    'nestedFilter',
                    'nestedReload',
                    'nestedColumns',
                    'nestedCreate'
                ].includes(item.id) &&
                model.shelf === false
            )
                return false;
            if (item.id === 'nestedColumns' && !model.gear) return false;
            if (item.id === 'nestedFilter' && model.search === false)
                return false;
            if (item.id === 'nestedCreate' && model.insert === false)
                return false;
            if (item.id === 'nestedClearSelection' && model.selection === false)
                return false;
            if (
                ['nestedPrevious', 'nestedNext'].includes(item.id) &&
                model.searchLimit === false
            )
                return false;
            return true;
        })
    };
}

export function row(model, record, language, viewportWidth = 0) {
    const fields = columns(model),
        nodes = [];
    const width = Math.max(
        viewportWidth,
        (model.selection === false ? 0 : metrics.selection + 36) +
            fields.reduce((sum, field) => sum + field.width, 0) +
            40
    );
    const selected = (model.selected || []).includes(record.key);
    nodes.push(
        node('Box', 'nestedRowSurface', rect(0, 0, width, rowHeight - 1), {
            background: selected ? paint.selected : paint.row,
            radius: 0
        })
    );
    if (model.selection !== false)
        nodes.push(
            node(
                'CheckBox',
                'nestedSelect',
                rect(6, (rowHeight - 28) / 2, 28, 28),
                {
                    checked: selected,
                    label: translate('Select row', language),
                    action: { type: 'select', key: record.key }
                }
            )
        );
    for (const field of fields)
        nodes.push(
            node(
                'View',
                'nestedCell_' + field.name,
                rect(field.x, 0, field.width, rowHeight - 1),
                {
                    view: 'tableCell',
                    weight: field.index === 0 ? 600 : 400,
                    column: field,
                    record: record.record,
                    cell: record.cells[field.name] || {
                        text: record.record[field.field || field.name] ?? ''
                    },
                    key: record.key,
                    nodeId: record.nodeId,
                    nestedState: model.children?.[record.key],
                    selected
                }
            )
        );
    if (model.selection !== false)
        nodes.push(
            node(
                'Action',
                'nestedDrag',
                rect(metrics.selection, (rowHeight - 28) / 2, 28, 28),
                {
                    label: translate('Select row', language),
                    enabled: true,
                    action: { type: 'select', key: record.key },
                    dragValue: {
                        searchType: model.searchType || model.scope?.searchType,
                        searchKeys: selected ? model.selected : [record.key]
                    },
                    children: [
                        node('Icon', 'nestedDragIcon', rect(4, 4, 20, 20), {
                            icon: 'drag-handle',
                            color: 'secondaryText'
                        })
                    ]
                }
            )
        );
    nodes.push(
        button(
            'nestedEdit',
            rect(width - 36, (rowHeight - 28) / 2, 28, 28),
            translate('Edit', language),
            'edit',
            { type: 'edit', key: record.key },
            true,
            { iconOnly: true, iconAction: true }
        )
    );
    if (record.detailOpen)
        nodes.push(
            node('View', 'nestedDetail', rect(0, rowHeight, width, height), {
                view: 'nestedTable',
                key: record.key,
                nodeId: record.nodeId
            })
        );
    return { nodes };
}

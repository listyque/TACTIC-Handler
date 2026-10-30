import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { layout } from '../../core/foundation.mjs';
import { metrics, paint } from './host.ui.mjs';
import { columnActions } from './menus.ui.mjs';

export const height = 320;
export const rowHeight = 68;

// Use the owner's viewport budget without tying row geometry to scroll position.
export function extent(state = {}, width = 0, availableHeight = height) {
    const model = Object.assign({}, state.scope, state);
    if (model.busy && !model.loaded && !model.rows?.length) return height;
    const inner = Math.max(0, width - metrics.margin * 2);
    const chrome =
        metrics.margin * 2 +
        42 +
        quickLayout(model, inner).height +
        40 +
        (model.gallery
            ? 0
            : metrics.header +
              3 +
              (tableWidth(model, inner) > inner ? layout.scrollbarExtent : 0));
    const content = rows(model, inner, availableHeight).reduce(
        (sum, row) => sum + row.extent,
        0
    );
    return Math.max(
        chrome + rowHeight,
        Math.min(availableHeight, chrome + content)
    );
}

function tableWidth(model, width) {
    const fields = columns(model),
        last = fields[fields.length - 1];
    return Math.max(width - 16, (last ? last.x + last.width : 0) + 40);
}

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
        scope.expression || '',
        scope.filters || []
    ]);
}

export function rows(model, width = 0, availableHeight = height) {
    if (model.gallery) {
        const count = Math.max(
            1,
            Math.floor(Math.max(0, width - 16) / (model.gallery.scale + 12))
        );
        const result = [];
        for (let index = 0; index < (model.rows || []).length; index += count)
            result.push({
                key: model.rows[index].key,
                items: model.rows.slice(index, index + count),
                extent: model.gallery.scale + 64
            });
        return result;
    }
    return (model.rows || []).map((record) =>
        Object.assign({}, record, {
            detailOpen: !!model.children?.[record.key]?.open,
            extent:
                rowHeight +
                (model.children?.[record.key]?.open
                    ? extent(
                          model.children[record.key].model ||
                              model.children[record.key],
                          width,
                          availableHeight
                      )
                    : 0)
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
                Number.parseFloat(column.width) ||
                    ([
                        'thumbnail',
                        'boolean',
                        'check',
                        'selection',
                        'locked',
                        'status_flag'
                    ].includes(column.cell?.kind)
                        ? 84
                        : 160)
            )
        );
        const result = Object.assign({}, column, { index, x: left, width });
        left += width;
        return result;
    });
}

export function headerActions(model, name, language) {
    const column = (model.columns || []).find((field) => field.name === name);
    return columnActions(
        {
            column,
            editable: !!model.gear,
            busy: model.busy,
            sorted: model.order?.startsWith(name + ' '),
            direction: model.order?.endsWith(' desc') ? 'desc' : 'asc'
        },
        language
    ).filter(
        (action, index) =>
            index === 0 ||
            [
                'sort:ascending',
                'sort:descending',
                'edit_definition',
                'columns'
            ].includes(action.command)
    );
}

export function describe(model, width, extent, language) {
    const margin = metrics.margin;
    const scene = content(
        model,
        Math.max(0, width - margin * 2),
        Math.max(0, extent - margin * 2),
        language
    );
    for (const item of scene.nodes) {
        item.x += margin;
        item.y += margin;
    }
    return scene;
}

function content(model, width, extent, language) {
    const t = (value) => translate(value, language);
    const toolOffset = model.embedded ? 36 : 0;
    const quick = quickLayout(model, width),
        quickColumns = quick.columns,
        quickHeight = quick.height;
    const fields = columns(model);
    const contentWidth = tableWidth(model, width);
    const gutter = contentWidth > width ? layout.scrollbarExtent : 0;
    const nodes = [
        node(
            'Box',
            'nestedToolbarSurface',
            rect(0, 0, width, 42 + quickHeight),
            { background: 'panel', radius: 0 }
        ),
        node(
            'Box',
            'nestedFooterSurface',
            rect(0, Math.max(0, extent - 40), width, 40),
            { background: 'panel', radius: 0 }
        ),
        node(
            'Box',
            'nestedFooterDivider',
            rect(0, Math.max(0, extent - 40), width, 1),
            { background: 'outlineVariant', radius: 0 }
        ),
        node(
            'View',
            'nestedFilter',
            rect(
                0,
                0,
                Math.max(0, width - (model.gear ? 156 : 120) + toolOffset),
                36
            ),
            {
                view: 'tableSearch'
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
            rect(8, extent - 36, Math.max(0, width - 136), 32),
            model.error
                ? t(model.error)
                : t('Results') + ': ' + (model.rows || []).length,
            { color: model.error ? 'error' : 'secondaryText' }
        ),
        button(
            'nestedClearSelection',
            rect(Math.max(0, width - 112), extent - 36, 32, 32),
            t('Clear selection'),
            'close',
            { type: 'clear-selection' },
            !!model.selected?.length,
            { iconOnly: true }
        ),
        button(
            'nestedPrevious',
            rect(Math.max(0, width - 76), extent - 36, 32, 32),
            t('Previous page'),
            'chevron-left',
            { type: 'page', value: -1 },
            !model.busy && model.offset > 0,
            { iconOnly: true }
        ),
        button(
            'nestedNext',
            rect(Math.max(0, width - 40), extent - 36, 32, 32),
            t('Next page'),
            'chevron-right',
            { type: 'page', value: 1 },
            !model.busy && !!model.hasNext,
            { iconOnly: true }
        )
    ];
    if (model.gallery) {
        const toolbar =
            model.search !== false ||
            model.refresh !== false ||
            model.gear ||
            model.insert !== false ||
            !model.embedded;
        const top = toolbar ? 42 : 0;
        nodes.push(
            node(
                'List',
                'nestedGallery',
                rect(0, top, width, Math.max(0, extent - top - 40)),
                {
                    source: 'rows',
                    scrollbarId: 'nestedGalleryScrollBar',
                    keyField: 'key',
                    fields: ['key', 'items', 'extent'],
                    rowHeightField: 'extent',
                    rowHeight: model.gallery.scale + 64,
                    rowGap: 0,
                    label: t('Snapshots'),
                    role: 'list'
                }
            )
        );
        if (!(model.rows || []).length && !model.busy && !model.error)
            nodes.push(
                label(
                    'nestedGalleryEmpty',
                    rect(8, top + 12, Math.max(0, width - 16), 30),
                    t('No snapshots found'),
                    { color: 'secondaryText' }
                )
            );
        return {
            nodes: nodes.filter((item) => {
                if (item.id === 'nestedToolbarSurface') return toolbar;
                if (item.id === 'nestedFilter')
                    return model.shelf !== false && model.search !== false;
                if (item.id === 'nestedReload')
                    return model.shelf !== false && model.refresh !== false;
                if (item.id === 'nestedColumns')
                    return model.shelf !== false && !!model.gear;
                if (item.id === 'nestedCreate')
                    return model.shelf !== false && model.insert !== false;
                if (item.id === 'nestedClose') return !model.embedded;
                if (item.id === 'nestedClearSelection') return false;
                if (['nestedPrevious', 'nestedNext'].includes(item.id))
                    return !!model.hasNext || model.offset > 0;
                return true;
            })
        };
    }
    const children = [
        node(
            'Box',
            'nestedHeaderSurface',
            rect(0, 0, contentWidth, metrics.header),
            { background: paint.header, radius: 0 }
        )
    ];
    for (const field of fields) {
        const menu = !!model.gear || field.sortable;
        children.push(
            node(
                'Box',
                'nestedHeader_' + field.name,
                rect(field.x, 0, field.width, metrics.header),
                {
                    contextAction:
                        menu && !model.busy
                            ? { type: 'header-menu', column: field.name }
                            : null,
                    children: [
                        node(
                            'Action',
                            'nestedHeaderSort_' + field.name,
                            rect(
                                0,
                                0,
                                field.width - (menu ? 34 : 0),
                                metrics.header
                            ),
                            {
                                text: field.title || field.name,
                                contextAction:
                                    menu && !model.busy
                                        ? {
                                              type: 'header-menu',
                                              column: field.name
                                          }
                                        : null,
                                action: field.sortable
                                    ? { type: 'sort', value: field.name }
                                    : null,
                                enabled: !model.busy,
                                children: [
                                    label(
                                        'nestedHeaderText_' + field.name,
                                        rect(
                                            8,
                                            0,
                                            Math.max(
                                                0,
                                                field.width - (menu ? 44 : 20)
                                            ),
                                            metrics.header
                                        ),
                                        field.title || field.name,
                                        { color: paint.headerText }
                                    )
                                ]
                            }
                        ),
                        ...(menu
                            ? [
                                  button(
                                      'nestedHeaderMenu_' + field.name,
                                      rect(field.width - 34, 2, 32, 32),
                                      t('Column actions'),
                                      'more-vert',
                                      {
                                          type: 'header-menu',
                                          column: field.name
                                      },
                                      !model.busy
                                  )
                              ]
                            : [])
                    ]
                }
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
                Math.max(
                    0,
                    extent - 82 - metrics.header - 3 - quickHeight - gutter
                )
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
                Math.max(0, extent - 82 - quickHeight)
            ),
            {
                contentWidth,
                contentHeight: Math.max(0, extent - 82 - quickHeight - gutter),
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
    if (model.gallery) {
        const size = Math.min(
            model.gallery.scale,
            Math.max(0, viewportWidth - 12)
        );
        return {
            nodes: (record.items || []).map((item, index) => {
                const values = item.record;
                const title = values.context || values.code || '';
                const image =
                    Object.values(item.cells || {}).find((cell) => cell.image)
                        ?.image || '';
                return node(
                    'Action',
                    'nestedSnapshot_' + item.key,
                    rect(
                        index * (model.gallery.scale + 12) + 6,
                        6,
                        size,
                        size + 50
                    ),
                    {
                        text: translate('Check out', language) + ': ' + title,
                        normalColor: 'transparent',
                        radius: 0,
                        action: { type: 'gallery-open', key: item.key },
                        children: [
                            node(
                                'Preview',
                                'nestedSnapshotPreview_' + item.key,
                                rect(0, 0, size, size),
                                {
                                    source: image,
                                    icon: 'snapshot',
                                    round: false,
                                    fit: 'contain',
                                    outlined: model.gallery.border
                                }
                            ),
                            label(
                                'nestedSnapshotContext_' + item.key,
                                rect(0, size + 4, size, 22),
                                title
                            ),
                            label(
                                'nestedSnapshotVersion_' + item.key,
                                rect(0, size + 26, size, 20),
                                String(
                                    item.cells.version?.text ??
                                        values.version ??
                                        ''
                                ),
                                { color: 'secondaryText' }
                            )
                        ]
                    }
                );
            })
        };
    }
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
            model.rowActions ? 'nestedMenu' : 'nestedEdit',
            rect(width - 36, (rowHeight - 28) / 2, 28, 28),
            translate(model.rowActions ? 'Object actions' : 'Edit', language),
            model.rowActions ? 'more-vert' : 'edit',
            model.rowActions
                ? { type: 'operate', nodeId: record.nodeId }
                : { type: 'edit', key: record.key },
            true,
            { iconOnly: true, iconAction: true }
        )
    );
    if (record.detailOpen)
        nodes.push(
            node(
                'View',
                'nestedDetail',
                rect(
                    0,
                    rowHeight,
                    width,
                    record.extent
                        ? record.extent - rowHeight
                        : extent(
                              model.children?.[record.key]?.model ||
                                  model.children?.[record.key],
                              width
                          )
                ),
                {
                    view: 'nestedTable',
                    key: record.key,
                    nodeId: record.nodeId
                }
            )
        );
    return { nodes };
}

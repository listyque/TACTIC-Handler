import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { metrics } from './host.ui.mjs';

export const height = 320;
export const rowHeight = 58;

function tableRowHeight(model) {
    return model.rowHeight || model.resultState?.table?.rowHeight || rowHeight;
}

// Use the owner's viewport budget without tying row geometry to scroll position.
export function extent(state = {}, width = 0, availableHeight = height) {
    const model = Object.assign({}, state.scope, state);
    if (model.busy && !model.loaded && !model.rows?.length) return height;
    const inner = Math.max(0, width);
    const chrome =
        42 +
        quickLayout(model, inner).height +
        40 +
        (model.gallery
            ? 0
            : metrics.header + (model.selected?.length ? 36 : 0));
    const content = rows(model, inner, availableHeight).reduce(
        (sum, row) => sum + row.extent,
        0
    );
    return Math.max(
        chrome + tableRowHeight(model),
        Math.min(availableHeight, chrome + content)
    );
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
                tableRowHeight(model) +
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

export function describe(model, width, extent, language) {
    const margin = 0;
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
            rect(8, extent - 36, Math.max(0, width - 84), 32),
            model.error
                ? t(model.error)
                : t('Results') + ': ' + (model.rows || []).length,
            { color: model.error ? 'error' : 'secondaryText' }
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
    if (model.loaded || model.definition)
        nodes.push(
            node(
                'View',
                'nestedTableBody',
                rect(
                    0,
                    42 + quickHeight,
                    width,
                    Math.max(0, extent - 82 - quickHeight)
                ),
                { view: 'tableBody' }
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
    return { nodes: [] };
}

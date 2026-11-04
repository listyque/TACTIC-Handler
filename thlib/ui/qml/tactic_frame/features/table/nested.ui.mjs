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
    const inner = Math.max(0, width);
    const chrome =
        toolbarHeight(model) +
        quickLayout(model, inner).height +
        40 +
        (model.gallery
            ? 0
            : metrics.header +
              (model.selected?.length ? 36 : 0) +
              (model.dirtyTaskCount ? 44 : 0));
    const expected =
        !model.loaded && !model.rows?.length
            ? Math.max(
                  1,
                  Math.min(
                      50,
                      Number(
                          String(model.expectedRows ?? model.text ?? '').match(
                              /\d+/
                          )?.[0]
                      ) || 1
                  )
              )
            : 0;
    const content = expected
        ? expected *
          (model.gallery ? model.gallery.scale + 64 : tableRowHeight(model))
        : rows(model, inner, availableHeight).reduce(
              (sum, row) => sum + row.extent,
              0
          );
    return Math.max(
        chrome + tableRowHeight(model),
        Math.min(availableHeight, chrome + content)
    );
}

function toolbarHeight(model) {
    return model.shelf !== false && model.search !== false ? 42 : 0;
}

// The active table is the transparent opening; the rest of its owner is inert.
export function focusScene(bounds, width, height, language) {
    if (!bounds) return { nodes: [] };
    const x = Math.max(0, Math.min(width, bounds.x));
    const y = Math.max(0, Math.min(height, bounds.y));
    const right = Math.max(x, Math.min(width, bounds.x + bounds.width));
    const bottom = Math.max(y, Math.min(height, bounds.y + bounds.height));
    if (right <= x || bottom <= y) return { nodes: [] };
    const nodes = [
        rect(0, 0, width, y),
        rect(0, bottom, width, height - bottom),
        rect(0, y, x, bottom - y),
        rect(right, y, width - right, bottom - y)
    ]
        .filter((part) => part.width > 0 && part.height > 0)
        .map((part, index) =>
            node('Action', 'nestedFocusScrim_' + index, part, {
                text: translate('Close', language),
                children: [],
                enabled: true,
                normalColor: 'scrim',
                hoverColor: 'scrim',
                pressedColor: 'scrim',
                radius: 0,
                action: { type: 'close' }
            })
        );
    nodes.push(
        node('Box', 'nestedFocusShadow', rect(x, y, right - x, bottom - y), {
            background: 'transparent',
            radius: 0,
            clip: false,
            shadow: { y: 6, blur: 14, opacity: 1 }
        })
    );
    return { nodes };
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
    const top = toolbarHeight(model);
    const tools = [
        model.shelf !== false && model.refresh !== false && 'nestedReload',
        model.shelf !== false && model.gear && 'nestedColumns',
        model.shelf !== false && model.insert !== false && 'nestedCreate',
        !model.embedded && 'nestedClose'
    ].filter(Boolean);
    const pages = model.searchLimit === false ? 0 : 2;
    const toolY = top ? 0 : Math.max(0, extent - 36);
    const toolX = (id) =>
        Math.max(0, width - (tools.length - tools.indexOf(id)) * 36 - 4);
    const quick = quickLayout(model, width),
        quickColumns = quick.columns,
        quickHeight = quick.height;
    const nodes = [
        node(
            'Box',
            'nestedToolbarSurface',
            rect(0, 0, width, top + quickHeight),
            { background: model.embedded ? 'transparent' : 'panel', radius: 0 }
        ),
        node(
            'Box',
            'nestedFooterSurface',
            rect(0, Math.max(0, extent - 40), width, 40),
            { background: model.embedded ? 'transparent' : 'panel', radius: 0 }
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
            rect(0, 0, Math.max(0, width - tools.length * 36 - 8), 36),
            {
                view: 'tableSearch'
            }
        ),
        button(
            'nestedReload',
            rect(toolX('nestedReload'), toolY, 32, 32),
            model.busy ? t('Loading data…') : t('Refresh'),
            model.busy ? 'loading' : 'refresh',
            { type: 'reload' },
            !model.busy,
            { iconOnly: true, iconAction: true, round: false }
        ),
        button(
            'nestedColumns',
            rect(toolX('nestedColumns'), toolY, 32, 32),
            t('Columns'),
            'view-column',
            { type: 'columns' },
            !model.busy,
            { iconOnly: true, iconAction: true, round: false }
        ),
        button(
            'nestedCreate',
            rect(toolX('nestedCreate'), toolY, 32, 32),
            t('Create'),
            'add',
            { type: 'create' },
            !model.busy && model.insert !== false,
            { iconOnly: true, iconAction: true, round: false }
        ),
        button(
            'nestedClose',
            rect(toolX('nestedClose'), toolY, 32, 32),
            t('Close'),
            'close',
            { type: 'close' },
            true,
            { iconOnly: true, iconAction: true, round: false }
        ),
        label(
            'nestedState',
            rect(
                8,
                extent - 36,
                Math.max(
                    0,
                    width - 12 - (pages + (top ? 0 : tools.length)) * 36
                ),
                32
            ),
            model.error
                ? t(model.error)
                : t('Results') + ': ' + (model.rows || []).length,
            { color: model.error ? 'error' : 'secondaryText' }
        ),
        button(
            'nestedPrevious',
            rect(
                Math.max(0, width - 76 - (top ? 0 : tools.length * 36)),
                extent - 36,
                32,
                32
            ),
            t('Previous page'),
            'chevron-left',
            { type: 'page', value: -1 },
            !model.busy && model.offset > 0,
            { iconOnly: true, iconAction: true, round: false }
        ),
        button(
            'nestedNext',
            rect(
                Math.max(0, width - 40 - (top ? 0 : tools.length * 36)),
                extent - 36,
                32,
                32
            ),
            t('Next page'),
            'chevron-right',
            { type: 'page', value: 1 },
            !model.busy && !!model.hasNext,
            { iconOnly: true, iconAction: true, round: false }
        )
    ];
    if (model.gallery) {
        const galleryTop = top + quickHeight;
        nodes.push(
            node(
                'List',
                'nestedGallery',
                rect(
                    0,
                    galleryTop,
                    width,
                    Math.max(0, extent - galleryTop - 40)
                ),
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
                    rect(8, galleryTop + 12, Math.max(0, width - 16), 30),
                    t('No snapshots found'),
                    { color: 'secondaryText' }
                )
            );
        return {
            nodes: nodes.filter((item) => {
                if (item.id === 'nestedToolbarSurface')
                    return top + quickHeight > 0;
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
                    top + quickHeight,
                    width,
                    Math.max(0, extent - top - 40 - quickHeight)
                ),
                { view: 'tableBody' }
            )
        );
    (model.simpleFilters || []).forEach((filter, index) => {
        const part = Math.max(0, (width - 24) / quickColumns),
            x = (index % quickColumns) * part,
            y = top + Math.floor(index / quickColumns) * 66;
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
            if (item.id === 'nestedToolbarSurface')
                return top + quickHeight > 0;
            if (item.id === 'nestedClose' && model.embedded) return false;
            if (item.id === 'nestedReload' && model.refresh === false)
                return false;
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

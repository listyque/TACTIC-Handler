import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { link } from './cells.ui.mjs';
import { quickLayout } from './nested.ui.mjs';
import * as Report from './report.ui.mjs';
import * as Filters from './page.filters.mjs';
import * as PageLayout from './page.layout.mjs';
import * as Parts from './record.parts.mjs';
import {
    textStyles,
    controls as controlMetrics
} from '../../core/foundation.mjs';
import {
    tab as workspaceTab,
    viewTabWidth
} from '../../controls/tabs/workspace.ui.mjs';

export function hasDetails(items = []) {
    return items.some(
        (item) => item.kind === 'details' || hasDetails(item.children || [])
    );
}
export function tables(items = [], prefix = 'customLayout') {
    const result = [];
    for (const [index, item] of items.entries()) {
        const key = prefix + '_' + index;
        if (item.kind === 'table') result.push({ key, scope: item.table });
        else result.push(...tables(item.children || [], key));
    }
    return result;
}
export function initial(cell) {
    return {
        form: cell.layoutForm || '',
        root: {},
        controls: cell.layoutControls || []
    };
}
export function change(state, selector, value) {
    return Object.assign({}, state, {
        controls: state.controls.map((item) =>
            item.selector === selector
                ? Object.assign({}, item, { value, selectedValue: value })
                : item
        )
    });
}
export function resize(state = {}, action) {
    if (
        !Number.isFinite(action.value) ||
        !Number.isFinite(action.extent) ||
        action.extent <= 0
    )
        return state;
    return Object.assign({}, state, {
        splits: Object.assign({}, state.splits, {
            [action.key]: Math.max(0, Math.min(1, action.value / action.extent))
        })
    });
}
function plain(value) {
    return String(value || '')
        .replace(/<[^>]*>/g, '')
        .replace(
            /&(amp|lt|gt|quot|#39);/g,
            (_, entity) =>
                ({ amp: '&', lt: '<', gt: '>', quot: '"', '#39': "'" })[entity]
        );
}
export function describe(
    cell,
    width,
    height,
    language,
    editable = true,
    server = '',
    measure = (text, size) => String(text).length * size
) {
    const tabOffset = cell.layoutTabs?.length ? 56 : 0;
    const children = [],
        gap = 8;
    let tableHeight = Math.max(320, height - tabOffset - 48);
    const controls = cell.layoutState?.controls || cell.layoutControls || [];
    function draw(
        items,
        originX,
        originY,
        space,
        prefix = 'customLayout',
        startIndex = 0,
        output = children,
        bottom = Infinity,
        spacing = 8,
        slotHeight = null
    ) {
        let top = originY;
        for (const [index, source] of (items || []).entries()) {
            const id = prefix + '_' + (index + startIndex);
            const item = Object.assign(
                {},
                source,
                controls.find(
                    (control) =>
                        control.selector && control.selector === source.selector
                )
            );
            const text =
                item.innerHTML !== undefined
                    ? plain(item.innerHTML)
                    : item.translate
                      ? translate(item.text, language)
                      : item.text || '';
            const padding = item.padding || [0, 0, 0, 0],
                margin = item.margin || [0, 0, 0, 0],
                outerTop = top,
                outerWidth = PageLayout.width(item, space, measure),
                x = originX + margin[3] + padding[3],
                available = Math.max(
                    0,
                    outerWidth - margin[1] - margin[3] - padding[1] - padding[3]
                ),
                firstOutput = output.length,
                childGap = item.gap === undefined ? 8 : item.gap,
                slotCapacity =
                    slotHeight === null
                        ? null
                        : Math.max(
                              0,
                              slotHeight -
                                  margin[0] -
                                  margin[2] -
                                  padding[0] -
                                  padding[2]
                          );
            top += margin[0] + padding[0];
            let extent = 0;
            if (item.children) {
                const horizontal =
                    item.kind === 'row' &&
                    available >= (item.collapseWidth ?? 600);
                if (item.kind === 'grid') {
                    const cells = PageLayout.grid(
                        item.children,
                        available,
                        item,
                        childGap
                    );
                    for (const cell of cells.placements)
                        draw(
                            [item.children[cell.index]],
                            x + cell.x,
                            top + cell.y,
                            cell.width,
                            id,
                            cell.index,
                            output,
                            bottom,
                            childGap,
                            cell.height
                        );
                    extent = cells.height || item.row_height || 120;
                } else if (horizontal) {
                    const navigator =
                        item.children.length === 2 &&
                        item.children[0].kind === 'items' &&
                        item.children[1].kind === 'details';
                    const seam = navigator
                        ? Math.max(childGap, controlMetrics.splitter.extent)
                        : childGap;
                    const budget = Math.max(
                        0,
                        available - seam * (item.children.length - 1)
                    );
                    const widths = PageLayout.rowWidths(
                        item.children,
                        budget,
                        measure
                    );
                    const paneHeight = navigator
                        ? Math.max(
                              0,
                              Math.min(
                                  slotCapacity ?? Infinity,
                                  Number.isFinite(item.height)
                                      ? item.height
                                      : height -
                                            tabOffset -
                                            top -
                                            margin[2] -
                                            padding[2]
                              )
                          )
                        : null;
                    if (navigator) {
                        const minimum = Math.min(
                            budget / 2,
                            Math.max(
                                160,
                                item.children[0].sizing?.min_width || 0
                            )
                        );
                        const maximum =
                            budget -
                            Math.min(
                                budget / 2,
                                Math.max(
                                    240,
                                    item.children[1].sizing?.min_width || 0
                                )
                            );
                        const ratio = cell.layoutState?.splits?.[id];
                        widths[0] = Math.max(
                            minimum,
                            Math.min(
                                maximum,
                                Number.isFinite(ratio)
                                    ? ratio * budget
                                    : widths[0]
                            )
                        );
                        widths[1] = budget - widths[0];
                        const action = {
                            type: 'layout-split',
                            key: id,
                            extent: budget
                        };
                        output.push(
                            node(
                                'Splitter',
                                id + '_split',
                                rect(x + widths[0], top, seam, paneHeight),
                                {
                                    text: translate(
                                        'Elements panel width',
                                        language
                                    ),
                                    value: widths[0],
                                    min: minimum,
                                    max: maximum,
                                    enabled: !cell.layoutEditing,
                                    action,
                                    cancelAction: action
                                }
                            )
                        );
                    }
                    let left = x;
                    for (const [column, child] of item.children.entries()) {
                        const part = widths[column];
                        extent = Math.max(
                            extent,
                            draw(
                                [
                                    navigator
                                        ? Object.assign({}, child, {
                                              sizing: Object.assign(
                                                  {},
                                                  child.sizing,
                                                  { height_mode: 'fill' }
                                              )
                                          })
                                        : child
                                ],
                                left,
                                top,
                                part,
                                id,
                                column,
                                output,
                                bottom,
                                childGap,
                                paneHeight
                            )
                        );
                        left += part + seam;
                    }
                } else
                    extent = draw(
                        item.children,
                        x,
                        top,
                        available,
                        id,
                        0,
                        output,
                        bottom,
                        childGap
                    );
            } else if (['chart', 'summary'].includes(item.kind)) {
                extent = Number.isFinite(item.height) ? item.height : 320;
                output.push(
                    node('Box', id, rect(x, top, available, extent), {
                        children: Report.describe(
                            item,
                            id,
                            available,
                            extent,
                            language
                        ).nodes
                    })
                );
            } else if (item.kind === 'metric') {
                extent = Number.isFinite(item.height) ? item.height : 104;
                const appearance = item.appearance;
                const decorated =
                    appearance &&
                    (appearance.fill !== 'transparent' ||
                        appearance.stroke_width ||
                        appearance.radius ||
                        appearance.shadow);
                output.push(
                    node('Box', id, rect(x, top, available, extent), {
                        background: decorated ? 'transparent' : 'panel',
                        border: decorated ? '' : 'outlineVariant',
                        radiusRole: decorated ? undefined : 'surfaceRadius',
                        radius: decorated ? 0 : undefined,
                        children: [
                            label(
                                id + '_label',
                                rect(16, 12, Math.max(0, available - 32), 36),
                                text,
                                { color: 'secondaryText', wrap: true }
                            ),
                            label(
                                id + '_value',
                                rect(16, 52, Math.max(0, available - 32), 40),
                                item.value == null &&
                                    Object.prototype.hasOwnProperty.call(
                                        item,
                                        'value'
                                    )
                                    ? '—'
                                    : String(item.value ?? 0),
                                { fontRole: 'hero', weight: 600 }
                            )
                        ]
                    })
                );
            } else if (['field', 'form'].includes(item.kind)) {
                const part =
                    item.kind === 'field'
                        ? Parts.field(item, id, available)
                        : Parts.describe(
                              item,
                              id,
                              available,
                              cell.layoutForms || {},
                              language,
                              editable &&
                                  !cell.layoutEditing &&
                                  !cell.layoutBusy
                          );
                output.push(
                    node(
                        'Box',
                        id + '_content',
                        rect(x, top, available, part.height),
                        {
                            background: 'transparent',
                            clip: false,
                            radius: 0,
                            children: part.children
                        }
                    )
                );
                extent = part.height;
            } else if (item.kind === 'action' && item.nativeAction) {
                extent = 40;
                output.push(
                    button(
                        id,
                        rect(x, top, available, extent),
                        text,
                        item.icon ||
                            {
                                details: 'search',
                                edit: 'edit',
                                notes: 'comment',
                                copy_link: 'link',
                                refresh: 'refresh'
                            }[item.nativeAction],
                        {
                            type: 'record-action',
                            name: item.nativeAction,
                            targetSearchKey: item.targetSearchKey,
                            view: item.editView,
                            process: item.process
                        },
                        editable &&
                            item.available !== false &&
                            !cell.layoutEditing &&
                            !cell.layoutBusy,
                        {
                            highlighted: item.buttonStyle === 'primary',
                            tonal: item.buttonStyle === 'tonal'
                        }
                    )
                );
            } else if (item.kind === 'text') {
                const role = item.textRole || 'body',
                    size = textStyles[role];
                extent = text
                    ? item.editorPath
                        ? PageLayout.textHeight(
                              text,
                              available,
                              size,
                              item.textWeight || 400,
                              measure
                          )
                        : Math.max(
                              28,
                              Math.ceil(
                                  String(text).length /
                                      Math.max(1, Math.floor(available / 8))
                              ) * 22
                          )
                    : 0;
                if (extent)
                    output.push(
                        label(id, rect(x, top, available, extent), text, {
                            wrap: true,
                            fontRole: role,
                            weight: item.textWeight || 400,
                            align: item.textAlign || 'left',
                            color: item.textColor || 'primaryText'
                        })
                    );
            } else if (item.kind === 'icon') {
                extent = item.iconSize || 32;
                output.push(
                    node(
                        'Icon',
                        id,
                        rect(x, top, Math.min(available, extent), extent),
                        {
                            icon: item.icon || 'folder',
                            text,
                            color: item.textColor || 'primaryText'
                        }
                    )
                );
            } else if (item.kind === 'image') {
                extent = Number.isFinite(item.height) ? item.height : 160;
                output.push(
                    node('Preview', id, rect(x, top, available, extent), {
                        source: link(item.image, server) || '',
                        initials: String(text).slice(0, 2),
                        round: false,
                        outlined: false,
                        fit: item.fit || 'contain'
                    })
                );
            } else if (item.kind === 'divider' || item.kind === 'spacer') {
                extent = item.height || (item.kind === 'divider' ? 24 : 16);
                if (item.kind === 'divider')
                    output.push(
                        node(
                            'Box',
                            id,
                            rect(x, top + Math.floor(extent / 2), available, 1),
                            {
                                background: item.textColor || 'outlineVariant',
                                radius: 0
                            }
                        )
                    );
            } else if (item.kind === 'markdown') {
                extent = Number.isFinite(item.height)
                    ? item.height
                    : prefix.startsWith('customLayoutDetails')
                      ? Math.max(
                            48,
                            Math.min(
                                560,
                                String(text)
                                    .split('\n')
                                    .reduce(
                                        (sum, line) =>
                                            sum +
                                            Math.max(
                                                1,
                                                Math.ceil(
                                                    line.length /
                                                        Math.max(
                                                            1,
                                                            Math.floor(
                                                                available / 8
                                                            )
                                                        )
                                                )
                                            ),
                                        0
                                    ) *
                                    22 +
                                    24
                            )
                        )
                      : Math.max(240, Math.min(560, tableHeight));
                if (
                    prefix.startsWith('customLayoutDetails') &&
                    !Number.isFinite(item.height)
                )
                    extent = Math.min(extent, Math.max(48, bottom - top));
                output.push(
                    node('View', id, rect(x, top, available, extent), {
                        view: 'layoutMarkdown',
                        text,
                        key: id,
                        contentInset: prefix.startsWith('customLayoutDetails')
                            ? 0
                            : 14
                    })
                );
            } else if (item.kind === 'preview') {
                extent = Math.min(available, item.size || 64);
                output.push(
                    node('Preview', id, rect(x, top, extent, extent), {
                        source: link(item.value?.image, server) || '',
                        initials: String(text).slice(0, 2),
                        round: false,
                        action: {
                            type: 'service',
                            name: item.javascript ? 'script' : 'sobject_detail',
                            javascript: item.javascript || '',
                            targetSearchKey: cell.targetSearchKey
                        },
                        enabled: !item.javascript || editable
                    })
                );
            } else if (item.kind === 'details') {
                extent =
                    PageLayout.height(
                        item,
                        item.height || tableHeight,
                        slotCapacity === null
                            ? null
                            : Math.max(0, slotCapacity - 32)
                    ) + 32;
                const detail = cell.layoutDetail || {},
                    detailNodes = [];
                const detailPadding = 24;
                const title =
                    detail.title ||
                    text ||
                    translate('Object details', language);
                const titleHeight = Math.min(
                    48,
                    Math.max(
                        24,
                        Math.ceil(
                            title.length /
                                Math.max(
                                    1,
                                    Math.floor(
                                        (available - detailPadding * 2) / 9
                                    )
                                )
                        ) * 24
                    )
                );
                const contentTop = 20 + titleHeight + 16;
                detailNodes.push(
                    label(
                        id + '_title',
                        rect(
                            detailPadding,
                            20,
                            Math.max(0, available - detailPadding * 2),
                            titleHeight
                        ),
                        title,
                        {
                            fontRole: 'heading',
                            weight: 600,
                            wrap: true,
                            maxLines: 2
                        }
                    )
                );
                const bodyHeight = draw(
                    detail.layoutNodes,
                    detailPadding,
                    contentTop,
                    Math.max(0, available - detailPadding * 2),
                    'customLayoutDetails',
                    0,
                    detailNodes,
                    extent - 24
                );
                const message =
                    detail.error ||
                    (detail.busy
                        ? translate('Loading...', language)
                        : !detail.targetSearchKey
                          ? translate('Select an item', language)
                          : '');
                if (message)
                    detailNodes.push(
                        label(
                            id + '_message',
                            rect(
                                detailPadding,
                                contentTop,
                                Math.max(0, available - detailPadding * 2),
                                56
                            ),
                            message,
                            {
                                wrap: true,
                                color: detail.error ? 'error' : 'secondaryText'
                            }
                        )
                    );
                output.push(
                    node(
                        'Box',
                        id + '_surface',
                        rect(x, top, available, extent),
                        {
                            background: 'panel',
                            border: 'outlineVariant',
                            radius: 4,
                            children: [
                                node(
                                    'Scroll',
                                    id,
                                    rect(0, 0, available, extent),
                                    {
                                        contentHeight: Math.max(
                                            extent,
                                            contentTop + 20 + bodyHeight
                                        ),
                                        scrollbarId: id + 'Bar',
                                        children: detailNodes
                                    }
                                )
                            ]
                        }
                    )
                );
            } else if (item.kind === 'items') {
                const itemsExtent = PageLayout.height(
                    item,
                    Number.isFinite(item.height) ? item.height : tableHeight,
                    slotCapacity === null
                        ? null
                        : Math.max(0, slotCapacity - 32)
                );
                extent = itemsExtent + 32;
                output.push(
                    label(id + '_title', rect(x, top, available, 28), text)
                );
                output.push(
                    node(
                        'View',
                        id,
                        rect(x, top + 32, available, itemsExtent),
                        {
                            view: 'layoutItems',
                            key: id,
                            items: item.items
                        }
                    )
                );
            } else if (item.kind === 'table') {
                const tableExtent = Number.isFinite(item.height)
                    ? item.height
                    : Math.max(
                          tableHeight,
                          quickLayout(cell.layoutTables?.[id] || {}, available)
                              .height + 260
                      );
                extent = tableExtent + 32;
                output.push(
                    label(id + '_title', rect(x, top, available, 28), text)
                );
                output.push(
                    node(
                        'View',
                        id,
                        rect(x, top + 32, available, tableExtent),
                        { view: 'layoutTable', key: id, table: item.table }
                    )
                );
            } else if (item.kind === 'choice') {
                extent = 40;
                output.push(
                    node('Choice', id, rect(x, top, available, extent), {
                        value:
                            item.selectedValue ||
                            item.value ||
                            item.options?.[0]?.value ||
                            '',
                        options: (item.options || []).map((option) => ({
                            value: option.value,
                            label: option.text || option.label
                        })),
                        enabled: editable && !cell.layoutBusy,
                        action: {
                            type: 'layout-change',
                            selector: item.selector
                        }
                    })
                );
            } else {
                extent = 40;
                output.push(
                    button(
                        id,
                        rect(x, top, available, extent),
                        text,
                        item.icon ||
                            (['link', 'button'].includes(item.kind)
                                ? 'open-in-new'
                                : 'edit'),
                        {
                            type: 'service',
                            name: ['link', 'button'].includes(item.kind)
                                ? 'layout-link'
                                : 'script',
                            href: item.href,
                            javascript: item.javascript,
                            selector: item.selector
                        },
                        ['link', 'button'].includes(item.kind)
                            ? !!item.href
                            : editable && !cell.layoutBusy,
                        {
                            highlighted: item.buttonStyle === 'primary',
                            tonal: item.buttonStyle === 'tonal'
                        }
                    )
                );
            }
            if (item.editorPath) {
                const overhead = ['items', 'table', 'details'].includes(
                    item.kind
                )
                    ? 32
                    : 0;
                const contentSlot =
                    slotHeight === null
                        ? null
                        : Math.max(
                              0,
                              slotHeight -
                                  margin[0] -
                                  margin[2] -
                                  padding[0] -
                                  padding[2] -
                                  overhead
                          );
                const resolved =
                    PageLayout.height(
                        item,
                        Math.max(0, extent - overhead),
                        contentSlot
                    ) + overhead;
                if (resolved !== extent) {
                    const surface = output[firstOutput];
                    if (
                        surface &&
                        [
                            'metric',
                            'form',
                            'field',
                            'action',
                            'image',
                            'button',
                            'link',
                            'chart',
                            'summary',
                            'markdown'
                        ].includes(item.kind)
                    )
                        surface.height = resolved;
                    if (['table', 'items'].includes(item.kind))
                        for (const surface of output.slice(firstOutput))
                            if (surface.kind === 'View')
                                surface.height = Math.max(0, resolved - 32);
                }
                extent = resolved;
            }
            const outerHeight =
                extent + margin[0] + margin[2] + padding[0] + padding[2];
            if (item.editorPath) {
                const content = output.splice(firstOutput);
                for (const child of content) {
                    child.x -= originX + margin[3];
                    child.y -= outerTop + margin[0];
                }
                if (item.appearance?.shadow)
                    for (const [index, dx, dy, grow, opacity] of [
                        [0, -1, 1, 2, 0.28],
                        [1, 1, 3, -2, 0.58]
                    ])
                        output.push(
                            node(
                                'Box',
                                id + '_shadow' + index,
                                rect(
                                    originX +
                                        margin[3] +
                                        (item.offsetX || 0) +
                                        dx,
                                    outerTop +
                                        margin[0] +
                                        (item.offsetY || 0) +
                                        dy,
                                    Math.max(
                                        0,
                                        outerWidth -
                                            margin[1] -
                                            margin[3] +
                                            grow
                                    ),
                                    Math.max(
                                        0,
                                        outerHeight - margin[0] - margin[2]
                                    ) + (index === 0 ? 2 : 0)
                                ),
                                {
                                    background: 'popupShadow',
                                    radius:
                                        (item.appearance.radius || 0) +
                                        (index === 0 ? 1 : 0),
                                    opacity,
                                    pointerTransparent: true
                                }
                            )
                        );
                output.push(
                    node(
                        'Box',
                        id + '_block',
                        rect(
                            originX + margin[3] + (item.offsetX || 0),
                            outerTop + margin[0] + (item.offsetY || 0),
                            Math.max(0, outerWidth - margin[1] - margin[3]),
                            Math.max(0, outerHeight - margin[0] - margin[2])
                        ),
                        {
                            background: item.appearance?.fill || 'transparent',
                            border: item.appearance?.stroke_width
                                ? item.appearance.stroke
                                : '',
                            borderWidth: item.appearance?.stroke_width || 0,
                            radius: item.appearance?.radius || 0,
                            motion:
                                item.appearance?.animate &&
                                !cell.layoutDesigning
                                    ? {
                                          x: 'clickMotionSlow',
                                          y: 'clickMotionSlow',
                                          width: 'clickMotionSlow',
                                          height: 'clickMotionSlow'
                                      }
                                    : null,
                            editorPath: item.editorPath,
                            clip:
                                Number.isFinite(item.height) ||
                                slotHeight !== null ||
                                !!item.sizing?.max_height ||
                                ['fixed', 'fill'].includes(
                                    item.sizing?.height_mode
                                ),
                            children: content
                        }
                    )
                );
            }
            top = outerTop + (outerHeight ? outerHeight + spacing : 0);
        }
        return Math.max(0, top - originY - spacing);
    }
    function visualBottom(nodes) {
        return Math.max(
            0,
            ...nodes.map(
                (item) =>
                    item.y +
                    Math.max(
                        item.height,
                        item.clip === false
                            ? visualBottom(item.children || [])
                            : 0
                    )
            )
        );
    }
    const viewportHeight = Math.max(0, height - tabOffset);
    let headerNodes = [],
        footerNodes = [],
        headerHeight = 0,
        footerHeight = 0;
    function drawRegion(region, space, output, start = 0, capacity = null) {
        const entries = (cell.layoutNodes || [])
            .map((item, index) => ({ item, index }))
            .filter(({ item }) => (item.region || 'content') === region);
        let top = start;
        for (const [position, { item, index }] of entries.entries()) {
            const slot =
                capacity !== null &&
                position === entries.length - 1 &&
                item.sizing?.height_mode === 'fill'
                    ? Math.max(0, capacity - top)
                    : null;
            top +=
                draw(
                    [item],
                    0,
                    top,
                    space,
                    'customLayout',
                    index,
                    output,
                    capacity ?? Infinity,
                    gap,
                    slot
                ) + gap;
        }
        return Math.max(
            start,
            top - (entries.length ? gap : 0),
            visualBottom(output)
        );
    }
    function header(space) {
        const filters = Filters.describe(
            cell.layoutFilters,
            cell.layoutFilterDraft || Filters.initial(cell.layoutFilters),
            Math.max(0, space - 24),
            language,
            editable &&
                !cell.layoutBusy &&
                !cell.layoutFilterBusy &&
                !cell.layoutEditing
        );
        const output = [];
        const contextHeight = drawRegion(
            'header',
            Math.max(0, space - 24),
            output
        );
        const filterTop =
            contextHeight + (contextHeight && filters.height ? gap : 0);
        for (const item of filters.nodes) {
            item.y += filterTop;
            output.push(item);
        }
        const extent = filterTop + filters.height;
        for (const item of output) {
            item.x += 12;
            item.y += 12;
        }
        return { nodes: output, height: output.length ? extent + 24 : 0 };
    }
    let head = header(width);
    let foot = [];
    let footerExtent = drawRegion('footer', Math.max(0, width - 24), foot);
    footerHeight = foot.length
        ? Math.min(footerExtent + 24, viewportHeight * 0.3)
        : 0;
    headerHeight = Math.min(
        head.height,
        Math.max(
            0,
            viewportHeight - footerHeight - Math.min(180, viewportHeight * 0.45)
        )
    );
    if (head.height > headerHeight)
        head = header(Math.max(0, width - controlMetrics.scrollBar.extent - 4));
    headerNodes = head.nodes;
    if (footerExtent + 24 > footerHeight && footerHeight) {
        foot = [];
        footerExtent = drawRegion(
            'footer',
            Math.max(0, width - 24 - controlMetrics.scrollBar.extent - 4),
            foot
        );
    }
    for (const item of foot) {
        item.x += 12;
        item.y += 12;
    }
    footerNodes = foot;
    const bodyHeight = Math.max(
        0,
        viewportHeight - headerHeight - footerHeight
    );
    if (headerHeight || footerHeight)
        tableHeight = Math.max(160, bodyHeight - 32);
    function render(contentWidth) {
        children.length = 0;
        const flowExtent = drawRegion(
            'content',
            contentWidth,
            children,
            0,
            bodyHeight
        );
        return Math.max(flowExtent, visualBottom(children));
    }
    let contentWidth = Math.max(0, width),
        extent = render(contentWidth);
    if (extent + (cell.layoutError ? 80 : 0) > bodyHeight) {
        contentWidth = Math.max(0, width - controlMetrics.scrollBar.extent - 4);
        extent = render(contentWidth);
    }
    if (cell.layoutError)
        children.push(
            label(
                'layoutError',
                rect(0, extent + gap, contentWidth, 64),
                cell.layoutError,
                { wrap: true, color: 'error' }
            )
        );
    const nodes = [
        node('Box', 'layoutBackground', rect(0, 0, width, height), {
            background: 'workspace'
        })
    ];
    for (const [name, y, extent, content, contentHeight] of [
        ['Header', tabOffset, headerHeight, headerNodes, head.height],
        [
            'Footer',
            height - footerHeight,
            footerHeight,
            footerNodes,
            footerExtent + 24
        ]
    ]) {
        if (!extent) continue;
        nodes.push(
            node('Box', 'customLayout' + name, rect(0, y, width, extent), {
                background: 'panel',
                radius: 0,
                children: [
                    node(
                        'Scroll',
                        'customLayout' + name + 'Scroll',
                        rect(0, 0, width, extent),
                        {
                            contentHeight,
                            scrollbarId: 'customLayout' + name + 'ScrollBar',
                            children: content
                        }
                    ),
                    node(
                        'Box',
                        'customLayout' + name + 'Divider',
                        rect(0, name === 'Header' ? extent - 1 : 0, width, 1),
                        { background: 'outlineVariant', radius: 0 }
                    )
                ]
            })
        );
    }
    if (tabOffset) {
        const tabs = [];
        let left = 0;
        for (const [index, entry] of cell.layoutTabs.entries()) {
            const size = viewTabWidth(String(entry.title).length * 8);
            tabs.push(
                node('Action', 'layoutTab_' + index, rect(left, 0, size, 42), {
                    enabled: !cell.layoutBusy,
                    action: { type: 'layout-tab', key: entry.key },
                    label: entry.title,
                    children: workspaceTab(size, 42, {
                        title: entry.title,
                        current: entry.key === cell.layoutTabKey,
                        closable: true
                    }).nodes
                })
            );
            tabs.push(
                node(
                    'Action',
                    'layoutCloseTab_' + index,
                    rect(left + size - 34, 7, 28, 28),
                    {
                        enabled: !cell.layoutBusy,
                        label: translate('Close', language),
                        action: { type: 'layout-close-tab', key: entry.key }
                    }
                )
            );
            left += size;
        }
        nodes.push(
            node('Scroll', 'layoutTabs', rect(0, 0, width, 56), {
                contentWidth: left,
                contentHeight: 42,
                scrollbarId: 'layoutTabsBar',
                children: tabs
            })
        );
    }
    nodes.push(
        node(
            'Scroll',
            'customLayoutScroll',
            rect(0, tabOffset + headerHeight, width, bodyHeight),
            {
                contentHeight: extent + (cell.layoutError ? 80 : 0),
                scrollbarId: 'customLayoutScrollBar',
                children
            }
        )
    );
    return { nodes };
}

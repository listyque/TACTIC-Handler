import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { link } from './cells.ui.mjs';
import { quickLayout } from './nested.ui.mjs';
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
    server = ''
) {
    const tabOffset = cell.layoutTabs?.length ? 56 : 0;
    const children = [],
        gap = 8,
        tableHeight = Math.max(320, height - tabOffset - 48);
    const controls = cell.layoutState?.controls || cell.layoutControls || [];
    function draw(
        items,
        x,
        y,
        available,
        prefix = 'customLayout',
        startIndex = 0,
        output = children,
        bottom = Infinity
    ) {
        let top = y;
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
            let extent = 0;
            if (item.children) {
                const horizontal = item.kind === 'row' && available >= 600;
                if (horizontal) {
                    const budget = Math.max(
                        0,
                        available - gap * (item.children.length - 1)
                    );
                    const requested = item.children.map((child) =>
                        /%$/.test(child.width || '')
                            ? (parseFloat(child.width) / 100) * budget
                            : /^\d+(?:px)?$/.test(child.width || '')
                              ? parseFloat(child.width)
                              : 0
                    );
                    const fixed = requested.reduce(
                        (sum, value) => sum + value,
                        0
                    );
                    const flex = item.children.reduce(
                        (sum, child, index) =>
                            sum +
                            (requested[index] ? 0 : Number(child.weight) || 1),
                        0
                    );
                    let left = x;
                    for (const [column, child] of item.children.entries()) {
                        const part = requested[column]
                            ? requested[column] *
                              Math.min(1, budget / Math.max(1, fixed))
                            : (Math.max(0, budget - fixed) *
                                  (Number(child.weight) || 1)) /
                              Math.max(1, flex);
                        extent = Math.max(
                            extent,
                            draw(
                                [child],
                                left,
                                top,
                                part,
                                id,
                                column,
                                output,
                                bottom
                            )
                        );
                        left += part + gap;
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
                        bottom
                    );
            } else if (item.kind === 'metric') {
                extent = 104;
                output.push(
                    node('Box', id, rect(x, top, available, extent), {
                        background: 'panel',
                        border: 'outlineVariant',
                        radiusRole: 'surfaceRadius',
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
                                String(item.value ?? 0),
                                { fontRole: 'hero', weight: 600 }
                            )
                        ]
                    })
                );
            } else if (item.kind === 'text') {
                extent = text
                    ? Math.max(
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
                            wrap: true
                        })
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
                extent = (item.height || tableHeight) + 32;
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
                const itemsExtent = Number.isFinite(item.height)
                    ? item.height
                    : tableHeight;
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
                        item.kind === 'link' ? 'open-in-new' : 'edit',
                        {
                            type: 'service',
                            name:
                                item.kind === 'link' ? 'layout-link' : 'script',
                            href: item.href,
                            javascript: item.javascript,
                            selector: item.selector
                        },
                        item.kind === 'link' || (editable && !cell.layoutBusy),
                        { outlined: true }
                    )
                );
            }
            if (extent) top += extent + gap;
        }
        return Math.max(0, top - y - gap);
    }
    const extent = draw(cell.layoutNodes, 0, 0, Math.max(0, width - 24));
    if (cell.layoutError)
        children.push(
            label(
                'layoutError',
                rect(0, extent + gap, Math.max(0, width - 24), 64),
                cell.layoutError,
                { wrap: true, color: 'error' }
            )
        );
    const nodes = [
        node('Box', 'layoutBackground', rect(0, 0, width, height), {
            background: 'workspace'
        })
    ];
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
            rect(0, tabOffset, width, Math.max(0, height - tabOffset)),
            {
                contentHeight: extent + (cell.layoutError ? 80 : 0),
                scrollbarId: 'customLayoutScrollBar',
                children
            }
        )
    );
    return { nodes };
}

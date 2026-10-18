import { node, rect, label, button } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { captionHeight } from '../../../controls/forms/sections.ui.mjs';

export function layout(nodes) {
    const levels = {},
        slots = {},
        result = {};
    let pending = nodes.slice();
    for (let pass = 0; pending.length && pass <= nodes.length; pass++) {
        const next = [];
        for (const row of pending) {
            if (
                row.parent &&
                nodes.some((node) => node.code === row.parent) &&
                levels[row.parent] === undefined
            ) {
                next.push(row);
                continue;
            }
            levels[row.code] =
                levels[row.parent] === undefined ? 0 : levels[row.parent] + 1;
        }
        if (next.length === pending.length) {
            for (const row of next) levels[row.code] = 0;
            break;
        }
        pending = next;
    }
    for (const row of nodes) {
        const level = levels[row.code] || 0,
            slot = slots[level] || 0;
        slots[level] = slot + 1;
        result[row.code] = { x: 24 + level * 204, y: 24 + slot * 88 };
    }
    return result;
}

export function paint(context, nodes, edges, zoom, color) {
    const positions = layout(nodes);
    context.save();
    context.scale(zoom, zoom);
    for (const edge of edges) {
        const a = positions[edge.source],
            b = positions[edge.target];
        if (!a || !b) continue;
        const x = a.x + 172,
            y = a.y + 32,
            targetX = b.x,
            targetY = b.y + 32;
        context.strokeStyle = color(edge.kind === 'merge' ? 'green' : 'action');
        context.lineWidth = 1.5;
        context.beginPath();
        context.moveTo(x, y);
        context.bezierCurveTo(
            x + 40,
            y,
            targetX - 40,
            targetY,
            targetX,
            targetY
        );
        context.stroke();
        context.beginPath();
        context.moveTo(targetX - 7, targetY - 4);
        context.lineTo(targetX, targetY);
        context.lineTo(targetX - 7, targetY + 4);
        context.stroke();
    }
    context.restore();
}

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language),
        records = model.nodes || [],
        positions = layout(records),
        zoom = Math.max(0.25, Math.min(2, model.zoom || 1)),
        inner = Math.max(0, width - 16);
    const tools = [];
    let left = 0;
    if (model.native) {
        tools.push(
            button(
                'streamGraphNew',
                rect(0, 0, 28, 28),
                tr('New stream'),
                'add',
                { type: 'new' },
                !model.busy,
                { iconOnly: true, iconAction: true }
            )
        );
        left = 32;
    }
    tools.push(
        label(
            'streamGraphTitle',
            rect(left, 0, Math.max(0, inner - left - 160), 28),
            tr('Stream Graph')
        )
    );
    tools.push(
        button(
            'streamGraphZoomOut',
            rect(inner - 156, 0, 28, 28),
            tr('Zoom out'),
            'minus',
            { type: 'zoom', value: Math.max(0.25, zoom - 0.1) },
            true,
            { iconOnly: true, iconAction: true }
        )
    );
    tools.push(
        label(
            'streamGraphZoom',
            rect(inner - 124, 0, 56, 28),
            Math.round(zoom * 100) + '%',
            { color: 'secondaryText', align: 'center' }
        )
    );
    tools.push(
        button(
            'streamGraphZoomIn',
            rect(inner - 64, 0, 28, 28),
            tr('Zoom in'),
            'plus',
            { type: 'zoom', value: Math.min(2, zoom + 0.1) },
            true,
            { iconOnly: true, iconAction: true }
        )
    );
    tools.push(
        button(
            'streamGraphRefresh',
            rect(inner - 28, 0, 28, 28),
            tr('Refresh'),
            'refresh',
            { type: 'refresh' },
            !model.busy,
            { iconOnly: true, iconAction: true }
        )
    );
    const hint = tr(
            model.native
                ? 'Parent links and submitted integrations. Double-click a stream to edit its settings.'
                : 'Parent links and submitted integrations.'
        ),
        hintHeight = Math.max(24, captionHeight(hint, inner) * 1.2),
        top = 44 + hintHeight;
    const footer = width < 500 ? 78 : 36;
    const contentWidth = Math.max(
        inner - 16,
        ...records.map((row) => (positions[row.code].x + 180) * zoom)
    );
    const contentHeight = Math.max(
        0,
        height - top - footer - 16,
        ...records.map((row) => (positions[row.code].y + 84) * zoom)
    );
    const children = [
        node(
            'View',
            'streamGraphEdges',
            rect(0, 0, contentWidth, contentHeight),
            { view: 'streamGraphEdges' }
        )
    ];
    for (const row of records) {
        const point = positions[row.code],
            chosen = model.selected === row.code;
        children.push(
            node(
                'Box',
                'streamGraphNodeSurface_' + row.code,
                rect(point.x * zoom, point.y * zoom, 172, 64),
                {
                    scale: zoom,
                    contextAction: model.native
                        ? { type: 'menu', key: row.code }
                        : null,
                    children: [
                        node(
                            'Action',
                            'streamGraphNode_' + row.code,
                            rect(0, 0, 172, 64),
                            {
                                text: row.code,
                                role: 'option',
                                selected: chosen,
                                normalColor: 'panel',
                                selectedColor: 'selected',
                                radius: 10,
                                action: { type: 'select', key: row.code },
                                doubleAction: model.native
                                    ? { type: 'edit', key: row.code }
                                    : null,
                                children: [
                                    label(
                                        'streamGraphNodeTitle',
                                        rect(8, 6, 156, 24),
                                        row.title || row.code,
                                        {
                                            fontRole: 'secondary',
                                            elideMiddle: true
                                        }
                                    ),
                                    label(
                                        'streamGraphNodeDetails',
                                        rect(8, 34, 156, 22),
                                        (row.stream_type || '') +
                                            ' · #' +
                                            row.revision +
                                            ' · ' +
                                            row.depot,
                                        {
                                            color: 'secondaryText',
                                            fontRole: 'secondary'
                                        }
                                    )
                                ]
                            }
                        )
                    ]
                }
            )
        );
    }
    const nodes = [
        node('Box', 'streamGraphBackground', rect(0, 0, width, height), {
            background: 'panelDeep',
            radius: 14
        }),
        node('Box', 'streamGraphTools', rect(8, 8, inner, 28), {
            children: tools
        }),
        label('streamGraphHint', rect(8, 40, inner, hintHeight), hint, {
            color: 'secondaryText',
            wrap: true
        }),
        node(
            'Scroll',
            'streamGraphScroll',
            rect(8, top, inner, Math.max(0, height - top - footer)),
            {
                contentWidth,
                contentHeight,
                scrollbarId: 'streamGraphScrollBar',
                children: [
                    node(
                        'Box',
                        'streamGraphPlane',
                        rect(0, 0, contentWidth, contentHeight),
                        {
                            children,
                            contextAction: model.native
                                ? { type: 'menu', key: '' }
                                : null
                        }
                    )
                ]
            }
        )
    ];
    const selected = records.find((row) => row.code === model.selected);
    nodes.push(
        label(
            'streamGraphSelection',
            rect(
                8,
                height - footer + 4,
                Math.max(0, inner - (width < 500 ? 0 : 300)),
                28
            ),
            selected
                ? selected.code + ' · #' + selected.revision
                : tr('Select a stream'),
            { color: 'secondaryText', elideMiddle: true }
        )
    );
    const y = height - 36;
    if (model.after)
        nodes.push(
            button(
                'streamGraphMore',
                rect(
                    width < 500 ? 8 : width - 300,
                    y,
                    width < 500 ? (inner - 8) / 2 : 140,
                    32
                ),
                tr('Next page'),
                'chevron-right',
                { type: 'more' },
                !model.busy
            )
        );
    if (model.edgesAfter)
        nodes.push(
            button(
                'streamGraphMoreEdges',
                rect(
                    width < 500 ? 16 + (inner - 8) / 2 : width - 152,
                    y,
                    width < 500 ? (inner - 8) / 2 : 144,
                    32
                ),
                tr('Next connections'),
                'chevron-right',
                { type: 'moreEdges' },
                !model.busy
            )
        );
    return { nodes };
}

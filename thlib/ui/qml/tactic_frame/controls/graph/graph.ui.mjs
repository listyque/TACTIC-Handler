import { node, rect, label, muted } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { bounds, curves, curvePoint } from './graph.state.mjs';
import { metrics } from '../../core/foundation.mjs';

function toolbarLayout(definition) {
    const width = Math.max(
        0,
        definition.width - (definition.toolbarRightInset || 0)
    );
    if (definition.toolbar === false || width < 36)
        return { height: 0, columns: 0, label: false };
    const label = width >= 202;
    const columns = label
        ? 4
        : Math.max(1, Math.min(4, Math.floor((width + 2) / 38)));
    return { label, columns, height: Math.ceil(4 / columns) * 38 - 2 };
}

export function viewport(definition) {
    const toolbar = toolbarLayout(definition);
    const top = toolbar.height ? toolbar.height + 6 : 0;
    return {
        x: 0,
        y: top,
        width: Math.max(1, definition.width - 16),
        height: Math.max(1, definition.height - top - 16)
    };
}
export function toolbar(definition, ui, language) {
    const layout = toolbarLayout(definition);
    if (!layout.columns)
        return {
            nodes: []
        };
    const tr = (text) => translate(text, language),
        width = definition.width,
        actions = [
            [
                'graphZoomOut',
                'Zoom out',
                'zoom-out',
                {
                    type: 'zoom',
                    value: ui.zoom - 0.1
                }
            ],
            [
                'graphZoomIn',
                'Zoom in',
                'zoom-in',
                {
                    type: 'zoom',
                    value: ui.zoom + 0.1
                }
            ],
            [
                'graphReset',
                'Reset view',
                'refresh',
                {
                    type: 'reset'
                }
            ],
            [
                'graphReveal',
                'Center selection',
                'fit-width',
                {
                    type: 'reveal'
                }
            ]
        ];
    const nodes = layout.label
        ? [
              label(
                  'graphZoomLabel',
                  rect(0, 0, 50, 36),
                  Math.round(ui.zoom * 100) + '%',
                  muted
              )
          ]
        : [];
    actions.forEach((action, index) =>
        nodes.push(
            node(
                'Button',
                action[0],
                rect(
                    (layout.label ? 52 : 0) + (index % layout.columns) * 38,
                    Math.floor(index / layout.columns) * 38,
                    36,
                    36
                ),
                {
                    text: tr(action[1]),
                    icon: action[2],
                    iconOnly: true,
                    action: action[3]
                }
            )
        )
    );
    if (width > 440 && definition.help !== false)
        nodes.push(
            label(
                'graphHelp',
                rect(214, 0, width - 218, 36),
                tr(
                    definition.readOnly
                        ? 'Wheel: zoom · Middle button: pan'
                        : 'Drag: move · Ctrl/Shift: select · F: center'
                ),
                {
                    color: 'secondaryText'
                }
            )
        );
    return {
        nodes
    };
}
const tint = (base, accent, amount) => ({
    mix: [base, accent, amount]
});
export function describe(definition, ui, language) {
    const tr = (text) => translate(text, language),
        nodes = [],
        selected = definition.selectedNodes || [];
    for (const edge of curves(ui, definition)) {
        if (edge.pending) continue;
        const p = curvePoint(edge, 0.6),
            title =
                (edge.label ? edge.label + ' · ' : '') +
                edge.from +
                ' → ' +
                edge.to;
        nodes.push(
            node(
                'Action',
                'graphEdge_' + edge.index,
                rect(p.x - ui.world.x - 18, p.y - ui.world.y - 18, 36, 36),
                {
                    text: title,
                    enabled: definition.selectionEnabled !== false,
                    selected: definition.selectedEdge === edge.index,
                    normalColor: 'transparent',
                    selectedColor: 'transparent',
                    action: {
                        type: 'activate',
                        target: {
                            kind: 'edge',
                            index: edge.index
                        }
                    }
                }
            )
        );
    }
    for (const record of definition.nodes || []) {
        const box = bounds(ui, record, definition.style),
            accent =
                record.kind === 'missing' ? 'error' : record.color || 'action',
            circular = record.kind === 'progress',
            chosen = selected.indexOf(record.identity) >= 0;
        const content = [
            node(
                'Box',
                'graphNodeSurface_' + record.identity,
                rect(0, 0, box.width, box.height),
                {
                    background: tint(
                        'surfaceContainer',
                        accent,
                        chosen ? 0.26 : 0.12
                    ),
                    border: chosen
                        ? accent
                        : tint('outlineVariant', accent, 0.5),
                    borderWidth: chosen ? 2 : 1,
                    radius: circular
                        ? box.width / 2
                        : metrics(definition.style).itemRadius
                }
            )
        ];
        content.push(
            label(
                'graphNodeTitle_' + record.identity,
                rect(
                    circular ? 8 : 22,
                    circular
                        ? (box.height - 28) / 2
                        : 12 + (box.height - 72) / 2,
                    box.width - (circular ? 16 : 44),
                    28
                ),
                record.label || record.identity,
                {
                    weight: 600,
                    align: circular ? 'center' : 'left'
                }
            )
        );
        if (!circular)
            content.push(
                label(
                    'graphNodeKind_' + record.identity,
                    rect(22, 44 + (box.height - 72) / 2, box.width - 44, 18),
                    record.pendingCreation
                        ? tr('New · many-to-many')
                        : record.kind === 'instance'
                          ? 'many-to-many'
                          : record.kind === 'missing'
                            ? tr('Missing process')
                            : record.kind || '',
                    muted
                )
            );
        nodes.push(
            node(
                'Action',
                'graphNode_' + record.identity,
                rect(
                    box.x - ui.world.x,
                    box.y - ui.world.y,
                    box.width,
                    box.height
                ),
                {
                    text: record.label || record.identity,
                    role: 'option',
                    selected: chosen,
                    enabled: definition.selectionEnabled !== false,
                    normalColor: 'transparent',
                    selectedColor: 'transparent',
                    children: content,
                    action: {
                        type: 'activate',
                        target: {
                            kind: 'node',
                            identity: record.identity
                        }
                    }
                }
            )
        );
        if (!definition.readOnly && !record.referenceOnly)
            for (const input of [true, false]) {
                const active =
                    ui.pending &&
                    (ui.pending.input === input
                        ? ui.pending.identity === record.identity
                        : ui.pending.identity !== record.identity);
                const children = [
                    node(
                        'Box',
                        'graphPortSurface_' +
                            (input ? 'in_' : 'out_') +
                            record.identity,
                        rect(12, 12, 12, 12),
                        {
                            radius: 6,
                            border: accent,
                            borderWidth: 2,
                            background: active || !input ? accent : 'workspace'
                        }
                    )
                ];
                nodes.push(
                    node(
                        'Action',
                        (input ? 'graphInput_' : 'graphOutput_') +
                            record.identity,
                        rect(
                            box.x - ui.world.x + (input ? -18 : box.width - 18),
                            box.y - ui.world.y + 18,
                            36,
                            36
                        ),
                        {
                            text: tr(
                                input
                                    ? 'Input — connect here'
                                    : 'Output — connect here'
                            ),
                            normalColor: 'transparent',
                            selectedColor: 'transparent',
                            children,
                            action: {
                                type: 'activate',
                                target: {
                                    kind: 'port',
                                    identity: record.identity,
                                    input
                                }
                            }
                        }
                    )
                );
            }
    }
    return {
        nodes
    };
}

// Both Canvas2D hosts call the same paint routine; no domain state is mutated.
export function paint(context, definition, ui, viewportSize, color, selection) {
    context.clearRect(0, 0, viewportSize.width, viewportSize.height);
    context.save();
    context.scale(ui.zoom, ui.zoom);
    context.translate(-ui.x, -ui.y);
    for (const edge of curves(ui, definition)) {
        context.strokeStyle = color(
            definition.selectedEdge === edge.index ? 'primaryText' : edge.color
        );
        context.lineWidth = definition.selectedEdge === edge.index ? 3.5 : 2.5;
        context.beginPath();
        context.moveTo(edge.x1, edge.y1);
        context.bezierCurveTo(
            edge.x1 + edge.bend,
            edge.y1,
            edge.x2 - edge.bend,
            edge.y2,
            edge.x2,
            edge.y2
        );
        context.stroke();
        const p = curvePoint(edge, 0.6),
            before = curvePoint(edge, 0.59),
            after = curvePoint(edge, 0.61),
            angle = Math.atan2(after.y - before.y, after.x - before.x);
        context.save();
        context.translate(p.x, p.y);
        context.rotate(angle);
        context.fillStyle = context.strokeStyle;
        context.beginPath();
        context.moveTo(-6, -5);
        context.lineTo(6, 0);
        context.lineTo(-6, 5);
        context.closePath();
        context.fill();
        context.restore();
    }
    if (selection) {
        context.fillStyle = color(tint('workspace', 'action', 0.14));
        context.strokeStyle = color('action');
        context.lineWidth = 1 / ui.zoom;
        context.fillRect(
            selection.x,
            selection.y,
            selection.width,
            selection.height
        );
        context.strokeRect(
            selection.x,
            selection.y,
            selection.width,
            selection.height
        );
    }
    context.restore();
}

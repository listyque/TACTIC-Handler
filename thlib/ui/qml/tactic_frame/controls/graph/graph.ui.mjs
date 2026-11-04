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
function overlapArea(a, b) {
    const w = Math.min(a.x + a.width, b.x + b.width) - Math.max(a.x, b.x),
        h = Math.min(a.y + a.height, b.y + b.height) - Math.max(a.y, b.y);
    return w > 0 && h > 0 ? w * h : 0;
}
export function describe(definition, ui, language) {
    const tr = (text) => translate(text, language),
        nodes = [],
        selected = definition.selectedNodes || [],
        nodeBoxes = (definition.nodes || []).map((record) => {
            const b = bounds(ui, record, definition.style);
            return {
                x: b.x - 6,
                y: b.y - 6,
                width: b.width + 12,
                height: b.height + 12
            };
        }),
        placedBadges = [];
    for (const edge of curves(ui, definition)) {
        if (edge.pending) continue;
        const badgeLines = Array.isArray(edge.badgeLines)
                ? edge.badgeLines.filter(Boolean)
                : [],
            chosenEdge = definition.selectedEdge === edge.index,
            title =
                edge.tooltip ||
                (edge.label ? edge.label + ' · ' : '') +
                    edge.from +
                    ' → ' +
                    edge.to;
        if (badgeLines.length) {
            const maxLen = Math.max.apply(
                    null,
                    badgeLines.map((line) => String(line).length)
                ),
                badgeW = Math.max(
                    84,
                    Math.min(290, Math.round(maxLen * 6.8 + 24))
                ),
                badgeH = badgeLines.length > 1 ? 42 : 24,
                candidates = edge.selfLoop
                    ? [0.5]
                    : [0.5, 0.36, 0.64, 0.28, 0.72];
            let bestP = curvePoint(edge, candidates[0]),
                bestScore = Infinity;
            for (const t of candidates) {
                const pt = curvePoint(edge, t),
                    box = {
                        x: pt.x - badgeW / 2 - 4,
                        y: pt.y - badgeH / 2 - 4,
                        width: badgeW + 8,
                        height: badgeH + 8
                    };
                let score = 0;
                for (const nb of nodeBoxes) score += overlapArea(box, nb) * 4;
                for (const pb of placedBadges) score += overlapArea(box, pb);
                if (score < bestScore) {
                    bestScore = score;
                    bestP = pt;
                    if (score === 0) break;
                }
            }
            placedBadges.push({
                x: bestP.x - badgeW / 2,
                y: bestP.y - badgeH / 2,
                width: badgeW,
                height: badgeH
            });
            const accent = edge.color || 'action',
                children = [
                    node(
                        'Box',
                        'graphEdgeBadge_' + edge.index,
                        rect(0, 0, badgeW, badgeH),
                        {
                            background: tint(
                                'surfaceContainerHigh',
                                accent,
                                chosenEdge ? 0.34 : 0.16
                            ),
                            border: chosenEdge ? 'primaryText' : accent,
                            borderWidth: chosenEdge ? 2 : 1,
                            radius: 11
                        }
                    ),
                    label(
                        'graphEdgeLabelPrimary_' + edge.index,
                        rect(8, 3, badgeW - 16, 18),
                        badgeLines[0],
                        {
                            align: 'center',
                            fontRole: 'caption',
                            weight: 600,
                            monospace: !!edge.primaryMono
                        }
                    )
                ];
            if (badgeLines.length > 1)
                children.push(
                    label(
                        'graphEdgeLabelSecondary_' + edge.index,
                        rect(8, 21, badgeW - 16, 18),
                        badgeLines[1],
                        {
                            align: 'center',
                            fontRole: 'caption',
                            monospace: true,
                            color: 'secondaryText'
                        }
                    )
                );
            nodes.push(
                node(
                    'Action',
                    'graphEdge_' + edge.index,
                    rect(
                        bestP.x - ui.world.x - badgeW / 2,
                        bestP.y - ui.world.y - badgeH / 2,
                        badgeW,
                        badgeH
                    ),
                    {
                        layer: 2,
                        text: title,
                        enabled: definition.selectionEnabled !== false,
                        selected: chosenEdge,
                        normalColor: 'transparent',
                        hoverColor: 'transparent',
                        pressedColor: 'transparent',
                        selectedColor: 'transparent',
                        children,
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
        } else {
            const p = curvePoint(edge, 0.6);
            nodes.push(
                node(
                    'Action',
                    'graphEdge_' + edge.index,
                    rect(
                        p.x - ui.world.x - 18,
                        p.y - ui.world.y - 18,
                        36,
                        36
                    ),
                    {
                        text: title,
                        enabled: definition.selectionEnabled !== false,
                        selected: chosenEdge,
                        normalColor: 'transparent',
                        hoverColor: 'transparent',
                        pressedColor: 'transparent',
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
    }
    for (const record of definition.nodes || []) {
        const box = bounds(ui, record, definition.style),
            rawKind = record.kind || '',
            vKind =
                record.visualKind ||
                (rawKind === 'missing' || rawKind === 'reference'
                    ? 'missing'
                    : record.draftType
                      ? 'draft'
                      : record.pendingCreation ||
                          rawKind === 'instance' ||
                          /(^|\/)[a-z0-9_]+_in_[a-z0-9_]+$/i.test(
                              record.identity || ''
                          )
                        ? 'instance'
                        : /^(sthpw|config)\//i.test(record.identity || '')
                          ? 'system'
                          : [
                                'manual',
                                'action',
                                'condition',
                                'approval',
                                'hierarchy',
                                'dependency',
                                'progress',
                                'status',
                                'search_type'
                            ].indexOf(rawKind) >= 0
                            ? rawKind
                            : String(record.identity || '').indexOf('/') >= 0
                              ? 'search_type'
                              : rawKind || 'manual'),
            defaultColor =
                vKind === 'action'
                    ? '#2e9b88'
                    : vKind === 'condition'
                      ? '#cf8a2e'
                      : vKind === 'approval'
                        ? '#8a5ec4'
                        : vKind === 'hierarchy'
                          ? '#3e8eb8'
                          : vKind === 'dependency'
                            ? '#c76a3e'
                            : vKind === 'progress'
                              ? '#49a065'
                              : vKind === 'status'
                                ? '#5b73c7'
                                : vKind === 'instance'
                                  ? '#488599'
                                  : vKind === 'draft'
                                    ? '#c7923e'
                                    : vKind === 'system'
                                      ? '#9a9248'
                                      : vKind === 'external'
                                        ? '#7a6fa8'
                                        : 'action',
            accent =
                record.kind === 'missing' || vKind === 'missing'
                    ? 'error'
                    : record.color || defaultColor,
            circular = record.kind === 'progress' || vKind === 'progress',
            pill =
                !circular &&
                (vKind === 'action' ||
                    vKind === 'approval' ||
                    vKind === 'instance'),
            nodeRadius = circular
                ? Math.round(box.width / 2)
                : pill
                  ? Math.round(box.height / 2)
                  : vKind === 'manual'
                    ? 6
                    : vKind === 'condition'
                      ? 16
                      : vKind === 'hierarchy' || vKind === 'dependency'
                        ? 14
                        : vKind === 'system' ||
                            vKind === 'external' ||
                            vKind === 'search_type'
                          ? 8
                          : metrics(definition.style).itemRadius,
            iconName =
                record.icon ||
                (vKind === 'missing'
                    ? 'warning'
                    : vKind === 'action'
                      ? 'bolt'
                      : vKind === 'condition'
                        ? 'help'
                        : vKind === 'approval'
                          ? 'approval'
                          : vKind === 'hierarchy'
                            ? 'hierarchy'
                            : vKind === 'dependency' || vKind === 'instance'
                              ? 'link'
                              : vKind === 'progress'
                                ? 'progress'
                                : vKind === 'status'
                                  ? 'status'
                                  : vKind === 'draft'
                                    ? 'edit'
                                    : vKind === 'system'
                                      ? 'dns'
                                      : vKind === 'external'
                                        ? 'folder'
                                        : vKind === 'search_type'
                                          ? 'table-view'
                                          : 'person'),
            badgeText =
                record.badgeText !== undefined
                    ? record.badgeText
                    : vKind === 'instance'
                      ? 'M:N'
                      : vKind === 'draft'
                        ? tr('DRAFT')
                        : '',
            chosen = selected.indexOf(record.identity) >= 0,
            hasSecondary = !circular && !!record.secondarySubtitle;
        const content = [
            node(
                'Box',
                'graphNodeSurface_' + record.identity,
                rect(0, 0, box.width, box.height),
                {
                    background: tint(
                        'surfaceContainer',
                        accent,
                        chosen ? 0.28 : pill ? 0.18 : 0.12
                    ),
                    border: chosen
                        ? accent
                        : tint('outlineVariant', accent, pill ? 0.72 : 0.52),
                    borderWidth: chosen ? 2 : 1,
                    radius: nodeRadius,
                    shadow: {
                        y: chosen ? 6 : 3,
                        blur: chosen ? 20 : 12,
                        opacity: chosen ? 0.38 : 0.22
                    }
                }
            )
        ];
        if (circular || vKind === 'approval' || vKind === 'instance') {
            content.push(
                node(
                    'Box',
                    'graphNodeInnerRing_' + record.identity,
                    rect(4, 4, box.width - 8, box.height - 8),
                    {
                        background: 'transparent',
                        border: tint(
                            'outlineVariant',
                            accent,
                            vKind === 'approval' ? 0.65 : 0.42
                        ),
                        borderWidth: 1,
                        radius: Math.max(4, nodeRadius - 4)
                    }
                )
            );
        }
        if (vKind === 'manual' || vKind === 'search_type') {
            content.push(
                node(
                    'Box',
                    'graphNodeLeftBar_' + record.identity,
                    rect(0, 6, 5, Math.max(8, box.height - 12)),
                    {
                        background: accent,
                        radius: 2
                    }
                )
            );
        } else if (vKind === 'condition') {
            content.push(
                node(
                    'Box',
                    'graphNodeDiamondTop_' + record.identity,
                    rect(Math.round(box.width / 2) - 18, 0, 36, 3),
                    {
                        background: accent,
                        radius: 2
                    }
                ),
                node(
                    'Box',
                    'graphNodeDiamondBottom_' + record.identity,
                    rect(
                        Math.round(box.width / 2) - 18,
                        box.height - 3,
                        36,
                        3
                    ),
                    {
                        background: accent,
                        radius: 2
                    }
                )
            );
        } else if (vKind === 'hierarchy') {
            content.push(
                node(
                    'Box',
                    'graphNodeTopBar_' + record.identity,
                    rect(14, 0, 64, 4),
                    {
                        background: accent,
                        radius: 2
                    }
                ),
                node(
                    'Box',
                    'graphNodeBottomBar_' + record.identity,
                    rect(14, box.height - 4, box.width - 28, 3),
                    {
                        background: tint('outlineVariant', accent, 0.7),
                        radius: 2
                    }
                )
            );
        } else if (vKind === 'dependency') {
            content.push(
                node(
                    'Box',
                    'graphNodeLeftBar_' + record.identity,
                    rect(3, 10, 4, Math.max(8, box.height - 20)),
                    {
                        background: accent,
                        radius: 2
                    }
                ),
                node(
                    'Box',
                    'graphNodeRightBar_' + record.identity,
                    rect(box.width - 7, 10, 4, Math.max(8, box.height - 20)),
                    {
                        background: accent,
                        radius: 2
                    }
                )
            );
        } else if (
            vKind === 'status' ||
            vKind === 'system' ||
            vKind === 'external'
        ) {
            content.push(
                node(
                    'Box',
                    'graphNodeTopBar_' + record.identity,
                    rect(10, 0, box.width - 20, 3),
                    {
                        background: accent,
                        radius: 2
                    }
                )
            );
        } else if (vKind === 'draft' || vKind === 'missing') {
            for (let seg = 0; seg < 4; seg++) {
                const sx = 16 + seg * 42;
                if (sx + 24 <= box.width - 12) {
                    content.push(
                        node(
                            'Box',
                            'graphNodeDashTop_' + seg + '_' + record.identity,
                            rect(sx, 0, 24, 3),
                            {
                                background: accent,
                                radius: 1
                            }
                        ),
                        node(
                            'Box',
                            'graphNodeDashBot_' + seg + '_' + record.identity,
                            rect(sx, box.height - 3, 24, 3),
                            {
                                background: accent,
                                radius: 1
                            }
                        )
                    );
                }
            }
        }
        if (circular) {
            content.push(
                node(
                    'Icon',
                    'graphNodeIcon_' + record.identity,
                    rect(Math.round((box.width - 16) / 2), 10, 16, 16),
                    {
                        icon: iconName,
                        color: accent
                    }
                ),
                label(
                    'graphNodeTitle_' + record.identity,
                    rect(8, Math.round((box.height - 24) / 2), box.width - 16, 24),
                    record.label || record.identity,
                    {
                        weight: 600,
                        align: 'center'
                    }
                ),
                label(
                    'graphNodeKind_' + record.identity,
                    rect(10, box.height - 24, box.width - 20, 16),
                    badgeText || '%',
                    {
                        align: 'center',
                        fontRole: 'caption',
                        weight: 600,
                        color: 'secondaryText'
                    }
                )
            );
        } else {
            const topY = (hasSecondary ? 6 : 11) + (box.height - 72) / 2,
                badgeW = badgeText
                    ? Math.max(32, Math.round(String(badgeText).length * 6.5 + 12))
                    : 0;
            content.push(
                node(
                    'Box',
                    'graphNodeIconBg_' + record.identity,
                    rect(12, Math.round(topY + 1), 22, 22),
                    {
                        background: tint('surfaceContainerHigh', accent, 0.28),
                        border: tint('outlineVariant', accent, 0.65),
                        borderWidth: 1,
                        radius: pill ? 11 : vKind === 'condition' ? 6 : 5
                    }
                ),
                node(
                    'Icon',
                    'graphNodeIcon_' + record.identity,
                    rect(16, Math.round(topY + 5), 14, 14),
                    {
                        icon: iconName,
                        color: accent
                    }
                )
            );
            if (badgeW) {
                content.push(
                    node(
                        'Box',
                        'graphNodeBadgeBg_' + record.identity,
                        rect(
                            box.width - badgeW - 10,
                            Math.round(topY + 3),
                            badgeW,
                            18
                        ),
                        {
                            background: tint(
                                'surfaceContainerHigh',
                                accent,
                                0.26
                            ),
                            border: tint('outlineVariant', accent, 0.6),
                            borderWidth: 1,
                            radius: 9
                        }
                    ),
                    label(
                        'graphNodeBadge_' + record.identity,
                        rect(
                            box.width - badgeW - 6,
                            Math.round(topY + 3),
                            badgeW - 8,
                            18
                        ),
                        badgeText,
                        {
                            align: 'center',
                            fontRole: 'caption',
                            weight: 600,
                            monospace: true
                        }
                    )
                );
            }
            content.push(
                label(
                    'graphNodeTitle_' + record.identity,
                    rect(
                        40,
                        topY,
                        Math.max(
                            24,
                            box.width - 40 - (badgeW ? badgeW + 16 : 12)
                        ),
                        hasSecondary ? 24 : 26
                    ),
                    record.label || record.identity,
                    {
                        weight: 600,
                        align: 'left'
                    }
                ),
                label(
                    'graphNodeKind_' + record.identity,
                    rect(
                        40,
                        (hasSecondary ? 31 : 42) + (box.height - 72) / 2,
                        box.width - 52,
                        18
                    ),
                    record.subtitle !== undefined
                        ? record.subtitle
                        : record.pendingCreation
                          ? tr('New · many-to-many')
                          : record.kind === 'instance'
                            ? 'many-to-many'
                            : record.kind === 'missing'
                              ? tr('Missing process')
                              : record.kind || '',
                    muted
                )
            );
            if (hasSecondary)
                content.push(
                    label(
                        'graphNodeSubkind_' + record.identity,
                        rect(
                            40,
                            49 + (box.height - 72) / 2,
                            box.width - 52,
                            17
                        ),
                        record.secondarySubtitle,
                        {
                            fontRole: 'caption',
                            monospace: true,
                            color: 'secondaryText'
                        }
                    )
                );
        }
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
                    radius: nodeRadius,
                    selected: chosen,
                    enabled: definition.selectionEnabled !== false,
                    normalColor: 'transparent',
                    hoverColor: 'transparent',
                    pressedColor: 'transparent',
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
                                    ? 'Input (to / parent) — connect here'
                                    : 'Output (from / child) — connect here'
                            ),
                            normalColor: 'transparent',
                            hoverColor: 'transparent',
                            pressedColor: 'transparent',
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
    if (ui.menu && definition.contextMenu && !definition.readOnly) {
        const target = ui.menu.target || { kind: 'selection' },
            wx = Math.round((ui.menu.worldX || 0) - 100),
            wy = Math.round((ui.menu.worldY || 0) - 36),
            items = [];
        if (definition.contextMenu === 'schema') {
            if (target.kind === 'node') {
                const hitNode = (definition.nodes || []).find(
                    (row) => row.identity === target.identity
                );
                if (hitNode && hitNode.draftType) {
                    items.push(
                        [
                            'graphMenu_registerDraftNow',
                            tr('Register Search Type in DB now'),
                            'check',
                            {
                                type: 'registerDraftType',
                                identity: target.identity
                            }
                        ],
                        [
                            'graphMenu_openDraftCreator',
                            tr('Open full Search Type creator…'),
                            'tune',
                            {
                                type: 'openDraftCreator',
                                identity: target.identity
                            }
                        ]
                    );
                }
                if (!hitNode || !hitNode.referenceOnly) {
                    items.push(
                        [
                            'graphMenu_startConnect',
                            tr('Start connection from here'),
                            'arrow-forward',
                            {
                                internal: {
                                    type: 'activate',
                                    target: {
                                        kind: 'port',
                                        identity: target.identity,
                                        input: false
                                    }
                                }
                            }
                        ],
                        [
                            'graphMenu_connectNodeMany',
                            tr('Connect Many-to-Many (M:N)…'),
                            'link',
                            {
                                type: 'openConnectManyToMany',
                                source: target.identity
                            }
                        ]
                    );
                }
                if (
                    hitNode &&
                    !hitNode.draftType &&
                    !hitNode.pendingCreation &&
                    !hitNode.referenceOnly
                ) {
                    items.push([
                        'graphMenu_nodeWorkflows',
                        tr('Workflows'),
                        'schema',
                        {
                            type: 'nodeWorkflows'
                        }
                    ]);
                }
                if (!hitNode || !hitNode.referenceOnly) {
                    items.push([
                        'graphMenu_removeNode',
                        tr('Remove from canvas'),
                        'delete',
                        {
                            type: 'remove'
                        },
                        true
                    ]);
                }
            } else if (target.kind === 'edge') {
                const hitEdge = (definition.edges || [])[target.index];
                if (!hitEdge || hitEdge.relationship !== 'instance') {
                    items.push([
                        'graphMenu_makeManyToMany',
                        tr('Convert to Many-to-Many (M:N)'),
                        'link',
                        {
                            type: 'relationship',
                            value: 'many_to_many'
                        }
                    ]);
                }
                items.push(
                    [
                        'graphMenu_setHierarchy',
                        tr('Set as Hierarchy (Child → Parent)'),
                        'hierarchy',
                        {
                            type: 'edgePreset',
                            preset: 'hierarchy'
                        }
                    ],
                    [
                        'graphMenu_setCode',
                        tr('Set as Direct key (code)'),
                        'code',
                        {
                            type: 'edgePreset',
                            preset: 'code'
                        }
                    ],
                    [
                        'graphMenu_reverseEdge',
                        tr('Reverse direction (from ↔ to)'),
                        'refresh',
                        {
                            type: 'reverse'
                        }
                    ],
                    [
                        'graphMenu_removeEdge',
                        tr('Remove connection'),
                        'delete',
                        {
                            type: 'remove'
                        },
                        true
                    ]
                );
            } else {
                items.push(
                    [
                        'graphMenu_draftNode',
                        tr('New draft node ("skeleton")'),
                        'add',
                        {
                            type: 'createDraftNode',
                            x: wx,
                            y: wy
                        }
                    ],
                    [
                        'graphMenu_createType',
                        tr('Create & register Search Type…'),
                        'table',
                        {
                            type: 'createType',
                            x: wx,
                            y: wy
                        }
                    ],
                    [
                        'graphMenu_addExisting',
                        tr('Add existing Search Type…'),
                        'search',
                        {
                            type: 'openAddNodeAt',
                            x: wx,
                            y: wy
                        }
                    ],
                    [
                        'graphMenu_connectMany',
                        tr('New Many-to-Many (M:N) relation…'),
                        'link',
                        {
                            type: 'openConnectManyToMany'
                        }
                    ],
                    [
                        'graphMenu_arrange',
                        tr('Arrange nodes'),
                        'hierarchy',
                        {
                            type: 'layout'
                        }
                    ],
                    [
                        'graphMenu_reset',
                        tr('Reset view'),
                        'refresh',
                        {
                            internal: {
                                type: 'reset'
                            }
                        }
                    ]
                );
            }
        } else if (definition.contextMenu === 'workflow') {
            if (target.kind === 'node') {
                items.push(
                    [
                        'graphMenu_startConnect',
                        tr('Start connection from here'),
                        'arrow-forward',
                        {
                            internal: {
                                type: 'activate',
                                target: {
                                    kind: 'port',
                                    identity: target.identity,
                                    input: false
                                }
                            }
                        }
                    ],
                    [
                        'graphMenu_removeNode',
                        tr('Remove from canvas'),
                        'delete',
                        {
                            type: 'remove'
                        },
                        true
                    ]
                );
            } else if (target.kind === 'edge') {
                items.push([
                    'graphMenu_removeEdge',
                    tr('Remove connection'),
                    'delete',
                    {
                        type: 'remove'
                    },
                    true
                ]);
            } else {
                items.push(
                    [
                        'graphMenu_addProcess',
                        tr('Add process here'),
                        'add',
                        {
                            type: 'createProcessAt',
                            x: wx,
                            y: wy
                        }
                    ],
                    [
                        'graphMenu_arrange',
                        tr('Arrange nodes'),
                        'hierarchy',
                        {
                            type: 'layout'
                        }
                    ],
                    [
                        'graphMenu_reset',
                        tr('Reset view'),
                        'refresh',
                        {
                            internal: {
                                type: 'reset'
                            }
                        }
                    ]
                );
            }
        }
        if (items.length) {
            const vp = viewport(definition),
                menuW = 296,
                menuH = items.length * 40 + 12,
                mx = Math.max(
                    8,
                    Math.min(Math.max(8, vp.width - menuW - 8), ui.menu.x || 0)
                ),
                my = Math.max(
                    8,
                    Math.min(
                        Math.max(8, vp.height - menuH - 8),
                        ui.menu.y || 0
                    )
                ),
                worldX = ui.x + mx / ui.zoom - ui.world.x,
                worldY = ui.y + my / ui.zoom - ui.world.y;
            nodes.push(
                node(
                    'Box',
                    'graphContextMenu',
                    rect(worldX, worldY, menuW, menuH),
                    {
                        layer: 30,
                        scale: 1 / ui.zoom,
                        background: 'surfaceContainerHigh',
                        border: 'outlineVariant',
                        radius: 10,
                        shadow: { y: 8, blur: 24, opacity: 0.36 },
                        children: items.map(
                            ([id, text, icon, cmd, destructive], idx) =>
                                node(
                                    'Button',
                                    id,
                                    rect(6, 6 + idx * 40, menuW - 12, 36),
                                    {
                                        text,
                                        icon,
                                        enabled: true,
                                        round: false,
                                        destructive: !!destructive,
                                        pressAction: {
                                            type: 'menuCommand',
                                            command: cmd
                                        },
                                        action: {
                                            type: 'menuCommand',
                                            command: cmd
                                        }
                                    }
                                )
                        )
                    }
                )
            );
        }
    }
    return {
        nodes
    };
}

export function paintBounds(definition, ui, viewportSize, selection) {
    let left = Infinity,
        top = Infinity,
        right = -Infinity,
        bottom = -Infinity;
    for (const edge of curves(ui, definition)) {
        const cy1 = edge.cy1 === undefined ? edge.y1 : edge.cy1,
            cy2 = edge.cy2 === undefined ? edge.y2 : edge.cy2;
        left = Math.min(
            left,
            edge.x1,
            edge.x2,
            edge.x1 + edge.bend,
            edge.x2 - edge.bend
        );
        right = Math.max(
            right,
            edge.x1,
            edge.x2,
            edge.x1 + edge.bend,
            edge.x2 - edge.bend
        );
        top = Math.min(top, edge.y1, edge.y2, cy1, cy2);
        bottom = Math.max(bottom, edge.y1, edge.y2, cy1, cy2);
    }
    if (selection) {
        left = Math.min(left, selection.x);
        right = Math.max(right, selection.x + selection.width);
        top = Math.min(top, selection.y);
        bottom = Math.max(bottom, selection.y + selection.height);
    }
    if (!Number.isFinite(left)) return rect(0, 0, 0, 0);
    // Include the existing arrowheads and stroke, then clip to the camera.
    const margin = 10;
    left = Math.max(
        0,
        Math.min(
            viewportSize.width,
            Math.floor((left - margin - ui.x) * ui.zoom)
        )
    );
    top = Math.max(
        0,
        Math.min(
            viewportSize.height,
            Math.floor((top - margin - ui.y) * ui.zoom)
        )
    );
    right = Math.max(
        0,
        Math.min(
            viewportSize.width,
            Math.ceil((right + margin - ui.x) * ui.zoom)
        )
    );
    bottom = Math.max(
        0,
        Math.min(
            viewportSize.height,
            Math.ceil((bottom + margin - ui.y) * ui.zoom)
        )
    );
    return rect(
        left,
        top,
        Math.max(0, right - left),
        Math.max(0, bottom - top)
    );
}

// Both Canvas2D hosts call the same paint routine; no domain state is mutated.
export function paint(context, definition, ui, viewportSize, color, selection) {
    context.clearRect(0, 0, viewportSize.width, viewportSize.height);
    context.save();
    context.scale(ui.zoom, ui.zoom);
    context.translate(-ui.x, -ui.y);
    for (const edge of curves(ui, definition)) {
        const cy1 = edge.cy1 === undefined ? edge.y1 : edge.cy1,
            cy2 = edge.cy2 === undefined ? edge.y2 : edge.cy2,
            hasBadge =
                Array.isArray(edge.badgeLines) &&
                edge.badgeLines.some(Boolean),
            arrowT = hasBadge && !edge.selfLoop ? 0.78 : 0.6;
        context.strokeStyle = color(
            definition.selectedEdge === edge.index ? 'primaryText' : edge.color
        );
        context.lineWidth = definition.selectedEdge === edge.index ? 3.5 : 2.5;
        context.beginPath();
        context.moveTo(edge.x1, edge.y1);
        context.bezierCurveTo(
            edge.x1 + edge.bend,
            cy1,
            edge.x2 - edge.bend,
            cy2,
            edge.x2,
            edge.y2
        );
        context.stroke();
        const p = curvePoint(edge, arrowT),
            before = curvePoint(edge, arrowT - 0.01),
            after = curvePoint(edge, arrowT + 0.01),
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

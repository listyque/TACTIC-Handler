import { node, rect, label, button, muted } from '../../core/frame.mjs';

export function listAction(
    id,
    bounds,
    text,
    icon,
    action,
    enabled = true,
    options = {}
) {
    const iconOnly = !!options.iconOnly;
    const left = icon ? 34 : 12;
    const children = icon
        ? [
              node(
                  'Icon',
                  id + 'Icon',
                  rect(
                      iconOnly ? (bounds.width - 16) / 2 : 10,
                      (bounds.height - 16) / 2,
                      16,
                      16
                  ),
                  {
                      icon,
                      color: enabled ? 'secondaryText' : 'disabledText'
                  }
              )
          ]
        : [];
    if (!iconOnly)
        children.push(
            label(
                id + 'Label',
                rect(
                    left,
                    0,
                    Math.max(
                        0,
                        bounds.width - left - 12 - (options.endInset || 0)
                    ),
                    bounds.height
                ),
                text,
                {
                    fontRole: options.fontRole || 'body',
                    weight: options.weight || 400,
                    color:
                        options.color ||
                        (enabled ? 'primaryText' : 'disabledText')
                }
            )
        );
    return node(
        'Action',
        id,
        bounds,
        Object.assign(
            {
                text,
                action,
                enabled,
                radius: 6,
                normalColor: 'transparent',
                selectedColor: 'contentSelection',
                children
            },
            options
        )
    );
}

// Neutral navigation row. The feature owns expansion, routing and availability.
export function navigationRow(width, record, state = {}) {
    const section = record.kind === 'section',
        separator = record.kind === 'separator';
    const height = separator ? 16 : section ? 48 : 56;
    if (separator)
        return {
            width,
            height,
            nodes: [
                node(
                    'Box',
                    'navigationSeparator',
                    rect(20, 7, Math.max(0, width - 40), 1),
                    { background: 'separator' }
                )
            ]
        };
    const selected = !!state.selected,
        x = 28 + Math.max(0, record.depth || 0) * 16;
    const count = record.badge > 99 ? '99+' : String(record.badge || '');
    const badgeWidth =
        record.badge > 0 ? Math.max(24, count.length * 7 + 12) : 0;
    const radius = state.radius === undefined ? 12 : state.radius;
    const nodes = [
        node(
            'Box',
            'sidebarRowSurface',
            rect(12, 4, Math.max(0, width - 24), height - 8),
            {
                background: selected ? 'contentSelection' : 'transparent',
                radius
            }
        ),
        node(
            'Box',
            'navigationRowOverlay',
            rect(12, 4, Math.max(0, width - 24), height - 8),
            {
                background: selected ? 'action' : 'primaryText',
                opacity: state.pressed
                    ? 0.12
                    : state.hovered || state.focused
                      ? 0.08
                      : 0,
                radius
            }
        ),
        section
            ? node(
                  'Icon',
                  'navigationRowIcon',
                  rect(x + 7.5, (height - 17) / 2, 17, 17),
                  {
                      icon: record.expanded ? 'chevron-down' : 'chevron-right',
                      color: 'secondaryText'
                  }
              )
            : node(
                  'Preview',
                  'navigationRowIcon',
                  rect(x, (height - 32) / 2, 32, 32),
                  {
                      icon: record.icon || 'link',
                      accent: record.accent || 'action',
                      outlined: false
                  }
              ),
        label(
            'sidebarRowTitle',
            rect(
                x + 44,
                (height - 24) / 2,
                Math.max(
                    0,
                    width - x - 72 - (badgeWidth ? badgeWidth + 12 : 0)
                ),
                24
            ),
            record.title,
            {
                fontRole: section ? 'secondary' : 'bodyLarge',
                weight: section ? 600 : selected ? 500 : 400,
                color: selected ? 'contentSelectionText' : 'primaryText'
            }
        )
    ];
    if (badgeWidth)
        nodes.push(
            node(
                'Box',
                'navigationRowBadge',
                rect(
                    Math.max(0, width - 28 - badgeWidth),
                    (height - 24) / 2,
                    badgeWidth,
                    24
                ),
                {
                    background: selected ? 'action' : 'rowHover',
                    radius: 12,
                    children: [
                        label(
                            'navigationRowCount',
                            rect(0, 0, badgeWidth, 24),
                            count,
                            {
                                weight: 600,
                                align: 'center',
                                color: selected
                                    ? 'selectedText'
                                    : 'secondaryText'
                            }
                        )
                    ]
                }
            )
        );
    return { width, height, nodes };
}

// Input is an owned, flat preorder snapshot. Expansion never mutates a record.
export function visibleRows(rows) {
    const visible = [];
    let collapsedDepth = -1;
    for (const row of rows) {
        if (collapsedDepth >= 0 && row.depth > collapsedDepth) continue;
        collapsedDepth = -1;
        visible.push(row);
        if (row.hasChildren && !row.expanded) collapsedDepth = row.depth;
    }
    return visible;
}

export function navigate(rows, id, key) {
    if (!rows.length) return null;
    const index = rows.findIndex((row) => row.id === id);
    if (index < 0) return { type: 'select', id: rows[0].id };
    const current = rows[Math.max(0, index)];
    if (key === 'ArrowRight' && current.hasChildren && !current.expanded)
        return { type: 'expand', id: current.id };
    if (key === 'ArrowLeft' && current.hasChildren && current.expanded)
        return { type: 'collapse', id: current.id };
    let target = index;
    if (key === 'Home') target = 0;
    else if (key === 'End') target = rows.length - 1;
    else if (key === 'ArrowDown') target = Math.min(rows.length - 1, index + 1);
    else if (key === 'ArrowUp') target = Math.max(0, index - 1);
    else if (key === 'ArrowRight' && rows[index + 1]?.depth > current.depth)
        target = index + 1;
    else if (key === 'ArrowLeft') {
        for (let before = index - 1; before >= 0; before--)
            if (rows[before].depth < current.depth) {
                target = before;
                break;
            }
    }
    return target >= 0 && target !== index
        ? { type: 'select', id: rows[target].id }
        : null;
}

export function row(id, width, record, options = {}) {
    const ids = options.ids || {};
    const x = 12 + Math.min(Math.max(0, record.depth || 0), 5) * 16;
    const nodes = [
        node('Action', id, rect(0, 0, width, 60), {
            text: record.title,
            role: 'treeitem',
            level: (record.depth || 0) + 1,
            expanded: record.hasChildren ? !!record.expanded : undefined,
            selected: !!options.selected,
            enabled: options.enabled !== false,
            opacity: options.dim ? 0.5 : 1,
            selectedColor: 'contentSelection',
            normalColor: 'transparent',
            rail: false,
            action: options.select,
            keys: options.keys,
            children: [
                node('Preview', ids.icon || id + '_icon', rect(x, 14, 32, 32), {
                    icon: record.icon || 'link',
                    accent: record.accent || '',
                    outlined: false
                }),
                label(
                    ids.title || id + '_title',
                    rect(
                        x + 32,
                        record.subtitle ? 8 : 18,
                        Math.max(1, width - x - 88),
                        24
                    ),
                    record.title,
                    { weight: 600 }
                ),
                ...(record.subtitle
                    ? [
                          label(
                              ids.detail || id + '_detail',
                              rect(x + 32, 32, Math.max(1, width - x - 88), 20),
                              record.subtitle,
                              muted
                          )
                      ]
                    : [])
            ]
        })
    ];
    if (record.hasChildren)
        nodes.push(
            button(
                ids.toggle || id + '_toggle',
                rect(width - 42, 11, 38, 38),
                options.toggleLabel || '',
                record.expanded ? 'chevron-down' : 'chevron-right',
                options.toggle,
                options.toggleEnabled === undefined
                    ? options.enabled !== false
                    : options.toggleEnabled,
                { iconOnly: true }
            )
        );
    return { nodes };
}

import { node, rect, label, button, muted } from '../../core/frame.mjs';

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

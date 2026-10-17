import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export const rowHeight = 30;

export function row(record, index, width, language) {
    const text = (key) => translate(key, language),
        x = 5 + (record.depth || 0) * 18,
        kindIcon = record.kind === 'child' || record.kind === 'process',
        title =
            record.title +
            (record.kind === 'child'
                ? text(' (child)')
                : record.kind === 'builtin'
                  ? text(' (builtin)')
                  : ''),
        titleX = x + (kindIcon ? 77 : 58),
        nodes = [];
    nodes.push(
        node(
            'Action',
            'processVisibilitySelect',
            rect(0, 0, width, rowHeight),
            {
                text: title,
                role: 'treeitem',
                level: (record.depth || 0) + 1,
                expanded: record.hasChildren ? !!record.expanded : undefined,
                radius: 0,
                selected: !!record.selected,
                normalColor:
                    index % 2 ? 'surfaceContainerHigh' : 'surfaceContainerLow',
                selectedColor: 'contentSelection',
                action: { type: 'select', index }
            }
        )
    );
    if (record.hasChildren)
        nodes.push(
            button(
                'processVisibilityExpand',
                rect(x, 5, 20, 20),
                text(record.expanded ? 'Collapse' : 'Expand'),
                record.expanded
                    ? 'keyboard_arrow_down'
                    : 'keyboard_arrow_right',
                { type: 'expand', index },
                true,
                { iconOnly: true, iconSize: 13 }
            )
        );
    if (record.checkable)
        nodes.push(
            node(
                'CheckBox',
                'processVisibilityCheck',
                rect(x + 23, 3, 28, 24),
                {
                    text: '',
                    label: title,
                    checked: !!record.checked,
                    compact: true,
                    action: { type: 'check', index }
                }
            )
        );
    if (kindIcon)
        nodes.push(
            node(
                'Icon',
                'processVisibilityKind',
                rect(
                    x + (record.kind === 'process' ? 56 : 54),
                    record.kind === 'process' ? 9 : 7,
                    record.kind === 'process' ? 12 : 16,
                    record.kind === 'process' ? 12 : 16
                ),
                {
                    icon:
                        record.kind === 'child'
                            ? 'view-sequential'
                            : 'process-marker',
                    color: record.accent || 'secondaryText'
                }
            )
        );
    nodes.push(
        label(
            'processSelectionTitle_' + record.kind,
            rect(titleX, 0, width - titleX - 6, rowHeight),
            title,
            { pointerTransparent: true }
        )
    );
    return { nodes };
}

export function togglers(model, width, language) {
    const text = (key) => translate(key, language),
        columns = width < 720 ? 1 : 2,
        nodes = [];
    let top = 0;
    if (model.expanded) {
        const items = [
            ['all', 'Toggle All', 'checkbox-multiple-marked-outline'],
            ['process', 'Toggle Process', 'checkbox-blank-circle'],
            ['builtin', 'Toggle Builtin Processes', 'checkbox-blank-circle'],
            ['child', 'Toggle Children', 'view-sequential']
        ];
        const cell = (width - (columns - 1) * 4) / columns;
        for (let index = 0; index < items.length; index++) {
            const item = items[index];
            nodes.push(
                button(
                    'processToggle_' + item[0],
                    rect(
                        (index % columns) * (cell + 4),
                        Math.floor(index / columns) * 40,
                        cell,
                        36
                    ),
                    text(item[1]),
                    item[2],
                    { type: 'toggleKind', value: item[0] },
                    true
                )
            );
        }
        top = Math.ceil(items.length / columns) * 40;
        if (model.versionChooser) {
            nodes.push(
                node(
                    'View',
                    'processSelectionSyncMode',
                    rect(0, top, width, 36),
                    { view: 'fullSync' }
                )
            );
            top += 40;
        }
    }
    nodes.push(
        button(
            'processVisibilityTogglers',
            rect(0, top, width, 36),
            text(model.expanded ? 'Hide Togglers' : 'Show Togglers'),
            model.expanded ? 'expand-more' : 'expand-less',
            { type: 'togglers' },
            true
        )
    );
    return { nodes, contentHeight: top + 36 };
}

export function header(model, width, language) {
    return {
        nodes: [
            node(
                'Box',
                'processVisibilityHeaderSurface',
                rect(0, 0, width, 42),
                {
                    background: 'surfaceContainerLow',
                    border: 'outlineVariant',
                    radius: 8
                }
            ),
            node('Icon', 'processVisibilityIcon', rect(10, 12, 18, 18), {
                icon: 'filter-alt',
                color: 'action'
            }),
            label(
                'processVisibilityContext',
                rect(38, 0, width - 48, 42),
                translate('Pipeline for:', language) +
                    ' ' +
                    (model.title || ''),
                { weight: 600 }
            )
        ],
        contentHeight: 42
    };
}

export function footer(model, width, language) {
    const text = (key) => translate(key, language),
        compact = width < (language === 'ru' ? 460 : 404),
        nodes = [];
    const actions = [
        ['cancel', 'Cancel', '', 102],
        ['save', 'Save', 'save', 100],
        ['saveClose', 'Save and close', 'check', language === 'ru' ? 210 : 164]
    ];
    nodes.push(
        node(
            'Box',
            'processVisibilityFooterSurface',
            rect(0, 0, width, compact ? 138 : 48),
            {
                background: 'surfaceContainerLow',
                border: 'outlineVariant',
                radius: 8
            }
        )
    );
    let right = width - 8,
        top = 6;
    for (const [type, title, icon, size] of actions.slice().reverse()) {
        if (!compact) right -= size;
        nodes.push(
            button(
                'processVisibility_' + type,
                rect(compact ? 8 : right, top, compact ? width - 16 : size, 36),
                text(title),
                icon,
                { type },
                type === 'cancel' || model.valid !== false,
                { highlighted: type === 'saveClose' }
            )
        );
        if (compact) top += 42;
        else right -= 6;
    }
    if (!compact && right > 100)
        nodes.push(
            label(
                'processVisibilityDirty',
                rect(8, 6, right - 8, 36),
                model.dirty ? text('Visibility has unsaved changes') : '',
                { fontRole: 'caption', color: 'secondaryText' }
            )
        );
    return { nodes, contentHeight: compact ? top : 48 };
}

export function empty(text, width, height, language) {
    return {
        nodes: [
            node(
                'Icon',
                'processVisibilityEmptyIcon',
                rect((width - 26) / 2, (height - 56) / 2, 26, 26),
                { icon: 'account-tree', color: 'disabledText' }
            ),
            label(
                'processVisibilityEmpty',
                rect(8, (height - 56) / 2 + 32, width - 16, 24),
                translate(text, language),
                { align: 'center', color: 'secondaryText' }
            )
        ]
    };
}

function processList(ignore, pipeline) {
    const values = (ignore.processes || {})[pipeline];
    return Array.isArray(values) ? values : [];
}

export function applyIgnore(records, ignore) {
    return records.map((record) =>
        Object.assign({}, record, {
            checked:
                record.kind === 'child'
                    ? !(ignore.children || []).includes(record.key)
                    : record.kind === 'builtin'
                      ? !(ignore.builtins || []).includes(record.key)
                      : record.kind === 'process'
                        ? !processList(ignore, record.group).includes(
                              record.key
                          )
                        : true
        })
    );
}

export function ignoreFrom(records) {
    const result = {
        children: [],
        builtins: [],
        processes: Object.create(null),
        show_builtins: false
    };
    for (const record of records) {
        if (record.kind === 'process' && !result.processes[record.group])
            result.processes[record.group] = [];
        if (!record.checkable || record.checked) continue;
        if (record.kind === 'child' && !result.children.includes(record.key))
            result.children.push(record.key);
        else if (
            record.kind === 'builtin' &&
            !result.builtins.includes(record.key)
        )
            result.builtins.push(record.key);
        else if (
            record.kind === 'process' &&
            !result.processes[record.group].includes(record.key)
        )
            result.processes[record.group].push(record.key);
    }
    return result.children.length ||
        result.builtins.length ||
        Object.keys(result.processes).some(
            (key) => result.processes[key].length
        )
        ? result
        : {};
}

export function updateVisibility(records) {
    const byId = {};
    for (const row of records) byId[row.nodeId] = row;
    for (const row of records) {
        let parent = row.parentId;
        row.rowVisible = true;
        const seen = {};
        while (parent && byId[parent] && !seen[parent]) {
            seen[parent] = true;
            if (!byId[parent].expanded) {
                row.rowVisible = false;
                break;
            }
            parent = byId[parent].parentId;
        }
    }
}

export function change(records, action) {
    const source = records[action.index];
    if (action.type === 'toggleKind') {
        const rows = records.filter(
                (row) =>
                    row.checkable &&
                    (action.value === 'all' || row.kind === action.value)
            ),
            checked = rows.some((row) => !row.checked);
        for (const row of rows) row.checked = checked;
    } else if (source && action.type === 'select') {
        const selected = !source.selected;
        for (const row of records)
            row.selected =
                row === source
                    ? selected
                    : action.control
                      ? row.selected
                      : false;
    } else if (source && action.type === 'check' && source.checkable) {
        const selection = records.filter(
                (row) => row.selected && row.checkable
            ),
            rows =
                source.selected && selection.length > 1 ? selection : [source];
        for (const row of records)
            if (
                rows.some(
                    (target) =>
                        row.kind === target.kind &&
                        row.key === target.key &&
                        row.group === target.group
                )
            )
                row.checked = action.value;
    } else if (source && action.type === 'expand' && source.hasChildren) {
        source.expanded = !source.expanded;
        if (action.shift) {
            const descendants = { [source.nodeId]: true };
            for (const row of records)
                if (descendants[row.parentId]) {
                    descendants[row.nodeId] = true;
                    if (row.hasChildren) row.expanded = source.expanded;
                }
        }
        updateVisibility(records);
    }
}

export function branchVisible(branch, record, ignore) {
    if (branch.kind === 'relation')
        return !(ignore.children || []).includes(branch.search_type);
    if (branch.kind !== 'process') return true;
    return (
        !(ignore.builtins || []).includes(branch.process) &&
        !processList(ignore, record.pipeline_code).includes(branch.process)
    );
}

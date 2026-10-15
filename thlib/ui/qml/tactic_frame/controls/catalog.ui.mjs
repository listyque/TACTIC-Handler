// Executable control examples. No requests or product-specific state.
import { node, rect, button, label } from '../core/frame.mjs';
import { translate } from '../core/strings.mjs';
import * as Tree from './lists/tree.ui.mjs';

export function initial() {
    return {
        text: 'Robot Arm',
        description: 'Sample asset',
        checked: true,
        mixed: true,
        choice: 'model',
        user: 'admin',
        date: '2024-02-29T13:14',
        color: '#78a6c4',
        icon: 'save',
        treeSelected: 'assets',
        split: 50,
        tree: [
            {
                id: 'assets',
                title: 'Assets',
                depth: 0,
                icon: 'folder',
                hasChildren: true,
                expanded: true
            },
            { id: 'arm', title: 'Robot Arm', depth: 1, icon: 'box' },
            { id: 'body', title: 'Robot Body', depth: 1, icon: 'box' },
            {
                id: 'textures',
                title: 'Textures',
                depth: 0,
                icon: 'folder',
                hasChildren: true,
                expanded: false
            },
            { id: 'metal', title: 'Metal', depth: 1, icon: 'image' }
        ],
        events: []
    };
}

export function transition(model, action) {
    const next = Object.assign({}, model, {
        events: model.events.concat([action])
    });
    if (
        Object.prototype.hasOwnProperty.call(model, action.type) &&
        action.value !== undefined
    )
        next[action.type] = action.value;
    if (action.type === 'checked') next.mixed = false;
    if (action.type === 'treeSelect') next.treeSelected = action.id;
    if (action.type === 'treeToggle')
        next.tree = model.tree.map((record) =>
            record.id === action.id
                ? Object.assign({}, record, { expanded: !record.expanded })
                : record
        );
    if (action.type === 'treeKey') {
        const command = Tree.navigate(
            Tree.visibleRows(model.tree),
            action.id,
            action.key
        );
        if (command?.type === 'select') next.treeSelected = command.id;
        else if (command)
            next.tree = model.tree.map((record) =>
                record.id === command.id
                    ? Object.assign({}, record, {
                          expanded: command.type === 'expand'
                      })
                    : record
            );
    }
    return next;
}

export const users = [
    {
        value: 'admin',
        login: 'admin',
        label: 'Administrator',
        displayName: 'Administrator',
        initials: 'A',
        groups: ['Artists'],
        primaryGroup: 'Artists'
    },
    {
        value: 'test',
        login: 'test',
        label: 'Test Artist',
        displayName: 'Test Artist',
        initials: 'TA',
        groups: ['Artists'],
        primaryGroup: 'Artists'
    }
];

export const choices = [
    { value: 'model', label: 'Model' },
    { value: 'rig', label: 'Rig' },
    { value: 'publish', label: 'Publish' }
];

export function describe(
    model,
    width,
    height,
    language = 'en',
    state = 'idle'
) {
    const tr = (text) => translate(text, language);
    const enabled = state !== 'disabled' && state !== 'loading';
    const readOnly = state === 'readonly';
    const error = state === 'error';
    const contentWidth = width - 16;
    const columns = contentWidth >= 700 ? 2 : 1;
    const cardWidth = (contentWidth - 24 - (columns - 1) * 20) / columns;
    const rowHeight = 116;
    const nodes = [];
    function card(index, title, content) {
        const x = 12 + (index % columns) * (cardWidth + 20),
            y = 12 + Math.floor(index / columns) * rowHeight;
        nodes.push(
            label('caption_' + index, rect(x, y, cardWidth, 22), tr(title), {
                fontRole: 'secondary'
            })
        );
        nodes.push(...content(x, y + 28, cardWidth));
    }
    card(0, 'Save', (x, y, w) => [
        button(
            'button',
            rect(x, y, Math.min(w, 220), 36),
            state === 'long'
                ? tr('Save') + ' / ' + tr('Description').repeat(8)
                : tr('Save'),
            'save',
            { type: 'save' },
            enabled
        )
    ]);
    card(1, 'Create', (x, y, w) => [
        button(
            'primary',
            rect(x, y, Math.min(w, 220), 36),
            tr('Create'),
            'plus',
            { type: 'create' },
            enabled,
            { highlighted: true }
        )
    ]);
    card(2, 'Delete', (x, y, w) => [
        button(
            'danger',
            rect(x, y, Math.min(w, 220), 36),
            tr('Delete'),
            'delete',
            { type: 'delete' },
            enabled,
            { highlighted: true, destructive: true }
        )
    ]);
    card(3, 'Display', (x, y, w) => [
        button(
            'segment',
            rect(x, y, w / 2 - 4, 36),
            tr('List'),
            'list',
            { type: 'list' },
            enabled,
            { radio: true, selected: true }
        ),
        button(
            'iconButton',
            rect(x + w - 36, y, 36, 36),
            tr('Help'),
            'help',
            { type: 'help' },
            enabled,
            { iconOnly: true, tooltip: tr('Help') }
        )
    ]);
    card(4, 'Name', (x, y, w) => [
        node('Field', 'field', rect(x, y, w, 36), {
            text: model.text,
            label: tr('Name'),
            enabled,
            readOnly,
            error,
            action: { type: 'text' }
        })
    ]);
    card(5, 'Description', (x, y, w) => [
        node('Area', 'area', rect(x, y, w, 68), {
            text: model.description,
            label: tr('Description'),
            enabled,
            readOnly,
            error,
            action: { type: 'description' }
        })
    ]);
    card(6, 'Process', (x, y, w) => [
        node('Choice', 'choice', rect(x, y, w, 36), {
            value: model.choice,
            options: choices,
            label: tr('Process'),
            enabled,
            action: { type: 'choice' }
        })
    ]);
    card(7, 'Enabled', (x, y, w) => [
        node('CheckBox', 'check', rect(x, y, w, 36), {
            text: tr('Enabled'),
            checked: model.checked,
            mixed: model.mixed,
            enabled,
            action: { type: 'checked' },
            children: [
                label('checkLabel', rect(30, 0, w - 30, 36), tr('Enabled'))
            ]
        })
    ]);
    card(8, 'Notifications', (x, y, w) => [
        node('Switch', 'switch', rect(x, y, w, 36), {
            text: tr('Notifications'),
            checked: model.checked,
            enabled,
            action: { type: 'checked' }
        })
    ]);
    card(9, 'Start date', (x, y, w) => [
        node('DateChoice', 'date', rect(x, y, w, 36), {
            text: model.date,
            label: tr('Start date'),
            language,
            includeTime: true,
            readOnly,
            enabled,
            action: { type: 'date' },
            commitAction: { type: 'dateCommit' }
        })
    ]);
    card(10, 'Assigned to', (x, y, w) => [
        node('UserChoice', 'user', rect(x, y, w, 36), {
            value: model.user,
            options: users,
            label: tr('Assigned to'),
            enabled,
            action: { type: 'user' }
        })
    ]);
    card(11, 'Color', (x, y, w) => [
        node('ColorChoice', 'color', rect(x, y, w, 36), {
            value: model.color,
            text: tr('Color'),
            enabled,
            action: { type: 'color' }
        })
    ]);
    card(12, 'Icon', (x, y, w) => [
        node('IconChoice', 'icon', rect(x, y, w, 36), {
            value: model.icon,
            enabled,
            action: { type: 'icon' }
        })
    ]);
    card(13, 'Actions', (x, y, w) => [
        node('View', 'menu', rect(x, y, w, 36), { view: 'menu' })
    ]);
    card(14, 'Loading', (x, y, w) => [
        node('View', 'busy', rect(x, y, w, 36), { view: 'busy' })
    ]);
    card(15, 'Size', (x, y, w) => [
        node('View', 'slider', rect(x, y, w, 36), { view: 'slider' })
    ]);
    const treeY = 12 + Math.ceil(16 / columns) * rowHeight;
    nodes.push(
        node(
            'List',
            'tree',
            rect(12, treeY, Math.max(1, contentWidth - 24), 168),
            {
                source: 'treeRows',
                role: 'tree',
                label: tr('Assets'),
                keyField: 'id',
                fields: [],
                rowHeight: 64
            }
        )
    );
    nodes.push(
        node(
            'Splitter',
            'splitter',
            rect(12, treeY + 180, contentWidth - 24, 10),
            {
                horizontal: true,
                text: tr('Size'),
                value: model.split,
                min: 0,
                max: 100,
                action: { type: 'split' },
                enabled
            }
        )
    );
    const gridY = treeY + 204;
    nodes.push(
        node('Grid', 'grid', rect(12, gridY, contentWidth - 24, 200), {
            source: 'cells',
            text: tr('Table'),
            rowHeaders: Array.from({ length: 50 }, (_, index) => ({
                label: String(index + 1)
            })),
            columnHeaders: choices.map((option) => option.label),
            cellWidth: 150,
            rowHeight: 38,
            labelWidth: 44,
            headerHeight: 32
        })
    );
    return {
        nodes: [
            node('Scroll', 'catalogScroll', rect(0, 0, width, height), {
                contentHeight: gridY + 216,
                children: nodes
            })
        ]
    };
}

export function menuActions(language) {
    return ['Save', 'Reload', 'Delete'].map((title, index) => ({
        title: translate(title, language),
        command: 'menu_' + index,
        icon: ['save', 'refresh', 'delete'][index]
    }));
}

export function treeRows(model) {
    return Tree.visibleRows(model.tree);
}
export function row(list, record, model, language, state) {
    const keys = {};
    for (const key of [
        'ArrowUp',
        'ArrowDown',
        'ArrowLeft',
        'ArrowRight',
        'Home',
        'End'
    ])
        keys[key] = { type: 'treeKey', id: record.id, key };
    return Tree.row('tree_' + record.id, list.width - 16, record, {
        selected: record.id === model.treeSelected,
        enabled: !['disabled', 'loading'].includes(state),
        select: { type: 'treeSelect', id: record.id },
        toggle: { type: 'treeToggle', id: record.id },
        toggleLabel: translate(
            record.expanded ? 'Collapse section' : 'Expand section',
            language
        ),
        keys
    });
}

export function cell(grid, record, row, column) {
    return {
        nodes: [
            label(
                'cell_' + row + '_' + column,
                rect(8, 0, grid.cellWidth - 16, grid.rowHeight),
                String(row + 1) + ' / ' + String(column + 1)
            )
        ]
    };
}

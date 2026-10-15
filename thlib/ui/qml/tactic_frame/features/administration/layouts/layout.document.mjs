// Engines parse XML with their standard parser; all layout edits run here.
export const widgets = [
    'group',
    'view',
    'text',
    'title',
    'description',
    'image',
    'link',
    'button',
    'metadata',
    'snapshot-details',
    'snapshot-size',
    'snapshot-summary',
    'branch-summary',
    'file-offline',
    'item-menu',
    'knowledge',
    'quick-actions',
    'relations'
];
export const roles = {
    '': 'None',
    preview: 'Preview',
    copy: 'Object information',
    'title-line': 'Heading',
    'title-actions': 'Snapshot actions',
    description: 'Description',
    metadata: 'Metadata',
    actions: 'Actions',
    'hover-actions': 'Actions on hover',
    communication: 'Tasks and notes',
    'task-button': 'Tasks',
    'note-button': 'Notes',
    'mobile-actions': 'Mobile actions',
    'file-offline': 'File Offline'
};
export const actions = [
    'inspect',
    'operate',
    'preview',
    'tasks',
    'notes',
    'upload',
    'create',
    'link',
    'relations'
];
export const variants = [
    'all',
    'main',
    'children',
    'process',
    'relation',
    'versions',
    'snapshot',
    'file'
];
const children = (node) =>
    (node.children || []).filter((child) => child.type === 1);
const get = (node, key) => {
    const pair = (node.attributes || []).find((pair) => pair[0] === key);
    return pair ? pair[1] : '';
};
function set(node, key, value) {
    const index = (node.attributes || []).findIndex((pair) => pair[0] === key);
    if (value === '') {
        if (index >= 0) node.attributes.splice(index, 1);
    } else if (index >= 0) node.attributes[index][1] = String(value);
    else (node.attributes || (node.attributes = [])).push([key, String(value)]);
}
const element = (name, attributes, content) => ({
    type: 1,
    name,
    attributes: attributes || [],
    children: content || []
});
function root(tree) {
    const node = tree.type === 9 ? children(tree)[0] : tree;
    if (!node || node.name !== 'config')
        throw Error('Invalid configuration XML');
    return node;
}
function viewOf(tree, view) {
    return children(root(tree)).find(
        (node) =>
            node.name === view ||
            (node.name === 'view' && get(node, 'name') === view)
    );
}
function content(node) {
    return [3, 4].indexOf(node.type) >= 0
        ? node.text || ''
        : (node.children || []).map(content).join('');
}
export function describe(tree, view) {
    const node = viewOf(tree, view);
    if (!node || get(node, 'layout') !== 'sobject-layout')
        throw Error('Select a SObject layout configuration');
    const elements = children(node)
        .filter((child) => child.name === 'element')
        .map((item) => {
            const display = children(item).find(
                    (child) => child.name === 'display'
                ),
                options = {};
            for (const option of display ? children(display) : [])
                options[option.name] = content(option);
            const result = {
                name: get(item, 'name'),
                title: get(item, 'title') || get(item, 'name'),
                kind: display
                    ? get(display, 'class') || get(display, 'widget')
                    : '',
                options,
                parent: get(item, 'parent'),
                variant: get(item, 'variant') || 'all',
                role: get(item, 'role'),
                tag: get(item, 'tag') || 'div',
                flow: get(item, 'flow') || 'grid',
                when: get(item, 'when').split(' ').filter(Boolean),
                layer: Number(get(item, 'layer') || 0),
                hidden:
                    ['true', '1', 'yes', 'on'].indexOf(get(item, 'hidden')) >=
                    0,
                align: get(item, 'align') || 'stretch',
                tone: get(item, 'tone') || 'normal'
            };
            for (const key of [
                'row',
                'column',
                'span',
                'rows',
                'columns',
                'height'
            ])
                result[key] = Number(
                    get(item, key) ||
                        {
                            span: 12,
                            columns: 12,
                            height: 40
                        }[key] ||
                        1
                );
            return result;
        });
    return {
        collection: get(node, 'collection') || 'grid',
        flow: get(node, 'flow') || 'grid',
        columns: Number(get(node, 'columns') || 12),
        tracks: get(node, 'tracks'),
        card_width: Number(get(node, 'card_width') || 280),
        elements
    };
}
export function serialize(node) {
    const escape = (value, attr) =>
        String(value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, attr ? '&quot;' : '"')
            .replace(/\r/g, attr ? '&#13;' : '\r')
            .replace(/\n/g, attr ? '&#10;' : '\n')
            .replace(/\t/g, attr ? '&#9;' : '\t');
    if (node.type === 9) return (node.children || []).map(serialize).join('');
    if (node.type === 3) return escape(node.text || '', false);
    if (node.type === 4) return '<![CDATA[' + (node.text || '') + ']]>';
    if (node.type === 8) return '<!--' + (node.text || '') + '-->';
    if (node.type === 7)
        return '<?' + node.name + (node.text ? ' ' + node.text : '') + '?>';
    if (node.type !== 1) throw Error('Unsupported XML node');
    const attributes = (node.attributes || [])
            .map((pair) => ' ' + pair[0] + '="' + escape(pair[1], true) + '"')
            .join(''),
        body = (node.children || []).map(serialize).join('');
    return (
        '<' +
        node.name +
        attributes +
        (node.children && node.children.length
            ? '>' + body + '</' + node.name + '>'
            : '/>')
    );
}
export function template(tree, view) {
    if (!/^[A-Za-z_][\w.@-]{0,127}$/.test(view))
        throw Error('Invalid view name');
    const next = JSON.parse(JSON.stringify(tree)),
        config = root(next),
        original = children(config)[0];
    if (!original) throw Error('Invalid layout template');
    original.name = view.indexOf('@') >= 0 ? 'view' : view;
    if (view.indexOf('@') >= 0) set(original, 'name', view);
    return next;
}
export function edit(tree, view, name, field, value) {
    const next = JSON.parse(JSON.stringify(tree)),
        root = viewOf(next, view);
    if (!root) throw Error('Configuration does not contain its view');
    let item = name
        ? children(root).find(
              (node) => node.name === 'element' && get(node, 'name') === name
          )
        : root;
    if (field === 'add') {
        if (widgets.indexOf(value) < 0)
            throw Error('Unsupported layout widget');
        const names = children(root).map((node) => get(node, 'name'));
        let index = 1;
        while (names.indexOf('item_' + index) >= 0) index++;
        const last = children(root).reduce(
            (max, node) =>
                Math.max(
                    max,
                    Number(get(node, 'row') || 1) +
                        Number(get(node, 'rows') || 1) -
                        1
                ),
            0
        );
        item = element(
            'element',
            [
                ['name', 'item_' + index],
                ['title', value],
                ['row', String(last + 1)],
                ['span', get(root, 'columns') || '12']
            ],
            [element('display', [['class', value]])]
        );
        root.children.push(item);
    } else if (!item) throw Error('Layout element no longer exists');
    else if (field === 'order') {
        const siblings = children(root).filter(
                (node) =>
                    node.name === 'element' &&
                    get(node, 'parent') === get(item, 'parent')
            ),
            offset = Number(value),
            target = siblings[siblings.indexOf(item) + offset];
        if (target && [-1, 1].indexOf(offset) >= 0) {
            root.children.splice(root.children.indexOf(item), 1);
            root.children.splice(
                root.children.indexOf(target) + (offset > 0 ? 1 : 0),
                0,
                item
            );
        }
    } else if (field === 'remove') {
        const names = [name];
        for (let depth = 0; depth < 8; depth++)
            for (const child of children(root))
                if (
                    names.indexOf(get(child, 'parent')) >= 0 &&
                    names.indexOf(get(child, 'name')) < 0
                )
                    names.push(get(child, 'name'));
        root.children = root.children.filter(
            (child) => child.type !== 1 || names.indexOf(get(child, 'name')) < 0
        );
    } else if (field.indexOf('option:') === 0 || field === 'kind') {
        let display = children(item).find((node) => node.name === 'display');
        if (!display) {
            display = element('display');
            item.children.push(display);
        }
        if (field === 'kind') {
            set(display, 'widget', '');
            set(display, 'class', value);
        } else {
            const key = field.slice(7);
            if (!/^[A-Za-z_][\w.-]*$/.test(key))
                throw Error('Invalid widget option');
            let option = children(display).find((node) => node.name === key);
            if (!value) {
                if (option)
                    display.children.splice(
                        display.children.indexOf(option),
                        1
                    );
            } else {
                if (!option) {
                    option = element(key);
                    display.children.push(option);
                }
                option.children = [
                    {
                        type: 3,
                        text: String(value)
                    }
                ];
            }
        }
    } else {
        if (!/^[A-Za-z_][\w.-]*$/.test(field))
            throw Error('Invalid layout attribute');
        set(item, field, value);
    }
    return next;
}
export function binding(binding, node) {
    if (
        !/^(record|node)\.[A-Za-z_]\w*(\.[A-Za-z_]\w*){0,4}$/.test(
            binding || ''
        )
    )
        return '';
    const parts = binding.split('.'),
        scope = parts.shift();
    let value = scope === 'record' ? node.record : node;
    for (const part of parts) {
        if (
            ['__proto__', 'prototype', 'constructor'].indexOf(part) >= 0 ||
            value == null ||
            !Object.prototype.hasOwnProperty.call(value, part)
        )
            return '';
        value = value[part];
    }
    return value === undefined || value === null ? '' : value;
}

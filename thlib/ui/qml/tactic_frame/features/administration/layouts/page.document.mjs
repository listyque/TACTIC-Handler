export const kinds = [
    'row',
    'column',
    'text',
    'markdown',
    'metric',
    'table',
    'items',
    'details',
    'link'
];
export const copy = (value) => JSON.parse(JSON.stringify(value));
export function path(value) {
    if (value === '') return [];
    if (!/^\d+(\.\d+)*$/.test(value)) throw Error('Select a page block');
    return value.split('.').map(Number);
}
export function siblings(document, indices) {
    let rows = document.blocks;
    for (const index of indices.slice(0, -1)) {
        if (!rows[index]) throw Error('The selected element no longer exists');
        rows = rows[index].children || [];
    }
    return rows;
}
export function block(document, key) {
    const p = path(key);
    if (!p.length) return null;
    const item = siblings(document, p)[p[p.length - 1]];
    if (!item) throw Error('The selected element no longer exists');
    return item;
}
export function layers(document, prefix = []) {
    const rows = prefix.length
        ? block(document, prefix.join('.')).children || []
        : document.blocks || [];
    let result = [];
    rows.forEach((item, index) => {
        const p = prefix.concat(index);
        result = result.concat(
            [
                {
                    key: p.join('.'),
                    depth: prefix.length,
                    label: item.title || item.kind,
                    kind: item.kind
                }
            ].concat(layers(document, p))
        );
    });
    return result;
}
export function change(document, key, field, value) {
    const result = copy(document),
        item = key === '' ? result : block(result, key);
    if (!item) throw Error('The selected element no longer exists');
    const limits = {
        width: [40, 2400],
        height: [24, 1600],
        weight: [1, 12],
        gap: [0, 128]
    };
    if (limits[field]) {
        if (value === '' && ['width', 'height'].includes(field)) value = null;
        else {
            const range = limits[field];
            if (
                !/^\d+$/.test(String(value)) ||
                Number(value) < range[0] ||
                Number(value) > range[1]
            )
                throw Error('Enter a whole number within the allowed range');
            value = Number(value);
        }
    } else if (
        !['title', 'text', 'search_type', 'view', 'href', 'field'].includes(
            field
        )
    )
        throw Error('Unsupported page property');
    item[field] = value;
    return result;
}
export function spacing(document, key, field, side, value) {
    if (
        !['padding', 'margin'].includes(field) ||
        !Number.isInteger(side) ||
        side < 0 ||
        side > 3 ||
        !/^\d+$/.test(String(value)) ||
        Number(value) > 256
    )
        throw Error('Enter spacing from 0 to 256');
    const result = copy(document),
        item = block(result, key);
    if (!item) throw Error('Select a page block');
    item[field] = (item[field] || [0, 0, 0, 0]).slice();
    item[field][side] = Number(value);
    return result;
}
export function add(document, key, kind, searchType) {
    if (!kinds.includes(kind)) throw Error('Unsupported page widget');
    const result = copy(document),
        selected = key ? block(result, key) : null;
    const parent =
        selected && ['row', 'column', 'details'].includes(selected.kind)
            ? path(key)
            : key
              ? path(key).slice(0, -1)
              : [];
    const owner = parent.length ? block(result, parent.join('.')) : null;
    const rows = owner
        ? owner.children || (owner.children = [])
        : result.blocks;
    if (rows.length >= 32 || layers(result).length >= 128)
        throw Error('Dashboard exceeds 128 bricks');
    if (parent.length > 6) throw Error('Dashboard nesting exceeds six levels');
    const item = { kind, title: kind };
    if (['row', 'column', 'details'].includes(kind)) {
        item.children = [];
        item.height = 180;
    }
    if (['items', 'table', 'metric'].includes(kind))
        Object.assign(item, {
            search_type: searchType || '',
            view: kind === 'items' ? 'continuous_example' : 'table'
        });
    if (['text', 'markdown'].includes(kind)) item.text = kind;
    rows.push(item);
    return { document: result, key: parent.concat(rows.length - 1).join('.') };
}
export function remove(document, key) {
    const result = copy(document),
        p = path(key);
    if (!p.length) throw Error('Select a page block');
    siblings(result, p).splice(p[p.length - 1], 1);
    return result;
}
export function geometry(document, change, boxes) {
    const result = copy(document),
        p = path(change.key),
        item = block(result, change.key);
    if (!item) throw Error('The selected element no longer exists');
    if (change.handle !== 'move') {
        const margin = item.margin || [0, 0, 0, 0],
            padding = item.padding || [0, 0, 0, 0];
        if (change.handle.includes('e'))
            item.width = Math.max(
                40,
                Math.min(
                    2400,
                    Math.round(change.after.width + margin[1] + margin[3])
                )
            );
        if (change.handle.includes('s')) {
            const overhead = ['items', 'table'].includes(item.kind) ? 32 : 0;
            const old =
                item.height === undefined || item.height === null
                    ? change.before.height - overhead - padding[0] - padding[2]
                    : item.height;
            item.height = Math.max(
                24,
                Math.min(
                    1600,
                    Math.round(old + change.after.height - change.before.height)
                )
            );
        }
        return { document: result, key: change.key };
    }
    if (change.keyboard) {
        const rows = siblings(result, p),
            index = p[p.length - 1];
        const delta =
            change.after.y - change.before.y ||
            change.after.x - change.before.x;
        const target = Math.max(0, Math.min(rows.length - 1, index + delta));
        rows.splice(index, 1);
        rows.splice(target, 0, item);
        return {
            document: result,
            key: p.slice(0, -1).concat(target).join('.')
        };
    }
    const x = change.after.x + change.after.width / 2,
        y = change.after.y + change.after.height / 2;
    const hit = boxes
        .filter(
            (b) =>
                b.key !== change.key &&
                !b.key.startsWith(change.key + '.') &&
                x >= b.x &&
                x <= b.x + b.width &&
                y >= b.y &&
                y <= b.y + b.height
        )
        .sort((a, b) => b.depth - a.depth)[0];
    let parent = hit ? path(hit.key) : [];
    if (
        hit &&
        !['row', 'column', 'details'].includes(block(result, hit.key)?.kind)
    )
        parent = parent.slice(0, -1);
    if (parent.length > 5) throw Error('Dashboard nesting exceeds six levels');
    const old = siblings(result, p),
        index = p[p.length - 1];
    const owner = parent.length ? block(result, parent.join('.')) : null;
    const target = owner
        ? owner.children || (owner.children = [])
        : result.blocks;
    const depth = (rows) =>
        rows.reduce(
            (value, row) => Math.max(value, 1 + depth(row.children || [])),
            0
        );
    if (parent.length + depth([item]) > 7)
        throw Error('Dashboard nesting exceeds six levels');
    if (target !== old && target.length >= 32)
        throw Error('Dashboard supports at most 32 siblings');
    const parentKind = parent.length
        ? block(result, parent.join('.')).kind
        : 'column';
    const axis = parentKind === 'row' ? 'x' : 'y',
        position = axis === 'x' ? x : y;
    const candidates = boxes
        .filter(
            (b) =>
                path(b.key).length === parent.length + 1 &&
                path(b.key).slice(0, -1).join('.') === parent.join('.') &&
                b.key !== change.key
        )
        .sort((a, b) => a[axis] - b[axis]);
    const before = candidates.find(
        (b) => position < b[axis] + b[axis === 'x' ? 'width' : 'height'] / 2
    );
    const targetPath = before ? path(before.key) : [];
    let insertion = before ? targetPath[targetPath.length - 1] : target.length;
    if (old === target && index < insertion) insertion--;
    old.splice(index, 1);
    target.splice(insertion, 0, item);
    function location(rows, prefix) {
        if (rows === target) return prefix;
        for (let i = 0; i < rows.length; i++) {
            const found = location(rows[i].children || [], prefix.concat(i));
            if (found) return found;
        }
        return null;
    }
    return {
        document: result,
        key: location(result.blocks, []).concat(insertion).join('.')
    };
}

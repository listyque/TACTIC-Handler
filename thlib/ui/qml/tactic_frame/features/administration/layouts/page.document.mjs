export const kinds = [
    'row',
    'column',
    'text',
    'markdown',
    'metric',
    'table',
    'items',
    'details',
    'link',
    'chart',
    'summary',
    'grid',
    'heading',
    'icon',
    'image',
    'button',
    'divider',
    'spacer',
    'field',
    'form',
    'action'
];
// QVariantMap exposes Python None as undefined; keep explicit null fields in drafts.
export const copy = (value) =>
    JSON.parse(
        JSON.stringify(value, (_key, item) =>
            item === undefined ? null : item
        )
    );
export function fingerprint(value) {
    // QVariantMap sorts keys and exposes None as undefined on the native host.
    return JSON.stringify(copy(value), (_key, item) => {
        if (item === undefined) return null;
        if (item && typeof item === 'object' && !Array.isArray(item)) {
            const result = {};
            Object.keys(item)
                .sort()
                .forEach((key) => {
                    result[key] = item[key];
                });
            return result;
        }
        return item;
    });
}
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
        gap: [0, 128],
        offset_x: [-2400, 2400],
        offset_y: [-1600, 1600],
        columns: [1, 12],
        min_cell_width: [80, 1200],
        row_height: [40, 800],
        column_span: [1, 12],
        row_span: [1, 12],
        collapse_width: [0, 2400],
        icon_size: [16, 128]
    };
    if (field === 'fields') {
        if (
            !Array.isArray(value) ||
            value.length > 16 ||
            new Set(value).size !== value.length ||
            value.some(
                (name) =>
                    typeof name !== 'string' ||
                    !/^[A-Za-z_][\w.-]{0,127}$/.test(name)
            )
        )
            throw Error('Choose distinct fields from the native edit view');
    } else if (field === 'edit_view') {
        if (
            typeof value !== 'string' ||
            !/^[A-Za-z_][\w.@-]{0,127}$/.test(value)
        )
            throw Error('Invalid view name');
    } else if (limits[field]) {
        if (value === '' && ['width', 'height'].includes(field)) value = null;
        else {
            const range = limits[field];
            if (
                !/^-?\d+$/.test(String(value)) ||
                Number(value) < range[0] ||
                Number(value) > range[1]
            )
                throw Error('Enter a whole number within the allowed range');
            value = Number(value);
        }
    } else if (
        [
            'text_role',
            'text_align',
            'button_style',
            'image_fit',
            'text_weight',
            'format',
            'native_action',
            'region'
        ].includes(field)
    ) {
        const choices = {
            region: ['header', 'content', 'footer'],
            text_role: [
                'auto',
                'caption',
                'body',
                'bodyLarge',
                'title',
                'heading',
                'display',
                'statistic',
                'hero'
            ],
            text_align: ['left', 'center', 'right'],
            button_style: ['normal', 'primary', 'tonal'],
            image_fit: ['cover', 'contain'],
            format: [
                'plain',
                'badge',
                'progress',
                'date',
                'datetime',
                'number'
            ],
            native_action: ['details', 'edit', 'notes', 'copy_link', 'refresh'],
            text_weight: [400, 600, 700]
        };
        if (field === 'region' && path(key).length !== 1 && value !== 'content')
            throw Error('Page regions are only available for top-level blocks');
        if (field === 'text_weight') value = Number(value);
        if (!choices[field].includes(value))
            throw Error('Choose a supported component property');
    } else if (field === 'text_color') {
        if (
            !/^(auto|primaryText|secondaryText|contentAccent|error|#[0-9a-fA-F]{6})$/.test(
                value
            )
        )
            throw Error('Choose a theme color or enter a six-digit hex color');
    } else if (field === 'icon') {
        if (
            typeof value !== 'string' ||
            value.length > 128 ||
            !/^[A-Za-z0-9_./:-]*$/.test(value)
        )
            throw Error('Choose a supported icon');
    } else if (
        ![
            'title',
            'text',
            'search_type',
            'view',
            'href',
            'field',
            'suffix'
        ].includes(field)
    )
        throw Error('Unsupported page property');
    if (['width', 'height'].includes(field))
        item.sizing = Object.assign({}, item.sizing || {}, {
            [field + '_mode']: value === null ? 'auto' : 'fixed'
        });
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
        selected && ['row', 'column', 'grid', 'details'].includes(selected.kind)
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
    if (['row', 'column', 'grid', 'details'].includes(kind)) {
        item.children = [];
        item.height = 180;
    }
    if (['items', 'table', 'metric', 'chart', 'summary'].includes(kind))
        Object.assign(item, {
            search_type: searchType || '',
            view: kind === 'items' ? 'continuous_example' : 'table'
        });
    if (['chart', 'summary'].includes(kind))
        item.aggregates = [
            { name: 'count', title: 'Count', function: 'count', column: '' }
        ];
    if (['text', 'heading', 'markdown'].includes(kind)) item.text = kind;
    if (kind === 'heading') item.text_weight = 600;
    if (kind === 'grid')
        Object.assign(item, {
            height: null,
            children: [],
            columns: 3,
            min_cell_width: 200,
            row_height: 120
        });
    if (kind === 'icon')
        Object.assign(item, { icon: 'folder', width: 40, height: 40 });
    if (kind === 'button')
        Object.assign(item, { title: 'Open project', href: '' });
    if (['field', 'form', 'action'].includes(kind))
        Object.assign(item, {
            binding: 'project',
            fields: [],
            field: kind === 'field' ? 'code' : ''
        });
    if (kind === 'image')
        Object.assign(item, { binding: 'project', height: 160 });
    if (['divider', 'spacer'].includes(kind)) item.height = 24;
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
function checkStructure(document) {
    const rows = layers(document);
    if (rows.length > 128 || document.blocks.length > 32)
        throw Error('Dashboard exceeds 128 bricks');
    if (rows.some((row) => path(row.key).length > 7))
        throw Error('Dashboard nesting exceeds six levels');
    if (
        rows.some(
            (row) => (block(document, row.key).children || []).length > 32
        )
    )
        throw Error('A container supports up to 32 widgets');
    if (rows.filter((row) => row.kind === 'items').length > 1)
        throw Error('A dashboard supports one items workspace');
    if (rows.filter((row) => row.kind === 'details').length > 1)
        throw Error('A dashboard supports one details pane');
}
export function duplicate(document, key) {
    const result = copy(document),
        p = path(key);
    const item = block(result, key);
    if (!item) throw Error('Select a page block');
    siblings(result, p).splice(p[p.length - 1] + 1, 0, copy(item));
    checkStructure(result);
    return {
        document: result,
        key: p
            .slice(0, -1)
            .concat(p[p.length - 1] + 1)
            .join('.')
    };
}
export function reorder(document, key, delta) {
    if (!Number.isInteger(delta)) throw Error('Select a page block');
    const result = copy(document),
        p = path(key),
        item = block(result, key);
    if (!item) throw Error('Select a page block');
    const rows = siblings(result, p),
        index = p[p.length - 1];
    const target = Math.max(0, Math.min(rows.length - 1, index + delta));
    rows.splice(index, 1);
    rows.splice(target, 0, item);
    return { document: result, key: p.slice(0, -1).concat(target).join('.') };
}
function location(rows, target, prefix = []) {
    if (rows === target) return prefix;
    for (let i = 0; i < rows.length; i++) {
        const found = location(
            rows[i].children || [],
            target,
            prefix.concat(i)
        );
        if (found) return found;
    }
    return null;
}
export function reparent(document, key, parent) {
    if (parent === key || parent.startsWith(key + '.'))
        throw Error('A widget cannot contain itself');
    const result = copy(document),
        p = path(key),
        item = block(result, key);
    if (!item) throw Error('Select a page block');
    const container = parent ? block(result, parent) : null;
    if (
        container &&
        !['row', 'column', 'grid', 'details'].includes(container.kind)
    )
        throw Error('Choose a row, column or details container');
    if (p.slice(0, -1).join('.') === parent) return { document: result, key };
    const target = container
        ? container.children || (container.children = [])
        : result.blocks;
    siblings(result, p).splice(p[p.length - 1], 1);
    if (container && item.region && item.region !== 'content')
        item.region = 'content';
    target.push(item);
    checkStructure(result);
    return {
        document: result,
        key: location(result.blocks, target)
            .concat(target.length - 1)
            .join('.')
    };
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
        item.sizing = Object.assign({}, item.sizing || {});
        if (change.handle.includes('e')) item.sizing.width_mode = 'fixed';
        if (change.handle.includes('s')) item.sizing.height_mode = 'fixed';
        return { document: result, key: change.key };
    }
    if (change.keyboard) {
        const delta =
            change.after.y - change.before.y ||
            change.after.x - change.before.x;
        return reorder(document, change.key, delta);
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
        !['row', 'column', 'grid', 'details'].includes(
            block(result, hit.key)?.kind
        )
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
    if (parent.length && item.region && item.region !== 'content')
        item.region = 'content';
    target.splice(insertion, 0, item);
    return {
        document: result,
        key: location(result.blocks, target).concat(insertion).join('.')
    };
}

export function appearances(document, keys, field, value) {
    const defaults = {
        fill: 'transparent',
        stroke: 'outlineVariant',
        stroke_width: 0,
        radius: 0,
        shadow: false,
        animate: false
    };
    const result = copy(document);
    if (!Object.prototype.hasOwnProperty.call(defaults, field))
        throw Error('Unsupported page property');
    if (['shadow', 'animate'].includes(field)) {
        if (typeof value !== 'boolean') throw Error('Choose Yes or No');
    } else if (['radius', 'stroke_width'].includes(field)) {
        if (
            !/^\d+$/.test(String(value)) ||
            Number(value) > (field === 'radius' ? 48 : 8)
        )
            throw Error('Enter a whole number within the allowed range');
        value = Number(value);
    } else if (
        !(
            field === 'fill'
                ? /^(transparent|panel|workspace|surfaceContainerLow|surfaceContainerLowest|#[0-9a-fA-F]{6})$/
                : /^(outlineVariant|contentAccent|transparent|#[0-9a-fA-F]{6})$/
        ).test(value)
    )
        throw Error('Choose a theme color or enter a six-digit hex color');
    for (const key of keys) {
        const item = block(result, key);
        item.appearance = Object.assign({}, defaults, item.appearance || {}, {
            [field]: value
        });
    }
    return result;
}
export function geometries(document, changes, boxes) {
    let result = copy(document);
    const keys = changes.map((change) => change.key);
    if (
        new Set(keys).size !== keys.length ||
        keys.some((key) => keys.some((other) => key.startsWith(other + '.')))
    )
        throw Error('Select independent page blocks');
    for (const change of changes) {
        if (change.position && change.handle === 'move') {
            const item = block(result, change.key);
            for (const axis of ['x', 'y']) {
                const delta = change.after[axis] - change.before[axis];
                const value = Math.round((item['offset_' + axis] || 0) + delta);
                if (
                    !Number.isFinite(value) ||
                    Math.abs(value) > (axis === 'x' ? 2400 : 1600)
                )
                    throw Error('Movement exceeds the page offset range');
                item['offset_' + axis] = value;
            }
        } else result = geometry(result, change, boxes).document;
    }
    return { document: result, keys };
}

export function sizing(document, key, field, value) {
    const result = copy(document),
        item = block(result, key);
    const size = Object.assign(
        {
            width_mode: 'auto',
            height_mode: 'auto',
            min_width: 0,
            min_height: 0,
            max_width: null,
            max_height: null
        },
        item.sizing || {}
    );
    if (['width_mode', 'height_mode'].includes(field)) {
        if (!['auto', 'fixed', 'fill', 'content'].includes(value))
            throw Error('Choose a supported size behavior');
        const axis = field === 'width_mode' ? 'width' : 'height';
        if (value === 'fixed' && item[axis] == null)
            item[axis] = axis === 'width' ? 240 : 120;
        if (['fill', 'content'].includes(value)) item[axis] = null;
    } else {
        if (
            !['min_width', 'max_width', 'min_height', 'max_height'].includes(
                field
            )
        )
            throw Error('Unsupported page property');
        if (value === '' && field.startsWith('max_')) value = null;
        else {
            if (
                !/^\d+$/.test(String(value)) ||
                Number(value) > (field.endsWith('width') ? 2400 : 1600) ||
                (field.startsWith('max_') &&
                    Number(value) < (field.endsWith('width') ? 40 : 24))
            )
                throw Error('Enter a whole number within the allowed range');
            value = Number(value);
        }
    }
    size[field] = value;
    for (const axis of ['width', 'height'])
        if (
            size['max_' + axis] !== null &&
            size['max_' + axis] < size['min_' + axis]
        )
            throw Error('Maximum size must not be smaller than minimum size');
    item.sizing = size;
    return result;
}

const SCALAR_DEFAULTS = [
    ['region', 'content', 'str'],
    ['title', '', 'str'],
    ['text', '', 'str'],
    ['source_key', '', 'str'],
    ['field', '', 'str'],
    ['binding', 'auto', 'str'],
    ['search_type', '', 'str'],
    ['view', 'table', 'str'],
    ['measure', '', 'str'],
    ['chart_type', 'bar', 'str'],
    ['group_limit', 50, 'int'],
    ['group_order', 'group', 'str'],
    ['href', '', 'str'],
    ['weight', 1, 'int'],
    ['width', null, 'int'],
    ['height', null, 'int'],
    ['gap', 8, 'int'],
    ['offset_x', 0, 'int'],
    ['offset_y', 0, 'int'],
    ['columns', 3, 'int'],
    ['min_cell_width', 200, 'int'],
    ['row_height', 120, 'int'],
    ['column_span', 1, 'int'],
    ['row_span', 1, 'int'],
    ['collapse_width', 600, 'int'],
    ['text_role', 'auto', 'str'],
    ['text_align', 'left', 'str'],
    ['text_color', 'auto', 'str'],
    ['text_weight', 400, 'int'],
    ['icon', '', 'str'],
    ['icon_size', 32, 'int'],
    ['image_fit', 'contain', 'str'],
    ['button_style', 'normal', 'str'],
    ['edit_view', 'edit', 'str'],
    ['format', 'plain', 'str'],
    ['suffix', '', 'str'],
    ['native_action', 'details', 'str']
];
const APPEARANCE_DEFAULTS = [
    ['fill', 'transparent', 'str'],
    ['stroke', 'outlineVariant', 'str'],
    ['stroke_width', 0, 'int'],
    ['radius', 0, 'int'],
    ['shadow', false, 'bool'],
    ['animate', false, 'bool']
];
const SIZING_DEFAULTS = [
    ['width_mode', 'auto', 'str'],
    ['height_mode', 'auto', 'str'],
    ['min_width', 0, 'int'],
    ['max_width', null, 'int'],
    ['min_height', 0, 'int'],
    ['max_height', null, 'int']
];

const escAttr = (v) =>
    String(v)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
const escText = (v) =>
    String(v)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
const unesc = (v) =>
    String(v).replace(
        /&(quot|apos|lt|gt|amp|#\d+|#x[0-9a-fA-F]+);/g,
        (m, code) => {
            if (code === 'quot') return '"';
            if (code === 'apos') return "'";
            if (code === 'lt') return '<';
            if (code === 'gt') return '>';
            if (code === 'amp') return '&';
            if (code[0] === '#')
                return String.fromCodePoint(
                    code[1] === 'x'
                        ? parseInt(code.slice(2), 16)
                        : parseInt(code.slice(1), 10)
                );
            return m;
        }
    );

function filterAttrs(item) {
    const pairs = [['column', item.column]];
    if ((item.relation || '=') !== '=') pairs.push(['relation', item.relation]);
    const val = item.value;
    if (val !== undefined && val !== null) {
        if (typeof val === 'boolean') {
            pairs.push(
                ['value', val ? 'true' : 'false'],
                ['value_type', 'bool']
            );
        } else if (typeof val === 'number') {
            pairs.push(
                ['value', String(val)],
                ['value_type', Number.isInteger(val) ? 'int' : 'float']
            );
        } else {
            pairs.push(['value', String(val)]);
        }
    }
    return pairs;
}

export function toXml(document) {
    if (!document || !document.name) return '';
    const lines = [
        '<config>',
        `  <view name="dashboard.${escAttr(document.name)}" title="${escAttr(document.title || document.name)}">`
    ];
    const pFilters = document.filters || [];
    const blocks = document.blocks || [];
    if (!pFilters.length && !blocks.length) {
        lines.push('    <dashboard></dashboard>', '  </view>', '</config>');
        return lines.join('\n');
    }
    lines.push('    <dashboard>');
    for (const pf of pFilters) {
        const pairs = [
            ['name', pf.name],
            ['title', pf.title],
            ['search_type', pf.search_type],
            ...filterAttrs(pf)
        ];
        if (pf.enabled) pairs.push(['enabled', 'true']);
        const attrs = pairs.map(([k, v]) => ` ${k}="${escAttr(v)}"`).join('');
        lines.push(`      <filter${attrs} />`);
    }
    function emitBlock(blk, depth) {
        const pad = '  '.repeat(depth);
        const pairs = [];
        let multiline = false;
        for (const [key, def] of SCALAR_DEFAULTS) {
            const val = blk[key] !== undefined ? blk[key] : def;
            if (val !== def && val !== null) {
                if (key === 'text' && String(val).includes('\n')) {
                    multiline = true;
                    continue;
                }
                pairs.push([key, String(val)]);
            }
        }
        for (const key of ['padding', 'margin']) {
            const val = blk[key];
            if (
                Array.isArray(val) &&
                (val[0] !== 0 || val[1] !== 0 || val[2] !== 0 || val[3] !== 0)
            )
                pairs.push([key, val.join(',')]);
        }
        if (Array.isArray(blk.fields) && blk.fields.length)
            pairs.push(['fields', blk.fields.join(',')]);
        if (blk.controls !== undefined && blk.controls !== null)
            pairs.push(['controls', blk.controls.join(',')]);
        const app = blk.appearance || {};
        for (const [key, def, typ] of APPEARANCE_DEFAULTS) {
            const val = app[key] !== undefined ? app[key] : def;
            if (val !== def)
                pairs.push([
                    key,
                    typ === 'bool' ? (val ? 'true' : 'false') : String(val)
                ]);
        }
        const sz = blk.sizing || {};
        for (const [key, def] of SIZING_DEFAULTS) {
            const val = sz[key] !== undefined ? sz[key] : def;
            if (val !== def && val !== null) pairs.push([key, String(val)]);
        }
        const attrs = pairs.map(([k, v]) => ` ${k}="${escAttr(v)}"`).join('');
        const childLines = [];
        const cPad = '  '.repeat(depth + 1);
        if (multiline)
            childLines.push(`${cPad}<content>${escText(blk.text)}</content>`);
        for (const flt of blk.filters || []) {
            const fAttrs = filterAttrs(flt)
                .map(([k, v]) => ` ${k}="${escAttr(v)}"`)
                .join('');
            childLines.push(`${cPad}<filter${fAttrs} />`);
        }
        if (blk.page_filters !== undefined && blk.page_filters !== null) {
            const keys = Object.keys(blk.page_filters);
            if (!keys.length)
                childLines.push(`${cPad}<page_filters none="true" />`);
            else
                for (const k of keys)
                    childLines.push(
                        `${cPad}<page_filter name="${escAttr(k)}" column="${escAttr(blk.page_filters[k])}" />`
                    );
        }
        for (const grp of blk.group_by || []) {
            const gPairs = [['column', grp.column]];
            if (grp.title) gPairs.push(['title', grp.title]);
            if (grp.period && grp.period !== 'value')
                gPairs.push(['period', grp.period]);
            const gAttrs = gPairs
                .map(([k, v]) => ` ${k}="${escAttr(v)}"`)
                .join('');
            childLines.push(`${cPad}<group_by${gAttrs} />`);
        }
        for (const agg of blk.aggregates || []) {
            const aPairs = [
                ['name', agg.name],
                ['title', agg.title]
            ];
            if (agg.function && agg.function !== 'count')
                aPairs.push(['function', agg.function]);
            if (agg.column) aPairs.push(['column', agg.column]);
            const aAttrs = aPairs
                .map(([k, v]) => ` ${k}="${escAttr(v)}"`)
                .join('');
            childLines.push(`${cPad}<aggregate${aAttrs} />`);
        }
        const nested = blk.children || [];
        if (!childLines.length && !nested.length) {
            lines.push(`${pad}<${blk.kind}${attrs} />`);
        } else {
            lines.push(`${pad}<${blk.kind}${attrs}>`);
            for (const line of childLines) lines.push(line);
            for (const ch of nested) emitBlock(ch, depth + 1);
            lines.push(`${pad}</${blk.kind}>`);
        }
    }
    for (const blk of blocks) emitBlock(blk, 3);
    lines.push('    </dashboard>', '  </view>', '</config>');
    return lines.join('\n');
}

function parseXmlTree(xml) {
    const s = String(xml)
        .replace(/<\?xml[\s\S]*?\?>/g, '')
        .replace(/<!--[\s\S]*?-->/g, '')
        .trim();
    if (!s.startsWith('<')) throw Error('Invalid dashboard XML');
    const stack = [{ tag: '#root', children: [] }];
    const tagRe =
        /<\/?([A-Za-z_][\w.-]*)((?:\s+[A-Za-z_][\w.-]*\s*=\s*(?:"[^"]*"|'[^']*'))*)\s*(\/?)>|([^<]+)/g;
    const attrRe = /([A-Za-z_][\w.-]*)\s*=\s*(?:"([^"]*)"|'([^']*)')/g;
    let match,
        lastIndex = 0;
    while ((match = tagRe.exec(s)) !== null) {
        if (match.index !== lastIndex) throw Error('Invalid dashboard XML');
        lastIndex = tagRe.lastIndex;
        if (match[4] !== undefined) {
            const top = stack[stack.length - 1];
            top.text = (top.text || '') + unesc(match[4]);
            continue;
        }
        const full = match[0],
            tag = match[1],
            attrStr = match[2] || '',
            selfClosing = match[3] === '/';
        if (full.startsWith('</')) {
            if (selfClosing || attrStr.trim() || stack.length < 2)
                throw Error('Invalid dashboard XML');
            const popped = stack.pop();
            if (popped.tag !== tag)
                throw Error(`Mismatched closing tag </${tag}>`);
            continue;
        }
        const attrib = {};
        let aMatch;
        const consumed = attrStr.replace(attrRe, (_, k, v1, v2) => {
            if (Object.prototype.hasOwnProperty.call(attrib, k))
                throw Error(`Duplicate attribute "${k}"`);
            attrib[k] = unesc(v1 !== undefined ? v1 : v2);
            return '';
        });
        if (consumed.trim()) throw Error(`Invalid attributes on <${tag}>`);
        const node = { tag, attrib, text: '', children: [] };
        stack[stack.length - 1].children.push(node);
        if (!selfClosing) stack.push(node);
    }
    if (
        lastIndex !== s.length ||
        stack.length !== 1 ||
        stack[0].children.length !== 1
    )
        throw Error('Invalid dashboard XML');
    return stack[0].children[0];
}

function readFilterValue(attrib) {
    if (!Object.prototype.hasOwnProperty.call(attrib, 'value')) return null;
    const raw = attrib.value,
        vtype = attrib.value_type || 'str';
    if (vtype === 'bool') {
        if (raw !== 'true' && raw !== 'false')
            throw Error('Filter boolean value must be true or false');
        return raw === 'true';
    }
    if (vtype === 'int') {
        if (!/^-?\d+$/.test(raw))
            throw Error('Filter integer value is invalid');
        return Number(raw);
    }
    if (vtype === 'float') {
        const n = Number(raw);
        if (!Number.isFinite(n)) throw Error('Filter number value is invalid');
        return n;
    }
    if (vtype === 'null') return null;
    return raw;
}

function parseTyped(raw, typ, name) {
    if (typ === 'bool') {
        if (raw !== 'true' && raw !== 'false')
            throw Error(`Attribute ${name} must be true or false`);
        return raw === 'true';
    }
    if (typ === 'int') {
        if (!/^-?\d+$/.test(String(raw)))
            throw Error(`Attribute ${name} must be a whole number`);
        return Number(raw);
    }
    return String(raw);
}

export function fromXml(source, fallbackName = '') {
    const trimmed = String(source || '').trim();
    if (!trimmed) throw Error('Invalid dashboard XML');
    if (trimmed.startsWith('{')) {
        const parsed = JSON.parse(trimmed);
        checkStructure(parsed);
        return parsed;
    }
    const root = parseXmlTree(trimmed);
    let viewName = '',
        viewTitle = '',
        dash = null;
    if (root.tag === 'dashboard') {
        dash = root;
    } else if (root.children.some((c) => c.tag === 'dashboard')) {
        viewName = root.attrib.name || (root.tag !== 'view' ? root.tag : '');
        viewTitle = root.attrib.title || '';
        dash = root.children.find((c) => c.tag === 'dashboard');
    } else {
        const vNode =
            root.children.find((c) => c.tag === 'view') ||
            root.children.find((c) =>
                c.children.some((gc) => gc.tag === 'dashboard')
            );
        if (vNode) {
            viewName =
                vNode.attrib.name || (vNode.tag !== 'view' ? vNode.tag : '');
            viewTitle = vNode.attrib.title || '';
            dash = vNode.children.find((c) => c.tag === 'dashboard');
        }
    }
    if (!dash) throw Error('Choose an existing dashboard');
    if (!dash.children.length && (dash.text || '').trim().startsWith('{')) {
        const parsed = JSON.parse(dash.text.trim());
        checkStructure(parsed);
        return parsed;
    }
    if ((dash.text || '').trim())
        throw Error('Unexpected text inside <dashboard>');
    const name =
        dash.attrib.name ||
        (viewName.startsWith('dashboard.') ? viewName.slice(10) : viewName) ||
        fallbackName;
    if (!/^[a-z][a-z0-9_]{0,47}$/.test(name))
        throw Error('Invalid dashboard name');
    const title = (dash.attrib.title || viewTitle || name).trim();
    if (!title || title.length > 256) throw Error('Enter a page title');

    const scalarMap = {};
    for (const [k, d, t] of SCALAR_DEFAULTS) scalarMap[k] = [d, t];
    const appMap = {};
    for (const [k, d, t] of APPEARANCE_DEFAULTS) appMap[k] = [d, t];
    const szMap = {};
    for (const [k, d, t] of SIZING_DEFAULTS) szMap[k] = [d, t];

    function parseBlockNode(node) {
        if (!kinds.includes(node.tag))
            throw Error(`Unsupported page widget <${node.tag}>`);
        if ((node.text || '').trim())
            throw Error(`Use text attribute or <content> inside <${node.tag}>`);
        const app = {};
        for (const [k, d] of APPEARANCE_DEFAULTS) app[k] = d;
        const sz = {};
        for (const [k, d] of SIZING_DEFAULTS) sz[k] = d;
        const raw = { kind: node.tag };
        for (const [attr, val] of Object.entries(node.attrib)) {
            if (scalarMap[attr]) {
                raw[attr] = parseTyped(val, scalarMap[attr][1], attr);
            } else if (attr === 'padding' || attr === 'margin') {
                const parts = val.split(',').map((p) => p.trim());
                if (parts.length !== 4)
                    throw Error(
                        `Attribute ${attr} requires four comma-separated numbers`
                    );
                raw[attr] = parts.map((p) => parseTyped(p, 'int', attr));
            } else if (attr === 'fields') {
                raw.fields = val
                    .split(',')
                    .map((p) => p.trim())
                    .filter(Boolean);
            } else if (attr === 'controls') {
                raw.controls = val
                    .split(',')
                    .map((p) => p.trim())
                    .filter(Boolean);
            } else if (appMap[attr]) {
                app[attr] = parseTyped(val, appMap[attr][1], attr);
            } else if (szMap[attr]) {
                sz[attr] = parseTyped(val, szMap[attr][1], attr);
            } else {
                throw Error(`Unsupported attribute "${attr}" on <${node.tag}>`);
            }
        }
        const bFilters = [],
            bGroupBy = [],
            bAggregates = [],
            bChildren = [];
        let bPageFilters = null;
        for (const ch of node.children) {
            if (ch.tag === 'content') {
                raw.text = ch.text || '';
            } else if (ch.tag === 'filter') {
                if (!ch.attrib.column)
                    throw Error('Invalid <filter> attributes');
                bFilters.push({
                    column: ch.attrib.column,
                    relation: ch.attrib.relation || '=',
                    value: readFilterValue(ch.attrib)
                });
            } else if (ch.tag === 'page_filters') {
                if (ch.attrib.none === 'true' && bPageFilters === null)
                    bPageFilters = {};
            } else if (ch.tag === 'page_filter') {
                if (!ch.attrib.name || !ch.attrib.column)
                    throw Error('Invalid <page_filter> attributes');
                if (bPageFilters === null) bPageFilters = {};
                bPageFilters[ch.attrib.name] = ch.attrib.column;
            } else if (ch.tag === 'group_by') {
                if (!ch.attrib.column)
                    throw Error('Invalid <group_by> attributes');
                bGroupBy.push({
                    column: ch.attrib.column,
                    title: ch.attrib.title || '',
                    period: ch.attrib.period || 'value'
                });
            } else if (ch.tag === 'aggregate') {
                if (!ch.attrib.name || !ch.attrib.title)
                    throw Error('Invalid <aggregate> attributes');
                bAggregates.push({
                    name: ch.attrib.name,
                    title: ch.attrib.title,
                    function: ch.attrib.function || 'count',
                    column: ch.attrib.column || ''
                });
            } else if (ch.tag === 'appearance') {
                for (const [k, v] of Object.entries(ch.attrib)) {
                    if (!appMap[k])
                        throw Error(`Unsupported appearance attribute "${k}"`);
                    app[k] = parseTyped(v, appMap[k][1], k);
                }
            } else if (ch.tag === 'sizing') {
                for (const [k, v] of Object.entries(ch.attrib)) {
                    if (!szMap[k])
                        throw Error(`Unsupported sizing attribute "${k}"`);
                    sz[k] = parseTyped(v, szMap[k][1], k);
                }
            } else if (kinds.includes(ch.tag)) {
                bChildren.push(parseBlockNode(ch));
            } else {
                throw Error(
                    `Unsupported element <${ch.tag}> inside <${node.tag}>`
                );
            }
        }
        return {
            region: raw.region ?? 'content',
            kind: node.tag,
            title: raw.title ?? '',
            text: raw.text ?? '',
            source_key: raw.source_key ?? '',
            field: raw.field ?? '',
            binding: raw.binding ?? 'auto',
            search_type: raw.search_type ?? '',
            view: raw.view ?? 'table',
            filters: bFilters,
            page_filters: bPageFilters,
            group_by: bGroupBy,
            aggregates: bAggregates,
            measure: raw.measure ?? '',
            chart_type: raw.chart_type ?? 'bar',
            group_limit: raw.group_limit ?? 50,
            group_order: raw.group_order ?? 'group',
            href: raw.href ?? '',
            weight: raw.weight ?? 1,
            width: raw.width ?? null,
            height: raw.height ?? null,
            padding: raw.padding ?? [0, 0, 0, 0],
            margin: raw.margin ?? [0, 0, 0, 0],
            gap: raw.gap ?? 8,
            offset_x: raw.offset_x ?? 0,
            offset_y: raw.offset_y ?? 0,
            appearance: app,
            sizing: sz,
            columns: raw.columns ?? 3,
            min_cell_width: raw.min_cell_width ?? 200,
            row_height: raw.row_height ?? 120,
            column_span: raw.column_span ?? 1,
            row_span: raw.row_span ?? 1,
            collapse_width: raw.collapse_width ?? 600,
            text_role: raw.text_role ?? 'auto',
            text_align: raw.text_align ?? 'left',
            text_color: raw.text_color ?? 'auto',
            text_weight: raw.text_weight ?? 400,
            icon: raw.icon ?? '',
            icon_size: raw.icon_size ?? 32,
            image_fit: raw.image_fit ?? 'contain',
            button_style: raw.button_style ?? 'normal',
            fields: raw.fields ?? [],
            edit_view: raw.edit_view ?? 'edit',
            format: raw.format ?? 'plain',
            suffix: raw.suffix ?? '',
            native_action: raw.native_action ?? 'details',
            controls: raw.controls ?? null,
            children: bChildren
        };
    }

    const filters = [],
        blocks = [];
    for (const ch of dash.children) {
        if (ch.tag === 'filter') {
            if (
                !ch.attrib.name ||
                !ch.attrib.title ||
                !ch.attrib.search_type ||
                !ch.attrib.column
            )
                throw Error('Invalid page <filter> attributes');
            filters.push({
                column: ch.attrib.column,
                relation: ch.attrib.relation || '=',
                value: readFilterValue(ch.attrib),
                name: ch.attrib.name,
                title: ch.attrib.title,
                search_type: ch.attrib.search_type,
                enabled: parseTyped(
                    ch.attrib.enabled || 'false',
                    'bool',
                    'enabled'
                )
            });
        } else {
            blocks.push(parseBlockNode(ch));
        }
    }
    const result = { name, title, filters, blocks };
    checkStructure(result);
    return result;
}

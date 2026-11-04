// Tactic Frame's data contract. This module runs unchanged in Qt and Vue.
export { cssRoles as colors } from './foundation.mjs';
import { textStyles } from './foundation.mjs';

/** @typedef {{x:number, y:number, width:number, height:number}} Bounds Logical pixels. */
/** @typedef {{type:string, [key:string]:unknown}} Action UI event or adapter command. */
/** @typedef {'Box'|'Label'|'Icon'|'Button'|'Action'|'CheckBox'|'Field'|'Area'|'Preview'|'List'|'Scroll'|'Choice'|'Grid'|'IconChoice'|'Splitter'|'Switch'|'Graph'|'Chart'|'View'|'ColorChoice'|'Code'|'DateChoice'|'UserChoice'|'SummaryChip'|'StatusChip'|'Segmented'|'Search'|'Identity'|'Progress'|'Empty'|'FileField'} ControlKind */
/** @typedef {Bounds & {kind:ControlKind, id:string, children:FrameNode[], fontRole:keyof typeof textStyles, fontSize:number, action:Action|null, [key:string]:unknown}} FrameNode */
/** @typedef {{nodes:FrameNode[]}} Scene */

export const controlKinds = Object.freeze([
    'Box',
    'Label',
    'Icon',
    'Button',
    'Action',
    'CheckBox',
    'Field',
    'Area',
    'Preview',
    'List',
    'Scroll',
    'Choice',
    'DateChoice',
    'UserChoice',
    'Grid',
    'IconChoice',
    'Splitter',
    'Switch',
    'Graph',
    'Chart',
    'View',
    'ColorChoice',
    'Code',
    'SummaryChip',
    'StatusChip',
    'Segmented',
    'Search',
    'Identity',
    'Progress',
    'Empty',
    'FileField'
]);

const controlKindSet = new Set(controlKinds);
const BOUNDS_KEYS = ['x', 'y', 'width', 'height'];
const RESERVED_KEYS = ['kind', 'id', 'x', 'y', 'width', 'height', 'fontSize'];
const ACTION_KEYS = [
    'action',
    'pressAction',
    'doubleAction',
    'contextAction',
    'activateAction',
    'commitAction',
    'cancelAction',
    'dropAction',
    'dragStartAction',
    'acceptAction'
];

export function rect(x, y, width, height) {
    return {
        x,
        y,
        width: Math.max(0, width),
        height: Math.max(0, height)
    };
}

export function revealListOffset(
    offset,
    index,
    height,
    count,
    rowHeight,
    rowGap = 0,
    offsets = null
) {
    const top = offsets ? offsets[index] : index * rowHeight,
        bottom = top + rowHeight - rowGap;
    const desired =
        top < offset
            ? top
            : bottom > offset + height
              ? bottom - height
              : offset;
    return Math.max(
        0,
        Math.min(
            desired,
            Math.max(
                0,
                (offsets ? offsets[count] : count * rowHeight) - rowGap - height
            )
        )
    );
}

export function label(id, bounds, text, extra) {
    return node(
        'Label',
        id,
        bounds,
        extra ? Object.assign({ text }, extra) : { text }
    );
}

export const muted = {
    fontRole: 'secondary',
    color: 'secondaryText'
};

export function button(id, bounds, text, icon, action, enabled, extra) {
    return node(
        'Button',
        id,
        bounds,
        extra
            ? Object.assign({ text, icon, action, enabled }, extra)
            : { text, icon, action, enabled }
    );
}

/**
 * Create a named native control. Only fontRole enters; fontSize is resolved output.
 * @param {ControlKind} kind
 * @param {string} id Stable within its sibling scene, independent of display text.
 * @param {Bounds} rect
 * @param {Object} [properties] Control data and actions; no engine objects or requests.
 * @returns {FrameNode}
 */
export function node(kind, id, rect, properties) {
    if (!controlKindSet.has(kind))
        throw Error('Unsupported Tactic Frame control: ' + kind);
    if (typeof id !== 'string' || !id.trim())
        throw Error('Missing Frame control id');
    if (
        !rect ||
        typeof rect.x !== 'number' ||
        !isFinite(rect.x) ||
        typeof rect.y !== 'number' ||
        !isFinite(rect.y) ||
        typeof rect.width !== 'number' ||
        !isFinite(rect.width) ||
        typeof rect.height !== 'number' ||
        !isFinite(rect.height)
    ) {
        for (let i = 0; i < BOUNDS_KEYS.length; i++) {
            const key = BOUNDS_KEYS[i];
            if (!rect || typeof rect[key] !== 'number' || !isFinite(rect[key]))
                throw Error('Invalid frame: ' + id + '..' + key);
        }
    }
    if (rect.width < 0 || rect.height < 0) throw Error('Negative frame: ' + id);
    const options = properties || {};
    for (let i = 0; i < RESERVED_KEYS.length; i++) {
        const key = RESERVED_KEYS[i];
        if (Object.prototype.hasOwnProperty.call(options, key))
            throw Error('Reserved Frame property: ' + id + '.' + key);
    }
    const fontRole = options.fontRole === undefined ? 'body' : options.fontRole;
    if (!Object.prototype.hasOwnProperty.call(textStyles, fontRole))
        throw Error('Unknown Frame font role: ' + id + '.' + fontRole);
    const isButton = kind === 'Button';
    const color =
        options.enabled === false &&
        (isButton || kind === 'Field' || kind === 'Area' || kind === 'Choice')
            ? 'disabledText'
            : isButton && options.destructive && !options.highlighted
              ? 'error'
              : isButton &&
                  (options.highlighted || (options.radio && options.selected))
                ? 'selectedText'
                : isButton && options.radio
                  ? 'secondaryText'
                  : 'primaryText';
    const result = {
        kind,
        id,
        text: '',
        color,
        fontRole,
        fontSize: textStyles[fontRole],
        weight: isButton
            ? options.radio && !options.selected
                ? 500
                : 600
            : 400,
        enabled: true,
        opacity: 1,
        children: [],
        action: null,
        x: rect.x,
        y: rect.y,
        width: rect.width,
        height: rect.height
    };
    if (kind === 'List') result.fields = [];
    if (properties) Object.assign(result, properties);
    if (result.titlebar && result.children)
        result.children = result.children.map((child) =>
            child.kind === 'Button'
                ? Object.assign({}, child, { round: true })
                : child
        );
    result.fontRole = fontRole;
    result.fontSize = textStyles[fontRole];
    result.text = options.text == null ? '' : String(options.text);
    return result;
}

/**
 * Validate one scene boundary. Models are engine-owned arrays or native models.
 * @param {Scene} scene
 * @param {Object} [models] Named snapshots/models, kept outside the scene tree.
 * @param {Object} [views] Registered child views; absent slots require optional:true.
 */
export function validateScene(scene, models, views) {
    if (!scene || !sequence(scene.nodes))
        throw Error('Frame scene needs nodes');
    const ids = new Set();
    for (let index = 0; index < scene.nodes.length; index++) {
        const value = scene.nodes[index];
        if (!value || !controlKindSet.has(value.kind))
            throw Error('Unsupported Frame scene control');
        if (!value.id || ids.has(value.id))
            throw Error('Duplicate/missing Frame id: ' + value.id);
        ids.add(value.id);
        if (
            value.scale !== undefined &&
            (!Number.isFinite(value.scale) || value.scale <= 0)
        )
            throw Error('Invalid Frame scale: ' + value.id);
        if (
            !Object.prototype.hasOwnProperty.call(textStyles, value.fontRole) ||
            value.fontSize !== textStyles[value.fontRole]
        )
            throw Error('Invalid Frame typography: ' + value.id);
        if (
            typeof value.x !== 'number' ||
            !isFinite(value.x) ||
            typeof value.y !== 'number' ||
            !isFinite(value.y) ||
            typeof value.width !== 'number' ||
            !isFinite(value.width) ||
            value.width < 0 ||
            typeof value.height !== 'number' ||
            !isFinite(value.height) ||
            value.height < 0
        ) {
            for (let i = 0; i < BOUNDS_KEYS.length; i++) {
                const key = BOUNDS_KEYS[i];
                if (
                    typeof value[key] !== 'number' ||
                    !isFinite(value[key]) ||
                    ((key === 'width' || key === 'height') && value[key] < 0)
                )
                    throw Error(
                        'Invalid Frame bounds: ' + value.id + '.' + key
                    );
            }
        }
        for (let i = 0; i < ACTION_KEYS.length; i++) {
            const key = ACTION_KEYS[i];
            if (
                value[key] != null &&
                (typeof value[key].type !== 'string' || !value[key].type)
            )
                throw Error('Invalid Frame action: ' + value.id + '.' + key);
        }
        if (value.kind === 'List' || value.kind === 'Grid') {
            if (
                typeof value.source !== 'string' ||
                !value.source ||
                !models ||
                !Object.prototype.hasOwnProperty.call(models, value.source) ||
                models[value.source] == null
            )
                throw Error(
                    'Missing Frame source: ' + value.id + '.' + value.source
                );
        }
        if (
            value.kind === 'List' &&
            (typeof value.keyField !== 'string' ||
                !value.keyField ||
                typeof value.rowHeight !== 'number' ||
                !isFinite(value.rowHeight) ||
                listRowHeight(value) <= 0 ||
                (value.rowGap !== undefined &&
                    (!Number.isFinite(value.rowGap) || value.rowGap < 0)))
        )
            throw Error(
                'List needs keyField, positive rowHeight and valid rowGap: ' +
                    value.id
            );
        if (value.kind === 'List' && !sequence(value.fields))
            throw Error('List needs declared model fields: ' + value.id);
        if (
            value.kind === 'List' &&
            value.rowHeightField !== undefined &&
            (typeof value.rowHeightField !== 'string' ||
                !value.rowHeightField ||
                !value.fields.includes(value.rowHeightField))
        )
            throw Error('List needs a declared rowHeightField: ' + value.id);
        // shortcut: variable extents use array models; add native model roles when a caller needs them.
        if (
            value.kind === 'List' &&
            value.rowHeightField !== undefined &&
            !sequence(models[value.source])
        )
            throw Error(
                'Variable Frame rows require an array model: ' + value.id
            );
        if (
            ['Box', 'Scroll', 'Action'].indexOf(value.kind) >= 0 &&
            !sequence(value.children)
        )
            throw Error('Frame container needs children: ' + value.id);
        if (
            value.kind === 'Grid' &&
            (!sequence(value.rowHeaders) ||
                !sequence(value.columnHeaders) ||
                !Number.isFinite(value.cellWidth) ||
                value.cellWidth <= 0 ||
                !Number.isFinite(value.rowHeight) ||
                value.rowHeight <= 0)
        )
            throw Error(
                'Grid needs headers and positive cell geometry: ' + value.id
            );
        if (
            value.kind === 'Search' &&
            value.suggestions !== undefined &&
            !sequence(value.suggestions)
        )
            throw Error('Search needs prepared suggestions: ' + value.id);
        if (
            value.kind === 'Progress' &&
            (!Number.isFinite(value.min ?? 0) ||
                !Number.isFinite(value.max ?? 1) ||
                (value.max ?? 1) <= (value.min ?? 0) ||
                (!value.indeterminate && !Number.isFinite(value.value)))
        )
            throw Error('Progress needs a finite range/value: ' + value.id);
        if (
            value.kind === 'View' &&
            (typeof value.view !== 'string' || !value.view)
        )
            throw Error('Frame View needs a registered name: ' + value.id);
        if (
            value.kind === 'View' &&
            (!views ||
                !Object.prototype.hasOwnProperty.call(views, value.view) ||
                views[value.view] == null) &&
            value.optional !== true
        )
            throw Error('Missing Frame View: ' + value.id + '.' + value.view);
    }
    return scene.nodes;
}

/** Array records are immutable snapshots; a key stays unique across sorting/filtering. */
export function recordIndex(rows, keyField) {
    if (!sequence(rows)) throw Error('Frame array list needs an array');
    const indexes = new Map();
    for (let index = 0; index < rows.length; index++) {
        const value = rows[index] && rows[index][keyField];
        if (
            (typeof value !== 'string' && typeof value !== 'number') ||
            value === '' ||
            (typeof value === 'number' && !isFinite(value))
        )
            throw Error(
                'Missing Frame record key: ' + keyField + '[' + index + ']'
            );
        const key = String(value);
        if (indexes.has(key)) throw Error('Duplicate Frame record key: ' + key);
        indexes.set(key, index);
    }
    return indexes;
}

function sequence(value) {
    // Qt QVariantList wrappers expose indexed access without Array's prototype.
    return (
        value !== null &&
        typeof value === 'object' &&
        Number.isInteger(value.length) &&
        value.length >= 0
    );
}

export function listRowHeight(definition) {
    return (
        definition.rowHeight -
        (definition.rowGap === undefined ? 4 : definition.rowGap)
    );
}

export function listOffsets(definition, rows) {
    if (!definition.rowHeightField) return null;
    const gap = definition.rowGap === undefined ? 4 : definition.rowGap;
    const offsets = [0];
    for (const row of rows) {
        const height = row[definition.rowHeightField];
        const next = offsets[offsets.length - 1] + height;
        if (!Number.isFinite(height) || height <= gap || !Number.isFinite(next))
            throw Error('Invalid Frame row height: ' + definition.id);
        offsets.push(next);
    }
    return offsets;
}

export function listBounds(definition, offsets, index) {
    const gap = definition.rowGap === undefined ? 4 : definition.rowGap;
    return {
        y: offsets ? offsets[index] : index * definition.rowHeight,
        height: offsets
            ? offsets[index + 1] - offsets[index] - gap
            : listRowHeight(definition)
    };
}

export function listRange(
    count,
    rowHeight,
    viewport,
    scroll,
    overscan,
    offsets = null
) {
    const fixed = virtualRange(count, rowHeight, viewport, scroll, overscan);
    if (!offsets) return fixed;
    if (offsets.length !== count + 1) throw Error('Invalid Frame row offsets');
    function boundary(pixel, after) {
        let first = 0,
            last = offsets.length;
        while (first < last) {
            const middle = Math.floor((first + last) / 2);
            if (offsets[middle] < pixel || (after && offsets[middle] === pixel))
                first = middle + 1;
            else last = middle;
        }
        return first;
    }
    const first = Math.min(
        count,
        Math.max(0, boundary(scroll, true) - 1 - overscan)
    );
    return {
        first,
        last: Math.max(
            first,
            Math.min(count, boundary(scroll + viewport, false) + overscan)
        ),
        height: offsets[count]
    };
}

export function virtualRange(count, rowHeight, viewport, scroll, overscan) {
    if (
        !Number.isInteger(count) ||
        count < 0 ||
        !Number.isFinite(rowHeight) ||
        rowHeight <= 0 ||
        !Number.isFinite(viewport) ||
        viewport < 0 ||
        !Number.isFinite(scroll) ||
        !Number.isInteger(overscan) ||
        overscan < 0
    )
        throw Error('Invalid Frame virtual range');
    const first = Math.min(
        count,
        Math.max(0, Math.floor(scroll / rowHeight) - overscan)
    );
    const last = Math.max(
        first,
        Math.min(count, Math.ceil((scroll + viewport) / rowHeight) + overscan)
    );
    return {
        first,
        last,
        height: count * rowHeight
    };
}

let nextCacheId = 1;
const viewCaches = new Map();

export function allocCache() {
    const id = nextCacheId++;
    viewCaches.set(id, {});
    return id;
}

export function freeCache(id) {
    viewCaches.delete(id);
}

export function getCache(id) {
    return viewCaches.get(id) || {};
}

export function setCache(id, cache) {
    viewCaches.set(id, cache);
}

export function setCachedNode(id, key, value) {
    let cache = viewCaches.get(id);
    if (!cache) {
        cache = {};
        viewCaches.set(id, cache);
    }
    cache[key] = value;
}

export function getCachedNode(id, key) {
    const cache = viewCaches.get(id);
    return cache ? cache[key] : undefined;
}

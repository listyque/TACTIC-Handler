import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { arrange } from '../objects/fields.ui.mjs';

export function key(item) {
    return JSON.stringify([item.editorPath, item.form.searchKey || 'readonly']);
}
function values(form) {
    const result = {};
    for (const field of form.fields) result[field.name] = field.value;
    return result;
}
export function entry(store, item) {
    return (
        store[key(item)] || {
            form: item.form,
            values: values(item.form),
            busy: false,
            uncertain: false,
            error: ''
        }
    );
}
export function dirty(state) {
    return JSON.stringify(state.values) !== JSON.stringify(values(state.form));
}
export function find(document, identity) {
    function walk(items) {
        for (const item of items || []) {
            if (item.kind === 'form' && key(item) === identity) return item;
            const nested = walk(item.children);
            if (nested) return nested;
        }
        return null;
    }
    return (
        walk(document.layoutNodes) || walk(document.layoutDetail?.layoutNodes)
    );
}
export function change(store, document, action) {
    const item = find(document, action.key);
    if (!item) return { store };
    const current = entry(store, item),
        next = Object.assign({}, store);
    if (current.busy || item.form.readOnly) return { store };
    if (action.intent === 'cancel') {
        if (!current.uncertain) delete next[action.key];
    } else if (action.intent === 'value' && !current.uncertain) {
        const field = current.form.fields.find(
            (field) => field.name === action.name
        );
        if (!field || field.readOnly) return { store };
        if (!next[action.key] && Object.keys(next).length >= 20)
            throw Error('Finish or discard another form draft first');
        next[action.key] = Object.assign({}, current, {
            values: Object.assign({}, current.values, {
                [action.name]: action.value
            }),
            error: ''
        });
    } else if (
        (action.intent === 'save' &&
            dirty(current) &&
            !current.uncertain &&
            !current.stale) ||
        (action.intent === 'check' && current.uncertain)
    ) {
        const changed = {};
        for (const field of current.form.fields)
            if (!field.readOnly && current.values[field.name] !== field.value)
                changed[field.name] = current.values[field.name];
        if (!Object.keys(changed).length) return { store };
        next[action.key] = Object.assign({}, current, {
            busy: true,
            error: ''
        });
        return {
            store: next,
            command: Object.assign({}, item.form.scope, {
                action: action.intent,
                values: changed,
                expected_revision: current.form.expectedRevision,
                config_revision: current.form.configRevision
            })
        };
    }
    return { store: next };
}
export function settled(store, identity, result, failure) {
    if (!store[identity]) return store;
    const next = Object.assign({}, store),
        state = next[identity];
    if (result?.state === 'saved') delete next[identity];
    else
        next[identity] = Object.assign({}, state, {
            busy: false,
            uncertain: !!failure?.uncertain,
            stale: result?.state === 'conflict',
            error:
                failure?.message ||
                (result?.state === 'unchanged'
                    ? 'Changes were not saved. You can save again.'
                    : 'Record changed. Reload before saving.')
        });
    return next;
}
export function interrupted(store) {
    let next = store;
    for (const identity of Object.keys(store))
        if (store[identity].busy)
            next = settled(next, identity, null, {
                message:
                    'The page changed while a save was pending. Check saved state.',
                uncertain: true
            });
    return next;
}
export function describe(item, id, width, store, language, enabled) {
    const state = entry(store, item),
        tr = (text) => translate(text, language),
        children = [];
    const event = (intent, extra = {}) =>
        Object.assign({ type: 'record-form', intent, key: key(item) }, extra);
    let y = 0;
    if (item.text) {
        children.push(
            label(id + '_title', rect(0, y, width, 28), item.text, {
                weight: 600
            })
        );
        y += 36;
    }
    if (state.form.hint) {
        children.push(
            label(id + '_hint', rect(0, y, width, 48), tr(state.form.hint), {
                wrap: true,
                color: 'secondaryText'
            })
        );
        y += 56;
    }
    const layout = arrange(
        width,
        state.form.fields.map(
            (field) => 24 + (field.type === 'multiline' ? 88 : 36)
        ),
        item.min_cell_width || 200,
        item.columns || 3,
        item.gap ?? 12
    );
    const top = y;
    for (const [index, field] of state.form.fields.entries()) {
        const box = layout.cells[index],
            x = box.x,
            fieldWidth = box.width;
        y = top + box.y;
        const name = id + '_field_' + field.name,
            active =
                enabled &&
                !state.busy &&
                !state.uncertain &&
                !state.stale &&
                !field.readOnly;
        children.push(
            label(
                name + '_label',
                rect(x, y, fieldWidth, 20),
                field.title + (field.required ? ' *' : ''),
                { color: 'secondaryText' }
            )
        );
        y += 24;
        const value = state.values[field.name],
            action = event('value', { name: field.name });
        if (field.readOnly)
            children.push(
                label(
                    name,
                    rect(x, y, fieldWidth, 32),
                    value == null ? '—' : String(value)
                )
            );
        else if (field.type === 'select')
            children.push(
                node('Choice', name, rect(x, y, fieldWidth, 36), {
                    value: value == null ? '' : String(value),
                    options: field.options.map((option) => ({
                        value: String(option.value),
                        label: option.label
                    })),
                    enabled: active,
                    action
                })
            );
        else if (field.type === 'bool')
            children.push(
                node('CheckBox', name, rect(x, y, fieldWidth, 36), {
                    checked: !!value,
                    text: field.title,
                    enabled: active,
                    action
                })
            );
        else if (['date', 'datetime-local'].includes(field.type))
            children.push(
                node('DateChoice', name, rect(x, y, fieldWidth, 36), {
                    text: value || '',
                    includeTime: field.type === 'datetime-local',
                    label: field.title,
                    enabled: active,
                    action
                })
            );
        else
            children.push(
                node(
                    field.type === 'multiline' ? 'Area' : 'Field',
                    name,
                    rect(
                        x,
                        y,
                        fieldWidth,
                        field.type === 'multiline' ? 88 : 36
                    ),
                    {
                        text: value == null ? '' : String(value),
                        inputType:
                            field.type === 'date'
                                ? 'date'
                                : field.type === 'datetime-local'
                                  ? 'datetime-local'
                                  : 'text',
                        enabled: active,
                        action
                    }
                )
            );
    }
    y = top + layout.height + 12;
    if (state.error) {
        children.push(
            label(id + '_error', rect(0, y, width, 48), tr(state.error), {
                color: 'error',
                wrap: true
            })
        );
        y += 56;
    }
    if (!item.form.readOnly) {
        const w = Math.min(150, (width - 8) / 2),
            active = enabled && !state.busy;
        children.push(
            button(
                id + '_save',
                rect(0, y, w, 36),
                tr(state.uncertain ? 'Check saved state' : 'Save'),
                state.uncertain ? 'refresh' : 'save',
                event(state.uncertain ? 'check' : 'save'),
                active && (state.uncertain || (!state.stale && dirty(state))),
                { highlighted: true }
            )
        );
        children.push(
            button(
                id + '_cancel',
                rect(w + 8, y, w, 36),
                tr('Cancel'),
                'close',
                event('cancel'),
                active && !state.uncertain && dirty(state)
            )
        );
        y += 44;
    }
    return { children, height: y };
}

export function field(item, id, width) {
    const children = [],
        value = item.value,
        hasValue = value !== null && value !== undefined;
    let text = hasValue ? String(value) : '—',
        y = 0;
    if (item.format === 'date' && hasValue) text = text.slice(0, 10);
    if (item.format === 'datetime' && hasValue)
        text = text.replace('T', ' ').slice(0, 19);
    if (hasValue && item.suffix) text += item.suffix;
    if (item.text) {
        children.push(
            label(id + '_label', rect(0, 0, width, 20), item.text, {
                color: 'secondaryText'
            })
        );
        y = 24;
    }
    if (item.format === 'badge')
        children.push(
            node(
                'StatusChip',
                id,
                rect(
                    0,
                    y,
                    Math.min(width, Math.max(80, text.length * 8 + 24)),
                    28
                ),
                {
                    text,
                    accent: item.textColor || 'contentAccent',
                    dense: true,
                    enabled: true
                }
            )
        );
    else
        children.push(
            label(id, rect(0, y, width, 28), text, {
                fontRole: item.textRole || 'body',
                color: item.textColor || 'primaryText',
                weight: item.textWeight || 400
            })
        );
    if (item.format === 'progress') {
        const percent = hasValue
            ? Math.max(0, Math.min(100, Number(value)))
            : 0;
        children.push(
            node('Box', id + '_track', rect(0, y + 30, width, 4), {
                background: 'outlineVariant',
                radius: 2
            })
        );
        children.push(
            node(
                'Box',
                id + '_progress',
                rect(0, y + 30, (width * percent) / 100, 4),
                { background: 'contentAccent', radius: 2 }
            )
        );
        y += 10;
    }
    return { children, height: y + 32 };
}

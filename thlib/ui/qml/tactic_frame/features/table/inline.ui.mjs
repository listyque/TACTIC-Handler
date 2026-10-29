import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { controls } from '../../core/foundation.mjs';

export function explicitSave(mode) {
    return (
        ['multiline', 'date', 'datetime', 'color', 'multi', 'tags'].indexOf(
            mode
        ) >= 0
    );
}

export function describe(model, width, language, measureTag) {
    const tr = (text) => translate(text, language);
    const enabled = !model.busy && !model.uncertain;
    const mode = model.mode || 'text',
        nodes = [];
    const action = { type: 'value' };
    let top = mode === 'multiline' || mode === 'tags' ? 32 : 0;
    if (top)
        nodes.push(
            label(
                'tableInlineHeading',
                rect(0, 0, width, 24),
                tr(mode === 'tags' ? 'Edit tags' : 'Edit description'),
                { weight: 600 }
            )
        );
    const bounds = rect(
        0,
        top,
        width,
        mode === 'multiline' ? 260 : Math.max(36, model.height || 36)
    );
    const options = model.options || [];
    const props = { label: model.title || '', enabled, action };
    if (mode === 'tags') {
        let left = 0;
        const chip = controls.button;
        const chrome =
            chip.iconPadding + chip.padding + chip.iconSize + chip.spacing;
        for (const [index, tag] of tags(model.value).entries()) {
            const chipWidth = Math.min(
                width,
                Math.max(chip.minimumWidth, Math.ceil(measureTag(tag)) + chrome)
            );
            if (left && left + chipWidth > width) {
                left = 0;
                top += 42;
            }
            nodes.push(
                button(
                    'tableInlineTag_' + index,
                    rect(left, top, chipWidth, 36),
                    tag,
                    'close',
                    { type: 'removeTag', value: tag },
                    enabled,
                    { tooltip: tr('Remove tag') + ': ' + tag, tonal: true }
                )
            );
            left += chipWidth + 6;
        }
        if (left) top += 42;
        nodes.push(
            node(
                'Choice',
                'tableInlineValue',
                rect(0, top, Math.max(0, width - 80), 36),
                {
                    editable: true,
                    enabled,
                    label: tr('Edit tags'),
                    placeholder: tr('Enter tags separated by commas'),
                    value: model.draft || '',
                    options: options.filter(
                        (option) => tags(model.value).indexOf(option.value) < 0
                    ),
                    action: { type: 'tagDraft' },
                    commitAction: { type: 'addTag' }
                }
            )
        );
        nodes.push(
            button(
                'tableInlineTagAdd',
                rect(Math.max(0, width - 72), top, 72, 36),
                tr('Add'),
                '',
                { type: 'addTag' },
                enabled && tags(model.draft).length > 0
            )
        );
        bounds.height = top + 36 - 32;
        top = 32;
    } else if (mode === 'select' || mode === 'user') {
        nodes.push(
            node(
                mode === 'user' ? 'UserChoice' : 'Choice',
                'tableInlineValue',
                bounds,
                Object.assign({}, props, { options, value: model.value })
            )
        );
    } else if (mode === 'bool') {
        nodes.push(
            node(
                'Switch',
                'tableInlineValue',
                rect(0, top, Math.min(54, width), bounds.height),
                Object.assign({}, props, { checked: !!model.value })
            )
        );
        nodes.push(
            label(
                'tableInlineBooleanLabel',
                rect(62, top, width - 62, bounds.height),
                tr(model.value ? 'Yes' : 'No')
            )
        );
    } else if (mode === 'date' || mode === 'datetime') {
        nodes.push(
            node(
                'DateChoice',
                'tableInlineValue',
                bounds,
                Object.assign({}, props, {
                    text: String(model.value || ''),
                    includeTime: mode === 'datetime',
                    language
                })
            )
        );
    } else if (mode === 'color') {
        nodes.push(
            node(
                'ColorChoice',
                'tableInlineValue',
                bounds,
                Object.assign({}, props, { value: model.value || '' })
            )
        );
    } else if (mode === 'multi') {
        const values = model.value || [];
        for (let index = 0; index < options.length; index++) {
            const option = options[index];
            nodes.push(
                node(
                    'CheckBox',
                    'tableInlineOption_' + index,
                    rect(0, top + index * 36, width, 32),
                    {
                        text: option.label,
                        checked: values.indexOf(option.value) >= 0,
                        enabled,
                        action: { type: 'toggle', value: option.value }
                    }
                )
            );
        }
        bounds.height = options.length * 36;
    } else {
        nodes.push(
            node(
                mode === 'multiline' ? 'Area' : 'Field',
                'tableInlineValue',
                bounds,
                Object.assign({}, props, {
                    text: String(model.value == null ? '' : model.value),
                    selectOnFocus: mode !== 'multiline',
                    inputType: mode === 'time' ? 'time' : 'text',
                    commitAction:
                        mode === 'multiline' || model.explicitSave
                            ? null
                            : { type: 'save' },
                    keys:
                        mode === 'multiline'
                            ? {}
                            : {
                                  Enter: { type: 'save' },
                                  Escape: { type: 'cancel' }
                              }
                })
            )
        );
    }
    top += bounds.height;
    if (model.count > 1 && mode === 'multiline') {
        top += 8;
        nodes.push(
            label(
                'tableInlineBatchCount',
                rect(0, top, width, 24),
                tr('Apply to {count} rows').replace('{count}', model.count),
                { color: 'secondaryText' }
            )
        );
        top += 24;
    }
    for (const message of [
        model.error,
        model.uncertain
            ? tr('Check the server result before saving again.')
            : ''
    ]) {
        if (!message) continue;
        top += 8;
        nodes.push(
            label(
                'tableInlineNotice_' + nodes.length,
                rect(0, top, width, 44),
                message,
                {
                    wrap: true,
                    color: model.error === message ? 'error' : 'secondaryText',
                    role: 'alert'
                }
            )
        );
        top += 44;
    }
    if (
        model.explicitSave ||
        explicitSave(mode) ||
        model.error ||
        model.uncertain
    ) {
        top += 8;
        const gap = 8,
            part = Math.max(0, (width - gap) / 2);
        if (model.uncertain) {
            nodes.push(
                button(
                    'tableInlineCheck',
                    rect(0, top, width, 36),
                    tr('Check saved changes'),
                    'refresh',
                    { type: 'check' },
                    !model.busy
                )
            );
            top += 44;
        }
        nodes.push(
            button(
                'tableInlineCancel',
                rect(0, top, part, 36),
                tr('Cancel'),
                '',
                { type: 'cancel' },
                !model.busy
            )
        );
        nodes.push(
            button(
                'tableInlineSave',
                rect(part + gap, top, part, 36),
                tr('Save'),
                '',
                { type: 'save' },
                enabled,
                { highlighted: true }
            )
        );
        top += 36;
    }
    return { nodes, height: top };
}

export function change(value, event) {
    if (event.type !== 'toggle') return event.value;
    const values = value || [];
    return values.indexOf(event.value) < 0
        ? values.concat([event.value])
        : values.filter((item) => item !== event.value);
}

export function savesOnChange(mode) {
    return ['select', 'user', 'bool'].indexOf(mode) >= 0;
}

export function tags(value) {
    const result = [];
    for (const tag of String(value == null ? '' : value).split(/[,\n]+/)) {
        const trimmed = tag.trim();
        if (trimmed && result.indexOf(trimmed) < 0) result.push(trimmed);
    }
    return result;
}

export function tagValue(value, draft) {
    return tags(tags(value).concat(tags(draft)).join(', ')).join(', ');
}

export function editTags(value, draft, action) {
    if (action.type === 'tagDraft') return { value, draft: action.value };
    if (action.type === 'removeTag')
        return {
            value: tags(value)
                .filter((tag) => tag !== action.value)
                .join(', '),
            draft
        };
    return {
        value: tagValue(
            value,
            action.value === undefined ? draft : action.value
        ),
        draft: ''
    };
}

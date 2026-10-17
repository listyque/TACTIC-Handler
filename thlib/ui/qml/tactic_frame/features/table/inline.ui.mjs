import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export function explicitSave(mode) {
    return (
        ['multiline', 'date', 'datetime', 'color', 'multi'].indexOf(mode) >= 0
    );
}

export function describe(model, width, language) {
    const tr = (text) => translate(text, language);
    const enabled = !model.busy && !model.uncertain;
    const mode = model.mode || 'text',
        nodes = [];
    const action = { type: 'value' };
    let top = mode === 'multiline' ? 32 : 0;
    if (top)
        nodes.push(
            label(
                'tableInlineHeading',
                rect(0, 0, width, 24),
                tr('Edit description'),
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
    if (mode === 'select' || mode === 'user') {
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
                        mode === 'multiline' ? null : { type: 'save' },
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
    if (explicitSave(mode) || model.error || model.uncertain) {
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

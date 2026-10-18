import { node, rect, label, button, muted } from '../../core/frame.mjs';
import { sections } from '../../controls/forms/sections.ui.mjs';
import { translate } from '../../core/strings.mjs';

export function fields(model, language) {
    return (model.schema.options || []).map((field) => {
        const kind =
            {
                boolean: 'Switch',
                choice: 'Choice',
                integer: 'Number',
                text: 'Field'
            }[field.type] || 'Field';
        const value = model.values[field.key];
        return {
            id: 'dccSettingControl_' + field.key,
            field: field.key,
            kind,
            title: field.title || field.key,
            description: field.description || '',
            controlWidth:
                kind === 'Switch'
                    ? 52
                    : kind === 'Number'
                      ? 130
                      : kind === 'Choice'
                        ? 220
                        : 320,
            value: Number(value || 0),
            min: Number(field.minimum || 0),
            max: Number(field.maximum === undefined ? 999999 : field.maximum),
            step: 1,
            options: (field.choices || []).map((row) => ({
                value: row.value,
                label: translate(row.label, language)
            })),
            props: {
                text: value === undefined ? '' : String(value),
                value,
                checked: !!value,
                readOnly: !!field.read_only,
                placeholder: translate(field.placeholder || '', language),
                inputType: kind === 'Number' ? 'number' : 'text',
                enabled: model.available && !field.read_only
            }
        };
    });
}

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language),
        inset = 16,
        inner = Math.max(0, width - inset * 2);
    const form = sections(
        fields(model, language),
        Math.max(0, inner - 16),
        language,
        model.available,
        model.style || 'md3'
    );
    const errorHeight = model.error ? 42 : 0;
    return {
        nodes: [
            node('Box', 'dccOptionsBackground', rect(0, 0, width, height), {
                background: 'panelDeep'
            }),
            node('Box', 'dccOptionsIconSurface', rect(inset, inset, 44, 44), {
                background: 'secondaryContainer',
                radius: 14,
                children: [
                    node('Icon', 'dccOptionsIcon', rect(11, 11, 22, 22), {
                        icon: model.schema.icon || 'deployed-code',
                        color: 'action'
                    })
                ]
            }),
            label(
                'dccOptionsTitle',
                rect(70, inset, width - 86, 22),
                tr(model.schema.title || 'DCC action'),
                { fontRole: 'bodyLarge', weight: 600 }
            ),
            label(
                'dccOptionsTarget',
                rect(70, inset + 24, width - 86, 20),
                model.target || '',
                muted
            ),
            node(
                'Scroll',
                'dccActionOptions',
                rect(
                    inset,
                    72,
                    inner,
                    Math.max(0, height - 72 - inset - 50 - errorHeight)
                ),
                {
                    scrollbarId: 'dccOptionsScrollBar',
                    contentHeight: form.height,
                    children: form.nodes
                }
            ),
            label(
                'dccOptionsError',
                rect(
                    inset,
                    height - inset - 38 - errorHeight,
                    inner,
                    errorHeight
                ),
                model.error || '',
                { color: 'error', wrap: true }
            ),
            button(
                'dccOptionsRun',
                rect(width - inset - 110, height - inset - 38, 110, 38),
                tr('Run'),
                model.schema.icon || 'play-arrow',
                { type: 'run' },
                model.available,
                { highlighted: true }
            )
        ]
    };
}

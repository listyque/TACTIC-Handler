import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export function describe(value, width, language, enabled = true) {
    const tr = (text) => translate(text, language),
        name = String(value || '')
            .replace(/\\/g, '/')
            .split('/')
            .pop(),
        actions = name ? 76 : 40;
    const nodes = [
        node('Box', 'fileInputSurface', rect(0, 0, width, 44), {
            background: 'surfaceContainerHigh'
        }),
        label(
            'fileInputName',
            rect(12, 10, Math.max(0, width - actions - 20), 24),
            name || tr('No file selected'),
            {
                color: name ? 'primaryText' : 'secondaryText',
                toolTip: name || '',
                elideMiddle: true
            }
        ),
        button(
            'fileInputChoose',
            rect(Math.max(0, width - actions), 6, 32, 32),
            tr('Choose file'),
            'attach-file',
            { type: 'choose' },
            enabled,
            { iconOnly: true, iconAction: true }
        )
    ];
    if (name)
        nodes.push(
            button(
                'fileInputClear',
                rect(Math.max(0, width - 36), 6, 32, 32),
                tr('Clear file'),
                'close',
                { type: 'clear' },
                enabled,
                { iconOnly: true, iconAction: true }
            )
        );
    return { height: 44, nodes };
}

import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export function describe(model, width, height, language, selected = 0) {
    const sections = model.sections || [],
        index = Math.max(
            0,
            Math.min(Number(selected) || 0, sections.length - 1)
        );
    const nodes = [
        label(
            'tableDocumentIdentity',
            rect(0, 0, Math.max(0, width - 44), 32),
            model.identity || '',
            { weight: 600 }
        ),
        button(
            'tableDocumentClose',
            rect(Math.max(0, width - 32), 0, 32, 32),
            translate('Close', language),
            'close',
            { type: 'close' },
            true,
            { iconOnly: true, iconAction: true }
        )
    ];
    if (!sections.length)
        nodes.push(
            label(
                'tableDocumentEmpty',
                rect(0, 42, width, 32),
                translate('No groups', language),
                { color: 'secondaryText' }
            )
        );
    else {
        nodes.push(
            node('Choice', 'tableDocumentGroup', rect(0, 42, width, 36), {
                value: String(index),
                label: translate('Groups', language),
                options: sections.map((section, index) => ({
                    value: String(index),
                    label: section.title
                })),
                action: { type: 'section' }
            })
        );
        const section = sections[index];
        nodes.push(
            node(
                'Code',
                'tableDocumentSource',
                rect(0, 88, width, Math.max(0, height - 88)),
                {
                    text: section.text || '',
                    syntax: section.syntax || 'text',
                    language,
                    readOnly: true,
                    helpAction: { type: 'help', topic: 'table_widgets_b07' },
                    bufferKey: section.title + ':' + index
                }
            )
        );
    }
    return { nodes };
}

import { node, rect, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { link } from './cells.ui.mjs';

export function describe(cell, width, height, language, editable, server) {
    const size = Math.min(60, Math.max(0, height - 38), Math.max(0, width - 8)),
        nodes = [];
    if (cell.preview && size > 0)
        nodes.push(
            node(
                'Preview',
                'publishPreview',
                rect((width - size) / 2, 2, size, size),
                {
                    source: link(cell.preview.image || '', server) || '',
                    icon: 'sobject',
                    round: false,
                    outlined: false
                }
            )
        );
    const top = cell.preview
        ? Math.min(height - 30, size + 6)
        : (height - 28) / 2;
    nodes.push(
        button(
            'tablePublish',
            rect(Math.max(0, (width - 28) / 2), Math.max(0, top), 28, 28),
            translate('Publish', language),
            'publish',
            {
                type: 'service',
                name: 'publish',
                view: cell.publishView || 'publish'
            },
            editable && cell.available !== false,
            { iconOnly: true, iconAction: true }
        )
    );
    return { nodes };
}

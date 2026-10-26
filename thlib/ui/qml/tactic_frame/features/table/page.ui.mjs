import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language);
    const nodes = [
        node('Box', 'workspacePageBackground', rect(0, 0, width, height), {
            background: 'workspace',
            radius: 0
        }),
        label(
            'workspacePageTitle',
            rect(16, 12, Math.max(0, width - 76), 28),
            model.title || '',
            {
                fontRole: 'heading',
                weight: 600
            }
        ),
        button(
            'workspacePageRefresh',
            rect(width - 48, 8, 32, 32),
            tr('Refresh'),
            'refresh',
            { type: 'refresh' },
            !model.busy,
            { iconOnly: true }
        )
    ];
    if (model.busy || model.error)
        nodes.push(
            label(
                'workspacePageStatus',
                rect(16, 64, Math.max(0, width - 32), 64),
                model.error || tr('Loading interface…'),
                { wrap: true, color: model.error ? 'error' : 'secondaryText' }
            )
        );
    return {
        nodes,
        bodyBounds: rect(
            12,
            52,
            Math.max(0, width - 24),
            Math.max(0, height - 64)
        )
    };
}

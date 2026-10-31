import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { spacing } from '../../core/foundation.mjs';

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language);
    const nodes = [
        node('Box', 'workspacePageBackground', rect(0, 0, width, height), {
            background: 'workspace',
            radius: 0
        }),
        node('Box', 'workspacePageHeader', rect(0, 0, width, 52), {
            background: 'panel',
            radius: 0
        }),
        node('Box', 'workspacePageHeaderDivider', rect(0, 51, width, 1), {
            background: 'outlineVariant',
            radius: 0
        }),
        label(
            'workspacePageTitle',
            rect(
                spacing.content,
                12,
                Math.max(0, width - (model.canEdit ? 104 : 64)),
                28
            ),
            model.title || '',
            {
                fontRole: 'heading',
                weight: 600
            }
        ),
        button(
            'workspacePageRefresh',
            rect(width - spacing.content - 32, 10, 32, 32),
            tr('Refresh'),
            'refresh',
            { type: 'refresh' },
            !model.busy,
            { iconOnly: true }
        )
    ];
    if (model.canEdit)
        nodes.push(
            button(
                'workspacePageEdit',
                rect(
                    width - spacing.content - 64 - spacing.compact,
                    10,
                    32,
                    32
                ),
                tr('Edit page layout'),
                'edit',
                { type: 'edit' },
                !model.busy,
                { iconOnly: true }
            )
        );
    if (model.busy || model.error)
        nodes.push(
            label(
                'workspacePageStatus',
                rect(
                    spacing.content,
                    64,
                    Math.max(0, width - spacing.content * 2),
                    64
                ),
                model.error || tr('Loading interface…'),
                { wrap: true, color: model.error ? 'error' : 'secondaryText' }
            )
        );
    return {
        nodes,
        bodyBounds: rect(0, 52, Math.max(0, width), Math.max(0, height - 52))
    };
}

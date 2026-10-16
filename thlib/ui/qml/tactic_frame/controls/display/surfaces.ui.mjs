import { node, rect, label, button } from '../../core/frame.mjs';

// Neutral surfaces: values and actions come from the containing form.
export function header(model, width, height = 60) {
    const actions = model.actions || [];
    const leading = model.back ? 48 : model.icon ? 42 : 12;
    const right = width - 12 - actions.length * 36;
    const nodes = [
        node('Box', 'headerSurface', rect(0, 0, width, height), {
            radius: model.radius || 0,
            background: 'surfaceContainerHigh'
        })
    ];
    if (model.back)
        nodes.push(
            button(
                'headerBack',
                rect(8, (height - 32) / 2, 32, 32),
                model.backLabel || 'Back',
                'chevron-left',
                { type: 'back' },
                model.enabled !== false,
                { iconOnly: true }
            )
        );
    else if (model.icon)
        nodes.push(
            node('Icon', 'headerIcon', rect(12, (height - 18) / 2, 18, 18), {
                icon: model.icon,
                color: 'action'
            })
        );
    nodes.push(
        label(
            'headerTitle',
            rect(
                leading,
                model.subtitle ? 10 : (height - 22) / 2,
                Math.max(0, right - leading - 8),
                22
            ),
            model.title || '',
            { fontRole: 'bodyLarge', weight: 600 }
        )
    );
    if (model.subtitle)
        nodes.push(
            label(
                'headerSubtitle',
                rect(leading, 34, Math.max(0, right - leading - 8), 16),
                model.subtitle,
                { fontRole: 'secondary', color: 'secondaryText' }
            )
        );
    actions.forEach((action, index) =>
        nodes.push(
            button(
                'headerAction_' + index,
                rect(right + index * 36, (height - 32) / 2, 32, 32),
                action.label,
                action.icon,
                { type: action.command },
                action.enabled !== false,
                { iconOnly: true }
            )
        )
    );
    return { width, height, nodes };
}

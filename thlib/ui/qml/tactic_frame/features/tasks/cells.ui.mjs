import { node, rect, label } from '../../core/frame.mjs';
import { fontMetricHeight, textStyles } from '../../core/foundation.mjs';

export function initials(label) {
    const words = String(label || '')
        .trim()
        .split(/\s+/)
        .filter(Boolean);
    return words.length
        ? (words[0][0] + (words[1]?.[0] || '')).toUpperCase()
        : '?';
}

// Value controls keep their lazy native editors; this is their shared idle surface.
export function choice(model, width, height) {
    const nodes = [
        node('Box', 'taskTableCellSurface', rect(0, 0, width, height), {
            background:
                model.enabled && model.hovered
                    ? 'surfaceContainerHigh'
                    : 'surfaceContainerLow',
            border: model.actionField === false ? 'outlineVariant' : undefined,
            radiusRole:
                model.actionField === false ? 'fieldRadius' : 'itemRadius'
        })
    ];
    let left = 11;
    if (model.avatar) {
        const size = Math.max(0, Math.min(22, height - 4));
        nodes.push(
            node(
                'View',
                'taskTableCellAvatar',
                rect(left, (height - size) / 2, size, size),
                { view: 'avatar' }
            )
        );
        left += size + 7;
    }
    if (model.showAccent && model.accent) {
        nodes.push(
            node(
                'Box',
                'taskTableCellAccent',
                rect(left, (height - 9) / 2, 9, 9),
                { background: model.accent, radius: 4.5 }
            )
        );
        left += 16;
    }
    const right = model.indicator ? 33 : 12;
    const textHeight = Math.min(
        height,
        model.textHeight ||
            fontMetricHeight(textStyles[model.fontRole || 'body'])
    );
    nodes.push(
        label(
            'taskTableCellDisplayLabel',
            rect(
                left,
                Math.round((height - textHeight) / 2),
                width - left - right,
                textHeight
            ),
            model.text || '',
            {
                fontRole: model.fontRole || 'body',
                color: model.enabled ? 'primaryText' : 'disabledText'
            }
        )
    );
    if (model.indicator)
        nodes.push(
            node(
                'Icon',
                'taskTableCellIndicator',
                rect(width - 26, (height - 17) / 2, 17, 17),
                {
                    icon: 'expand-more',
                    color: model.enabled ? 'secondaryText' : 'disabledText'
                }
            )
        );
    return { nodes, height };
}

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

export function choiceStyle(model) {
    return {
        background:
            model.enabled && model.hovered
                ? 'surfaceContainerHigh'
                : 'surfaceContainerLow',
        border: model.actionField === false ? 'outlineVariant' : undefined,
        radiusRole: model.actionField === false ? 'fieldRadius' : 'itemRadius',
        textColor: model.enabled ? 'primaryText' : 'disabledText',
        indicatorColor: model.enabled ? 'secondaryText' : 'disabledText',
        indicatorIcon: 'expand-more'
    };
}

export function choiceLayout(model, width, height) {
    let left = 11;
    const avatarSize = Math.max(0, Math.min(22, height - 4));
    const avatar = model.avatar
        ? rect(left, (height - avatarSize) / 2, avatarSize, avatarSize)
        : null;
    if (avatar) left += avatar.width + 7;
    const accent =
        model.showAccent && model.accent
            ? Object.assign(rect(left, (height - 9) / 2, 9, 9), { radius: 4.5 })
            : null;
    if (accent) left += 16;
    const textHeight = Math.min(
        height,
        model.textHeight ||
            fontMetricHeight(textStyles[model.fontRole || 'body'])
    );
    return {
        avatar,
        accent,
        label: label(
            'taskTableCellDisplayLabel',
            rect(
                left,
                Math.round((height - textHeight) / 2),
                width - left - (model.indicator ? 33 : 12),
                textHeight
            ),
            model.text || '',
            { fontRole: model.fontRole || 'body' }
        ),
        indicator: model.indicator
            ? rect(width - 26, (height - 17) / 2, 17, 17)
            : null
    };
}

// Both renderers use the same geometry and paint roles.
export function choice(model, width, height) {
    const layout = choiceLayout(model, width, height),
        style = choiceStyle(model);
    const nodes = [
        node('Box', 'taskTableCellSurface', rect(0, 0, width, height), {
            background: style.background,
            border: style.border,
            radiusRole: style.radiusRole
        })
    ];
    if (layout.avatar)
        nodes.push(
            node('View', 'taskTableCellAvatar', layout.avatar, {
                view: 'avatar'
            })
        );
    if (layout.accent) {
        nodes.push(
            node(
                'Box',
                'taskTableCellAccent',
                rect(
                    layout.accent.x,
                    layout.accent.y,
                    layout.accent.width,
                    layout.accent.height
                ),
                { background: model.accent, radius: layout.accent.radius }
            )
        );
    }
    nodes.push(Object.assign(layout.label, { color: style.textColor }));
    if (layout.indicator)
        nodes.push(
            node('Icon', 'taskTableCellIndicator', layout.indicator, {
                icon: style.indicatorIcon,
                color: style.indicatorColor
            })
        );
    return { nodes, height };
}

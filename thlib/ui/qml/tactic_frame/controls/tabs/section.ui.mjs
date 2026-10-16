import { node, rect, label } from '../../core/frame.mjs';
import { blend, readableText } from '../../core/foundation.mjs';
import { dimensions, sectionWidth } from './workspace.ui.mjs';

const hexColor = (channels) =>
    '#' +
    channels
        .map((value) => ('0' + Math.round(value).toString(16)).slice(-2))
        .join('');

export const metrics = Object.assign({}, dimensions, {
    top: 7,
    bottom: 7,
    panelBottom: 5,
    closeExtent: 32,
    closeInset: 7,
    menuWidth: 244,
    closeIconSize: 14,
    closeAllowance: 40,
    holdDelay: 500
});

export function row(width, record, state, palette) {
    const selected = !!record.current,
        expanded = !!state.revealed;
    const raw = String(record.accent || ''),
        hex = raw.replace(/^#/, '');
    const expandedHex =
        hex.length === 3
            ? [...hex].map((value) => value + value).join('')
            : hex;
    const accent = /^[a-f0-9]{6}$/i.test(expandedHex)
        ? expandedHex.match(/../g).map((value) => parseInt(value, 16))
        : palette.action;
    const accentRole = hexColor(accent),
        badge = blend(accent, [0, 0, 0], 1 - 1 / (selected ? 1.35 : 1.65));
    const surfaceWidth = Math.max(0, width - (expanded ? 4 : 8));
    const base = selected ? 'contentSelection' : 'toolBar';
    const amount = state.pressed ? 0.12 : expanded ? 0.08 : 0;
    const background = amount
        ? { mix: [base, selected ? 'action' : 'primaryText', amount] }
        : base;
    return {
        width,
        height: metrics.rowHeight,
        nodes: [
            node('Box', 'sectionTabSurface', rect(4, 2, surfaceWidth, 38), {
                background,
                radius: 9
            }),
            node(
                'Box',
                'sectionTabSelection',
                rect(4 + surfaceWidth - 3, 7, 3, 28),
                { background: accentRole, radius: 1.5, visible: selected }
            ),
            node('Box', 'sectionTabBadge', rect(7, 6, 30, 30), {
                background: hexColor(badge),
                border: accentRole,
                radius: 15
            }),
            node('Icon', 'sectionTabIcon', rect(14, 13, 16, 16), {
                icon: record.icon || 'link',
                color: hexColor(readableText(badge))
            }),
            label(
                'sectionTabTitle',
                rect(51, 12.5, Math.max(0, width - 97), 17),
                record.title,
                {
                    fontRole: 'body',
                    weight: selected ? 700 : 600,
                    color: selected ? 'selectedText' : 'primaryText',
                    visible: expanded && width > 96
                }
            ),
            node('View', 'sectionTabClose', closeBounds(width), {
                view: 'close',
                visible: expanded && width > 120
            })
        ]
    };
}

export function expandedWidth(labelWidth, available = 320) {
    return sectionWidth(labelWidth, available);
}

// Both engines hit-test Y; a collapsed neighbor has no hit area at the panel center.
export function targetAt(rows, center) {
    if (!rows.length) return -1;
    for (let index = 0; index < rows.length - 1; index++)
        if (center < (rows[index].bottom + rows[index + 1].top) / 2)
            return index;
    return rows.length - 1;
}

export function drag(press, point, scroll, threshold = metrics.dragThreshold) {
    const dy = point.y - press.y;
    if (Math.abs(dy) < threshold || Math.abs(dy) < Math.abs(point.x - press.x))
        return null;
    const translation = dy + scroll - press.scroll;
    const source = press.boxes[press.source];
    return {
        source: press.source,
        target: targetAt(
            press.boxes,
            source.top + source.height / 2 + translation
        ),
        translation,
        step: source.height + metrics.rowSpacing
    };
}

export function actions(index, count, title) {
    return [
        { header: true, title, translate: false },
        {
            title: 'Move section up',
            icon: 'arrow-upward',
            command: 'up',
            enabled: index > 0
        },
        {
            title: 'Move section down',
            icon: 'arrow-downward',
            command: 'down',
            enabled: index < count - 1
        },
        { title: 'Close tab', icon: 'close', command: 'close' }
    ];
}

export function panel(height, radius) {
    return {
        width: metrics.railWidth,
        height,
        nodes: [
            node(
                'Box',
                'sectionRailBackground',
                rect(
                    0,
                    0,
                    metrics.railWidth,
                    Math.max(0, height - metrics.panelBottom)
                ),
                { background: 'toolBar', radius: 0, bottomRightRadius: radius }
            )
        ]
    };
}

export function closeBounds(width) {
    return rect(
        width - metrics.closeInset - metrics.closeExtent,
        (metrics.rowHeight - metrics.closeExtent) / 2,
        metrics.closeExtent,
        metrics.closeExtent
    );
}

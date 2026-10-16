import { node, rect } from '../../core/frame.mjs';

export function height(record, extent) {
    return record.separator
        ? 5
        : record.header
          ? 28
          : record.status
            ? 48
            : extent;
}

export function row(record, width, options) {
    const h = height(record, options.extent),
        nodes = [];
    if (record.separator)
        return {
            width,
            height: h,
            nodes: [
                node('Box', 'menuSeparator', rect(0, 2, width, 1), {
                    background: 'separator'
                })
            ]
        };
    const enabled = record.enabled !== false && !record.header;
    const foreground = enabled
        ? record.checked && record.accent
            ? record.accent
            : 'primaryText'
        : 'secondaryText';
    nodes.push(
        node('Box', 'menuRowSurface', rect(0, 0, width, h), {
            background:
                record.checked && record.accent ? record.accent : 'primaryText',
            opacity: record.header
                ? 0
                : record.checked && record.accent
                  ? 0.14
                  : !enabled
                    ? 0
                    : options.pressed
                      ? 0.12
                      : options.hovered
                        ? 0.08
                        : options.focused
                          ? 0.1
                          : 0,
            radius: options.radius
        })
    );
    let left = 10,
        right = width - 8;
    if (record.secondaryCommand) {
        right -= 15;
        nodes.push(
            node('Icon', 'menuSecondary', rect(right, (h - 15) / 2, 15, 15), {
                icon: record.secondaryIcon || 'update',
                color: 'secondaryText'
            })
        );
        right -= 9;
    }
    if (record.children || record.submenuPopup) {
        right -= 16;
        nodes.push(
            node('Icon', 'menuChildren', rect(right, (h - 16) / 2, 16, 16), {
                icon: 'chevron-right',
                color: 'secondaryText'
            })
        );
        right -= 9;
    }
    if (record.checked) {
        right -= 18;
        nodes.push(
            node('Icon', 'menuChecked', rect(right, (h - 18) / 2, 18, 18), {
                icon: 'check-circle',
                color: record.accent || 'action'
            })
        );
        right -= 9;
    }
    if (Number(record.badgeCount) > 0 || record.showZeroBadge) {
        const count = Number(record.badgeCount || 0),
            text = count > 99 ? '99+' : String(count),
            badge = Math.max(
                18,
                (options.badgeTextWidth === undefined
                    ? text.length * 7
                    : options.badgeTextWidth) + 8
            );
        right -= badge;
        nodes.push(
            node('Box', 'menuBadge', rect(right, (h - 18) / 2, badge, 18), {
                background:
                    record.badgeUpdated === false ? 'secondaryText' : 'error',
                radius: 9
            })
        );
        nodes.push(
            node(
                'Label',
                'menuBadgeText',
                rect(right, (h - 18) / 2, badge, 18),
                {
                    text,
                    fontRole: 'caption',
                    weight: 700,
                    align: 'center',
                    color: 'selectedText',
                    translate: false
                }
            )
        );
        right -= 9;
    }
    if (!record.header && record.accent && !record.accentIcon) {
        const extent = record.compactAccent ? 12 : 24;
        if (!record.compactAccent)
            nodes.push(
                node(
                    'Box',
                    'menuAccentSurface',
                    rect(left, (h - extent) / 2, extent, extent),
                    {
                        background: record.accent,
                        opacity: 0.16,
                        radius: extent / 2
                    }
                )
            );
        const dot = record.compactAccent ? 8 : 10;
        nodes.push(
            node(
                'Box',
                'menuAccent',
                rect(left + (extent - dot) / 2, (h - dot) / 2, dot, dot),
                { background: record.accent, radius: dot / 2 }
            )
        );
        left += extent + 9;
    }
    if (!record.header && (record.avatarUrl || record.initials)) {
        nodes.push(
            node('Preview', 'menuAvatar', rect(left, (h - 26) / 2, 26, 26), {
                source: record.avatarUrl || '',
                initials: record.initials || '',
                accent: record.avatarColor || record.accent || 'action',
                round: true
            })
        );
        left += 35;
    } else if (!record.header && record.icon) {
        nodes.push(
            node('Icon', 'menuIcon', rect(left, (h - 16) / 2, 16, 16), {
                icon: record.icon,
                color: record.accentIcon
                    ? record.accent || 'action'
                    : 'secondaryText'
            })
        );
        left += 25;
    }
    nodes.push(
        node(
            'Label',
            'menuTitle',
            rect(
                left,
                record.status ? 8 : 0,
                Math.max(0, right - left),
                record.status ? 16 : h
            ),
            {
                text: record.title || '',
                translate: false,
                color: foreground,
                fontRole: record.header ? 'menuHeading' : 'secondary',
                weight: record.header ? 600 : 400
            }
        )
    );
    if (record.status)
        nodes.push(
            node(
                'Label',
                'menuStatus',
                rect(left, 24, Math.max(0, right - left), 16),
                {
                    text: record.status,
                    translate: false,
                    color:
                        record.status === 'Experimental'
                            ? 'action'
                            : 'secondaryText',
                    fontRole: 'secondary'
                }
            )
        );
    return { width, height: h, nodes };
}

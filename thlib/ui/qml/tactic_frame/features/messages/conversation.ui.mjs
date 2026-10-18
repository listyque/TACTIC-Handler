import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export const metrics = {
    margin: 14,
    gap: 12,
    header: 26,
    row: 68,
    rowGap: 6,
    scrollbar: 14,
    minimum: 210,
    preferred: 252,
    maximum: 420
};
export const accents = ['action', 'green', 'cyan', 'violet', 'yellow'];
export function accent(model) {
    return accents[Math.max(0, Math.min(4, Number(model.colorIndex) || 0))];
}
export function layout(width, height) {
    const inner = Math.max(0, width - 2 * metrics.margin);
    return {
        inner,
        header: rect(14, 14, inner, 26),
        list: rect(14, 52, inner, Math.max(0, height - 66)),
        rowWidth: Math.max(0, inner - metrics.scrollbar)
    };
}
export function heading(width, busy, language) {
    const tr = (text) => translate(text, language);
    return {
        height: 26,
        nodes: [
            label(
                'conversationsTitle',
                rect(0, 4, Math.max(0, width - 34), 18),
                tr('CONVERSATIONS'),
                { fontRole: 'body', weight: 600, color: 'secondaryText' }
            ),
            button(
                'newConversation',
                rect(Math.max(0, width - 26), 0, 26, 26),
                '',
                'group-add',
                { type: 'create' },
                !busy,
                {
                    label: tr('New conversation'),
                    iconOnly: true,
                    iconAction: true,
                    iconSize: 16
                }
            )
        ]
    };
}
export function row(model, width, language) {
    const tr = (text, values) => translate(text, language, values),
        selected = !!model.selected,
        foreground = selected ? 'selectedText' : 'primaryText',
        muted = selected ? 'selectedText' : 'secondaryText',
        color = accent(model),
        unread = Math.max(0, Number(model.unread) || 0),
        mentions = Number(model.mentionCount) > 0,
        unreadText = unread > 99 ? '99+' : String(unread),
        unreadWidth = unread ? Math.max(18, unreadText.length * 6 + 8) : 0,
        trailing = unreadWidth + (mentions ? 26 : 0),
        textWidth = Math.max(0, width - 61 - trailing),
        title = model.isPersonalNotes ? tr('Favorites') : model.title || '',
        subtitle = model.isPersonalNotes
            ? tr('Your personal notes')
            : tr(
                  Number(model.participantCount) === 1
                      ? '{count} member'
                      : '{count} members',
                  { count: Number(model.participantCount) || 0 }
              ),
        summary =
            model.summary ||
            model.lastMessageSummary ||
            String(model.lastMessage || '')
                .replace(/\s+/g, ' ')
                .trim(),
        last = summary
            ? (model.lastSender ? model.lastSender + ': ' : '') +
              summary +
              (model.lastMessageLinkedCount
                  ? ' · ' +
                    model.lastMessageLinkedCount +
                    ' ' +
                    tr(model.lastMessageLinkedCount === 1 ? 'link' : 'links')
                  : '')
            : model.status || tr('No messages yet');
    const nodes = [
        node('Action', 'conversationSelect', rect(0, 0, width, 68), {
            text: title,
            selected,
            radius: 10,
            accent: color,
            rail: unread > 0,
            normalColor: 'surfaceContainerHigh',
            selectedColor: 'contentSelection',
            role: 'button',
            action: {
                type: 'select',
                key: model.conversationId,
                index: model.index
            },
            description: [
                unread ? tr('{count} unread messages', { count: unread }) : '',
                mentions
                    ? tr('{count} unread mentions', {
                          count: Number(model.mentionCount)
                      })
                    : ''
            ]
                .filter(Boolean)
                .join(' · '),
            children: [
                node('Preview', 'conversationAvatar', rect(9, 17, 34, 34), {
                    source: model.isPersonalNotes ? '' : model.avatarUrl || '',
                    initials: model.isPersonalNotes
                        ? ''
                        : model.acronym || model.initials || '',
                    icon: model.isPersonalNotes ? 'bookmark' : 'group',
                    round: true,
                    outlined: true,
                    accent: color,
                    selected
                }),
                label('conversationName', rect(51, 9, textWidth, 18), title, {
                    fontRole: 'body',
                    weight: 600,
                    color: foreground
                }),
                label(
                    'conversationMembers',
                    rect(51, 28, textWidth, 15),
                    subtitle,
                    { fontRole: 'caption', color: muted }
                ),
                label(
                    'conversationSummary',
                    rect(51, 44, textWidth, 15),
                    last,
                    { fontRole: 'caption', color: muted, opacity: 0.82 }
                )
            ]
        })
    ];
    const badge = (id, x, w, text, fill, ink) =>
        node('Box', id, rect(x, 25, w, 18), {
            background: fill,
            radius: 9,
            children: [
                label(id + 'Text', rect(0, 1, w, 16), text, {
                    fontRole: 'caption',
                    weight: 700,
                    color: ink,
                    align: 'center'
                })
            ]
        });
    if (mentions)
        nodes[0].children.push(
            badge(
                'conversationMentions',
                width - 9 - unreadWidth - (unread ? 8 : 0) - 18,
                18,
                '@',
                selected ? 'selectedText' : 'tertiary',
                selected ? 'tertiary' : 'selectedText'
            )
        );
    if (unread)
        nodes[0].children.push(
            badge(
                'conversationUnread',
                width - 9 - unreadWidth,
                unreadWidth,
                unreadText,
                selected ? 'selectedText' : 'action',
                selected ? 'action' : 'selectedText'
            )
        );
    return { height: 68, nodes };
}

export function header(model, width, language) {
    const tr = (text) => translate(text, language),
        nodes = [
            node('Box', 'chatHeaderSurface', rect(0, 0, width, 58), {
                background: 'surfaceContainerHigh',
                radius: 9
            })
        ],
        compact = !!model.compact;
    let left = 12;
    const icon = (id, x, name, title, type, extra = {}) =>
        nodes.push(
            button(
                id,
                rect(x, 16, 26, 26),
                '',
                name,
                { type },
                !model.busy,
                Object.assign(
                    {
                        label: tr(title),
                        iconOnly: true,
                        iconAction: true,
                        iconSize: 16
                    },
                    extra
                )
            )
        );
    if (compact) {
        icon('chatBack', left, 'arrow-back', 'Conversations', 'back');
        left += 34;
    }
    if (model.conversationId) {
        nodes.push(
            node('Preview', 'chatAvatar', rect(left, 12, 34, 34), {
                source: model.isPersonalNotes ? '' : model.avatarUrl || '',
                initials: model.isPersonalNotes ? '' : model.acronym || '',
                icon: model.isPersonalNotes ? 'bookmark' : 'group',
                round: true,
                outlined: true,
                accent: accent(model)
            })
        );
        left += 42;
    }
    let right = width - 10 - (model.busy ? 28 : 0);
    if (model.conversationId) {
        right -= 26;
        icon('chatActionsButton', right, 'more-vert', 'Chat actions', 'menu');
    }
    if (!compact) {
        right -= 34;
        icon(
            'chatRefresh',
            right,
            'refresh',
            'Refresh conversations and messages',
            'refresh'
        );
        if (model.conversationId) {
            right -= 34;
            icon('chatSearch', right, 'search', 'Search messages', 'search', {
                color: model.search ? 'action' : 'primaryText'
            });
            right -= 34;
            icon('chatFiles', right, 'attach-file', 'Chat files', 'files', {
                badgeCount: model.attachmentCount || 0
            });
            if (!model.isPersonalNotes) {
                right -= 34;
                icon('chatMembers', right, 'group', 'Chat members', 'members', {
                    badgeCount: model.participantCount || 0
                });
            }
        }
    }
    const textWidth = Math.max(0, right - left - 8),
        title = model.isPersonalNotes
            ? tr('Favorites')
            : model.title || tr('Select a conversation');
    nodes.push(
        label('chatTitle', rect(left, 14, textWidth, 16), title, {
            fontRole: 'secondary',
            weight: 600
        })
    );
    let subtitleX = left,
        subtitleWidth = textWidth;
    if (model.presence) {
        const presenceWidth = Math.min(
            Math.max(0, textWidth - 17),
            Math.max(0, model.presenceWidth || 0)
        );
        nodes.push(
            node('Box', 'chatPresenceDot', rect(left, 36, 7, 7), {
                background: model.online ? 'green' : 'disabledText',
                radius: 3.5
            })
        );
        nodes.push(
            label(
                'chatPresence',
                rect(left + 12, 32, presenceWidth, 15),
                model.presence,
                {
                    fontRole: 'caption',
                    color: model.online ? 'green' : 'secondaryText',
                    toolTip: model.presence
                }
            )
        );
        subtitleX += presenceWidth + 17;
        subtitleWidth = Math.max(0, textWidth - presenceWidth - 17);
    }
    nodes.push(
        label(
            'chatSubtitle',
            rect(subtitleX, 32, subtitleWidth, 15),
            model.subtitle || '',
            {
                fontRole: 'caption',
                color: 'secondaryText'
            }
        )
    );
    return { height: 58, nodes };
}

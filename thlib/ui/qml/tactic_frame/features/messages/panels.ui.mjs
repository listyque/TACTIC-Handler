import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export function heading(mode, width, count, language) {
    const tr = (text, values) => translate(text, language, values),
        title =
            {
                history: 'EDIT HISTORY',
                'pin-history': 'PIN HISTORY',
                'view-members': 'CHAT MEMBERS',
                files: 'CHAT FILES'
            }[mode] || 'Messages',
        right = mode === 'files' ? 100 : 0;
    const nodes = [
        label(
            'messagePanelTitle',
            rect(0, 0, Math.max(0, width - right), 18),
            tr(title),
            { fontRole: 'body', weight: 600, color: 'secondaryText' }
        )
    ];
    if (right)
        nodes.push(
            label(
                'messagePanelCount',
                rect(Math.max(0, width - right), 1, right, 16),
                tr('{count} loaded', { count: count || 0 }),
                {
                    fontRole: 'secondary',
                    align: 'right',
                    color: 'secondaryText'
                }
            )
        );
    return { height: 18, nodes };
}
export function revision(model, width, bodyHeight, language) {
    const tr = (text, values) => translate(text, language, values),
        pin = model.mode === 'pin-history',
        height = 16 + 15 + 4 + Math.max(18, bodyHeight || 18),
        caption =
            tr(pin ? 'Pinned by {user}' : 'Edited by {user}', {
                user: (pin ? model.pinnedBy : model.editedBy) || tr('unknown')
            }) +
            '  ·  ' +
            (pin ? model.pinnedAt : model.editedAt || ''),
        nodes = [
            node('Box', 'messageRevisionSurface', rect(0, 0, width, height), {
                background: pin ? 'row' : 'surfaceContainer',
                radius: 10
            }),
            label(
                'messageRevisionCaption',
                rect(8, 8, Math.max(0, width - 16), 15),
                caption,
                { fontRole: 'caption', color: 'secondaryText' }
            ),
            node(
                'View',
                'messageRevisionBodyPort',
                rect(
                    8,
                    27,
                    Math.max(0, width - 16),
                    Math.max(18, bodyHeight || 18)
                ),
                { view: 'body' }
            )
        ];
    if (pin)
        nodes.push(
            node('Action', 'messageRevisionOpen', rect(0, 0, width, height), {
                text: model.summary || model.body || tr('Pinned message'),
                radius: 10,
                enabled: !!model.messageId && !model.busy,
                action: { type: 'open', value: model.messageId }
            })
        );
    return { height, nodes };
}
export function forward(model, width, language) {
    const tr = (text, values) => translate(text, language, values),
        title = model.isPersonalNotes ? tr('Favorites') : model.title || '',
        nodes = [
            node(
                'Box',
                'forwardTargetSurface',
                rect(1, 1, Math.max(0, width - 2), 52),
                {
                    background: model.selected ? 'contentSelection' : 'row',
                    radius: 12
                }
            ),
            node('CheckBox', 'forwardTargetCheck', rect(8, 8, 30, 38), {
                text: title,
                checked: !!model.selected,
                enabled: !model.busy,
                action: { type: 'toggle', key: model.conversationId }
            }),
            node(
                'Action',
                'forwardTargetLabel',
                rect(42, 0, Math.max(0, width - 42), 54),
                {
                    text: title,
                    enabled: !model.busy,
                    radius: 12,
                    action: { type: 'toggle', key: model.conversationId },
                    children: [
                        label(
                            'forwardTargetTitle',
                            rect(4, 9, Math.max(0, width - 58), 18),
                            title,
                            {
                                fontRole: 'body',
                                weight: 600,
                                color: model.selected
                                    ? 'selectedText'
                                    : 'primaryText'
                            }
                        ),
                        label(
                            'forwardTargetMembers',
                            rect(4, 29, Math.max(0, width - 58), 15),
                            model.isPersonalNotes
                                ? tr('Your personal notes')
                                : tr(
                                      model.participantCount === 1
                                          ? '{count} member'
                                          : '{count} members',
                                      { count: model.participantCount || 0 }
                                  ),
                            {
                                fontRole: 'caption',
                                color: model.selected
                                    ? 'selectedText'
                                    : 'secondaryText'
                            }
                        )
                    ]
                }
            )
        ];
    return { height: 54, nodes };
}
export function forwarding(model, width, height, language) {
    const tr = (text, values) => translate(text, language, values),
        footer = Math.max(100, height - 38),
        submitWidth = 120,
        cancelWidth = language === 'ru' ? 100 : 90;
    return {
        nodes: [
            label(
                'forwardInstructions',
                rect(0, 0, width, 36),
                tr('Choose one or more destination chats'),
                { fontRole: 'body', wrap: true }
            ),
            node(
                'List',
                'forwardConversations',
                rect(0, 44, width, Math.max(0, footer - 56)),
                {
                    source: 'conversations',
                    keyField: 'conversationId',
                    fields: [
                        'conversationId',
                        'title',
                        'participantCount',
                        'isPersonalNotes'
                    ],
                    rowHeight: 58,
                    rowGap: 4,
                    label: tr('Destination chats')
                }
            ),
            label(
                'forwardSelectedCount',
                rect(
                    0,
                    footer + 10,
                    Math.max(0, width - submitWidth - cancelWidth - 16),
                    18
                ),
                tr(
                    model.count === 1
                        ? '{count} message selected'
                        : '{count} messages selected',
                    { count: model.count || 0 }
                ),
                { fontRole: 'secondary', color: 'secondaryText' }
            ),
            button(
                'forwardCancel',
                rect(
                    Math.max(0, width - submitWidth - cancelWidth - 8),
                    footer,
                    cancelWidth,
                    38
                ),
                tr('Cancel'),
                '',
                { type: 'cancel' },
                !model.busy
            ),
            button(
                'forwardSubmit',
                rect(Math.max(0, width - submitWidth), footer, submitWidth, 38),
                tr('Forward'),
                '',
                { type: 'submit' },
                !model.busy && !!model.valid,
                { highlighted: true }
            )
        ]
    };
}
export function mention(model, width) {
    return {
        height: 46,
        nodes: [
            node(
                'Action',
                'mentionOption_' + model.login,
                rect(0, 0, width, 46),
                {
                    text: model.displayName || model.login,
                    role: 'option',
                    elementId: model.elementId,
                    selected: !!model.selected,
                    radius: 10,
                    normalColor: 'row',
                    selectedColor: 'contentSelection',
                    action: { type: 'mention', login: model.login },
                    children: [
                        node(
                            'Preview',
                            'mentionAvatar_' + model.login,
                            rect(8, 8, 30, 30),
                            {
                                source: model.avatarUrl || '',
                                initials: model.initials || '',
                                icon: 'person',
                                round: true,
                                accent: model.avatarColor || 'action'
                            }
                        ),
                        label(
                            'mentionName_' + model.login,
                            rect(46, 7, Math.max(0, width - 54), 18),
                            model.displayName || model.login,
                            {
                                fontRole: 'body',
                                color: model.selected
                                    ? 'selectedText'
                                    : 'primaryText'
                            }
                        ),
                        label(
                            'mentionLogin_' + model.login,
                            rect(46, 25, Math.max(0, width - 54), 15),
                            '@' + model.login,
                            {
                                fontRole: 'caption',
                                color: model.selected
                                    ? 'selectedText'
                                    : 'secondaryText'
                            }
                        )
                    ]
                }
            )
        ]
    };
}
export function gallery(model, width, language) {
    const tr = (text) => translate(text, language),
        reserve = model.actions ? 28 : 0,
        title = model.title || tr('File'),
        nodes = [
            node(
                'Action',
                'chatFileEntry',
                rect(0, 0, Math.max(0, width - reserve), 60),
                {
                    text: title,
                    radius: 12,
                    normalColor: 'row',
                    action: { type: 'jump', value: model.messageId },
                    children: [
                        node('Icon', 'chatFileIcon', rect(12, 21, 18, 18), {
                            icon: model.preview ? 'image' : 'description',
                            color: 'action'
                        }),
                        label(
                            'chatFileName',
                            rect(40, 12, Math.max(0, width - 52 - reserve), 18),
                            title,
                            { fontRole: 'body', weight: 600 }
                        ),
                        label(
                            'chatFileSender',
                            rect(40, 32, Math.max(0, width - 52 - reserve), 15),
                            (model.sender || tr('Unknown')) +
                                (model.time ? '  ·  ' + model.time : ''),
                            { fontRole: 'caption', color: 'secondaryText' }
                        )
                    ]
                }
            )
        ];
    if (model.actions)
        nodes.push(
            button(
                'chatFileActions',
                rect(Math.max(0, width - 28), 17, 26, 26),
                '',
                'more-vert',
                { type: 'menu' },
                !model.busy,
                {
                    label: tr('Attachment actions'),
                    iconOnly: true,
                    iconAction: true,
                    iconSize: 16
                }
            )
        );
    return { height: 60, nodes };
}

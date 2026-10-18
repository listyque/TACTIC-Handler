import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { bodyOrder } from './messaging.state.mjs';

export const metrics = {
    header: 18,
    gap: 6,
    action: 28,
    minimumCellWidth: 210,
    preferredCellWidth: 240,
    maximumColumns: 2
};
export function header(model, width, language) {
    const tr = (text, values) => translate(text, language, values),
        nodes = [],
        available = !!(model.hovered || model.focused || model.touch),
        actionCount =
            2 + (model.selectionMode ? 1 : 0) + (model.pinned ? 1 : 0),
        actionWidth = actionCount * 28;
    const action = (id, index, title, icon, type, extra = {}) =>
        nodes.push(
            button(
                id,
                rect(
                    width - (index + 1) * 28,
                    2 - (model.padding || 13),
                    28,
                    28
                ),
                '',
                icon,
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
    action('messageActionsButton', 0, 'Message actions', 'more-vert', 'menu', {
        opacity: available ? 1 : 0
    });
    action('messageAddReaction', 1, 'Add reaction', 'emoji', 'reaction', {
        opacity: available && model.canReact !== false && !model.touch ? 1 : 0,
        enabled: !model.busy && model.canReact !== false && !model.touch
    });
    let index = 2;
    if (model.pinned)
        action('messageUnpin', index++, 'Unpin message', 'push-pin', 'pin', {
            color: 'tertiary',
            enabled: !model.busy && model.canPin !== false
        });
    if (model.selectionMode)
        action(
            'messageSelect',
            index++,
            model.selected ? 'Deselect message' : 'Select message',
            model.selected ? 'check-circle' : 'check-box-outline-blank',
            'select',
            { color: model.selected ? 'tertiary' : 'secondaryText' }
        );
    const editedWidth = model.edited ? (width < 150 ? 16 : 40) : 0,
        deliveryWidth = model.own && model.recipientCount ? 17 : 0,
        timeWidth = Math.min(
            92,
            Math.max(42, String(model.time || '').length * 5.5),
            Math.max(0, width - actionWidth - editedWidth - deliveryWidth - 10)
        ),
        titleWidth = Math.max(
            0,
            width - actionWidth - editedWidth - timeWidth - deliveryWidth - 10
        ),
        sender =
            (model.senderDisplay || model.sender || '') +
            (model.sender &&
            model.senderDisplay &&
            model.senderDisplay !== model.sender
                ? ' (' + model.sender + ')'
                : '');
    if (model.first !== false)
        nodes.push(
            node('Action', 'messageSender', rect(0, 0, titleWidth, 18), {
                text: tr('Open profile for {name}', {
                    name: model.sender || ''
                }),
                radius: 0,
                enabled: !!model.sender,
                action: { type: 'profile' },
                children: [
                    label(
                        'messageSenderLabel',
                        rect(0, 0, titleWidth, 16),
                        sender,
                        {
                            fontRole: 'secondary',
                            weight: 600,
                            color: model.senderColor || 'action'
                        }
                    )
                ]
            })
        );
    let x = titleWidth + 5;
    if (deliveryWidth) {
        nodes.push(
            node('Icon', 'messageDelivery', rect(x, 1, 14, 14), {
                focusable: true,
                icon: model.deliveryStatus === 'sent' ? 'check' : 'done-all',
                color:
                    model.deliveryStatus === 'read'
                        ? 'action'
                        : 'secondaryText',
                text: tr(
                    model.deliveryStatus === 'read'
                        ? 'Read by {count} of {total}'
                        : model.deliveryStatus === 'delivered'
                          ? 'Delivered to {count} of {total}'
                          : 'Sent',
                    {
                        count:
                            model.deliveryStatus === 'read'
                                ? model.readCount
                                : model.deliveredCount,
                        total: model.recipientCount
                    }
                )
            })
        );
        x += deliveryWidth;
    }
    nodes.push(
        label('messageTimeLabel', rect(x, 0, timeWidth, 16), model.time || '', {
            fontRole: 'caption',
            color: 'secondaryText',
            align: 'right',
            toolTip: model.fullTime || '',
            focusable: true
        })
    );
    x += timeWidth + 5;
    if (model.edited)
        nodes.push(
            node('Action', 'messageEdited', rect(x, 0, editedWidth, 18), {
                text: tr('Edited'),
                toolTip: model.editedBy
                    ? tr('Last edited by {name} · {time}', {
                          name: model.editedBy,
                          time: model.editedAt || ''
                      })
                    : tr('Edited'),
                radius: 0,
                action: { type: 'history' },
                children:
                    editedWidth === 16
                        ? [
                              node(
                                  'Icon',
                                  'messageEditedIcon',
                                  rect(0, 0, 14, 14),
                                  { icon: 'edit', color: 'secondaryText' }
                              )
                          ]
                        : [
                              label(
                                  'messageEditedText',
                                  rect(0, 0, editedWidth, 16),
                                  tr('Edited'),
                                  {
                                      fontRole: 'caption',
                                      color: 'secondaryText'
                                  }
                              )
                          ]
            })
        );
    const naturalWidth =
        actionWidth +
        (model.edited ? 40 : 0) +
        Math.min(92, Math.max(42, String(model.time || '').length * 5.5)) +
        (model.own && model.recipientCount ? 17 : 0) +
        Math.max(42, sender.length * 6) +
        10;
    return { height: 18, naturalWidth, nodes };
}
export function body(model, width, heights = {}) {
    let top = 0;
    const nodes = [];
    for (const part of bodyOrder) {
        if (!model[part]) continue;
        if (nodes.length) top += metrics.gap;
        const height = Math.max(1, heights[part] || 1);
        nodes.push(
            node('View', 'messageBody_' + part, rect(0, top, width, height), {
                view: part
            })
        );
        top += height;
    }
    return { height: top, nodes };
}
export function reference(model, width, language, bodyHeight = 19) {
    const tr = (text, values) => translate(text, language, values),
        right = model.dismissible ? 33 : 0,
        textWidth = Math.max(0, width - 45 - right),
        color = model.available
            ? model.forwarded
                ? 'tertiary'
                : 'action'
            : 'error',
        body = model.available && !!model.body,
        attachments =
            model.available && model.forwarded && model.attachments > 0,
        measured = body
            ? Math.min(model.forwarded ? 57 : 38, Math.max(19, bodyHeight))
            : 0,
        height = Math.max(
            model.forwarded ? 62 : 54,
            14 + 18 + (body ? 2 + measured : 0) + (attachments ? 19 : 0)
        ),
        title = !model.available
            ? tr(
                  model.forwarded
                      ? 'Forwarded message unavailable'
                      : 'Original message is unavailable'
              )
            : tr(
                  model.forwarded ? 'Forwarded from {name}' : 'Reply to {name}',
                  { name: model.sender || tr('Unknown user') }
              ),
        nodes = [
            node('Box', 'messageReferenceSurface', rect(0, 0, width, height), {
                background: 'surfaceContainerHighest',
                radius: 10,
                border: 'outlineVariant',
                borderWidth: 1
            }),
            node('Box', 'messageReferenceRail', rect(0, 0, 4, height), {
                background: color,
                radius: 2
            }),
            node('Icon', 'messageReferenceIcon', rect(12, 7, 18, 18), {
                icon: model.forwarded ? 'share' : 'reply',
                color
            }),
            label('messageReferenceTitle', rect(38, 7, textWidth, 18), title, {
                fontRole: 'body',
                weight: 600,
                color
            })
        ];
    if (body)
        nodes.push(
            node(
                'View',
                'messageReferenceBodyPort',
                rect(38, 27, textWidth, measured),
                { view: 'body' }
            )
        );
    if (attachments)
        nodes.push(
            label(
                'messageReferenceAttachments',
                rect(38, 27 + (body ? measured + 3 : 0), textWidth, 16),
                tr('{count} attachments', { count: model.attachments }),
                { fontRole: 'secondary', color: 'secondaryText' }
            )
        );
    if (model.available && !model.dismissible)
        nodes.push(
            node('Action', 'messageReferenceOpen', rect(0, 0, width, height), {
                text: title,
                radius: 10,
                action: { type: 'open' }
            })
        );
    if (model.dismissible)
        nodes.push(
            button(
                'messageReplyCancel',
                rect(Math.max(0, width - 33), (height - 26) / 2, 26, 26),
                '',
                'close',
                { type: 'dismiss' },
                true,
                {
                    label: tr('Cancel reply'),
                    iconOnly: true,
                    iconAction: true,
                    iconSize: 16
                }
            )
        );
    return { height, nodes };
}
export function pinned(model, width, language) {
    const tr = (text, values) => translate(text, language, values),
        nodes = [
            node('Box', 'pinnedMessageSurface', rect(0, 0, width, 48), {
                background: 'surfaceContainerHigh',
                radius: 12,
                border: 'outlineVariant',
                borderWidth: 1
            }),
            node('Box', 'pinnedMessageIconSurface', rect(12, 10, 28, 28), {
                background: 'tertiaryContainer',
                radius: 9
            }),
            node('Icon', 'pinnedMessageIcon', rect(18, 16, 16, 16), {
                icon: 'push-pin',
                color: 'tertiary'
            })
        ];
    let right = width - 36;
    const badge = (id, icon, count) => {
        if (!count) return;
        right -= 40;
        nodes.push(
            node('Icon', id + 'Icon', rect(right, 17, 15, 15), {
                icon,
                color: 'tertiary'
            })
        );
        nodes.push(
            label(id + 'Count', rect(right + 18, 17, 22, 16), String(count), {
                fontRole: 'secondary',
                color: 'secondaryText'
            })
        );
    };
    badge(
        'pinnedMessageLinks',
        model.linkedMessageCount === model.linkedCount ? 'chat' : 'link',
        model.linkedCount || 0
    );
    badge('pinnedMessageFiles', 'attach-file', model.attachmentCount || 0);
    for (const pair of [
        ['reply', model.hasReply],
        ['share', model.forwarded]
    ])
        if (pair[1]) {
            right -= 23;
            nodes.push(
                node(
                    'Icon',
                    'pinnedMessage' + pair[0],
                    rect(right, 17, 15, 15),
                    { icon: pair[0], color: 'secondaryText' }
                )
            );
        }
    const w = Math.max(0, right - 53);
    nodes.push(
        label(
            'pinnedMessageTitle',
            rect(49, 6, w, 18),
            model.summary || model.body || tr('Pinned message'),
            { fontRole: 'body', weight: 600 }
        )
    );
    nodes.push(
        label(
            'pinnedMessageSubtitle',
            rect(49, 26, w, 15),
            (model.senderDisplay ? model.senderDisplay + '  ·  ' : '') +
                tr('Pinned by {user}', {
                    user: model.pinnedBy || tr('unknown')
                }),
            { fontRole: 'caption', color: 'secondaryText' }
        )
    );
    nodes.push(
        node(
            'Action',
            'pinnedMessageOpen',
            rect(0, 0, Math.max(0, width - 36), 48),
            {
                text: tr('Pinned message'),
                description: model.summary || model.body || '',
                radius: 12,
                action: { type: 'open' }
            }
        )
    );
    nodes.push(
        button(
            'pinHistoryButton',
            rect(Math.max(0, width - 34), 11, 26, 26),
            '',
            'history',
            { type: 'history' },
            !model.busy,
            {
                label: tr('Pin history'),
                iconOnly: true,
                iconAction: true,
                iconSize: 16
            }
        )
    );
    return { height: 48, nodes };
}

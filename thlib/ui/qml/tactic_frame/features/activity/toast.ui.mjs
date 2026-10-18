import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { accent, icon } from './notifications.ui.mjs';

export const metrics = {
    width: 390,
    gap: 8,
    radius: 14,
    shadowX: 2,
    shadowY: 5,
    shadowBlur: 12
};
export function describe(model, width, heights = {}, language, phone = false) {
    const tr = (text) => translate(text, language),
        nodes = [],
        padding = phone ? 8 : 12,
        avatar = phone ? 24 : 46,
        gap = phone ? 8 : 10,
        dismiss = model.dismissible !== false ? 26 : 0,
        left = padding + avatar + gap,
        textWidth = Math.max(
            0,
            width - left - padding - (dismiss ? dismiss + gap : 0)
        ),
        source =
            model.sourceType === 'message'
                ? tr('Message')
                : model.sourceType === 'activity'
                  ? tr('Activity Feed')
                  : '',
        sourceText =
            source +
            (source && model.sourceTitle ? ' · ' : '') +
            (model.sourceTitle || ''),
        messageHeight = Math.max(phone ? 16 : 18, heights.message || 18),
        detailHeight = model.detail
            ? Math.min(30, Math.max(15, heights.detail || 15))
            : 0;
    let y = padding;
    const sourceHeight = sourceText ? 18 : 0,
        contentHeight =
            sourceHeight +
            messageHeight +
            (detailHeight ? 3 + detailHeight : 0) +
            (model.kind === 'progress' ? 15 : 0),
        mainHeight = Math.max(avatar, contentHeight);
    if (model.action)
        nodes.push(
            node(
                'Action',
                'notificationActivation',
                rect(0, 0, width, mainHeight + padding * 2),
                {
                    text: tr(
                        model.sourceType === 'message'
                            ? 'Open Messages'
                            : 'Open Activity Feed'
                    ),
                    radius: 14,
                    action: { type: 'activate' }
                }
            )
        );
    nodes.push(
        node(
            'Preview',
            'notificationAvatar',
            rect(padding, padding + (mainHeight - avatar) / 2, avatar, avatar),
            {
                source: model.previewUrl || '',
                initials: String(model.avatarText || '')
                    .slice(0, 2)
                    .toUpperCase(),
                icon: model.sourceIcon || icon(model.kind),
                accent: model.avatarColor || accent(model.kind),
                round:
                    model.sourceType === 'message' ||
                    model.sourceType === 'activity',
                outlined: true,
                pointerTransparent: true
            }
        )
    );
    if (sourceText)
        nodes.push(
            label(
                'notificationSource',
                rect(left, y, textWidth, 15),
                sourceText,
                {
                    fontRole: 'caption',
                    weight: 600,
                    color: 'action',
                    pointerTransparent: true
                }
            )
        );
    y += sourceHeight;
    nodes.push(
        node(
            'View',
            'notificationMessagePort',
            rect(left, y, textWidth, messageHeight),
            {
                view: 'message',
                pointerTransparent: !(
                    phone && ['error', 'warning'].includes(model.kind)
                )
            }
        )
    );
    y += messageHeight;
    if (detailHeight) {
        y += 3;
        nodes.push(
            node(
                'View',
                'notificationDetailPort',
                rect(left, y, textWidth, detailHeight),
                { view: 'detail', pointerTransparent: true }
            )
        );
        y += detailHeight;
    }
    if (model.kind === 'progress') {
        y += 3;
        nodes.push(
            node(
                'View',
                'notificationProgressPort',
                rect(left, y, textWidth, 12),
                { view: 'progress' }
            )
        );
        y += 12;
    }
    y = padding + mainHeight;
    if (dismiss)
        nodes.push(
            button(
                'notificationDismiss',
                rect(
                    width - padding - dismiss,
                    padding + (mainHeight - dismiss) / 2,
                    dismiss,
                    dismiss
                ),
                '',
                'close',
                { type: 'dismiss' },
                true,
                {
                    label: tr('Dismiss notification'),
                    iconOnly: true,
                    iconAction: true,
                    iconSize: 17
                }
            )
        );
    if (
        model.sourceType === 'message' &&
        model.actionData &&
        !model.replyOpen
    ) {
        y += 10;
        nodes.push(
            button(
                'notificationReplyButton',
                rect(Math.max(padding, width - padding - 92), y, 92, 38),
                tr('Reply'),
                '',
                { type: 'reply' },
                model.canReply !== false
            )
        );
        y += 38;
    }
    if (model.replyOpen) {
        y += 10;
        const fieldWidth = Math.max(0, width - padding * 2 - 72 - 26 - 12);
        nodes.push(
            node(
                'Field',
                'notificationReplyField',
                rect(padding, y, fieldWidth, 38),
                {
                    label: tr('Write a reply'),
                    placeholder: tr('Write a reply'),
                    text: model.replyText || '',
                    enabled: !model.replySending,
                    action: { type: 'text' },
                    keys: phone
                        ? { Escape: { type: 'cancel' } }
                        : {
                              Enter: { type: 'send' },
                              Escape: { type: 'cancel' }
                          }
                }
            )
        );
        nodes.push(
            button(
                'notificationSendReplyButton',
                rect(padding + fieldWidth + 6, y, 72, 38),
                tr('Send'),
                '',
                { type: 'send' },
                !model.replySending && !!String(model.replyText || '').trim()
            )
        );
        nodes.push(
            button(
                'notificationCancelReply',
                rect(width - padding - 26, y + 6, 26, 26),
                '',
                'close',
                { type: 'cancel' },
                !model.replySending,
                {
                    label: tr('Cancel reply'),
                    iconOnly: true,
                    iconAction: true,
                    iconSize: 17
                }
            )
        );
        y += 38;
    }
    if (model.replyError) {
        y += 10;
        const errorHeight = Math.max(15, heights.error || 15);
        nodes.push(
            node(
                'View',
                'notificationReplyErrorPort',
                rect(padding, y, Math.max(0, width - padding * 2), errorHeight),
                { view: 'error' }
            )
        );
        y += errorHeight;
    }
    return {
        height: y + padding,
        radius: phone ? 9 : 14,
        background: 'panelRaised',
        border: 'outline',
        nodes
    };
}

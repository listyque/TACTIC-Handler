import { node, rect, label } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
export const metrics = {
    row: 54,
    member: 58,
    avatar: 36,
    header: 38,
    gap: 8,
    scrollbar: 16
};
export function row(model, width, language) {
    const tr = (text) => translate(text, language),
        picker = !!model.picker,
        blocked = model.selectable === false,
        selected = !!model.selected,
        height = picker ? 54 : 58,
        trailing = picker ? (model.currentUnavailable ? 108 : 26) : 0,
        textWidth = Math.max(0, width - 60 - trailing),
        ink = selected
            ? 'selectedText'
            : blocked
              ? 'disabledText'
              : 'primaryText',
        muted = selected
            ? 'selectedText'
            : blocked
              ? 'disabledText'
              : 'secondaryText',
        subtitle = picker
            ? model.login +
              ((model.groups || []).length
                  ? '  ·  ' + model.groups.join(', ')
                  : '')
            : model.current
              ? tr('You')
              : model.login,
        children = [
            node(
                'Preview',
                'userPickerAvatar_' + model.login,
                rect(
                    picker ? 8 : 10,
                    (height - (picker ? 36 : 34)) / 2,
                    picker ? 36 : 34,
                    picker ? 36 : 34
                ),
                {
                    source: model.avatarUrl || '',
                    initials: model.initials || '?',
                    icon: 'person',
                    round: true,
                    outlined: true,
                    accent: model.avatarColor || 'action',
                    selected,
                    opacity: blocked ? 0.58 : 1
                }
            ),
            label(
                'userPickerName_' + model.login,
                rect(52, height / 2 - 17, textWidth, 18),
                model.displayName || model.login,
                { fontRole: 'body', weight: 600, color: ink }
            ),
            label(
                'userPickerSubtitle_' + model.login,
                rect(52, height / 2 + 2, textWidth, 15),
                subtitle,
                { fontRole: 'caption', color: muted }
            )
        ];
    if (picker && selected)
        children.push(
            node(
                'Icon',
                'userPickerChosen_' + model.login,
                rect(Math.max(0, width - 29), (height - 19) / 2, 19, 19),
                { icon: 'check-circle', color: 'selectedText' }
            )
        );
    if (picker && model.currentUnavailable) {
        children.push(
            node(
                'Icon',
                'userPickerCurrentLock_' + model.login,
                rect(Math.max(0, width - 108), (height - 14) / 2, 14, 14),
                { icon: 'lock', color: 'disabledText' }
            )
        );
        children.push(
            label(
                'userPickerCurrentMarker',
                rect(Math.max(0, width - 90), (height - 16) / 2, 82, 16),
                tr('Current user'),
                { fontRole: 'caption', color: 'disabledText' }
            )
        );
    }
    return {
        height,
        nodes: [
            node(
                'Action',
                (picker ? 'userPickerAction_' : 'chatMember_') + model.login,
                rect(0, 0, width, height),
                {
                    text: model.displayName || model.login,
                    role: picker ? 'checkbox' : 'button',
                    checked: selected,
                    selected,
                    normalColor: 'row',
                    selectedColor: 'contentSelection',
                    radius: 12,
                    enabled: !blocked,
                    action: {
                        type: picker ? 'select' : 'profile',
                        login: model.login
                    },
                    children
                }
            )
        ]
    };
}

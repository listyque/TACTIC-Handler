import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
export const titles = {
    create: 'New conversation',
    members: 'Add or remove members',
    rename: 'Rename chat',
    search: 'Search messages',
    edit: 'Edit message',
    clear: 'Clear favorites?',
    delete: 'Delete chat?',
    'delete-message': 'Delete this message?'
};
export function description(mode, language) {
    return translate(
        {
            clear: 'All messages in Favorites will be cleared. Favorites itself will remain.',
            delete: 'The chat will be archived for every participant. Message history and attachments remain available for audit.',
            'delete-message': 'Delete this message?'
        }[mode] || '',
        language
    );
}
export function form(model, width, height, language, measured = {}) {
    const tr = (text, values) => translate(text, language, values),
        mode = model.mode,
        people = mode === 'create' || mode === 'members',
        nodes = [],
        group = mode === 'create' && model.count > 1,
        warning = group && !model.canCreateGroup,
        buttons = {
            create: 'Create',
            members: 'Save members',
            rename: 'Rename',
            edit: 'Save',
            clear: 'Clear messages',
            delete: 'Delete chat',
            'delete-message': 'Delete'
        },
        heading = people || mode === 'rename' || mode === 'search';
    let y = 0;
    if (heading) {
        if (people)
            nodes.push(
                node('Icon', 'messageFormHeadingIcon', rect(0, 4, 22, 22), {
                    icon: mode === 'create' ? 'group-add' : 'manage-accounts',
                    color: 'action'
                })
            );
        nodes.push(
            label(
                'messageFormTitle',
                rect(
                    people ? 32 : 0,
                    0,
                    Math.max(0, width - (people ? 32 : 0)),
                    20
                ),
                tr(titles[mode]),
                {
                    fontRole: people ? 'bodyLarge' : 'body',
                    weight: 600,
                    color: people ? 'primaryText' : 'secondaryText'
                }
            )
        );
        if (people)
            nodes.push(
                label(
                    'messageFormSubtitle',
                    rect(32, 22, Math.max(0, width - 32), 32),
                    tr(
                        mode === 'create'
                            ? 'Find people and start a direct or group chat'
                            : 'Select everyone who should remain in this chat'
                    ),
                    {
                        fontRole: 'secondary',
                        color: 'secondaryText',
                        wrap: true
                    }
                )
            );
        y = people ? 66 : 32;
    }
    if (mode === 'search') {
        nodes.push(
            node(
                'Field',
                'messageSearchField',
                rect(0, y, Math.max(0, width - 66), 38),
                {
                    label: tr('Search messages'),
                    placeholder: tr('Type a message or phrase'),
                    text: model.text || '',
                    action: { type: 'text' },
                    keys: { Enter: { type: 'submit' } }
                }
            )
        );
        nodes.push(
            button(
                'messageSearchClear',
                rect(Math.max(0, width - 59), y + 6, 26, 26),
                '',
                'close',
                { type: 'clear-search' },
                !!model.activeSearch,
                { label: tr('Clear search'), iconOnly: true, iconAction: true }
            )
        );
        nodes.push(
            button(
                'messageSearchApply',
                rect(Math.max(0, width - 26), y + 6, 26, 26),
                '',
                'search',
                { type: 'submit' },
                !model.busy,
                { label: tr('Search'), iconOnly: true, iconAction: true }
            )
        );
        return { height: y + 38, nodes };
    }
    if (people) {
        const footer = 38,
            extra = (group ? 50 : 0) + (warning ? 48 : 0),
            peopleHeight = Math.max(100, height - y - footer - 12 - extra);
        nodes.push(
            node('View', 'messageFormPeople', rect(0, y, width, peopleHeight), {
                view: 'people'
            })
        );
        y += peopleHeight + 12;
        if (group) {
            nodes.push(
                node('Field', 'messageGroupTitle', rect(0, y, width, 38), {
                    label: tr('Group chat title'),
                    placeholder: tr('Group chat title'),
                    text: model.text || '',
                    enabled: !model.busy,
                    action: { type: 'text' },
                    keys: { Enter: { type: 'submit' } }
                })
            );
            y += 50;
        }
        if (warning) {
            nodes.push(
                label(
                    'messageFormGroupWarning',
                    rect(0, y, width, 36),
                    tr(
                        'Group chats can be created by administrators and supervisors'
                    ),
                    { fontRole: 'secondary', color: 'yellow', wrap: true }
                )
            );
            y += 48;
        }
    } else if (mode === 'rename') {
        nodes.push(
            node('Field', 'messageChatTitle', rect(0, y, width, 38), {
                label: tr('Chat title'),
                placeholder: tr('Chat title'),
                text: model.text || '',
                enabled: !model.busy,
                action: { type: 'text' },
                keys: { Enter: { type: 'submit' } }
            })
        );
        y += 50;
    } else if (mode === 'edit') {
        nodes.push(
            node('Area', 'messageEditBody', rect(0, y, width, 130), {
                label: tr('Message text'),
                placeholder: tr('Message'),
                text: model.text || '',
                enabled: !model.busy,
                action: { type: 'text' }
            })
        );
        y += 142;
    } else {
        const contentHeight = Math.max(18, measured.description || 72);
        nodes.push(
            node(
                'View',
                'messageFormDescription',
                rect(0, y, width, contentHeight),
                { view: 'description' }
            )
        );
        y += contentHeight + 12;
    }
    const submit = tr(buttons[mode] || 'Save'),
        submitWidth = Math.min(
            Math.max(92, submit.length * 7 + 28),
            width * 0.55
        ),
        cancelWidth = language === 'ru' ? 100 : 90,
        remaining = Math.max(0, width - submitWidth - cancelWidth - 16);
    if (people)
        nodes.push(
            label(
                'messageFormSelected',
                rect(0, y + 10, remaining, 18),
                tr(
                    mode === 'create'
                        ? '{count} selected'
                        : '{count} members selected',
                    { count: model.count || 0 }
                ),
                { fontRole: 'secondary', color: 'secondaryText' }
            )
        );
    nodes.push(
        button(
            'messageFormCancel',
            rect(
                Math.max(0, width - submitWidth - cancelWidth - 8),
                y,
                cancelWidth,
                38
            ),
            tr('Cancel'),
            '',
            { type: 'cancel' },
            !model.busy
        )
    );
    nodes.push(
        button(
            'messageFormSubmit',
            rect(Math.max(0, width - submitWidth), y, submitWidth, 38),
            submit,
            '',
            { type: 'submit' },
            !model.busy && model.valid !== false,
            {
                highlighted: !['delete', 'delete-message', 'clear'].includes(
                    mode
                ),
                destructive: ['delete', 'delete-message', 'clear'].includes(
                    mode
                )
            }
        )
    );
    return { height: y + 38, nodes };
}

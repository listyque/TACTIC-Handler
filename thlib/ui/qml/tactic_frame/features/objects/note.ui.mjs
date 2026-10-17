import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

// Rich text and native file operations remain value ports; their measured heights drive the card.
export function geometry(model, width) {
    const status = !!model.status;
    const cardWidth = Math.min(
        Math.max(0, width - (status ? 48 : 20)) * (status ? 0.9 : 0.82),
        status ? 640 : 560
    );
    return {
        width: cardWidth,
        x: status ? 34 : model.own ? Math.max(10, width - cardWidth - 10) : 10,
        contentX: 50,
        contentWidth: Math.max(0, cardWidth - 60),
        padding: 10,
        spacing: 6,
        headerHeight: 28,
        radius: 14
    };
}
export function card(model, width, height) {
    const fill = model.status
        ? model.statusColor || 'action'
        : model.own
          ? 'secondaryContainer'
          : 'surfaceContainerHigh';
    const nodes = [
        node('Box', 'noteBubbleFill', rect(0, 0, width, height), {
            background: fill,
            opacity: model.status ? 48 / 255 : 1,
            radius: 14
        })
    ];
    if (model.selected || model.status || model.unread)
        nodes.push(
            node('Box', 'noteBubbleBorder', rect(0, 0, width, height), {
                background: 'transparent',
                radius: 14,
                border: model.selected
                    ? 'action'
                    : model.status
                      ? model.statusColor || 'action'
                      : 'action',
                borderWidth: model.selected ? 2 : 1
            })
        );
    nodes.push(
        node('Preview', 'noteAuthorAvatar', rect(10, 10, 32, 32), {
            source: model.avatarUrl || '',
            initials: model.initials || '',
            icon: 'person',
            round: true,
            outlined: true,
            accent: model.authorColor || 'action'
        })
    );
    return { nodes };
}
export function header(model, width, language) {
    const tr = (text) => translate(text, language),
        actions = model.status ? 0 : model.reply ? 56 : 28;
    const timeWidth = Math.min(
        110,
        Math.max(48, String(model.time || '').length * 6)
    );
    const authorWidth = Math.max(0, width - timeWidth - actions - 12);
    const author =
        (model.authorLabel || model.author || '') +
        (model.author && model.authorLabel && model.authorLabel !== model.author
            ? ' (' + model.author + ')'
            : '');
    const nodes = [
        node('Action', 'noteAuthor', rect(0, 0, authorWidth, 28), {
            text: author,
            normalColor: 'transparent',
            radius: 0,
            enabled: !!model.author,
            action: { type: 'profile', login: model.author },
            children: [
                label('noteAuthorName', rect(0, 4, authorWidth, 20), author, {
                    fontRole: 'secondary',
                    weight: 600,
                    color: model.authorColor || 'action'
                })
            ]
        }),
        label(
            'noteTime',
            rect(authorWidth + 6, 5, timeWidth, 18),
            model.time || '',
            {
                fontRole: 'caption',
                align: 'right',
                color: 'secondaryText',
                toolTip: model.fullTime || ''
            }
        )
    ];
    if (!model.status) {
        if (model.reply)
            nodes.push(
                button(
                    'noteReply',
                    rect(width - 56, 0, 28, 28),
                    tr('Reply'),
                    'comment',
                    { type: 'reply' },
                    !model.busy,
                    { iconOnly: true, iconAction: true, iconSize: 16 }
                )
            );
        nodes.push(
            button(
                'noteActions',
                rect(Math.max(0, width - 28), 0, 28, 28),
                tr('Note actions'),
                'more',
                { type: 'menu' },
                !model.busy,
                {
                    iconOnly: true,
                    iconAction: true,
                    iconSize: 16,
                    opacity: model.actionsVisible === false ? 0 : 1
                }
            )
        );
    }
    return { height: 28, nodes };
}

export const bodyMetrics = {
    gap: 6,
    minimumCellWidth: 210,
    preferredCellWidth: 240,
    maximumColumns: 2
};

// The rich-text/file controls report their real heights; Frame owns the order and spacing.
export function body(model, width, heights = {}) {
    let top = 0;
    const nodes = [];
    for (const part of ['status', 'text', 'previews', 'attachments']) {
        if (!model[part]) continue;
        if (nodes.length) top += bodyMetrics.gap;
        const height = Math.max(
            1,
            heights[part] || (part === 'status' ? 24 : 1)
        );
        nodes.push(
            node('View', 'noteBody_' + part, rect(0, top, width, height), {
                view: part
            })
        );
        top += height;
    }
    return { height: top, nodes };
}

export function edit(model, width, language) {
    const tr = (text) => translate(text, language),
        gap = 8;
    const cancelWidth = 94,
        saveWidth = 94;
    const nodes = [
        node('Area', 'noteEditText', rect(0, 0, width, 150), {
            text: model.text || '',
            label: tr('Note text'),
            placeholder: tr('Note text'),
            enabled: !model.busy && !model.uncertain,
            action: { type: 'text' }
        })
    ];
    if (model.error)
        nodes.push(
            node('Area', 'noteEditError', rect(0, 158, width, 72), {
                text: model.error,
                label: tr('Error'),
                readOnly: true,
                enabled: true,
                error: true
            })
        );
    const y = model.error ? 242 : 162;
    nodes.push(
        button(
            'noteEditCancel',
            rect(
                Math.max(0, width - cancelWidth - saveWidth - gap),
                y,
                cancelWidth,
                36
            ),
            tr('Cancel'),
            '',
            { type: 'cancel' },
            !model.busy
        )
    );
    nodes.push(
        button(
            'noteEditSave',
            rect(Math.max(0, width - saveWidth), y, saveWidth, 36),
            tr('Save'),
            '',
            { type: 'save' },
            !model.busy &&
                !model.uncertain &&
                !!String(model.text || '').trim(),
            { highlighted: true }
        )
    );
    return { height: y + 36, nodes };
}

export function remove(model, width, language) {
    const tr = (text) => translate(text, language),
        nodes = [];
    const y = model.error ? 84 : 0;
    if (model.error)
        nodes.push(
            node('Area', 'noteDeleteError', rect(0, 0, width, 72), {
                text: model.error,
                label: tr('Error'),
                readOnly: true,
                enabled: true,
                error: true
            })
        );
    nodes.push(
        button(
            'noteDeleteCancel',
            rect(Math.max(0, width - 196), y, 94, 36),
            tr('Cancel'),
            '',
            { type: 'cancel' },
            !model.busy
        )
    );
    nodes.push(
        button(
            'noteDeleteConfirm',
            rect(Math.max(0, width - 94), y, 94, 36),
            tr('Delete'),
            '',
            { type: 'delete' },
            !model.busy && !model.uncertain,
            { destructive: true }
        )
    );
    return { height: y + 36, nodes };
}

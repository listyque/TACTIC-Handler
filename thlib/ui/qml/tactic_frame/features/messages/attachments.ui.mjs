import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export function controls(model, language) {
    const tr = (text) => translate(text, language),
        nodes = [];
    let x = 0;
    const icon = (id, name, title, type, enabled = true, extra = {}) => {
        nodes.push(
            button(
                id,
                rect(x, 0, 26, 26),
                '',
                name,
                { type },
                enabled,
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
        x += 30;
    };
    icon(
        'messageAttachFiles',
        'attach-file',
        'Attach file',
        'choose',
        !model.busy && model.upload !== false
    );
    if (model.clipboard !== false)
        icon(
            'messageAttachClipboard',
            'content-paste',
            'Attach image from clipboard',
            'paste',
            !model.busy && model.upload !== false
        );
    if (model.count) {
        icon(
            'messageAttachmentDrafts',
            'inventory-2',
            'Attachments to send',
            'drafts',
            true,
            { badgeCount: model.count, pressAction: { type: 'drafts-press' } }
        );
        icon(
            'messageClearAttachments',
            model.busy ? 'close' : 'delete-sweep',
            model.busy ? 'Cancel attachment upload' : 'Clear attachments',
            model.busy ? 'cancel' : 'clear',
            !model.busy || !!model.canCancel
        );
    }
    return { width: Math.max(0, x - 4), height: 26, nodes };
}
export function panel(model, width, height, language) {
    const tr = (text) => translate(text, language),
        rowHeight = model.previews ? 100 : 44;
    return {
        nodes: [
            label(
                'messageAttachmentDraftTitle',
                rect(0, 0, width, 18),
                tr('ATTACHMENTS TO SEND'),
                { fontRole: 'body', weight: 600, color: 'secondaryText' }
            ),
            node(
                'CheckBox',
                'messageAttachmentPreviews',
                rect(0, 25, width, 28),
                {
                    text: tr('Show attachment previews'),
                    checked: !!model.previews,
                    compact: true,
                    action: { type: 'previews' }
                }
            ),
            node(
                'List',
                'messageAttachmentDraftList',
                rect(0, 60, width, Math.max(0, height - 60)),
                {
                    source: 'drafts',
                    keyField: 'token',
                    fields: [
                        'token',
                        'title',
                        'size',
                        'status',
                        'previewUrl',
                        'error'
                    ],
                    rowHeight,
                    rowGap: 2,
                    label: tr('Attachments to send')
                }
            )
        ]
    };
}
export function row(model, width, language) {
    const tr = (text) => translate(text, language),
        preview = !!model.previews,
        height = preview ? 98 : 42,
        left = preview ? 82 : 32,
        removeX = Math.max(0, width - 31),
        titleWidth = Math.max(0, removeX - left - 8),
        error = model.status === 'failed' || !!model.error,
        status =
            model.error ||
            tr(
                {
                    ready: 'Ready to upload',
                    uploading: 'Uploading',
                    uploaded: 'Uploaded',
                    failed: 'Upload failed. Retry sending.'
                }[model.status] || ''
            ),
        nodes = [
            node('Box', 'attachmentDraftSurface', rect(0, 0, width, height), {
                background: 'row',
                radius: 11
            }),
            label(
                'attachmentDraftName',
                rect(left, preview ? 12 : 5, titleWidth, 16),
                model.title || '',
                { fontRole: 'secondary', weight: preview ? 600 : 400 }
            ),
            label(
                'attachmentDraftSize',
                rect(left, preview ? 33 : 23, titleWidth, 15),
                String(model.size || ''),
                { fontRole: 'caption', color: 'secondaryText' }
            )
        ];
    if (preview) {
        nodes.push(
            node('Preview', 'attachmentDraftPreview', rect(8, 8, 66, 66), {
                source: model.previewUrl || '',
                initials: '',
                icon: 'description',
                round: false,
                radius: 9,
                fit: 'contain',
                accent: error ? 'error' : 'action'
            })
        );
        if (status)
            nodes.push(
                label(
                    'attachmentDraftStatus',
                    rect(left, 54, titleWidth, 36),
                    status,
                    {
                        fontRole: 'caption',
                        color: error ? 'error' : 'secondaryText',
                        wrap: true
                    }
                )
            );
        if (model.canOpen)
            nodes.push(
                node(
                    'Action',
                    'attachmentDraftOpen',
                    rect(0, 0, Math.max(0, removeX - 4), height),
                    {
                        text: tr('Open attachment'),
                        radius: 11,
                        action: { type: 'open', key: model.token }
                    }
                )
            );
    } else
        nodes.push(
            node('Icon', 'attachmentDraftIcon', rect(9, 13, 16, 16), {
                icon: error ? 'warning' : 'description',
                color: error ? 'error' : 'action',
                text: status
            })
        );
    nodes.push(
        button(
            'attachmentDraftRemove',
            rect(removeX, (height - 26) / 2, 26, 26),
            '',
            'close',
            { type: 'remove', key: model.token },
            !model.busy,
            {
                label: tr('Remove attachment'),
                iconOnly: true,
                iconAction: true,
                iconSize: 16
            }
        )
    );
    return { height, nodes };
}

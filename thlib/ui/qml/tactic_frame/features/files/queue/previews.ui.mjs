import { node, rect, label, button, muted } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';

export const metrics = {
    width: 520,
    height: 460,
    ownerMargin: 32,
    clearWidth: 420
};

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language),
        compact = width < 420,
        footerHeight = compact ? 142 : 52,
        nodes = [
            node(
                'List',
                'commitQueuePreviewList',
                rect(0, 0, width, Math.max(0, height - footerHeight - 8)),
                {
                    source: 'previews',
                    keyField: 'key',
                    rowHeight: 64,
                    rowGap: 6,
                    label: tr('Operation previews'),
                    fields: [
                        'key',
                        'index',
                        'operationId',
                        'sourceKey',
                        'source',
                        'title',
                        'canRemove'
                    ]
                }
            )
        ];
    if (!model.count)
        nodes.push(
            label(
                'commitQueuePreviewsEmpty',
                rect(12, 20, width - 24, 50),
                tr('No previews'),
                Object.assign({}, muted, { wrap: true, align: 'center' })
            )
        );
    const actions = [
            {
                id: 'commitQueuePreviewsAdd',
                text: 'Add images',
                label: 'Choose preview images',
                icon: 'image',
                command: 'choose',
                enabled: !!model.canEdit
            },
            {
                id: 'commitQueuePreviewsPaste',
                text: 'Paste image',
                label: 'Paste preview image from clipboard',
                icon: 'clipboard',
                command: 'paste',
                enabled:
                    !!model.canEdit &&
                    (!model.clipboardKnown || !!model.clipboardHasImage)
            },
            {
                id: 'commitQueuePreviewsClose',
                text: 'Close',
                label: 'Close',
                icon: '',
                command: 'close',
                enabled: true
            }
        ],
        gap = 8,
        w = compact ? width : (width - gap * 2) / 3;
    actions.forEach((action, index) =>
        nodes.push(
            button(
                action.id,
                rect(
                    compact ? 0 : index * (w + gap),
                    height - footerHeight + (compact ? index * 46 : 0),
                    w,
                    38
                ),
                tr(action.text),
                action.icon,
                { type: 'preview', command: action.command },
                action.enabled,
                { label: tr(action.label) }
            )
        )
    );
    return { nodes };
}

export function row(record, width, language) {
    return {
        nodes: [
            node(
                'Box',
                'commitQueuePreviewRow_' + record.key,
                rect(0, 0, width, 58),
                {
                    background: 'surfaceContainerHigh',
                    radius: 12,
                    children: [
                        node(
                            'View',
                            'commitQueuePreviewImage_' + record.key,
                            rect(6, 6, 46, 46),
                            {
                                view: 'preview',
                                sourceKey: record.sourceKey,
                                source: record.source,
                                initials: '',
                                icon: 'image',
                                accent: 'action',
                                radius: 12
                            }
                        ),
                        label(
                            'commitQueuePreviewName_' + record.key,
                            rect(60, 0, width - 100, 58),
                            record.title,
                            { elideMiddle: true }
                        ),
                        button(
                            'commitQueuePreviewRemove_' + record.key,
                            rect(width - 34, 15, 28, 28),
                            translate('Remove preview', language),
                            'close',
                            {
                                type: 'removePreview',
                                index: record.index,
                                operationId: record.operationId
                            },
                            record.canRemove,
                            { iconOnly: true, iconAction: true }
                        )
                    ]
                }
            )
        ]
    };
}

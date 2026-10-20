import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { prettySize, sourceIcon } from './file_values.mjs';
import * as Confirmation from '../../controls/feedback/confirmation.ui.mjs';
import { captionHeight } from '../../controls/forms/sections.ui.mjs';
import { controls } from '../../core/foundation.mjs';

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language),
        margin = 10,
        inner = Math.max(0, width - 20),
        stacked = width < 370,
        footerHeight = stacked ? 100 : 60,
        closeWidth = stacked ? inner : 120;
    const nodes = [
        node('Box', 'snapshotCheckoutSurface', rect(0, 0, width, height), {
            background: 'surfaceContainerHigh',
            radius: 0
        })
    ];
    if (model.conflict)
        return {
            nodes: nodes.concat(
                Confirmation.describe(
                    {
                        message: tr(
                            'The local file differs from the server. Replace it?'
                        ),
                        accept: 'Overwrite',
                        destructive: true
                    },
                    width,
                    height,
                    language
                ).nodes
            )
        };
    let y = margin;
    nodes.push(
        label(
            'snapshotCheckoutContext',
            rect(margin, y, inner, 24),
            model.context || '',
            { color: 'secondaryText' }
        )
    );
    y += 32;
    for (const [name, text, error] of [
        ['error', model.error, true],
        ['message', model.message, false]
    ]) {
        if (!text) continue;
        const textHeight = Math.max(24, captionHeight(text, inner - 16) + 12);
        const viewport = Math.min(
            textHeight,
            Math.max(48, Math.min(104, height / 3))
        );
        nodes.push(
            node(
                'Scroll',
                'snapshotCheckoutNotice_' + name,
                rect(margin, y, inner, viewport),
                {
                    contentHeight: textHeight,
                    scrollbarId: 'snapshotCheckoutNoticeScrollBar_' + name,
                    children: [
                        label(
                            'snapshotCheckout_' + name,
                            rect(0, 0, inner - 16, textHeight),
                            text,
                            {
                                wrap: true,
                                fontRole: 'caption',
                                color: error ? 'error' : 'secondaryText',
                                role: error ? 'alert' : 'status'
                            }
                        )
                    ]
                }
            )
        );
        y += viewport + 8;
    }
    if (model.loading || model.busy) {
        nodes.push(
            node(
                'View',
                'snapshotCheckoutProgress',
                rect(margin, y, inner, controls.feedback.progressHeight),
                {
                    view: 'progress',
                    min: 0,
                    max: 1,
                    indeterminate:
                        !!model.loading ||
                        (!!model.busy && typeof model.progress !== 'number'),
                    value: Number(model.progress) || 0,
                    label: tr(model.loading ? 'Loading data…' : 'Downloading')
                }
            )
        );
        y += controls.feedback.progressHeight + 8;
    }
    nodes.push(
        node(
            'List',
            'snapshotCheckoutFiles',
            rect(margin, y, inner, Math.max(0, height - y - footerHeight - 4)),
            {
                source: 'files',
                keyField: 'token',
                rowHeight: 62,
                rowGap: 4,
                label: tr('Files'),
                role: 'listbox',
                scrollbarId: 'snapshotCheckoutFilesScrollBar',
                fields: [
                    'token',
                    'title',
                    'fileType',
                    'bytes',
                    'selected',
                    'enabled'
                ]
            }
        )
    );
    if (!model.loading && !model.count)
        nodes.push(
            label(
                'snapshotCheckoutEmpty',
                rect(margin, y + 12, inner, 40),
                tr('No files'),
                { color: 'secondaryText' }
            )
        );
    nodes.push(
        button(
            'snapshotCheckoutClose',
            rect(
                margin,
                height - footerHeight + (stacked ? 6 : 12),
                closeWidth,
                38
            ),
            tr('Close'),
            'close',
            { type: 'close' },
            true
        )
    );
    nodes.push(
        button(
            'snapshotCheckoutDownload',
            rect(
                stacked ? margin : margin + closeWidth + 8,
                height - 48,
                stacked ? inner : Math.max(0, inner - closeWidth - 8),
                38
            ),
            tr(model.busy ? 'Cancel transfer' : 'Check out'),
            model.busy ? 'cancel' : 'download',
            { type: model.busy ? 'cancelTransfer' : 'checkout' },
            !!model.busy || (!!model.ready && !!model.count),
            { highlighted: !model.busy }
        )
    );
    return { nodes };
}

export function fileRow(record, width, language) {
    return {
        nodes: [
            node(
                'Action',
                'snapshotCheckoutFile_' + record.token,
                rect(0, 0, width, 58),
                {
                    text: record.title,
                    enabled: record.enabled !== false,
                    selected: !!record.selected,
                    selectedColor: 'contentSelection',
                    role: 'option',
                    action: { type: 'select', token: record.token },
                    children: [
                        node(
                            'Icon',
                            'snapshotCheckoutIcon_' + record.token,
                            rect(12, 20, 18, 18),
                            { icon: sourceIcon(record.title), color: 'action' }
                        ),
                        label(
                            'snapshotCheckoutName_' + record.token,
                            rect(42, 7, Math.max(0, width - 54), 22),
                            record.title,
                            { elideMiddle: true, pointerTransparent: true }
                        ),
                        label(
                            'snapshotCheckoutSize_' + record.token,
                            rect(42, 33, Math.max(0, width - 54), 18),
                            [record.fileType, prettySize(record.bytes)]
                                .filter(Boolean)
                                .join(' · '),
                            {
                                fontRole: 'caption',
                                color: 'secondaryText',
                                pointerTransparent: true
                            }
                        )
                    ]
                }
            )
        ]
    };
}

import { node, rect, label, button, muted } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { captionHeight } from '../../../controls/forms/sections.ui.mjs';
import * as Editor from './editor.ui.mjs';

export function describe(model, width, height, language) {
    const tr = (text, values) => translate(text, language, values);
    const w = width,
        h = height,
        children = [],
        record = model.record || {},
        showRetry = !!record.canRetry || !!model.resumeAvailable,
        splitAuxiliary = w < 410 && model.busy && showRetry,
        footerHeight = splitAuxiliary ? 142 : w < 410 ? 96 : 52;
    let top = 0;
    if (model.duplicate) {
        const text =
                model.duplicateDescription ||
                tr(
                    'The same files are already prepared for this object and context.'
                ),
            stacked = w < 500,
            messageHeight = Math.max(
                36,
                captionHeight(text, stacked ? w - 20 : w - 240)
            ),
            duplicateHeight = messageHeight + (stacked ? 58 : 18);
        const content = [
            label(
                'commitQueueDuplicateMessage',
                rect(10, 9, stacked ? w - 20 : w - 240, messageHeight),
                text,
                { fontRole: 'secondary', wrap: true }
            )
        ];
        [
            ['replace', 'Replace'],
            ['add', 'Add another'],
            ['ignore', 'Ignore duplicate']
        ].forEach(([decision, title], index) => {
            const buttonWidth = stacked ? (w - 36) / 3 : 70,
                x = stacked
                    ? 10 + index * (buttonWidth + 8)
                    : w - 230 + index * 76;
            content.push(
                button(
                    'commitQueueDuplicate_' + decision,
                    rect(x, stacked ? messageHeight + 14 : 9, buttonWidth, 36),
                    tr(title),
                    decision === 'ignore' ? 'close' : '',
                    { type: 'duplicate', decision },
                    decision !== 'replace' || model.canReplace !== false
                )
            );
        });
        children.push(
            node(
                'Box',
                'commitQueueDuplicate',
                rect(0, 0, w, duplicateHeight),
                {
                    background: 'tertiaryContainer',
                    border: 'tertiary',
                    radius: 16,
                    children: content
                }
            )
        );
        top = duplicateHeight + 8;
    }
    if (model.selected >= 0) {
        const form = Editor.describe(model, Math.max(0, w - 16), language);
        children.push(
            node(
                'Scroll',
                'commitQueueEditorScroll',
                rect(0, top, w, Math.max(0, h - top - footerHeight - 8)),
                { contentHeight: form.height, children: form.nodes }
            )
        );
    } else {
        const title = tr(
                model.count ? 'Select an operation' : 'Ready for operations'
            ),
            message = tr(
                model.count
                    ? 'Select an operation in the queue to review its files and settings.'
                    : 'Add files through Save Snapshot or Drop Plate. You can review every prepared operation before sending it.'
            ),
            center = Math.max(12, (h - footerHeight - 140) / 2);
        children.push(
            node(
                'Icon',
                'commitQueueWelcomeIcon',
                rect((w - 36) / 2, center, 36, 36),
                {
                    icon: model.count ? 'queue' : 'upload',
                    color: 'disabledText'
                }
            )
        );
        children.push(
            label(
                'commitQueueWelcomeTitle',
                rect(20, center + 48, w - 40, 30),
                title,
                { fontRole: 'bodyLarge', weight: 600, align: 'center' }
            )
        );
        children.push(
            label(
                'commitQueueWelcomeMessage',
                rect(20, center + 84, w - 40, 70),
                message,
                Object.assign({}, muted, { wrap: true, align: 'center' })
            )
        );
    }
    const footer = [],
        narrow = w < 410,
        actionY = splitAuxiliary ? 96 : narrow ? 46 : 7,
        auxiliaryY = splitAuxiliary ? 46 : actionY,
        auxiliaryCount = (model.busy ? 1 : 0) + (showRetry ? 1 : 0);
    footer.push(
        label(
            'commitQueueFooterStatus',
            rect(
                8,
                4,
                narrow
                    ? w - 16
                    : Math.max(
                          0,
                          w -
                              184 -
                              auxiliaryCount * 88 -
                              (record.canInspect ? 34 : 0)
                      ),
                narrow ? 32 : 44
            ),
            model.error ||
                (model.busy
                    ? record.stage || tr('Working…')
                    : tr('{count} queue items · Ready to send', {
                          count: model.count
                      })),
            {
                fontRole: 'secondary',
                color: model.error ? 'error' : 'secondaryText',
                role: model.error ? 'alert' : 'status'
            }
        )
    );
    const x = w - 168;
    let auxiliaryX = splitAuxiliary ? 96 : x - 88;
    if (model.busy) {
        footer.push(
            button(
                'commitQueueCancel',
                rect(auxiliaryX, auxiliaryY, 80, 38),
                tr('Cancel'),
                'stop',
                { type: 'cancel' },
                model.canCancel !== false,
                { destructive: true }
            )
        );
        auxiliaryX -= 88;
    }
    if (showRetry) {
        footer.push(
            button(
                'commitQueueRetry',
                rect(auxiliaryX, auxiliaryY, 80, 38),
                tr('Retry'),
                'refresh',
                { type: 'retry' },
                (!model.busy || !!model.resumeAvailable) && !model.versionError
            )
        );
        auxiliaryX -= 88;
    }
    if (record.canInspect)
        footer.push(
            button(
                'commitQueueSnapshot',
                rect(
                    splitAuxiliary ? 8 : Math.max(4, auxiliaryX + 54),
                    actionY + 5,
                    28,
                    28
                ),
                tr('Snapshot Browser'),
                'snapshot',
                { type: 'snapshot' },
                true,
                { iconOnly: true, iconAction: true }
            )
        );
    footer.push(
        button(
            'commitQueuePrimarySendButton',
            rect(x, actionY, 126, 38),
            tr('Commit all'),
            'upload',
            { type: 'all' },
            !model.busy && !!model.hasReady,
            { highlighted: true }
        )
    );
    footer.push(
        button(
            'commitQueueSendOverflowButton',
            rect(w - 34, actionY + 5, 28, 28),
            tr('More send actions'),
            'more',
            { type: 'sendMenu' },
            !model.busy,
            { iconOnly: true, iconAction: true }
        )
    );
    children.push(
        node(
            'Box',
            'commitQueueActionFooter',
            rect(0, Math.max(0, h - footerHeight), w, footerHeight),
            { background: 'surfaceContainerLow', radius: 16, children: footer }
        )
    );
    return {
        nodes: [
            node('Box', 'commitQueueDetailsPanel', rect(0, 0, width, height), {
                children
            })
        ]
    };
}

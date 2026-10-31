import { spacing } from '../../../core/foundation.mjs';
import { node, rect } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import * as Progress from './progress.ui.mjs';
import { describe as queueList } from './list.ui.mjs';
import { describe as details } from './details.ui.mjs';
export { operationRow, sourceRow } from './rows.ui.mjs';
export { namingRows, namingRow, versionValue } from './editor.ui.mjs';
export {
    preview as previewActions,
    send as sendActions,
    operation as operationActions,
    toolbar as toolbarActions
} from './actions.ui.mjs';

export function layout(model, width, height, language) {
    const compact = width < 700,
        margin = spacing.content,
        gap = 10,
        progress = Progress.describe(
            model.progress,
            width - margin * 2,
            language
        ),
        top =
            margin +
            (progress.height ? progress.height + gap : 0) +
            (compact ? 44 : 0),
        available = Math.max(0, width - margin * 2 - gap),
        pane = compact
            ? width - margin * 2
            : Math.max(
                  Math.min(270, available * 0.45),
                  Math.min(
                      model.paneWidth || available * 0.36,
                      available - Math.min(320, available * 0.5)
                  )
              ),
        bodyHeight = Math.max(0, height - top - margin);
    return {
        compact,
        progress,
        top,
        pane,
        showQueue: !compact || !model.details,
        showDetails: !compact || !!model.details,
        queue: rect(margin, top, pane, bodyHeight),
        splitter: rect(margin + pane, top, gap, bodyHeight),
        details: rect(
            compact ? margin : margin + pane + gap,
            top,
            compact ? width - margin * 2 : available - pane,
            bodyHeight
        )
    };
}

export function describe(model, width, height, language) {
    const tr = (text, values) => translate(text, language, values),
        bounds = layout(model, width, height, language),
        nodes = [
            node('Box', 'commitQueueBackground', rect(0, 0, width, height), {
                background: 'workspace',
                radius: 0
            })
        ];
    if (bounds.progress.height)
        nodes.push(
            node(
                'Box',
                'commitQueueProgress',
                rect(10, 10, width - 20, bounds.progress.height),
                { children: bounds.progress.nodes }
            )
        );
    if (bounds.compact)
        nodes.push(
            node(
                'Segmented',
                'commitQueueNavigation',
                rect(10, bounds.top - 44, width - 20, 36),
                {
                    label: tr('Commit Queue'),
                    value: model.details ? 'details' : 'queue',
                    options: [
                        { value: 'queue', label: tr('QUEUE'), icon: 'queue' },
                        {
                            value: 'details',
                            label: tr('Operation details'),
                            icon: 'settings',
                            disabled: model.selected < 0
                        }
                    ],
                    action: { type: 'navigate' }
                }
            )
        );
    if (bounds.showQueue)
        nodes.push(
            node('Box', 'commitQueueListSlot', bounds.queue, {
                children: queueList(
                    model,
                    bounds.queue.width,
                    bounds.queue.height,
                    language
                ).nodes
            })
        );
    if (!bounds.compact)
        nodes.push(
            node('Splitter', 'commitQueueMainSplitter', bounds.splitter, {
                label: tr('Queue pane width'),
                value: bounds.pane,
                min: Math.min(270, (width - 30) * 0.45),
                max: Math.max(0, width - 350),
                action: { type: 'paneWidthDraft' },
                commitAction: { type: 'paneWidth' },
                cancelAction: { type: 'paneWidthCancel' }
            })
        );
    if (bounds.showDetails)
        nodes.push(
            node('Box', 'commitQueueDetailsSlot', bounds.details, {
                children: details(
                    model,
                    bounds.details.width,
                    bounds.details.height,
                    language
                ).nodes
            })
        );
    return { nodes };
}

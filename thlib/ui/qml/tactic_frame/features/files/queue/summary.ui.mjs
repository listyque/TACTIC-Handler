import { node, rect, label, button } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { status, statusTitle, preview } from './actions.ui.mjs';

export function describe(model, width, language) {
    const tr = (text, values) => translate(text, language, values),
        record = model.record || {},
        compact = width < 620,
        stacked = width < 460,
        height = stacked ? 140 : 98,
        actionsWidth = compact ? 68 : 340,
        titleWidth = Math.max(0, width - 108 - actionsWidth),
        nodes = [
            node('View', 'commitQueueSummaryPreview', rect(12, 12, 72, 72), {
                view: 'preview',
                sourceKey: record.operationId,
                source: record.previewUrl || '',
                initials: record.previewExtension || 'FILE',
                accent: 'action',
                radius: 12
            }),
            label(
                'commitQueueObjectTitle',
                rect(96, 12, titleWidth, 22),
                record.objectTitle || tr('Operation details'),
                { fontRole: 'bodyLarge', weight: 600 }
            ),
            label(
                'commitQueueFutureName',
                rect(96, 38, titleWidth, 20),
                record.futureFileName || record.title || tr('Snapshot'),
                { elideMiddle: true }
            )
        ];
    if (!compact) {
        const state = status(record.status);
        nodes.push(
            node(
                'StatusChip',
                'commitQueueOperationStatus',
                rect(width - actionsWidth, 14, 164, 26),
                {
                    text: tr(statusTitle(record)),
                    icon: state.icon,
                    accent:
                        record.status === 'Prepared' ? 'green' : state.color,
                    dense: true
                }
            )
        );
        preview(model)
            .filter((action) => !action.separator)
            .forEach((action, index) => {
                nodes.push(
                    button(
                        'commitQueuePreview_' + action.command,
                        rect(width - 166 + index * 32, 48, 28, 28),
                        tr(action.title),
                        action.icon,
                        { type: 'preview', command: action.command },
                        action.enabled,
                        { iconOnly: true, iconAction: true }
                    )
                );
            });
    } else {
        nodes.push(
            button(
                'commitQueuePreviewButton',
                rect(width - 72, 16, 28, 28),
                tr(
                    record.previewCount
                        ? 'Manage selected previews'
                        : 'Choose preview images'
                ),
                record.previewCount ? 'collections' : 'image',
                {
                    type: 'preview',
                    command: record.previewCount ? 'manage' : 'choose'
                },
                !model.busy && (!!record.previewCount || !!record.canPreview),
                { iconOnly: true, iconAction: true }
            )
        );
        nodes.push(
            button(
                'commitQueuePreviewOverflowButton',
                rect(width - 38, 16, 28, 28),
                tr('Preview actions'),
                'more',
                { type: 'previewMenu' },
                !model.busy,
                { iconOnly: true, iconAction: true }
            )
        );
    }
    const x = stacked ? 12 : 96,
        y = stacked ? 98 : 64,
        available = width - x - 12 - (compact ? 0 : actionsWidth),
        processWidth = Math.min(90, Math.max(50, available * 0.24)),
        branchWidth = Math.min(
            170,
            Math.max(80, available - processWidth - 86)
        );
    nodes.push(
        label(
            'commitQueueSummaryProcess',
            rect(x, y, processWidth, 28),
            record.process || 'publish',
            { fontRole: 'secondary', color: 'secondaryText' }
        )
    );
    if (model.contextEditing)
        nodes.push(
            node(
                'Field',
                'commitQueueContextField',
                rect(x + processWidth + 6, y, branchWidth, 28),
                {
                    label: tr('Context branch'),
                    placeholder: tr('Context branch'),
                    text: model.contextDraft || '',
                    enabled: !!record.canContext && !model.busy,
                    selectOnFocus: true,
                    action: { type: 'contextDraft' },
                    commitAction: { type: 'contextCommit' },
                    keys: {
                        Enter: { type: 'contextCommit' },
                        Escape: { type: 'contextCancel' }
                    }
                }
            )
        );
    else
        nodes.push(
            node(
                'StatusChip',
                'commitQueueContextChip',
                rect(x + processWidth + 6, y, branchWidth, 28),
                {
                    text: record.contextBranch
                        ? tr('Context: {context}', {
                              context: record.contextBranch
                          })
                        : tr('Add context'),
                    icon: 'edit',
                    accent: record.contextBranch ? 'action' : 'secondaryText',
                    dense: true,
                    enabled: !!record.canContext && !model.busy,
                    action: { type: 'contextEdit' }
                }
            )
        );
    if (available - processWidth - branchWidth > 28)
        nodes.push(
            label(
                'commitQueueFileSummary',
                rect(
                    x + processWidth + branchWidth + 18,
                    y,
                    available - processWidth - branchWidth - 18,
                    28
                ),
                tr('{count} files', { count: record.fileCount || 0 }),
                { fontRole: 'secondary', color: 'secondaryText' }
            )
        );
    return {
        nodes: [
            node(
                'Box',
                'commitQueueOperationSummary',
                rect(0, 0, width, height),
                {
                    background: 'surfaceContainerLow',
                    radius: 16,
                    children: nodes
                }
            )
        ],
        height
    };
}

import { captionedSwitch } from '../../../controls/forms/toggle.ui.mjs';
import { node, rect, label, button, muted } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';

export function discovery(model, language) {
    const tr = (text, values) => translate(text, language, values);
    if (model.discoveryState === 'objects')
        return tr('Requesting object list from TACTIC');
    if (model.discoveryState === 'scope')
        return tr('Preparing parallel repository chunks');
    if (model.discoveryState === 'processing')
        return tr('Processing server response: {count} objects', {
            count: model.totalRoots
        });
    if (model.discoveryState === 'snapshots')
        return tr('Requesting snapshots: {done} / {total} objects', {
            done: model.processedRoots,
            total: model.totalRoots
        });
    if (model.discoveryState === 'publishing')
        return tr('Preparing download queue: {count} files', {
            count: model.total
        });
    if (model.discoveryState === 'streaming' && model.totalRoots > 0)
        return tr('Parallel repository chunks: {done} / {total} objects', {
            done: model.processedRoots,
            total: model.totalRoots
        });
    if (model.discoveryState === 'cancelling')
        return tr('Stopping repository discovery');
    return tr('Discovering repository files');
}

function summary(model, width, language) {
    const tr = (text, values) => translate(text, language, values),
        columns = width >= 760 ? 4 : width >= 520 ? 3 : 2,
        metrics = [
            ['Processed / total files', model.processed + ' / ' + model.total],
            ['Total size', model.totalSize],
            ['Downloaded', model.downloadedSize],
            ['Remaining data', model.remainingSize],
            [model.active > 0 ? 'Speed' : 'Average speed', model.speed],
            ['Elapsed', model.elapsed],
            ['Remaining', model.eta],
            ['Successful / errors', model.completed + ' / ' + model.failed]
        ],
        gap = 8,
        cellWidth = (width - 24 - gap * (columns - 1)) / columns,
        children = [],
        accent =
            model.failed > 0 ? 'error' : model.active > 0 ? 'action' : 'green',
        message = model.discovering
            ? discovery(model, language)
            : tr(
                  model.active > 0
                      ? 'Downloading repository files'
                      : model.processed === 0
                        ? 'Ready to download repository files'
                        : model.failed > 0
                          ? 'Repository download finished with errors'
                          : 'Repository download complete'
              );
    children.push(
        node('Icon', 'repositorySyncSummaryIcon', rect(12, 14, 18, 18), {
            icon:
                model.failed > 0
                    ? 'warning'
                    : model.active > 0
                      ? 'cloud-download'
                      : 'task-alt',
            color: accent
        })
    );
    children.push(
        label(
            'repositorySyncSummaryStatus',
            rect(38, 10, width - 108, 28),
            message,
            { weight: 600 }
        )
    );
    children.push(
        label(
            'repositorySyncSummaryPercent',
            rect(width - 62, 10, 50, 28),
            Math.round(model.progress * 100) + '%',
            {
                color: 'action',
                weight: 700,
                align: 'right',
                fontRole: 'caption'
            }
        )
    );
    children.push(
        node('Box', 'repositorySyncOverallTrack', rect(12, 46, width - 24, 7), {
            background: 'surfaceContainerHigh',
            radius: 3.5,
            children: [
                node(
                    'Box',
                    'repositorySyncOverallFill',
                    rect(
                        0,
                        0,
                        (width - 24) *
                            Math.max(0, Math.min(1, model.progress || 0)),
                        7
                    ),
                    {
                        background:
                            model.failed > 0 && !model.active
                                ? 'error'
                                : 'action',
                        radius: 3.5
                    }
                )
            ]
        })
    );
    metrics.forEach(([title, value], index) =>
        children.push(
            node(
                'Box',
                'repositorySyncMetric_' + index,
                rect(
                    12 + (index % columns) * (cellWidth + gap),
                    61 + Math.floor(index / columns) * 56,
                    cellWidth,
                    48
                ),
                {
                    background: 'surfaceContainerHigh',
                    radius: 12,
                    children: [
                        label(
                            'repositorySyncMetricTitle_' + index,
                            rect(10, 5, cellWidth - 20, 18),
                            tr(title),
                            {
                                fontRole: 'secondary',
                                weight: 600,
                                color: 'secondaryText'
                            }
                        ),
                        label(
                            'repositorySyncMetricValue_' + index,
                            rect(10, 25, cellWidth - 20, 18),
                            String(value || '—'),
                            { fontRole: 'secondary', weight: 600 }
                        )
                    ]
                }
            )
        )
    );
    const height = 61 + Math.ceil(metrics.length / columns) * 56 + 4;
    return {
        height,
        nodes: [
            node('Box', 'repositorySyncSummary', rect(0, 0, width, height), {
                background: 'panel',
                border: 'outlineVariant',
                radius: 12,
                children
            })
        ]
    };
}

export function describe(model, width, height, language) {
    const tr = (text, values) => translate(text, language, values),
        compact = width < 520,
        toolbarHeight = compact ? 92 : 50,
        footerHeight = 42,
        nodes = [
            node('Box', 'repositorySyncBackground', rect(0, 0, width, height), {
                background: 'workspace'
            })
        ],
        toolbar = [
            node('Icon', 'repositorySyncHeadingIcon', rect(11, 17, 16, 16), {
                icon: 'repository-sync',
                color: 'action'
            })
        ],
        status = model.discovering
            ? discovery(model, language)
            : model.discoveryState === 'failed'
              ? tr('Repository discovery failed')
              : model.active > 0
                ? tr('{count} active downloads', { count: model.active })
                : tr('{count} files in queue', { count: model.count });
    toolbar.push(
        label(
            'repositorySyncStatusLabel',
            rect(34, 5, Math.max(0, width - (compact ? 46 : 300)), 40),
            status,
            { weight: 600 }
        )
    );
    const actionY = compact ? 50 : 11;
    let x = width - 40;
    toolbar.push(
        button(
            'repositorySyncClear',
            rect(x, actionY, 28, 28),
            tr('Clear completed downloads'),
            'delete',
            { type: 'clear' },
            true,
            { iconOnly: true, iconAction: true }
        )
    );
    x -= compact ? 124 : 150;
    toolbar.push(
        captionedSwitch(
            'repositorySyncAutoClean',
            rect(x, actionY - 2, compact ? 116 : 142, 32),
            {
                text: tr('Auto-clean'),
                checked: !!model.autoClean,
                action: { type: 'autoClean' },
                toolTip: tr('Auto-clean completed repository downloads')
            }
        )
    );
    x -= 36;
    toolbar.push(
        button(
            'repositorySyncStart',
            rect(x, actionY, 28, 28),
            tr('Start checked downloads'),
            'sync',
            { type: 'start' },
            true,
            { iconOnly: true, iconAction: true }
        )
    );
    if (model.discovering && model.discoveryMode === 'partial') {
        x -= 36;
        toolbar.push(
            button(
                'repositorySyncStopDiscovery',
                rect(x, actionY, 28, 28),
                tr('Stop discovering more files'),
                'close',
                { type: 'stopDiscovery' },
                true,
                { iconOnly: true, iconAction: true, destructive: true }
            )
        );
    }
    if (model.discovering || model.active > 0)
        toolbar.push(
            node(
                'View',
                'repositorySyncBusy',
                rect(compact ? 11 : Math.max(0, x - 32), actionY + 2, 24, 24),
                { view: 'busy', label: tr('Working…') }
            )
        );
    nodes.push(
        node('Box', 'repositorySyncToolbar', rect(0, 0, width, toolbarHeight), {
            background: 'panel',
            children: toolbar
        })
    );
    let top = toolbarHeight + 8;
    if (model.discovering || model.total > 0 || model.count > 0) {
        const card = summary(model, Math.max(0, width - 16), language);
        nodes.push(
            node(
                'Box',
                'repositorySyncSummarySlot',
                rect(8, top, width - 16, card.height),
                { children: card.nodes }
            )
        );
        top += card.height + 7;
    }
    const queueHeight = Math.max(0, height - footerHeight - top - 7);
    nodes.push(
        node(
            'View',
            'repositorySyncQueue',
            rect(7, top, Math.max(0, width - 14), queueHeight),
            { view: 'queue' }
        )
    );
    if (!model.count)
        nodes.push(
            label(
                'repositorySyncEmpty',
                rect(
                    19,
                    top + Math.max(0, (queueHeight - 64) / 2),
                    width - 38,
                    64
                ),
                model.discovering
                    ? discovery(model, language)
                    : model.discoveryState === 'failed'
                      ? model.discoveryError
                      : tr(
                            model.total > 0
                                ? 'Completed rows were cleared; the batch summary is retained'
                                : 'Repository Sync queue is empty'
                        ),
                Object.assign({}, muted, {
                    wrap: true,
                    align: 'center',
                    color:
                        model.discoveryState === 'failed'
                            ? 'error'
                            : 'secondaryText'
                })
            )
        );
    const message =
        model.active > 0
            ? tr(
                  'Background transfers are active — the interface remains responsive'
              )
            : model.failed > 0
              ? tr('{count} failed downloads', { count: model.failed })
              : tr(
                    'Files are verified before downloading and written atomically'
                );
    nodes.push(
        node(
            'Box',
            'repositorySyncFooter',
            rect(0, Math.max(0, height - footerHeight), width, footerHeight),
            {
                background: 'panel',
                children: [
                    label(
                        'repositorySyncFooterMessage',
                        rect(11, 3, width - 22, footerHeight - 6),
                        message,
                        {
                            fontRole: 'secondary',
                            color: 'secondaryText',
                            wrap: true
                        }
                    )
                ]
            }
        )
    );
    return { nodes };
}

export function row(record, index, width, language) {
    const tr = (text) => translate(text, language),
        phase = record.phase,
        color =
            phase === 'failed'
                ? 'error'
                : phase === 'completed'
                  ? 'green'
                  : phase === 'cancelled'
                    ? 'secondaryText'
                    : 'cyan',
        state = record.alreadyExists
            ? 'Local'
            : phase === 'completed'
              ? 'Completed'
              : phase === 'downloading'
                ? 'Downloading'
                : phase === 'failed'
                  ? 'Failed'
                  : phase === 'cancelled'
                    ? 'Cancelled'
                    : 'Queued',
        narrow = width < 520,
        actionX = width - 36,
        textWidth = Math.max(0, width - 96 - (narrow ? 0 : 142)),
        children = [
            node(
                'CheckBox',
                'repositorySyncCheck_' + record.taskId,
                rect(6, 22, 28, 28),
                {
                    label: tr('Select file'),
                    checked: !!record.checked,
                    action: { type: 'check', index, key: record.taskId },
                    indicatorX: 4
                }
            ),
            node(
                'Icon',
                'repositorySyncIcon_' + record.taskId,
                rect(39, 30, 15, 15),
                {
                    icon:
                        phase === 'failed'
                            ? 'priority-high'
                            : phase === 'cancelled'
                              ? 'cancel'
                              : phase === 'completed'
                                ? 'check-circle'
                                : 'repository-sync',
                    color
                }
            ),
            label(
                'repositorySyncTitle_' + record.taskId,
                rect(62, 6, textWidth, 21),
                record.title,
                { weight: 500 }
            ),
            label(
                'repositorySyncMessage_' + record.taskId,
                rect(62, 29, textWidth, 19),
                (record.process ? record.process + ' · ' : '') +
                    (record.error || record.progress || ''),
                {
                    fontRole: 'secondary',
                    color: phase === 'failed' ? 'error' : 'secondaryText'
                }
            ),
            label(
                'repositorySyncPath_' + record.taskId,
                rect(62, 50, textWidth, 18),
                record.localPath || '',
                {
                    fontRole: 'caption',
                    monospace: true,
                    color: 'secondaryText',
                    opacity: 0.72,
                    elideMiddle: true,
                    toolTip: record.localPath || ''
                }
            )
        ];
    if (!narrow) {
        children.push(
            label(
                'repositorySyncState_' + record.taskId,
                rect(width - 172, 10, 130, 24),
                tr(state),
                {
                    fontRole: 'caption',
                    weight: 600,
                    color:
                        phase === 'failed'
                            ? 'error'
                            : phase === 'completed'
                              ? 'green'
                              : 'secondaryText',
                    align: 'right'
                }
            )
        );
        children.push(
            label(
                'repositorySyncSpeed_' + record.taskId,
                rect(width - 172, 38, 130, 24),
                record.speed || '',
                {
                    fontRole: 'caption',
                    color: 'secondaryText',
                    align: 'right',
                    monospace: true
                }
            )
        );
    }
    if (phase === 'failed' || phase === 'cancelled')
        children.push(
            button(
                'repositorySyncRetry_' + record.taskId,
                rect(actionX, 24, 28, 28),
                tr('Retry'),
                'refresh',
                { type: 'retry', index, key: record.taskId },
                true,
                { iconOnly: true, iconAction: true }
            )
        );
    if (record.active)
        children.push(
            button(
                'repositorySyncCancel_' + record.taskId,
                rect(actionX, 24, 28, 28),
                tr('Cancel'),
                'close',
                { type: 'cancel', index, key: record.taskId },
                true,
                { iconOnly: true, iconAction: true, destructive: true }
            )
        );
    if (record.active)
        children.push(
            node(
                'Box',
                'repositorySyncRowProgress_' + record.taskId,
                rect(
                    1,
                    73,
                    (width - 2) *
                        Math.max(0, Math.min(1, record.progressValue || 0)),
                    3
                ),
                { background: 'action', radius: 1.5 }
            )
        );
    return {
        nodes: [
            node(
                'Box',
                'repositorySyncRow_' + record.taskId,
                rect(0, 0, width, 76),
                {
                    background: record.active
                        ? 'surfaceContainerHigh'
                        : record.hovered
                          ? 'rowHover'
                          : 'panel',
                    border: record.active ? 'action' : 'outlineVariant',
                    radius: 9,
                    contextAction: { type: 'menu', index, key: record.taskId },
                    children
                }
            )
        ]
    };
}

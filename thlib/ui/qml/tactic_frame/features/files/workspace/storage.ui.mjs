import { node, rect, label, button } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { captionHeight } from '../../../controls/forms/sections.ui.mjs';
import { describe as confirmation } from '../../../controls/feedback/confirmation.ui.mjs';

export const fields = [
    ['bytes_limit', 'Byte quota', 'Zero means unlimited.'],
    ['files_limit', 'File quota', 'Zero means unlimited.'],
    ['max_parallel', 'Parallel transfers', 'From 1 to 16.'],
    [
        'upload_retention_seconds',
        'Unfinished uploads (seconds)',
        'Zero disables expiration.'
    ],
    [
        'reverted_retention_seconds',
        'Reverted changelists (seconds)',
        'Zero disables expiration.'
    ],
    [
        'task_retention_seconds',
        'Completed tasks (seconds)',
        'Zero disables expiration.'
    ],
    [
        'shelf_retention_seconds',
        'Shelved changelists (seconds)',
        'Zero disables expiration.'
    ],
    [
        'gc_grace_seconds',
        'Quarantine before deletion (seconds)',
        'Unreferenced contents stay in quarantine before physical deletion.'
    ],
    [
        'gc_interval_seconds',
        'Automatic GC interval (seconds)',
        'Zero disables automatic cleanup.'
    ]
];

export function size(value) {
    for (const unit of ['B', 'KB', 'MB', 'GB', 'TB']) {
        if (value < 1024 || unit === 'TB')
            return value.toFixed(unit === 'B' ? 0 : 1) + ' ' + unit;
        value /= 1024;
    }
}

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language),
        status = model.status || {},
        policy = model.draft?.policy,
        gc = status.gc || {},
        active = ['queued', 'running'].includes(gc.state);
    const inner = Math.max(0, Math.min(660, width - 32)),
        body = [];
    let y = 0;
    function text(id, value, heading = false, color = 'secondaryText') {
        const h = Math.max(
            heading ? 28 : 22,
            captionHeight(value, inner) * 1.2
        );
        body.push(
            label(id, rect(0, y, inner, h), value, {
                wrap: true,
                fontRole: heading ? 'title' : 'body',
                weight: heading ? 600 : 400,
                color: heading ? 'primaryText' : color
            })
        );
        y += h + 8;
    }
    function actions(items) {
        const columns = inner < 460 ? 1 : 2,
            w = (inner - (columns - 1) * 8) / columns;
        for (const [index, item] of items.entries())
            body.push(
                button(
                    item.id,
                    rect(
                        (index % columns) * (w + 8),
                        y + Math.floor(index / columns) * 46,
                        w,
                        38
                    ),
                    tr(item.text),
                    item.icon || '',
                    item.action,
                    item.enabled !== false
                )
            );
        y += Math.ceil(items.length / columns) * 46;
    }
    text('workspaceStorageTitle', tr('Storage administration'), true);
    text(
        'workspaceStorageUsage',
        size(status.allocated_bytes || 0) +
            ' · ' +
            (status.allocated_files || 0) +
            ' ' +
            tr('files') +
            ' · ' +
            tr(
                status.indexed
                    ? 'Storage index complete'
                    : 'Storage index incomplete'
            )
    );
    const top = [
        {
            id: 'workspaceStorageRefresh',
            text: 'Refresh',
            icon: 'refresh',
            action: { type: 'action', operation: 'storage_status' },
            enabled: !model.busy
        }
    ];
    if (!status.initialized)
        top.push({
            id: 'workspaceStorageInitialize',
            text: 'Initialize storage',
            action: { type: 'action', operation: 'storage_upgrade' },
            enabled: !model.busy
        });
    if (status.initialized && !status.indexed)
        top.push({
            id: 'workspaceStorageIndex',
            text: 'Continue storage index',
            action: { type: 'action', operation: 'storage_index' },
            enabled: !model.busy
        });
    if (model.indexing && model.busy)
        top.push({
            id: 'workspaceStorageStop',
            text: 'Stop waiting',
            icon: 'close',
            action: { type: 'stop' }
        });
    actions(top);
    if (!status.indexed)
        text(
            'workspaceStorageIndexNotice',
            tr(
                'Finish indexing before editing the policy or running GC. Indexing can be stopped and continued.'
            ) +
                (status.index_table === undefined
                    ? ''
                    : '\n' +
                      tr('Table') +
                      ': ' +
                      status.index_table +
                      ' · ' +
                      (status.index_after || ''))
        );
    if (model.notice)
        text('workspaceStorageNotice', model.notice, false, 'error');
    if (policy) {
        for (const [index, [key, title, hint]] of fields.entries()) {
            if (index === 0 || index === 3)
                text(
                    'workspaceStorageSection' + index,
                    tr(index === 0 ? 'Quotas' : 'Retention and cleanup'),
                    true
                );
            text('workspaceStorageFieldLabel' + index, tr(title));
            body.push(
                node('Field', 'storagePolicy_' + key, rect(0, y, inner, 38), {
                    text: String(policy[key] ?? ''),
                    label: tr(title),
                    inputMode: 'numeric',
                    enabled: !model.busy && !!status.indexed,
                    action: { type: 'field', key }
                })
            );
            y += 46;
            text('workspaceStorageFieldHint' + index, tr(hint));
        }
        actions([
            {
                id: 'workspaceStorageReset',
                text: 'Reset',
                icon: 'undo',
                action: { type: 'reset' },
                enabled: !model.busy
            },
            {
                id: 'workspaceStorageSave',
                text: 'Save storage policy',
                icon: 'content-save',
                action: { type: 'save' },
                enabled: !model.busy && !!status.indexed
            }
        ]);
    }
    text('workspaceStorageGcTitle', tr('Garbage collection'), true);
    text(
        'workspaceStorageGcHelp',
        tr(
            'Dry run counts unused objects without deleting them. Safe GC expires retained records and quarantines unused contents according to the saved policy.'
        )
    );
    if (!model.filesService)
        text(
            'workspaceStorageGcService',
            tr('Enable the files service on the server to process GC tasks.')
        );
    const canGc =
        !model.busy && !!status.indexed && !!model.filesService && !active;
    const gcActions = [
        {
            id: 'workspaceStorageDryRun',
            text: 'GC dry run',
            enabled: canGc,
            action: { type: 'action', operation: 'gc_begin', dry: true }
        },
        {
            id: 'workspaceStorageGc',
            text: 'Run safe GC',
            enabled: canGc,
            action: { type: 'confirmGc' }
        }
    ];
    if (active)
        gcActions.push({
            id: 'workspaceStorageGcCancel',
            text: 'Cancel GC',
            icon: 'close',
            enabled: !model.busy,
            action: { type: 'action', operation: 'gc_cancel' }
        });
    actions(gcActions);
    if (gc.code)
        text(
            'workspaceStorageGcStatus',
            gc.code +
                ' · ' +
                tr(gc.state || '') +
                ' · ' +
                (gc.phase || '') +
                ' · ' +
                tr(gc.dry_run ? 'GC dry run' : 'Run safe GC') +
                '\n' +
                tr('Objects scanned') +
                ': ' +
                (gc.objects_done || 0) +
                ' · ' +
                tr('Candidates') +
                ': ' +
                (gc.candidates || 0) +
                ' · ' +
                size(gc.candidate_bytes || 0) +
                '\n' +
                tr('Expired records') +
                ': ' +
                (gc.expired || 0) +
                ' · ' +
                tr('Quarantined') +
                ': ' +
                (gc.quarantined || 0) +
                ' · ' +
                tr('Purged') +
                ': ' +
                (gc.purged || 0)
        );
    if (gc.error) text('workspaceStorageGcError', gc.error, false, 'error');
    if (gc.state === 'error')
        text(
            'workspaceStorageGcRecovery',
            tr(
                'GC stopped. After fixing the cause, start a new dry run or safe GC.'
            )
        );
    return {
        nodes: [
            node(
                'Box',
                'workspaceStorageBackground',
                rect(0, 0, width, height),
                { background: 'panelDeep', radius: 14 }
            ),
            node(
                'Scroll',
                'workspaceStorageScroll',
                rect(8, 8, Math.max(0, width - 16), Math.max(0, height - 16)),
                {
                    scrollbarId: 'workspaceStorageScrollBar',
                    contentHeight: y + 8,
                    children: body
                }
            )
        ]
    };
}

export function confirm(model, width, height, language) {
    return confirmation(
        {
            message: translate(
                'Run safe GC using the configured retention policy?',
                language
            ),
            accept: 'Run safe GC',
            busy: !!model.busy
        },
        width,
        height,
        language
    );
}

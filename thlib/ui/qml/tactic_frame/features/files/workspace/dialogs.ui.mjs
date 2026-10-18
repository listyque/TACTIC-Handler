import { node, rect, label, button } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { captionHeight } from '../../../controls/forms/sections.ui.mjs';
import { buttonWidth } from '../../../controls/buttons/metrics.mjs';
import { columnTitles } from './presentation.mjs';
export { buttonWidth };

export function confirmationTitle(action, language) {
    return translate(
        action === 'revert'
            ? 'Revert changelist'
            : ['query_revert', 'remove_files'].includes(action)
              ? 'Remove files'
              : action === 'delete_local'
                ? 'Move to Trash'
                : ['mark_delete', 'query_delete'].includes(action)
                  ? 'Mark for deletion'
                  : 'Delete',
        language
    );
}

export function editorTitle(kind, language) {
    return translate(
        {
            offer_change: 'Recipient login',
            goto_change: 'Changelist number',
            local_root: 'Local workspace root',
            rename_file: 'New depot path',
            move_files: 'Target changelist',
            merge_begin: 'Merge source stream'
        }[kind] || 'Shelf changelist',
        language
    );
}

export function promptContent(kind, model, language) {
    const tr = (text) => translate(text, language),
        actions = [];
    let message = '',
        messageId = 'workspacePromptMessage';
    if (kind === 'blocked') {
        message = model.message || '';
        actions.push({
            id: 'workspaceDropBlockedOk',
            text: 'OK',
            type: 'accept',
            highlighted: true
        });
    } else if (kind === 'drop') {
        message =
            tr('Selected items: {count}').replace('{count}', model.count || 0) +
            '\n' +
            tr(
                model.origin === 'move'
                    ? 'Move selected files between pending changelists. Local files are kept.'
                    : model.origin === 'shelf'
                      ? 'Restore shelved files into this changelist. Review conflicts before Submit.'
                      : 'Open selected files for editing in this changelist. Missing local copies will be downloaded; existing local files are kept.'
            );
        messageId = 'workspaceDropDescription';
        actions.push(
            { id: 'workspaceDropCancel', text: 'Cancel', type: 'reject' },
            {
                id: 'workspaceDropAddButton',
                text: 'Add',
                type: 'accept',
                icon: 'add',
                highlighted: true
            }
        );
    } else if (kind === 'nonempty') {
        message = tr(
            'Move all files to another changelist, then delete the empty changelist. Or revert this changelist; it will appear in Reverted. Local files are kept.'
        );
        actions.push(
            { id: 'workspaceNonemptyCancel', text: 'Cancel', type: 'reject' },
            {
                id: 'workspaceMoveAllFiles',
                text: 'Move files…',
                type: 'move',
                icon: 'swap-horizontal'
            },
            {
                id: 'workspaceRevertAllFiles',
                text: 'Revert changelist',
                type: 'revert',
                icon: 'undo'
            }
        );
    } else if (kind === 'switch') {
        message =
            tr(
                'Pending changes and server tasks remain in the previous workspace. Local files are kept.'
            ) +
            '\n' +
            (model.previous || '') +
            ' → ' +
            (model.workspace || '');
        actions.push(
            { id: 'workspaceSwitchCancel', text: 'Cancel', type: 'reject' },
            {
                id: 'workspaceSwitchAccept',
                text: 'OK',
                type: 'accept',
                highlighted: true
            }
        );
    } else if (kind === 'confirm') {
        const action = model.action,
            targets = model.targets || [];
        if (action === 'delete_change')
            message =
                tr(
                    'Delete {count} changelist(s) / shelf(s)? Local files are kept. Shelved contents will no longer be available. The whole selection is deleted together.'
                ).replace('{count}', targets.length) +
                '\n' +
                targets
                    .slice(0, 10)
                    .map((row) => '#' + row.number)
                    .join(', ') +
                (targets.length > 10 ? '…' : '');
        else if (['query_delete', 'query_revert'].includes(action))
            message = tr(
                'Apply the pinned query to all matching server files? The batch is atomic; local files are kept.'
            );
        else if (
            [
                'mark_delete',
                'delete_local',
                'delete_shelf_files',
                'remove_files'
            ].includes(action)
        )
            message = tr(
                'Confirm {operation} for the selected items? Local changes may be affected.'
            ).replace(
                '{operation}',
                tr(
                    action === 'mark_delete'
                        ? 'depot deletion on submit'
                        : action === 'delete_local'
                          ? 'moving local copies to Trash'
                          : 'removing files from the changelist'
                )
            );
        else message = tr('Revert the changelist? Local files will be kept.');
        messageId = 'workspaceConfirmationMessage';
        actions.push(
            {
                id: 'workspaceConfirmationCancel',
                text: 'Cancel',
                type: 'reject'
            },
            {
                id: 'workspaceConfirmationAccept',
                text:
                    action === 'revert'
                        ? 'Revert'
                        : confirmationTitle(action, language),
                type: 'accept',
                icon: action === 'revert' ? 'undo' : 'delete',
                destructive: true
            }
        );
    } else throw Error('Unknown workspace prompt: ' + kind);
    return {
        message,
        messageId,
        actions: actions.map((action) =>
            Object.assign({}, action, { text: tr(action.text) })
        )
    };
}

export function promptMetrics(kind, model, width, language) {
    const content = promptContent(kind, model, language);
    const widths = content.actions.map((action, index) =>
        Math.min(
            width,
            model.buttonWidths?.[index] ||
                buttonWidth(action.text.length * 7, !!action.icon)
        )
    );
    const total =
        widths.reduce((sum, value) => sum + value, 0) + (widths.length - 1) * 8;
    const stacked = total > width;
    return {
        widths,
        total,
        stacked,
        footer: (stacked ? widths.length : 1) * 44,
        messageHeight: Math.max(
            40,
            captionHeight(content.message, Math.max(0, width - 16)) * 1.3
        )
    };
}

export function promptHeight(kind, model, width, language) {
    const metrics = promptMetrics(kind, model, width, language);
    return metrics.messageHeight + metrics.footer + 8;
}

export function prompt(kind, model, width, height, language) {
    const content = promptContent(kind, model, language),
        metrics = promptMetrics(kind, model, width, language),
        body = [
            label(
                content.messageId,
                rect(0, 0, Math.max(0, width - 16), metrics.messageHeight),
                content.message,
                {
                    wrap: true,
                    color:
                        kind === 'drop' || kind === 'nonempty'
                            ? 'primaryText'
                            : 'secondaryText'
                }
            )
        ];
    const nodes = [
        node(
            'Scroll',
            'workspacePromptScroll',
            rect(0, 0, width, Math.max(0, height - metrics.footer - 8)),
            {
                scrollbarId: 'workspacePromptScrollBar',
                contentHeight: metrics.messageHeight,
                children: body
            }
        )
    ];
    let x = Math.max(0, width - metrics.total);
    for (const [index, action] of content.actions.entries()) {
        const w = metrics.widths[index];
        nodes.push(
            button(
                action.id,
                rect(
                    metrics.stacked ? width - w : x,
                    height -
                        metrics.footer +
                        (metrics.stacked ? index * 44 : 0),
                    w,
                    38
                ),
                action.text,
                action.icon || '',
                { type: action.type },
                action.type === 'reject' || kind === 'blocked' || !model.busy,
                {
                    highlighted: !!action.highlighted,
                    destructive: !!action.destructive
                }
            )
        );
        x += w + 8;
    }
    return { nodes };
}

export function editor(model, width, height, language) {
    const tr = (text) => translate(text, language),
        inner = Math.max(0, width - 16),
        stacked = width < 320,
        footer = stacked ? 90 : 44,
        w = stacked ? width : (width - 8) / 2;
    return {
        nodes: [
            node(
                'Area',
                'workspaceEditorValue',
                rect(0, 0, inner, Math.max(40, height - footer - 12)),
                {
                    text: model.draft || '',
                    label: editorTitle(model.kind, language),
                    placeholder: ['move_files', 'unshelve_begin'].includes(
                        model.kind
                    )
                        ? tr('Changelist number, e.g. #42')
                        : '',
                    action: { type: 'draft' }
                }
            ),
            button(
                'workspaceEditorCancel',
                rect(0, height - footer, w, 38),
                tr('Cancel'),
                'close',
                { type: 'reject' },
                true
            ),
            button(
                'workspaceEditorSave',
                rect(
                    stacked ? 0 : w + 8,
                    height - footer + (stacked ? 46 : 0),
                    w,
                    38
                ),
                tr('Save'),
                'save',
                { type: 'accept' },
                !model.busy
            )
        ]
    };
}

export function validColumnWidth(value) {
    return (
        /^[0-9]+$/.test(String(value)) &&
        Number(value) >= 48 &&
        Number(value) <= 900
    );
}

export function columns(model, width, height, language) {
    const tr = (text) => translate(text, language),
        inner = Math.max(0, width - 16),
        body = [];
    let y = 0;
    if (model.notice) {
        const h = Math.max(36, captionHeight(model.notice, inner) * 1.2);
        body.push(
            label(
                'workspaceColumnsNotice',
                rect(0, y, inner, h),
                model.notice,
                { color: 'error', wrap: true }
            )
        );
        y += h + 8;
    }
    for (const row of model.columns || []) {
        const narrow = inner < 420,
            h = narrow ? 80 : 46,
            children = [],
            caption = tr(columnTitles[row.key] || row.key);
        children.push(
            node(
                'CheckBox',
                'workspaceColumnVisible_' + row.key,
                rect(0, 0, narrow ? inner : Math.max(0, inner - 152), 38),
                {
                    text: caption,
                    checked: !!row.visible,
                    enabled: row.key !== 'path',
                    wrapText: true,
                    action: { type: 'visible', key: row.key }
                }
            )
        );
        const x = narrow ? 0 : inner - 144,
            top = narrow ? 40 : 0,
            value = Object.prototype.hasOwnProperty.call(
                model.widths || {},
                row.key
            )
                ? model.widths[row.key]
                : String(row.width);
        children.push(
            node(
                'Field',
                'workspaceColumnWidth_' + row.key,
                rect(x, top, 70, 38),
                {
                    text: value,
                    label: tr('Column width'),
                    inputMode: 'numeric',
                    error: !validColumnWidth(value),
                    action: { type: 'widthDraft', key: row.key },
                    activateAction: { type: 'width', key: row.key }
                }
            )
        );
        children.push(
            button(
                'workspaceColumnLeft_' + row.key,
                rect(x + 78, top + 5, 28, 28),
                tr('Move column left'),
                'arrow-up',
                { type: 'move', key: row.key, value: -1 },
                true,
                { iconOnly: true, iconAction: true }
            )
        );
        children.push(
            button(
                'workspaceColumnRight_' + row.key,
                rect(x + 110, top + 5, 28, 28),
                tr('Move column right'),
                'arrow-down',
                { type: 'move', key: row.key, value: 1 },
                true,
                { iconOnly: true, iconAction: true }
            )
        );
        body.push(
            node('Box', 'workspaceColumn_' + row.key, rect(0, y, inner, h), {
                children
            })
        );
        y += h;
    }
    return {
        nodes: [
            node(
                'Scroll',
                'workspaceColumnsBody',
                rect(0, 0, width, Math.max(0, height - 52)),
                {
                    contentHeight: y,
                    scrollbarId: 'workspaceColumnsScrollBar',
                    children: body
                }
            ),
            button(
                'workspaceColumnsClose',
                rect(Math.max(0, width - 110), height - 44, 110, 38),
                tr('Close'),
                'close',
                { type: 'close' },
                true
            )
        ]
    };
}

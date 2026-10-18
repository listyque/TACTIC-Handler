import { node, rect, label, button } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { captionHeight } from '../../../controls/forms/sections.ui.mjs';

function surface(body, footer, width, height, contentHeight) {
    const rows = width < 320 ? footer.length : 1;
    const footerHeight = rows * 44;
    const buttonWidth =
        rows > 1 ? width : (width - (footer.length - 1) * 8) / footer.length;
    return {
        nodes: [
            node(
                'Scroll',
                'workspaceFormScroll',
                rect(0, 0, width, Math.max(0, height - footerHeight - 8)),
                {
                    scrollbarId: 'workspaceFormScrollBar',
                    contentHeight,
                    children: body
                }
            ),
            ...footer.map((item, index) =>
                button(
                    item.id,
                    rect(
                        rows > 1 ? 0 : index * (buttonWidth + 8),
                        height - footerHeight + (rows > 1 ? index * 44 : 0),
                        buttonWidth,
                        38
                    ),
                    item.text,
                    item.icon || '',
                    { type: item.type },
                    item.enabled !== false,
                    {
                        highlighted: !!item.highlighted,
                        destructive: !!item.destructive
                    }
                )
            )
        ]
    };
}

export function revert(model, width, height, language) {
    const tr = (text) => translate(text, language),
        inner = Math.max(0, width - 16);
    let y = 0;
    const body = [];
    for (const [id, text, color] of [
        ['Caption', model.caption, 'secondaryText'],
        [
            'Message',
            tr(
                'Revert pending changes. Local files are kept unless deletion is selected.'
            ),
            'primaryText'
        ]
    ]) {
        const h = Math.max(28, captionHeight(text || '', inner) * 1.2);
        body.push(
            label('workspaceRevert' + id, rect(0, y, inner, h), text || '', {
                wrap: true,
                color
            })
        );
        y += h + 12;
    }
    const checkHeight = Math.max(
        32,
        captionHeight(tr('Delete files not in depot'), inner - 32) * 1.2
    );
    body.push(
        node(
            'CheckBox',
            'workspaceRevertDeleteNew',
            rect(0, y, inner, checkHeight),
            {
                text: tr('Delete files not in depot'),
                wrapText: true,
                checked: !!model.deleteNew,
                action: { type: 'deleteNew' }
            }
        )
    );
    y += checkHeight + 12;
    if (model.deleteNew) {
        const text = tr(
            'Only newly added local files absent from the published stream will be moved to Trash after the server revert succeeds.'
        );
        const h = Math.max(60, captionHeight(text, inner) * 1.2);
        body.push(
            label('workspaceRevertWarning', rect(0, y, inner, h), text, {
                wrap: true,
                color: 'secondaryText'
            })
        );
        y += h + 8;
    }
    return surface(
        body,
        [
            { id: 'workspaceRevertCancel', text: tr('Cancel'), type: 'reject' },
            {
                id: 'workspaceRevertAccept',
                text: tr('Revert'),
                icon: 'undo',
                type: 'accept',
                enabled: !model.busy,
                destructive: true
            }
        ],
        width,
        height,
        y
    );
}

export function validRevision(model) {
    return (
        model.selector === '' ||
        (model.selector === 'at_date'
            ? !!String(model.value || '').trim()
            : /^[0-9]+$/.test(model.value || '') &&
              Number(model.value) >= (model.selector === 'revision' ? 0 : 1))
    );
}

export function revision(model, width, height, language) {
    const tr = (text) => translate(text, language),
        inner = Math.max(0, width - 16),
        body = [];
    const targetHeight = Math.max(
        30,
        captionHeight(model.target || '', inner) * 1.2
    );
    body.push(
        label(
            'workspaceRevisionTarget',
            rect(0, 0, inner, targetHeight),
            model.target || '',
            { wrap: true, wrapAnywhere: true }
        )
    );
    let y = targetHeight + 12;
    body.push(
        node('Choice', 'workspaceRevisionSelector', rect(0, y, inner, 38), {
            label: tr('Revision selector'),
            value: model.selector,
            options: [
                ['', 'Latest'],
                ['file_revision', 'File revision (each file)'],
                ['changelist', 'Submitted changelist'],
                ['at_date', 'As of date / time'],
                ['revision', 'Stream revision']
            ].map(([value, label]) => ({ value, label: tr(label) })),
            action: { type: 'selector' }
        })
    );
    y += 50;
    if (model.selector) {
        body.push(
            node('Field', 'workspaceRevisionValue', rect(0, y, inner, 38), {
                text: model.value || '',
                label: tr('Revision number or date'),
                placeholder: tr(
                    model.selector === 'at_date'
                        ? 'YYYY-MM-DD or ISO date / time'
                        : 'Number'
                ),
                action: { type: 'value' }
            })
        );
        y += 50;
    }
    const message = tr(
        model.selector === 'at_date'
            ? 'Without a timezone, UTC is used. A date includes the whole UTC day.'
            : model.selector === 'file_revision'
              ? 'Files without this revision are left unchanged and reported in the Log.'
              : 'Changelist and stream revision select the complete submitted state of the selected stream.'
    );
    const messageHeight = Math.max(42, captionHeight(message, inner) * 1.2);
    body.push(
        label(
            'workspaceRevisionExplanation',
            rect(0, y, inner, messageHeight),
            message,
            { wrap: true, color: 'secondaryText' }
        )
    );
    y += messageHeight + 12;
    const forceText = tr('Force overwrite local files'),
        checkHeight = Math.max(32, captionHeight(forceText, inner - 32) * 1.2);
    body.push(
        node(
            'CheckBox',
            'workspaceRevisionForce',
            rect(0, y, inner, checkHeight),
            {
                text: forceText,
                wrapText: true,
                checked: !!model.force,
                action: { type: 'force' }
            }
        )
    );
    y += checkHeight + 12;
    if (model.force) {
        const text = tr(
                'Force replaces modified files and removes files absent from the selected state. Preserve your local changes first.'
            ),
            h = Math.max(60, captionHeight(text, inner) * 1.2);
        body.push(
            label('workspaceRevisionWarning', rect(0, y, inner, h), text, {
                wrap: true,
                color: 'error'
            })
        );
        y += h + 12;
    }
    return surface(
        body,
        [
            {
                id: 'workspaceRevisionCancel',
                text: tr('Cancel'),
                type: 'reject'
            },
            {
                id: 'workspaceRevisionAccept',
                text: tr('Get'),
                icon: 'cloud-download',
                type: 'accept',
                enabled: validRevision(model) && !model.busy
            }
        ],
        width,
        height,
        y
    );
}

export function shelf(model, width, height, language) {
    const tr = (text) => translate(text, language),
        inner = Math.max(0, width - 16);
    const message = tr(
            'Select a permitted shelf in the same stream. Replacing it preserves its previous contents.'
        ),
        textHeight = Math.max(54, captionHeight(message, inner) * 1.2);
    const body = [
        node('Choice', 'workspaceShelfChoice', rect(0, 0, inner, 38), {
            label: tr('Shelved changelist'),
            options: model.options || [],
            value: model.code || '',
            enabled: !model.busy,
            action: { type: 'shelf' }
        }),
        label(
            'workspaceShelfMessage',
            rect(0, 50, inner, textHeight),
            message,
            { wrap: true, color: 'secondaryText' }
        )
    ];
    if (model.after)
        body.push(
            button(
                'workspaceShelfMore',
                rect(0, 62 + textHeight, inner, 38),
                tr('Next shelves'),
                'chevron-right',
                { type: 'more' },
                !model.busy
            )
        );
    return surface(
        body,
        [
            { id: 'workspaceShelfCancel', text: tr('Cancel'), type: 'reject' },
            {
                id: 'workspaceTargetAccept',
                text: tr('Continue'),
                icon: 'check',
                type: 'accept',
                enabled: !model.busy && !!model.code,
                highlighted: true
            }
        ],
        width,
        height,
        62 + textHeight + (model.after ? 50 : 0)
    );
}

export function target(model, width, height, language) {
    const tr = (text) => translate(text, language),
        inner = Math.max(0, width - 16),
        body = [];
    body.push(
        node('Choice', 'workspaceTargetChoice', rect(0, 0, inner, 38), {
            label: tr('Target changelist'),
            value: model.target || '',
            options: model.options || [],
            enabled: !model.creating && !model.busy,
            action: { type: 'target' }
        })
    );
    let y = 50;
    if (model.operation === 'apply_reconcile') {
        const message = tr(
                'Review selected add, edit, delete and rename operations. Local files are kept.'
            ),
            h = Math.max(48, captionHeight(message, inner) * 1.2);
        body.push(
            label('workspaceTargetMessage', rect(0, y, inner, h), message, {
                wrap: true,
                color: 'secondaryText'
            })
        );
        y += h + 8;
        body.push(
            node('List', 'workspaceTargetPreview', rect(0, y, inner, 160), {
                source: 'targetFiles',
                keyField: 'path',
                rowHeight: 32,
                scrollbarId: 'workspaceTargetPreviewScrollBar'
            })
        );
        y += 172;
    }
    const text = tr('Create a new changelist'),
        h = Math.max(32, captionHeight(text, inner - 32) * 1.2);
    body.push(
        node('CheckBox', 'workspaceTargetCreate', rect(0, y, inner, h), {
            text,
            checked: !!model.creating,
            wrapText: true,
            enabled: !model.busy,
            action: { type: 'creating' }
        })
    );
    y += h + 12;
    if (model.creating) {
        body.push(
            node('Field', 'workspaceTargetDescription', rect(0, y, inner, 38), {
                label: tr('Changelist description'),
                placeholder: tr('Changelist description'),
                text: model.description || '',
                enabled: !model.busy,
                action: { type: 'description' }
            })
        );
        y += 50;
    }
    const acceptText =
        model.operation === 'apply_reconcile'
            ? 'Add to changelist'
            : ['checkout', 'bulk_checkout'].includes(model.operation)
              ? 'Checkout'
              : 'Continue';
    return surface(
        body,
        [
            { id: 'workspaceTargetCancel', text: tr('Cancel'), type: 'reject' },
            {
                id: 'workspaceTargetAccept',
                text: tr(acceptText),
                icon: 'check',
                type: 'accept',
                enabled: !model.busy && (model.creating || !!model.target),
                highlighted: true
            }
        ],
        width,
        height,
        y
    );
}

export function targetFile(row, width) {
    return {
        nodes: [
            label(
                'workspaceTargetFile',
                rect(0, 0, width, 32),
                (row.rename_from ? row.rename_from + ' → ' : '') +
                    row.path +
                    ' · ' +
                    (row.reconcile_action || row.local_status || ''),
                { elideMiddle: true, fontRole: 'secondary', toolTip: row.path }
            )
        ]
    };
}

export function review(model, width, height, language) {
    const tr = (text) => translate(text, language),
        data = model.review || {},
        inner = Math.max(0, width - 16),
        body = [];
    let y = 0;
    function message(id, text, color = 'primaryText') {
        const h = Math.max(28, captionHeight(text, inner) * 1.2);
        body.push(label(id, rect(0, y, inner, h), text, { wrap: true, color }));
        y += h + 6;
    }
    message(
        'workspaceReviewCaption',
        data.number
            ? tr('Changelist #{number}').replace('{number}', data.number) +
                  ' · ' +
                  (data.files_unknown
                      ? (data.items || []).length
                      : data.files || 0) +
                  ' ' +
                  tr(data.files_unknown ? 'files on this page' : 'files')
            : tr('Loading')
    );
    if (data.source)
        message(
            'workspaceReviewSource',
            data.source + ' → ' + (data.target || '')
        );
    body.push(
        node('Area', 'workspaceReviewDescription', rect(0, y, inner, 70), {
            text: model.description || '',
            label: tr('Changelist description'),
            readOnly: true
        })
    );
    y += 78;
    if (data.active_transfer || data.integration || data.rebase_required)
        message(
            'workspaceReviewBlocked',
            tr(
                data.active_transfer
                    ? 'Finish or cancel the upload before submit'
                    : data.integration
                      ? 'Resolve all conflicts before submit'
                      : 'Stream head changed; rebase before submit'
            ),
            'error'
        );
    if (model.operation === 'shelve_revert')
        message(
            'workspaceReviewRevertNotice',
            tr('The shelf is saved before reverting. Local files are kept.'),
            'secondaryText'
        );
    const listHeight = Math.max(100, height - y - 110);
    body.push(
        node('List', 'workspaceReviewFiles', rect(0, y, inner, listHeight), {
            source: 'reviewFiles',
            keyField: 'path',
            rowHeight: 32,
            scrollbarId: 'workspaceReviewFilesScrollBar'
        })
    );
    y += listHeight + 6;
    body.push(
        button(
            'workspaceReviewMore',
            rect(0, y, inner, 38),
            tr('Next page'),
            'chevron-right',
            { type: 'more' },
            !model.busy && !!data.after
        )
    );
    y += 46;
    const footer = [
        { id: 'workspaceReviewCancel', text: tr('Cancel'), type: 'reject' }
    ];
    if (model.operation !== 'compare_shelf')
        footer.push({
            id: 'workspaceReviewAccept',
            text: tr(
                {
                    merge_begin: 'Merge stream',
                    unshelve_begin: 'Unshelve',
                    rebase_begin: 'Rebase / resolve',
                    update_shelf: 'Replace shelf files'
                }[model.operation] || 'Shelve'
            ),
            icon: data.kind ? 'source-branch' : 'archive',
            type: 'accept',
            enabled:
                !model.busy &&
                !!data.number &&
                !!data.editable &&
                !data.active_transfer &&
                !data.integration &&
                (!['merge_begin', 'unshelve_begin'].includes(model.operation) ||
                    !data.rebase_required)
        });
    return surface(body, footer, width, height, y);
}

export function reviewFile(row, width, language) {
    const tr = (text) => translate(text, language);
    const text =
        row.path +
        ' · ' +
        (row.excluded
            ? tr('Excluded by workspace mapping')
            : row.conflict
              ? tr('Conflict')
              : row.action || '') +
        (row.shelf_status ? ' · ' + row.shelf_status : '');
    return {
        nodes: [
            label('workspaceReviewFile', rect(0, 0, width, 32), text, {
                elideMiddle: true,
                fontRole: 'secondary',
                toolTip: text
            })
        ]
    };
}

export function comparison(model, width, height, language) {
    const tr = (text) => translate(text, language),
        data = model.comparison || {},
        inner = Math.max(0, width - 16),
        body = [];
    let y = 0;
    for (const [index, side] of [data.left || {}, data.right || {}].entries()) {
        const text =
                (side.path || '') +
                ' · ' +
                (side.size || 0) +
                ' ' +
                tr('bytes') +
                (side.sha256 ? ' · SHA-256 ' + side.sha256 : ''),
            h = Math.max(32, captionHeight(text, inner) * 1.2);
        body.push(
            label(
                'workspaceComparisonSide' + index,
                rect(0, y, inner, h),
                text,
                { wrap: true, wrapAnywhere: true, color: 'secondaryText' }
            )
        );
        y += h + 8;
    }
    if (data.kind !== 'text') {
        const text = tr(
                'Binary or large file. Use an external comparison application.'
            ),
            h = Math.max(36, captionHeight(text, inner) * 1.2);
        body.push(
            label('workspaceComparisonMessage', rect(0, y, inner, h), text, {
                wrap: true,
                color: 'secondaryText'
            })
        );
        y += h + 8;
    }
    const areaHeight = Math.max(100, height - y - 70);
    body.push(
        node(
            'Area',
            'workspaceComparisonResult',
            rect(0, y, inner, areaHeight),
            {
                text:
                    data.text ||
                    (data.identical === true ? tr('No differences.') : ''),
                readOnly: true,
                monospace: true,
                label: tr('Comparison result')
            }
        )
    );
    y += areaHeight + 8;
    return surface(
        body,
        [
            {
                id: 'workspaceComparisonExternal',
                text: tr('Compare with application…'),
                icon: 'compare',
                type: 'external',
                enabled: !model.busy
            },
            {
                id: 'workspaceComparisonClose',
                text: tr('Close'),
                icon: 'close',
                type: 'reject'
            }
        ],
        width,
        height,
        y
    );
}

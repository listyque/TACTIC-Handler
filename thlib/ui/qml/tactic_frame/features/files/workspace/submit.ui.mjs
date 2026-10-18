import { node, rect, label, button } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { captionHeight } from '../../../controls/forms/sections.ui.mjs';

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language),
        review = model.review || {},
        context = model.context || {},
        inner = Math.max(0, width - 16),
        children = [],
        editable = !model.busy;
    let y = 0;
    function text(id, value, color = 'secondaryText') {
        const h = Math.max(24, captionHeight(value, inner) * 1.2);
        children.push(
            label(id, rect(0, y, inner, h), value, { wrap: true, color })
        );
        y += h + 8;
    }
    function check(id, value, caption, key) {
        const title = tr(caption),
            h = Math.max(32, captionHeight(title, inner - 30) * 1.2);
        children.push(
            node('CheckBox', id, rect(0, y, inner, h), {
                text: title,
                checked: !!value,
                compact: true,
                wrapText: true,
                enabled: editable,
                action: { type: 'field', key }
            })
        );
        y += h + 8;
    }
    function more(id, caption, enabled, action) {
        children.push(
            button(
                id,
                rect(0, y, inner, 36),
                tr(caption),
                'chevron-right',
                action,
                editable && !!enabled
            )
        );
        y += 44;
    }
    text('submitDescriptionLabel', tr('Changelist description'), 'primaryText');
    children.push(
        node('Area', 'submitDescription', rect(0, y, inner, 80), {
            text: model.draft || '',
            label: tr('Changelist description'),
            enabled: editable,
            action: { type: 'field', key: 'draft' }
        })
    );
    y += 88;
    if (model.error || model.notice)
        text('submitNotice', model.notice || model.error, 'error');
    if (review.active_transfer || review.integration || review.rebase_required)
        text(
            'submitBlocked',
            tr(
                review.active_transfer
                    ? 'Finish or cancel the upload before submit'
                    : review.integration
                      ? 'Resolve all conflicts before submit'
                      : 'Stream head changed; rebase before submit'
            ),
            'error'
        );
    text(
        'submitChooseFiles',
        model.busy
            ? tr('Preparing submit…')
            : tr('Choose files to submit ({count})').replace(
                  '{count}',
                  review.files || 0
              ),
        'primaryText'
    );
    children.push(
        node('CheckBox', 'submitSelectAll', rect(0, y, inner, 32), {
            text: tr('Select all files'),
            checked: !!model.selectionAll && !(model.exceptions || []).length,
            enabled: editable,
            action: { type: 'selectAll' }
        })
    );
    y += 40;
    children.push(
        node('List', 'submitPendingFiles', rect(0, y, inner, 150), {
            source: 'pendingFiles',
            keyField: 'path',
            rowHeight: 34,
            scrollbarId: 'submitPendingFilesScrollBar'
        })
    );
    y += 158;
    text(
        'submitPendingNotice',
        tr('Unchecked files remain pending. Local files are kept.')
    );
    more('submitFilesMore', 'Next page', review.after, { type: 'filesMore' });
    text('submitShelvesTitle', tr('Shelved files'), 'primaryText');
    children.push(
        node('Choice', 'submitShelf', rect(0, y, inner, 38), {
            label: tr('Shelf changelist'),
            value:
                context.shelf_files?.change ||
                context.shelves?.items?.[0]?.code ||
                '',
            options: (context.shelves?.items || []).map((row) => ({
                value: row.code,
                label: '#' + row.number
            })),
            enabled: editable,
            action: { type: 'shelf' }
        })
    );
    y += 46;
    more('submitShelvesMore', 'Next shelves', context.shelves?.after, {
        type: 'shelvesMore'
    });
    children.push(
        node('List', 'submitShelvedFiles', rect(0, y, inner, 120), {
            source: 'shelfFiles',
            keyField: 'path',
            rowHeight: 34,
            scrollbarId: 'submitShelvedFilesScrollBar'
        })
    );
    y += 128;
    text(
        'submitShelvesNotice',
        tr('Shelves are separate snapshots and are kept after submit.')
    );
    more('submitShelfFilesMore', 'Next page', context.shelf_files?.after, {
        type: 'shelfFilesMore'
    });
    text('submitAdditionalTitle', tr('Additional options'), 'primaryText');
    check(
        'submitGuardResolved',
        model.guardResolved,
        'Do not submit if resolved files have been modified',
        'guardResolved'
    );
    check(
        'submitReopen',
        model.reopenFiles,
        'Check out submitted files after submit',
        'reopenFiles'
    );
    check(
        'submitRestricted',
        model.restrictAccess,
        'Restrict access to changelist',
        'restrictAccess'
    );
    if (model.restrictAccess)
        text(
            'submitRestrictedNotice',
            tr(
                'Only the owner and administrators can view changelist details. Depot file permissions do not change.'
            )
        );
    text('submitUnchangedLabel', tr('On submit'));
    children.push(
        node('Choice', 'submitUnchangedPolicy', rect(0, y, inner, 38), {
            label: tr('On submit'),
            value: model.unchangedPolicy || 'revert',
            options: [
                ['submit', 'Submit all selected files'],
                ['revert', 'Revert unchanged files'],
                ['leave', 'Leave unchanged files pending']
            ].map(([value, label]) => ({ value, label: tr(label) })),
            enabled: editable,
            action: { type: 'field', key: 'unchangedPolicy' }
        })
    );
    y += 46;
    text(
        'submitTasksTitle',
        tr('Link tasks to changelist (optional)'),
        'primaryText'
    );
    children.push(
        node('Field', 'submitTaskSearch', rect(0, y, inner, 38), {
            label: tr('Find tasks by code or description'),
            placeholder: tr('Find tasks by code or description'),
            text: model.taskQuery || '',
            enabled: editable,
            action: { type: 'field', key: 'taskQuery' },
            activateAction: { type: 'searchTasks' }
        })
    );
    y += 46;
    children.push(
        button(
            'submitTaskSearchButton',
            rect(0, y, inner, 36),
            tr('Search tasks'),
            'search',
            { type: 'searchTasks' },
            editable
        )
    );
    y += 44;
    more('submitTasksMore', 'Next tasks', context.tasks?.after, {
        type: 'tasksMore'
    });
    children.push(
        node('List', 'submitTaskList', rect(0, y, inner, 110), {
            source: 'tasks',
            keyField: 'code',
            rowHeight: 36,
            scrollbarId: 'submitTaskScrollBar'
        })
    );
    y += 118;
    if (!model.taskCount)
        text('submitNoTasks', tr('No tasks. Create tasks in Task Manager.'));
    text(
        'submitSelectedTasks',
        tr('Selected tasks: {count}').replace(
            '{count}',
            model.selectedTasks?.length || 0
        )
    );
    text('submitTaskStatusLabel', tr('Status after submit'));
    children.push(
        node('Choice', 'submitTaskStatus', rect(0, y, inner, 38), {
            label: tr('Status after submit'),
            options: model.taskChoices || [],
            value: model.taskStatus || '',
            enabled: editable && !!model.selectedTasks?.length,
            action: { type: 'field', key: 'taskStatus' }
        })
    );
    y += 46;
    const columns = width < 550 ? 2 : 4,
        footerHeight = Math.ceil(4 / columns) * 46,
        w = (width - (columns - 1) * 8) / columns;
    const footer = [
        ['submitCancel', 'Cancel', 'close', 'reject', true],
        ['submitSave', 'Save', 'content-save', 'save', model.ready],
        ['submitApply', 'Apply', '', 'apply', model.ready],
        [
            'submitAccept',
            'Submit',
            'publish',
            'submit',
            model.ready && (model.selectionAll || model.exceptions?.length > 0)
        ]
    ];
    return {
        nodes: [
            node(
                'Scroll',
                'submitBody',
                rect(0, 0, width, Math.max(0, height - footerHeight - 8)),
                {
                    contentHeight: y,
                    scrollbarId: 'submitBodyScrollBar',
                    children
                }
            ),
            ...footer.map(([id, title, icon, type, enabled], index) =>
                button(
                    id,
                    rect(
                        (index % columns) * (w + 8),
                        height -
                            footerHeight +
                            Math.floor(index / columns) * 46,
                        w,
                        38
                    ),
                    tr(title),
                    icon,
                    { type },
                    !!enabled,
                    { highlighted: type === 'submit' }
                )
            )
        ]
    };
}

export function fileRow(model, row, width, language, shelved = false) {
    const tr = (text) => translate(text, language),
        checkWidth = shelved ? 0 : 30;
    const action = ['delete', 'move/delete'].includes(row.action)
        ? 'Delete'
        : row.action === 'move/add'
          ? 'Rename'
          : row.base
            ? 'Edit'
            : 'Add';
    const nodes = [];
    if (!shelved)
        nodes.push(
            node(
                'CheckBox',
                'submitFileSelect:' + row.path,
                rect(0, 0, 24, 34),
                {
                    checked: model.selectionAll
                        ? !model.exceptions.includes(row.path)
                        : model.exceptions.includes(row.path),
                    enabled: !model.busy,
                    label: row.path,
                    action: { type: 'selectFile', key: row.path }
                }
            )
        );
    nodes.push(
        node('Icon', 'submitFileIcon', rect(checkWidth, 9, 16, 16), {
            icon: action === 'Delete' ? 'delete' : row.base ? 'edit' : 'add',
            color: 'secondaryText'
        })
    );
    nodes.push(
        label(
            'submitFilePath',
            rect(checkWidth + 22, 0, Math.max(0, width - checkWidth - 132), 34),
            row.path,
            { elideMiddle: true, toolTip: row.path }
        )
    );
    nodes.push(
        label(
            'submitFileAction',
            rect(Math.max(checkWidth + 22, width - 100), 0, 100, 34),
            tr(action),
            { color: 'secondaryText' }
        )
    );
    return { nodes };
}

export function taskRow(model, row, width) {
    return {
        nodes: [
            node(
                'CheckBox',
                'submitTaskSelect:' + row.code,
                rect(0, 0, 24, 36),
                {
                    checked: model.selectedTasks.some(
                        (task) => task.code === row.code
                    ),
                    label: row.code,
                    enabled: !model.busy,
                    action: { type: 'selectTask', key: row.code }
                }
            ),
            label(
                'submitTaskDescription',
                rect(32, 0, Math.max(0, width - 150), 36),
                row.code + ' · ' + row.description,
                { toolTip: row.description }
            ),
            label(
                'submitTaskState',
                rect(Math.max(32, width - 110), 0, 110, 36),
                row.status,
                { color: 'secondaryText' }
            )
        ]
    };
}

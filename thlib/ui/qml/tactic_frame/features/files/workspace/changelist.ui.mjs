import { node, rect, label, button } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { captionHeight } from '../../../controls/forms/sections.ui.mjs';
import { date } from './inspector.ui.mjs';

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language),
        change = model.change || {},
        details = model.details || {},
        inner = Math.max(0, width - 40),
        body = [];
    let y = 0;
    function text(id, value, color = 'secondaryText') {
        const h = Math.max(24, captionHeight(value, inner) * 1.2);
        body.push(
            label(id, rect(0, y, inner, h), value, { wrap: true, color })
        );
        y += h + 8;
    }
    function section(id, title, view, shown, tableHeight, after, command) {
        body.push(
            button(
                id + 'Toggle',
                rect(0, y, 28, 28),
                title,
                shown ? 'chevron-down' : 'chevron-right',
                { type: 'toggle', key: id },
                true,
                { iconOnly: true, iconAction: true }
            )
        );
        body.push(
            label(id + 'Title', rect(34, y, Math.max(0, inner - 72), 28), title)
        );
        if (command)
            body.push(
                button(
                    id + 'More',
                    rect(Math.max(0, inner - 30), y, 28, 28),
                    tr('Next page'),
                    'chevron-right',
                    { type: 'load', section: command },
                    !model.loading && !!after,
                    { iconOnly: true, iconAction: true }
                )
            );
        y += 36;
        if (shown) {
            body.push(
                node('View', id + 'Table', rect(0, y, inner, tableHeight), {
                    view
                })
            );
            y += tableHeight + 8;
        }
    }
    body.push(
        node('Icon', 'changelistTitleIcon', rect(0, 0, 22, 22), {
            icon: 'archive',
            color: 'action'
        })
    );
    body.push(
        label(
            'fileWorkspaceChangelistNumber',
            rect(30, 0, Math.max(0, inner - 66), 28),
            tr('Changelist #{number}').replace(
                '{number}',
                change.number || model.changeCode || ''
            ),
            { weight: 600 }
        )
    );
    body.push(
        button(
            'changelistDetailsRefresh',
            rect(Math.max(0, inner - 28), 0, 28, 28),
            tr('Refresh'),
            'refresh',
            { type: 'refresh' },
            !model.loading && !model.dirty,
            { iconOnly: true, iconAction: true }
        )
    );
    y += 36;
    const fields = [
        [
            'State',
            tr(
                {
                    pending: 'Pending',
                    submitted: 'Submitted',
                    shelved: 'Shelved',
                    reverted: 'Reverted'
                }[change.state] ||
                    change.state ||
                    ''
            )
        ],
        ['Workspace', change.workspace || '—'],
        [
            'Date',
            change.created_at
                ? date(change.created_at * 1000000)
                : change.date || '—'
        ],
        ['User', change.owner || '—'],
        ['Access type', tr(change.restricted ? 'Restricted' : 'Public')],
        ['Stream', change.stream || '—']
    ];
    const columns = inner < 600 ? 1 : 2,
        columnWidth = (inner - (columns - 1) * 20) / columns;
    for (const [index, [title, value]] of fields.entries()) {
        const x = (index % columns) * (columnWidth + 20),
            top = y + Math.floor(index / columns) * 24,
            caption = Math.min(96, columnWidth * 0.4);
        body.push(
            label(
                'changelistFieldLabel' + index,
                rect(x, top, caption - 6, 20),
                tr(title),
                { color: 'secondaryText', fontRole: 'secondary' }
            )
        );
        body.push(
            label(
                'changelistField' + index,
                rect(x + caption, top, Math.max(0, columnWidth - caption), 20),
                String(value),
                { elideMiddle: true, toolTip: String(value) }
            )
        );
    }
    y += Math.ceil(fields.length / columns) * 24 + 8;
    text('changelistDescriptionLabel', tr('Description'));
    body.push(
        node(
            'Area',
            'fileWorkspaceChangelistDescription',
            rect(0, y, inner, 120),
            {
                text: model.draft || '',
                label: tr('Changelist description'),
                readOnly: !model.editable || !model.editing,
                action: { type: 'description' }
            }
        )
    );
    y += 128;
    const error = details.error || (model.sameChange ? model.error : '');
    if (model.loading || error)
        text(
            'changelistNotice',
            model.loading ? tr('Loading changelist contents…') : error,
            error ? 'error' : 'secondaryText'
        );
    section(
        'files',
        tr('Files ({count})').replace(
            '{count}',
            details.files?.files ?? change.opened_files ?? '—'
        ),
        'files',
        model.showFiles,
        210,
        details.files?.after,
        'files'
    );
    body.push(
        button(
            'changelistShelvesToggle',
            rect(0, y, 28, 28),
            tr('Shelved files'),
            model.showShelves ? 'chevron-down' : 'chevron-right',
            { type: 'toggle', key: 'shelves' },
            true,
            { iconOnly: true, iconAction: true }
        )
    );
    body.push(
        label(
            'changelistShelvesTitle',
            rect(34, y, Math.max(0, inner - 34), 28),
            tr('Shelved files')
        )
    );
    y += 36;
    if (model.showShelves) {
        const choiceWidth = Math.max(0, inner - 72);
        body.push(
            node(
                'Choice',
                'changelistShelfChoice',
                rect(0, y, choiceWidth, 38),
                {
                    label: tr('Shelf changelist'),
                    value:
                        details.shelf_files?.change ||
                        details.shelves?.items?.[0]?.code ||
                        '',
                    options: (details.shelves?.items || []).map((row) => ({
                        value: row.code,
                        label: '#' + row.number
                    })),
                    enabled: !!details.shelves?.items?.length,
                    action: { type: 'shelf' }
                }
            )
        );
        body.push(
            button(
                'changelistShelfMore',
                rect(choiceWidth + 8, y + 4, 28, 28),
                tr('Next shelves'),
                'more_horiz',
                { type: 'load', section: 'shelves' },
                !model.loading && !!details.shelves?.after,
                { iconOnly: true, iconAction: true }
            )
        );
        body.push(
            button(
                'changelistShelfFilesMore',
                rect(choiceWidth + 40, y + 4, 28, 28),
                tr('Next page'),
                'chevron-right',
                { type: 'load', section: 'shelf_files' },
                !model.loading && !!details.shelf_files?.after,
                { iconOnly: true, iconAction: true }
            )
        );
        y += 46;
        body.push(
            node('View', 'changelistShelvedTable', rect(0, y, inner, 140), {
                view: 'shelves'
            })
        );
        y += 148;
    }
    section(
        'tasks',
        tr('Tasks ({count})').replace(
            '{count}',
            details.tasks?.items?.length || 0
        ),
        'tasks',
        model.showTasks,
        125,
        false,
        ''
    );
    if (!model.sameChange)
        text(
            'changelistChanged',
            tr('The selected changelist has changed. Reopen its details.')
        );
    const footerHeight = 44,
        footerY = height - footerHeight;
    const nodes = [
        node('Box', 'changelistBackground', rect(0, 0, width, height), {
            background: 'panelDeep'
        }),
        node(
            'Scroll',
            'changelistDetailsScroll',
            rect(
                12,
                12,
                Math.max(0, width - 24),
                Math.max(0, height - footerHeight - 24)
            ),
            {
                contentHeight: y + 12,
                scrollbarId: 'changelistDetailsScrollBar',
                children: body
            }
        ),
        node('Box', 'changelistFooter', rect(0, footerY, width, footerHeight), {
            background: 'panelDeep'
        })
    ];
    nodes.push(
        button(
            'fileWorkspaceDetailsActions',
            rect(12, footerY + 6, 28, 32),
            tr('Changelist actions'),
            'more_vert',
            { type: 'actions' },
            !!model.editable && !model.dirty,
            { iconOnly: true, iconAction: true }
        )
    );
    nodes.push(
        button(
            'fileWorkspaceDetailsEdit',
            rect(48, footerY + 4, 88, 36),
            tr('Edit'),
            'edit',
            { type: 'edit' },
            !!model.editable && !model.loading,
            { visible: !model.editing }
        )
    );
    nodes.push(
        button(
            'fileWorkspaceDetailsSave',
            rect(48, footerY + 4, 88, 36),
            tr('Save'),
            'content-save',
            { type: 'save' },
            !!model.editable && !!model.dirty,
            { visible: !!model.editing, highlighted: true }
        )
    );
    nodes.push(
        button(
            'fileWorkspaceDetailsClose',
            rect(Math.max(144, width - 100), footerY + 4, 88, 36),
            tr('Close'),
            'close',
            { type: 'close' },
            true
        )
    );
    return { nodes };
}

import { node, rect, label, button } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { captionHeight } from '../../../controls/forms/sections.ui.mjs';

export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language),
        narrow = width < 600,
        available = narrow ? Math.max(0, height - 60) : Math.max(0, width - 16),
        extent = Math.max(
            0,
            Math.min(
                available - 10,
                model.extent ?? available * (narrow ? 0.4 : 0.55)
            )
        );
    const list = rect(
        8,
        52,
        narrow ? width - 16 : extent,
        narrow ? extent : height - 60
    );
    const detail = rect(
            narrow ? 8 : 18 + extent,
            narrow ? 62 + extent : 52,
            narrow ? width - 16 : width - 26 - extent,
            narrow ? height - 70 - extent : height - 60
        ),
        inner = Math.max(0, detail.width - 16);
    const children = [],
        draft = model.draft || {},
        editing = draft.creating !== undefined,
        selected = model.selected || {};
    let y = 0;
    function text(id, value, heading = false) {
        const h = Math.max(
            heading ? 28 : 24,
            captionHeight(value, inner) * 1.2
        );
        children.push(
            label(id, rect(0, y, inner, h), value, {
                wrap: true,
                fontRole: heading ? 'title' : 'body',
                color: heading ? 'primaryText' : 'secondaryText',
                weight: heading ? 600 : 400
            })
        );
        y += h + 8;
    }
    function actions(items) {
        const count = inner < 420 ? 1 : 2,
            w = (inner - (count - 1) * 8) / count;
        for (const [index, item] of items.entries())
            children.push(
                button(
                    item.id,
                    rect(
                        (index % count) * (w + 8),
                        y + Math.floor(index / count) * 46,
                        w,
                        38
                    ),
                    tr(item.text),
                    item.icon || '',
                    { type: item.type },
                    item.enabled !== false
                )
            );
        y += Math.ceil(items.length / count) * 46;
    }
    if (model.notice) text('workspaceDepotNotice', model.notice);
    if (editing) {
        text(
            'workspaceDepotEditTitle',
            tr(draft.creating ? 'New depot' : 'Edit depot'),
            true
        );
        for (const [key, title, id] of [
            ['code', 'Depot code', 'depotEditorCode'],
            ['title', 'Name', 'depotEditorName']
        ]) {
            text(id + 'Label', tr(title));
            children.push(
                node('Field', id, rect(0, y, inner, 38), {
                    text: draft[key] || '',
                    label: tr(title),
                    readOnly: key === 'code' && !draft.creating,
                    enabled: !model.busy,
                    action: { type: 'field', key }
                })
            );
            y += 46;
        }
        text('workspaceDepotRepositoryLabel', tr('Repository'));
        const options = [{ value: '', label: tr('Project storage') }].concat(
            (model.repositories || []).map((value) => ({ value, label: value }))
        );
        if (
            draft.repository &&
            !options.some((row) => row.value === draft.repository)
        )
            options.push({ value: draft.repository, label: draft.repository });
        children.push(
            node('Choice', 'workspaceDepotRepository', rect(0, y, inner, 38), {
                label: tr('Repository'),
                options,
                value: draft.repository || '',
                enabled: !model.busy,
                action: { type: 'field', key: 'repository' }
            })
        );
        y += 46;
        text(
            'workspaceDepotRepositoryHelp',
            tr(
                'Repository changes apply to new uploads. Existing file contents stay in their original storage.'
            )
        );
        text(
            'workspaceDepotAccessHelp',
            tr(
                'Depot paths are case-sensitive. Access is configured in Administration → Rules using file_depot.'
            )
        );
        actions([
            {
                id: 'workspaceDepotReset',
                text: 'Reset',
                icon: 'undo',
                type: 'reset',
                enabled: !model.busy
            },
            {
                id: 'workspaceDepotCancel',
                text: 'Cancel',
                icon: 'close',
                type: 'cancel',
                enabled: !model.busy
            },
            {
                id: 'workspaceDepotSave',
                text: draft.creating ? 'Create' : 'Save',
                icon: 'content-save',
                type: 'save',
                enabled: !model.busy && !!String(draft.code || '').trim()
            }
        ]);
    } else {
        text(
            'workspaceDepotSelectedTitle',
            selected.code || tr('Select a depot'),
            true
        );
        if (selected.code)
            text(
                'workspaceDepotDetails',
                (selected.title || '') +
                    '\n' +
                    tr('Repository') +
                    ': ' +
                    (selected.storage?.repository || tr('Project storage')) +
                    '\n' +
                    tr('Revision') +
                    ': ' +
                    selected.revision +
                    '\n' +
                    tr('Case-sensitive depot paths')
            );
        if (model.administrator)
            actions([
                {
                    id: 'workspaceDepotNew',
                    text: 'New depot',
                    icon: 'add',
                    type: 'new',
                    enabled: !model.busy
                },
                {
                    id: 'workspaceDepotEdit',
                    text: 'Edit depot',
                    icon: 'edit',
                    type: 'edit',
                    enabled: !model.busy && !!selected.code
                }
            ]);
    }
    return {
        nodes: [
            node('Box', 'workspaceDepotBackground', rect(0, 0, width, height), {
                background: 'panelDeep',
                radius: 14
            }),
            label(
                'workspaceDepotTitle',
                rect(8, 8, Math.max(0, width - 220), 36),
                tr('Depots'),
                { fontRole: 'title', weight: 600 }
            ),
            button(
                'workspaceDepotRefresh',
                rect(Math.max(8, width - 208), 8, 96, 36),
                tr('Refresh'),
                'refresh',
                { type: 'refresh' },
                !model.busy
            ),
            button(
                'workspaceDepotMore',
                rect(Math.max(8, width - 104), 8, 96, 36),
                tr('Next page'),
                'chevron-right',
                { type: 'more' },
                !model.busy && !!model.after
            ),
            node('List', 'workspaceDepotList', list, {
                source: 'depots',
                keyField: 'id',
                fields: ['id', 'node'],
                rowHeight: 62,
                rowGap: 4,
                label: tr('Depots'),
                scrollbarId: 'workspaceDepotListScrollBar'
            }),
            node(
                'Splitter',
                'workspaceDepotSplitter',
                rect(
                    narrow ? 8 : extent + 8,
                    narrow ? extent + 52 : 52,
                    narrow ? width - 16 : 10,
                    narrow ? 10 : height - 60
                ),
                {
                    horizontal: narrow,
                    value: extent,
                    min: 0,
                    max: Math.max(0, available - 10),
                    text: tr('Depots'),
                    action: { type: 'split' }
                }
            ),
            node('Scroll', 'workspaceDepotDetails', detail, {
                contentHeight: y,
                scrollbarId: 'workspaceDepotDetailsScrollBar',
                children
            })
        ]
    };
}

export function row(model, record, width, language) {
    const tr = (text) => translate(text, language),
        data = record.node;
    return {
        nodes: [
            node(
                'Action',
                'workspaceDepot_' + record.id,
                rect(0, 0, width, 58),
                {
                    text: data.code,
                    role: 'option',
                    selected: model.selected?.code === data.code,
                    selectedColor: 'selected',
                    normalColor: 'transparent',
                    action: { type: 'select', key: record.id },
                    children: [
                        node(
                            'Icon',
                            'workspaceDepotIcon',
                            rect(10, 20, 18, 18),
                            { icon: 'database', color: 'action' }
                        ),
                        label(
                            'workspaceDepotCode',
                            rect(36, 4, Math.max(0, width - 44), 24),
                            data.code,
                            { elideMiddle: true }
                        ),
                        label(
                            'workspaceDepotSubtitle',
                            rect(36, 30, Math.max(0, width - 44), 20),
                            (data.title || data.code) +
                                ' · ' +
                                (data.storage?.repository ||
                                    tr('Project storage')),
                            { fontRole: 'secondary', color: 'secondaryText' }
                        )
                    ]
                }
            )
        ]
    };
}

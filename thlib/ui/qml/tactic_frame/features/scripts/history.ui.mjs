import { node, rect, label, button, muted } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { listAction } from '../../controls/lists/tree.ui.mjs';
import * as Settings from '../configuration/settings.ui.mjs';

export function initial() {
    return {
        visible: null,
        mobile: false,
        width: 280,
        query: '',
        searchOpen: false,
        grouping: 'time',
        archived: false,
        collapsed: {},
        edit: null
    };
}
export function layout(model, width) {
    const small = width < 940;
    const visible = small
        ? !!model.history.mobile
        : (model.history.visible ?? true);
    const panel = visible
        ? small
            ? width
            : Math.min(Math.max(220, model.history.width), width - 500)
        : 0;
    return {
        small,
        visible,
        panel,
        mainX: small ? 0 : panel,
        mainWidth: small ? width : width - panel
    };
}
export function change(model, action, small = false) {
    const history = model.history;
    if (action.type === 'historyOptions')
        return Object.assign({}, history, { edit: { kind: 'options' } });
    if (action.type === 'historySearch')
        return Object.assign({}, history, {
            searchOpen: !history.searchOpen,
            query: history.searchOpen ? '' : history.query
        });
    if (action.type === 'historyToggle')
        return Object.assign(
            {},
            history,
            small
                ? { mobile: !history.mobile }
                : { visible: !(history.visible ?? action.value) }
        );
    if (action.type === 'historyWidth')
        return Object.assign({}, history, { width: action.value });
    if (action.type === 'historyQuery')
        return Object.assign({}, history, { query: action.value });
    if (action.type === 'historyGrouping')
        return Object.assign({}, history, {
            grouping: action.value,
            edit: null
        });
    if (action.type === 'historyArchived')
        return Object.assign({}, history, {
            archived: !!action.value,
            edit: null
        });
    if (action.type === 'historyCollapse')
        return Object.assign({}, history, {
            collapsed: Object.assign({}, history.collapsed, {
                [action.value]: !history.collapsed[action.value]
            })
        });
    if (action.type === 'historyCancel')
        return Object.assign({}, history, { edit: null });
    if (action.type === 'historyRemoveConfirm')
        return Object.assign({}, history, {
            edit: Object.assign({}, history.edit, { confirm: true })
        });
    if (action.type === 'historyGroupEdit') {
        const group = (model.groups || []).find(
            (item) => item.id === action.value
        );
        return Object.assign({}, history, {
            visible: true,
            mobile: small,
            edit: {
                kind: 'group',
                id: group?.id || '',
                name: group?.name || '',
                revision: model.groups_revision
            }
        });
    }
    if (action.type === 'historyEdit' && action.value) {
        const row =
            model.requests.find((item) => item.request_id === action.value) ||
            (model.request?.request_id === action.value
                ? model.request.library_summary
                : null);
        if (!row) return null;
        return Object.assign({}, history, {
            visible: true,
            mobile: small,
            edit: {
                kind: 'chat',
                id: row.request_id,
                title: row.default_title ? '' : row.title,
                group: row.group || '',
                pinned: !!row.pinned,
                archived: !!row.archived,
                revision: row.library_revision,
                status: row.status
            }
        });
    }
    const fields = {
        historyTitle: 'title',
        historyFolder: 'group',
        historyPinned: 'pinned',
        historyName: 'name'
    };
    if (fields[action.type] && history.edit)
        return Object.assign({}, history, {
            edit: Object.assign({}, history.edit, {
                [fields[action.type]]: action.value
            })
        });
    return null;
}
export function draft(model) {
    return {
        prompt: model.prompt,
        attachments: model.attachments.slice(),
        model: model.model,
        provider: model.provider,
        effort: model.effort,
        allowChanges: model.allowChanges,
        allowWeb: model.allowWeb
    };
}
export function restored(value) {
    return Object.assign(
        {
            prompt: '',
            attachments: [],
            model: null,
            provider: null,
            effort: null,
            allowChanges: false,
            allowWeb: false
        },
        value || {}
    );
}
export function merge(previous, current) {
    const records = new Map(previous.map((row) => [row.request_id, row]));
    for (const row of current) records.set(row.request_id, row);
    return Array.from(records.values());
}
export function rows(model, language, now = Date.now()) {
    const tr = (text) => translate(text, language),
        history = model.history;
    const folders = new Map(
        (model.groups || []).map((group) => [group.id, group.name])
    );
    const groups = new Map();
    function add(key, title, row, folder = '') {
        if (!groups.has(key))
            groups.set(key, { key, title, folder, records: [] });
        if (row) groups.get(key).records.push(row);
    }
    const midnight = new Date(now);
    midnight.setHours(0, 0, 0, 0);
    const today = midnight.getTime();
    const sorted = model.requests
        .slice()
        .sort(
            (a, b) =>
                (b.activity || 0) - (a.activity || 0) ||
                b.request_id.localeCompare(a.request_id)
        );
    const topPinned = (row) =>
        row.pinned && (history.grouping !== 'group' || !row.group);
    for (const row of sorted.filter(topPinned))
        add('pinned', tr('Pinned conversations'), row);
    if (history.grouping === 'group')
        for (const group of model.groups || [])
            add('folder:' + group.id, group.name, null, group.id);
    for (const row of sorted.filter((row) => !topPinned(row))) {
        if (history.grouping === 'type') {
            add(
                'type:' + row.search_type,
                row.type_title || row.search_type || tr('No Search Type'),
                row
            );
        } else if (history.grouping === 'group') {
            add(
                'folder:' + (row.group || ''),
                folders.get(row.group) || tr('Ungrouped'),
                row,
                row.group || ''
            );
        } else {
            const date = new Date((row.activity || 0) * 1000);
            date.setHours(0, 0, 0, 0);
            const days = Math.round((today - date.getTime()) / 86400000);
            const key =
                days < 1
                    ? 'Today'
                    : days === 1
                      ? 'Yesterday'
                      : days < 7
                        ? 'Previous 7 days'
                        : days < 30
                          ? 'Previous 30 days'
                          : 'Older conversations';
            add('time:' + key, tr(key), row);
        }
    }
    const result = [];
    for (const group of groups.values()) {
        if (history.grouping === 'group')
            group.records.sort((a, b) => Number(b.pinned) - Number(a.pinned));
        result.push(
            Object.assign({}, group, {
                kind: 'heading',
                count: group.records.length
            })
        );
        if (!group.folder || !history.collapsed[group.key])
            for (const record of group.records)
                result.push(
                    Object.assign({}, record, {
                        key: record.request_id,
                        kind: 'chat'
                    })
                );
    }
    return result;
}

export function row(model, record, width, language) {
    const tr = (text) => translate(text, language),
        idle = !model.busy && !model.pending && !model.uploading;
    if (record.kind === 'heading') {
        const folder = !!record.folder;
        const nodes = [
            folder
                ? listAction(
                      'historyGroup_' + record.key,
                      rect(8, 0, width - 16, 32),
                      record.title,
                      model.history.collapsed[record.key]
                          ? 'chevron-right'
                          : 'chevron-down',
                      { type: 'historyCollapse', value: record.key },
                      true,
                      {
                          fontRole: 'secondary',
                          color: 'secondaryText',
                          weight: 500,
                          endInset: 28
                      }
                  )
                : label(
                      'historyGroup_' + record.key,
                      rect(12, 4, width - 24, 24),
                      record.title,
                      Object.assign({}, muted, {
                          fontRole: 'secondary',
                          role: 'heading',
                          level: 2
                      })
                  )
        ];
        if (folder)
            nodes.push(
                listAction(
                    'historyFolderEdit_' + record.folder,
                    rect(width - 36, 2, 28, 28),
                    tr('Edit conversation folder'),
                    'more-horiz',
                    { type: 'historyGroupEdit', value: record.folder },
                    idle,
                    {
                        iconOnly: true,
                        revealOnRowInteraction: !model.history.mobile
                    }
                )
            );
        return { nodes };
    }
    const working = ['queued', 'running', 'cancelling'].includes(record.status);
    const title = record.default_title ? tr(record.title) : record.title;
    return {
        nodes: [
            listAction(
                'agentHistoryOpen_' + record.request_id,
                rect(8, 0, width - 16, 32),
                title,
                working ? 'sync' : '',
                { type: 'select', value: record.request_id },
                idle,
                {
                    selected: model.selected === record.request_id,
                    toolTip: title,
                    endInset: 28
                }
            ),
            listAction(
                'agentHistoryEdit_' + record.request_id,
                rect(width - 36, 2, 28, 28),
                tr('Conversation settings'),
                'more-horiz',
                { type: 'historyEdit', value: record.request_id },
                idle,
                {
                    iconOnly: true,
                    revealOnRowInteraction: !model.history.mobile
                }
            )
        ]
    };
}
export function describe(model, width, height, language, small) {
    const tr = (text) => translate(text, language),
        edit = model.history.edit;
    const idle = !model.busy && !model.pending && !model.uploading;
    const heading = edit
        ? edit.kind === 'options'
            ? 'Conversation view'
            : edit.kind === 'group'
              ? 'Conversation folder'
              : 'Conversation settings'
        : model.history.archived
          ? 'Archived conversations'
          : 'Conversations';
    const nodes = [
        node('Box', 'agentHistorySurface', rect(0, 0, width, height), {
            background: 'surfaceContainerLow',
            border: 'outlineVariant',
            borderWidth: 1,
            radius: 0
        }),
        label(
            'agentHistoryHeading',
            rect(16, 8, Math.max(20, width - (edit ? 96 : 128)), 32),
            tr(heading),
            { weight: 600 }
        ),
        listAction(
            'agentHistoryClose',
            rect(width - 40, 8, 32, 32),
            tr('Hide conversations'),
            'chevron-left',
            { type: 'historyToggle', value: true },
            true,
            { iconOnly: true }
        )
    ];
    if (edit && edit.kind === 'options') {
        nodes.push(
            listAction(
                'agentHistoryBack',
                rect(width - 76, 8, 32, 32),
                tr('Back to conversations'),
                'arrow-back',
                { type: 'historyCancel' },
                true,
                { iconOnly: true }
            )
        );
        const fields = [
            {
                kind: 'Choice',
                field: 'grouping',
                title: 'Group conversations',
                action: { type: 'historyGrouping' },
                options: [
                    { value: 'time', label: tr('By time') },
                    { value: 'type', label: tr('By Search Type') },
                    { value: 'group', label: tr('By folder') }
                ]
            },
            {
                kind: 'Switch',
                field: 'archived',
                title: 'Archived conversations',
                action: { type: 'historyArchived' }
            },
            {
                kind: 'Button',
                id: 'agentHistoryNewGroup',
                title: 'New conversation folder',
                icon: 'create-new-folder',
                action: { type: 'historyGroupEdit', value: '' }
            }
        ];
        nodes.push(
            node(
                'Box',
                'agentHistoryOptionsForm',
                rect(0, 48, width, height - 60),
                {
                    children: Settings.describe(
                        { fields, values: model.history, busy: !idle },
                        width,
                        height - 60,
                        language
                    ).nodes
                }
            )
        );
        return { nodes };
    }
    if (edit) {
        const fields =
            edit.kind === 'group'
                ? [
                      {
                          kind: 'Field',
                          field: 'name',
                          title: 'Folder name',
                          action: { type: 'historyName' },
                          props: { maxLength: 120 }
                      }
                  ]
                : [
                      {
                          kind: 'Field',
                          field: 'title',
                          title: 'Conversation name',
                          action: { type: 'historyTitle' },
                          props: { maxLength: 160 }
                      },
                      {
                          kind: 'Choice',
                          field: 'group',
                          title: 'Conversation folder',
                          action: { type: 'historyFolder' },
                          options: [
                              { value: '', label: tr('Ungrouped') }
                          ].concat(
                              (model.groups || []).map((group) => ({
                                  value: group.id,
                                  label: group.name,
                                  dataLabel: true
                              }))
                          )
                      },
                      {
                          kind: 'Switch',
                          field: 'pinned',
                          title: 'Pin conversation',
                          action: { type: 'historyPinned' }
                      }
                  ];
        nodes.push(
            node(
                'Box',
                'agentHistoryEditor',
                rect(0, 48, width, Math.max(60, height - 176)),
                {
                    children: Settings.describe(
                        { fields, values: edit, busy: !idle },
                        width,
                        Math.max(60, height - 176),
                        language
                    ).nodes
                }
            )
        );
        if (edit.confirm)
            nodes.push(
                label(
                    'agentHistoryRemoveNotice',
                    rect(16, height - 128, width - 32, 64),
                    tr(
                        'Remove this folder? Its conversations will move to Ungrouped.'
                    ),
                    Object.assign({}, muted, { wrap: true })
                )
            );
        else if (edit.id)
            nodes.push(
                button(
                    'agentHistoryArchive',
                    rect(12, height - 120, width - 24, 32),
                    tr(
                        edit.kind === 'group'
                            ? 'Remove folder'
                            : edit.archived
                              ? 'Restore conversation'
                              : 'Archive conversation'
                    ),
                    edit.kind === 'group'
                        ? 'delete'
                        : edit.archived
                          ? 'undo'
                          : 'archive',
                    {
                        type:
                            edit.kind === 'group'
                                ? 'historyRemoveConfirm'
                                : 'historyArchive'
                    },
                    idle &&
                        (edit.kind === 'group' ||
                            !['queued', 'running', 'cancelling'].includes(
                                edit.status
                            ))
                )
            );
        nodes.push(
            button(
                'agentHistorySave',
                rect(12, height - 48, (width - 32) / 2, 32),
                tr(edit.confirm ? 'Remove folder' : 'Save'),
                edit.confirm ? 'delete' : 'save',
                { type: edit.confirm ? 'historyGroupRemove' : 'historySave' },
                idle && (edit.kind !== 'group' || !!edit.name.trim()),
                { highlighted: true, destructive: !!edit.confirm }
            ),
            button(
                'agentHistoryCancel',
                rect(20 + (width - 32) / 2, height - 48, (width - 32) / 2, 32),
                tr('Cancel'),
                'close',
                { type: 'historyCancel' },
                idle
            )
        );
        return { nodes };
    }
    const searching = model.history.searchOpen || !!model.history.query;
    const listTop = searching ? 132 : 88;
    const footer = model.next_offset == null ? 0 : 40;
    nodes.push(
        listAction(
            'agentHistorySearchToggle',
            rect(width - 112, 8, 32, 32),
            tr('Search conversations'),
            'search',
            { type: 'historySearch' },
            true,
            { iconOnly: true }
        ),
        listAction(
            'agentHistoryOptions',
            rect(width - 76, 8, 32, 32),
            tr('Conversation view'),
            'more-horiz',
            { type: 'historyOptions' },
            idle,
            { iconOnly: true }
        ),
        listAction(
            'agentHistoryNew',
            rect(12, 48, width - 24, 32),
            tr('New conversation'),
            'add',
            { type: 'historyNew' },
            idle
        ),
        node(
            'List',
            'agentHistoryList',
            rect(
                0,
                listTop,
                width,
                Math.max(36, height - listTop - 12 - footer)
            ),
            {
                source: 'agentHistoryRows',
                rowHeight: 36,
                keyField: 'key',
                fields: [
                    'key',
                    'kind',
                    'title',
                    'default_title',
                    'folder',
                    'request_id',
                    'status',
                    'pinned'
                ],
                role: 'list',
                label: tr('Conversations')
            }
        )
    );
    if (searching)
        nodes.push(
            node('Field', 'agentHistorySearch', rect(12, 88, width - 24, 32), {
                label: tr('Search conversations'),
                placeholder: tr('Search conversations'),
                text: model.history.query,
                maxLength: 200,
                action: { type: 'historyQuery' }
            })
        );
    if (footer)
        nodes.push(
            listAction(
                'agentHistoryMore',
                rect(12, height - 40, width - 24, 28),
                tr('Load more conversations'),
                'expand-more',
                { type: 'historyMore' },
                idle
            )
        );
    if (!model.requests.length)
        nodes.push(
            label(
                'agentHistoryEmpty',
                rect(16, listTop + 12, width - 32, 52),
                tr(
                    model.history.query
                        ? 'No conversations found'
                        : 'No conversations yet'
                ),
                Object.assign({}, muted, { wrap: true })
            )
        );
    if (!small)
        nodes.push(
            node(
                'Splitter',
                'agentHistorySplitter',
                rect(width - 4, 0, 4, height),
                {
                    text: tr('Conversations panel width'),
                    value: model.history.width,
                    min: 220,
                    max: 420,
                    action: { type: 'historyWidth' }
                }
            )
        );
    return { nodes };
}

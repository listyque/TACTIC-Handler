import { node, rect, label, button, muted } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

const serviceViews = [
    'definition',
    'default_definition',
    'edit_definition',
    'edit',
    'insert',
    'search',
    'filter',
    'custom_filter',
    'simple_filter'
];
export function choices(views) {
    return views.filter(
        (row) =>
            typeof row.view === 'string' && !serviceViews.includes(row.view)
    );
}
export function initial() {
    return { query: '', selected: 'table', mode: '', title: '' };
}
export function loaded(ui, model) {
    const selected = model.selected || ui.selected;
    return Object.assign({}, ui, {
        selected: model.views.some((row) => row.view === selected)
            ? selected
            : model.current || 'table',
        mode: '',
        title: ''
    });
}
export function rows(model, ui) {
    const query = ui.query.trim().toLocaleLowerCase();
    return model.views.filter((row) =>
        (row.title + ' ' + row.view).toLocaleLowerCase().includes(query)
    );
}
export function transition(ui, model, action) {
    if (model.busy) return { ui };
    const selected = model.views.find((row) => row.view === ui.selected);
    if (action.type === 'query')
        return { ui: Object.assign({}, ui, { query: action.value }) };
    if (action.type === 'title')
        return { ui: Object.assign({}, ui, { title: action.value }) };
    if (action.type === 'select')
        return {
            ui: Object.assign({}, ui, {
                selected: action.view,
                mode: '',
                title: ''
            })
        };
    if (action.type === 'cancel')
        return { ui: Object.assign({}, ui, { mode: '', title: '' }) };
    if (['create', 'copy', 'rename', 'delete'].includes(action.type)) {
        if (!model.revision || model.uncertain) return { ui };
        if (action.type !== 'create' && !selected) return { ui };
        if (['rename', 'delete'].includes(action.type) && selected.protected)
            return { ui };
        return {
            ui: Object.assign({}, ui, {
                mode: action.type,
                title: action.type === 'rename' ? selected.title : ''
            })
        };
    }
    if (action.type === 'apply') {
        if (!model.revision || model.uncertain) return { ui };
        if (!ui.mode || (ui.mode !== 'delete' && !ui.title.trim()))
            return { ui };
        return {
            ui,
            command: {
                action: ui.mode,
                view: ui.selected,
                title: ui.title.trim(),
                revision: model.revision
            }
        };
    }
    if (['read', 'use', 'configure'].includes(action.type))
        return { ui, command: { action: action.type, view: ui.selected } };
    return { ui };
}
export function describe(model, ui, width, height, language) {
    const tr = (key) => translate(key, language);
    if (width < 600 || height < 540)
        return {
            nodes: [
                node(
                    'Scroll',
                    'tableViewsWindowScroll',
                    rect(0, 0, width, height),
                    {
                        contentWidth: Math.max(600, width - 16),
                        contentHeight: Math.max(540, height),
                        scrollbarId: 'tableViewsWindowScrollBar',
                        children: describe(
                            model,
                            ui,
                            Math.max(600, width - 16),
                            Math.max(540, height),
                            language
                        ).nodes
                    }
                )
            ]
        };
    const left = Math.min(320, width * 0.4),
        x = left + 24,
        inner = width - x - 16;
    const selected = model.views.find((row) => row.view === ui.selected);
    const enabled =
        !!model.revision && !model.busy && !model.uncertain && !ui.mode;
    const nodes = [
        node('Box', 'tableViewsHeader', rect(0, 0, width, 50), {
            background: 'surfaceContainerHigh',
            children: [
                label(
                    'tableViewsContext',
                    rect(16, 8, width - 72, 34),
                    (model.projectTitle || model.project) +
                        ' · ' +
                        (model.searchTitle || model.searchType),
                    { weight: 600 }
                ),
                button(
                    'tableViewsRefresh',
                    rect(width - 48, 9, 32, 32),
                    tr('Refresh'),
                    'refresh',
                    { type: 'read' },
                    !model.busy,
                    { iconOnly: true }
                )
            ]
        }),
        node('Box', 'tableViewsCatalog', rect(12, 62, left, height - 124), {
            background: 'surfaceContainerLow',
            border: 'outlineVariant',
            children: [
                node('Field', 'tableViewsSearch', rect(10, 10, left - 20, 34), {
                    text: ui.query,
                    label: tr('Find a table view'),
                    placeholder: tr('Find a table view'),
                    enabled: !model.busy,
                    action: { type: 'query' }
                }),
                node(
                    'List',
                    'tableViewsList',
                    rect(10, 54, left - 20, height - 190),
                    {
                        source: 'views',
                        keyField: 'view',
                        rowHeight: 52,
                        fields: [],
                        scrollbarId: 'tableViewsListScrollBar'
                    }
                )
            ]
        }),
        node('Box', 'tableViewsDetails', rect(x, 62, inner, height - 124), {
            background: 'surfaceContainerLow',
            border: 'outlineVariant',
            children: []
        })
    ];
    const body = nodes[2].children;
    if (selected) {
        body.push(
            label(
                'tableViewsTitle',
                rect(16, 14, inner - 32, 32),
                selected.view === 'table'
                    ? tr('Default table')
                    : selected.title,
                { fontRole: 'section', weight: 600 }
            )
        );
        body.push(
            label(
                'tableViewsCode',
                rect(16, 52, inner - 32, 24),
                selected.view,
                muted
            )
        );
        body.push(
            label(
                'tableViewsScope',
                rect(16, 86, inner - 32, 54),
                tr(
                    selected.protected
                        ? 'The default table is protected. Create a copy to customize it.'
                        : 'Project view. Renaming changes its label and keeps existing links.'
                ),
                { wrap: true, color: 'secondaryText' }
            )
        );
        body.push(
            label(
                'tableViewsColumns',
                rect(16, 146, inner - 32, 26),
                tr('Columns') + ': ' + selected.columns
            )
        );
        body.push(
            label(
                'tableViewsCurrent',
                rect(16, 176, inner - 32, 24),
                selected.view === model.current ? tr('Current view') : '',
                { color: 'action' }
            )
        );
    }
    if (ui.mode) {
        const deleting = ui.mode === 'delete';
        body.push(
            label(
                'tableViewsEditHeading',
                rect(16, 218, inner - 32, 28),
                tr(
                    {
                        create: 'New table view',
                        copy: 'Duplicate table view',
                        rename: 'Rename table view',
                        delete: 'Delete table view'
                    }[ui.mode]
                ),
                { weight: 600 }
            )
        );
        if (deleting)
            body.push(
                label(
                    'tableViewsDeleteWarning',
                    rect(16, 250, inner - 32, 64),
                    tr(
                        'Delete this project view and its saved layers? Existing links to it may stop working.'
                    ),
                    { wrap: true, color: 'error' }
                )
            );
        else
            body.push(
                node('Field', 'tableViewsName', rect(16, 252, inner - 32, 36), {
                    text: ui.title,
                    label: tr('View name'),
                    enabled: !model.busy,
                    action: { type: 'title' },
                    props: { maxLength: 120 }
                })
            );
        body.push(
            button(
                'tableViewsApply',
                rect(16, 326, 124, 32),
                tr(deleting ? 'Delete' : 'Save'),
                deleting ? 'delete' : 'save',
                { type: 'apply' },
                !model.busy &&
                    !model.uncertain &&
                    (deleting || !!ui.title.trim()),
                { highlighted: !deleting, destructive: deleting }
            )
        );
        body.push(
            button(
                'tableViewsCancel',
                rect(150, 326, 112, 32),
                tr('Cancel'),
                'close',
                { type: 'cancel' },
                !model.busy
            )
        );
    } else {
        for (const [index, entry] of [
            ['create', 'New view', 'add'],
            ['copy', 'Duplicate', 'content-copy'],
            ['rename', 'Rename', 'edit'],
            ['delete', 'Delete', 'delete']
        ].entries())
            nodes.push(
                button(
                    'tableViews_' + entry[0],
                    rect(12 + index * 146, height - 48, 138, 32),
                    tr(entry[1]),
                    entry[2],
                    { type: entry[0] },
                    enabled &&
                        (entry[0] === 'create' ||
                            (!!selected &&
                                (!['rename', 'delete'].includes(entry[0]) ||
                                    !selected.protected))),
                    { destructive: entry[0] === 'delete' }
                )
            );
        body.push(
            button(
                'tableViewsUse',
                rect(16, 228, Math.min(inner - 32, 160), 34),
                tr('Use this view'),
                'check',
                { type: 'use' },
                enabled && !!selected,
                { highlighted: true }
            )
        );
        body.push(
            button(
                'tableViewsConfigure',
                rect(16, 272, Math.min(inner - 32, 200), 34),
                tr('Configure columns'),
                'view-column',
                { type: 'configure' },
                enabled && !!selected
            )
        );
    }
    if (model.error || model.busy)
        nodes.push(
            label(
                'tableViewsStatus',
                rect(x + 16, height - 94, inner - 32, 30),
                model.error || tr('Working on the server…'),
                { color: model.error ? 'error' : 'secondaryText', wrap: true }
            )
        );
    return { nodes };
}
export function row(list, record, ui, model, language) {
    const title =
        record.view === 'table'
            ? translate('Default table', language)
            : record.title;
    return {
        nodes: [
            node(
                'Action',
                'tableView_' + record.view,
                rect(0, 0, list.width - 16, 50),
                {
                    text: title,
                    selected: ui.selected === record.view,
                    normalColor: 'transparent',
                    selectedColor: 'contentSelection',
                    rail: false,
                    enabled: !model.busy && !ui.mode,
                    action: { type: 'select', view: record.view },
                    children: [
                        node('Icon', 'tableViewIcon', rect(8, 15, 20, 20), {
                            icon:
                                record.view === model.current
                                    ? 'check'
                                    : 'table-view',
                            color: 'action'
                        }),
                        label(
                            'tableViewTitle',
                            rect(36, 4, list.width - 60, 24),
                            title,
                            { weight: 600 }
                        ),
                        label(
                            'tableViewCode',
                            rect(36, 28, list.width - 60, 18),
                            record.view,
                            muted
                        )
                    ]
                }
            )
        ]
    };
}

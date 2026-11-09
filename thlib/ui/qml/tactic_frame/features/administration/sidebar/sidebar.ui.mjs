import { row as treeRow } from '../../../controls/lists/tree.ui.mjs';
import { button } from '../../../core/frame.mjs';
import { node } from '../../../core/frame.mjs';
import {
    rect,
    label,
    muted,
    policy,
    toolbar,
    notices,
    tabs
} from '../admin.document.mjs';
import { sections as form } from '../../../controls/forms/sections.ui.mjs';
import { translate } from '../../../core/strings.mjs';
export { toolbar };
const list = (id, bounds, source, rowHeight) =>
    node('List', id, bounds, {
        source,
        rowHeight,
        keyField: 'index',
        fields: [],
        role: source === 'entries' ? 'tree' : undefined,
        scrollbarId: id + 'ScrollBar'
    });
export function describe(model, ui, width, height, language) {
    if (width <= 0 || height <= 0)
        return {
            nodes: []
        };
    const tr = (text) => translate(text, language),
        edit = policy(model).editable && !ui.confirmation;
    const notice = notices(
        model,
        ui,
        width,
        language,
        ui.confirmation === 'delete'
            ? 'Delete the selected sidebar item?'
            : 'Discard unsaved sidebar changes?',
        ui.confirmation === 'delete' ? 'Delete item' : ''
    );
    const nodes = notice.nodes;
    let y = notice.top;
    const compact = width < 750,
        h = compact ? 142 : 58;
    const minimum = notice.top + h + (compact ? 328 : 316);
    if (height < minimum)
        return {
            nodes: [
                node('Scroll', 'sidebarPageScroll', rect(0, 0, width, height), {
                    contentHeight: minimum,
                    scrollbarId: 'sidebarPageScrollBar',
                    children: describe(
                        model,
                        ui,
                        Math.max(1, width - 16),
                        minimum,
                        language
                    ).nodes
                })
            ]
        };
    nodes.push(
        node('Box', 'sidebarHeading', rect(0, y, width, h), {
            background: 'surfaceContainerHigh',
            children: [
                label(
                    'sidebarTitle',
                    rect(14, 6, compact ? width - 108 : width - 472, 24),
                    tr('Project navigation'),
                    {
                        weight: 600
                    }
                ),
                label(
                    'sidebarProject',
                    rect(14, 30, compact ? width - 28 : width - 472, 22),
                    model.projectTitle,
                    muted
                ),
                tabs(
                    'sidebarSourceSelector',
                    [
                        {
                            value: 'handler',
                            label: 'TH',
                            icon: 'desktop'
                        },
                        {
                            value: 'tactic',
                            label: 'TACTIC',
                            icon: 'globe'
                        }
                    ],
                    model.source,
                    rect(
                        compact ? 12 : width - 450,
                        compact ? 58 : 10,
                        compact ? (width - 32) / 2 : 164,
                        38
                    ),
                    edit,
                    'source'
                ),
                tabs(
                    'sidebarModeSelector',
                    [
                        {
                            value: 'simple',
                            label: tr('Simple'),
                            icon: 'table'
                        },
                        {
                            value: 'xml',
                            label: 'XML',
                            icon: 'code'
                        }
                    ],
                    ui.mode,
                    rect(
                        compact ? width / 2 + 4 : width - 278,
                        compact ? 58 : 10,
                        compact ? (width - 32) / 2 : 180,
                        38
                    ),
                    edit,
                    'mode'
                ),
                button(
                    'sidebarReload',
                    rect(width - 88, compact ? 6 : 10, 38, 38),
                    tr('Reload sidebar'),
                    'refresh',
                    {
                        type: 'reload'
                    },
                    !model.busy,
                    {
                        iconOnly: true
                    }
                ),
                button(
                    'sidebarHelp',
                    rect(width - 46, compact ? 6 : 10, 38, 38),
                    tr('Sidebar Editor help'),
                    'help',
                    {
                        type: 'help'
                    },
                    true,
                    {
                        iconOnly: true
                    }
                ),
                ...(compact
                    ? [
                          label(
                              'sidebarStatus',
                              rect(12, 104, width - 24, 30),
                              tr(
                                  model.dirty
                                      ? 'Sidebar has unsaved changes'
                                      : 'Sidebar is up to date'
                              ),
                              muted
                          )
                      ]
                    : [])
            ]
        })
    );
    y += h + 8;
    if (!model.ready) {
        nodes.push(
            label(
                'sidebarEmpty',
                rect(12, y, width - 24, 70),
                tr(model.busy ? 'Working on the server…' : 'Select a project'),
                {
                    wrap: true
                }
            )
        );
        return {
            nodes
        };
    }
    const split = width >= 850,
        treeVisible = ui.treeVisible !== false,
        treeWidth = split
            ? treeVisible
                ? Math.min(Math.max(280, ui.treeWidth), width * 0.48)
                : 56
            : width,
        minHeight = split ? 270 : 320;
    const contentHeight = Math.max(minHeight, height - y - (compact ? 0 : 38));
    const children = [];
    if (split || !ui.editing)
        tree(
            children,
            model,
            ui,
            rect(0, 0, treeWidth, contentHeight),
            language,
            edit,
            split
        );
    if (split && treeVisible)
        children.push(
            node(
                'Splitter',
                'sidebarSplitter',
                rect(treeWidth, 0, 10, contentHeight),
                {
                    text: tr('Sidebar preview width'),
                    value: treeWidth,
                    min: 280,
                    max: width * 0.48,
                    action: {
                        type: 'split'
                    }
                }
            )
        );
    if (split || ui.editing)
        editor(
            children,
            model,
            ui,
            rect(
                split ? treeWidth + 10 : 0,
                0,
                split ? width - treeWidth - 10 : width,
                contentHeight
            ),
            language,
            edit,
            !split
        );
    if (contentHeight > height - y)
        nodes.push(
            node(
                'Scroll',
                'sidebarPageScroll',
                rect(0, y, width, Math.max(1, height - y)),
                {
                    contentHeight,
                    scrollbarId: 'sidebarPageScrollBar',
                    children: children.map((item) =>
                        Object.assign({}, item, {
                            width: Math.max(1, item.width - 16)
                        })
                    )
                }
            )
        );
    else
        nodes.push(
            node('Box', 'sidebarColumns', rect(0, y, width, contentHeight), {
                children
            })
        );
    if (!compact)
        nodes.push(
            label(
                'sidebarStatus',
                rect(0, height - 30, width, 30),
                tr(
                    model.dirty
                        ? 'Sidebar has unsaved changes'
                        : 'Sidebar is up to date'
                ),
                muted
            )
        );
    return {
        nodes
    };
}
function tree(nodes, model, ui, bounds, language, edit, split = false) {
    const tr = (text) => translate(text, language),
        width = bounds.width,
        treeVisible = !split || ui.treeVisible !== false,
        children = [];
    if (treeVisible) {
        children.push(
            label(
                'sidebarTreeTitle',
                rect(12, 10, Math.max(0, width - (split ? 62 : 24)), 34),
                tr(
                    model.source === 'handler' ? 'TH sidebar' : 'TACTIC sidebar'
                ),
                {
                    weight: 600
                }
            )
        );
        let y = 52;
        if (model.source === 'handler') {
            children.push(
                node(
                    'Choice',
                    'sidebarGroupPreview',
                    rect(12, y, width - 24, 38),
                    {
                        label: tr('Preview group'),
                        options: model.previewOptions.map((option) => ({
                            value: option.value,
                            label: option.label
                        })),
                        value: model.previewGroup,
                        enabled: edit,
                        action: {
                            type: 'preview'
                        }
                    }
                )
            );
            y += 46;
        }
        children.push(
            label(
                'sidebarAddLabel',
                rect(12, y, width - 158, 38),
                tr('Add'),
                muted
            )
        );
        [
            ['link', 'Add link', 'add'],
            ['section', 'Add section', 'folder'],
            ['separator', 'Add separator', 'sidebar-separator']
        ].forEach(([value, text, icon], index) =>
            children.push(
                button(
                    'sidebarAdd_' + value,
                    rect(width - 138 + index * 42, y, 38, 38),
                    tr(text),
                    icon,
                    {
                        type: 'add',
                        value
                    },
                    edit,
                    {
                        iconOnly: true,
                        round: false
                    }
                )
            )
        );
        y += 46;
        children.push(
            list(
                'sidebarEditorEntries',
                rect(8, y, width - 16, bounds.height - y - 8),
                'entries',
                64
            )
        );
        if (!model.entries.length)
            children.push(
                label(
                    'sidebarTreeEmpty',
                    rect(20, y + 12, width - 40, 70),
                    tr(
                        model.previewGroup
                            ? 'This group has no sidebar items'
                            : 'This sidebar has no items'
                    ),
                    {
                        wrap: true,
                        color: 'secondaryText'
                    }
                )
            );
    }
    if (split)
        children.push(
            button(
                'sidebarToggleTree',
                rect(treeVisible ? width - 46 : (width - 34) / 2, 10, 34, 34),
                tr(treeVisible ? 'Hide sidebar tree' : 'Show sidebar tree'),
                treeVisible ? 'chevron-left' : 'chevron-right',
                {
                    type: 'treeVisible'
                },
                true,
                {
                    iconOnly: true,
                    iconAction: true,
                    round: false
                }
            )
        );
    nodes.push(
        node('Box', 'sidebarTreePanel', bounds, {
            background: 'surfaceContainerLow',
            border: 'outlineVariant',
            children
        })
    );
}
function editor(nodes, model, ui, bounds, language, edit, back) {
    const tr = (text) => translate(text, language),
        width = bounds.width,
        inner = width - 40,
        children = [],
        entry = model.entry;
    let y = 12;
    if (back) {
        children.push(
            button(
                'sidebarBack',
                rect(12, y, 110, 36),
                tr('Back'),
                'chevron-left',
                {
                    type: 'back'
                },
                !model.busy
            )
        );
        y += 44;
    }
    children.push(
        label(
            'sidebarSelectedTitle',
            rect(12, y, width - 164, 38),
            entry.title || tr('Selected element'),
            {
                fontRole: 'section',
                weight: 600
            }
        )
    );
    [
        ['up', 'Move up', 'arrow-up', -1],
        ['down', 'Move down', 'arrow-down', 1],
        ['delete', 'Delete item', 'delete', 0]
    ].forEach(([key, text, icon, value], index) =>
        children.push(
            button(
                'sidebarItem_' + key,
                rect(width - 140 + index * 42, y, 38, 38),
                tr(text),
                icon,
                {
                    type: value ? 'move' : 'delete',
                    value
                },
                edit && model.selected >= 0,
                {
                    iconOnly: true
                }
            )
        )
    );
    y += 46;
    if (model.selected < 0)
        children.push(
            label(
                'sidebarSelectHelp',
                rect(12, y, inner, 100),
                tr(
                    'Select an item in the preview to edit it, or add a new link or section.'
                ),
                {
                    wrap: true,
                    color: 'secondaryText'
                }
            )
        );
    else if (ui.mode === 'xml') {
        children.push(
            label(
                'sidebarXmlTitle',
                rect(12, y, inner, 26),
                tr('Advanced XML'),
                {
                    weight: 600
                }
            )
        );
        y += 34;
        children.push(
            node(
                'Area',
                'sidebarXml',
                rect(12, y, inner, Math.max(90, bounds.height - y - 58)),
                {
                    text: ui.xml === null ? model.xml : ui.xml,
                    label: tr('Selected element XML'),
                    monospace: true,
                    enabled: edit,
                    action: {
                        type: 'xml'
                    }
                }
            ),
            button(
                'sidebarApplyXml',
                rect(12, bounds.height - 46, inner, 38),
                tr('Apply XML'),
                'code',
                {
                    type: 'apply'
                },
                edit && ui.xml !== null
            )
        );
    } else {
        children.push(
            tabs(
                'sidebarPages',
                [
                    ['item', 'Item', 'edit'],
                    ['access', 'Access', 'groups'],
                    ['technical', 'Technical', 'code']
                ].map(([value, text, icon]) => ({
                    value,
                    label: tr(text),
                    icon
                })),
                ui.page,
                rect(12, y, width - 24, 38),
                !model.busy,
                'page'
            )
        );
        y += 46;
        if (ui.page === 'access') {
            children.push(
                label(
                    'sidebarAccessHeading',
                    rect(12, y, inner, 28),
                    tr('Who can see this item'),
                    {
                        fontRole: 'section',
                        weight: 600,
                        role: 'heading',
                        level: 2
                    }
                )
            );
            y += 36;
            children.push(
                label(
                    'sidebarAccessHelp',
                    rect(12, y, inner, 72),
                    tr(
                        'Select the login groups allowed to see this sidebar item. The group preview uses these draft permissions immediately.'
                    ),
                    Object.assign(
                        {
                            wrap: true
                        },
                        muted
                    )
                )
            );
            y += 80;
            children.push(
                button(
                    'manageSidebarGroups',
                    rect(12, y, width - 24, 38),
                    tr('Manage groups and members'),
                    'groups',
                    {
                        type: 'groups'
                    },
                    edit && !model.dirty
                )
            );
            y += 46;
            children.push(
                list(
                    'sidebarAccessGroups',
                    rect(
                        12,
                        y,
                        width - 24,
                        Math.max(1, bounds.height - y - 12)
                    ),
                    'groups',
                    42
                )
            );
            if (!model.groups.length)
                children.push(
                    label(
                        'sidebarNoGroups',
                        rect(12, y, inner, 72),
                        tr('No login groups were loaded from the server.'),
                        {
                            wrap: true,
                            color: 'secondaryText'
                        }
                    )
                );
        } else {
            const body = form(
                fields(model, ui, language),
                inner,
                language,
                edit
            );
            children.push(
                node(
                    'Scroll',
                    'sidebarSettingsViewport',
                    rect(
                        12,
                        y,
                        width - 24,
                        Math.max(1, bounds.height - y - 12)
                    ),
                    {
                        contentHeight: body.height,
                        resetKey: ui.page + ':' + entry.name,
                        scrollbarId: 'sidebarSettingsScrollBar',
                        children: body.nodes
                    }
                )
            );
        }
    }
    nodes.push(
        node('Box', 'sidebarEntryPanel', bounds, {
            background: 'surfaceContainerLow',
            border: 'outlineVariant',
            children
        })
    );
}
function fields(model, ui, language) {
    const tr = (text) => translate(text, language),
        entry = model.entry,
        link = entry.entryType === 'link',
        section = entry.entryType === 'section',
        text = (field) =>
            Object.prototype.hasOwnProperty.call(ui.text, field)
                ? ui.text[field]
                : entry[field] || '';
    const heading = (id, title, description) => ({
        id,
        kind: 'Heading',
        title,
        description
    });
    const field = (id, key, title, description, extra) =>
        Object.assign(
            {
                id,
                field: key,
                title,
                description,
                props: {
                    text: text(key),
                    action: {
                        type: 'text',
                        field: key
                    }
                }
            },
            extra || {}
        );
    const optionsWithEmpty = (options, title) =>
        options.some((option) => option.value === '')
            ? options.map((option) =>
                  option.value === ''
                      ? {
                            value: '',
                            label: tr(title)
                        }
                      : option
              )
            : [
                  {
                      value: '',
                      label: tr(title)
                  }
              ].concat(options);
    const choice = (id, key, title, description, options) =>
        field(id, key, title, description, {
            kind: 'Choice',
            options,
            props: {
                value: entry[key] || ''
            }
        });
    const action = (id, title, type, enabled) => ({
        id,
        kind: 'Button',
        title,
        props: {
            text: tr(title),
            enabled,
            action: {
                type
            }
        }
    });
    if (ui.page === 'technical')
        return [
            heading(
                'sidebarTechnicalHeading',
                'Technical settings',
                'TACTIC identifiers and widget options. For normal setup, use Item.'
            ),
            choice(
                'sidebarItemType',
                'entryType',
                'Item type',
                'A link opens a search, a section groups links, and a separator divides the list.',
                [
                    ['link', 'Link'],
                    ['section', 'Section'],
                    ['separator', 'Separator']
                ].map(([value, label]) => ({
                    value,
                    label: tr(label)
                }))
            ),
            field(
                'sidebarNameField',
                'name',
                'Internal name',
                'The stable identifier for this sidebar item and its quick-filter defaults. Change the title for a visual rename.'
            ),
            field(
                'sidebarChildView',
                'targetView',
                'Child view',
                "The SideBarWdg view containing this section's links.",
                {
                    when: section
                }
            ),
            field(
                'sidebarIconName',
                'icon',
                'Icon name',
                'The server icon identifier. You can also choose an icon on the Item page.',
                {
                    when: entry.entryType !== 'separator'
                }
            ),
            Object.assign(
                choice(
                    'sidebarWidgetType',
                    'widgetType',
                    'Widget Type',
                    'The TACTIC web widget used by this link.',
                    model.widgetOptions
                ),
                {
                    when: link
                }
            ),
            field(
                'sidebarClassName',
                'displayClassName',
                'Class Path',
                'The Python class registered for this TACTIC widget.',
                {
                    when: link && entry.widgetType === '__class__'
                }
            ),
            field(
                'sidebarDisplayView',
                'displayView',
                'View',
                'The server view used to render the selected TACTIC widget.',
                {
                    when:
                        link &&
                        [
                            'custom_layout',
                            'edit_layout',
                            'tile_layout',
                            'fast_layout'
                        ].indexOf(entry.widgetType) >= 0
                }
            )
        ];
    return [
        heading(
            'sidebarAppearance',
            'Appearance',
            'How this item appears in project navigation. Selection follows your theme.'
        ),
        field(
            'sidebarTitleField',
            'title',
            'Title',
            'A short, recognizable name in the sidebar.'
        ),
        {
            id: 'sidebarIconPicker',
            kind: 'IconChoice',
            title: 'Icon',
            description:
                'Click the icon to choose from the searchable library.',
            field: 'icon',
            when: entry.entryType !== 'separator',
            props: {
                value: entry.glyph || entry.icon,
                tacticCompatibleOnly: true
            }
        },
        field(
            'sidebarColorField',
            'color',
            'Navigation color',
            'Optional #RRGGBB override; leave empty to use the Search Type color.'
        ),
        {
            id: 'sidebarEntryVisibleCheck',
            kind: 'CheckBox',
            title: 'Visible in navigation',
            description: 'Hide this item without deleting its settings.',
            field: 'isVisible',
            props: {
                checked: entry.isVisible
            }
        },
        ...(link
            ? [
                  heading(
                      'sidebarSearchHeading',
                      'Search and quick filters',
                      "The saved search defines the starting query. Quick filters refine it in the same search tab and use this item's own defaults."
                  ),
                  choice(
                      'sidebarSearchType',
                      'searchType',
                      'Search Type',
                      'Which project objects this item opens.',
                      model.typeOptions
                  ),
                  choice(
                      'sidebarSearchPreset',
                      'searchView',
                      'Predefined search',
                      'Choose a saved query or leave the list unfiltered.',
                      optionsWithEmpty(
                          model.presetOptions,
                          'No predefined search'
                      )
                  ),
                  ...(model.streamApi !== false &&
                  entry.widgetType === 'custom_layout' &&
                  entry.displayView?.startsWith('dashboard.')
                      ? [
                            action(
                                'sidebarEditPage',
                                'Edit page layout',
                                'pageLayout',
                                !model.dirty
                            )
                        ]
                      : []),
                  action(
                      'sidebarSearchSetupButton',
                      'Configure search',
                      'search',
                      !model.dirty && !!entry.searchType && !!entry.isVisible
                  ),
                  choice(
                      'sidebarResultView',
                      'resultViewMode',
                      'Default item view',
                      'The initial presentation when this search tab is opened.',
                      model.resultOptions
                  ),
                  choice(
                      'sidebarLayoutPreset',
                      'layoutPreset',
                      'Workspace layout',
                      'Apply a saved dock arrangement when this sidebar item opens.',
                      optionsWithEmpty(
                          model.layoutOptions,
                          'Do not change workspace layout'
                      )
                  ),
                  choice(
                      'sidebarScriptShelf',
                      'scriptShelf',
                      'Script shelf',
                      'Show this shared shelf when the sidebar tab is active.',
                      optionsWithEmpty(
                          model.shelfOptions,
                          'Project default shelf'
                      )
                  )
              ]
            : [])
    ];
}
export function row(listNode, record, model, ui, language) {
    if (listNode.source === 'groups')
        return {
            nodes: [
                node(
                    'CheckBox',
                    'sidebarGroup_' + record.code,
                    rect(0, 0, listNode.width - 16, 38),
                    {
                        text: record.label,
                        label: record.label,
                        checked: record.allowed,
                        enabled: policy(model).editable && !ui.confirmation,
                        indicatorX: 8,
                        action: {
                            type: 'group',
                            code: record.code
                        },
                        children: [
                            label(
                                'sidebarGroupLabel_' + record.code,
                                rect(36, 0, listNode.width - 56, 38),
                                record.label
                            )
                        ]
                    }
                )
            ]
        };
    return treeRow(
        'sidebarEditorEntry_' + record.index,
        listNode.width - 16,
        {
            title:
                record.entryType === 'separator'
                    ? translate('Separator', language)
                    : record.title,
            subtitle: record.searchType,
            depth: record.displayDepth || record.depth || 0,
            icon: record.glyph || record.icon || 'link',
            accent: record.accent || '',
            hasChildren: record.entryType === 'section',
            expanded: record.expanded
        },
        {
            selected: record.index === model.selected,
            enabled: !model.busy && !ui.confirmation,
            dim: !record.isVisible || record.included === false,
            select: { type: 'select', index: record.index },
            keys: [
                'ArrowUp',
                'ArrowDown',
                'ArrowLeft',
                'ArrowRight',
                'Home',
                'End'
            ].reduce((keys, key) => {
                keys[key] = { type: 'treeKey', index: record.index, key };
                return keys;
            }, {}),
            toggle: { type: 'toggle', index: record.index },
            toggleEnabled: !model.busy,
            toggleLabel: translate(
                record.expanded ? 'Collapse section' : 'Expand section',
                language
            ),
            ids: {
                icon: 'sidebarEntryIcon_' + record.index,
                title: 'sidebarEntryTitle_' + record.index,
                detail: 'sidebarEntryType_' + record.index,
                toggle: 'sidebarEntryToggle_' + record.index
            }
        }
    );
}

import { button } from '../../../core/frame.mjs';
import { node } from '../../../core/frame.mjs';
import {
    rect,
    label,
    muted,
    policy,
    toolbar as documentToolbar,
    notices,
    tabs
} from '../admin.document.mjs';
import { translate } from '../../../core/strings.mjs';
import * as Access from './security.access.mjs';
import {
    inheritanceChoices,
    matrixScopes,
    pending
} from './security.state.mjs';
export function toolbar(model, ui, width, language) {
    const scene = documentToolbar(model, ui, width, language),
        discard = scene.nodes.find(
            (item) => item.id === 'adminDiscardDocument'
        );
    discard.text = translate('Reset', language);
    discard.toolTip = translate('Discard changes', language);
    return scene;
}

export const scopes = [
    ['effective', 'Effective permissions'],
    ['defaults', 'Group inheritance'],
    ['project', 'Projects'],
    ['builtin', 'Application features'],
    ['link', 'Sidebar links'],
    ['gear_menu', 'Menu actions'],
    ['search_type', 'Search Types'],
    ['process', 'Processes'],
    ['tasks', 'Task statuses'],
    ['sobject', 'Search Objects'],
    ['sobject_column', 'Field access'],
    ['search_filter', 'Search restrictions'],
    ['agent_tool', 'AI tools'],
    ['mcp_tool', 'MCP tools'],
    ['technical', 'Advanced rules']
];
export const levels = [
    ['deny', 'Deny'],
    ['view', 'Read'],
    ['edit', 'Modify'],
    ['insert', 'Create'],
    ['retire', 'Archive'],
    ['delete', 'Delete'],
    ['allow', 'Full access']
];
const levelIcons = {
    deny: 'close',
    view: 'visibility',
    edit: 'edit',
    insert: 'add',
    retire: 'inventory-2',
    delete: 'delete',
    allow: 'check'
};
export const scopeDetails = {
    effective: [
        'person',
        'Inspect saved user permissions and their source groups.'
    ],
    agent_tool: [
        'security',
        'Choose which tools this group can use through the agent chat.'
    ],
    mcp_tool: ['link', 'Choose which tools this group can expose through MCP.'],
    defaults: ['groups', 'Choose the groups whose permissions are inherited.'],
    project: ['folder', 'Choose which projects each group can open.'],
    link: ['link', 'Choose which sidebar links each group can see.'],
    gear_menu: ['menu', 'Choose which menu actions each group can use.'],
    search_type: ['sobject', 'Control access to entity types in this project.'],
    process: ['workflow', 'Control access to the project workflow processes.'],
    tasks: ['tasks', 'Control access to task workflow statuses.'],
    sobject: [
        'sobject',
        'Set permissions for individual records or record keys.'
    ],
    sobject_column: [
        'table-view',
        'Control access to individual entity fields.'
    ],
    builtin: [
        'security',
        'Choose access to individual application features. Legacy rules are marked explicitly.'
    ],
    search_filter: [
        'filter-alt',
        'Limit the records a group can find using native search rules.'
    ],
    technical: [
        'code',
        'Inspect and edit native rules, defaults and custom XML.'
    ]
};
const names = {
    project: ['code'],
    search_type: ['code'],
    process: ['process', 'pipeline'],
    link: ['element'],
    sobject: ['key'],
    sobject_column: ['search_type', 'column'],
    builtin: ['key'],
    gear_menu: ['submenu', 'label'],
    search_filter: ['search_type', 'column', 'op', 'value']
};
const contains = (value, query) =>
    String(value).toLowerCase().indexOf(String(query).trim().toLowerCase()) >=
    0;
const builtinFeatures = {
    view_side_bar: [
        'Sidebar navigation',
        'Show the project navigation sidebar in the legacy interface.'
    ],
    view_site_admin: [
        'Administration',
        'Open administration in the legacy interface. Modern administration still requires an administrator.'
    ],
    view_script_editor: [
        'Script editor',
        'Open the legacy script editor. This does not grant permission to execute scripts.'
    ],
    side_bar_schema: [
        'Schema navigation',
        'Show the schema section of the legacy sidebar.'
    ],
    view_save_my_view: [
        'Saved views',
        'Open and save personal views in the legacy interface.'
    ],
    view_private_notes: [
        'Private notes',
        'Read private notes belonging to other users. The server checks this rule when retrieving notes.'
    ],
    view_column_manager: [
        'Table column manager',
        'Open the column manager in the legacy interface.'
    ],
    view_template_projects: [
        'Template projects',
        'Show template projects in the legacy project list.'
    ],
    create_projects: [
        'Project creation',
        'Create projects through the legacy interface. Modern project creation still requires an administrator.'
    ],
    export_all_csv: [
        'Export all rows to CSV',
        'Export all search results, beyond the current page, in the legacy interface.'
    ],
    import_csv: [
        'CSV import',
        'Import records from CSV through the legacy interface.'
    ],
    retire_delete: [
        'Archive and delete records',
        'Show archive and delete operations in the legacy interface. Record permissions are checked separately.'
    ],
    edit: [
        'Edit records',
        'Show record editing in the legacy interface. Record and field permissions are checked separately.'
    ]
};
function builtinFeature(model, key) {
    const entry =
        (model.metadata.builtinPermissions || []).find(
            (item) => item.key === key
        ) || {};
    const description = builtinFeatures[key];
    return {
        label: description ? description[0] : entry.title || key,
        description: description ? description[1] : entry.description || '',
        active: key === 'view_private_notes',
        known: !!description
    };
}
export function targets(model, scope) {
    return scope === 'builtin'
        ? (model.metadata.builtinPermissions || []).map((item) => ({
              label: builtinFeature(model, item.key).label,
              attributes: {
                  key: item.key
              }
          }))
        : (model.metadata.targets || {})[scope] || [];
}
export function title(record, model, language) {
    const scope = record.group || record.category,
        target = targets(model, scope).find((item) =>
            Object.keys(item.attributes).every(
                (key) =>
                    String(record[key] || '') === String(item.attributes[key])
            )
        );
    const value = target
        ? target.label
        : record.code ||
          record.process ||
          record.element ||
          record.key ||
          record.search_type ||
          record.label;
    return !value || value === '*'
        ? translate('All targets', language)
        : scope === 'builtin'
          ? translate(value, language)
          : String(value);
}
export function detail(record) {
    return [
        record.pipeline,
        record.search_type,
        record.column,
        record.submenu,
        record.project,
        record.group === 'search_filter'
            ? String(record.op || '=') + ' ' + String(record.value || '')
            : ''
    ]
        .filter(Boolean)
        .join(' · ');
}
export function models(model, ui, language) {
    const editorScope =
        model.attributes.group || model.attributes.category || ui.scope;
    return Object.assign(Access.models(model, ui, language), {
        rules: model.records.filter(
            (record) =>
                (record.group || record.category) === ui.scope &&
                contains(
                    title(record, model, language) +
                        ' ' +
                        detail(record) +
                        ' ' +
                        JSON.stringify(record),
                    ui.query
                )
        ),
        allRules: model.records,
        inheritance: inheritanceChoices(model),
        targets: targets(model, editorScope)
            .map((target, index) =>
                Object.assign(
                    {
                        index
                    },
                    target
                )
            )
            .filter((target) => contains(target.label, ui.targetQuery))
    });
}
const list = (id, bounds, source, rowHeight, keyField) =>
    node('List', id, bounds, {
        source,
        rowHeight,
        keyField,
        fields: [],
        scrollbarId: id + 'ScrollBar'
    });

export function describe(model, ui, width, height, language) {
    const tr = (text) => translate(text, language),
        navigate = !model.busy && !pending(ui),
        notice = notices(
            model,
            ui,
            width,
            language,
            'Discard unsaved access changes?'
        ),
        nodes = notice.nodes,
        rail = width >= 900,
        railWidth = rail ? (language === 'ru' ? 232 : 212) : 0,
        offset = rail ? railWidth + 8 : 0,
        contentWidth = width - offset,
        details = scopeDetails[ui.scope] || scopeDetails.project,
        selected = scopes.find((entry) => entry[0] === ui.scope) || scopes[1];
    const confirmation = nodes.find(
        (item) => item.id === 'adminDocumentConfirmation'
    );
    if (confirmation)
        confirmation.children.forEach((item) => {
            if (item.id === 'adminCancelSave') item.icon = 'close';
            if (item.id === 'adminConfirmSave')
                item.icon = ui.confirmation === 'save' ? 'save' : 'undo';
        });
    let top = notice.top;
    if (rail) {
        const entries = [],
            groups = [
                [
                    'Groups and projects',
                    ['effective', 'defaults', 'project', 'builtin']
                ],
                ['Agent access', ['agent_tool', 'mcp_tool']],
                ['Interface', ['link', 'gear_menu']],
                [
                    'Data and workflow',
                    [
                        'search_type',
                        'process',
                        'tasks',
                        'sobject',
                        'sobject_column',
                        'search_filter'
                    ]
                ],
                ['Advanced', ['technical']]
            ];
        let y = 4;
        groups.forEach(([caption, values]) => {
            entries.push(
                label(
                    'adminSecurityCategory_' + values[0],
                    rect(8, y, railWidth - 32, 20),
                    tr(caption),
                    muted
                )
            );
            y += 22;
            values.forEach((value) => {
                const entry = scopes.find((item) => item[0] === value),
                    current = scopes.findIndex((item) => item[0] === ui.scope),
                    action = (index) => ({
                        type: 'scope',
                        value: scopes[
                            (index + scopes.length) % scopes.length
                        ][0]
                    });
                entries.push(
                    node(
                        'Action',
                        'adminSecurityTab_' + value,
                        rect(4, y, railWidth - 24, 30),
                        {
                            text: tr(entry[1]),
                            description: tr(scopeDetails[value][1]),
                            selected: ui.scope === value,
                            enabled: navigate,
                            normalColor: 'transparent',
                            selectedColor: 'selected',
                            radius: 4,
                            rail: ui.scope === value,
                            keys: {
                                ArrowDown: action(current + 1),
                                ArrowUp: action(current - 1),
                                Home: action(0),
                                End: action(scopes.length - 1)
                            },
                            action: { type: 'scope', value },
                            children: [
                                node(
                                    'Icon',
                                    'adminSecurityTabIcon_' + value,
                                    rect(8, 6, 18, 18),
                                    {
                                        icon: scopeDetails[value][0],
                                        color:
                                            ui.scope === value
                                                ? 'action'
                                                : 'secondaryText'
                                    }
                                ),
                                label(
                                    'adminSecurityTabTitle_' + value,
                                    rect(34, 0, railWidth - 66, 30),
                                    tr(entry[1]),
                                    { fontRole: 'secondary' }
                                )
                            ]
                        }
                    )
                );
                y += 32;
            });
            y += 6;
        });
        nodes.push(
            node(
                'Box',
                'adminSecurityNavigationPanel',
                rect(0, top, railWidth, height - top),
                {
                    background: 'surfaceContainerLow',
                    border: 'outlineVariant',
                    radius: 8,
                    children: [
                        node(
                            'Scroll',
                            'adminSecurityNavigation',
                            rect(0, 0, railWidth, height - top),
                            {
                                children: entries,
                                contentHeight: y,
                                scrollbarId: 'adminSecurityNavigationScrollBar'
                            }
                        )
                    ]
                }
            )
        );
    } else {
        nodes.push(
            node('Choice', 'adminSecurityScope', rect(0, top, width, 38), {
                value: ui.scope,
                label: tr('Access rules'),
                options: scopes.map(([value, text]) => ({
                    value,
                    label: tr(text)
                })),
                enabled: navigate,
                action: { type: 'scope' }
            })
        );
        top += 46;
    }
    const headerHeight = contentWidth < 520 ? 112 : 80;
    nodes.push(
        node(
            'Box',
            'adminSecurityContext',
            rect(offset, top, contentWidth, headerHeight),
            {
                background: 'surfaceContainerLow',
                border: 'outlineVariant',
                radius: 8,
                children: [
                    node(
                        'Icon',
                        'adminSecurityContextIcon',
                        rect(14, 14, 24, 24),
                        { icon: details[0], color: 'action' }
                    ),
                    label(
                        'adminSecurityContextTitle',
                        rect(50, 10, contentWidth - 64, 26),
                        tr(selected[1]),
                        { fontRole: 'section', weight: 600 }
                    ),
                    label(
                        'adminSecurityContextDescription',
                        rect(50, 38, contentWidth - 64, headerHeight - 46),
                        tr(details[1]),
                        Object.assign({ wrap: true }, muted)
                    )
                ]
            }
        )
    );
    const bodyY = top + headerHeight + 12,
        bodyWidth = Math.max(1, contentWidth - 24),
        bodyHeight = Math.max(1, height - bodyY - 24);
    nodes.push(
        node(
            'Box',
            'adminSecurityWorkspacePanel',
            rect(offset, bodyY, contentWidth, height - bodyY),
            {
                background: 'surfaceContainerLow',
                border: 'outlineVariant',
                radius: 8,
                children: [
                    node(
                        'Box',
                        'adminSecurityWorkspace',
                        rect(12, 12, bodyWidth, bodyHeight),
                        {
                            children: workspace(
                                model,
                                ui,
                                bodyWidth,
                                bodyHeight,
                                language
                            ).nodes
                        }
                    )
                ]
            }
        )
    );
    return { nodes };
}

function workspace(model, ui, width, height, language) {
    if (ui.scope === 'effective')
        return Access.workspace(model, ui, width, height, language);
    const tr = (text) => translate(text, language),
        allow = policy(model),
        edit = allow.editable && !pending(ui),
        navigate = !model.busy && !pending(ui),
        matrix = matrixScopes.indexOf(ui.scope) >= 0,
        nodes = [];
    let y = 0;
    if (!matrix) {
        nodes.push(
            node('Icon', 'adminSecurityGroupIcon', rect(0, y + 9, 20, 20), {
                icon: 'groups',
                color: 'secondaryText'
            }),
            label(
                'adminSecurityGroupCaption',
                rect(28, y, 64, 38),
                tr('Group'),
                muted
            ),
            node(
                'Choice',
                'adminSecurityAdvancedGroup',
                rect(98, y, width - 98, 38),
                {
                    label: tr('Group'),
                    options: model.groups.map((group) => ({
                        value: group.identity,
                        label: group.label
                    })),
                    value: model.group,
                    enabled: navigate,
                    action: {
                        type: 'group'
                    }
                }
            )
        );
        y += 46;
    }
    if (!model.ready) {
        nodes.push(
            label(
                'adminSecurityEmpty',
                rect(12, y + 12, width - 24, 70),
                tr(model.busy ? 'Working on the server…' : 'Select a project'),
                {
                    wrap: true,
                    color: 'secondaryText'
                }
            )
        );
        return {
            nodes
        };
    }
    if (ui.scope === 'agent_tool' || ui.scope === 'mcp_tool') {
        const access = Access.workspace(model, ui, width, height - y, language);
        return {
            nodes: nodes.concat(
                access.nodes.map((item) =>
                    Object.assign({}, item, { y: item.y + y })
                )
            )
        };
    }
    if (matrix) {
        const searchWidth = (width - 12) / 2;
        nodes.push(
            node(
                'Field',
                'adminSecurityTargetSearch',
                rect(0, y, searchWidth, 38),
                {
                    text: ui.query,
                    label: tr('Find a permission'),
                    placeholder: tr('Find a permission'),
                    enabled: navigate,
                    action: {
                        type: 'query'
                    }
                }
            ),
            node(
                'Field',
                'adminSecurityGroupSearch',
                rect(searchWidth + 12, y, searchWidth, 38),
                {
                    text: ui.groupQuery,
                    label: tr('Find a group'),
                    placeholder: tr('Find a group'),
                    enabled: navigate,
                    action: {
                        type: 'groupQuery'
                    }
                }
            )
        );
        y += 46;
        const legendHeight = width < 600 ? 60 : 32,
            footer = (width < 560 ? 78 : 40) + legendHeight,
            gridHeight = Math.max(1, height - y - footer - 8);
        nodes.push(
            node('Grid', 'adminSecurityMatrix', rect(0, y, width, gridHeight), {
                source: 'matrix',
                labelWidth: Math.min(260, width * 0.36),
                headerHeight: 38,
                cellWidth: 156,
                rowHeight: 46,
                caption: tr('Permission'),
                rowHeaders: model.matrixRows.map((target) => ({
                    label: target.all ? tr('All') : target.label,
                    detail: detail(target.attributes || {})
                })),
                columnHeaders: model.matrixGroups.map((group) => group.label),
                verticalBarId: 'adminSecurityMatrixVerticalBar',
                horizontalBarId: 'adminSecurityMatrixHorizontalBar',
                rowHeadersId: 'adminSecurityRowHeaders',
                columnHeadersId: 'adminSecurityColumnHeaders'
            })
        );
        const cell = model.selectedCell || {};
        const legendY = y + gridHeight + 4,
            legend = [
                ['Allowed', 'check', 'action'],
                ['Denied', 'close', 'secondaryText'],
                ['Inherited', 'account-tree', 'secondaryText'],
                ['Other rule', 'lock', 'secondaryText']
            ],
            legendColumns = width < 600 ? 2 : 4,
            legendWidth = width / legendColumns;
        legend.forEach(([text, icon, color], index) => {
            const x = (index % legendColumns) * legendWidth,
                ly = legendY + Math.floor(index / legendColumns) * 28;
            nodes.push(
                node(
                    'Icon',
                    'adminSecurityLegendIcon_' + index,
                    rect(x, ly + 5, 16, 16),
                    { icon, color }
                )
            );
            nodes.push(
                label(
                    'adminSecurityLegend_' + index,
                    rect(x + 22, ly, legendWidth - 26, 26),
                    tr(text),
                    muted
                )
            );
        });
        nodes.push(
            button(
                'adminSecurityInherit',
                rect(0, y + gridHeight + legendHeight + 8, 168, 38),
                tr('Use inherited'),
                'undo',
                {
                    type: 'inherit'
                },
                edit && !!ui.selectedCell && !!cell.explicit && !cell.custom
            )
        );
        nodes.push(
            label(
                'adminSecurityMatrixHelp',
                rect(
                    width < 560 ? 0 : 180,
                    y + gridHeight + legendHeight + (width < 560 ? 46 : 8),
                    width < 560 ? width : width - 180,
                    34
                ),
                tr(
                    'Changes apply to the draft. Save to server to publish them.'
                ),
                Object.assign(
                    {
                        wrap: true
                    },
                    muted
                )
            )
        );
    } else if (ui.scope === 'defaults')
        groupSettings(
            nodes,
            model,
            ui,
            rect(0, y, width, height - y),
            language,
            edit
        );
    else if (ui.scope === 'technical')
        technical(
            nodes,
            model,
            ui,
            rect(0, y, width, height - y),
            language,
            edit,
            navigate
        );
    else {
        const split = width >= 780,
            editorWidth = split ? Math.max(320, width * 0.36) : width,
            listWidth = split ? width - editorWidth - 12 : width;
        if (split || !ui.editing) {
            nodes.push(
                node(
                    'Field',
                    'adminAccessSearch',
                    rect(0, y, listWidth - 50, 38),
                    {
                        text: ui.query,
                        label: tr('Find a permission'),
                        placeholder: tr('Find a permission'),
                        enabled: navigate,
                        action: {
                            type: 'query'
                        }
                    }
                ),
                button(
                    'adminAddAccessRule',
                    rect(listWidth - 38, y, 38, 38),
                    tr('Add rule'),
                    'add',
                    {
                        type: 'addRule'
                    },
                    edit,
                    {
                        iconOnly: true
                    }
                ),
                list(
                    'adminAccessRules',
                    rect(0, y + 46, listWidth, height - y - 46),
                    'rules',
                    76,
                    'ruleIndex'
                )
            );
            if (!models(model, ui, language).rules.length)
                nodes.push(
                    label(
                        'adminAccessRulesEmpty',
                        rect(12, y + 58, listWidth - 40, 60),
                        tr('No rules match the search'),
                        {
                            wrap: true,
                            color: 'secondaryText'
                        }
                    )
                );
        }
        if (split || ui.editing)
            editor(
                nodes,
                model,
                ui,
                rect(split ? listWidth + 12 : 0, y, editorWidth, height - y),
                language,
                edit,
                !split
            );
    }
    return {
        nodes
    };
}

function editor(nodes, model, ui, bounds, language, edit, back) {
    const tr = (text) => translate(text, language),
        width = bounds.width,
        inner = Math.max(1, width - 40),
        children = [];
    let y = 12;
    if (back) {
        children.push(
            button(
                'adminAccessBack',
                rect(12, y, 100, 34),
                tr('Back'),
                'chevron-left',
                {
                    type: 'back'
                },
                !model.busy
            )
        );
        y += 42;
    }
    if (
        model.selected < 0 ||
        (ui.scope === 'builtin' &&
            (model.attributes.group || model.attributes.category) !== 'builtin')
    ) {
        children.push(
            label(
                'adminAccessEditorEmpty',
                rect(12, y, inner, 80),
                tr('Select a rule to edit'),
                {
                    wrap: true,
                    color: 'secondaryText'
                }
            )
        );
    } else {
        const attrs = model.attributes,
            scope = attrs.group || attrs.category || ui.scope,
            fields = (names[scope] || []).slice();
        if (Object.prototype.hasOwnProperty.call(attrs, 'project'))
            fields.push('project');
        if (scope === 'builtin') fields.splice(fields.indexOf('key'), 1);
        children.push(
            label(
                'adminAccessEditorTitle',
                rect(12, y, inner, 28),
                title(attrs, model, language),
                {
                    fontRole: 'section',
                    weight: 600
                }
            )
        );
        y += 36;
        if (scope === 'builtin') {
            const feature = builtinFeature(model, attrs.key),
                helpHeight = width < 380 ? 112 : 80,
                options = targets(model, 'builtin').map((target) => ({
                    value: target.attributes.key,
                    label: tr(target.label)
                }));
            if (!options.some((option) => option.value === attrs.key))
                options.push({ value: attrs.key, label: attrs.key });
            children.push(
                node('Choice', 'adminBuiltinFeature', rect(12, y, inner, 38), {
                    value: attrs.key,
                    options,
                    label: tr('Application feature'),
                    enabled: edit,
                    action: { type: 'builtinTarget' }
                }),
                label(
                    'adminBuiltinDescription',
                    rect(12, y + 48, inner, helpHeight),
                    [
                        tr(feature.description),
                        tr(
                            feature.active
                                ? 'Checked by the server.'
                                : feature.known
                                  ? 'Legacy interface rule: this does not control the modern TH/TS screen.'
                                  : 'Custom rule: its effect depends on the plugin or script that checks it.'
                        )
                    ]
                        .filter(Boolean)
                        .join('\n'),
                    Object.assign({ wrap: true }, muted)
                )
            );
            y += 48 + helpHeight + 8;
        }
        if (scope !== 'search_filter') {
            const count = width < 380 ? 1 : width < 620 ? 2 : 3,
                choices =
                    scope === 'builtin'
                        ? [
                              ['deny', 'Deny access'],
                              ['allow', 'Allow access']
                          ]
                        : levels,
                cellWidth =
                    inner / (scope === 'builtin' ? Math.min(count, 2) : count);
            choices.forEach(([value, text], index) =>
                children.push(
                    button(
                        'adminAccessLevel_' + value,
                        rect(
                            12 + (index % count) * cellWidth,
                            y + Math.floor(index / count) * 38,
                            cellWidth - 4,
                            34
                        ),
                        tr(text),
                        levelIcons[value],
                        {
                            type: 'attribute',
                            field: 'access',
                            value
                        },
                        edit,
                        {
                            radio: true,
                            selected: attrs.access === value
                        }
                    )
                )
            );
            y += Math.ceil(choices.length / count) * 38 + 8;
        }
        if (scope === 'builtin') {
            const unusual = !['allow', 'deny'].includes(attrs.access),
                helpHeight = width < 380 ? 96 : 72;
            children.push(
                label(
                    'adminBuiltinInheritanceHelp',
                    rect(12, y, inner, helpHeight),
                    tr(
                        unusual
                            ? 'Existing access: {access}. It is preserved until you choose Allow or Deny. Use Advanced rules for other native access levels.'
                            : "This is the selected group's rule, not the user's final access. Other groups can grant access; administrators bypass these rules. Use Effective permissions to inspect a user."
                    ).replace('{access}', attrs.access || ''),
                    Object.assign({ wrap: true }, muted)
                )
            );
            y += helpHeight + 8;
            children.push(
                label(
                    'adminBuiltinKey',
                    rect(12, y, inner, 24),
                    tr('Rule key: {key}').replace('{key}', attrs.key || ''),
                    muted
                )
            );
            y += 32;
        }
        const fieldLabels = {
            code: scope === 'project' ? 'Project' : 'Search Type',
            process: 'Process',
            pipeline: 'Pipeline',
            element: 'Sidebar link',
            key:
                scope === 'builtin'
                    ? 'Permission'
                    : 'Search Object or operation',
            search_type: 'Search Type',
            column: 'Field',
            submenu: 'Submenu',
            label: 'Menu action',
            op: 'Operator',
            value: 'Value',
            project: 'Rule project'
        };
        fields.forEach((field) => {
            children.push(
                label(
                    'adminAccessLabel_' + field,
                    rect(12, y, inner, 22),
                    tr(fieldLabels[field] || field)
                ),
                node(
                    'Field',
                    'adminAccessField_' + field,
                    rect(12, y + 26, inner, 38),
                    {
                        text: attrs[field] || '',
                        label: tr(fieldLabels[field] || field),
                        enabled: edit,
                        action: {
                            type: 'attribute',
                            field
                        }
                    }
                )
            );
            y += 74;
        });
        children.push(
            button(
                'adminRemoveAccessRule',
                rect(12, y, inner, 38),
                tr(
                    scope === 'builtin' ? 'Use inherited access' : 'Remove rule'
                ),
                scope === 'builtin' ? 'account-tree' : 'delete',
                {
                    type: 'removeRule'
                },
                edit,
                {
                    destructive: scope !== 'builtin'
                }
            )
        );
        y += 50;
        if (scope === 'builtin') {
            children.push(
                label(
                    'adminBuiltinResetHelp',
                    rect(12, y, inner, 84),
                    tr(
                        'Removes only this rule from the group draft. Other groups and native defaults still apply. Save to apply the change.'
                    ),
                    Object.assign({ wrap: true }, muted)
                )
            );
            y += 92;
        } else {
            children.push(
                node(
                    'Field',
                    'adminAccessTargetSearch',
                    rect(12, y, inner, 38),
                    {
                        text: ui.targetQuery,
                        label: tr('Find a target'),
                        placeholder: tr('Find a target'),
                        enabled: !model.busy,
                        action: {
                            type: 'targetQuery'
                        }
                    }
                )
            );
            y += 46;
            children.push(
                list(
                    'adminAccessTargets',
                    rect(12, y, inner, 200),
                    'targets',
                    54,
                    'index'
                )
            );
            y += 212;
        }
    }
    nodes.push(
        node('Box', 'adminAccessRuleEditor', bounds, {
            background: 'surfaceContainerLow',
            border: 'outlineVariant',
            children: [
                node(
                    'Scroll',
                    'adminAccessEditorScroll',
                    rect(0, 0, width, bounds.height),
                    {
                        children,
                        contentHeight: y + 12,
                        resetKey: model.group + ':' + model.selected,
                        scrollbarId: 'adminAccessEditorScrollBar'
                    }
                )
            ]
        })
    );
}

function technical(nodes, model, ui, bounds, language, edit, navigate) {
    const tr = (text) => translate(text, language),
        width = bounds.width,
        y = bounds.y,
        backWidth = ui.page === 'group' ? 0 : 46;
    if (backWidth)
        nodes.push(
            button(
                'adminSecurityBackToRules',
                rect(0, y, 38, 38),
                tr('Group defaults'),
                'chevron-left',
                { type: 'page', value: 'group' },
                navigate,
                { iconOnly: true }
            )
        );
    const options = [
        ['group', 'Group defaults', 'groups'],
        ['xml', 'XML', 'code'],
        ['rule', 'Selected rule JSON', 'code'],
        ['inherited', 'Inherited rules', 'account-tree']
    ].map(([value, text, icon]) => ({
        value,
        icon,
        label: tr(text),
        disabled: value === 'rule' && model.selected < 0
    }));
    nodes.push(
        width < 880
            ? node(
                  'Choice',
                  'adminSecurityTechnicalPages',
                  rect(backWidth, y, width - backWidth, 38),
                  {
                      value: ui.page,
                      options: options.filter((option) => !option.disabled),
                      label: tr('Advanced rules'),
                      enabled: navigate,
                      action: {
                          type: 'page'
                      }
                  }
              )
            : tabs(
                  'adminSecurityTechnicalPages',
                  options,
                  ui.page,
                  rect(backWidth, y, width - backWidth, 38),
                  navigate,
                  'page'
              )
    );
    const top = y + 46,
        remaining = Math.max(1, bounds.height - 46);
    if (ui.page !== 'group') {
        const readonly = ui.page === 'inherited',
            footer = readonly ? 0 : 46;
        nodes.push(
            node(
                'Area',
                'adminSecuritySource',
                rect(0, top, width, remaining - footer),
                {
                    text: ui.text,
                    label: tr(
                        ui.page === 'rule'
                            ? 'Selected rule JSON'
                            : ui.page === 'inherited'
                              ? 'Inherited rules'
                              : 'XML'
                    ),
                    monospace: true,
                    enabled: !model.busy,
                    readOnly: readonly || !policy(model).editable,
                    action: {
                        type: 'text'
                    }
                }
            )
        );
        if (!readonly)
            nodes.push(
                button(
                    'adminSecurityApplyText',
                    rect(
                        0,
                        top + remaining - 38,
                        Math.min(250, width * 0.6),
                        38
                    ),
                    tr('Apply to draft'),
                    'check',
                    {
                        type: 'applyText'
                    },
                    policy(model).editable && pending(ui)
                ),
                button(
                    'adminSecurityDiscardText',
                    rect(
                        Math.min(250, width * 0.6) + 8,
                        top + remaining - 38,
                        Math.min(160, width * 0.4 - 8),
                        38
                    ),
                    tr('Discard text'),
                    'undo',
                    {
                        type: 'discardText'
                    },
                    !model.busy && pending(ui)
                )
            );
        return;
    }
    groupSettings(
        nodes,
        model,
        ui,
        rect(0, top, width, remaining),
        language,
        edit
    );
}

function groupSettings(nodes, model, ui, bounds, language, edit) {
    const tr = (text) => translate(text, language),
        width = bounds.width,
        formWidth = Math.max(1, width - 16),
        columns = width >= 600 ? 2 : 1,
        fieldWidth = (formWidth - (columns - 1) * 12) / columns;
    const fields = [
            ['accessLevel', 'Access level'],
            ['project', 'Project']
        ],
        form = [];
    fields.forEach(([field, text], index) => {
        const x = (index % columns) * (fieldWidth + 12),
            fy = Math.floor(index / columns) * 76;
        form.push(
            label(
                'adminSecurityGroupLabel_' + field,
                rect(x, fy, fieldWidth, 22),
                tr(text)
            )
        );
        form.push(
            node(
                'Choice',
                'adminSecurityGroup_' + field,
                rect(x, fy + 28, fieldWidth, 38),
                {
                    text: model.groupDocument[field] || '',
                    value: model.groupDocument[field] || '',
                    label: tr(text),
                    options:
                        field === 'project'
                            ? [
                                  { value: '', label: tr('All projects') },
                                  ...(model.metadata.targets?.project || [])
                                      .filter((target) => !target.all)
                                      .map((target) => ({
                                          value: target.attributes.code,
                                          label: target.label
                                      }))
                              ]
                            : (model.metadata.accessLevels || []).map(
                                  (value) => ({
                                      value,
                                      label: value
                                  })
                              ),
                    enabled: edit,
                    action: {
                        type: 'groupField',
                        field
                    }
                }
            )
        );
    });
    const formHeight = Math.ceil(fields.length / columns) * 76,
        helpHeight = width >= 900 ? 48 : width >= 600 ? 64 : 112;
    form.push(
        label(
            'adminSecurityInheritanceHelp',
            rect(0, formHeight + 4, formWidth, helpHeight),
            tr(
                'This group inherits permissions from the selected groups. For the same rule key, the highest access wins; a deny does not cancel another grant.'
            ),
            Object.assign({ wrap: true }, muted)
        )
    );
    const known = new Set(model.groups.map((group) => group.label)),
        other = (model.groupDocument.subGroups || '')
            .split('|')
            .filter((name) => name && !known.has(name));
    let contentHeight = formHeight + helpHeight + 12;
    if (other.length) {
        form.push(
            label(
                'adminSecurityOtherInheritance',
                rect(0, contentHeight, formWidth, 48),
                tr('Other inherited groups: {groups}').replace(
                    '{groups}',
                    other.join(', ')
                ),
                { wrap: true }
            )
        );
        contentHeight += 56;
    }
    const headerHeight = Math.min(contentHeight, bounds.height * 0.58);
    nodes.push(
        node(
            'Scroll',
            'adminSecurityDefaults',
            rect(0, bounds.y, width, headerHeight),
            {
                children: form,
                contentHeight,
                scrollbarId: 'adminSecurityDefaultsScrollBar'
            }
        )
    );
    const listY = bounds.y + headerHeight + 8;
    nodes.push(
        label(
            'adminSecurityInheritanceCaption',
            rect(0, listY, width, 24),
            tr(
                ui.scope === 'technical'
                    ? 'Access rules'
                    : 'Inherit permissions from'
            )
        )
    );
    nodes.push(
        list(
            ui.scope === 'technical'
                ? 'adminSecurityAllRules'
                : 'adminSecurityInheritanceList',
            rect(
                0,
                listY + 32,
                width,
                Math.max(1, bounds.y + bounds.height - listY - 32)
            ),
            ui.scope === 'technical' ? 'allRules' : 'inheritance',
            ui.scope === 'technical' ? 62 : 42,
            ui.scope === 'technical' ? 'ruleIndex' : 'identity'
        )
    );
}

export function row(listNode, record, model, ui, language) {
    if (listNode.source === 'effective' || listNode.source === 'agentTools')
        return Access.row(listNode, record, model, ui, language);
    const tr = (text) => translate(text, language),
        width = Math.max(1, listNode.width - 16),
        height = listNode.rowHeight - 4,
        edit = policy(model).editable && !pending(ui),
        navigate = !model.busy && !pending(ui),
        nodes = [];
    if (listNode.source === 'inheritance')
        return {
            nodes: [
                node(
                    'CheckBox',
                    'adminSecurityInheritance_' + record.identity,
                    rect(0, 0, width, height),
                    {
                        text: record.label,
                        description: record.cycle
                            ? tr('This inheritance would create a cycle.')
                            : tr('Inherit permissions from'),
                        checked: record.checked,
                        enabled: edit && (!record.cycle || record.checked),
                        indicatorX: 8,
                        action: {
                            type: 'inheritGroup',
                            identity: record.identity
                        },
                        children: [
                            label(
                                'adminSecurityInheritanceName_' +
                                    record.identity,
                                rect(40, 0, width - 48, height),
                                record.label
                            )
                        ]
                    }
                )
            ]
        };
    if (listNode.source === 'targets')
        return {
            nodes: [
                node(
                    'Action',
                    'adminAccessTarget_' + record.index,
                    rect(0, 0, width, height),
                    {
                        text: record.label,
                        enabled: edit,
                        action: {
                            type: 'target',
                            attributes: record.attributes
                        },
                        children: [
                            label(
                                'adminAccessTargetTitle_' + record.index,
                                rect(12, 4, width - 24, 22),
                                record.label
                            ),
                            label(
                                'adminAccessTargetDetail_' + record.index,
                                rect(12, 26, width - 24, 18),
                                detail(record.attributes),
                                muted
                            )
                        ]
                    }
                )
            ]
        };
    const index = record.ruleIndex,
        all = listNode.source === 'allRules',
        quick = !all && !['search_filter', 'builtin'].includes(ui.scope),
        small = width < 540,
        levelWidth = 36;
    const textWidth =
        quick && !small ? width - levelWidth * 4 - 42 : width - 44;
    nodes.push(
        node('Action', 'adminAccessRule_' + index, rect(0, 0, width, height), {
            text: title(record, model, language),
            selected: model.selected === index,
            rail: true,
            normalColor: 'transparent',
            selectedColor: 'selected',
            enabled: navigate,
            action: {
                type: 'selectRule',
                index
            },
            children: [
                label(
                    'adminAccessRuleTitle_' + index,
                    rect(12, 4, textWidth - 20, 24),
                    title(record, model, language),
                    {
                        weight: 600
                    }
                ),
                label(
                    'adminAccessRuleDetail_' + index,
                    rect(12, 28, textWidth - 20, 20),
                    (all
                        ? (record.group || record.category || '') + ' · '
                        : '') +
                        ((record.group || record.category) === 'builtin'
                            ? tr(
                                  record.access === 'allow'
                                      ? 'Allowed by this group'
                                      : record.access === 'deny'
                                        ? 'Denied by this group'
                                        : 'Existing access: {access}'
                              ).replace('{access}', record.access || '')
                            : detail(record)),
                    muted
                )
            ]
        })
    );
    if (quick)
        ['deny', 'view', 'edit', 'allow'].forEach((value, col) =>
            nodes.push(
                button(
                    'adminPermission_' + index + '_' + value,
                    rect(
                        small
                            ? 8 + col * levelWidth
                            : textWidth + col * levelWidth,
                        small ? 46 : 18,
                        levelWidth - 4,
                        32
                    ),
                    tr(levels.find((level) => level[0] === value)[1]),
                    levelIcons[value],
                    {
                        type: 'ruleAccess',
                        index,
                        value
                    },
                    edit,
                    {
                        radio: true,
                        selected: record.access === value,
                        iconOnly: true,
                        fontRole: 'caption'
                    }
                )
            )
        );
    nodes.push(
        button(
            'adminEditAccessRule_' + index,
            rect(width - 36, 6, 32, 32),
            tr('Edit rule'),
            'edit',
            {
                type: 'selectRule',
                index
            },
            navigate,
            {
                iconOnly: true
            }
        )
    );
    return {
        nodes
    };
}

export function cell(grid, record, row, column, model, ui, language) {
    const tr = (text) => translate(text, language),
        id = 'adminSecurityCell_' + row + '_' + column,
        enabled =
            policy(model).editable &&
            !pending(ui) &&
            !record.locked &&
            !record.custom,
        keys = {};
    [
        ['ArrowLeft', -1, 0],
        ['ArrowRight', 1, 0],
        ['ArrowUp', 0, -1],
        ['ArrowDown', 0, 1]
    ].forEach(([key, dx, dy]) => {
        keys[key] = {
            type: 'navigateCell',
            row,
            column,
            dx,
            dy
        };
    });
    const description = record.custom
        ? tr('Custom access level: {level}. Edit it in Advanced rules.')
              .split('{level}')
              .join(record.access)
        : record.locked
          ? tr(
                'Granted by defaults, subgroups or an All rule. Change the granting rule first.'
            )
          : record.inherited
            ? tr('Inherited. Click to set an explicit permission.')
            : tr('Explicit permission for this group.');
    const background =
        ui.selectedCell &&
        ui.selectedCell.row === row &&
        ui.selectedCell.column === column
            ? 'selected'
            : 'surfaceContainerLow';
    const access = record.custom
            ? levels.find((entry) => entry[0] === record.access)
            : null,
        caption = access
            ? tr(access[1])
            : tr(record.checked ? 'Allowed' : 'Denied');
    const children = [
        node(
            'Box',
            'adminSecurityCellDivider_' + row + '_' + column,
            rect(0, grid.rowHeight - 2, grid.cellWidth - 1, 1),
            { background: 'outlineVariant' }
        ),
        label(
            'adminSecurityAccess_' + row + '_' + column,
            rect(38, 0, grid.cellWidth - 66, grid.rowHeight - 1),
            caption,
            {
                fontRole: 'caption',
                color: record.checked ? 'primaryText' : 'secondaryText'
            }
        )
    ];
    if (record.custom || record.locked || record.inherited)
        children.push(
            node(
                'Icon',
                'adminSecurityOrigin_' + row + '_' + column,
                rect(grid.cellWidth - 24, 14, 16, 16),
                {
                    icon: record.custom
                        ? 'code'
                        : record.locked
                          ? 'lock'
                          : 'account-tree',
                    text: description,
                    color: 'secondaryText'
                }
            )
        );
    return {
        nodes: [
            node(
                'CheckBox',
                id,
                rect(0, 0, grid.cellWidth - 1, grid.rowHeight - 1),
                {
                    text:
                        (model.matrixGroups[column] || {}).label +
                        ' · ' +
                        ((model.matrixRows[row] || {}).all
                            ? tr('All')
                            : (model.matrixRows[row] || {}).label),
                    description,
                    checked: !!record.checked,
                    keys,
                    enabled,
                    indicatorX: 10,
                    radius: 0,
                    normalColor: background,
                    selectedColor: background,
                    action: {
                        type: 'matrix',
                        row,
                        column
                    },
                    children
                }
            )
        ]
    };
}

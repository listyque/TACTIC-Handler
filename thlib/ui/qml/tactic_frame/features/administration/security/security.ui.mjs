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
import { translate } from '../../../core/strings.mjs';
import { matrixScopes, pending } from './security.state.mjs';
export { toolbar };

export const scopes = [
    ['project', 'Projects'],
    ['link', 'Sidebar links'],
    ['gear_menu', 'Menu actions'],
    ['search_type', 'Search Types'],
    ['process', 'Processes'],
    ['tasks', 'Task statuses'],
    ['sobject', 'Search Objects'],
    ['sobject_column', 'Field access'],
    ['builtin', 'Global permissions'],
    ['search_filter', 'Search restrictions'],
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
export function targets(model, scope) {
    return scope === 'builtin'
        ? (model.metadata.builtinPermissions || []).map((item) => ({
              label: item.title,
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
    return {
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
    };
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
        allow = policy(model),
        edit = allow.editable && !pending(ui),
        navigate = !model.busy && !pending(ui);
    const notice = notices(
            model,
            ui,
            width,
            language,
            'Discard unsaved access changes?'
        ),
        nodes = notice.nodes;
    let y = notice.top;
    const matrix = matrixScopes.indexOf(ui.scope) >= 0,
        narrow = width < 600,
        scopeWidth = matrix ? width : narrow ? width : (width - 12) / 2;
    if (width < 700) {
        nodes.push(
            node('Choice', 'adminSecurityScope', rect(0, y, width, 38), {
                value: ui.scope,
                label: tr('Access rules'),
                options: scopes.map(([value, text]) => ({
                    value,
                    label: tr(text)
                })),
                enabled: navigate,
                action: {
                    type: 'scope'
                }
            })
        );
        y += 46;
    } else {
        const columns = Math.max(
                1,
                Math.floor(width / (language === 'ru' ? 190 : 150))
            ),
            cellWidth = width / columns;
        const current = scopes.findIndex((scope) => scope[0] === ui.scope),
            keys = {
                Home: {
                    type: 'scope',
                    value: scopes[0][0]
                },
                End: {
                    type: 'scope',
                    value: scopes[scopes.length - 1][0]
                },
                ArrowLeft: {
                    type: 'scope',
                    value: scopes[
                        (current + scopes.length - 1) % scopes.length
                    ][0]
                },
                ArrowRight: {
                    type: 'scope',
                    value: scopes[(current + 1) % scopes.length][0]
                }
            };
        scopes.forEach(([value, text], index) =>
            nodes.push(
                button(
                    'adminSecurityTab_' + value,
                    rect(
                        (index % columns) * cellWidth,
                        y + Math.floor(index / columns) * 40,
                        cellWidth - 6,
                        34
                    ),
                    tr(text),
                    '',
                    {
                        type: 'scope',
                        value
                    },
                    navigate,
                    {
                        radio: true,
                        selected: ui.scope === value,
                        keys
                    }
                )
            )
        );
        y += Math.ceil(scopes.length / columns) * 40 + 6;
    }
    if (!matrix) {
        nodes.push(
            node(
                'Choice',
                'adminSecurityAdvancedGroup',
                rect(0, y, width, 38),
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
        const footer = width < 560 ? 78 : 40,
            gridHeight = Math.max(1, height - y - footer - 8);
        nodes.push(
            node('Grid', 'adminSecurityMatrix', rect(0, y, width, gridHeight), {
                source: 'matrix',
                labelWidth: Math.min(260, width * 0.36),
                headerHeight: 38,
                cellWidth: 136,
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
        nodes.push(
            button(
                'adminSecurityInherit',
                rect(0, y + gridHeight + 8, 168, 38),
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
                    y + gridHeight + (width < 560 ? 46 : 8),
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
    } else if (ui.scope === 'technical')
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
        const split = width >= 900,
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
    if (model.selected < 0) {
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
        if (scope !== 'search_filter') {
            const count = width < 360 ? 2 : 3,
                cellWidth = inner / count;
            levels.forEach(([value, text], index) =>
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
                        '',
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
            y += Math.ceil(levels.length / count) * 38 + 8;
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
                tr('Remove rule'),
                'delete',
                {
                    type: 'removeRule'
                },
                edit,
                {
                    destructive: true
                }
            )
        );
        y += 50;
        children.push(
            node('Field', 'adminAccessTargetSearch', rect(12, y, inner, 38), {
                text: ui.targetQuery,
                label: tr('Find a target'),
                placeholder: tr('Find a target'),
                enabled: !model.busy,
                action: {
                    type: 'targetQuery'
                }
            })
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
        y = bounds.y;
    const options = [
        ['group', 'Group defaults'],
        ['xml', 'XML'],
        ['rule', 'Selected rule JSON'],
        ['inherited', 'Inherited rules']
    ].map(([value, text]) => ({
        value,
        label: tr(text),
        disabled: value === 'rule' && model.selected < 0
    }));
    nodes.push(
        width < 650
            ? node(
                  'Choice',
                  'adminSecurityTechnicalPages',
                  rect(0, y, width, 38),
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
                  rect(0, y, width, 38),
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
    const formWidth = Math.max(1, width - 16),
        columns = width >= 800 ? 3 : 1,
        fieldWidth = (formWidth - (columns - 1) * 12) / columns;
    const fields = [
            ['accessLevel', 'Access level'],
            ['project', 'Project'],
            ['subGroups', 'Subgroups']
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
                field === 'accessLevel' ? 'Choice' : 'Field',
                'adminSecurityGroup_' + field,
                rect(x, fy + 28, fieldWidth, 38),
                {
                    text: model.groupDocument[field] || '',
                    value: model.groupDocument[field] || '',
                    label: tr(text),
                    options: (model.metadata.accessLevels || []).map(
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
    const formHeight = Math.ceil(fields.length / columns) * 76;
    nodes.push(
        node(
            'Scroll',
            'adminSecurityDefaults',
            rect(0, top, width, Math.min(formHeight, remaining * 0.55)),
            {
                children: form,
                contentHeight: formHeight,
                scrollbarId: 'adminSecurityDefaultsScrollBar'
            }
        )
    );
    const listY = top + Math.min(formHeight, remaining * 0.55) + 8;
    nodes.push(
        list(
            'adminSecurityAllRules',
            rect(0, listY, width, Math.max(1, top + remaining - listY)),
            'allRules',
            62,
            'ruleIndex'
        )
    );
}

export function row(listNode, record, model, ui, language) {
    const tr = (text) => translate(text, language),
        width = Math.max(1, listNode.width - 16),
        height = listNode.rowHeight - 4,
        edit = policy(model).editable && !pending(ui),
        navigate = !model.busy && !pending(ui),
        nodes = [];
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
        quick = !all && ui.scope !== 'search_filter',
        small = width < 540,
        levelWidth = small ? 48 : 64;
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
                        : '') + detail(record),
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
                        small ? 24 : 34
                    ),
                    tr(levels.find((level) => level[0] === value)[1]),
                    '',
                    {
                        type: 'ruleAccess',
                        index,
                        value
                    },
                    edit,
                    {
                        radio: true,
                        selected: record.access === value,
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
    const children = [];
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
                    indicatorX: (grid.cellWidth - 20) / 2,
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

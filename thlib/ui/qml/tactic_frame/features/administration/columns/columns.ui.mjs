import { node } from '../../../core/frame.mjs';
import {
    rect,
    label,
    muted,
    toolbar,
    notices,
    tabs,
    policy
} from '../admin.document.mjs';
import { form } from '../admin.form.mjs';
import { translate } from '../../../core/strings.mjs';
export { toolbar };
const button = (id, bounds, text, icon, action, enabled, extra) =>
    node(
        'Button',
        id,
        bounds,
        Object.assign(
            {
                text,
                icon,
                action,
                enabled
            },
            extra || {}
        )
    );
const list = (id, bounds, source, rowHeight) =>
    node('List', id, bounds, {
        source,
        rowHeight,
        keyField: source === 'definitions' ? 'identity' : 'path',
        fields: [],
        scrollbarId: id + 'ScrollBar'
    });
export function records(model, ui) {
    const query = ui.query.trim().toLowerCase();
    return model.records.filter(
        (row) =>
            (!ui.searchType || row.searchType === ui.searchType) &&
            (!query ||
                [
                    row.view,
                    row.searchType,
                    row.code,
                    row.login,
                    row.category,
                    row.widgetType
                ]
                    .join(' ')
                    .toLowerCase()
                    .indexOf(query) >= 0)
    );
}
export function describe(model, ui, width, height, language) {
    if (width <= 0 || height <= 0)
        return {
            nodes: []
        };
    const tr = (text) => translate(text, language),
        notice = notices(
            model,
            ui,
            width,
            language,
            'Discard unsaved definition changes?'
        ),
        nodes = notice.nodes;
    const y = notice.top,
        minimum = y + 380;
    if (height < minimum)
        return {
            nodes: [
                node('Scroll', 'columnsPageScroll', rect(0, 0, width, height), {
                    contentHeight: minimum,
                    scrollbarId: 'columnsPageScrollBar',
                    children: describe(model, ui, width - 16, minimum, language)
                        .nodes
                })
            ]
        };
    const split = width >= 850,
        left = split ? Math.min(ui.catalogWidth, width * 0.44) : width,
        h = height - y;
    const edit = policy(model).editable && !ui.confirmation,
        navigate =
            !model.busy && !model.dirty && !model.uncertain && !ui.confirmation;
    if (split || !ui.editing) {
        const children = [
            label(
                'definitionCatalogHeading',
                rect(12, 8, left - 70, 28),
                tr('Saved definitions'),
                {
                    fontSize: 15,
                    weight: 600
                }
            ),
            label(
                'definitionCatalogCount',
                rect(left - 58, 8, 46, 28),
                String(records(model, ui).length),
                muted
            ),
            node(
                'Choice',
                'definitionCatalogSearchTypeFilter',
                rect(12, 44, left - 24, 38),
                {
                    label: tr('Filter by Search Type'),
                    value: ui.searchType,
                    options: [
                        {
                            value: '',
                            label: tr('All Search Types')
                        }
                    ].concat(
                        model.typeOptions.map((row) => ({
                            value: row.value,
                            label: row.label
                        }))
                    ),
                    enabled: navigate,
                    action: {
                        type: 'searchType'
                    }
                }
            ),
            node(
                'Field',
                'definitionCatalogFilter',
                rect(12, 90, left - 24, 38),
                {
                    text: ui.query,
                    label: tr('Filter saved views'),
                    placeholder: tr('Filter saved views'),
                    enabled: navigate,
                    action: {
                        type: 'query'
                    }
                }
            ),
            list(
                'definitionCatalogList',
                rect(12, 136, left - 24, h - 148),
                'definitions',
                64
            )
        ];
        if (!records(model, ui).length)
            children.push(
                label(
                    'definitionCatalogEmpty',
                    rect(24, 148, left - 48, 100),
                    tr(
                        model.busy
                            ? 'Working on the server…'
                            : 'No saved definitions match the filter'
                    ),
                    {
                        wrap: true,
                        color: 'secondaryText'
                    }
                )
            );
        nodes.push(
            node('Box', 'definitionCatalogPanel', rect(0, y, left, h), {
                background: 'surfaceContainerLow',
                border: 'outlineVariant',
                children
            })
        );
    }
    if (split)
        nodes.push(
            node(
                'Splitter',
                'columnsCatalogSplitHandle',
                rect(left, y, 10, h),
                {
                    text: tr('Saved definitions panel width'),
                    min: 220,
                    max: width * 0.44,
                    value: left,
                    action: {
                        type: 'split',
                        field: 'catalogWidth'
                    }
                }
            )
        );
    if (split || ui.editing)
        editor(
            nodes,
            model,
            ui,
            rect(
                split ? left + 10 : 0,
                y,
                split ? width - left - 10 : width,
                h
            ),
            language,
            edit,
            !split
        );
    return {
        nodes
    };
}
function editor(nodes, model, ui, bounds, language, edit, back) {
    const tr = (text) => translate(text, language),
        width = bounds.width,
        inner = width - 40,
        children = [];
    let y = 12;
    if (back) {
        children.push(
            button(
                'columnsBack',
                rect(12, y, 100, 36),
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
    if (!model.ready)
        children.push(
            label(
                'columnsSelectHelp',
                rect(12, y, inner, 100),
                tr('Select a definition'),
                {
                    wrap: true,
                    color: 'secondaryText'
                }
            )
        );
    else {
        const selected = model.selected;
        children.push(
            label(
                'definitionViewTitle',
                rect(12, y, inner, 26),
                selected.view,
                {
                    fontSize: 15,
                    weight: 600
                }
            ),
            label(
                'definitionViewType',
                rect(12, y + 30, inner, 24),
                selected.searchType +
                    (selected.login ? ' · ' + selected.login : ''),
                muted
            )
        );
        y += 62;
        children.push(
            tabs(
                'definitionCatalogMode',
                [
                    {
                        value: 'simple',
                        label: tr('Wizard'),
                        icon: 'table'
                    },
                    {
                        value: 'xml',
                        label: 'XML',
                        icon: 'code'
                    }
                ],
                ui.mode,
                rect(12, y, width - 24, 38),
                !model.busy,
                'mode'
            )
        );
        y += 46;
        if (ui.mode === 'xml')
            children.push(
                node(
                    'Area',
                    'definitionCatalogXml',
                    rect(12, y, width - 24, bounds.height - y - 42),
                    {
                        text: model.xml,
                        label: tr('Definition XML'),
                        monospace: true,
                        enabled: edit,
                        action: {
                            type: 'xml'
                        }
                    }
                )
            );
        else if (model.wizard.supported && model.elements.length) {
            children.push(
                label(
                    'definitionColumnsLabel',
                    rect(12, y, (width - 24) / 2, 22),
                    tr('Columns'),
                    muted
                ),
                label(
                    'definitionLayoutLabel',
                    rect(width / 2, y, width / 2 - 12, 22),
                    model.wizard.layout
                        ? tr('Layout: ') + model.wizard.layout
                        : model.wizard.view,
                    muted
                )
            );
            y += 30;
            const stacked = width < 720,
                columnWidth = stacked
                    ? width - 24
                    : Math.min(ui.columnWidth, width * 0.4),
                columnHeight = stacked
                    ? Math.min(ui.columnHeight, (bounds.height - y - 42) * 0.42)
                    : bounds.height - y - 42;
            children.push(
                list(
                    'definitionCatalogElementList',
                    rect(12, y, columnWidth, columnHeight),
                    'columns',
                    60
                )
            );
            children.push(
                node(
                    'Splitter',
                    'definitionColumnsSplitHandle',
                    rect(
                        stacked ? 12 : 12 + columnWidth,
                        stacked ? y + columnHeight : y,
                        stacked ? columnWidth : 10,
                        stacked ? 10 : columnHeight
                    ),
                    {
                        horizontal: stacked,
                        text: tr(
                            stacked
                                ? 'Columns list height'
                                : 'Columns list width'
                        ),
                        value: stacked ? columnHeight : columnWidth,
                        min: stacked ? 100 : 180,
                        max: stacked
                            ? Math.max(100, bounds.height * 0.42)
                            : width * 0.4,
                        action: {
                            type: 'split',
                            field: stacked ? 'columnHeight' : 'columnWidth'
                        }
                    }
                )
            );
            const formX = stacked ? 12 : columnWidth + 22,
                formY = stacked ? y + columnHeight + 10 : y,
                formWidth = width - formX - 28;
            const element = model.element,
                text = (key) =>
                    Object.prototype.hasOwnProperty.call(ui.text, key)
                        ? ui.text[key]
                        : String(element[key] || '');
            const fields = [
                {
                    kind: 'Heading',
                    id: 'definitionColumnHeading',
                    title: 'Column',
                    description:
                        'Edit one native TACTIC element at a time. Custom options remain unchanged in XML.'
                },
                {
                    kind: 'Label',
                    id: 'definitionCatalogName',
                    title: 'Field name',
                    description: 'Native field identifier.',
                    props: {
                        text: element.name || ''
                    }
                },
                {
                    id: 'definitionCatalogTitle',
                    title: 'Title',
                    description: 'The column heading shown to users.',
                    field: 'title',
                    props: {
                        text: text('title'),
                        action: {
                            type: 'text',
                            field: 'title'
                        },
                        commitAction: {
                            type: 'commit'
                        }
                    }
                },
                {
                    kind: 'Switch',
                    id: 'definitionCatalogVisible',
                    title: 'Show in table',
                    description: 'Keep the column in this saved view.',
                    field: 'visible',
                    props: {
                        checked: element.visible
                    }
                },
                {
                    kind: 'Number',
                    min: 48,
                    max: 640,
                    step: 8,
                    value: element.width,
                    id: 'definitionCatalogWidth',
                    title: 'Width',
                    description: 'Default width in the table view.',
                    field: 'width',
                    props: {
                        text: text('width'),
                        inputMode: 'numeric',
                        action: {
                            type: 'text',
                            field: 'width'
                        },
                        commitAction: {
                            type: 'commit'
                        },
                        keys: {
                            ArrowUp: {
                                type: 'step',
                                value: 8
                            },
                            ArrowDown: {
                                type: 'step',
                                value: -8
                            }
                        }
                    }
                },
                {
                    kind: 'Choice',
                    id: 'definitionCatalogWidget',
                    title: 'Display widget',
                    description: 'Choose a supported TACTIC table widget.',
                    field: 'widget',
                    options: model.widgetOptions.map((row) => ({
                        value: row.value,
                        label: tr(row.label)
                    })),
                    props: {
                        value: element.widget || ''
                    }
                }
            ];
            const body = form(fields, formWidth, language, edit);
            children.push(
                node(
                    'Scroll',
                    'definitionCatalogForm',
                    rect(
                        formX,
                        formY,
                        width - formX - 12,
                        Math.max(1, bounds.height - formY - 42)
                    ),
                    {
                        contentHeight: body.height,
                        resetKey: ui.path,
                        scrollbarId: 'definitionCatalogFormScrollBar',
                        children: body.nodes
                    }
                )
            );
        } else {
            children.push(
                label(
                    'definitionCatalogWizardEmpty',
                    rect(12, y, width - 24, 100),
                    tr(
                        model.wizard.error ||
                            (model.wizard.supported
                                ? 'This TACTIC view has no columns. Add elements in XML mode.'
                                : 'This definition does not use a native TACTIC table layout. Open XML to edit its exact structure.')
                    ),
                    {
                        wrap: true,
                        color: 'secondaryText'
                    }
                ),
                button(
                    'definitionOpenXml',
                    rect(12, y + 108, inner, 38),
                    tr('Open XML'),
                    'code',
                    {
                        type: 'mode',
                        value: 'xml'
                    },
                    !model.busy
                )
            );
        }
        children.push(
            label(
                'definitionCode',
                rect(12, bounds.height - 30, inner, 22),
                selected.code || '',
                muted
            )
        );
    }
    nodes.push(
        node('Box', 'definitionEditorPanel', bounds, {
            background: 'surfaceContainerLow',
            border: 'outlineVariant',
            children
        })
    );
}
export function row(listNode, record, model, ui) {
    const width = listNode.width - 16,
        definition = listNode.source === 'definitions',
        selected = definition
            ? model.selected.identity === record.identity
            : model.element.path === record.path;
    return {
        nodes: [
            node(
                'Action',
                definition
                    ? 'definitionRow_' + record.identity
                    : 'definitionColumn_' + record.path,
                rect(0, 0, width, definition ? 60 : 56),
                {
                    text: definition
                        ? record.view +
                          ' · ' +
                          record.searchType +
                          (record.login ? ' · ' + record.login : '')
                        : record.name,
                    selected,
                    normalColor: 'surfaceContainerHigh',
                    selectedColor: 'contentSelection',
                    rail: false,
                    enabled:
                        !model.busy &&
                        !ui.confirmation &&
                        (!definition || (!model.dirty && !model.uncertain)),
                    action: definition
                        ? {
                              type: 'select',
                              identity: record.identity
                          }
                        : {
                              type: 'column',
                              path: record.path
                          },
                    children: [
                        node(
                            'Icon',
                            'definitionRowIcon_' +
                                (record.identity || record.path),
                            rect(10, 18, 18, 18),
                            {
                                icon: definition
                                    ? 'table'
                                    : record.visible
                                      ? 'eye'
                                      : 'eye-off',
                                color: 'action'
                            }
                        ),
                        label(
                            'definitionRowTitle_' +
                                (record.identity || record.path),
                            rect(38, 6, width - 48, 24),
                            definition ? record.view : record.title,
                            {
                                weight: 600
                            }
                        ),
                        label(
                            'definitionRowDetail_' +
                                (record.identity || record.path),
                            rect(38, 30, width - 48, 20),
                            definition
                                ? record.searchType +
                                      (record.login ? ' · ' + record.login : '')
                                : record.name,
                            muted
                        )
                    ]
                }
            )
        ]
    };
}

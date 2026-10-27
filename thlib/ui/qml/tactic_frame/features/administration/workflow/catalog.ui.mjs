import { node, rect, label, muted, button } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { listAction } from '../../../controls/lists/tree.ui.mjs';
export function records(model, ui, language) {
    const tr = (text) => translate(text, language),
        groups = {},
        query = ui.query.trim().toLowerCase();
    for (const row of model.catalog || []) {
        if (
            !query ||
            (row.label + ' ' + row.identity + ' ' + row.searchType)
                .toLowerCase()
                .includes(query)
        )
            (
                groups[row.searchType || ''] ||
                (groups[row.searchType || ''] = [])
            ).push(row);
    }
    groups['sthpw/task'] = groups['sthpw/task'] || [];
    if (model.ready && !model.identity)
        groups[model.document.searchType || ''] =
            groups[model.document.searchType || ''] || [];
    const keys = Object.keys(groups).sort((a, b) =>
            a === 'sthpw/task'
                ? 1
                : b === 'sthpw/task'
                  ? -1
                  : a.localeCompare(b)
        ),
        out = [];
    for (const key of keys) {
        const info =
            (model.metadata.searchTypes || []).find(
                (row) => row.identity === key
            ) || {};
        out.push({
            key: 'group:' + key,
            identity: 'group:' + key,
            group: true,
            searchType: key,
            color: info.color || '',
            label:
                key === 'sthpw/task'
                    ? tr('Task status workflows')
                    : info.label || key || tr('No Search Type')
        });
        if (
            ui.collapsed.indexOf(key) < 0 ||
            (!model.identity && model.document.searchType === key)
        ) {
            if (
                model.ready &&
                !model.identity &&
                model.document.searchType === key
            )
                out.push({
                    key: 'draft:' + key,
                    identity: '',
                    label: tr('New workflow'),
                    searchType: key,
                    typeColor: info.color || ''
                });
            out.push.apply(
                out,
                groups[key]
                    .slice()
                    .sort((a, b) =>
                        (a.label || a.identity).localeCompare(
                            b.label || b.identity
                        )
                    )
                    .map((row) =>
                        Object.assign({}, row, {
                            key: 'pipeline:' + row.identity,
                            typeColor: info.color || ''
                        })
                    )
            );
        }
    }
    return out;
}
export function row(list, record, model, ui, language) {
    const width = list.width - 16,
        tr = (text) => translate(text, language);
    if (list.source === 'graphPipelines') {
        if (record.group)
            return {
                nodes: [
                    ...(record.color
                        ? [
                              node(
                                  'Box',
                                  'workflowGroupColor_' + record.searchType,
                                  rect(0, 7, 3, 20),
                                  { background: record.color, radius: 1 }
                              )
                          ]
                        : []),
                    listAction(
                        'workflowGroup_' + record.searchType,
                        rect(8, 0, width - 8, 34),
                        record.label,
                        ui.collapsed.indexOf(record.searchType) >= 0
                            ? 'chevron-right'
                            : 'chevron-down',
                        {
                            type: 'collapse',
                            identity: record.searchType
                        },
                        !model.busy,
                        {
                            fontRole: 'secondary',
                            color: 'secondaryText',
                            weight: 500,
                            endInset: 32
                        }
                    ),
                    listAction(
                        'workflowCreate_' + record.searchType,
                        rect(width - 34, 2, 30, 30),
                        tr('Create workflow'),
                        'add',
                        {
                            type: 'createWorkflow',
                            searchType: record.searchType
                        },
                        !model.busy &&
                            !model.dirty &&
                            !model.uncertain &&
                            (model.canWrite || model.metadata.canCreate),
                        {
                            iconOnly: true,
                            revealOnRowInteraction: true
                        }
                    )
                ]
            };
        return {
            nodes: [
                node(
                    'Action',
                    'workflowPipeline_' + record.identity,
                    rect(0, 0, width, 38),
                    {
                        text: record.label || record.identity,
                        selected: model.identity === record.identity,
                        normalColor: 'transparent',
                        radius: 6,
                        toolTip:
                            (record.label || record.identity) +
                            ' · ' +
                            record.identity,
                        selectedColor: 'contentSelection',
                        accent: record.color || record.typeColor || undefined,
                        rail: !!(record.color || record.typeColor),
                        enabled: !model.busy && !model.uncertain,
                        children: [
                            label(
                                'workflowPipelineTitle_' + record.identity,
                                rect(14, 0, width - 24, 38),
                                record.label || record.identity
                            )
                        ],
                        action: {
                            type: 'selectPipeline',
                            identity: record.identity
                        }
                    }
                )
            ]
        };
    }
    if (list.source === 'graphTypes')
        return {
            nodes: [
                node(
                    'Action',
                    'graphType_' + record.identity,
                    rect(0, 0, width, 62),
                    {
                        text: record.label || record.identity,
                        selected: ui.typeToAdd === record.identity,
                        normalColor: 'transparent',
                        selectedColor: 'contentSelection',
                        accent: record.color || undefined,
                        rail: !!record.color,
                        enabled: !model.busy,
                        children: [
                            label(
                                'graphTypeTitle_' + record.identity,
                                rect(10, 4, width - 20, 26),
                                record.label || record.identity,
                                {
                                    weight: 600
                                }
                            ),
                            label(
                                'graphTypeIdentity_' + record.identity,
                                rect(10, 32, width - 20, 22),
                                record.identity,
                                muted
                            )
                        ],
                        action: {
                            type: 'typeToAdd',
                            value: record.identity
                        }
                    }
                )
            ]
        };
    if (list.source === 'graphSelection')
        return {
            nodes: [
                node(
                    'CheckBox',
                    'graphSelect_' + record.identity,
                    rect(0, 0, width, 38),
                    {
                        text: record.label || record.identity,
                        checked:
                            model.selectedNodes.indexOf(record.identity) >= 0,
                        enabled: !model.busy,
                        action: {
                            type: 'selectNodes',
                            identities:
                                model.selectedNodes.indexOf(record.identity) >=
                                0
                                    ? model.selectedNodes.filter(
                                          (value) => value !== record.identity
                                      )
                                    : model.selectedNodes.concat([
                                          record.identity
                                      ]),
                            primary: record.identity
                        }
                    }
                )
            ]
        };
    return {
        nodes: []
    };
}
export function models(model, ui, language) {
    const query = ui.typeQuery.trim().toLowerCase();
    return {
        graphPipelines: records(model, ui, language),
        graphTypes: (model.metadata.searchTypes || []).filter((row) =>
            (row.label + ' ' + row.identity).toLowerCase().includes(query)
        ),
        graphSelection: model.nodes || []
    };
}

// The editor owns its library in both the side panel and narrow tab layout.
export function panel(model, ui, bounds, language, narrow = false) {
    const tr = (text) => translate(text, language);
    const w = bounds.width,
        h = bounds.height,
        children = [];
    if (narrow || ui.catalogVisible)
        children.push(
            label(
                'adminWorkflowCatalogTitle',
                rect(12, 12, w - (narrow ? 24 : 74), 38),
                tr('Workflows'),
                {
                    weight: 600
                }
            ),
            node('Field', 'adminWorkflowSearch', rect(12, 58, w - 24, 38), {
                text: ui.query,
                placeholder: tr('Find a workflow'),
                label: tr('Find a workflow'),
                action: {
                    type: 'query'
                }
            }),
            node(
                'List',
                'adminWorkflowCatalog',
                rect(12, 104, w - 24, Math.max(0, h - 116)),
                {
                    source: 'graphPipelines',
                    keyField: 'key',
                    rowHeight: 42,
                    scrollbarId: 'adminWorkflowCatalogScrollBar'
                }
            )
        );
    if (!narrow)
        children.push(
            button(
                'adminToggleWorkflowList',
                rect(ui.catalogVisible ? w - 50 : (w - 38) / 2, 12, 38, 38),
                tr(
                    ui.catalogVisible
                        ? 'Hide workflow list'
                        : 'Show workflow list'
                ),
                ui.catalogVisible ? 'chevron-left' : 'chevron-right',
                {
                    type: 'catalogVisible'
                },
                true,
                {
                    iconOnly: true
                }
            )
        );

    return node('Box', 'adminWorkflowCatalogPanel', bounds, {
        background: 'surfaceContainerLow',
        border: 'outlineVariant',
        children
    });
}

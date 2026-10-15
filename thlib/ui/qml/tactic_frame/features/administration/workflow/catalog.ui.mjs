import { node, rect, label, muted, button } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
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
            identity: 'group:' + key,
            group: true,
            searchType: key,
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
                    identity: '',
                    label: tr('New workflow'),
                    searchType: key
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
                    button(
                        'workflowGroup_' + record.searchType,
                        rect(0, 0, width - 42, 38),
                        record.label,
                        ui.collapsed.indexOf(record.searchType) >= 0
                            ? 'chevron-right'
                            : 'chevron-down',
                        {
                            type: 'collapse',
                            identity: record.searchType
                        },
                        !model.busy
                    ),
                    button(
                        'workflowCreate_' + record.searchType,
                        rect(width - 38, 0, 38, 38),
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
                            iconOnly: true
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
                        normalColor: 'surfaceContainerHigh',
                        selectedColor: 'contentSelection',
                        enabled: !model.busy && !model.uncertain,
                        children: [
                            label(
                                'workflowPipelineTitle_' + record.identity,
                                rect(10, 0, width - 20, 38),
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
                        normalColor: 'surfaceContainerHigh',
                        selectedColor: 'contentSelection',
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

// The same catalog is hosted in the Administration sidebar or the narrow editor.
export function panel(model, ui, bounds, language, narrow = false) {
    const tr = (text) => translate(text, language);
    const w = bounds.width,
        h = bounds.height,
        children = [];
    if (narrow || ui.catalogVisible)
        children.push(
            label(
                'adminWorkflowCatalogTitle',
                rect(8, 4, w - 56, 30),
                tr('Workflows'),
                {
                    weight: 600
                }
            ),
            node('Field', 'adminWorkflowSearch', rect(8, 42, w - 16, 38), {
                text: ui.query,
                placeholder: tr('Find a workflow'),
                label: tr('Find a workflow'),
                action: {
                    type: 'query'
                }
            }),
            node('List', 'adminWorkflowCatalog', rect(8, 88, w - 16, h - 96), {
                source: 'graphPipelines',
                keyField: 'identity',
                rowHeight: 42,
                scrollbarId: 'adminWorkflowCatalogScrollBar'
            })
        );
    if (!narrow)
        children.push(
            button(
                'adminToggleWorkflowList',
                rect(w - 38, 0, 38, 38),
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

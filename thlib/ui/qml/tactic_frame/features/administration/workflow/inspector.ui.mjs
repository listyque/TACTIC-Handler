import { sections } from '../../../controls/forms/sections.ui.mjs';
import { node, rect, label, muted, button } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { policy, sectionSelector } from '../admin.document.mjs';
import { form } from '../admin.form.mjs';
import * as Process from './process.ui.mjs';
const own = (object, key) => Object.prototype.hasOwnProperty.call(object, key);
export function inspector(model, ui, width, language) {
    const tr = (text) => translate(text, language),
        nodes = [],
        editable = policy(model).editable && !ui.confirmation,
        contentWidth = width - 24;
    const selectedNode = (model.nodes || []).find(
            (row) => row.identity === model.selectedNode
        ),
        selectedEdge = (model.edges || [])[model.selectedEdge],
        referenceOnly = !!(selectedNode && selectedNode.referenceOnly);
    let contentY = 0;
    function addForm(fields, enabled, sectioned) {
        const build = sectioned ? sections : form;
        const body = build(
            fields,
            contentWidth,
            language,
            enabled === undefined ? editable : enabled,
            model.style
        );
        nodes.push(
            node(
                'Box',
                'graphInspectorForm_' + contentY,
                rect(0, contentY, contentWidth, body.height),
                {
                    children: body.nodes
                }
            )
        );
        contentY += body.height + 8;
    }
    function action(id, text, icon, event, enabled) {
        nodes.push(
            button(
                id,
                rect(0, contentY, contentWidth, 38),
                tr(text),
                icon,
                event,
                enabled === undefined ? editable : enabled
            )
        );
        contentY += 46;
    }
    function heading(id, text, description) {
        addForm(
            [
                {
                    kind: 'Heading',
                    id,
                    title: text,
                    description
                }
            ],
            false
        );
    }
    function editor(key, title, source, description) {
        heading('graph_' + key + 'Heading', title, description);
        nodes.push(
            node(
                'Area',
                'graph_' + key + 'Editor',
                rect(0, contentY, contentWidth, 220),
                {
                    label: tr(title),
                    text: own(ui.text, key) ? ui.text[key] : source || '',
                    monospace: true,
                    readOnly: !editable || referenceOnly,
                    action: {
                        type: 'buffer',
                        key
                    }
                }
            )
        );
        contentY += 228;
        action(
            'graphApply_' + key,
            'Apply',
            'check',
            {
                type: 'apply',
                key
            },
            editable && !referenceOnly && own(ui.text, key)
        );
    }
    function addPositionFields() {
        addForm([
            {
                id: 'adminGraphPositionX',
                title: 'Horizontal position',
                description: 'Move this node without dragging.',
                props: {
                    text: own(ui.text, 'positionX')
                        ? ui.text.positionX
                        : String(selectedNode.nodeX),
                    inputMode: 'decimal',
                    action: {
                        type: 'buffer',
                        key: 'positionX'
                    },
                    commitAction: {
                        type: 'position',
                        key: 'positionX'
                    }
                }
            },
            {
                id: 'adminGraphPositionY',
                title: 'Vertical position',
                description: 'Move this node without dragging.',
                props: {
                    text: own(ui.text, 'positionY')
                        ? ui.text.positionY
                        : String(selectedNode.nodeY),
                    inputMode: 'decimal',
                    action: {
                        type: 'buffer',
                        key: 'positionY'
                    },
                    commitAction: {
                        type: 'position',
                        key: 'positionY'
                    }
                }
            }
        ]);
    }
    if (model.mode !== 'workflow') {
        nodes.push(
            sectionSelector(
                'adminGraphInspectorPages',
                [
                    {
                        value: 'selection',
                        label: tr('Selection'),
                        icon: 'tune'
                    },
                    {
                        value: 'add_node',
                        label: tr('Add node'),
                        icon: 'add'
                    }
                ],
                ui.inspector,
                rect(0, contentY, contentWidth, 38),
                !model.busy,
                'inspector'
            )
        );
        contentY += 46;
    }
    if (ui.inspector === 'add_node') {
        if (model.mode === 'workflow') {
            addForm([
                {
                    id: 'adminNodeName',
                    title: 'Node name',
                    description: 'Enter a unique node name',
                    props: {
                        text: ui.nodeName,
                        action: {
                            type: 'nodeName'
                        }
                    }
                },
                {
                    kind: 'Choice',
                    id: 'adminNodeKind',
                    title: 'Node type',
                    options: (model.metadata.nodeTypes || []).map((value) => ({
                        value,
                        label: value
                    })),
                    props: {
                        value:
                            model.document.searchType === 'sthpw/task'
                                ? 'status'
                                : ui.nodeKind,
                        enabled:
                            editable &&
                            model.document.searchType !== 'sthpw/task',
                        action: {
                            type: 'nodeKind'
                        }
                    }
                }
            ]);
        } else {
            action('adminCreateSchemaTypeInspector', 'New Search Type', 'add', {
                type: 'createType'
            });
            addForm(
                [
                    {
                        id: 'adminGraphTypeFilter',
                        title: 'Find a Search Type',
                        props: {
                            text: ui.typeQuery,
                            action: {
                                type: 'typeQuery'
                            }
                        }
                    }
                ],
                !model.busy
            );
            nodes.push(
                node(
                    'List',
                    'adminGraphTypeCatalog',
                    rect(0, contentY, contentWidth, 220),
                    {
                        source: 'graphTypes',
                        keyField: 'identity',
                        rowHeight: 66,
                        scrollbarId: 'adminGraphTypeCatalogScrollBar'
                    }
                )
            );
            contentY += 228;
        }
        action(
            'adminAddNode',
            'Add node',
            'add',
            {
                type: 'addNode'
            },
            editable &&
                !!(model.mode === 'workflow'
                    ? ui.nodeName.trim()
                    : ui.typeToAdd)
        );
        const options = (model.nodes || [])
            .filter((row) => !row.referenceOnly)
            .map((row) => ({
                value: row.identity,
                label: row.label || row.identity
            }));
        addForm([
            {
                kind: 'Choice',
                id: 'adminConnectSource',
                title: 'Source',
                options,
                props: {
                    value: ui.source,
                    action: {
                        type: 'source'
                    }
                }
            },
            {
                kind: 'Choice',
                id: 'adminConnectTarget',
                title: 'Destination',
                options,
                props: {
                    value: ui.target,
                    action: {
                        type: 'target'
                    }
                }
            }
        ]);
        action(
            'adminConnectNodes',
            'Connect',
            'link',
            {
                type: 'connect'
            },
            editable && !!ui.source && !!ui.target && ui.source !== ui.target
        );
    } else if (selectedNode || selectedEdge) {
        if (model.mode !== 'workflow' || !selectedNode || referenceOnly) {
            heading(
                'graphSelectionHeading',
                selectedNode
                    ? selectedNode.identity
                    : selectedEdge.from + ' → ' + selectedEdge.to,
                referenceOnly
                    ? model.mode === 'workflow'
                        ? 'This process is referenced by a connection. Add the missing process or remove its connections before saving.'
                        : 'This type is referenced by a connection. Add its registered node to the canvas to move it.'
                    : ''
            );
        }
        if ((model.selectedNodes || []).length > 1) {
            nodes.push(
                node(
                    'List',
                    'adminGraphMultiSelection',
                    rect(0, contentY, contentWidth, 152),
                    {
                        source: 'graphSelection',
                        keyField: 'identity',
                        rowHeight: 40
                    }
                )
            );
            contentY += 160;
        }
        if (model.mode !== 'workflow') {
            action(
                'adminRemoveGraphSelection',
                'Remove from canvas',
                'close',
                {
                    type: 'remove'
                },
                (editable && !referenceOnly) || (editable && !!selectedEdge)
            );
        }
        if (selectedNode && !referenceOnly) {
            if (model.mode === 'schema') addPositionFields();
            if (model.mode === 'schema') {
                action(
                    'adminNodeWorkflows',
                    'Workflows',
                    'schema',
                    {
                        type: 'nodeWorkflows'
                    },
                    !model.busy
                );
                if (
                    !model.instance &&
                    ['sthpw', 'config'].indexOf(
                        selectedNode.identity.split('/')[0]
                    ) < 0
                )
                    action(
                        'adminDeleteSearchType',
                        'Delete from project',
                        'close',
                        {
                            type: 'deleteType'
                        },
                        editable
                    );
            }
        }
        if (model.mode === 'workflow' && selectedEdge) {
            const choices = (model.nodes || [])
                .filter((row) => !row.referenceOnly)
                .map((row) => ({
                    value: row.identity,
                    label: row.label || row.identity
                }));
            addForm(
                ['from', 'to', 'from_attr', 'to_attr'].map((key) => ({
                    id: 'adminWorkflowEdge_' + key,
                    title: {
                        from: 'Source',
                        to: 'Destination',
                        from_attr: 'Output condition',
                        to_attr: 'Input name'
                    }[key],
                    description: 'Native connection attributes.',
                    kind: key === 'from' || key === 'to' ? 'Choice' : 'Field',
                    options: choices,
                    props: Object.assign(
                        {
                            action: {
                                type: 'attribute',
                                key
                            }
                        },
                        key === 'from' || key === 'to'
                            ? {
                                  value: selectedEdge[key] || ''
                              }
                            : {
                                  text: selectedEdge[key] || ''
                              }
                    )
                }))
            );
            editor('attributes', 'Attributes (JSON)', model.attributes);
        } else if (
            model.mode === 'workflow' &&
            selectedNode &&
            !referenceOnly
        ) {
            nodes.push(
                sectionSelector(
                    'adminProcessPages',
                    [
                        {
                            value: 'parameters',
                            label: tr('Parameters'),
                            icon: 'tune'
                        },
                        {
                            value: 'native_json',
                            label: tr('Advanced JSON'),
                            icon: 'code'
                        }
                    ],
                    ui.processPage,
                    rect(0, contentY, contentWidth, 38),
                    !model.busy,
                    'processPage'
                )
            );
            contentY += 46;
            if (ui.processPage === 'parameters') {
                addForm(Process.fields(model, ui, language), undefined, true);
                const defaults = (model.processSettings || {}).default || {};
                if (
                    ['action', 'condition'].indexOf(model.processKind) >= 0 &&
                    defaults.action !== 'command'
                )
                    editor(
                        'script',
                        'Script body',
                        defaults.script,
                        'The code is stored with this process. Applying the draft does not run it.'
                    );
            } else {
                addPositionFields();
                editor(
                    'settings',
                    'Native process settings',
                    model.settings,
                    'Advanced access to native data, including parameters of installed custom nodes. Standard settings are available in Parameters.'
                );
                editor('attributes', 'Attributes (JSON)', model.attributes);
            }
        } else {
            if (model.mode === 'schema' && (model.instance || selectedEdge)) {
                const connection = model.connection || {};
                if (model.instance) {
                    heading(
                        'schemaInstanceHeading',
                        'Many-to-many · new Search Type',
                        'This is a draft. The instance table and its key columns will be created only when you save the schema.'
                    );
                    addForm([
                        {
                            id: 'adminSchemaInstanceName',
                            title: 'Instance table name',
                            props: {
                                text: own(ui.text, 'instance')
                                    ? ui.text.instance
                                    : model.instance.split('/').pop(),
                                action: {
                                    type: 'buffer',
                                    key: 'instance'
                                },
                                commitAction: {
                                    type: 'commitInstance'
                                }
                            }
                        }
                    ]);
                    if (!selectedEdge)
                        for (const link of model.instanceLinks || [])
                            action(
                                'schemaInstanceLink_' + link.edgeIndex,
                                link.to,
                                'link',
                                {
                                    type: 'selectEdge',
                                    index: link.edgeIndex
                                },
                                !model.busy
                            );
                    action(
                        'adminSchemaRestoreDirect',
                        'Restore direct connection',
                        'undo',
                        {
                            type: 'restoreDirect'
                        }
                    );
                }
                if (selectedEdge) {
                    if (!model.instance)
                        addForm([
                            {
                                kind: 'Choice',
                                id: 'adminSchemaRelationship',
                                title: 'Relationship type',
                                description:
                                    'Many-to-many creates a separate instance Search Type with two key connections.',
                                options: [
                                    {
                                        value: 'code',
                                        label: 'code'
                                    },
                                    {
                                        value: 'id',
                                        label: 'id'
                                    }
                                ].concat(
                                    [
                                        selectedEdge.from,
                                        selectedEdge.to
                                    ].indexOf('*') < 0
                                        ? [
                                              {
                                                  value: 'many_to_many',
                                                  label: 'many_to_many'
                                              }
                                          ]
                                        : []
                                ),
                                props: {
                                    value: selectedEdge.relationship || 'code',
                                    action: {
                                        type: 'relationship'
                                    }
                                }
                            }
                        ]);
                    addForm([
                        {
                            kind: 'Switch',
                            id: 'adminSchemaCreateColumns',
                            title: 'Create missing columns',
                            description:
                                "Choose existing columns below, or enter a new key column name. New columns are created on schema save, using the opposite key's type.",
                            props: {
                                checked: !!model.createColumns,
                                action: {
                                    type: 'createColumns'
                                }
                            }
                        }
                    ]);
                    action(
                        'adminSchemaReverse',
                        'Reverse connection',
                        'refresh',
                        {
                            type: 'reverse'
                        },
                        editable && !model.instance
                    );
                    action(
                        'adminSchemaRefreshColumns',
                        'Reload columns from server',
                        'refresh',
                        {
                            type: 'refreshColumns'
                        },
                        !model.busy && !model.columnsBusy
                    );
                    if (model.columnsError || model.columnsBusy) {
                        nodes.push(
                            node(
                                'Area',
                                'adminSchemaColumnsStatus',
                                rect(0, contentY, contentWidth, 64),
                                {
                                    label: tr('Columns'),
                                    text: tr(
                                        model.columnsError || 'Loading data…'
                                    ),
                                    readOnly: true,
                                    notice: true,
                                    color: model.columnsError
                                        ? 'error'
                                        : 'secondaryText'
                                }
                            )
                        );
                        contentY += 72;
                    }
                    for (const side of [
                        {
                            key: 'from_col',
                            name: connection.from,
                            title: 'Source key column'
                        },
                        {
                            key: 'to_col',
                            name: connection.to,
                            title: 'Destination key column'
                        }
                    ]) {
                        const info =
                                (model.columnCatalog || {})[side.name] || {},
                            columns = info.columns || [],
                            options = columns.map((row) => ({
                                value: row.name,
                                label:
                                    row.name +
                                    ' · ' +
                                    (row.type || '') +
                                    (row.pending ? ' · ' + tr('Pending') : '')
                            }));
                        addForm([
                            {
                                id: 'adminSchema_' + side.key,
                                title: side.title,
                                description: side.name,
                                props: {
                                    text: connection[side.key] || '',
                                    action: {
                                        type: 'column',
                                        key: side.key
                                    }
                                }
                            },
                            {
                                kind: 'Choice',
                                id: 'adminSchemaChoose_' + side.key,
                                title: 'Existing columns',
                                options: [
                                    {
                                        value: '',
                                        label: tr('Choose a column')
                                    }
                                ].concat(options),
                                props: {
                                    value: connection[side.key] || '',
                                    action: {
                                        type: 'column',
                                        key: side.key
                                    }
                                }
                            }
                        ]);
                        if (info.tableAvailable === false)
                            heading(
                                'schemaAbsent_' + side.key,
                                'Database table unavailable',
                                'The database table is absent. No table is created by reading columns.'
                            );
                    }
                    addForm([
                        {
                            id: 'adminSchemaPath',
                            title: 'Relationship path',
                            description:
                                'Optional native path used to distinguish multiple relationships.',
                            props: {
                                text: selectedEdge.path || '',
                                action: {
                                    type: 'attribute',
                                    key: 'path'
                                }
                            }
                        }
                    ]);
                }
            }
            if (!referenceOnly)
                editor('attributes', 'Attributes (JSON)', model.attributes);
        }
    } else if (model.mode === 'workflow' && model.ready) {
        addForm(
            [
                {
                    kind: 'Heading',
                    id: 'pipelineSettingsHeading',
                    title: 'Pipeline settings',
                    description:
                        'These settings belong to the whole pipeline. Select a node on the canvas to configure that process and its task statuses.'
                },
                {
                    id: 'adminPipelineName',
                    title: 'Title',
                    description: 'The pipeline name shown to other users.',
                    field: 'name',
                    props: {
                        text: model.document.name || ''
                    }
                },
                {
                    id: 'adminPipelineDescription',
                    title: 'Description',
                    field: 'description',
                    description: 'Explain what this pipeline is used for.',
                    props: {
                        text: model.document.description || ''
                    }
                },
                {
                    id: 'adminPipelineColor',
                    title: 'Color',
                    field: 'color',
                    description:
                        'The color of the entire pipeline, independent of its process colors.',
                    kind: 'ColorChoice',
                    props: {
                        value: model.document.color || ''
                    }
                }
            ],
            undefined,
            true
        );
    } else
        heading(
            'graphSelectHelp',
            'Select a node or a connection',
            'Its details appear here. Use Add node to extend the canvas.'
        );
    return {
        nodes,
        height: contentY + 12
    };
}

import { node, rect, label, muted, button } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import {
    notices,
    toolbar as documentToolbar,
    policy,
    sectionSelector
} from '../admin.document.mjs';
import { inspector } from './inspector.ui.mjs';
export { inspector };
import { panel as catalogPanel } from './catalog.ui.mjs';
export { records, row, models } from './catalog.ui.mjs';
const own = (object, key) => Object.prototype.hasOwnProperty.call(object, key);
export function toolbar(model, ui, width, language) {
    const result = documentToolbar(model, ui, width, language),
        tr = (text) => translate(text, language);
    result.nodes = result.nodes.filter(
        (row) => row.id !== 'adminDocumentStatus'
    );
    result.nodes.push(
        button(
            model.mode === 'workflow'
                ? 'adminCreateDocument'
                : 'adminCreateSchemaType',
            rect(46, 0, 38, 38),
            tr(
                model.mode === 'workflow'
                    ? 'Create workflow'
                    : 'New Search Type'
            ),
            'add',
            {
                type:
                    model.mode === 'workflow' ? 'createWorkflow' : 'createType',
                searchType:
                    model.document.searchType || model.creationSearchType
            },
            !model.busy &&
                !model.uncertain &&
                (model.canWrite || model.metadata.canCreate) &&
                (!model.dirty || model.mode !== 'workflow') &&
                (model.mode !== 'workflow' ||
                    !!(model.document.searchType || model.creationSearchType)),
            {
                iconOnly: true
            }
        )
    );
    return result;
}
export function describe(model, ui, width, height, language) {
    if (width <= 0 || height <= 0)
        return {
            nodes: []
        };
    const tr = (text) => translate(text, language),
        workflow = model.mode === 'workflow',
        internalCatalog = workflow,
        narrow = width < (workflow ? 1000 : 800),
        edit = policy(model).editable && !ui.confirmation;
    const noticeModel = Object.assign({}, model, {
        error: model.error || ui.error
    });
    if (ui.confirmation === 'remove')
        noticeModel.confirmationText = workflow
            ? 'Remove the selection from this workflow draft?'
            : 'Remove the selection from the schema draft? Search Types, tables and data will be kept.';
    if (ui.confirmation === 'selection')
        noticeModel.confirmationText = 'Discard unapplied JSON changes?';
    const notice = notices(
            noticeModel,
            ui,
            width,
            language,
            undefined,
            ui.confirmation === 'remove' ? 'Remove from canvas' : undefined
        ),
        nodes = notice.nodes;
    let y = notice.top;
    nodes.push(
        sectionSelector(
            'adminGraphPages',
            [
                {
                    value: 'canvas',
                    label: tr('Canvas'),
                    icon: 'schema'
                },
                {
                    value: 'technical',
                    label: tr('Technical'),
                    icon: 'code'
                }
            ],
            ui.page,
            rect(0, y, Math.min(width, 320), 38),
            !model.busy,
            'page'
        )
    );
    if (workflow && ui.page === 'canvas') {
        const settingsY = width >= 560 ? y : y + 46;
        nodes.push(
            button(
                'adminEditPipeline',
                rect(
                    width >= 560 ? 328 : 0,
                    settingsY,
                    Math.min(200, width),
                    38
                ),
                tr('Pipeline settings'),
                'tune',
                { type: 'clear' },
                !model.busy
            )
        );
        if (width < 560) y += 46;
    }
    y += 46;
    if (workflow) {
        const searchType =
            model.document.searchType || model.creationSearchType || '';
        const details = (model.metadata.searchTypes || []).find(
            (record) => record.identity === searchType
        );
        const context =
            details && details.label && details.label !== searchType
                ? details.label + ' · ' + searchType
                : searchType;
        const text = searchType
            ? tr('Search Type: %1').replace('%1', context)
            : tr(
                  'No Search Type is linked. Create a workflow from the Search Type editor.'
              );
        const captionHeight = Math.max(
            18,
            Math.ceil((text.length * 6) / Math.max(1, width)) * 15
        );
        const color = details?.color || '';
        if (color)
            nodes.push(
                node(
                    'Box',
                    'adminWorkflowSearchTypeColor',
                    rect(0, y, 3, captionHeight),
                    { background: color, radius: 1 }
                )
            );
        nodes.push(
            label(
                'adminWorkflowSearchType',
                rect(
                    color ? 12 : 0,
                    y,
                    width - (color ? 12 : 0),
                    captionHeight
                ),
                text,
                Object.assign({}, muted, { wrap: true })
            )
        );
        y += captionHeight + 12;
    }
    if (!model.ready) {
        nodes.push(
            label(
                'adminGraphEmpty',
                rect(12, y, width - 24, 80),
                tr('Select a workflow or create a new one.'),
                {
                    wrap: true
                }
            )
        );
    }
    const info = model.metadata.shared
        ? 'Shared pipeline: read-only. Create a project-owned pipeline to make project-specific changes.'
        : !workflow && model.identity && !model.canWrite
          ? 'Built-in system schema · read-only'
          : '';
    if (info) {
        nodes.push(
            label(
                'adminGraphReadOnly',
                rect(0, y, width, 64),
                tr(info),
                Object.assign(
                    {
                        wrap: true
                    },
                    muted
                )
            )
        );
        y += 72;
    }
    const missing = workflow
        ? (model.nodes || [])
              .filter((row) => row.referenceOnly)
              .map((row) => row.identity)
        : [];
    if (missing.length) {
        nodes.push(
            node('Area', 'adminMissingProcesses', rect(0, y, width, 68), {
                label: tr('Missing processes'),
                text:
                    tr('Connections refer to missing processes') +
                    ': ' +
                    missing.join(', '),
                notice: true,
                readOnly: true,
                color: 'error'
            })
        );
        y += 76;
    }
    if (narrow) {
        nodes.push(
            sectionSelector(
                'adminGraphPanels',
                [].concat(
                    internalCatalog
                        ? [
                              {
                                  value: 'catalog',
                                  label: tr('Workflows'),
                                  icon: 'list'
                              }
                          ]
                        : [],
                    [
                        {
                            value: 'canvas',
                            label: tr('Canvas'),
                            icon: 'schema'
                        },
                        {
                            value: 'properties',
                            label: tr('Properties'),
                            icon: 'tune'
                        }
                    ]
                ),
                ui.panel,
                rect(0, y, width, 38),
                !model.busy,
                'panel'
            )
        );
        y += 46;
    }
    const h = Math.max(1, height - y),
        catalogWidth =
            internalCatalog && !narrow
                ? ui.catalogVisible
                    ? Math.min(ui.catalogWidth, width * 0.28)
                    : 56
                : 0,
        propertiesWidth = !narrow
            ? ui.propertiesVisible
                ? Math.min(
                      ui.propertiesWidth,
                      workflow ? 460 : 420,
                      width * (workflow ? 0.5 : 0.45)
                  )
                : 56
            : 0;
    if (internalCatalog && (!narrow || ui.panel === 'catalog')) {
        const w = narrow ? width : catalogWidth;
        nodes.push(
            Object.assign(
                catalogPanel(model, ui, rect(0, y, w, h), language, narrow),
                {
                    visible: ui.page === 'canvas' || !narrow
                }
            )
        );
        if (!narrow && ui.catalogVisible)
            nodes.push(
                node('Splitter', 'adminCatalogSplit', rect(w, y, 10, h), {
                    visible: ui.page === 'canvas' || !narrow,
                    text: tr('Workflow list width'),
                    value: w,
                    min: 180,
                    max: Math.min(420, width * 0.28),
                    action: {
                        type: 'catalogSplit'
                    }
                })
            );
    }
    const x = narrow ? 0 : internalCatalog ? catalogWidth + 10 : 0,
        graphWidth = narrow
            ? width
            : Math.max(1, width - x - propertiesWidth - 10);
    const graphNodes = (model.nodes || []).map((row) => ({
        identity: row.identity,
        label: row.label || row.identity,
        nodeX: row.nodeX,
        nodeY: row.nodeY,
        color: row.color || '',
        kind: workflow && row.kind === 'process' ? 'manual' : row.kind,
        referenceOnly: !!row.referenceOnly,
        pendingCreation:
            !!model.document.newTypes &&
            own(model.document.newTypes, row.identity)
    }));
    const graphEdges = (model.edges || []).map((row, index) => ({
        from: row.from,
        to: row.to,
        edgeIndex: index,
        relationship: row.relationship || '',
        from_attr: row.from_attr || '',
        to_attr: row.to_attr || '',
        label: workflow ? row.from_attr || '' : row.relationship || 'code',
        color: row.color || ''
    }));
    nodes.push(
        node('Graph', 'adminGraphCanvas', rect(x, y, graphWidth, h), {
            toolbarRightInset: 46,
            visible: ui.page === 'canvas' && (!narrow || ui.panel === 'canvas'),
            help: false,
            label: tr(workflow ? 'Workflow' : 'Project schema'),
            nodes: graphNodes,
            edges: graphEdges,
            selectedNode: model.selectedNode || '',
            selectedNodes: model.selectedNodes || [],
            selectedEdge: model.selectedEdge,
            readOnly: !edit,
            selectionEnabled: !model.busy,
            resetKey: model.identity || 'draft:' + model.document.searchType,
            language,
            action: {
                type: 'graph'
            }
        })
    );
    if (!narrow || ui.panel === 'properties') {
        const w = narrow ? width : propertiesWidth,
            px = narrow ? 0 : width - w,
            children = [];
        if (narrow || ui.propertiesVisible) {
            const inner = inspector(model, ui, w - 24, language);
            children.push(
                node(
                    'Scroll',
                    'adminGraphPropertiesScroll',
                    rect(12, 62, w - 24, Math.max(0, h - 74)),
                    {
                        contentHeight: inner.height,
                        resetKey:
                            ui.inspector +
                            ':' +
                            ui.processPage +
                            ':' +
                            model.selectedNode +
                            ':' +
                            model.selectedEdge,
                        scrollbarId: 'adminGraphPropertiesScrollBar',
                        children: inner.nodes
                    }
                )
            );
        }
        if (!narrow)
            children.push(
                button(
                    'adminToggleGraphProperties',
                    rect(
                        ui.propertiesVisible
                            ? workflow
                                ? w - 50
                                : 12
                            : (w - 38) / 2,
                        12,
                        38,
                        38
                    ),
                    tr(
                        ui.propertiesVisible
                            ? 'Hide properties'
                            : 'Show properties'
                    ),
                    ui.propertiesVisible ? 'chevron-right' : 'chevron-left',
                    {
                        type: 'propertiesVisible'
                    },
                    true,
                    {
                        iconOnly: true
                    }
                )
            );
        if (narrow || ui.propertiesVisible)
            children.push(
                button(
                    'adminGraphAddNode',
                    rect(
                        workflow ? w - (narrow ? 50 : 94) : narrow ? 12 : 58,
                        12,
                        workflow ? 38 : w - (narrow ? 24 : 70),
                        38
                    ),
                    tr(ui.inspector === 'add_node' ? 'Selection' : 'Add node'),
                    ui.inspector === 'add_node' ? 'tune' : 'add',
                    {
                        type: 'inspector',
                        value:
                            ui.inspector === 'add_node'
                                ? 'selection'
                                : 'add_node'
                    },
                    !model.busy,
                    { iconOnly: workflow }
                )
            );
        if (workflow && (narrow || ui.propertiesVisible)) {
            children.push(
                label(
                    'adminGraphInspectorTitle',
                    rect(12, 12, Math.max(0, w - (narrow ? 112 : 156)), 38),
                    tr('Inspector'),
                    { weight: 600 }
                )
            );
            if (model.selectedNode || model.selectedEdge >= 0) {
                const selectedNode = (model.nodes || []).find(
                    (record) => record.identity === model.selectedNode
                );
                children.push(
                    button(
                        'adminRemoveGraphSelection',
                        rect(w - (narrow ? 94 : 138), 12, 38, 38),
                        tr('Remove from canvas'),
                        'delete',
                        { type: 'remove' },
                        edit && !(selectedNode && selectedNode.referenceOnly),
                        { iconOnly: true, destructive: true }
                    )
                );
            }
        }
        nodes.push(
            node('Box', 'adminGraphProperties', rect(px, y, w, h), {
                visible: ui.page === 'canvas',
                background: 'surfaceContainerLow',
                border: 'outlineVariant',
                children
            })
        );
        if (!narrow && ui.propertiesVisible)
            nodes.push(
                node(
                    'Splitter',
                    'adminGraphSplitHandle',
                    rect(px - 10, y, 10, h),
                    {
                        visible: ui.page === 'canvas',
                        text: tr('Properties panel width'),
                        value: w,
                        min: 240,
                        max: Math.min(640, width * 0.4),
                        reverse: true,
                        action: {
                            type: 'propertiesSplit'
                        }
                    }
                )
            );
    }
    if (ui.page === 'technical')
        nodes.push(
            node(
                'Area',
                'adminGraphXmlEditor',
                rect(
                    narrow ? 0 : x,
                    y,
                    width - (narrow ? 0 : x),
                    Math.max(1, h - 46)
                ),
                {
                    label: tr('Native XML'),
                    text: own(ui.text, 'xml') ? ui.text.xml : model.xml || '',
                    monospace: true,
                    readOnly: !edit,
                    action: {
                        type: 'buffer',
                        key: 'xml'
                    }
                }
            ),
            button(
                'adminGraphApplyXml',
                rect(
                    narrow ? 0 : x,
                    height - 38,
                    Math.min(240, width - (narrow ? 0 : x)),
                    38
                ),
                tr('Apply XML'),
                'check',
                {
                    type: 'apply',
                    key: 'xml'
                },
                edit && own(ui.text, 'xml')
            )
        );
    if (ui.page === 'canvas' && (!narrow || ui.panel === 'canvas')) {
        // Layout commands share the graph's unused toolbar space after zoom controls.
        const toolbarX = x + 230,
            available = graphWidth - 230;
        if (available > 130) {
            nodes.push(
                node(
                    'Choice',
                    'adminGraphLayoutStyle',
                    rect(toolbarX, y, Math.max(80, available - 46), 38),
                    {
                        label: tr('Automatic layout'),
                        options: [
                            {
                                value: 'flow',
                                label: tr('Directed flow')
                            },
                            {
                                value: 'network',
                                label: tr('Network clusters')
                            },
                            {
                                value: 'grid',
                                label: tr('Alphabetical grid')
                            }
                        ],
                        value: ui.arrange,
                        action: {
                            type: 'arrange'
                        },
                        enabled: edit
                    }
                ),
                button(
                    'adminArrangeGraph',
                    rect(x + graphWidth - 38, y, 38, 38),
                    tr('Arrange nodes'),
                    'hierarchy',
                    {
                        type: 'layout'
                    },
                    edit && (model.nodes || []).length > 0,
                    {
                        iconOnly: true
                    }
                )
            );
        } else
            nodes.push(
                button(
                    'adminArrangeGraph',
                    rect(x + graphWidth - 38, y, 38, 38),
                    tr('Arrange nodes'),
                    'hierarchy',
                    {
                        type: 'layout'
                    },
                    edit && (model.nodes || []).length > 0,
                    {
                        iconOnly: true
                    }
                )
            );
    }
    return {
        nodes
    };
}

import { button } from '../../../core/frame.mjs';
import { node } from '../../../core/frame.mjs';
import {
    rect,
    label,
    muted,
    notices,
    toolbar as documentToolbar,
    sectionSelector,
    policy
} from '../admin.document.mjs';
import { sections as form } from '../../../controls/forms/sections.ui.mjs';
import { translate } from '../../../core/strings.mjs';
import {
    automaticFields,
    fieldTypes,
    removalReasons
} from './search_types.fields.mjs';
export function records(model, ui) {
    const query = ui.query.toLowerCase();
    return model.catalog.filter(
        (row) =>
            (!ui.projectOnly || row.projectLocal) &&
            (!ui.hideConfig || row.namespace !== 'config') &&
            [row.label, row.identity].join(' ').toLowerCase().indexOf(query) >=
                0
    );
}
export function existing(model, ui) {
    return Object.keys(model.metadata.columns || {})
        .filter(
            (name) =>
                name.toLowerCase().indexOf(ui.fieldQuery.toLowerCase()) >= 0
        )
        .map((name) => ({
            name,
            info: model.metadata.columns[name]
        }));
}
export function toolbar(model, ui, width, language) {
    if (ui.page === 'naming')
        return {
            nodes: []
        };
    const scene = documentToolbar(
            Object.assign({}, model, {
                saveAllowed:
                    (!model.creationOnly || ui.page === 'ready') &&
                    !!String(model.document.title || '').trim()
            }),
            ui,
            width,
            language
        ),
        tr = (text) => translate(text, language);
    scene.nodes = scene.nodes.filter((row) => row.id !== 'adminDocumentStatus');
    if (!model.creationOnly)
        scene.nodes.push(
            button(
                'adminCreateDocument',
                rect(46, 0, 38, 38),
                tr('New Search Type'),
                'add',
                {
                    type: 'create'
                },
                model.canWrite &&
                    !model.busy &&
                    !model.dirty &&
                    !model.uncertain &&
                    !model.namingLocked,
                {
                    iconOnly: true
                }
            )
        );
    return scene;
}
export function describe(model, ui, width, height, language) {
    if (width <= 0 || height <= 0)
        return {
            nodes: []
        };
    const tr = (text, values) => translate(text, language, values),
        changed = model.document.removedColumns || [],
        details = changed.length
            ? tr(
                  'All data in these columns will be lost. This editor cannot restore it after saving. Check any scripts, naming rules and saved searches that use these fields.'
              ) +
              '\n\n' +
              model.identity +
              '\n' +
              changed.map((name) => '• ' + name).join('\n')
            : '';
    const notice = notices(
            Object.assign({}, model, {
                error: model.error || ui.error,
                confirmationDetails: details
            }),
            ui,
            width,
            language,
            'Discard unsaved Search Type changes?'
        ),
        nodes = notice.nodes,
        y = notice.top,
        h = height - y;
    if (h < 320)
        return {
            nodes: [
                node('Scroll', 'typesPageScroll', rect(0, 0, width, height), {
                    contentHeight: y + 420,
                    children: describe(model, ui, width - 16, y + 420, language)
                        .nodes
                })
            ]
        };
    const split = !model.creationOnly && width >= 850,
        left = split ? Math.min(ui.catalogWidth, width * 0.4) : width,
        edit = policy(model).editable && !ui.confirmation,
        navigate =
            !model.busy &&
            !model.dirty &&
            !model.uncertain &&
            !model.namingLocked &&
            !ui.confirmation;
    if (!model.creationOnly && (split || !ui.editing)) {
        const children = [
            label(
                'typesCatalogTitle',
                rect(12, 8, left - 24, 28),
                tr('Search Types'),
                {
                    fontRole: 'section',
                    weight: 600
                }
            ),
            node(
                'Field',
                'adminSearchTypeFilter',
                rect(12, 44, left - 24, 38),
                {
                    label: tr('Find a Search Type'),
                    placeholder: tr('Find a Search Type'),
                    text: ui.query,
                    enabled: !model.busy,
                    action: {
                        type: 'query'
                    }
                }
            ),
            node(
                'CheckBox',
                'adminSearchTypesProjectOnly',
                rect(12, 90, left - 24, 32),
                {
                    text: tr('Only current project'),
                    checked: ui.projectOnly,
                    enabled: !model.busy,
                    action: {
                        type: 'projectOnly'
                    }
                }
            ),
            node(
                'CheckBox',
                'adminSearchTypesHideConfig',
                rect(12, 128, left - 24, 32),
                {
                    text: tr('Hide config types'),
                    checked: ui.hideConfig,
                    enabled: !model.busy,
                    action: {
                        type: 'hideConfig'
                    }
                }
            ),
            node(
                'List',
                'adminSearchTypesList',
                rect(12, 170, left - 24, h - 182),
                {
                    source: 'types',
                    rowHeight: 88,
                    keyField: 'identity',
                    scrollbarId: 'adminSearchTypesScrollBar'
                }
            )
        ];
        if (!records(model, ui).length)
            children.push(
                label(
                    'typesCatalogEmpty',
                    rect(12, 180, left - 24, 90),
                    tr('No types found'),
                    Object.assign(
                        {
                            wrap: true
                        },
                        muted
                    )
                )
            );
        nodes.push(
            node('Box', 'typesCatalogPanel', rect(0, y, left, h), {
                background: 'surfaceContainerLow',
                border: 'outlineVariant',
                children
            })
        );
    }
    if (split)
        nodes.push(
            node('Splitter', 'typesCatalogSplitHandle', rect(left, y, 10, h), {
                text: tr('Search Types panel width'),
                value: left,
                min: 200,
                max: width * 0.4,
                action: {
                    type: 'split'
                }
            })
        );
    if (!model.creationOnly && !split && !ui.editing)
        return {
            nodes
        };
    const bounds = rect(
            split ? left + 10 : 0,
            y,
            split ? width - left - 10 : width,
            h
        ),
        w = bounds.width - 40,
        children = [];
    let top = 12;
    if (!split && !model.creationOnly) {
        children.push(
            button(
                'typesBack',
                rect(12, top, 100, 36),
                tr('Back'),
                'chevron-left',
                {
                    type: 'back'
                },
                !model.busy && !!model.identity
            )
        );
        top += 44;
    }
    if (!model.ready)
        children.push(
            label(
                'typesSelectHelp',
                rect(12, top, w, 80),
                tr('Select a Search Type'),
                Object.assign(
                    {
                        wrap: true
                    },
                    muted
                )
            )
        );
    else {
        const pages = model.identity
            ? [
                  ['summary', 'Summary', 'info'],
                  ['workflow', 'Workflow', 'workflow'],
                  ['naming', 'Naming', 'edit'],
                  ['details', 'Details', 'edit'],
                  ['fields', 'Fields', 'table']
              ]
            : [
                  ['details', '1. Details', 'edit'],
                  ['fields', '2. Fields', 'table'],
                  ['ready', '3. Ready', 'check']
              ];
        children.push(
            sectionSelector(
                'searchTypePages',
                pages.map((row) => ({
                    value: row[0],
                    label: tr(row[1]),
                    icon: row[2]
                })),
                ui.page,
                rect(12, top, bounds.width - 24, 38),
                !model.busy,
                'page',
                tr('Search Type sections')
            )
        );
        top += 46;
        if (ui.page === 'naming')
            children.push(
                node(
                    'View',
                    'typeNaming',
                    rect(12, top, bounds.width - 24, h - top - 12),
                    {
                        view: 'naming'
                    }
                )
            );
        else {
            const footer = model.identity ? 0 : 46,
                body = content(
                    model,
                    ui,
                    w,
                    Math.max(160, h - top - 12 - footer),
                    language,
                    edit,
                    navigate
                );
            children.push(
                node(
                    'Scroll',
                    'adminSearchTypeForm',
                    rect(12, top, bounds.width - 24, h - top - 12 - footer),
                    {
                        contentHeight: body.height,
                        resetKey: model.identity + ':' + ui.page,
                        scrollbarId: 'adminSearchTypeFormScrollBar',
                        children: body.nodes
                    }
                )
            );
            if (!model.identity) {
                if (ui.page !== 'details')
                    children.push(
                        button(
                            'adminTypeWizardBack',
                            rect(12, h - 50, 100, 38),
                            tr('Back'),
                            'chevron-left',
                            {
                                type: 'page',
                                value:
                                    ui.page === 'ready' ? 'fields' : 'details'
                            },
                            !model.busy
                        )
                    );
                if (ui.page !== 'ready')
                    children.push(
                        button(
                            'adminTypeWizardNext',
                            rect(bounds.width - 112, h - 50, 100, 38),
                            tr('Next'),
                            'chevron-right',
                            {
                                type: 'page',
                                value:
                                    ui.page === 'details' ? 'fields' : 'ready'
                            },
                            edit
                        )
                    );
            }
        }
    }
    nodes.push(
        node('Box', 'typesEditorPanel', bounds, {
            background: 'surfaceContainerLow',
            border: 'outlineVariant',
            children
        })
    );
    return {
        nodes
    };
}
function content(model, ui, width, height, language, edit, navigate) {
    const tr = (text, values) => translate(text, language, values),
        nodes = [],
        doc = model.document,
        meta = model.metadata;
    let y = 0;
    const text = (key) => String(doc[key] || '');
    const heading = (id, title, description) => {
        nodes.push(
            label(id, rect(0, y, width, 28), title, {
                role: 'heading',
                level: 2,
                fontRole: 'section',
                weight: 600
            })
        );
        y += 34;
        if (description) {
            nodes.push(
                label(
                    id + 'Description',
                    rect(0, y, width, width < 420 ? 82 : 60),
                    description,
                    Object.assign(
                        {
                            wrap: true
                        },
                        muted
                    )
                )
            );
            y += width < 420 ? 90 : 68;
        }
    };
    if (meta.tableAvailable === false) {
        nodes.push(
            node(
                'Area',
                'adminSearchTypeMissingTable',
                rect(0, y, width, 100),
                {
                    text: tr(
                        'The database table is missing. Check the server schema before editing.'
                    ),
                    label: tr('Database'),
                    readOnly: true,
                    notice: true,
                    color: 'error'
                }
            )
        );
        y += 108;
    }
    if (ui.page === 'details') {
        const fields = [
            {
                kind: 'Heading',
                id: 'typeDetailsHeading',
                title: 'Details',
                description:
                    'How this Search Type appears in navigation and Search Object lists.'
            },
            {
                id: 'adminSearchTypeTitle',
                title: 'Title',
                description: 'A recognizable name for users.',
                props: {
                    text: text('title'),
                    action: {
                        type: 'field',
                        field: 'title'
                    }
                }
            },
            {
                id: 'adminSearchTypeDescription',
                title: 'Description',
                description: 'Explain what these Search Objects represent.',
                kind: 'Area',
                height: 82,
                props: {
                    text: text('description'),
                    action: {
                        type: 'field',
                        field: 'description'
                    }
                }
            },
            {
                kind: 'ColorChoice',
                id: 'adminSearchTypeColor',
                title: 'Accent color',
                description:
                    'Used in lists and the project schema. Reset to use the theme color.',
                field: 'color',
                props: {
                    value: doc.color || ''
                }
            },
            {
                kind: 'Button',
                id: 'adminSearchTypeResetColor',
                title: 'Reset color',
                props: {
                    icon: 'reset',
                    enabled: edit && !!doc.color,
                    action: {
                        type: 'field',
                        field: 'color',
                        value: ''
                    }
                }
            }
        ];
        if (!model.identity)
            fields.push({
                kind: 'Switch',
                id: 'adminSearchTypeHasPipeline',
                title: 'Objects use a pipeline',
                description: 'Allow processes and tasks for this Search Type.',
                field: 'hasPipeline',
                props: {
                    checked: !!doc.hasPipeline
                }
            });
        const body = form(fields, width, language, edit);
        nodes.push(
            ...body.nodes.map((row) =>
                Object.assign({}, row, {
                    y: row.y + y
                })
            )
        );
        y += body.height;
        heading(
            'typeImageHeading',
            tr('Search Type image'),
            tr(
                model.identity
                    ? 'The image belongs to the Search Type itself, not to one of its Search Objects. Saving adds the replacement to Commit Queue.'
                    : 'You can choose an image now. After the Search Type is created, its preview will be sent through Commit Queue.'
            )
        );
        const side = width < 420 ? 112 : 144;
        nodes.push(
            node('Preview', 'adminSearchTypePreview', rect(0, y, side, side), {
                source: model.previewUrl || '',
                initials: String(doc.title || '').slice(0, 2),
                round: false,
                icon: 'sobject',
                accent: doc.color || 'action',
                outlined: true
            }),
            button(
                'adminSearchTypeChoosePreview',
                rect(side + 12, y, width - side - 12, 38),
                tr('Choose image'),
                'image',
                {
                    type: 'preview'
                },
                edit && !model.previewQueued
            ),
            button(
                'adminSearchTypeCancelPreview',
                rect(side + 12, y + 46, width - side - 12, 38),
                tr('Undo image change'),
                'undo',
                {
                    type: 'clearPreview'
                },
                edit && model.previewStaged
            )
        );
        y += side + 12;
        nodes.push(
            node('Area', 'typeImageStatus', rect(0, y, width, 70), {
                text:
                    tr(
                        model.previewStaged
                            ? 'A new preview is ready to be queued'
                            : model.previewQueued
                              ? 'Image sent to Commit Queue; track upload progress there'
                              : model.identity
                                ? 'Current Search Type preview'
                                : 'Preview is optional'
                    ) + (model.previewError ? '\n' + model.previewError : ''),
                label: tr('Search Type image'),
                notice: true,
                readOnly: true,
                color: model.previewError ? 'error' : 'secondaryText'
            })
        );
        y += 78;
        nodes.push(
            button(
                'typeImageQueue',
                rect(0, y, width, 38),
                tr('Open Commit Queue'),
                'cloud-upload',
                {
                    type: 'queue'
                },
                true
            )
        );
        y += 46;
    } else if (ui.page === 'fields') {
        if (!model.identity) {
            heading(
                'adminAutomaticFields',
                tr('Default fields'),
                tr(
                    'TACTIC creates these fields automatically. Add only extra fields below.'
                )
            );
            nodes.push(
                node(
                    'Area',
                    'adminAutomaticFieldNames',
                    rect(0, y, width, 84),
                    {
                        text: automaticFields.join(', '),
                        label: tr('Default fields'),
                        readOnly: true,
                        notice: true
                    }
                ),
                label(
                    'adminAutomaticPipelineField',
                    rect(0, y + 92, width, 70),
                    tr(
                        doc.hasPipeline
                            ? 'pipeline_code will also be created: pipeline support is enabled.'
                            : 'pipeline_code will not be created: pipeline support is disabled.'
                    ),
                    Object.assign(
                        {
                            wrap: true
                        },
                        muted
                    )
                )
            );
            y += 170;
        }
        const field =
            fieldTypes.find((row) => row.value === ui.fieldType) ||
            fieldTypes[0];
        const body = form(
            [
                {
                    kind: 'Heading',
                    id: 'typeAddFieldHeading',
                    title: 'Add a field',
                    description:
                        'A field stores one attribute of each Search Object. Define its name and type here; fill in actual values when editing the objects.'
                },
                {
                    id: 'adminNewColumnName',
                    title: 'Field name',
                    description:
                        'A technical name: lowercase Latin letters, numbers and underscores. No spaces; start with a letter.',
                    props: {
                        text: ui.fieldName,
                        placeholder: field.name,
                        action: {
                            type: 'fieldName'
                        },
                        keys: {
                            Enter: {
                                type: 'addField'
                            }
                        }
                    }
                },
                {
                    id: 'adminNewColumnType',
                    kind: 'Choice',
                    title: 'Field type',
                    description: field.help,
                    options: fieldTypes.map((row) => ({
                        value: row.value,
                        label: tr(row.label)
                    })),
                    props: {
                        value: ui.fieldType,
                        action: {
                            type: 'fieldType'
                        }
                    }
                }
            ],
            width,
            language,
            edit
        );
        nodes.push(
            ...body.nodes.map((row) =>
                Object.assign({}, row, {
                    y: row.y + y
                })
            )
        );
        y += body.height;
        // These examples describe the type; they never create sample database values.
        nodes.push(
            label(
                'adminNewColumnExample',
                rect(0, y, width, 64),
                tr('Example: {name} = {value}', {
                    name: ui.fieldName.trim() || field.name,
                    value: tr(field.example)
                }) +
                    ' · ' +
                    tr('Database type: {type}', {
                        type: ui.fieldType
                    }),
                Object.assign(
                    {
                        wrap: true
                    },
                    muted
                )
            ),
            button(
                'adminStageColumn',
                rect(0, y + 72, width, 38),
                tr('Add field'),
                'add',
                {
                    type: 'addField'
                },
                edit && !!ui.fieldName.trim()
            )
        );
        y += 118;
        if ((doc.columns || []).length) {
            heading(
                'typeDraftFieldsHeading',
                tr('Fields to create ({count})', {
                    count: doc.columns.length
                }),
                tr(
                    'These fields exist only in your draft. Save creates them; removing a draft field does not change the database.'
                )
            );
            for (let index = 0; index < doc.columns.length; index++) {
                const row = doc.columns[index];
                nodes.push(
                    label(
                        'typeDraftName_' + row.name,
                        rect(0, y, width - 44, 26),
                        row.name,
                        {
                            weight: 600
                        }
                    ),
                    label(
                        'typeDraftType_' + row.name,
                        rect(0, y + 30, width - 44, 26),
                        row.type,
                        muted
                    ),
                    button(
                        'adminRemoveColumn_' + row.name,
                        rect(width - 38, y, 38, 38),
                        tr('Remove draft field {name}', {
                            name: row.name
                        }),
                        'delete',
                        {
                            type: 'removeDraft',
                            index
                        },
                        edit,
                        {
                            iconOnly: true
                        }
                    )
                );
                y += 66;
            }
        }
        if (model.identity) {
            heading(
                'typeExistingFieldsHeading',
                tr('Existing fields ({count})', {
                    count: Object.keys(meta.columns || {}).length
                }),
                tr(
                    'Delete marks a field for removal. Undo cancels the mark. Confirming Save deletes the column and its values; field types are not changed here.'
                )
            );
            nodes.push(
                node(
                    'Field',
                    'adminExistingFieldsFilter',
                    rect(0, y, width, 38),
                    {
                        text: ui.fieldQuery,
                        label: tr('Find a field'),
                        placeholder: tr('Find a field'),
                        action: {
                            type: 'fieldQuery'
                        }
                    }
                )
            );
            y += 46;
            nodes.push(
                node(
                    'List',
                    'typeExistingFields',
                    rect(0, y, width, Math.max(250, height - y)),
                    {
                        source: 'fields',
                        keyField: 'name',
                        rowHeight: width < 420 ? 192 : 144,
                        scrollbarId: 'typeExistingFieldsScrollBar'
                    }
                )
            );
            y += Math.max(250, height - y);
        }
    } else if (ui.page === 'summary') {
        heading(
            'typeSummaryHeading',
            doc.title || model.identity,
            model.identity
        );
        const metrics = [
                ['total', 'Search Objects'],
                ['active', 'Active'],
                ['retired', 'Retired'],
                ['fields', 'Fields'],
                ['pipelines', 'Pipelines'],
                ['processes', 'Processes']
            ],
            columns = width < 420 ? 2 : 3;
        metrics.forEach((row, index) => {
            const x = ((index % columns) * width) / columns,
                top = y + Math.floor(index / columns) * 72;
            nodes.push(
                label(
                    'adminSearchTypeCount_' + row[0],
                    rect(x, top, width / columns - 8, 34),
                    String(
                        (meta.summary || {})[row[0]] === undefined
                            ? '—'
                            : meta.summary[row[0]]
                    ),
                    {
                        fontRole: 'hero',
                        weight: 600
                    }
                ),
                label(
                    'typeMetricLabel_' + row[0],
                    rect(x, top + 38, width / columns - 8, 26),
                    tr(row[1]),
                    muted
                )
            );
        });
        y += Math.ceil(metrics.length / columns) * 72;
        nodes.push(
            label(
                'typeSummaryHelp',
                rect(0, y, width, 76),
                tr(
                    'Totals include retired Search Objects. Shared system types are counted in their own database. Reload to update the summary.'
                ),
                Object.assign(
                    {
                        wrap: true
                    },
                    muted
                )
            )
        );
        y += 84;
        heading(
            'typeGraphHeading',
            tr('Relationship map'),
            tr(
                'A read-only view of this Search Type and only its direct schema relationships.'
            )
        );
        nodes.push(
            node(
                'Graph',
                'adminSearchTypeRelationshipGraph',
                rect(0, y, width, 400),
                Object.assign(
                    {},
                    model.relationshipGraph || {
                        nodes: [],
                        edges: []
                    },
                    {
                        label: tr('Relationship map'),
                        style: model.style,
                        language,
                        readOnly: true,
                        selectionEnabled: false,
                        selectedNodes: model.identity ? [model.identity] : []
                    }
                )
            )
        );
        y += 412;
        heading(
            'typeRelationsHeading',
            tr('Schema relationships'),
            tr(
                meta.linkTable
                    ? 'This is a link table for a many-to-many relationship, not a separate object category.'
                    : "Relationships come from this project's schema and inherited schemas, not from table names."
            )
        );
        nodes.push(
            node('Area', 'typeDataLocation', rect(0, y, width, 92), {
                text:
                    tr('Database') +
                    ': ' +
                    (meta.database || '—') +
                    ' · ' +
                    tr('Table') +
                    ': ' +
                    (meta.table || '—') +
                    '\n' +
                    tr(
                        meta.projectLocal
                            ? 'Stored in the selected project'
                            : 'Shared data outside the selected project'
                    ),
                label: tr('Data location'),
                readOnly: true,
                notice: true
            })
        );
        y += 100;
        for (
            let index = 0;
            index < (meta.relationships || []).length;
            index++
        ) {
            const edge = meta.relationships[index],
                name = (id) =>
                    (model.catalog.find((row) => row.identity === id) || {})
                        .label || id;
            nodes.push(
                node(
                    'Area',
                    'adminSearchTypeRelation_' + index,
                    rect(0, y, width, 164),
                    {
                        text:
                            name(edge.from) +
                            ' → ' +
                            name(edge.to) +
                            '\n' +
                            relationshipDescription(edge, language),
                        label: tr('Schema relationships'),
                        readOnly: true,
                        notice: true
                    }
                )
            );
            y += 172;
        }
        if (!(meta.relationships || []).length) {
            nodes.push(
                label(
                    'typeRelationshipsEmpty',
                    rect(0, y, width, 72),
                    tr(
                        'No explicit relationships for this type in the loaded schemas.'
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
        }
    } else if (ui.page === 'workflow') {
        heading(
            'typeWorkflowsHeading',
            tr('Linked workflows'),
            tr(
                'Pipelines linked to this Search Type, including shared workflows.'
            )
        );
        if (!meta.hasPipeline) {
            nodes.push(
                label(
                    'typePipelineMissing',
                    rect(0, y, width, 80),
                    tr(
                        'This type has no pipeline_code field. Add it in Fields to assign workflows to its objects.'
                    ),
                    Object.assign(
                        {
                            wrap: true
                        },
                        muted
                    )
                )
            );
            y += 88;
        }
        for (const row of meta.pipelines || []) {
            nodes.push(
                label(
                    'typeWorkflowTitle_' + row.identity,
                    rect(0, y, width, 28),
                    row.label,
                    {
                        weight: 600
                    }
                ),
                node(
                    'Area',
                    'typeWorkflowDescription_' + row.identity,
                    rect(0, y + 32, width, 86),
                    {
                        text:
                            (row.description || '') +
                            '\n' +
                            tr('{count} processes', {
                                count: row.processCount
                            }) +
                            (row.shared
                                ? ' · ' + tr('Shared · read-only')
                                : ''),
                        label: tr('Workflow'),
                        readOnly: true,
                        notice: true
                    }
                ),
                button(
                    'adminSearchTypeWorkflow_' + row.identity,
                    rect(0, y + 126, width, 38),
                    tr('Open workflow'),
                    'workflow',
                    {
                        type: 'workflow',
                        identity: row.identity
                    },
                    !model.busy && !model.uncertain && !model.namingLocked
                )
            );
            y += 178;
        }
        if (!(meta.pipelines || []).length) {
            nodes.push(
                label(
                    'typeWorkflowsEmpty',
                    rect(0, y, width, 70),
                    tr('No workflows linked to this Search Type.'),
                    Object.assign(
                        {
                            wrap: true
                        },
                        muted
                    )
                )
            );
            y += 78;
        }
        nodes.push(
            button(
                'adminCreateTypeWorkflow',
                rect(0, y, width, 38),
                tr('Create workflow'),
                'add',
                {
                    type: 'workflow',
                    identity: ''
                },
                !model.busy &&
                    !model.uncertain &&
                    !model.namingLocked &&
                    model.canWrite
            )
        );
        y += 46;
    } else if (ui.page === 'ready') {
        heading(
            'adminSearchTypeCreationReview',
            tr('Ready to create'),
            tr(
                'This is how the new Search Type will appear. Nothing has been created on the server yet.'
            )
        );
        nodes.push(
            node(
                'Preview',
                'adminSearchTypeCreationPreview',
                rect(0, y, 144, 144),
                {
                    source: model.previewUrl || '',
                    initials: String(doc.title || '').slice(0, 2),
                    round: false,
                    accent: doc.color || 'action',
                    icon: 'sobject'
                }
            )
        );
        y += 156;
        nodes.push(
            label(
                'adminSearchTypeCreationTitle',
                rect(0, y, width, 32),
                doc.title || '',
                {
                    fontRole: 'display',
                    weight: 600,
                    color: doc.color || 'action'
                }
            )
        );
        y += 40;
        for (const row of [
            ['adminSearchTypeCreationDescription', doc.description],
            [
                'typeReviewPipeline',
                tr(doc.hasPipeline ? 'Objects use a pipeline' : 'No pipeline')
            ],
            [
                'adminSearchTypeCreationStandardFields',
                automaticFields
                    .concat(doc.hasPipeline ? ['pipeline_code'] : [])
                    .join(', ')
            ],
            [
                'adminSearchTypeCreationAdditionalFields',
                (doc.columns || [])
                    .map((row) => row.name + ' (' + row.type + ')')
                    .join('\n')
            ]
        ]) {
            nodes.push(
                node('Area', row[0], rect(0, y, width, 80), {
                    text: row[1] || '',
                    label: tr('Ready to create'),
                    readOnly: true,
                    notice: true
                })
            );
            y += 88;
        }
        nodes.push(
            button(
                'typeCreateNow',
                rect(0, y, width, 38),
                tr('Create Search Type'),
                'add',
                {
                    type: 'save'
                },
                edit
            )
        );
        y += 46;
    }
    return {
        nodes,
        height: y + 8
    };
}
export function relationshipDescription(edge, language) {
    const tr = (text, values) => translate(text, language, values),
        parts = [];
    if (edge.manyToMany)
        parts.push(
            tr(
                'Many-to-many (M:N): each side can be linked to several objects on the other side.'
            )
        );
    else if (edge.type === 'hierarchy')
        parts.push(tr('Hierarchy: child → parent.'));
    if (edge.relationship || edge.type)
        parts.push(
            tr('Relationship in schema: {kind}', {
                kind: edge.relationship || edge.type
            })
        );
    if (edge.instanceType)
        parts.push(
            tr('Link table: {name}', {
                name: edge.instanceType
            })
        );
    if (edge.from_col || edge.to_col)
        parts.push(
            tr('Key fields: {from} → {to}', {
                from: edge.from_col || '—',
                to: edge.to_col || '—'
            })
        );
    parts.push(
        tr('Schema: {name}', {
            name: edge.schema || '—'
        })
    );
    return parts.join('\n');
}
export function fieldDescription(info, language) {
    const tr = (text, values) => translate(text, language, values),
        name = String(info.data_type || '')
            .toLowerCase()
            .split('(')[0]
            .trim();
    const index = {
            varchar: 0,
            'character varying': 0,
            character: 0,
            char: 0,
            text: 1,
            integer: 2,
            bigint: 2,
            smallint: 2,
            int: 2,
            int4: 2,
            int8: 2,
            numeric: 3,
            decimal: 3,
            real: 3,
            'double precision': 3,
            boolean: 4,
            bool: 4
        }[name],
        type = fieldTypes[name.indexOf('timestamp') === 0 ? 5 : index];
    const parts = [
        type ? tr(type.label) + ' · ' + info.data_type : info.data_type || ''
    ];
    if (info.character_maximum_length)
        parts.push(
            tr('Up to {count} characters', {
                count: info.character_maximum_length
            })
        );
    if (info.is_nullable === 'NO' || info.is_nullable === false)
        parts.push(tr('Cannot be empty in the database'));
    if (type)
        parts.push(
            tr('Example value: {value}', {
                value: tr(type.example)
            })
        );
    return parts.join('\n');
}
export function row(listNode, record, model, ui, language) {
    const width = listNode.width - 16,
        tr = (text, values) => translate(text, language, values);
    if (listNode.source === 'types') {
        const role = record.linkTable
            ? tr('Link table · M:N')
            : record.manyToMany
              ? tr('Many-to-many · M:N')
              : (record.relationships || []).length
                ? tr('Schema relationships: {count}', {
                      count: record.relationships.length
                  })
                : record.table || '';
        return {
            nodes: [
                node(
                    'Action',
                    'adminSearchType_' + record.identity,
                    rect(0, 0, width, 84),
                    {
                        text: record.label,
                        selected: model.identity === record.identity,
                        enabled:
                            !model.busy &&
                            (model.identity === record.identity ||
                                (!model.dirty &&
                                    !model.uncertain &&
                                    !model.namingLocked)),
                        normalColor: 'surfaceContainerHigh',
                        selectedColor: 'contentSelection',
                        children: [
                            node(
                                'Icon',
                                'typeIcon_' + record.identity,
                                rect(10, 12, 22, 22),
                                {
                                    icon: record.linkTable ? 'link' : 'sobject',
                                    color: record.color || 'action'
                                }
                            ),
                            label(
                                'typeTitle_' + record.identity,
                                rect(42, 6, width - 54, 26),
                                record.label,
                                {
                                    weight: 600
                                }
                            ),
                            label(
                                'typeIdentity_' + record.identity,
                                rect(42, 34, width - 54, 20),
                                record.identity,
                                muted
                            ),
                            label(
                                'adminSearchTypeRole_' + record.identity,
                                rect(42, 58, width - 54, 20),
                                role,
                                muted
                            )
                        ],
                        action: {
                            type: 'select',
                            identity: record.identity
                        }
                    }
                )
            ]
        };
    }
    const marked =
            (model.document.removedColumns || []).indexOf(record.name) >= 0,
        reason =
            removalReasons[
                (model.metadata.columnRemovalBlocks || {})[record.name]
            ],
        narrow = width < 420;
    return {
        nodes: [
            label(
                'typeExistingName_' + record.name,
                rect(0, 0, narrow ? width : width - 160, 26),
                record.name,
                {
                    weight: 600,
                    strike: marked
                }
            ),
            label(
                'adminExistingField_' + record.name,
                rect(0, 32, narrow ? width : width - 160, narrow ? 104 : 100),
                marked
                    ? tr(
                          'Marked for deletion. The column and its data will be deleted when you save.'
                      )
                    : fieldDescription(record.info, language) +
                          (reason ? '\n' + tr(reason) : ''),
                Object.assign(
                    {
                        wrap: true
                    },
                    muted
                )
            ),
            button(
                'adminDeleteColumn_' + record.name,
                rect(narrow ? 0 : width - 152, narrow ? 144 : 8, 152, 36),
                tr(marked ? 'Undo deletion' : 'Delete field'),
                marked ? 'undo' : 'delete',
                {
                    type: 'removeField',
                    name: record.name
                },
                policy(model).editable && (!reason || marked),
                {
                    destructive: !marked && !reason
                }
            )
        ]
    };
}

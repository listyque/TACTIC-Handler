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
    const query = (ui.query || '').toLowerCase();
    if (!query && !ui.projectOnly && !ui.hideConfig) return model.catalog;
    return model.catalog.filter(
        (row) =>
            (!ui.projectOnly || row.projectLocal) &&
            (!ui.hideConfig || row.namespace !== 'config') &&
            (!query ||
                String(row.label || '')
                    .toLowerCase()
                    .indexOf(query) >= 0 ||
                String(row.identity || '')
                    .toLowerCase()
                    .indexOf(query) >= 0)
    );
}
export function existing(model, ui) {
    const columns = model.metadata.columns || {},
        query = (ui.fieldQuery || '').toLowerCase(),
        names = Object.keys(columns);
    return (
        query
            ? names.filter((name) => name.toLowerCase().indexOf(query) >= 0)
            : names
    ).map((name) => ({
        name,
        info: columns[name]
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
        catalogVisible = ui.catalogVisible !== false,
        left = split
            ? catalogVisible
                ? Math.min(ui.catalogWidth, width * 0.4)
                : 56
            : width,
        edit = policy(model).editable && !ui.confirmation,
        navigate =
            !model.busy &&
            !model.dirty &&
            !model.uncertain &&
            !model.namingLocked &&
            !ui.confirmation;
    if (!model.creationOnly && (split || !ui.editing)) {
        const children = [];
        if (!split || catalogVisible) {
            children.push(
                label(
                    'typesCatalogTitle',
                    rect(12, 10, Math.max(0, left - (split ? 62 : 24)), 34),
                    tr('Search Types'),
                    {
                        weight: 600
                    }
                ),
                node(
                    'Field',
                    'adminSearchTypeFilter',
                    rect(12, 52, left - 24, 38),
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
                    rect(12, 98, left - 24, 32),
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
                    rect(12, 136, left - 24, 32),
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
                    rect(12, 176, left - 24, Math.max(0, h - 188)),
                    {
                        source: 'types',
                        rowHeight: 88,
                        keyField: 'identity',
                        scrollbarId: 'adminSearchTypesScrollBar'
                    }
                )
            );
            if (!records(model, ui).length)
                children.push(
                    label(
                        'typesCatalogEmpty',
                        rect(12, 186, left - 24, 90),
                        tr('No types found'),
                        Object.assign(
                            {
                                wrap: true
                            },
                            muted
                        )
                    )
                );
        }
        if (split)
            children.push(
                button(
                    'adminToggleTypesCatalog',
                    rect(
                        catalogVisible ? left - 46 : (left - 34) / 2,
                        10,
                        34,
                        34
                    ),
                    tr(
                        catalogVisible
                            ? 'Hide Search Types'
                            : 'Show Search Types'
                    ),
                    catalogVisible ? 'chevron-left' : 'chevron-right',
                    {
                        type: 'catalogVisible'
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
            node('Box', 'typesCatalogPanel', rect(0, y, left, h), {
                background: 'surfaceContainerLow',
                border: 'outlineVariant',
                children
            })
        );
    }
    if (split && catalogVisible)
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
        const addPad = width < 380 ? 10 : 14,
            inlineAdd = width >= 560,
            addBtnW = inlineAdd
                ? Math.min(
                      Math.max(164, tr('Add field').length * 7.5 + 48),
                      210
                  )
                : Math.max(1, width - addPad * 2),
            exampleW = Math.max(
                40,
                width -
                    addPad * 2 -
                    28 -
                    (inlineAdd ? addBtnW + 14 : 0)
            ),
            addCardH = inlineAdd ? 62 : 104;
        nodes.push(
            node(
                'Box',
                'typeAddFieldFooterCard',
                rect(0, y, width, addCardH),
                {
                    background: 'surfaceContainer',
                    border: 'outlineVariant',
                    radius: 10,
                    children: [
                        node(
                            'Icon',
                            'typeAddFieldExampleIcon',
                            rect(addPad, inlineAdd ? 22 : 14, 18, 18),
                            {
                                icon: 'code',
                                color: 'action'
                            }
                        ),
                        label(
                            'adminNewColumnExample',
                            rect(
                                addPad + 26,
                                inlineAdd ? 10 : 8,
                                exampleW,
                                42
                            ),
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
                                    wrap: true,
                                    monospace: true
                                },
                                muted
                            )
                        ),
                        button(
                            'adminStageColumn',
                            inlineAdd
                                ? rect(
                                      width - addPad - addBtnW,
                                      12,
                                      addBtnW,
                                      38
                                  )
                                : rect(addPad, 54, addBtnW, 38),
                            tr('Add field'),
                            'add',
                            {
                                type: 'addField'
                            },
                            edit && !!ui.fieldName.trim()
                        )
                    ]
                }
            )
        );
        y += addCardH + 14;
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
                const row = doc.columns[index],
                    dPad = width < 380 ? 10 : 14;
                nodes.push(
                    node(
                        'Box',
                        'typeDraftCard_' + row.name,
                        rect(0, y, width, 62),
                        {
                            background: 'surfaceContainer',
                            border: 'outlineVariant',
                            radius: 10,
                            children: [
                                node(
                                    'Icon',
                                    'typeDraftIcon_' + row.name,
                                    rect(dPad, 14, 18, 18),
                                    {
                                        icon: 'add',
                                        color: 'action'
                                    }
                                ),
                                label(
                                    'typeDraftName_' + row.name,
                                    rect(
                                        dPad + 26,
                                        8,
                                        Math.max(0, width - dPad * 2 - 74),
                                        24
                                    ),
                                    row.name,
                                    {
                                        weight: 600,
                                        monospace: true
                                    }
                                ),
                                label(
                                    'typeDraftType_' + row.name,
                                    rect(
                                        dPad + 26,
                                        32,
                                        Math.max(0, width - dPad * 2 - 74),
                                        20
                                    ),
                                    row.type,
                                    Object.assign({ monospace: true }, muted)
                                ),
                                button(
                                    'adminRemoveColumn_' + row.name,
                                    rect(width - dPad - 38, 12, 38, 38),
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
                                        iconOnly: true,
                                        round: false
                                    }
                                )
                            ]
                        }
                    )
                );
                y += 70;
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
                        rowHeight: width < 420 ? 188 : 136,
                        scrollbarId: 'typeExistingFieldsScrollBar'
                    }
                )
            );
            y += Math.max(250, height - y);
        }
    } else if (ui.page === 'summary') {
        const textHeight = (value) =>
            String(value)
                .split('\n')
                .reduce(
                    (lines, line) =>
                        lines +
                        Math.max(
                            1,
                            Math.ceil(
                                line.length /
                                    Math.max(12, Math.floor((width - 24) / 7))
                            )
                        ),
                    0
                ) * 20;
        const summaryHeading = (id, title, description) => {
            nodes.push(
                label(id, rect(0, y, width, 28), title, {
                    role: 'heading',
                    level: 2,
                    fontRole: 'section',
                    weight: 600
                })
            );
            y += 30;
            if (description) {
                const h = textHeight(description);
                nodes.push(
                    label(
                        id + 'Description',
                        rect(0, y, width, h),
                        description,
                        Object.assign({ wrap: true }, muted)
                    )
                );
                y += h + 8;
            }
        };
        const metrics = [
                ['total', 'Search Objects'],
                ['active', 'Active'],
                ['retired', 'Retired'],
                ['fields', 'Fields'],
                ['pipelines', 'Pipelines'],
                ['processes', 'Processes']
            ],
            columns = width >= 960 ? 6 : width >= 540 ? 3 : 2,
            rowHeight = 64,
            metricsHeight = Math.ceil(metrics.length / columns) * rowHeight,
            metricNodes = [];
        metrics.forEach((row, index) => {
            const x = ((index % columns) * width) / columns,
                top = Math.floor(index / columns) * rowHeight;
            if (index % columns)
                metricNodes.push(
                    node(
                        'Box',
                        'typeMetricDivider_' + row[0],
                        rect(x, top + 10, 1, rowHeight - 20),
                        { background: 'outlineVariant', radius: 0 }
                    )
                );
            if (index && index % columns === 0)
                metricNodes.push(
                    node(
                        'Box',
                        'typeMetricRowDivider_' + row[0],
                        rect(12, top, width - 24, 1),
                        { background: 'outlineVariant', radius: 0 }
                    )
                );
            metricNodes.push(
                label(
                    'adminSearchTypeCount_' + row[0],
                    rect(x + 12, top + 6, width / columns - 24, 28),
                    String(
                        (meta.summary || {})[row[0]] === undefined
                            ? '—'
                            : meta.summary[row[0]]
                    ),
                    {
                        fontRole: 'title',
                        weight: 600
                    }
                ),
                label(
                    'typeMetricLabel_' + row[0],
                    rect(x + 12, top + 36, width / columns - 24, 22),
                    tr(row[1]),
                    muted
                )
            );
        });
        nodes.push(
            node(
                'Box',
                'typeSummaryMetrics',
                rect(0, y, width, metricsHeight),
                {
                    background: 'surfaceContainerHigh',
                    border: 'outlineVariant',
                    radius: 10,
                    children: metricNodes
                }
            )
        );
        y += metricsHeight + 12;
        summaryHeading('typeGraphHeading', tr('Relationship map'));
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
        summaryHeading(
            'typeRelationsHeading',
            tr('Schema relationships'),
            tr(
                meta.linkTable
                    ? 'This is a link table for a many-to-many relationship, not a separate object category.'
                    : "Relationships come from this project's schema and inherited schemas, not from table names."
            )
        );
        const locPad = width < 380 ? 10 : 14,
            locInner = Math.max(1, width - locPad * 2),
            locCols = locInner >= 420 ? 2 : 1,
            locCellW = (locInner - (locCols - 1) * 10) / locCols,
            locScopeText = tr(
                meta.projectLocal
                    ? 'Stored in the selected project'
                    : 'Shared data outside the selected project'
            ),
            locText =
                tr('Database') +
                ': ' +
                (meta.database || '—') +
                ' · ' +
                tr('Table') +
                ': ' +
                (meta.table || '—') +
                '\n' +
                locScopeText,
            locRows = locCols === 2 ? 1 : 2,
            locCardH = 44 + locRows * 52 + (locRows - 1) * 8 + 12,
            locChildren = [
                node('Icon', 'typeDataLocationIcon', rect(locPad, 12, 18, 18), {
                    icon: 'storage',
                    color: 'action'
                }),
                label(
                    'typeDataLocationTitle',
                    rect(locPad + 26, 9, Math.max(0, locInner - 26), 24),
                    tr('Data location'),
                    {
                        weight: 600
                    }
                )
            ];
        if (width >= 460) {
            const badgeW = Math.min(
                Math.max(150, locScopeText.length * 6.8 + 36),
                Math.floor(width * 0.56)
            );
            locChildren.push(
                node(
                    'Box',
                    'typeDataLocationScopeBadge',
                    rect(width - locPad - badgeW, 8, badgeW, 26),
                    {
                        background: 'surfaceContainerHigh',
                        border: 'outlineVariant',
                        radius: 13,
                        children: [
                            node(
                                'Icon',
                                'typeDataLocationScopeIcon',
                                rect(10, 5, 15, 15),
                                {
                                    icon: meta.projectLocal
                                        ? 'folder-open'
                                        : 'layers',
                                    color: 'action'
                                }
                            ),
                            label(
                                'typeDataLocationScopeLabel',
                                rect(30, 3, Math.max(0, badgeW - 38), 20),
                                locScopeText,
                                {
                                    fontRole: 'secondary',
                                    weight: 600
                                }
                            )
                        ]
                    }
                )
            );
        }
        [
            ['db', 'dns', tr('Database'), meta.database || '—'],
            ['table', 'table-view', tr('Table'), meta.table || '—']
        ].forEach(([key, iconName, titleText, valText], idx) => {
            const r = Math.floor(idx / locCols),
                c = idx % locCols,
                tx = locPad + c * (locCellW + 10),
                ty = 44 + r * 60;
            locChildren.push(
                node(
                    'Box',
                    'typeDataLocationTile_' + key,
                    rect(tx, ty, locCellW, 52),
                    {
                        background: 'surfaceContainerHigh',
                        border: 'outlineVariant',
                        radius: 8,
                        children: [
                            node(
                                'Icon',
                                'typeDataLocationTileIcon_' + key,
                                rect(10, 8, 14, 14),
                                {
                                    icon: iconName,
                                    color: 'action'
                                }
                            ),
                            label(
                                'typeDataLocationTileLabel_' + key,
                                rect(28, 5, Math.max(0, locCellW - 36), 18),
                                titleText,
                                muted
                            ),
                            label(
                                'typeDataLocationTileValue_' + key,
                                rect(10, 25, Math.max(0, locCellW - 20), 22),
                                valText,
                                {
                                    weight: 600,
                                    monospace: true
                                }
                            )
                        ]
                    }
                )
            );
        });
        nodes.push(
            node('Box', 'typeDataLocation', rect(0, y, width, locCardH), {
                text: locText,
                background: 'surfaceContainer',
                border: 'outlineVariant',
                radius: 10,
                children: locChildren
            })
        );
        y += locCardH + 10;
        for (
            let index = 0;
            index < (meta.relationships || []).length;
            index++
        ) {
            const edge = meta.relationships[index],
                name = (id) =>
                    (model.catalog.find((row) => row.identity === id) || {})
                        .label || id,
                fromLabel = name(edge.from),
                toLabel = name(edge.to),
                description =
                    fromLabel +
                    ' → ' +
                    toLabel +
                    '\n' +
                    relationshipDescription(edge, language),
                cardPad = width < 380 ? 10 : 14,
                innerW = Math.max(1, width - cardPad * 2),
                tiles = [];
            if (edge.from_col || edge.to_col)
                tiles.push([
                    'keys',
                    'key',
                    tr('Key fields'),
                    (edge.from_col || '—') + '  →  ' + (edge.to_col || '—'),
                    true
                ]);
            if (edge.relationship || edge.type)
                tiles.push([
                    'kind',
                    'code',
                    tr('Relationship in schema'),
                    String(edge.relationship || edge.type),
                    true
                ]);
            tiles.push([
                'schema',
                'folder-open',
                tr('Schema'),
                String(edge.schema || '—'),
                true
            ]);
            if (edge.instanceType)
                tiles.push([
                    'linkTable',
                    'link',
                    tr('Link table'),
                    String(edge.instanceType),
                    true
                ]);
            const tileCols =
                    innerW >= 620
                        ? Math.min(tiles.length, 3)
                        : innerW >= 400
                          ? Math.min(tiles.length, 2)
                          : 1,
                tileGap = 10,
                tileW =
                    (innerW - (tileCols - 1) * tileGap) /
                    Math.max(1, tileCols),
                tileRows = Math.ceil(tiles.length / Math.max(1, tileCols)),
                manyNote = edge.manyToMany
                    ? tr(
                          'Many-to-many (M:N): each side can be linked to several objects on the other side.'
                      )
                    : '',
                manyNoteH = manyNote ? (width < 460 ? 44 : 26) : 0,
                relationHeight =
                    52 +
                    tileRows * 52 +
                    Math.max(0, tileRows - 1) * 8 +
                    (manyNoteH ? manyNoteH + 10 : 0) +
                    14,
                modeBadgeText = edge.manyToMany
                    ? tr('Many-to-many · M:N')
                    : edge.type === 'hierarchy'
                      ? tr('Hierarchy · child → parent')
                      : tr('Schema link'),
                showBadge = width >= 460,
                badgeW = showBadge
                    ? Math.min(
                          Math.max(130, modeBadgeText.length * 6.8 + 34),
                          Math.floor(width * 0.44)
                      )
                    : 0,
                headerAvailW = Math.max(
                    60,
                    innerW - 26 - (showBadge ? badgeW + 10 : 0)
                ),
                relChildren = [
                    node(
                        'Icon',
                        'adminSearchTypeRelationIcon_' + index,
                        rect(cardPad, 13, 18, 18),
                        {
                            icon: edge.manyToMany ? 'link' : 'hierarchy',
                            color: 'action'
                        }
                    ),
                    label(
                        'adminSearchTypeRelationTitle_' + index,
                        rect(cardPad + 26, 10, headerAvailW, 24),
                        fromLabel + '  →  ' + toLabel,
                        {
                            fontRole: 'section',
                            weight: 600
                        }
                    ),
                    node(
                        'Box',
                        'adminSearchTypeRelationDivider_' + index,
                        rect(cardPad, 42, innerW, 1),
                        {
                            background: 'outlineVariant'
                        }
                    )
                ];
            if (showBadge) {
                relChildren.push(
                    node(
                        'Box',
                        'adminSearchTypeRelationBadge_' + index,
                        rect(width - cardPad - badgeW, 9, badgeW, 26),
                        {
                            background: 'surfaceContainerHigh',
                            border: 'outlineVariant',
                            radius: 13,
                            children: [
                                node(
                                    'Icon',
                                    'adminSearchTypeRelationBadgeIcon_' + index,
                                    rect(10, 5, 15, 15),
                                    {
                                        icon: edge.manyToMany
                                            ? 'link'
                                            : 'hierarchy',
                                        color: 'action'
                                    }
                                ),
                                label(
                                    'adminSearchTypeRelationBadgeText_' + index,
                                    rect(30, 3, Math.max(0, badgeW - 38), 20),
                                    modeBadgeText,
                                    {
                                        fontRole: 'secondary',
                                        weight: 600
                                    }
                                )
                            ]
                        }
                    )
                );
            }
            tiles.forEach(([tKey, tIcon, tLabel, tVal, mono], tIdx) => {
                const r = Math.floor(tIdx / tileCols),
                    c = tIdx % tileCols,
                    tx = cardPad + c * (tileW + tileGap),
                    ty = 52 + r * 60;
                relChildren.push(
                    node(
                        'Box',
                        'adminSearchTypeRelationTile_' + index + '_' + tKey,
                        rect(tx, ty, tileW, 52),
                        {
                            background: 'surfaceContainerHigh',
                            border: 'outlineVariant',
                            radius: 8,
                            children: [
                                node(
                                    'Icon',
                                    'adminSearchTypeRelationTileIcon_' +
                                        index +
                                        '_' +
                                        tKey,
                                    rect(10, 8, 14, 14),
                                    {
                                        icon: tIcon,
                                        color: 'action'
                                    }
                                ),
                                label(
                                    'adminSearchTypeRelationTileLabel_' +
                                        index +
                                        '_' +
                                        tKey,
                                    rect(28, 5, Math.max(0, tileW - 36), 18),
                                    tLabel,
                                    muted
                                ),
                                label(
                                    'adminSearchTypeRelationTileValue_' +
                                        index +
                                        '_' +
                                        tKey,
                                    rect(10, 25, Math.max(0, tileW - 20), 22),
                                    tVal,
                                    {
                                        weight: 600,
                                        monospace: !!mono
                                    }
                                )
                            ]
                        }
                    )
                );
            });
            if (manyNote) {
                const noteY =
                    52 + tileRows * 52 + Math.max(0, tileRows - 1) * 8 + 8;
                relChildren.push(
                    label(
                        'adminSearchTypeRelationNote_' + index,
                        rect(cardPad, noteY, innerW, manyNoteH),
                        manyNote,
                        Object.assign({ wrap: true }, muted)
                    )
                );
            }
            nodes.push(
                node(
                    'Box',
                    'adminSearchTypeRelation_' + index,
                    rect(0, y, width, relationHeight),
                    {
                        text: description,
                        background: 'surfaceContainer',
                        border: 'outlineVariant',
                        radius: 10,
                        children: relChildren
                    }
                )
            );
            y += relationHeight + 10;
        }
        if (!(meta.relationships || []).length) {
            const empty = tr(
                    'No explicit relationships for this type in the loaded schemas.'
                ),
                emptyHeight = textHeight(empty);
            nodes.push(
                label(
                    'typeRelationshipsEmpty',
                    rect(0, y, width, emptyHeight),
                    empty,
                    Object.assign(
                        {
                            wrap: true
                        },
                        muted
                    )
                )
            );
            y += emptyHeight + 8;
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
            const missingPad = width < 380 ? 10 : 14,
                missingH = width < 520 ? 76 : 56;
            nodes.push(
                node(
                    'Box',
                    'typePipelineMissingCard',
                    rect(0, y, width, missingH),
                    {
                        background: 'surfaceContainer',
                        border: 'outlineVariant',
                        radius: 10,
                        children: [
                            node(
                                'Icon',
                                'typePipelineMissingIcon',
                                rect(missingPad, 14, 18, 18),
                                {
                                    icon: 'warning',
                                    color: 'warning'
                                }
                            ),
                            label(
                                'typePipelineMissing',
                                rect(
                                    missingPad + 28,
                                    10,
                                    Math.max(0, width - missingPad * 2 - 28),
                                    missingH - 20
                                ),
                                tr(
                                    'This type has no pipeline_code field. Add it in Fields to assign workflows to its objects.'
                                ),
                                Object.assign({ wrap: true }, muted)
                            )
                        ]
                    }
                )
            );
            y += missingH + 12;
        }
        const canOpenWorkflow =
            !model.busy && !model.uncertain && !model.namingLocked;
        for (const row of meta.pipelines || []) {
            const cardPad = width < 380 ? 10 : 14,
                innerW = Math.max(1, width - cardPad * 2),
                inlineAction = width >= 460,
                openBtnW = inlineAction
                    ? Math.min(
                          Math.max(156, tr('Open workflow').length * 7.5 + 44),
                          210
                      )
                    : innerW,
                scopeText = row.shared
                    ? tr('Shared · read-only')
                    : tr('Current project'),
                showBadge = width >= 660,
                badgeW = showBadge
                    ? Math.min(
                          Math.max(126, scopeText.length * 6.8 + 34),
                          Math.floor(width * 0.34)
                      )
                    : 0,
                titleW = Math.max(
                    60,
                    innerW -
                        28 -
                        (inlineAction ? openBtnW + 10 : 0) -
                        (showBadge ? badgeW + 10 : 0)
                ),
                tiles = [
                    ['code', 'code', tr('Code'), row.identity, true],
                    [
                        'processes',
                        'checklist',
                        tr('Processes'),
                        tr('{count} processes', { count: row.processCount }),
                        false
                    ],
                    [
                        'scope',
                        row.shared ? 'layers' : 'folder-open',
                        tr('Data location'),
                        scopeText,
                        false
                    ]
                ],
                tileCols =
                    innerW >= 580 ? 3 : innerW >= 380 ? 2 : 1,
                tileGap = 10,
                tileW =
                    (innerW - (tileCols - 1) * tileGap) /
                    Math.max(1, tileCols),
                tileRows = Math.ceil(tiles.length / Math.max(1, tileCols)),
                descText = String(row.description || '').trim(),
                descH = descText
                    ? Math.max(
                          24,
                          Math.ceil(
                              descText.length /
                                  Math.max(18, Math.floor((innerW - 28) / 7))
                          ) * 20
                      )
                    : 0,
                tilesTop = 54,
                tilesBottom =
                    tilesTop +
                    tileRows * 52 +
                    Math.max(0, tileRows - 1) * 8,
                descTop = descH ? tilesBottom + 10 : tilesBottom,
                bottomBtnTop = !inlineAction
                    ? (descH ? descTop + descH + 10 : tilesBottom + 10)
                    : 0,
                cardH =
                    (!inlineAction
                        ? bottomBtnTop + 38
                        : descH
                          ? descTop + descH
                          : tilesBottom) + 14,
                summaryText =
                    (descText ? descText + '\n' : '') +
                    tr('{count} processes', { count: row.processCount }) +
                    (row.shared ? ' · ' + tr('Shared · read-only') : ''),
                cardChildren = [
                    node(
                        'Icon',
                        'typeWorkflowIcon_' + row.identity,
                        rect(cardPad, 15, 18, 18),
                        {
                            icon: 'workflow',
                            color: row.color || 'action'
                        }
                    ),
                    label(
                        'typeWorkflowTitle_' + row.identity,
                        rect(cardPad + 26, 11, titleW, 26),
                        row.label,
                        {
                            fontRole: 'section',
                            weight: 600
                        }
                    ),
                    node(
                        'Box',
                        'typeWorkflowDivider_' + row.identity,
                        rect(cardPad, 45, innerW, 1),
                        {
                            background: 'outlineVariant'
                        }
                    )
                ];
            if (showBadge) {
                const badgeX =
                    width -
                    cardPad -
                    (inlineAction ? openBtnW + 10 : 0) -
                    badgeW;
                cardChildren.push(
                    node(
                        'Box',
                        'typeWorkflowBadge_' + row.identity,
                        rect(badgeX, 10, badgeW, 26),
                        {
                            background: 'surfaceContainerHigh',
                            border: 'outlineVariant',
                            radius: 13,
                            children: [
                                node(
                                    'Icon',
                                    'typeWorkflowBadgeIcon_' + row.identity,
                                    rect(10, 5, 15, 15),
                                    {
                                        icon: row.shared
                                            ? 'layers'
                                            : 'folder-open',
                                        color: row.color || 'action'
                                    }
                                ),
                                label(
                                    'typeWorkflowBadgeText_' + row.identity,
                                    rect(30, 3, Math.max(0, badgeW - 38), 20),
                                    scopeText,
                                    {
                                        fontRole: 'secondary',
                                        weight: 600
                                    }
                                )
                            ]
                        }
                    )
                );
            }
            tiles.forEach(([tKey, tIcon, tLabel, tVal, mono], tIdx) => {
                const r = Math.floor(tIdx / tileCols),
                    c = tIdx % tileCols,
                    tx = cardPad + c * (tileW + tileGap),
                    ty = tilesTop + r * 60;
                cardChildren.push(
                    node(
                        'Box',
                        'typeWorkflowTile_' + row.identity + '_' + tKey,
                        rect(tx, ty, tileW, 52),
                        {
                            background: 'surfaceContainerHigh',
                            border: 'outlineVariant',
                            radius: 8,
                            children: [
                                node(
                                    'Icon',
                                    'typeWorkflowTileIcon_' +
                                        row.identity +
                                        '_' +
                                        tKey,
                                    rect(10, 8, 14, 14),
                                    {
                                        icon: tIcon,
                                        color: row.color || 'action'
                                    }
                                ),
                                label(
                                    'typeWorkflowTileLabel_' +
                                        row.identity +
                                        '_' +
                                        tKey,
                                    rect(28, 5, Math.max(0, tileW - 36), 18),
                                    tLabel,
                                    muted
                                ),
                                label(
                                    'typeWorkflowTileValue_' +
                                        row.identity +
                                        '_' +
                                        tKey,
                                    rect(10, 25, Math.max(0, tileW - 20), 22),
                                    tVal,
                                    {
                                        weight: 600,
                                        monospace: !!mono
                                    }
                                )
                            ]
                        }
                    )
                );
            });
            if (descH) {
                cardChildren.push(
                    node(
                        'Icon',
                        'typeWorkflowDescIcon_' + row.identity,
                        rect(cardPad, descTop + 3, 15, 15),
                        {
                            icon: 'description',
                            color: 'muted'
                        }
                    ),
                    label(
                        'typeWorkflowDescription_' + row.identity,
                        rect(
                            cardPad + 24,
                            descTop,
                            Math.max(0, innerW - 24),
                            descH
                        ),
                        descText,
                        Object.assign({ wrap: true }, muted)
                    )
                );
            }
            cardChildren.push(
                button(
                    'adminSearchTypeWorkflow_' + row.identity,
                    inlineAction
                        ? rect(width - cardPad - openBtnW, 7, openBtnW, 32)
                        : rect(cardPad, bottomBtnTop, innerW, 38),
                    tr('Open workflow'),
                    'workflow',
                    {
                        type: 'workflow',
                        identity: row.identity
                    },
                    canOpenWorkflow
                )
            );
            nodes.push(
                node(
                    'Box',
                    'typeWorkflowCard_' + row.identity,
                    rect(0, y, width, cardH),
                    {
                        text: summaryText,
                        background: 'surfaceContainer',
                        border: 'outlineVariant',
                        radius: 10,
                        children: cardChildren
                    }
                )
            );
            y += cardH + 10;
        }
        if (!(meta.pipelines || []).length) {
            const emptyPad = width < 380 ? 10 : 14;
            nodes.push(
                node('Box', 'typeWorkflowsEmptyCard', rect(0, y, width, 56), {
                    background: 'surfaceContainer',
                    border: 'outlineVariant',
                    radius: 10,
                    children: [
                        node(
                            'Icon',
                            'typeWorkflowsEmptyIcon',
                            rect(emptyPad, 19, 18, 18),
                            {
                                icon: 'workflow',
                                color: 'muted'
                            }
                        ),
                        label(
                            'typeWorkflowsEmpty',
                            rect(
                                emptyPad + 28,
                                16,
                                Math.max(0, width - emptyPad * 2 - 28),
                                24
                            ),
                            tr('No workflows linked to this Search Type.'),
                            Object.assign({ wrap: true }, muted)
                        )
                    ]
                })
            );
            y += 68;
        }
        const createPad = width < 380 ? 10 : 14,
            inlineCreate = width >= 520,
            createBtnW = inlineCreate
                ? Math.min(
                      Math.max(168, tr('Create workflow').length * 7.5 + 48),
                      230
                  )
                : Math.max(1, width - createPad * 2),
            createCardH = inlineCreate ? 56 : 92,
            createChildren = [
                node(
                    'Icon',
                    'typeCreateWorkflowIcon',
                    rect(createPad, 19, 18, 18),
                    {
                        icon: 'add',
                        color: 'action'
                    }
                ),
                label(
                    'typeCreateWorkflowHint',
                    rect(
                        createPad + 26,
                        inlineCreate ? 16 : 12,
                        Math.max(
                            0,
                            width -
                                createPad * 2 -
                                26 -
                                (inlineCreate ? createBtnW + 12 : 0)
                        ),
                        24
                    ),
                    tr('New workflow'),
                    {
                        weight: 600
                    }
                ),
                button(
                    'adminCreateTypeWorkflow',
                    inlineCreate
                        ? rect(
                              width - createPad - createBtnW,
                              10,
                              createBtnW,
                              36
                          )
                        : rect(createPad, 44, createBtnW, 38),
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
            ];
        nodes.push(
            node(
                'Box',
                'typeCreateWorkflowCard',
                rect(0, y, width, createCardH),
                {
                    background: 'surfaceContainer',
                    border: 'outlineVariant',
                    radius: 10,
                    children: createChildren
                }
            )
        );
        y += createCardH + 10;
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
                        normalColor: 'transparent',
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
        narrow = width < 420,
        cardPad = width < 380 ? 10 : 14,
        cardH = narrow ? 180 : 128,
        info = record.info || {},
        rawType = String(info.data_type || '')
            .toLowerCase()
            .split('(')[0]
            .trim(),
        typeIndex = {
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
        }[rawType],
        fieldTypeDef =
            fieldTypes[rawType.indexOf('timestamp') === 0 ? 5 : typeIndex],
        typeSummary = fieldTypeDef
            ? tr(fieldTypeDef.label) + ' · ' + (info.data_type || '')
            : info.data_type || '—',
        constraints = [
            info.character_maximum_length
                ? tr('Up to {count} characters', {
                      count: info.character_maximum_length
                  })
                : '',
            info.is_nullable === 'NO' || info.is_nullable === false
                ? tr('Cannot be empty in the database')
                : '',
            fieldTypeDef
                ? tr('Example value: {value}', {
                      value: tr(fieldTypeDef.example)
                  })
                : ''
        ]
            .filter(Boolean)
            .join('  ·  '),
        fullText = marked
            ? tr(
                  'Marked for deletion. The column and its data will be deleted when you save.'
              )
            : fieldDescription(info, language) +
              (reason ? '\n' + tr(reason) : ''),
        btnW = 152,
        showTypeBadge = !narrow && width >= 540,
        badgeText = String(info.data_type || 'text'),
        badgeW = showTypeBadge
            ? Math.min(Math.max(84, badgeText.length * 7 + 30), 170)
            : 0,
        nameAvailW = Math.max(
            60,
            width -
                cardPad * 2 -
                26 -
                (narrow ? 0 : btnW + 10) -
                (showTypeBadge ? badgeW + 10 : 0)
        ),
        fieldIcon = marked
            ? 'delete'
            : reason
              ? 'lock'
              : rawType.indexOf('timestamp') === 0
                ? 'calendar'
                : typeIndex === 2 || typeIndex === 3
                  ? 'tag'
                  : typeIndex === 4
                    ? 'check'
                    : 'description',
        cardChildren = [
            node(
                'Icon',
                'typeExistingIcon_' + record.name,
                rect(cardPad, 13, 18, 18),
                {
                    icon: fieldIcon,
                    color: marked ? 'error' : reason ? 'muted' : 'action'
                }
            ),
            label(
                'typeExistingName_' + record.name,
                rect(cardPad + 26, 9, nameAvailW, 24),
                record.name,
                {
                    weight: 600,
                    monospace: true,
                    strike: marked
                }
            ),
            node(
                'Box',
                'typeExistingDivider_' + record.name,
                rect(cardPad, 43, Math.max(1, width - cardPad * 2), 1),
                {
                    background: 'outlineVariant'
                }
            )
        ];
    if (showTypeBadge) {
        const bx = width - cardPad - btnW - 10 - badgeW;
        cardChildren.push(
            node(
                'Box',
                'typeExistingBadge_' + record.name,
                rect(bx, 9, badgeW, 26),
                {
                    background: 'surfaceContainerHigh',
                    border: 'outlineVariant',
                    radius: 13,
                    children: [
                        node(
                            'Icon',
                            'typeExistingBadgeIcon_' + record.name,
                            rect(9, 6, 14, 14),
                            {
                                icon: 'code',
                                color: 'action'
                            }
                        ),
                        label(
                            'typeExistingBadgeText_' + record.name,
                            rect(26, 3, Math.max(0, badgeW - 34), 20),
                            badgeText,
                            {
                                fontRole: 'secondary',
                                weight: 600,
                                monospace: true
                            }
                        )
                    ]
                }
            )
        );
    }
    if (marked) {
        cardChildren.push(
            node(
                'Icon',
                'typeExistingMarkedIcon_' + record.name,
                rect(cardPad, 56, 16, 16),
                {
                    icon: 'warning',
                    color: 'error'
                }
            ),
            label(
                'typeExistingMarkedText_' + record.name,
                rect(
                    cardPad + 24,
                    52,
                    Math.max(0, width - cardPad * 2 - 24),
                    56
                ),
                tr(
                    'Marked for deletion. The column and its data will be deleted when you save.'
                ),
                {
                    wrap: true,
                    color: 'error',
                    weight: 600
                }
            )
        );
    } else {
        cardChildren.push(
            node(
                'Icon',
                'typeExistingTypeRowIcon_' + record.name,
                rect(cardPad, 54, 15, 15),
                {
                    icon: 'storage',
                    color: 'action'
                }
            ),
            label(
                'typeExistingTypeRowText_' + record.name,
                rect(
                    cardPad + 22,
                    50,
                    Math.max(0, width - cardPad * 2 - 22),
                    22
                ),
                typeSummary + (constraints ? '  ·  ' + constraints : ''),
                Object.assign({ wrap: true }, muted)
            )
        );
        if (reason) {
            cardChildren.push(
                node(
                    'Icon',
                    'typeExistingReasonIcon_' + record.name,
                    rect(cardPad, 82, 15, 15),
                    {
                        icon: 'lock',
                        color: 'warning'
                    }
                ),
                label(
                    'typeExistingReasonText_' + record.name,
                    rect(
                        cardPad + 22,
                        78,
                        Math.max(0, width - cardPad * 2 - 22),
                        40
                    ),
                    tr(reason),
                    Object.assign({ wrap: true }, muted)
                )
            );
        }
    }
    cardChildren.push(
        button(
            'adminDeleteColumn_' + record.name,
            narrow
                ? rect(cardPad, cardH - 46, Math.max(1, width - cardPad * 2), 36)
                : rect(width - cardPad - btnW, 6, btnW, 32),
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
    );
    return {
        nodes: [
            node(
                'Box',
                'adminExistingField_' + record.name,
                rect(0, 0, width, cardH),
                {
                    text: fullText,
                    background: 'surfaceContainer',
                    border: 'outlineVariant',
                    radius: 10,
                    children: cardChildren
                }
            )
        ]
    };
}

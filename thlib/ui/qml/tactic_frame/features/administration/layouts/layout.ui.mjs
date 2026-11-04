import { button } from '../../../core/frame.mjs';
import { node } from '../../../core/frame.mjs';
import {
    rect,
    label,
    muted,
    notices,
    toolbar as documentToolbar,
    policy,
    sectionSelector
} from '../admin.document.mjs';
import { sections as form } from '../../../controls/forms/sections.ui.mjs';
import { translate } from '../../../core/strings.mjs';
import * as Document from './layout.document.mjs';
import { spacingField } from './canvas.mjs';
import { pending, reference } from './layout.state.mjs';
import * as Samples from './layout.samples.mjs';
import * as Catalog from './layout.catalog.mjs';
export const labels = {
    group: 'Group',
    view: 'Reusable view',
    text: 'Text',
    field: 'Field',
    title: 'Title',
    description: 'Description',
    image: 'Image',
    link: 'Link',
    button: 'Button',
    metadata: 'Metadata',
    'snapshot-details': 'Snapshot details',
    'snapshot-size': 'File size',
    'snapshot-summary': 'Snapshot summary',
    'branch-summary': 'Branch summary',
    'file-offline': 'File Offline',
    'item-menu': 'Item actions',
    'quick-actions': 'Snapshot actions',
    knowledge: 'Knowledge Base',
    relations: 'Relationship actions',
    all: 'All items',
    main: 'Main object',
    children: 'Child object',
    process: 'Process',
    relation: 'Relation',
    versions: 'Versions',
    snapshot: 'Snapshot',
    file: 'File',
    inspect: 'Object details',
    operate: 'Object actions',
    preview: 'File preview',
    tasks: 'Tasks',
    notes: 'Notes',
    upload: 'Add files',
    create: 'Create related object',
    cover: 'Fill the image area',
    contain: 'Show the whole image',
    stretch: 'Fill the cell',
    start: 'Start',
    center: 'Center',
    end: 'End',
    normal: 'Normal',
    muted: 'Muted',
    strong: 'Strong'
};
export function choices(values, language) {
    return values.map((value) => ({
        value,
        label: translate(labels[value] || value || 'None', language)
    }));
}
export function model(raw, ui, language = 'en', screenWidth = 1000) {
    let layout = {
            elements: [],
            columns: 12,
            flow: 'grid',
            collection: 'grid',
            tracks: '',
            card_width: 280
        },
        layoutError = raw.parseError ? 'Invalid configuration XML' : '';
    if (!layoutError && raw.tree)
        try {
            layout = Document.describe(raw.tree, raw.view);
        } catch (error) {
            layoutError = String(error.message || error);
        }
    if (
        !layoutError &&
        (!Number.isInteger(layout.columns) ||
            layout.columns < 1 ||
            layout.columns > 12 ||
            !Number.isFinite(layout.card_width) ||
            layout.elements.some((row) =>
                [
                    'row',
                    'column',
                    'span',
                    'rows',
                    'columns',
                    'height',
                    'layer'
                ].some((key) => !Number.isFinite(row[key]))
            ))
    )
        layoutError = 'Invalid layout size';
    if (!layoutError) {
        const names = [];
        for (const item of layout.elements) {
            if (!item.name || names.indexOf(item.name) >= 0) {
                layoutError = 'Invalid or duplicate layout element name';
                break;
            }
            names.push(item.name);
        }
        if (layout.elements.length > 128)
            layoutError = 'Layout supports at most 128 elements';
        for (const item of layout.elements) {
            if (item.options.colors) {
                try {
                    const colors = JSON.parse(item.options.colors);
                    if (
                        !colors ||
                        typeof colors !== 'object' ||
                        Array.isArray(colors)
                    )
                        throw Error('Invalid field value colors');
                } catch (error) {
                    layoutError = 'Invalid field value colors';
                    break;
                }
            }
            const seen = [item.name];
            let parent = item.parent;
            while (parent) {
                if (seen.indexOf(parent) >= 0 || seen.length >= 8) {
                    layoutError = 'Invalid or cyclic layout container';
                    break;
                }
                seen.push(parent);
                const container = layout.elements.find(
                    (row) => row.name === parent
                );
                parent = container ? container.parent : '';
            }
        }
    }
    const record = ((raw.sampleItems || [])[0] || {}).record || {},
        bindings = [''].concat(
            Object.keys((raw.preview || {}).columns || record)
                .filter((key) => key.indexOf('__') !== 0)
                .map((key) => 'record.' + key),
            [
                'node.title',
                'node.subtitle',
                'node.preview.image',
                'node.note_count',
                'node.task_count',
                'node.branch.count',
                'node.snapshot_display.version',
                'node.snapshot_display.author'
            ]
        );
    const types = (raw.searchTypes || [])
        .slice()
        .sort((a, b) =>
            a.label.toLowerCase() < b.label.toLowerCase()
                ? -1
                : a.label.toLowerCase() > b.label.toLowerCase()
                  ? 1
                  : 0
        );
    return Object.assign({}, raw, {
        samplePreview:
            !raw.busy && !raw.error && !raw.sampleError && !raw.previewError
                ? Samples.fallback(
                      raw.liveInterface?.table?.item_layout,
                      raw.sampleItems,
                      raw.searchType,
                      ui.selected,
                      language,
                      screenWidth
                  )
                : null,
        ready: !!raw.configuration,
        canLoad: !!raw.canLoad,
        canWrite: !!raw.canWrite,
        searchTypes: types,
        bindings,
        dirty: !!raw.dirty || pending(ui),
        pendingText: pending(ui),
        layout,
        layoutError,
        document: {},
        identity: raw.view || '',
        saveAllowed:
            !!raw.checked &&
            raw.checked === raw.xml &&
            !layoutError &&
            !pending(ui),
        error: raw.error || ui.error,
        message: raw.message || ''
    });
}
export function toolbar(model, ui, width, language, embedded = false) {
    const tr = (text) => translate(text, language),
        result = documentToolbar(model, ui, width, language),
        edit = policy(model).editable && !ui.confirmation;
    result.nodes = result.nodes.filter(
        (row) => row.id !== 'adminDocumentStatus'
    );
    result.nodes.push(
        button(
            'layoutCheck',
            rect(46, 0, 38, 38),
            tr('Check and preview'),
            'check',
            {
                type: 'check'
            },
            edit && !model.layoutError && !pending(ui),
            {
                iconOnly: true
            }
        ),
        button(
            'layoutHelp',
            rect(90, 0, 38, 38),
            tr('Layout guide'),
            'help',
            {
                type: 'help'
            },
            true,
            {
                iconOnly: true
            }
        ),
        button(
            'layoutOpenView',
            rect(embedded ? 90 : 134, 0, 38, 38),
            tr('Open saved view'),
            'open-in-new',
            {
                type: 'openView'
            },
            edit &&
                !model.dirty &&
                !!(
                    model.configuration &&
                    model.configuration.resolved &&
                    model.configuration.resolved.configured
                ),
            {
                iconOnly: true
            }
        )
    );
    if (embedded)
        result.nodes = result.nodes.filter((row) => row.id !== 'layoutHelp');
    if (ui.page === 'xml')
        result.nodes.push(
            button(
                'layoutFormatXml',
                rect(embedded ? 134 : 178, 0, 38, 38),
                tr('Format XML'),
                'code',
                { type: 'formatXml' },
                edit && !model.layoutError && !pending(ui),
                { iconOnly: true }
            )
        );
    return result;
}
export function models(model, language = 'en') {
    return {
        layoutElements: model.layout.elements,
        layoutViews: Catalog.views(model, language)
    };
}
export function row(list, record, model, ui, language) {
    if (list.source === 'layoutViews') return Catalog.row(list, record, model);
    const width = list.width - 16,
        tr = (text) => translate(text, language),
        id = 'layoutElement_' + record.name;
    return {
        nodes: [
            node('Action', id, rect(0, 0, width, 46), {
                text: record.title || record.name,
                selected: ui.selected === record.name,
                normalColor: 'transparent',
                selectedColor: 'contentSelection',
                dragValue:
                    policy(model).editable && !pending(ui) ? record.name : null,
                dragStartAction: {
                    type: 'select',
                    name: record.name
                },
                children: [
                    label(
                        id + 'Title',
                        rect(
                            record.parent ? 22 : 10,
                            0,
                            width - (record.parent ? 32 : 20),
                            26
                        ),
                        (record.parent ? '↳ ' : '') +
                            (record.title || record.name),
                        {
                            weight: 600
                        }
                    ),
                    label(
                        id + 'Kind',
                        rect(10, 26, width - 20, 18),
                        tr(labels[record.kind] || record.kind),
                        muted
                    )
                ],
                action: {
                    type: 'select',
                    name: record.name
                }
            })
        ]
    };
}
function propertyFields(model, ui, language, width) {
    const tr = (text) => translate(text, language),
        item = model.layout.elements.find((row) => row.name === ui.selected);
    if (!item) return [];
    const edit = policy(model).editable,
        enabled = edit && !pending(ui),
        fields = [];
    function text(field, title, value, description, name) {
        const key = item.name + ':' + field,
            buffered = field === 'title' || field === 'when';
        return {
            id: 'layoutProperty_' + field.replace(/:/g, '_'),
            title,
            description,
            props: {
                text:
                    buffered &&
                    Object.prototype.hasOwnProperty.call(ui.text, key)
                        ? ui.text[key]
                        : value === undefined
                          ? ''
                          : String(value),
                enabled: buffered
                    ? edit &&
                      Object.keys(ui.text).every((value) => value === key)
                    : enabled,
                action: buffered
                    ? {
                          type: 'text',
                          field,
                          key,
                          name
                      }
                    : {
                          type: 'change',
                          field,
                          name
                      },
                commitAction: buffered
                    ? {
                          type: 'finishText',
                          key
                      }
                    : null
            }
        };
    }
    function choice(field, title, value, options, description, name) {
        return {
            id: 'layoutProperty_' + field.replace(/:/g, '_'),
            title,
            description,
            kind: 'Choice',
            options,
            props: {
                value,
                enabled,
                action: {
                    type: 'change',
                    field,
                    name
                }
            }
        };
    }
    function integer(field, title, value, description) {
        const key = item.name + ':' + field;
        return {
            id: 'layoutProperty_' + field,
            title,
            description,
            props: {
                text: Object.prototype.hasOwnProperty.call(ui.text, key)
                    ? ui.text[key]
                    : String(value),
                enabled: edit,
                action: {
                    type: 'buffer',
                    key
                },
                commitAction: {
                    type: 'number',
                    key,
                    field
                },
                inputMode: 'numeric'
            }
        };
    }
    const bindings = [
        {
            value: '',
            label: tr('Fixed text')
        }
    ].concat(
        (model.bindings || []).filter(Boolean).map((value) => ({
            value,
            label: tr(
                {
                    'node.title': 'Object title',
                    'node.subtitle': 'Object description',
                    'node.preview.image': 'Object preview',
                    'node.note_count': 'Number of notes',
                    'node.task_count': 'Number of tasks',
                    'node.branch.count': 'Number of children',
                    'node.snapshot_display.version': 'Snapshot version',
                    'node.snapshot_display.author': 'Snapshot author'
                }[value] || value.replace(/^record\./, '')
            )
        }))
    );
    fields.push(
        {
            kind: 'Heading',
            id: 'layoutElementHeading',
            title: item.title || item.name
        },
        text('title', 'Label', item.title),
        choice('kind', 'Widget', item.kind, choices(Document.widgets, language))
    );
    if (
        [
            'text',
            'field',
            'title',
            'description',
            'image',
            'link',
            'button'
        ].indexOf(item.kind) >= 0
    ) {
        fields.push(
            {
                kind: 'Heading',
                id: 'layoutContentHeading',
                title: 'Content'
            },
            choice(
                'option:bind',
                'Data binding',
                item.options.bind || '',
                bindings,
                'Choose which object value to display'
            )
        );
        if (!item.options.bind || item.kind === 'field')
            fields.push(
                text(
                    'option:text',
                    item.kind === 'image'
                        ? 'Image URL'
                        : item.kind === 'field'
                          ? 'Label'
                          : 'Text',
                    item.options.text || ''
                )
            );
        if (item.kind === 'image') {
            if (item.role !== 'preview')
                fields.push(integer('height', 'Image height', item.height));
            fields.push(
                choice(
                    'option:fit',
                    'Image fit',
                    item.options.fit || 'cover',
                    choices(['cover', 'contain'], language)
                )
            );
        }
        if (item.kind === 'link' || item.kind === 'button')
            fields.push(
                text('option:href', 'Link URL', item.options.href || '')
            );
        if (item.kind === 'button')
            fields.push(
                choice(
                    'option:action',
                    'Action',
                    item.options.action || '',
                    choices([''].concat(Document.actions), language)
                ),
                choice(
                    'option:badge',
                    'Badge binding',
                    item.options.badge || '',
                    bindings.map((row) =>
                        row.value
                            ? row
                            : {
                                  value: '',
                                  label: tr('No badge')
                              }
                    ),
                    'Choose a number to show on the button'
                ),
                text('option:icon', 'Icon', item.options.icon || '')
            );
    }
    const palette = [
        ['', 'Auto'],
        ['primaryText', 'Text'],
        ['secondaryText', 'Secondary'],
        ['contentAccent', 'Accent'],
        ['green', 'Green'],
        ['yellow', 'Yellow'],
        ['red', 'Red'],
        ['cyan', 'Cyan'],
        ['violet', 'Violet']
    ];
    const colorOptions = (value, entries = palette) =>
        entries
            .map(([value, label]) => ({ value, label: tr(label) }))
            .concat(value?.startsWith('#') ? [{ value, label: value }] : []);
    if (['field', 'text', 'title', 'description'].includes(item.kind)) {
        fields.push(
            choice(
                'option:color',
                'Text / icon color',
                item.options.color || '',
                colorOptions(item.options.color)
            )
        );
    }
    if (item.kind === 'field') {
        fields.push(
            choice(
                'option:format',
                'Field display',
                item.options.format || 'plain',
                [
                    ['plain', 'Plain text'],
                    ['date', 'Date'],
                    ['datetime', 'Date and time'],
                    ['badge', 'Status badge'],
                    ['progress', 'Progress']
                ].map(([value, label]) => ({ value, label: tr(label) }))
            )
        );
        const colors = item.options.colors
                ? JSON.parse(item.options.colors)
                : {},
            values = [
                ...new Set(
                    Object.keys(colors).concat(
                        (model.sampleItems || [])
                            .map((sample) =>
                                String(
                                    Document.binding(item.options.bind, sample)
                                )
                            )
                            .filter(Boolean)
                    )
                )
            ].slice(0, 32);
        for (const value of values)
            fields.push(
                choice(
                    'valueColor:' + value,
                    'Value color',
                    colors[value] || '',
                    colorOptions(colors[value]),
                    '«' + value + '»'
                )
            );
    }
    if (item.kind === 'group') {
        const surfaces = [
                ['', 'None'],
                ['panel', 'Panel'],
                ['workspace', 'Workspace'],
                ['surfaceContainerLow', 'Surface']
            ],
            borders = [
                ['', 'None'],
                ['outlineVariant', 'Outline'],
                ['contentAccent', 'Accent']
            ];
        fields.push(
            choice(
                'option:fill',
                'Fill color',
                item.options.fill || '',
                colorOptions(item.options.fill, surfaces)
            ),
            choice(
                'option:stroke',
                'Stroke color',
                item.options.stroke || '',
                colorOptions(item.options.stroke, borders)
            ),
            text('option:radius', 'Corner radius', item.options.radius || '0')
        );
    }
    if (item.kind === 'view') {
        const field = text(
            'option:view',
            'Reusable view',
            item.options.view || ''
        );
        field.trailingAction = {
            title: 'Edit nested item layout',
            icon: 'open-in-new',
            enabled: !model.busy && !model.uncertain && !!reference(model, ui),
            action: { type: 'openLayout' }
        };
        fields.push(field);
    }
    const parentOptions = [
            {
                value: '',
                label: tr('View root')
            }
        ].concat(
            model.layout.elements
                .filter((row) => row.kind === 'group' && row.name !== item.name)
                .map((row) => ({
                    value: row.name,
                    label: row.title || row.name
                }))
        ),
        parent = model.layout.elements.find((row) => row.name === item.parent),
        grid = (parent ? parent.flow : model.layout.flow) === 'grid';
    fields.push(
        {
            kind: 'Heading',
            id: 'layoutPositionHeading',
            title: 'Position'
        },
        choice('parent', 'Container', item.parent, parentOptions)
    );
    if (
        grid &&
        model.layout.flow !== 'contents' &&
        model.layout.collection !== 'table'
    ) {
        for (const name of ['padding', 'margin'])
            fields.push(
                spacingField(
                    'layout' + name,
                    tr(name === 'padding' ? 'Padding' : 'Margin'),
                    item[name] || [0, 0, 0, 0],
                    ui.text,
                    { type: 'spacing', field: name },
                    language,
                    edit,
                    width - 48
                )
            );
    }
    if (grid)
        for (const key of ['row', 'column', 'span', 'rows'])
            fields.push(
                integer(
                    key,
                    {
                        row: 'Row',
                        column: 'Column',
                        span: 'Column span',
                        rows: 'Row span'
                    }[key],
                    item[key]
                )
            );
    else
        fields.push({
            kind: 'Heading',
            id: 'layoutSharedPositionHelp',
            title: 'Shared item layout',
            description:
                'Positions follow shared item styles. Choose Grid in the parent container for placement by rows and columns.'
        });
    fields.push(
        integer(
            'layer',
            'Layer',
            item.layer,
            'Higher layers appear in front. Use the same grid cells to place text or buttons over an image.'
        ),
        {
            kind: 'Heading',
            id: 'layoutAdvancedHeading',
            title: 'More element settings'
        },
        {
            kind: 'Switch',
            id: 'layoutPropertyVisible',
            title: 'Visible',
            props: {
                checked: !item.hidden,
                enabled,
                action: {
                    type: 'change',
                    field: 'hidden',
                    invert: true
                }
            }
        },
        choice(
            'variant',
            'Item variant',
            item.variant,
            choices(Document.variants, language)
        ),
        choice('search_type', 'Search Type', item.search_type || '', [
            { value: '', label: tr('All') },
            ...model.searchTypes
        ]),
        text('option:bind', 'Custom data binding', item.options.bind || '')
    );
    // The same value has two captions, so controls keep distinct stable identities.
    fields[fields.length - 1].id = 'layoutCustomBinding';
    if (item.kind === 'link' || item.kind === 'button')
        fields.push(
            choice(
                'option:href_bind',
                'Link URL binding',
                item.options.href_bind || '',
                bindings
            )
        );
    fields.push(
        choice(
            'role',
            'Style role',
            item.role,
            Object.keys(Document.roles).map((value) => ({
                value,
                label: tr(Document.roles[value])
            }))
        )
    );
    if (item.kind === 'group')
        fields.push(
            choice('flow', 'Child layout', item.flow, [
                {
                    value: 'grid',
                    label: tr('Grid')
                },
                {
                    value: 'contents',
                    label: tr('Shared item layout')
                }
            ]),
            integer('columns', 'Grid columns', item.columns)
        );
    fields.push(
        choice(
            'tag',
            'Markup tag',
            item.tag,
            ['div', 'span', 'strong', 'small'].map((value) => ({
                value,
                label: value
            }))
        ),
        text(
            'when',
            'Display conditions',
            item.when.join(' '),
            'Limit the element to desktop, mobile or particular items'
        ),
        choice(
            'align',
            'Alignment',
            item.align,
            choices(['stretch', 'start', 'center', 'end'], language)
        ),
        choice(
            'tone',
            'Text style',
            item.tone,
            choices(['normal', 'muted', 'strong'], language)
        )
    );
    return fields;
}
export function describe(model, ui, width, height, language) {
    if (width <= 0 || height <= 0)
        return {
            nodes: []
        };
    if (height < 400)
        return {
            nodes: [
                node('Scroll', 'layoutPageScroll', rect(0, 0, width, height), {
                    contentHeight: 640,
                    scrollbarId: 'layoutPageScrollBar',
                    children: describe(model, ui, width - 16, 640, language)
                        .nodes
                })
            ]
        };
    const tr = (text) => translate(text, language),
        edit = policy(model).editable && !ui.confirmation,
        noticeModel = Object.assign({}, model);
    if (ui.confirmation === 'remove')
        noticeModel.confirmationText = 'Remove this element and its children?';
    if (ui.confirmation === 'context')
        noticeModel.confirmationText =
            'Discard changes to the current view and continue?';
    const notice = notices(
            noticeModel,
            ui,
            width,
            language,
            undefined,
            ui.confirmation === 'remove' ? 'Remove element' : undefined
        ),
        nodes = notice.nodes;
    let y = notice.top;
    const context = Catalog.context(model, ui, width, language);
    nodes.push(
        node(
            'Box',
            'layoutDocumentContext',
            rect(0, y, width, context.height),
            { children: context.nodes }
        )
    );
    y += context.height;
    nodes.push(
        sectionSelector(
            'layoutPages',
            [
                {
                    value: 'design',
                    label: tr('Design')
                },
                {
                    value: 'configuration',
                    label: tr('Configuration')
                },
                {
                    value: 'xml',
                    label: tr('Source XML')
                },
                {
                    value: 'changes',
                    label: tr('Configuration changes')
                },
                {
                    value: 'resolved',
                    label: tr('Resolved preview')
                }
            ],
            ui.page,
            rect(0, y, width, 38),
            !model.busy,
            'page'
        )
    );
    y += 46;
    if (ui.page === 'design' && width >= 500) {
        nodes.push(
            label(
                'layoutSelectionHint',
                rect(0, y, width, 24),
                tr('Click to select. Alt-click for underlying layers.'),
                Object.assign({}, muted, { fontRole: 'caption' })
            )
        );
        y += 32;
    }
    if (model.sampleError) {
        nodes.push(
            node('Area', 'layoutSampleError', rect(0, y, width, 58), {
                label: tr('Preview data could not be loaded'),
                text:
                    tr('Preview data could not be loaded') +
                    ': ' +
                    model.sampleError,
                readOnly: true,
                notice: true
            })
        );
        y += 66;
    }
    const h = Math.max(1, height - y),
        layout = model.layout,
        selected = layout.elements.find((row) => row.name === ui.selected);
    if (ui.page === 'xml') {
        nodes.push(
            node('Code', 'layoutXmlSource', rect(0, y, width, h), {
                text: model.xml || '',
                language,
                syntax: 'xml',
                readOnly: !edit,
                service: 'sourceEditor',
                bufferKey: [
                    model.project,
                    model.searchType,
                    model.view,
                    model.source
                ].join(':'),
                action: {
                    type: 'xml'
                },
                helpAction: {
                    type: 'help'
                }
            })
        );
        return {
            nodes
        };
    }
    if (ui.page === 'changes') {
        nodes.push(
            node('Area', 'layoutChanges', rect(0, y, width, h), {
                text:
                    model.diff ||
                    tr('Check and preview the draft before saving.'),
                label: tr('Configuration changes'),
                monospace: true,
                readOnly: true
            })
        );
        return {
            nodes
        };
    }
    if (ui.page === 'configuration') {
        const sourceOptions = (model.configuration?.sources || [])
            .map((row) => ({
                value: row.id,
                label:
                    String(row.id) +
                    ' · ' +
                    tr('Priority') +
                    ' ' +
                    (row.priority ?? '')
            }))
            .concat([{ value: '', label: tr('New override') }]);
        const fields = [
            {
                kind: 'Choice',
                id: 'layoutSource',
                title: 'Configuration source',
                options: sourceOptions,
                props: {
                    value: model.source,
                    enabled: !model.busy && !model.dirty && !model.uncertain,
                    action: { type: 'source' }
                }
            }
        ];
        if (!model.layoutError) {
            const integer = (key, title) => ({
                id: 'layoutRoot_' + key,
                title,
                props: {
                    text: Object.prototype.hasOwnProperty.call(
                        ui.text,
                        'root:' + key
                    )
                        ? ui.text['root:' + key]
                        : String(layout[key]),
                    enabled: edit,
                    action: {
                        type: 'buffer',
                        key: 'root:' + key
                    },
                    commitAction: {
                        type: 'number',
                        key: 'root:' + key,
                        name: '',
                        field: key
                    },
                    inputMode: 'numeric'
                }
            });
            fields.push(
                {
                    kind: 'Heading',
                    id: 'layoutCollectionHeading',
                    title: 'Collection layout'
                },
                {
                    kind: 'Choice',
                    id: 'layoutCollection',
                    title: 'Collection layout',
                    options: [
                        {
                            value: 'grid',
                            label: tr('Cards')
                        },
                        {
                            value: 'list',
                            label: tr('List')
                        },
                        {
                            value: 'tree',
                            label: tr('Continuous Tree')
                        },
                        {
                            value: 'table',
                            label: tr('Table View')
                        }
                    ],
                    props: {
                        value: layout.collection,
                        enabled: edit && !pending(ui),
                        action: {
                            type: 'change',
                            name: '',
                            field: 'collection'
                        }
                    }
                }
            );
            if (layout.collection === 'grid')
                fields.push(integer('card_width', 'Card width'));
            fields.push(
                {
                    kind: 'Choice',
                    id: 'layoutFlow',
                    title: 'Container layout',
                    options: [
                        {
                            value: 'grid',
                            label: tr('Grid')
                        },
                        {
                            value: 'contents',
                            label: tr('Shared item layout')
                        }
                    ],
                    props: {
                        value: layout.flow,
                        enabled: edit && !pending(ui),
                        action: {
                            type: 'change',
                            name: '',
                            field: 'flow'
                        }
                    }
                },
                integer('columns', 'Grid columns'),
                {
                    id: 'layoutTracks',
                    title: 'Column tracks',
                    description: 'Optional sizes such as 128px 1fr auto',
                    props: {
                        text: layout.tracks || '',
                        enabled: edit && !pending(ui),
                        action: {
                            type: 'change',
                            name: '',
                            field: 'tracks'
                        }
                    }
                }
            );
        }
        const body = form(fields, width - 16, language, edit);
        nodes.push(
            node('Scroll', 'layoutConfigurationScroll', rect(0, y, width, h), {
                contentHeight: body.height,
                scrollbarId: 'layoutConfigurationScrollBar',
                children: body.nodes
            })
        );
        return {
            nodes
        };
    }
    if (ui.page === 'resolved') {
        const resolved =
            model.preview &&
            (model.preview.item_layout ||
                (model.preview.table || {}).item_layout);
        if (!resolved) {
            nodes.push(
                label(
                    'layoutResolvedHelp',
                    rect(12, y, width - 24, 96),
                    tr('Check and preview the draft before saving.'),
                    Object.assign(
                        {
                            wrap: true
                        },
                        muted
                    )
                )
            );
            return {
                nodes
            };
        }
        return {
            nodes: nodes.concat(
                node(
                    'View',
                    'layoutResolvedResults',
                    rect(0, y, width, Math.max(1, height - y)),
                    { view: 'itemResults' }
                )
            )
        };
    }
    if (model.layoutError) {
        nodes.push(
            node('Area', 'layoutInvalid', rect(0, y, width, h), {
                text:
                    tr(model.layoutError) +
                    '. ' +
                    tr(
                        'Use Source XML or create a view from a layout template.'
                    ),
                label: tr('Layout Editor'),
                readOnly: true,
                notice: true,
                color: 'error'
            })
        );
        return {
            nodes
        };
    }
    const wide = width >= 1000,
        catalogVisible = ui.catalogVisible !== false,
        propertiesVisible = ui.propertiesVisible !== false,
        left = wide
            ? catalogVisible
                ? Math.min(ui.catalogWidth, width * 0.24)
                : 56
            : width,
        properties = wide
            ? propertiesVisible
                ? Math.min(ui.propertiesWidth, width * 0.34)
                : 56
            : width;
    if (!wide) {
        nodes.push(
            sectionSelector(
                'layoutPanels',
                [
                    {
                        value: 'elements',
                        label: tr('Elements')
                    },
                    {
                        value: 'preview',
                        label: tr('Item preview')
                    },
                    {
                        value: 'settings',
                        label: tr('Element settings')
                    }
                ],
                ui.panel,
                rect(0, y, width, 38),
                !model.busy,
                'panel'
            )
        );
        y += 46;
    }
    const bodyHeight = Math.max(1, height - y);
    if (wide || ui.panel === 'elements') {
        const w = left,
            viewsHeight = Math.min(144, Math.max(68, bodyHeight * 0.24)),
            elementsTop = 58 + viewsHeight,
            children = [];
        if (!wide || catalogVisible)
            children.push(
                label(
                    'layoutViewsHeading',
                    rect(12, 10, Math.max(0, w - (wide ? 62 : 24)), 34),
                    tr('Views'),
                    { weight: 600 }
                ),
                node(
                    'List',
                    'layoutViewsList',
                    rect(12, 52, w - 24, viewsHeight),
                    {
                        source: 'layoutViews',
                        keyField: 'value',
                        rowHeight: 38,
                        scrollbarId: 'layoutViewsScrollBar'
                    }
                ),
                label(
                    'layoutElementsHeading',
                    rect(12, elementsTop + 8, w - 24, 28),
                    tr('Elements'),
                    {
                        weight: 600
                    }
                ),
                node(
                    'Choice',
                    'layoutAddWidget',
                    rect(12, elementsTop + 44, w - 24, 38),
                    {
                        label: tr('Add widget'),
                        value: '',
                        options: [
                            {
                                value: '',
                                label: tr('Add widget')
                            }
                        ].concat(choices(Document.widgets, language)),
                        enabled: edit && !pending(ui),
                        action: {
                            type: 'add'
                        }
                    }
                ),
                node(
                    'List',
                    'layoutElementsList',
                    rect(
                        12,
                        elementsTop + 90,
                        w - 24,
                        Math.max(0, bodyHeight - elementsTop - 146)
                    ),
                    {
                        source: 'layoutElements',
                        keyField: 'name',
                        rowHeight: 50,
                        scrollbarId: 'layoutElementsScrollBar'
                    }
                ),
                button(
                    'layoutEarlier',
                    rect(12, bodyHeight - 44, (w - 32) / 2, 36),
                    tr('Move element earlier'),
                    'chevron-up',
                    {
                        type: 'change',
                        field: 'order',
                        value: -1
                    },
                    edit && !!selected && !pending(ui),
                    {
                        iconOnly: true
                    }
                ),
                button(
                    'layoutLater',
                    rect((w + 8) / 2, bodyHeight - 44, (w - 32) / 2, 36),
                    tr('Move element later'),
                    'chevron-down',
                    {
                        type: 'change',
                        field: 'order',
                        value: 1
                    },
                    edit && !!selected && !pending(ui),
                    {
                        iconOnly: true
                    }
                )
            );
        if (wide)
            children.push(
                button(
                    'layoutToggleElements',
                    rect(
                        catalogVisible ? w - 46 : (w - 34) / 2,
                        10,
                        34,
                        34
                    ),
                    tr(
                        catalogVisible
                            ? 'Hide elements'
                            : 'Show elements'
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
            node('Box', 'layoutElementsPanel', rect(0, y, w, bodyHeight), {
                background: 'surfaceContainerLow',
                border: 'outlineVariant',
                children
            })
        );
        if (wide && catalogVisible)
            nodes.push(
                node(
                    'Splitter',
                    'layoutElementsSplit',
                    rect(w, y, 10, bodyHeight),
                    {
                        text: tr('Elements panel width'),
                        value: w,
                        min: 180,
                        max: Math.min(420, width * 0.24),
                        action: {
                            type: 'catalogSplit'
                        }
                    }
                )
            );
    }
    if (wide || ui.panel === 'settings') {
        const w = properties,
            x = wide ? width - w : 0,
            settingsChildren = [];
        if (!wide || propertiesVisible) {
            const fields = propertyFields(model, ui, language, w),
                body = form(fields, w - 40, language, edit && !pending(ui));
            if (selected) {
                body.nodes.push(
                    button(
                        'layoutRemoveElement',
                        rect(0, body.height, w - 40, 38),
                        tr('Remove element'),
                        'delete',
                        {
                            type: 'remove'
                        },
                        edit && !pending(ui)
                    )
                );
                body.height += 46;
            } else {
                body.nodes.push(
                    label(
                        'layoutSelectHelp',
                        rect(0, 0, w - 40, 120),
                        tr('Select an element or add a new widget.'),
                        Object.assign(
                            {
                                wrap: true
                            },
                            muted
                        )
                    )
                );
                body.height = 128;
            }
            settingsChildren.push(
                label(
                    'layoutSettingsHeading',
                    rect(12, 10, Math.max(0, w - (wide ? 62 : 24)), 34),
                    tr('Element settings'),
                    { weight: 600 }
                ),
                node(
                    'Scroll',
                    'layoutSettingsScroll',
                    rect(12, 52, w - 24, Math.max(0, bodyHeight - 64)),
                    {
                        contentHeight: body.height,
                        resetKey: ui.selected,
                        scrollbarId: 'layoutSettingsScrollBar',
                        children: body.nodes
                    }
                )
            );
        }
        if (wide)
            settingsChildren.push(
                button(
                    'layoutToggleSettings',
                    rect(
                        propertiesVisible ? w - 46 : (w - 34) / 2,
                        10,
                        34,
                        34
                    ),
                    tr(
                        propertiesVisible
                            ? 'Hide element settings'
                            : 'Show element settings'
                    ),
                    propertiesVisible ? 'chevron-right' : 'chevron-left',
                    {
                        type: 'propertiesVisible'
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
            node('Box', 'layoutSettingsPanel', rect(x, y, w, bodyHeight), {
                background: 'surfaceContainerLow',
                border: 'outlineVariant',
                children: settingsChildren
            })
        );
        if (wide && propertiesVisible)
            nodes.push(
                node(
                    'Splitter',
                    'layoutSettingsSplit',
                    rect(x - 10, y, 10, bodyHeight),
                    {
                        text: tr('Element settings width'),
                        value: w,
                        min: 240,
                        max: Math.min(520, width * 0.34),
                        reverse: true,
                        action: {
                            type: 'propertiesSplit'
                        }
                    }
                )
            );
    }
    if (wide || ui.panel === 'preview') {
        const x = wide ? left + 10 : 0,
            w = wide ? Math.max(1, width - left - properties - 20) : width;
        nodes.push(
            node('Box', 'layoutPreviewPanel', rect(x, y, w, bodyHeight), {
                background: 'surfaceContainerLow',
                border: 'outlineVariant',
                children: [
                    label(
                        'layoutPreviewHeading',
                        rect(12, 8, w - 24, 28),
                        tr(
                            model.samplePreview
                                ? 'Item preview · Sample data'
                                : 'Item preview'
                        ),
                        { weight: 600 }
                    ),
                    layout.elements.length
                        ? node(
                              'View',
                              'layoutPreviewResults',
                              rect(12, 44, w - 24, bodyHeight - 56),
                              { view: 'itemResults' }
                          )
                        : label(
                              'layoutBlankCanvas',
                              rect(12, 44, w - 24, 80),
                              tr('Add a widget to start this view.'),
                              Object.assign({ wrap: true }, muted)
                          )
                ]
            })
        );
    }
    return {
        nodes
    };
}

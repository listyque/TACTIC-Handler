import { node, rect, label, button, muted } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { sections } from '../../../controls/forms/sections.ui.mjs';
import { notices, toolbar as documentToolbar } from '../admin.document.mjs';
import * as Document from './page.document.mjs';
import { sectionSelector } from '../admin.document.mjs';
import { spacingField } from './canvas.mjs';
import * as Data from './page.data.mjs';
import * as Reports from './page.reports.mjs';
import { listAction } from '../../../controls/lists/tree.ui.mjs';
import * as Viewport from './page.viewport.mjs';
import * as Components from './page.components.mjs';

function blockTitle(item, key, language) {
    if (item.title && item.title !== item.kind) return item.title;
    return (
        translate(item.kind[0].toUpperCase() + item.kind.slice(1), language) +
        ' ' +
        (Number(key.split('.').pop()) + 1)
    );
}

export function model(raw, ui) {
    return Object.assign({}, raw, {
        ready: raw.canWrite,
        identity: raw.document?.name || '',
        dirty: raw.dirty || Object.keys(ui.text).length > 0,
        pendingText: Object.keys(ui.text).length > 0,
        saveAllowed: !!raw.checked,
        error: raw.error || ui.error,
        document: raw.document || {},
        layers: [
            {
                key: 'page',
                depth: 0,
                label: raw.document?.title || 'Page',
                kind: 'page'
            }
        ].concat(Document.layers(raw.document || { blocks: [] }))
    });
}
export function toolbar(model, ui, width, language) {
    return documentToolbar(model, ui, width, language);
}
export function models(model) {
    return { pageBlocks: model.layers };
}
export function row(list, record, model, ui, language) {
    const key = record.key === 'page' ? '' : record.key;
    const title =
        record.label === record.kind
            ? blockTitle({ kind: record.kind }, record.key, language)
            : record.label;
    return {
        nodes: [
            node(
                'Action',
                'pageBlock_' + record.key,
                rect(0, 0, list.width - 16, 38),
                {
                    text: title,
                    normalColor: 'transparent',
                    selectedColor: 'contentSelection',
                    selected:
                        (ui.selection || []).includes(key) ||
                        ui.selected === key,
                    children: [
                        label(
                            'pageBlockLabel_' + record.key,
                            rect(
                                8 + record.depth * 12,
                                0,
                                list.width - 32 - record.depth * 12,
                                38
                            ),
                            title
                        )
                    ],
                    action: { type: 'select', key }
                }
            )
        ]
    };
}

export function describe(model, ui, width, height, language) {
    if (width <= 0 || height <= 0) return { nodes: [] };
    // Native document and selection notifications can arrive in either order.
    if (ui.selected && !model.layers.some((row) => row.key === ui.selected))
        ui = Object.assign({}, ui, { selected: '' });
    if (height < 400)
        return {
            nodes: [
                node('Scroll', 'pageEditorScroll', rect(0, 0, width, height), {
                    contentHeight: 640,
                    scrollbarId: 'pageEditorScrollBar',
                    children: describe(model, ui, width - 16, 640, language)
                        .nodes
                })
            ]
        };
    const tr = (s) => translate(s, language),
        canEdit = model.canWrite && !model.busy && !model.uncertain;
    const noticesModel = Object.assign({}, model, {
        confirmationText:
            ui.confirmation === 'page'
                ? 'Discard changes to the current view and continue?'
                : ui.confirmation === 'remove'
                  ? 'Remove this widget from the page?'
                  : undefined
    });
    const notice = notices(noticesModel, ui, width, language),
        nodes = notice.nodes;
    let y = notice.top;
    const newWidth = language === 'ru' ? 170 : 120;
    const pickerWidth = Math.min(360, Math.max(100, width - newWidth - 70));
    nodes.push(
        node('Choice', 'pageLayoutChoice', rect(0, y, pickerWidth, 38), {
            label: tr('Page layout'),
            value: model.document.name || '',
            options: model.catalog.map((r) => ({
                value: r.identity,
                label: r.label
            })),
            enabled: !model.busy && !model.uncertain,
            action: { type: 'load' }
        }),
        button(
            'pageLayoutNew',
            rect(pickerWidth + 12, y, newWidth, 38),
            tr('New page'),
            'add',
            { type: 'new' },
            canEdit
        ),
        button(
            'pageLayoutOpen',
            rect(pickerWidth + newWidth + 24, y, 38, 38),
            tr('Open saved view'),
            'open-in-new',
            { type: 'open' },
            !model.dirty && !!model.document.name && !model.busy
        )
    );
    y += 50;
    if (ui.creating) {
        const w = Math.min(300, Math.max(100, (width - 12) / 2));
        nodes.push(
            node('Field', 'pageLayoutName', rect(0, y, w, 38), {
                label: tr('Page name'),
                placeholder: 'my_dashboard',
                text: ui.newName,
                action: { type: 'newName' }
            }),
            node('Field', 'pageLayoutTitle', rect(w + 12, y, w, 38), {
                label: tr('Title'),
                placeholder: tr('Title'),
                text: ui.newTitle,
                action: { type: 'newTitle' }
            }),
            button(
                'pageLayoutCreate',
                rect(0, y + 48, 164, 38),
                tr('Create draft'),
                'add',
                { type: 'create' },
                canEdit
            ),
            button(
                'pageLayoutCancelNew',
                rect(176, y + 48, 120, 38),
                tr('Cancel'),
                'close',
                { type: 'cancelNew' },
                true
            )
        );
        y += 98;
    }
    if (!model.document.name) {
        nodes.push(
            label(
                'pageChooseHelp',
                rect(0, y, width, 90),
                tr('Choose a page or create a new page.'),
                Object.assign({}, muted, { wrap: true })
            )
        );
        return { nodes };
    }
    const narrow = width < 1000,
        modeWidth = narrow ? 38 : language === 'ru' ? 200 : 176,
        left = narrow ? width : 220,
        right = narrow ? width : 310,
        canvasX = narrow || ui.preview ? 0 : left + 12,
        canvasWidth = narrow || ui.preview ? width : width - left - right - 24;
    nodes.push(
        node('Choice', 'pageAddWidget', rect(0, y, Math.min(width, 220), 38), {
            label: tr('Add widget'),
            value: '',
            options: [{ value: '', label: tr('Add widget') }].concat(
                Document.kinds.map((value) => ({
                    value,
                    label: tr(
                        {
                            items: 'Items',
                            details: 'Details',
                            row: 'Row',
                            column: 'Column',
                            text: 'Text',
                            markdown: 'Markdown',
                            metric: 'Metric',
                            table: 'Table',
                            link: 'Link',
                            chart: 'Bar chart',
                            summary: 'Grouped report',
                            grid: 'Grid layout',
                            heading: 'Heading',
                            icon: 'Icon',
                            image: 'Object image',
                            button: 'Button',
                            divider: 'Divider',
                            spacer: 'Spacer'
                        }[value]
                    )
                }))
            ),
            enabled: canEdit && !ui.preview,
            toolTip: model.layers.some((row) => row.kind === 'items')
                ? tr('Items preview shows up to three records.')
                : '',
            action: { type: 'add' }
        })
    );
    if (!ui.preview) {
        const current = Document.fingerprint(model.document);
        const historyCurrent = ui.historyDocument === current;
        const ready = canEdit && !model.pendingText && !ui.confirmation;
        const single = (ui.selection || []).length < 2;
        const p = Document.path(ui.selected),
            rows = p.length ? Document.siblings(model.document, p) : [];
        const actions = [
            [
                'Undo',
                'undo',
                { type: 'undo' },
                ready && historyCurrent && ui.past?.length
            ],
            [
                'Redo',
                'redo',
                { type: 'redo' },
                ready && historyCurrent && ui.future?.length
            ],
            [
                'Duplicate widget',
                'content-copy',
                { type: 'duplicate' },
                ready && single && !!ui.selected
            ],
            [
                'Move up',
                'arrow-upward',
                { type: 'reorder', delta: -1 },
                ready && single && p.length && p[p.length - 1] > 0
            ],
            [
                'Move down',
                'arrow-downward',
                { type: 'reorder', delta: 1 },
                ready && single && p.length && p[p.length - 1] < rows.length - 1
            ]
        ];
        const separate = width < 700;
        actions.forEach(([title, icon, action, enabled], index) =>
            nodes.push(
                button(
                    'pageAction_' + action.type + (action.delta || ''),
                    rect(
                        (separate ? 0 : 232) + index * 40,
                        y + (separate ? 44 : 0),
                        32,
                        32
                    ),
                    tr(title),
                    icon,
                    action,
                    !!enabled,
                    { iconOnly: true }
                )
            )
        );
    }
    y += 50;
    nodes.push(
        button(
            'pagePreviewMode',
            rect(width - modeWidth, y - 50, modeWidth, 38),
            tr(ui.preview ? 'Back to editing' : 'Clean preview'),
            ui.preview ? 'edit' : 'visibility',
            { type: 'preview' },
            !model.busy && !ui.creating && !model.pendingText,
            { iconOnly: narrow }
        )
    );
    if (!ui.preview && width < 700) y += 44;
    if (width >= 500) {
        if (ui.preview)
            nodes.push(
                label(
                    'pageSelectionHint',
                    rect(0, y, width, 24),
                    tr(
                        ui.preview
                            ? 'Read-only draft preview. Nothing is saved.'
                            : 'Click to select. Alt-click for underlying layers.'
                    ),
                    Object.assign({}, muted, { fontRole: 'caption' })
                )
            );
        else {
            const p = Document.path(ui.selected),
                crumbs = [
                    { key: '', title: model.document.title || tr('Page') }
                ];
            p.forEach((_, index) => {
                const key = p.slice(0, index + 1).join('.'),
                    item = Document.block(model.document, key);
                crumbs.push({
                    key,
                    title: blockTitle(item, key, language)
                });
            });
            let x = 0;
            const children = [];
            crumbs.forEach((crumb, index) => {
                if (index) {
                    children.push(
                        label(
                            'pageAncestorSeparator_' + index,
                            rect(x, 0, 20, 30),
                            '›',
                            muted
                        )
                    );
                    x += 20;
                }
                const w = Math.max(
                    60,
                    Math.min(180, crumb.title.length * 8 + 24)
                );
                children.push(
                    listAction(
                        'pageAncestor_' + (crumb.key || 'page'),
                        rect(x, 0, w, 30),
                        crumb.title,
                        '',
                        { type: 'select', key: crumb.key },
                        !model.busy && !model.pendingText,
                        {
                            toolTip: crumb.title,
                            selected: crumb.key === ui.selected
                        }
                    )
                );
                x += w;
            });
            nodes.push(
                node('Scroll', 'pageAncestors', rect(0, y, width, 46), {
                    contentWidth: x,
                    contentHeight: 30,
                    scrollbarId: 'pageAncestorsBar',
                    children
                })
            );
        }
        y += ui.preview ? 32 : 50;
    }
    if (narrow && !ui.preview) {
        nodes.push(
            sectionSelector(
                'pageEditorPanels',
                [
                    { value: 'layers', label: tr('Page blocks') },
                    { value: 'canvas', label: tr('Canvas') },
                    { value: 'properties', label: tr('Properties') }
                ],
                ui.panel,
                rect(0, y, width, 38),
                !model.busy,
                'panel'
            )
        );
        y += 50;
    }
    const h = Math.max(100, height - y);
    {
        if (!ui.preview && (!narrow || ui.panel === 'layers'))
            nodes.push(
                node('Box', 'pageLayersPanel', rect(0, y, left, h), {
                    background: 'surfaceContainerLow',
                    border: 'outlineVariant',
                    children: [
                        label(
                            'pageLayersTitle',
                            rect(12, 12, left - 24, 24),
                            tr('Page blocks'),
                            { weight: 600 }
                        ),
                        node(
                            'List',
                            'pageBlocks',
                            rect(12, 48, left - 24, Math.max(0, h - 60)),
                            {
                                source: 'pageBlocks',
                                keyField: 'key',
                                rowHeight: 42,
                                scrollbarId: 'pageBlocksScrollBar'
                            }
                        )
                    ]
                })
            );
        const item = ui.selected
                ? Document.block(model.document, ui.selected)
                : null,
            fields = [];
        function field(name, title, value, root = false, kind) {
            const key = (root ? 'page' : ui.selected) + ':' + name;
            const props = {
                text: Object.prototype.hasOwnProperty.call(ui.text, key)
                    ? ui.text[key]
                    : String(value ?? ''),
                action: { type: 'buffer', key },
                commitAction: { type: 'commit', key, field: name, root },
                enabled: canEdit && (ui.selection || []).length < 2
            };
            fields.push({ id: 'pageProperty_' + name, title, kind, props });
        }
        field(
            'title',
            'Title',
            item ? item.title : model.document.title,
            !item
        );
        if (!item)
            fields.push(
                ...Reports.fields(
                    model,
                    ui,
                    right - 24,
                    language,
                    canEdit && (ui.selection || []).length < 2
                )
            );
        if (item) {
            const parent = Document.path(ui.selected).slice(0, -1).join('.');
            fields.push({
                kind: 'Choice',
                id: 'pageParent',
                title: 'Parent container',
                props: {
                    value: parent,
                    enabled:
                        canEdit &&
                        (ui.selection || []).length < 2 &&
                        !model.pendingText,
                    action: { type: 'reparent' }
                },
                options: [
                    { value: '', label: model.document.title || tr('Page') }
                ].concat(
                    model.layers
                        .filter(
                            (row) =>
                                ['row', 'column', 'grid', 'details'].includes(
                                    row.kind
                                ) &&
                                row.key !== ui.selected &&
                                !row.key.startsWith(ui.selected + '.')
                        )
                        .map((row) => ({
                            value: row.key,
                            label: Document.path(row.key)
                                .map((_, index) => {
                                    const key = Document.path(row.key)
                                        .slice(0, index + 1)
                                        .join('.');
                                    const item = Document.block(
                                        model.document,
                                        key
                                    );
                                    return blockTitle(item, key, language);
                                })
                                .join(' / ')
                        }))
                )
            });
            fields.push(
                ...Data.fields(
                    model,
                    ui,
                    right - 24,
                    language,
                    canEdit && (ui.selection || []).length < 2
                )
            );
            fields.push(
                ...Reports.fields(
                    model,
                    ui,
                    right - 24,
                    language,
                    canEdit && (ui.selection || []).length < 2
                )
            );
            if (
                ['text', 'heading', 'markdown'].includes(item.kind) &&
                Data.mode(model.document, ui.selected) === 'static'
            )
                field(
                    'text',
                    'Text',
                    item.text || '',
                    false,
                    item.kind === 'markdown' ? 'Area' : undefined
                );
            if (['link', 'button'].includes(item.kind))
                field('href', 'Link URL', item.href || '');
            Components.componentFields(
                fields,
                item,
                ui,
                canEdit,
                language,
                field
            );
            fields.push({
                kind: 'Heading',
                id: 'pageLayoutHeading',
                title: 'Layout'
            });
            field('offset_x', 'Horizontal offset', item.offset_x || 0);
            field('offset_y', 'Vertical offset', item.offset_y || 0);
            Components.sizingFields(
                fields,
                item,
                ui,
                model.document,
                parent,
                canEdit,
                language,
                field
            );
            field('width', 'Width', item.width);
            field('height', 'Height', item.height);
            field('weight', 'Flexible width', item.weight || 1);
            if (['row', 'column', 'grid', 'details'].includes(item.kind))
                field('gap', 'Gap', item.gap ?? 8);
            for (const name of ['padding', 'margin'])
                fields.push(
                    spacingField(
                        'page' + name,
                        tr(name === 'padding' ? 'Padding' : 'Margin'),
                        item[name] || [0, 0, 0, 0],
                        ui.text,
                        { type: 'spacing', field: name },
                        language,
                        canEdit && (ui.selection || []).length < 2,
                        right - 72
                    )
                );
            fields.push({
                kind: 'Heading',
                id: 'pageAppearanceHeading',
                title:
                    (ui.selection || []).length > 1
                        ? 'Appearance for selection'
                        : 'Appearance'
            });
            const appearance = Object.assign(
                {
                    fill: 'transparent',
                    stroke: 'outlineVariant',
                    stroke_width: 0,
                    radius: 0,
                    shadow: false,
                    animate: false
                },
                item.appearance || {}
            );
            for (const [name, title] of [
                ['fill', 'Fill color'],
                ['stroke', 'Stroke color'],
                ['stroke_width', 'Stroke width'],
                ['radius', 'Corner radius'],
                ['shadow', 'Shadow'],
                ['animate', 'Animate layout changes']
            ]) {
                if (['fill', 'stroke'].includes(name)) {
                    const roles =
                        name === 'fill'
                            ? [
                                  ['transparent', 'Transparent'],
                                  ['panel', 'Panel'],
                                  ['workspace', 'Workspace'],
                                  ['surfaceContainerLow', 'Low surface']
                              ]
                            : [
                                  ['outlineVariant', 'Outline'],
                                  ['contentAccent', 'Accent'],
                                  ['transparent', 'Transparent']
                              ];
                    fields.push({
                        kind: 'Choice',
                        id: 'pageAppearance_' + name,
                        title,
                        props: {
                            value: appearance[name],
                            enabled: canEdit,
                            action: { type: 'appearance', field: name }
                        },
                        options: roles
                            .map(([value, label]) => ({
                                value,
                                label: tr(label)
                            }))
                            .concat(
                                appearance[name].startsWith('#')
                                    ? [
                                          {
                                              value: appearance[name],
                                              label: appearance[name]
                                          }
                                      ]
                                    : []
                            )
                    });
                    fields.push({
                        kind: 'ColorChoice',
                        id: 'pageColor_' + name,
                        title:
                            name === 'fill'
                                ? 'Custom fill color'
                                : 'Custom stroke color',
                        props: {
                            value: appearance[name].startsWith('#')
                                ? appearance[name]
                                : '#607D8B',
                            enabled: canEdit,
                            action: { type: 'appearance', field: name }
                        }
                    });
                    continue;
                }
                const key = ui.selected + ':appearance:' + name,
                    toggle = ['shadow', 'animate'].includes(name);
                fields.push({
                    id: 'pageAppearance_' + name,
                    title,
                    kind: toggle ? 'CheckBox' : 'Field',
                    description:
                        name === 'animate'
                            ? 'Follows appearance motion settings. Disabled while editing.'
                            : undefined,
                    props: toggle
                        ? {
                              checked: appearance[name],
                              action: { type: 'appearance', field: name },
                              enabled: canEdit
                          }
                        : {
                              text: Object.prototype.hasOwnProperty.call(
                                  ui.text,
                                  key
                              )
                                  ? ui.text[key]
                                  : String(appearance[name]),
                              action: { type: 'buffer', key },
                              commitAction: {
                                  type: 'appearanceCommit',
                                  field: name,
                                  key
                              },
                              enabled: canEdit
                          }
                });
            }
            if (item.kind === 'items')
                fields.push({
                    kind: 'Button',
                    id: 'pageEditCard',
                    title: 'Edit card layout',
                    props: {
                        icon: 'edit',
                        enabled: !model.busy,
                        action: { type: 'card' }
                    }
                });
            fields.push({
                kind: 'Button',
                id: 'pageRemoveBlock',
                title: 'Remove widget',
                props: {
                    icon: 'delete',
                    enabled: canEdit && (ui.selection || []).length < 2,
                    action: { type: 'remove' }
                }
            });
        }
        const properties =
            (ui.selection || []).length > 1
                ? fields.filter(
                      (field) =>
                          field.id === 'pageAppearanceHeading' ||
                          field.id.startsWith('pageAppearance_') ||
                          field.id.startsWith('pageColor_')
                  )
                : fields;
        const body = sections(properties, right - 24, language, canEdit);
        if (!ui.preview && (!narrow || ui.panel === 'properties'))
            nodes.push(
                node(
                    'Box',
                    'pagePropertiesPanel',
                    rect(width - right, y, right, h),
                    {
                        background: 'surfaceContainerLow',
                        border: 'outlineVariant',
                        children: [
                            node(
                                'Scroll',
                                'pageProperties',
                                rect(12, 12, right - 24, h - 24),
                                {
                                    contentHeight: body.height,
                                    scrollbarId: 'pagePropertiesBar',
                                    children: body.nodes
                                }
                            )
                        ]
                    }
                )
            );
    }
    if (ui.preview || !narrow || ui.panel === 'canvas') {
        const tools = Viewport.controls(
            ui,
            canvasWidth - 24,
            language,
            !model.busy
        );
        nodes.push(
            node('Box', 'pageCanvasPanel', rect(canvasX, y, canvasWidth, h), {
                background: 'workspace',
                border: 'outlineVariant',
                children: [
                    node(
                        'Box',
                        'pageCanvasTools',
                        rect(12, 12, canvasWidth - 24, tools.height),
                        {
                            children: tools.nodes
                        }
                    ),
                    node(
                        'View',
                        'pageCanvas',
                        rect(
                            12,
                            20 + tools.height,
                            canvasWidth - 24,
                            Math.max(1, h - tools.height - 32)
                        ),
                        { view: 'pagePreview' }
                    )
                ]
            })
        );
    }
    return { nodes };
}

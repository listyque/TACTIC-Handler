import { node, rect } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { sections } from '../../../controls/forms/sections.ui.mjs';
import { notices, toolbar as documentToolbar } from '../admin.document.mjs';
import * as Document from './page.document.mjs';
import * as Links from './page.links.mjs';
import { sectionSelector } from '../admin.document.mjs';
import { spacingField } from './canvas.mjs';
import * as Data from './page.data.mjs';
import * as Reports from './page.reports.mjs';
import * as Components from './page.components.mjs';
import * as Chrome from './page.chrome.mjs';

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
                kind: 'page',
                hasChildren: !!raw.document?.blocks?.length
            }
        ].concat(
            Document.layers(raw.document || { blocks: [] }).map(
                (row, index, rows) =>
                    Object.assign({}, row, {
                        depth: row.depth + 1,
                        hasChildren: rows[index + 1]?.depth > row.depth
                    })
            )
        )
    });
}
export function toolbar(model, ui, width, language) {
    return documentToolbar(model, ui, width, language);
}
export { actions, toolEvent } from './page.chrome.mjs';
export function models(model, ui) {
    return {
        pageBlocks: model.layers.filter(
            (row) =>
                !(ui.collapsed || []).some(
                    (key) =>
                        row.key !== key &&
                        (key === 'page' || row.key.startsWith(key + '.'))
                )
        )
    };
}
export function row(list, record, model, ui, language) {
    return Chrome.treeRow(list, record, model, ui, language, blockTitle);
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
    const geometry = Chrome.geometry(width, ui),
        { narrow, left, right, canvasX, canvasWidth } = geometry;
    const tools = Chrome.canvasTools(model, ui, width - 16, language, canEdit);
    nodes.push(
        node(
            'Box',
            model.document.name ? 'pageCanvasTools' : 'pageEmptyTools',
            rect(0, y, width, tools.height + 16),
            {
                background: 'surfaceContainerLow',
                children: tools.nodes.map((item) =>
                    Object.assign({}, item, { x: item.x + 8, y: item.y + 8 })
                )
            }
        )
    );
    y += tools.height + 24;
    if (!model.document.name) {
        if (!ui.creating)
            nodes.push(
                node('Label', 'pageEmptyHint', rect(12, y, width - 24, 32), {
                    text: tr('Choose a page or create a new page.'),
                    color: 'secondaryText'
                })
            );
        return { nodes };
    }
    if (narrow && !ui.preview && !ui.source) {
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
                true,
                'panel'
            )
        );
        y += 42;
    }
    const h = Math.max(100, height - y);
    {
        if (!ui.preview && !ui.source && (!narrow || ui.panel === 'layers'))
            nodes.push(
                Chrome.treePanel(
                    model,
                    ui,
                    rect(0, y, left, h),
                    language,
                    canEdit,
                    narrow
                )
            );
        if (!narrow && !ui.preview && !ui.source)
            nodes.push(...Chrome.splitters(geometry, y, h, language));
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
            if (!parent)
                fields.push({
                    kind: 'Choice',
                    id: 'pageProperty_region',
                    title: 'Page region',
                    props: {
                        value: item.region || 'content',
                        enabled: canEdit && (ui.selection || []).length < 2,
                        action: { type: 'change', field: 'region' }
                    },
                    options: [
                        ['header', 'Header'],
                        ['content', 'Content'],
                        ['footer', 'Footer']
                    ].map(([value, label]) => ({ value, label: tr(label) }))
                });
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
            if (['link', 'button'].includes(item.kind)) {
                field('href', 'Link URL', item.href || '');
                if (
                    Links.target(
                        item.href,
                        model.project,
                        model.origin,
                        model.catalog
                    )
                )
                    fields[fields.length - 1].trailingAction = {
                        title: 'Edit linked page layout',
                        icon: 'open-in-new',
                        enabled: !model.busy && !model.dirty,
                        action: { type: 'linkedPage' }
                    };
            }
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
        if (!ui.preview && !ui.source && (!narrow || ui.panel === 'properties'))
            nodes.push(
                node(
                    'Box',
                    'pagePropertiesPanel',
                    rect(width - right, y, right, h),
                    {
                        background: 'surfaceContainerLow',
                        border: 'outlineVariant',
                        children: Chrome.propertiesHeader(
                            ui,
                            right,
                            language,
                            narrow
                        ).concat(
                            ui.propertiesHidden && !narrow
                                ? []
                                : [
                                      node(
                                          'Scroll',
                                          'pageProperties',
                                          rect(8, 36, right - 16, h - 44),
                                          {
                                              contentHeight: body.height,
                                              scrollbarId: 'pagePropertiesBar',
                                              children: body.nodes
                                          }
                                      )
                                  ]
                        )
                    }
                )
            );
    }
    if (ui.preview || ui.source || !narrow || ui.panel === 'canvas') {
        nodes.push(
            node('Box', 'pageCanvasPanel', rect(canvasX, y, canvasWidth, h), {
                background: 'workspace',
                border: 'outlineVariant',
                children: [
                    ui.source
                        ? node(
                              'Code',
                              'pageXmlSource',
                              rect(8, 8, canvasWidth - 16, Math.max(1, h - 16)),
                              {
                                  text: model.checked
                                      ? model.sourceXml || ''
                                      : '',
                                  syntax: 'xml',
                                  language,
                                  readOnly: true,
                                  service: 'sourceEditor',
                                  label: tr('Source XML'),
                                  bufferKey: 'page:' + model.document.name
                              }
                          )
                        : node(
                              'View',
                              'pageCanvas',
                              rect(8, 8, canvasWidth - 16, Math.max(1, h - 16)),
                              { view: 'pagePreview' }
                          )
                ]
            })
        );
    }
    return { nodes };
}

import { node, rect, label, button, muted } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { sections } from '../../../controls/forms/sections.ui.mjs';
import { notices, toolbar as documentToolbar } from '../admin.document.mjs';
import * as Document from './page.document.mjs';
import { sectionSelector } from '../admin.document.mjs';
import { spacingField } from './canvas.mjs';

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
            ? translate(
                  record.kind[0].toUpperCase() + record.kind.slice(1),
                  language
              )
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
                    selected: ui.selected === key,
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
                            link: 'Link'
                        }[value]
                    )
                }))
            ),
            enabled: canEdit && !ui.preview,
            action: { type: 'add' }
        })
    );
    if (width >= 700 && model.layers.some((row) => row.kind === 'items'))
        nodes.push(
            label(
                'pageSampleHint',
                rect(232, y, Math.max(0, width - 244 - modeWidth), 38),
                tr('Items preview shows up to three records.'),
                Object.assign({}, muted, { fontRole: 'caption', wrap: true })
            )
        );
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
    if (width >= 500) {
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
        y += 32;
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
                enabled: canEdit
            };
            fields.push({ id: 'pageProperty_' + name, title, kind, props });
        }
        field(
            'title',
            'Title',
            item ? item.title : model.document.title,
            !item
        );
        if (item) {
            if (['text', 'markdown'].includes(item.kind))
                field('text', 'Text', item.text || '');
            if (['items', 'table', 'metric'].includes(item.kind))
                fields.push({
                    kind: 'Choice',
                    id: 'pageProperty_search_type',
                    title: 'Search Type',
                    options: model.searchTypes || [],
                    props: {
                        value: item.search_type,
                        enabled: canEdit,
                        action: { type: 'change', field: 'search_type' }
                    }
                });
            if (['items', 'table'].includes(item.kind))
                field('view', 'View', item.view || 'table');
            if (item.kind === 'link')
                field('href', 'Link URL', item.href || '');
            field('width', 'Width', item.width);
            field('height', 'Height', item.height);
            field('weight', 'Flexible width', item.weight || 1);
            if (['row', 'column', 'details'].includes(item.kind))
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
                        canEdit,
                        right - 72
                    )
                );
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
                    enabled: canEdit,
                    action: { type: 'remove' }
                }
            });
        }
        const body = sections(fields, right - 24, language, canEdit);
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
    if (ui.preview || !narrow || ui.panel === 'canvas')
        nodes.push(
            node('Box', 'pageCanvasPanel', rect(canvasX, y, canvasWidth, h), {
                background: 'workspace',
                border: 'outlineVariant',
                children: [
                    node(
                        'View',
                        'pageCanvas',
                        rect(12, 12, canvasWidth - 24, h - 24),
                        { view: 'pagePreview' }
                    )
                ]
            })
        );
    return { nodes };
}

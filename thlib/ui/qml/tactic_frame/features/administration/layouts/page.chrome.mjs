import { node, rect, label, button } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { listAction } from '../../../controls/lists/tree.ui.mjs';
import * as Document from './page.document.mjs';
import * as Viewport from './page.viewport.mjs';
import { buttonWidth } from '../../../controls/buttons/metrics.mjs';

export const icons = {
    page: 'dashboard',
    row: 'view-agenda',
    column: 'view-column',
    grid: 'grid-view',
    text: 'notes',
    markdown: 'description',
    metric: 'speed',
    table: 'table',
    items: 'view-list',
    details: 'info',
    link: 'link',
    chart: 'bar-chart',
    summary: 'summarize',
    heading: 'title',
    icon: 'star',
    image: 'image',
    button: 'smart-button',
    divider: 'horizontal-rule',
    spacer: 'space-bar',
    field: 'input',
    form: 'edit-note',
    action: 'bolt'
};
const titles = {
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
    spacer: 'Spacer',
    field: 'Record field',
    form: 'Record form',
    action: 'Record action'
};
export function geometry(width, ui) {
    const narrow = width < 1000;
    if (narrow || ui.preview || ui.source)
        return {
            narrow,
            left: width,
            right: width,
            canvasX: 0,
            canvasWidth: width
        };
    const left = ui.layersHidden
        ? 32
        : Math.max(140, Math.min(ui.layersWidth, 320));
    const right = ui.propertiesHidden
        ? 32
        : Math.max(240, Math.min(ui.propertiesWidth, 420, width - left - 380));
    return {
        narrow,
        left,
        right,
        canvasX: left + 10,
        canvasWidth: width - left - right - 20
    };
}
export function treeRow(list, record, model, ui, language, blockTitle) {
    const key = record.key === 'page' ? '' : record.key;
    const title =
        record.label === record.kind
            ? blockTitle({ kind: record.kind }, record.key, language)
            : record.label;
    const children = record.hasChildren;
    const indent = 4 + record.depth * 6;
    const row = listAction(
        'pageBlock_' + record.key,
        rect(0, 0, list.width - 16, 32),
        title,
        icons[record.kind],
        { type: 'select', key },
        true,
        {
            selected: (ui.selection || []).includes(key) || ui.selected === key,
            toolTip: title
        }
    );
    row.children.forEach((child) => {
        child.x = indent + (child.kind === 'Label' ? 52 : 32);
        if (child.kind === 'Label')
            child.width = Math.max(0, row.width - child.x - 4);
    });
    row.keys = {
        ArrowLeft: { type: 'treeCollapse', key: record.key },
        ArrowRight: { type: 'treeExpand', key: record.key }
    };
    return {
        nodes: [row].concat(
            children
                ? [
                      listAction(
                          'pageTreeToggle_' + record.key,
                          rect(indent, 0, 32, 32),
                          translate('Expand or collapse', language),
                          ui.collapsed.includes(record.key)
                              ? 'chevron-right'
                              : 'chevron-down',
                          { type: 'treeToggle', key: record.key },
                          true,
                          { iconOnly: true }
                      )
                  ]
                : []
        )
    };
}
export function treePanel(model, ui, bounds, language, enabled, narrow) {
    const tr = (text) => translate(text, language),
        width = bounds.width,
        collapsed = ui.layersHidden && !narrow;
    const children = [
        button(
            'pageLayersToggle',
            rect(
                collapsed ? (width - 28) / 2 : width - 46,
                10,
                collapsed ? 28 : 34,
                34
            ),
            tr(ui.layersHidden ? 'Show page blocks' : 'Hide page blocks'),
            ui.layersHidden ? 'chevron-right' : 'chevron-left',
            { type: 'togglePanel', panel: 'layers' },
            true,
            { iconOnly: true, iconAction: true, round: false }
        )
    ];
    if (!ui.layersHidden || narrow)
        children.push(
            label(
                'pageLayersTitle',
                rect(12, 10, Math.max(0, width - (narrow ? 24 : 62)), 34),
                tr('Page blocks'),
                { weight: 600 }
            ),
            node('Choice', 'pageAddWidget', rect(12, 52, width - 24, 36), {
                label: tr('Add widget'),
                value: '',
                enabled,
                options: [
                    {
                        value: '',
                        label: tr(width < 210 ? 'Add' : 'Add widget'),
                        icon: 'add'
                    }
                ].concat(
                    Document.kinds.map((value) => ({
                        value,
                        label: tr(titles[value]),
                        icon: icons[value]
                    }))
                ),
                action: { type: 'add' }
            }),
            node(
                'List',
                'pageBlocks',
                rect(8, 96, width - 16, Math.max(0, bounds.height - 104)),
                {
                    source: 'pageBlocks',
                    keyField: 'key',
                    rowHeight: 34,
                    rowGap: 2,
                    scrollbarId: 'pageBlocksScrollBar'
                }
            )
        );
    if (narrow) children.shift();
    return node('Box', 'pageLayersPanel', bounds, {
        background: 'surfaceContainerLow',
        border: 'outlineVariant',
        children
    });
}
export function propertiesHeader(ui, width, language, narrow) {
    const tr = (text) => translate(text, language),
        collapsed = ui.propertiesHidden && !narrow,
        children = [
            button(
                'pagePropertiesToggle',
                rect(
                    collapsed ? (width - 28) / 2 : width - 46,
                    10,
                    collapsed ? 28 : 34,
                    34
                ),
                tr(ui.propertiesHidden ? 'Show properties' : 'Hide properties'),
                ui.propertiesHidden ? 'chevron-left' : 'chevron-right',
                { type: 'togglePanel', panel: 'properties' },
                true,
                { iconOnly: true, iconAction: true, round: false }
            )
        ];
    if (!ui.propertiesHidden || narrow)
        children.push(
            label(
                'pagePropertiesTitle',
                rect(12, 10, Math.max(0, width - (narrow ? 24 : 62)), 34),
                tr('Properties'),
                { weight: 600 }
            )
        );
    return narrow ? children.slice(1) : children;
}
export function splitters(g, y, height, language) {
    return [
        node('Splitter', 'pageLayersSplitter', rect(g.left, y, 10, height), {
            text: translate('Page blocks', language),
            value: g.left,
            min: 140,
            max: Math.min(320, g.left + g.canvasWidth - 360),
            enabled: g.left > 32,
            action: { type: 'panelSize', panel: 'layers' }
        }),
        node(
            'Splitter',
            'pagePropertiesSplitter',
            rect(g.canvasX + g.canvasWidth, y, 10, height),
            {
                text: translate('Properties', language),
                value: g.right,
                min: 240,
                max: Math.min(420, g.right + g.canvasWidth - 360),
                reverse: true,
                enabled: g.right > 32,
                action: { type: 'panelSize', panel: 'properties' }
            }
        )
    ];
}
export function actions(model, ui, language) {
    const ready =
        model.canWrite &&
        !model.busy &&
        !model.uncertain &&
        !model.pendingText &&
        !ui.confirmation;
    const p = Document.path(ui.selected),
        rows = p.length ? Document.siblings(model.document, p) : [];
    return [
        [
            'open',
            'Open saved view',
            'open-in-new',
            !model.dirty && !!model.document.name && !model.busy
        ],
        [
            'duplicate',
            'Duplicate widget',
            'content-copy',
            ready && !ui.preview && !!ui.selected && ui.selection.length < 2
        ],
        [
            'moveUp',
            'Move up',
            'arrow-upward',
            ready && !ui.preview && p.length && p[p.length - 1] > 0
        ],
        [
            'moveDown',
            'Move down',
            'arrow-downward',
            ready &&
                !ui.preview &&
                p.length &&
                p[p.length - 1] < rows.length - 1
        ],
        ['canvasSettings', 'Canvas settings', 'tune', true]
    ].map(([command, title, icon, enabled]) => ({
        command,
        title: translate(title, language),
        icon,
        enabled: !!enabled,
        translate: false
    }));
}
export function toolEvent(command) {
    return command === 'moveUp' || command === 'moveDown'
        ? { type: 'reorder', delta: command === 'moveUp' ? -1 : 1 }
        : { type: command };
}
export function canvasTools(model, ui, width, language, canEdit) {
    const tr = (text) => translate(text, language),
        nodes = [];
    const named = !!model.document.name,
        ready = canEdit && !model.pendingText && !ui.confirmation;
    const pages = model.catalog.map((row) => ({
        value: row.identity,
        label: row.label
    }));
    if (named && !pages.some((page) => page.value === model.document.name))
        pages.unshift({
            value: model.document.name,
            label: model.document.title || model.document.name
        });
    let x = 0,
        y = 0;
    function place(item) {
        item.width = Math.min(item.width, width);
        if (x && x + item.width > width) {
            x = 0;
            y += 38;
        }
        item.x = x;
        item.y = y;
        nodes.push(item);
        x += item.width + 8;
    }
    function action(id, title, icon, event, enabled, extra) {
        const text = tr(title);
        place(
            button(
                id,
                rect(
                    0,
                    0,
                    Math.max(80, buttonWidth(text.length * 8, true)),
                    32
                ),
                text,
                icon,
                event,
                enabled,
                extra
            )
        );
    }
    place(
        node('Choice', 'pageLayoutChoice', rect(0, 0, 260, 32), {
            label: tr('Page layout'),
            value: model.document.name || '',
            options: (named
                ? []
                : [{ value: '', label: tr('Page layout') }]
            ).concat(pages),
            enabled: !model.busy && !model.uncertain,
            action: { type: 'load' }
        })
    );
    action(
        'pageNew',
        'New page',
        'add',
        { type: 'new' },
        ready && !ui.creating,
        { highlighted: !named }
    );
    if (named) {
        action(
            'pagePreviewToggle',
            ui.preview ? 'Back to editing' : 'Clean preview',
            ui.preview ? 'edit' : 'visibility',
            { type: 'preview' },
            !model.busy && !ui.creating && !model.pendingText,
            { highlighted: ui.preview }
        );
        action(
            'pageSourceXml',
            ui.source ? 'Design' : 'XML',
            ui.source ? 'dashboard' : 'code',
            { type: 'sourceXml' },
            true,
            { highlighted: ui.source, toolTip: tr('Source XML') }
        );
        place(
            node(
                'View',
                'pageToolsMenu',
                rect(0, 0, buttonWidth(tr('Actions').length * 8, true), 32),
                {
                    view: 'pageTools',
                    actions: actions(model, ui, language),
                    label: tr('Actions')
                }
            )
        );
    }
    y += 40;
    if (ui.creating) {
        const inline = width >= 760,
            createWidth = buttonWidth(tr('Create draft').length * 8, true),
            w = inline
                ? Math.min(240, (width - createWidth - 144) / 2)
                : (width - 8) / 2;
        nodes.push(
            node('Field', 'pageLayoutName', rect(0, y, w, 32), {
                label: tr('Page name'),
                placeholder: 'my_dashboard',
                text: ui.newName,
                action: { type: 'newName' }
            }),
            node('Field', 'pageLayoutTitle', rect(w + 8, y, w, 32), {
                label: tr('Title'),
                placeholder: tr('Title'),
                text: ui.newTitle,
                action: { type: 'newTitle' }
            }),
            button(
                'pageLayoutCreate',
                rect(
                    inline ? 2 * w + 16 : 0,
                    inline ? y : y + 40,
                    createWidth,
                    32
                ),
                tr('Create draft'),
                'add',
                { type: 'create' },
                canEdit
            ),
            button(
                'pageLayoutCancelNew',
                rect(
                    inline ? 2 * w + createWidth + 24 : createWidth + 8,
                    inline ? y : y + 40,
                    120,
                    32
                ),
                tr('Cancel'),
                'close',
                { type: 'cancelNew' },
                true
            )
        );
        y += inline ? 40 : 80;
    }
    if (named && !ui.source) {
        let offset = 0;
        if (!ui.preview) {
            const current = Document.fingerprint(model.document),
                ready =
                    canEdit &&
                    !model.pendingText &&
                    !ui.confirmation &&
                    ui.historyDocument === current;
            for (const [index, type] of ['undo', 'redo'].entries())
                nodes.push(
                    button(
                        'pageAction_' + type,
                        rect(index * 38, y, 32, 32),
                        tr(type === 'undo' ? 'Undo' : 'Redo'),
                        type,
                        { type },
                        !!(
                            ready &&
                            ui[type === 'undo' ? 'past' : 'future']?.length
                        ),
                        { iconOnly: true }
                    )
                );
            offset = 84;
        }
        const tools = Viewport.controls(
            ui,
            width - offset,
            language,
            !model.busy
        );
        nodes.push(
            node(
                'Box',
                'pageViewportTools',
                rect(offset, y, width - offset, tools.height),
                { children: tools.nodes }
            )
        );
        y += tools.height + 6;
    }
    return { nodes, height: y };
}

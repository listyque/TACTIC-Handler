import { node, rect, label, button } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';
import { listAction } from '../../../controls/lists/tree.ui.mjs';
import * as Document from './page.document.mjs';
import * as Viewport from './page.viewport.mjs';

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
        width = bounds.width;
    const children = [
        button(
            'pageLayersToggle',
            rect(width - 32, 0, 32, 32),
            tr('Page blocks'),
            ui.layersHidden ? 'chevron-right' : 'chevron-left',
            { type: 'togglePanel', panel: 'layers' },
            true,
            { iconOnly: true }
        )
    ];
    if (!ui.layersHidden || narrow)
        children.push(
            label(
                'pageLayersTitle',
                rect(8, 0, width - 44, 32),
                tr('Page blocks'),
                { weight: 600 }
            ),
            node('Choice', 'pageAddWidget', rect(8, 34, width - 16, 32), {
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
                rect(4, 72, width - 8, Math.max(0, bounds.height - 76)),
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
    const children = [
        button(
            'pagePropertiesToggle',
            rect(0, 0, 32, 32),
            translate('Properties', language),
            ui.propertiesHidden ? 'chevron-left' : 'chevron-right',
            { type: 'togglePanel', panel: 'properties' },
            true,
            { iconOnly: true }
        )
    ];
    if (!ui.propertiesHidden || narrow)
        children.push(
            label(
                'pagePropertiesTitle',
                rect(narrow ? 8 : 36, 0, width - 44, 32),
                translate('Properties', language),
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
        ['new', 'New page', 'add', ready],
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
        ['canvasSettings', 'Canvas settings', 'tune', true],
        [
            'preview',
            ui.preview ? 'Back to editing' : 'Clean preview',
            ui.preview ? 'edit' : 'visibility',
            !model.busy && !ui.creating && !model.pendingText
        ]
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
    const sourceWidth = ui.source ? (language === 'ru' ? 148 : 104) : 80;
    const pickerWidth = Math.max(
        80,
        Math.min(
            260,
            width - sourceWidth - (!ui.source && !ui.preview ? 126 : 48)
        )
    );
    nodes.push(
        node('Choice', 'pageLayoutChoice', rect(0, 0, pickerWidth, 32), {
            label: tr('Page layout'),
            value: model.document.name || '',
            options: model.catalog.map((row) => ({
                value: row.identity,
                label: row.label
            })),
            enabled: !model.busy && !model.uncertain,
            action: { type: 'load' }
        }),
        button(
            'pageSourceXml',
            rect(width - sourceWidth - 42, 0, sourceWidth, 32),
            ui.source ? tr('Design') : 'XML',
            ui.source ? 'dashboard' : 'code',
            { type: 'sourceXml' },
            !!model.document.name,
            { highlighted: ui.source, toolTip: tr('Source XML') }
        ),
        node('View', 'pageToolsMenu', rect(width - 32, 0, 32, 32), {
            view: 'pageTools',
            actions: actions(model, ui, language),
            label: tr('Editor tools')
        })
    );
    let y = 40;
    if (ui.creating) {
        const w = Math.max(80, (width - 8) / 2);
        nodes.push(
            node('Field', 'pageLayoutName', rect(0, y, w, 32), {
                label: tr('Page name'),
                placeholder: 'my_dashboard',
                text: ui.newName,
                action: { type: 'newName' }
            }),
            node('Field', 'pageLayoutTitle', rect(w + 8, y, w, 32), {
                label: tr('Title'),
                text: ui.newTitle,
                action: { type: 'newTitle' }
            }),
            button(
                'pageLayoutCreate',
                rect(0, y + 40, 160, 32),
                tr('Create draft'),
                'add',
                { type: 'create' },
                canEdit
            ),
            button(
                'pageLayoutCancelNew',
                rect(168, y + 40, 120, 32),
                tr('Cancel'),
                'close',
                { type: 'cancelNew' },
                true
            )
        );
        y += 80;
    }
    if (!ui.source) {
        const tools = Viewport.controls(ui, width, language, !model.busy);
        nodes.push(
            node('Box', 'pageViewportTools', rect(0, y, width, tools.height), {
                children: tools.nodes
            })
        );
        y += tools.height + 6;
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
                        rect(width - sourceWidth - 120 + index * 38, 0, 32, 32),
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
        }
    }
    return { nodes, height: y };
}

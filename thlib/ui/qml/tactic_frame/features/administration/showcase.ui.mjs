import { describe as preview } from '../../controls/showcase.examples.mjs';
import * as Extended from './showcase.examples.mjs';
export { cell, models } from './showcase.examples.mjs';
// Local examples of shipped controls; no project, transport or persistent draft.
import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { lineHeights, spacing } from '../../core/foundation.mjs';
import { listAction } from '../../controls/lists/tree.ui.mjs';
export { catalogue } from '../../controls/catalog.data.mjs';

export const live = [
    'typography',
    'headers',
    'colors',
    'icons',
    'buttons',
    'toggles',
    'text-fields',
    'choices',
    'numbers',
    'dates',
    'user-choice',
    'pickers',
    'tabs',
    'badges',
    'lists',
    'charts'
].concat(Extended.families);
export const states = [
    'default',
    'disabled',
    'readonly',
    'error',
    'long',
    'loading',
    'empty',
    'selected'
];
const stateLabels = [
    'Default',
    'Disabled',
    'Read only',
    'Error',
    'Long text',
    'Loading',
    'Empty',
    'Selected'
];

export function initial() {
    return {
        family: 'typography',
        query: '',
        category: '',
        state: 'default',
        code: false,
        text: 'Robot Arm',
        area: 'A local example',
        checked: true,
        choice: 'model',
        user: 'admin',
        date: '2026-11-02',
        color: '#78a6c4',
        icon: 'save',
        number: '42',
        row: 'assets',
        tab: 'overview',
        search: '',
        menuChecked: true,
        dialogOpen: false,
        progress: 42,
        cells: {},
        revision: 0,
        split: 0.5,
        files: [],
        fit: 'contain',
        previewSelected: false,
        editorText: 'def example():\n    return 42\n',
        graphPositions: [],
        graphSelected: [],
        resetRevision: 0,
        presses: 0,
        activations: 0,
        cancels: 0,
        ime: '',
        surface: 'cards',
        taskDraft: 'Review the model',
        savedTaskDraft: '',
        last: ''
    };
}

export function transition(model, event, catalog) {
    const next = Object.assign({}, model);
    if (
        event.type === 'family' &&
        catalog.families.some((f) => f.id === event.value)
    )
        Object.assign(next, { family: event.value, dialogOpen: false });
    else if (
        event.type === 'category' &&
        (event.value === '' ||
            catalog.categories.some((c) => c.id === event.value))
    )
        next.category = event.value;
    else if (event.type === 'state' && states.includes(event.value))
        Object.assign(next, { state: event.value, dialogOpen: false });
    else if (event.type === 'query')
        next.query = String(event.value || '').slice(0, 200);
    else if (event.type === 'code') next.code = !model.code;
    else if (event.type === 'reset')
        return Object.assign(initial(), {
            resetRevision: model.resetRevision + 1,
            family: model.family,
            query: model.query,
            category: model.category
        });
    else if (
        event.type.startsWith('sample') ||
        ['search', 'searchAccept', 'searchSubmit', 'surface'].includes(
            event.type
        )
    ) {
        if (
            ['disabled', 'readonly', 'loading'].includes(model.state) &&
            event.type !== 'sampleDialog'
        )
            return model;
        next.last = event.type;
        if (event.type === 'search')
            next.search = String(event.value || '').slice(0, 200);
        else if (event.type === 'searchAccept')
            next.search = String(event.value.title || '');
        else if (event.type === 'sampleMenu') {
            next.last = String(event.value);
            if (event.value === 'toggle') next.menuChecked = !model.menuChecked;
        } else if (event.type === 'sampleDialogOpen') next.dialogOpen = true;
        else if (event.type === 'sampleDialog') {
            next.dialogOpen = false;
            next.last = String(event.value);
        } else if (event.type === 'sampleAdvance')
            next.progress = Math.min(100, model.progress + 10);
        else if (event.type === 'sampleRetry') {
            next.progress = 0;
            next.state = 'default';
        } else if (event.type === 'sampleCell') {
            next.cells = Object.assign({}, model.cells);
            next.cells[event.row + ':' + event.column] = event.value;
            next.revision++;
        } else if (event.type === 'sampleSplit' && event.width > 0)
            next.split = Math.max(
                0,
                Math.min(1, Number(event.value) / event.width)
            );
        else if (event.type === 'sampleCollapse')
            next.split = model.split < 0.2 ? 0.5 : 0;
        else if (event.type === 'sampleFit')
            next.fit = event.value === 'cover' ? 'cover' : 'contain';
        else if (event.type === 'samplePreviewSelect')
            next.previewSelected = !model.previewSelected;
        else if (event.type === 'sampleFiles')
            next.files = fileLabels(event.value);
        else if (event.type === 'sampleFilesClear') next.files = [];
        else if (event.type === 'sampleEditor')
            next.editorText = String(event.value);
        else if (event.type === 'sampleGraphSelect')
            next.graphSelected = Array.isArray(event.value) ? event.value : [];
        else if (event.type === 'sampleGraphMove')
            next.graphPositions = Array.isArray(event.value) ? event.value : [];
        else if (event.type === 'sampleGraphReset') {
            next.resetRevision++;
            next.graphSelected = [];
            next.graphPositions = [];
        } else if (event.type === 'sampleGraph' && event.value) {
            if (event.value.type === 'clear') next.graphSelected = [];
            if (event.value.type === 'selectNodes')
                next.graphSelected = event.value.identities || [];
            else if (event.value.type === 'moveNodes') {
                const positions = event.value.positions || [];
                next.graphPositions = model.graphPositions
                    .filter(
                        (old) =>
                            !positions.some(
                                (row) => row.identity === old.identity
                            )
                    )
                    .concat(positions);
            }
        } else if (event.type === 'sampleActivate') next.activations++;
        else if (event.type === 'samplePress') next.presses++;
        else if (event.type === 'sampleCancel') next.cancels++;
        else if (event.type === 'sampleIME') next.ime = String(event.value);
        else if (
            event.type === 'surface' &&
            ['cards', 'compact', 'workspace'].includes(event.value)
        )
            next.surface = event.value;
        else if (event.type === 'sampleTaskDraft')
            next.taskDraft = String(event.value);
        else if (event.type === 'sampleTaskSave')
            next.savedTaskDraft = model.taskDraft;
    } else if (
        [
            'text',
            'area',
            'checked',
            'choice',
            'user',
            'date',
            'color',
            'icon',
            'number',
            'row',
            'tab'
        ].includes(event.type)
    )
        next[event.type] = event.value;
    else next.last = event.type;
    return next;
}

// Browser File handles and native URLs remain in their respective owners; no uploads.
export function fileLabels(values) {
    if (!Array.isArray(values)) return [];
    return values
        .slice(0, 100)
        .map((value) => {
            const raw = typeof value === 'string' ? value : value && value.name;
            if (!raw || (typeof value === 'string' && !raw.startsWith('file:')))
                return null;
            let name = String(raw).split(/[\\/]/).pop();
            try {
                name = decodeURIComponent(name);
            } catch (_) {}
            return { name: name.slice(0, 240) };
        })
        .filter(Boolean);
}

export function families(catalog, model, language) {
    const query = model.query.trim().toLocaleLowerCase();
    const groups = catalog.categories.map((c) => c.id);
    const foundations = ['typography', 'colors', 'headers', 'icons'];
    return catalog.families
        .filter(
            (f) =>
                (!model.category || f.category === model.category) &&
                (!query ||
                    [f.id, f.title, f.label, ...f.native, ...f.vue, ...f.tokens]
                        .join(' ')
                        .toLocaleLowerCase()
                        .includes(query))
        )
        .sort(
            (a, b) =>
                groups.indexOf(a.category) - groups.indexOf(b.category) ||
                (a.category === 'foundations'
                    ? foundations.indexOf(a.id) - foundations.indexOf(b.id)
                    : catalog.families.indexOf(a) - catalog.families.indexOf(b))
        )
        .map((f) => ({
            id: f.id,
            title: language === 'ru' ? f.title : f.label,
            level: f.level,
            available: live.includes(f.id),
            count: f.native.length + f.vue.length
        }));
}

export function row(list, record, model, language) {
    const tr = (text) => translate(text, language);
    const result = listAction(
        'showcaseFamily_' + record.id,
        rect(0, 0, list.width, 48),
        record.title,
        '',
        { type: 'family', value: record.id },
        true,
        { selected: model.family === record.id }
    );
    result.children[0].height = 27;
    result.children.push(
        label(
            'showcaseFamilyState_' + record.id,
            rect(12, 27, list.width - 24, 16),
            tr(record.available ? 'Live example' : 'Catalogue entry'),
            { fontRole: 'caption', color: 'secondaryText' }
        )
    );
    return { nodes: [result], width: list.width, height: 48 };
}

export function describe(model, catalog, width, height, language = 'en') {
    const tr = (text) => translate(text, language),
        narrow = width < 740,
        nav = narrow ? 0 : 228,
        gap = narrow ? spacing.none : spacing.content;
    const x = nav + gap,
        w = Math.max(0, width - x),
        top = narrow ? 96 : 48;
    const visible = families(catalog, model, language),
        family =
            catalog.families.find((f) => f.id === model.family) ||
            catalog.families[0];
    const nodes = [];
    nodes.push(
        node('Field', 'showcaseSearch', rect(0, 0, narrow ? width : nav, 36), {
            text: model.query,
            label: tr('Search components'),
            placeholder: tr('Search components'),
            enabled: true,
            action: { type: 'query' }
        })
    );
    const groupOptions = [
        { value: '', label: tr('All component groups') },
        ...catalog.categories.map((c) => ({
            value: c.id,
            label: c.title[language === 'ru' ? 'ru' : 'en']
        }))
    ];
    if (!narrow) {
        nodes.push(
            node('Choice', 'showcaseCategory', rect(0, 44, nav, 36), {
                value: model.category,
                options: groupOptions,
                enabled: true,
                label: tr('Category'),
                action: { type: 'category' }
            })
        );
        nodes.push(
            node(
                'List',
                'showcaseFamilies',
                rect(0, 88, nav, Math.max(0, height - 88)),
                {
                    source: 'families',
                    fields: ['id', 'title', 'available', 'count', 'level'],
                    rowHeight: 52,
                    selectedKey: model.family,
                    keyField: 'id',
                    resetKey: model.query + '|' + model.category
                }
            )
        );
    } else
        nodes.push(
            node(
                'Choice',
                'showcaseFamilyChoice',
                rect(0, 44, Math.max(0, width - 168), 36),
                {
                    value: model.family,
                    options: visible.map((f) => ({
                        value: f.id,
                        label: f.title
                    })),
                    enabled: true,
                    label: tr('Component showcase'),
                    action: { type: 'family' }
                }
            )
        );
    const controlsX = narrow ? Math.max(0, width - 160) : x;
    nodes.push(
        node(
            'Choice',
            'showcaseState',
            rect(controlsX, narrow ? 44 : 0, narrow ? 120 : 160, 36),
            {
                value: model.state,
                options: states.map((value, i) => ({
                    value,
                    label: tr(stateLabels[i])
                })),
                label: tr('Component state'),
                enabled: true,
                action: { type: 'state' }
            }
        )
    );
    nodes.push(
        button(
            'showcaseReset',
            rect(narrow ? width - 36 : x + 168, narrow ? 44 : 0, 36, 36),
            tr('Reset'),
            'refresh',
            { type: 'reset' },
            true,
            { iconOnly: true }
        )
    );
    if (!narrow)
        nodes.push(
            button(
                'showcaseCode',
                rect(Math.max(x + 212, width - 136), 0, 136, 36),
                tr(model.code ? 'Preview' : 'Code example'),
                'code',
                { type: 'code' },
                true,
                { selected: model.code, radio: true }
            )
        );
    const content = [],
        inner = Math.max(0, w - 32),
        titleHeight = narrow ? lineHeights.hero * 2 : 46;
    content.push(
        label(
            'showcaseTitle',
            rect(16, 12, inner, titleHeight),
            language === 'ru' ? family.title : family.label,
            {
                fontRole: 'hero',
                weight: 600,
                wrap: true,
                maxLines: 2,
                verticalAlign: 'top',
                role: 'heading',
                level: 2
            }
        )
    );
    content.push(
        label(
            'showcaseScope',
            rect(16, titleHeight + 16, inner, 32),
            tr(
                live.includes(family.id)
                    ? 'Local demo; project data stays unchanged'
                    : 'Standalone example not added yet'
            ),
            { fontRole: 'secondary', color: 'secondaryText', wrap: true }
        )
    );
    let y = titleHeight + 64;
    if (!visible.length) {
        content.push(
            label(
                'showcaseNoResults',
                rect(16, y, inner, 48),
                tr('No matching components'),
                { wrap: true }
            )
        );
        y += 64;
    } else if (live.includes(family.id)) {
        const p = Extended.families.includes(family.id)
            ? Extended.describe(model, family.id, inner, language)
            : preview(model, family.id, inner, language);
        if (p.code) {
            if (narrow)
                content.push(
                    button(
                        'showcaseCode',
                        rect(16, y, Math.min(inner, 160), 36),
                        tr(model.code ? 'Preview' : 'Code example'),
                        'code',
                        { type: 'code' },
                        true,
                        { selected: model.code, radio: true }
                    )
                );
            if (narrow) y += 48;
            if (model.code) {
                content.push(
                    node(
                        'Code',
                        'showcaseCodeSource',
                        rect(16, y, inner, 260),
                        {
                            text: p.code,
                            language: 'javascript',
                            readOnly: true,
                            enabled: true
                        }
                    )
                );
                y += 276;
            }
        }
        if (!model.code || !p.code) {
            content.push(
                node('Box', 'showcasePreview', rect(16, y, inner, p.height), {
                    background: 'transparent',
                    children: p.nodes,
                    clip: false
                })
            );
            y += p.height + 12;
        }
    }
    for (const [title, values] of [
        ['Native controls', family.native],
        ['Vue controls', family.vue]
    ]) {
        content.push(
            label('showcaseOwner_' + title, rect(16, y, inner, 22), tr(title), {
                fontRole: 'secondary',
                weight: 600
            })
        );
        y += 26;
        const text = values.join(' · ') || '—',
            h = Math.max(
                24,
                Math.ceil(text.length / Math.max(12, inner / 7)) * 18
            );
        content.push(
            label('showcaseNames_' + title, rect(16, y, inner, h), text, {
                wrap: true,
                fontRole: 'secondary',
                color: 'secondaryText'
            })
        );
        y += h + 20;
    }
    if (model.last) {
        content.push(
            label(
                'showcaseEvent',
                rect(16, y, inner, 28),
                tr('Action') + ': ' + model.last,
                { fontRole: 'caption', color: 'secondaryText' }
            )
        );
        y += 40;
    }
    nodes.push(
        node(
            'Box',
            'showcaseSurface',
            rect(x, top, w, Math.max(0, height - top)),
            { background: 'surfaceContainerLowest', radius: 8 }
        )
    );
    nodes.push(
        node(
            'Scroll',
            'showcaseContent',
            rect(
                x,
                top,
                Math.max(0, w - (y + 8 > height - top ? 12 : 0)),
                Math.max(0, height - top)
            ),
            { contentHeight: y + 8, resetKey: model.family, children: content }
        )
    );
    return { nodes };
}

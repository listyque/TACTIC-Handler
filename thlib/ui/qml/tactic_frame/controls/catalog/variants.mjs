// Standalone, neutral examples. These records are shared by the actual Qt/Vue hosts.
import { node, rect, label } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { header } from '../display/surfaces.ui.mjs';
import * as BaseCatalog from '../catalog.ui.mjs';
import { users, choices } from '../catalog.ui.mjs';
import { filterGeometry } from '../display/chips.mjs';
import { controls } from '../../core/foundation.mjs';

// The edge stripe distinguishes a real crop from a stretched source texture.
const exampleImage =
    'data:image/svg+xml,' +
    encodeURIComponent(
        '<svg xmlns="http://www.w3.org/2000/svg" width="120" height="60"><path fill="#cc6655" d="M0 0h60v60H0z"/><path fill="#5588aa" d="M60 0h60v60H60z"/><path fill="#55aa66" d="M0 0h12v60H0z"/></svg>'
    );

function sample(id, family, kind, properties = {}, height = 36) {
    return { id, family, kind, properties, height };
}

export const directKinds = [
    'Icon',
    'Grid',
    'Graph',
    'Code',
    'tree',
    'Button',
    'CheckBox',
    'Switch',
    'Field',
    'Area',
    'Choice',
    'DateChoice',
    'UserChoice',
    'Preview',
    'ColorChoice',
    'IconChoice',
    'header',
    'Scroll',
    'Splitter'
];

export const examples = [
    sample(
        'icon-material',
        'icons',
        'Icon',
        { icon: 'material-design:account', color: 'action' },
        24
    ),
    sample(
        'icon-solid',
        'icons',
        'Icon',
        { icon: 'fontawesome-solid:user', color: 'action' },
        24
    ),
    sample(
        'icon-outline',
        'icons',
        'Icon',
        { icon: 'fontawesome-outline:user', color: 'action' },
        24
    ),
    sample(
        'icon-fluent',
        'icons',
        'Icon',
        { icon: 'fluent-regular:person', color: 'action' },
        24
    ),
    sample(
        'icon-fluent-filled',
        'icons',
        'Icon',
        { icon: 'fluent-filled:person', color: 'action' },
        24
    ),
    sample(
        'icon-small',
        'icons',
        'Icon',
        { icon: 'save', color: 'secondaryText' },
        16
    ),
    sample(
        'icon-large',
        'icons',
        'Icon',
        { icon: 'save', color: 'action' },
        40
    ),
    sample('tree', 'lists', 'tree', {}, 280),
    sample('table', 'tables', 'Grid', {}, 280),
    sample('table-readonly', 'tables', 'Grid', { readOnly: true }, 280),
    sample('graph', 'graphs', 'Graph', {}, 320),
    sample('graph-readonly', 'graphs', 'Graph', { readOnly: true }, 320),
    sample(
        'code',
        'editors',
        'Code',
        { value: 'def example():\n    return 42\n' },
        300
    ),
    sample(
        'code-readonly',
        'editors',
        'Code',
        { value: 'def example():\n    return 42\n', readOnly: true },
        300
    ),
    sample('button', 'buttons', 'Button', { text: 'Save', icon: 'save' }),
    sample('button-primary', 'buttons', 'Button', {
        text: 'Create',
        icon: 'add',
        highlighted: true
    }),
    sample('button-tonal', 'buttons', 'Button', { text: 'Apply', tonal: true }),
    sample('button-danger', 'buttons', 'Button', {
        text: 'Delete',
        icon: 'delete',
        destructive: true
    }),
    sample('button-filled-danger', 'buttons', 'Button', {
        text: 'Delete',
        icon: 'delete',
        destructive: true,
        highlighted: true
    }),
    sample('button-icon', 'buttons', 'Button', {
        text: 'Refresh',
        icon: 'refresh',
        iconOnly: true
    }),
    sample('button-badge-zero', 'buttons', 'counter', { value: 0 }),
    sample('button-badge', 'buttons', 'counter', { value: 4 }),
    sample('button-badge-overflow', 'buttons', 'counter', { value: 132 }),
    sample('button-disclosure', 'buttons', 'disclosure', { value: false }),
    sample('button-preview', 'buttons', 'previewNavigation', { value: 0 }),
    sample('button-send', 'buttons', 'send', { value: false }),
    sample('checkbox', 'toggles', 'CheckBox', {
        text: 'Enabled',
        value: false
    }),
    sample('checkbox-checked', 'toggles', 'CheckBox', {
        text: 'Enabled',
        value: true
    }),
    sample(
        'checkbox-wrapped',
        'toggles',
        'CheckBox',
        {
            text: 'Very long example item title that wraps in a narrow viewport',
            wrapText: true,
            value: true
        },
        64
    ),
    sample('checkbox-mixed', 'toggles', 'CheckBox', {
        text: 'Enabled',
        value: true,
        mixed: true
    }),
    sample('checkbox-compact', 'toggles', 'CheckBox', {
        text: 'Enabled',
        value: true,
        compact: true
    }),
    sample('checkbox-prominent', 'toggles', 'CheckBox', {
        text: 'Enabled',
        value: false,
        prominent: true
    }),
    sample('switch-off', 'toggles', 'Switch', {
        text: 'Enabled',
        value: false
    }),
    sample('switch-on', 'toggles', 'Switch', { text: 'Enabled', value: true }),
    sample('segments', 'toggles', 'segments', { value: 'model' }),
    sample('segments-icons', 'toggles', 'segments', {
        value: 'model',
        iconOnly: true
    }),
    sample('segments-outline', 'toggles', 'segments', {
        value: 'model',
        outlined: true
    }),
    sample('segments-disabled-option', 'toggles', 'segments', {
        value: 'model',
        disabledOption: true,
        dataLabels: true
    }),
    sample('field', 'text-fields', 'Field', {
        value: 'Robot Arm',
        label: 'Name'
    }),
    sample('field-empty', 'text-fields', 'Field', {
        value: '',
        label: 'Name',
        placeholder: 'Name'
    }),
    sample('field-password', 'text-fields', 'Field', {
        value: 'private example',
        label: 'Password',
        password: true
    }),
    sample('field-readonly', 'text-fields', 'Field', {
        value: 'Read only',
        label: 'Name',
        readOnly: true
    }),
    sample('field-error', 'text-fields', 'Field', {
        value: 'Invalid value',
        label: 'Name',
        error: true
    }),
    sample('field-inline', 'text-fields', 'Field', {
        value: 'Robot Arm',
        label: 'Name',
        tableCell: true
    }),
    sample(
        'text-area',
        'text-fields',
        'Area',
        { value: 'First line\nSecond line', label: 'Description' },
        100
    ),
    sample('search', 'search', 'search', { value: 'Robot' }),
    sample('search-empty', 'search', 'search', { value: '' }),
    sample('search-suggestions', 'search', 'search', {
        value: 'Robot',
        suggestions: true
    }),
    sample('choice', 'choices', 'Choice', { value: 'model' }),
    sample('choice-empty', 'choices', 'Choice', { value: '' }),
    sample('choice-editable', 'choices', 'Choice', {
        value: 'custom_process',
        editable: true
    }),
    sample('choice-disabled-option', 'choices', 'Choice', {
        value: 'model',
        disabledOption: true
    }),
    sample('choice-icons', 'choices', 'Choice', {
        value: 'model',
        choiceIcons: true
    }),
    sample('choice-status', 'choices', 'status', { value: 'model' }, 28),
    sample('packed-choices', 'choices', 'packedChoices', { value: '' }, 280),
    sample('integer', 'numbers', 'spin', {
        value: 5,
        min: 0,
        max: 10,
        step: 1,
        decimals: 0
    }),
    sample('decimal', 'numbers', 'spin', {
        value: 1.25,
        min: -2,
        max: 3,
        step: 0.25,
        decimals: 2
    }),
    sample('integer-min', 'numbers', 'spin', {
        value: 0,
        min: 0,
        max: 10,
        step: 1,
        decimals: 0
    }),
    sample('integer-max', 'numbers', 'spin', {
        value: 10,
        min: 0,
        max: 10,
        step: 1,
        decimals: 0
    }),
    sample(
        'slider',
        'numbers',
        'slider',
        { value: 50, min: 0, max: 100, step: 1 },
        26
    ),
    sample(
        'slider-step',
        'numbers',
        'slider',
        { value: 50, min: 0, max: 100, step: 5 },
        26
    ),
    sample(
        'slider-fixed',
        'numbers',
        'slider',
        { value: 5, min: 5, max: 5, step: 1 },
        26
    ),
    sample('date', 'dates', 'DateChoice', {
        value: '2024-02-29',
        includeTime: false
    }),
    sample('datetime', 'dates', 'DateChoice', {
        value: '2024-02-29T13:14',
        includeTime: true
    }),
    sample('date-early-year', 'dates', 'DateChoice', {
        value: '0099-01-01',
        includeTime: false
    }),
    sample('date-invalid', 'dates', 'DateChoice', {
        value: '2023-02-29',
        includeTime: false
    }),
    sample('date-empty', 'dates', 'DateChoice', {
        value: '',
        includeTime: false
    }),
    sample('user', 'user-choice', 'UserChoice', { value: 'admin' }),
    sample('user-empty', 'user-choice', 'UserChoice', { value: '' }),
    sample('users-multiple', 'user-choice', 'users', { value: ['admin'] }, 300),
    sample(
        'avatar-initials',
        'identity',
        'Preview',
        { initials: 'A', round: true, outlined: true, accent: '#557f75' },
        40
    ),
    sample(
        'avatar-two-initials',
        'identity',
        'Preview',
        { initials: 'TA', round: true, outlined: true, accent: '#557f75' },
        40
    ),
    sample(
        'avatar-fallback',
        'identity',
        'Preview',
        { icon: 'person', round: true, outlined: true, accent: '#557f75' },
        40
    ),
    sample('identity', 'identity', 'identity', { value: 'admin' }, 40),
    sample(
        'identity-retired',
        'identity',
        'identity',
        { value: 'admin', retired: true },
        40
    ),
    sample(
        'identity-emphasized',
        'identity',
        'identity',
        { value: 'admin', emphasized: true, avatarSize: 56 },
        56
    ),
    sample('user-group', 'identity', 'userGroup', { value: 'Artists' }, 34),
    sample(
        'user-group-compact',
        'identity',
        'userGroup',
        { value: 'Artists', compact: true },
        28
    ),
    sample(
        'user-group-empty',
        'identity',
        'userGroup',
        { value: 'Ungrouped' },
        34
    ),
    sample(
        'profile-info',
        'identity',
        'profileInfo',
        { value: 'Administrator' },
        40
    ),
    sample('color', 'pickers', 'ColorChoice', { value: '#78a6c4' }),
    sample('icon-choice', 'pickers', 'IconChoice', { value: 'save' }),
    sample('emoji', 'pickers', 'emoji', { value: '' }),
    sample('image-picker', 'pickers', 'image', { value: '' }, 220),
    sample('accent-presets', 'pickers', 'presets', { value: 'blue' }, 48),
    sample(
        'preview-square',
        'previews',
        'Preview',
        { initials: 'RA', accent: '#557f75', round: false, outlined: false },
        96
    ),
    sample(
        'preview-outline',
        'previews',
        'Preview',
        { initials: 'RA', accent: '#557f75', round: false, outlined: true },
        96
    ),
    sample(
        'preview-broken',
        'previews',
        'Preview',
        {
            initials: 'RA',
            source: 'missing-example.png',
            accent: '#557f75',
            round: false
        },
        96
    ),
    sample(
        'preview-loading',
        'previews',
        'Preview',
        { loading: true, source: 'pending-preview:example' },
        96
    ),
    sample(
        'preview-photo',
        'previews',
        'Preview',
        { source: exampleImage, round: false },
        96
    ),
    sample(
        'preview-contain',
        'previews',
        'Preview',
        { source: exampleImage, round: false, fit: 'contain' },
        96
    ),
    sample(
        'preview-selected',
        'previews',
        'Preview',
        { source: exampleImage, round: false, selected: true },
        96
    ),
    sample(
        'avatar-photo',
        'identity',
        'Preview',
        { source: exampleImage, round: true },
        40
    ),
    sample('chip', 'badges', 'chip', { value: 4 }, 30),
    sample(
        'chip-clickable',
        'badges',
        'chip',
        { value: 4, clickable: true },
        30
    ),
    sample('chip-compact', 'badges', 'chip', { value: 4, compact: true }, 24),
    sample('status-chip', 'badges', 'statusChip', { value: 'Ready' }, 24),
    sample(
        'status-chip-dense',
        'badges',
        'statusChip',
        { value: 'Ready', dense: true },
        20
    ),
    sample(
        'status-chip-action',
        'badges',
        'statusChip',
        { value: 'Ready', interactive: true },
        24
    ),
    sample('reaction', 'badges', 'reaction', { value: false, count: 1 }, 28),
    sample(
        'reaction-count',
        'badges',
        'reaction',
        { value: false, count: 4 },
        28
    ),
    sample(
        'reaction-checked',
        'badges',
        'reaction',
        { value: true, count: 4 },
        28
    ),
    sample('filter-chip', 'badges', 'filterChip', { value: false }, 32),
    sample('filter-chip-checked', 'badges', 'filterChip', { value: true }, 32),
    sample(
        'filter-chip-subtle',
        'badges',
        'filterChip',
        { value: true, subtle: true },
        32
    ),
    sample(
        'filter-chip-marker',
        'badges',
        'filterChip',
        { value: true, marker: true },
        32
    ),
    sample(
        'filter-chip-emphasis',
        'badges',
        'filterChip',
        { value: true, emphasis: 1 },
        filterGeometry(1).height
    ),
    sample('tab', 'tabs', 'tab', { value: false }),
    sample('tab-current', 'tabs', 'tab', { value: true }),
    sample('header', 'headers', 'header', { subtitle: 'Description' }, 60),
    sample(
        'header-back',
        'headers',
        'header',
        { back: true, subtitle: 'Description' },
        60
    ),
    sample(
        'header-actions',
        'headers',
        'header',
        {
            actions: [
                { label: 'Refresh', icon: 'refresh', command: 'refresh' },
                { label: 'Actions', icon: 'more', command: 'menu' }
            ]
        },
        60
    ),
    sample('editor-panel', 'headers', 'editorPanel', {}, 160),
    sample('configuration-section', 'headers', 'configurationSection', {}, 160),
    sample('section-label', 'headers', 'sectionLabel', {}, 24),
    sample(
        'info-values',
        'headers',
        'infoValues',
        {
            items: [
                { label: 'Type', value: 'Asset' },
                { label: 'Version', value: 'v003' }
            ]
        },
        16
    ),
    sample('field-frame', 'headers', 'fieldFrame', { value: 'Robot Arm' }, 150),
    sample(
        'field-frame-required',
        'headers',
        'fieldFrame',
        { value: 'Robot Arm', required: true },
        150
    ),
    sample(
        'field-frame-error',
        'headers',
        'fieldFrame',
        { value: '', error: true },
        180
    ),
    sample(
        'field-frame-readonly',
        'headers',
        'fieldFrame',
        { value: 'Robot Arm', readOnly: true },
        180
    ),
    sample('list-item', 'lists', 'listItem', { value: 'Example item' }, 72),
    sample(
        'list-item-selected',
        'lists',
        'listItem',
        { value: 'Example item', selected: true },
        72
    ),
    sample(
        'list-item-badge',
        'lists',
        'listItem',
        { value: 'Example item', badge: true },
        72
    ),
    sample(
        'list-item-long',
        'lists',
        'listItem',
        {
            value: 'Very long example item title that wraps in a narrow viewport',
            wrapTitle: true
        },
        100
    ),
    sample('menu', 'menus', 'menu', { value: '' }),
    sample('menu-checks', 'menus', 'menu', { value: '', checkable: true }),
    sample('busy', 'feedback', 'busy', { value: true }, 24),
    sample('progress', 'feedback', 'progress', { value: 0.5 }, 4),
    sample('progress-empty', 'feedback', 'progress', { value: 0 }, 4),
    sample('progress-complete', 'feedback', 'progress', { value: 1 }, 4),
    sample(
        'progress-indeterminate',
        'feedback',
        'progress',
        { value: null },
        4
    ),
    sample('loading-overlay', 'feedback', 'loadingOverlay', {}, 220),
    sample(
        'loading-cancellable',
        'feedback',
        'loadingOverlay',
        { cancellable: true },
        220
    ),
    sample('empty', 'feedback', 'empty', { value: '' }, 180),
    sample('error-retry', 'feedback', 'empty', { value: '', error: true }, 220),
    sample(
        'drop-target',
        'drag-files',
        'drop',
        { value: '', accepted: true },
        180
    ),
    sample(
        'drop-rejected',
        'drag-files',
        'drop',
        { value: '', accepted: false },
        180
    ),
    sample(
        'markdown',
        'typography',
        'markdown',
        {
            value: '# Example\n\n**Bold** and a [link](https://example.org).\n\n- First item\n- Second item'
        },
        200
    ),
    sample('middle-elide', 'typography', 'elide', {
        value: 'D:/very/long/project/path/to/production/scene-file.ext'
    }),
    sample('setting-row', 'scroll-layout', 'setting', { value: true }, 100),
    sample('flow', 'scroll-layout', 'flow', { value: '' }, 150),
    sample('scroll-vertical', 'scroll-layout', 'Scroll', {}, 280),
    sample(
        'scroll-horizontal',
        'scroll-layout',
        'Scroll',
        { horizontal: true },
        120
    ),
    sample('scroll-both', 'scroll-layout', 'Scroll', { both: true }, 280),
    sample(
        'splitter-vertical',
        'scroll-layout',
        'Splitter',
        { value: 50 },
        160
    ),
    sample(
        'splitter-horizontal',
        'scroll-layout',
        'Splitter',
        { value: 50, horizontal: true },
        10
    )
];

export function find(id) {
    const result = examples.find((example) => example.id === id);
    if (!result) throw Error('Unknown control example: ' + id);
    return result;
}

export function initial(id) {
    const example = find(id);
    return Object.assign(BaseCatalog.initial(), {
        id,
        value:
            example.properties.value === undefined
                ? ''
                : example.properties.value,
        cells: {},
        graphPositions: [],
        graphSelected: [],
        events: []
    });
}

export function transition(model, action) {
    const result = BaseCatalog.transition(model, action);
    if (action.type === 'cell')
        result.cells = Object.assign({}, model.cells, {
            [action.row + ':' + action.column]: action.value
        });
    if (action.value !== undefined) result.value = action.value;
    if (action.type === 'graph' && action.value) {
        if (action.value.type === 'selectNodes')
            result.graphSelected = action.value.identities;
        if (action.value.type === 'moveNodes')
            result.graphPositions = action.value.positions;
    }
    return result;
}

export function options(example) {
    return choices.map((choice, index) =>
        Object.assign({}, choice, {
            label:
                example.properties.dataLabels && index === 0
                    ? 'Enabled'
                    : choice.label,
            translate: !example.properties.dataLabels,
            enabled: !(example.properties.disabledOption && index === 1),
            disabled: !!(example.properties.disabledOption && index === 1),
            icon:
                example.properties.choiceIcons || example.kind === 'segments'
                    ? ['view-list', 'edit', 'publish'][index]
                    : '',
            color: ['#ce6868', '#7b85ca', '#55a9ad'][index]
        })
    );
}

export function describe(
    model,
    width,
    height,
    language = 'en',
    state = 'idle'
) {
    const example = find(model.id);
    const tr = (text) => translate(text, language);
    const bounds = rect(20, 64, Math.max(0, width - 40), example.height);
    if (example.kind === 'Preview' || example.kind === 'Icon')
        bounds.width = bounds.height;
    if (example.kind === 'chip') bounds.width = 140;
    if (['statusChip', 'reaction'].indexOf(example.kind) >= 0)
        bounds.width = 140;
    if (example.kind === 'filterChip') bounds.width = 220;
    if (example.kind === 'Splitter' && !example.properties.horizontal)
        bounds.width = 10;
    if (example.kind === 'busy') bounds.width = bounds.height;
    if (
        ['counter', 'disclosure', 'emoji', 'menu', 'send'].indexOf(
            example.kind
        ) >= 0
    )
        bounds.width = 36;
    if (example.kind === 'previewNavigation') {
        bounds.width = 40;
        bounds.height = 84;
    }
    if (example.properties.iconOnly && example.kind === 'Button')
        bounds.width = 36;
    const values = Object.assign({}, example.properties, {
        enabled: state !== 'disabled' && state !== 'loading',
        readOnly: !!example.properties.readOnly || state === 'readonly',
        action: { type: 'change' },
        value: model.value,
        text:
            ['Field', 'Area', 'DateChoice'].indexOf(example.kind) >= 0
                ? String(model.value)
                : tr(example.properties.text || ''),
        label: tr(example.properties.label || 'Name'),
        placeholder: tr(example.properties.placeholder || ''),
        checked: !!model.value,
        mixed: !!example.properties.mixed && !model.events.length,
        options: example.kind === 'UserChoice' ? users : options(example),
        users,
        error: example.properties.error || state === 'error',
        language
    });
    if (example.kind === 'CheckBox') {
        const indicator = values.prominent
            ? controls.checkBox.prominentIndicator
            : values.compact
              ? controls.checkBox.compactIndicator
              : controls.checkBox.indicator;
        const spacing = values.compact
            ? controls.checkBox.compactSpacing
            : controls.checkBox.spacing;
        values.children = [
            label(
                'checkLabel',
                rect(
                    indicator + spacing,
                    0,
                    Math.max(0, bounds.width - indicator - spacing),
                    bounds.height
                ),
                values.text,
                {
                    fontRole: values.compact ? 'secondary' : 'body',
                    wrap: !!values.wrapText,
                    color: values.enabled ? 'primaryText' : 'disabledText'
                }
            )
        ];
    }
    let content;
    if (example.kind === 'Scroll') {
        const contentWidth =
            example.properties.horizontal || example.properties.both
                ? 900
                : bounds.width;
        const contentHeight = example.properties.horizontal ? 80 : 900;
        const children = Array.from(
            { length: example.properties.horizontal ? 7 : 20 },
            (_, index) =>
                label(
                    'scrollRow_' + index,
                    rect(
                        example.properties.horizontal
                            ? 8 + index * 120
                            : index % 2 && example.properties.both
                              ? 500
                              : 8,
                        example.properties.horizontal ? 8 : index * 40,
                        example.properties.horizontal ? 100 : 280,
                        32
                    ),
                    'Example ' + String(index + 1),
                    { fontRole: 'body' }
                )
        );
        const scroll = { contentHeight, children };
        if (example.properties.horizontal || example.properties.both)
            scroll.contentWidth = contentWidth;
        content = [node('Scroll', 'sample', bounds, scroll)];
    } else if (example.kind === 'Splitter') {
        content = [
            node(
                'Splitter',
                'sample',
                bounds,
                Object.assign({}, values, {
                    text: tr('Size'),
                    min: 0,
                    max: 100,
                    horizontal: !!example.properties.horizontal
                })
            )
        ];
    } else if (example.kind === 'tree') {
        content = [
            node('List', 'sample', bounds, {
                source: 'treeRows',
                keyField: 'id',
                rowHeight: 36
            })
        ];
    } else if (example.kind === 'Grid') {
        content = [
            node(
                'Grid',
                'sample',
                bounds,
                Object.assign({}, values, {
                    source: 'cells',
                    text: tr('Table'),
                    rowHeaders: Array.from({ length: 50 }, (_, index) => ({
                        label: String(index + 1)
                    })),
                    columnHeaders: choices.map((option) => option.label),
                    cellWidth: 160,
                    rowHeight: 38,
                    labelWidth: 40,
                    headerHeight: 32,
                    revision: model.events.length
                })
            )
        ];
    } else if (example.kind === 'Graph') {
        content = [
            node(
                'Graph',
                'sample',
                bounds,
                Object.assign({}, values, {
                    label: tr('Graph'),
                    language,
                    nodes: [
                        {
                            identity: 'a',
                            label: 'First',
                            nodeX: 20,
                            nodeY: 20,
                            color: 'action'
                        },
                        {
                            identity: 'b',
                            label: 'Second',
                            nodeX: 280,
                            nodeY: 140,
                            color: 'action'
                        }
                    ].map((record) =>
                        Object.assign(
                            {},
                            record,
                            model.graphPositions.find(
                                (position) =>
                                    position.identity === record.identity
                            ) || {}
                        )
                    ),
                    selectedNodes: model.graphSelected,
                    edges: [{ from: 'a', to: 'b' }],
                    action: { type: 'graph' },
                    selectAction: { type: 'graphSelect' },
                    moveAction: { type: 'graphMove' }
                })
            )
        ];
    } else if (example.kind === 'Code') {
        content = [
            node(
                'Code',
                'sample',
                bounds,
                Object.assign({}, values, {
                    text: String(model.value),
                    service: 'sourceEditor',
                    bufferKey: model.id,
                    language
                })
            )
        ];
    } else if (example.kind === 'header') {
        content = header(
            Object.assign({}, example.properties, {
                title: tr('Name'),
                subtitle: tr(example.properties.subtitle || ''),
                backLabel: tr('Back'),
                enabled: values.enabled,
                actions: (example.properties.actions || []).map((action) =>
                    Object.assign({}, action, {
                        label: tr(action.label),
                        enabled: values.enabled && action.enabled !== false
                    })
                )
            }),
            bounds.width,
            bounds.height
        );
        content = [node('Box', 'sample', bounds, { children: content.nodes })];
    } else {
        content = [
            directKinds.indexOf(example.kind) >= 0
                ? node(example.kind, 'sample', bounds, values)
                : node('View', 'sample', bounds, { view: 'example' })
        ];
    }
    return {
        width,
        height,
        nodes: [
            label('exampleTitle', rect(20, 16, width - 40, 28), example.id, {
                fontRole: 'bodyLarge',
                weight: 600
            }),
            ...content,
            label(
                'exampleEvents',
                rect(20, height - 36, width - 40, 24),
                String(model.events.length),
                { fontRole: 'secondary' }
            )
        ]
    };
}

export function row(list, record, model, language, state) {
    return BaseCatalog.row(list, record, model, language, state);
}

export function cell(grid, record, row, column, model, state) {
    const key = row + ':' + column;
    return {
        nodes: [
            node(
                'Field',
                'cell_' + row + '_' + column,
                rect(0, 0, grid.cellWidth, grid.rowHeight),
                {
                    text:
                        model.cells[key] === undefined
                            ? String(row + 1) + ' / ' + String(column + 1)
                            : model.cells[key],
                    label: 'Name',
                    tableCell: true,
                    readOnly: grid.readOnly || state === 'readonly',
                    enabled: state !== 'disabled',
                    action: { type: 'cell', row, column }
                }
            )
        ]
    };
}

export function packedOptions(value) {
    return Array.from({ length: 1000 }, (_, index) => ({
        key: String(index),
        title: 'Option ' + String(index).padStart(4, '0'),
        icon: index % 3 === 0 ? 'folder' : '',
        marker: index % 5 === 0,
        accent: '#55a9ad',
        selected: String(index) === value
    }));
}

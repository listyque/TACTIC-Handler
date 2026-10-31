import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export const views = [
    {
        value: 'continious',
        label: 'Continuous tree',
        icon: 'MDI_FORMAT_LIST_BULLETED'
    },
    { value: 'tiles', label: 'Cards', icon: 'MDI_VIEW_DASHBOARD' },
    { value: 'table', label: 'Table', icon: 'MDI_TABLE' },
    { value: 'compact', label: 'Compact rows', icon: 'MDI_VIEW_LIST' },
    {
        value: 'splitted_vertical',
        label: 'Versions on the right',
        icon: 'MDI_VIEW_COLUMN'
    },
    {
        value: 'splitted_horizontal',
        label: 'Versions at the bottom',
        icon: 'MDI_VIEW_AGENDA'
    }
];

export const viewPicker = { width: 114, height: 40, iconSize: 20 };

export function inlineViews(width, tabsWidth = 0, historyWidth = 0) {
    // Reserve existing toolbar actions and comfortable natural tab widths.
    return (
        width >= 720 &&
        width - 240 - historyWidth - Math.max(220, tabsWidth) >=
            viewPicker.width + 8
    );
}

export function describeViewPicker(model, language) {
    return {
        nodes: [
            node(
                'Segmented',
                'searchResultViewPicker',
                rect(0, 0, viewPicker.width, viewPicker.height),
                {
                    label: translate('Result view', language),
                    options: views.slice(0, 3).map((view) =>
                        Object.assign({}, view, {
                            label: translate(view.label, language),
                            translate: false
                        })
                    ),
                    value: model.mode,
                    enabled: !model.busy,
                    iconOnly: true,
                    iconSize: viewPicker.iconSize,
                    action: { type: 'view' }
                }
            )
        ]
    };
}
export const groups = [
    { value: 'none', label: 'No grouping', icon: 'list-alt' },
    { value: 'status', label: 'SObject status', icon: 'group-items' },
    { value: 'pipeline', label: 'Pipeline', icon: 'process' }
];
export const sorts = [
    {
        value: 'name_asc',
        label: 'Name A-Z',
        icon: 'sort-items',
        column: 'name',
        direction: 'asc'
    },
    {
        value: 'name_desc',
        label: 'Name Z-A',
        icon: 'sort-items',
        column: 'name',
        direction: 'desc'
    },
    {
        value: 'updated_desc',
        label: 'Recently updated',
        icon: 'history',
        column: 'timestamp',
        direction: 'desc'
    },
    {
        value: 'updated_asc',
        label: 'Oldest updated',
        icon: 'history',
        column: 'timestamp',
        direction: 'asc'
    }
];
function choices(items, value, busy) {
    return items.map((item) => ({
        title: item.label,
        icon: item.icon,
        command: item.value,
        checked: item.value === value,
        enabled: !busy
    }));
}
export function viewActions(value, busy) {
    return choices(views, value, busy);
}
export function sortActions(model) {
    const actions = [{ title: 'Sort items', header: true }].concat(
        choices(sorts, model.mode, model.busy)
    );
    if (model.defaultOrder)
        actions.push({
            title: 'Default order',
            icon: 'list-alt',
            command: 'default',
            checked: !model.column,
            enabled: !model.busy
        });
    return actions.concat([
        { separator: true },
        {
            title: 'Sort by column',
            icon: 'table',
            command: 'column',
            enabled: !model.busy
        }
    ]);
}
export function groupActions(model) {
    const actions = [{ title: 'Group items', header: true }].concat(
        choices(groups, model.mode, model.busy)
    );
    if ((model.processes || []).length) {
        actions.push(
            { separator: true },
            { title: 'Task status by process', header: true }
        );
        for (const process of model.processes)
            actions.push({
                title: process.title || process.key,
                translate: false,
                icon: 'process-marker',
                accent: process.accent,
                command: 'task_status:' + process.key,
                checked: model.mode === 'task_status:' + process.key,
                enabled: !model.busy
            });
    }
    return actions;
}
export function filterActions(model) {
    const actions = (
        model.base || [
            {
                title: 'Advanced Search',
                icon: 'advanced-search',
                command: 'advanced_search'
            },
            {
                title: 'Filter Processes',
                icon: 'filter-alt',
                command: 'filter_processes'
            }
        ]
    ).slice();
    actions.push(
        { separator: true },
        { title: 'Saved searches', header: true }
    );
    for (const preset of model.presets || [])
        actions.push({
            title: preset.title || 'Saved search',
            translate: false,
            icon: 'save',
            command: 'preset:' + preset.view,
            checked: preset.view === model.selected,
            enabled: !model.busy && !preset.error
        });
    if (!(model.presets || []).length)
        actions.push({
            title: model.busy
                ? 'Loading saved searches...'
                : model.error || 'No saved searches',
            icon: model.busy ? 'hourglass_empty' : 'save',
            command: '',
            enabled: false
        });
    actions.push(
        { separator: true },
        {
            title: 'Refresh saved searches',
            icon: 'refresh',
            command: 'refresh_presets',
            enabled: !model.busy
        }
    );
    return actions;
}
export function sortColumn(model, width, language) {
    const text = (key) => translate(key, language);
    return {
        nodes: [
            label(
                'searchSortColumnTitle',
                rect(0, 0, width, 24),
                text('Sort by column'),
                { weight: 600 }
            ),
            node('Choice', 'searchSortColumn', rect(0, 30, width, 36), {
                label: text('Sort by'),
                value: model.column,
                options: model.columns || [],
                action: { type: 'column' },
                enabled: !model.busy
            }),
            button(
                'searchSortDirection',
                rect(0, 72, width, 36),
                text(model.direction === 'desc' ? 'Descending' : 'Ascending'),
                'sort',
                { type: 'direction' },
                !model.busy
            ),
            button(
                'searchSortApply',
                rect(width - 112, 120, 112, 36),
                text('Apply'),
                'check',
                { type: 'apply' },
                !model.busy && !!model.column,
                { highlighted: true }
            )
        ],
        contentHeight: 156
    };
}

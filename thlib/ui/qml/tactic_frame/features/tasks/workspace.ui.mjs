import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { actions as scopeActions } from './scope.ui.mjs';
import { controls } from '../../core/foundation.mjs';
export const modeWidth = 106;

export function pending(model, width, language) {
    const tr = (text, values) => translate(text, language, values);
    const height = 42;
    const saveWidth = model.saving ? 112 : 100;
    const saveX = width - 8 - saveWidth;
    const discardX = saveX - 8 - 96;
    let textRight = discardX - 8;
    const nodes = [
        node('Box', 'taskPendingSurface', rect(0, 0, width, height), {
            background: 'secondaryContainer',
            radius: 0
        }),
        node('Icon', 'taskPendingIcon', rect(12, 13, 16, 16), {
            icon: 'edit',
            color: 'action'
        }),
        button(
            'taskDiscard',
            rect(discardX, 5, 96, 32),
            tr('Discard').toUpperCase(),
            '',
            { type: 'discard' },
            !model.saving,
            { label: tr('Discard task changes'), fontRole: 'secondary' }
        ),
        button(
            'taskSave',
            rect(saveX, 5, saveWidth, 32),
            tr(model.saving ? 'Saving…' : 'Save').toUpperCase(),
            'save',
            { type: 'save' },
            !model.blocked,
            {
                label: tr('Save task changes'),
                highlighted: true,
                fontRole: 'secondary'
            }
        )
    ];
    for (const [visible, type, title, icon] of [
        [model.preview, 'preview', 'Preview Gantt changes', 'visibility'],
        [model.rebase, 'rebase', 'Reload draft revisions', 'refresh']
    ]) {
        if (!visible) continue;
        textRight -= 36;
        nodes.push(
            button(
                'taskPending_' + type,
                rect(textRight, 7, 28, 28),
                tr(title),
                icon,
                { type },
                !model.blocked,
                { iconOnly: true, iconAction: true, iconSize: 16 }
            )
        );
    }
    nodes.push(
        label(
            'taskPendingCount',
            rect(36, 11, textRight - 36, 20),
            tr(
                model.count === 1
                    ? '{count} task has unsaved changes'
                    : '{count} tasks have unsaved changes',
                { count: model.count }
            ),
            { fontRole: 'secondary' }
        )
    );
    return { height, nodes };
}

export function surfaces(model, width, language) {
    const tr = (text) => translate(text, language);
    const height = model.controlHeight || 36;
    return {
        height,
        nodes: [
            node(
                'Segmented',
                'quickTaskViewSwitcher',
                rect(0, 0, width, height),
                {
                    label: tr('Task workspace surface'),
                    iconOnly: true,
                    value: model.value,
                    enabled: !model.disabled,
                    options: [
                        {
                            value: 'cards',
                            label: tr('Task cards'),
                            icon: 'grid-view'
                        },
                        {
                            value: 'compact',
                            label: tr('Compact task list'),
                            icon: 'view-list'
                        },
                        {
                            value: 'workspace',
                            label: tr('Open task workspace'),
                            icon: 'dashboard-customize'
                        }
                    ],
                    action: { type: 'surface' }
                }
            )
        ]
    };
}

export function toolbar(model, width, language) {
    const tr = (text) => translate(text, language);
    const phone = !!model.phone,
        height = phone ? 40 : model.embedded === false ? 42 : 58,
        gap = 4,
        size = phone ? 32 : model.controlHeight || 36,
        y = (height - size) / 2;
    const compact = width < 800,
        condensed = width < 520;
    const directSort = !phone && width >= 1180,
        directGroup = !phone && width >= 720;
    const scopeSegments = !phone && width >= 1360;
    const scopeButton = !phone && width >= 380 && !scopeSegments;
    const scopeWidth = Math.max(
        controls.button.minimumWidth,
        Math.ceil(
            (model.scopeTextWidth === undefined
                ? String(model.scopeLabel || '').length * 7
                : model.scopeTextWidth) +
                controls.button.iconPadding +
                controls.button.padding +
                controls.button.spacing +
                controls.button.iconSize +
                1
        )
    );
    const nodes = [
        node('Box', 'taskToolbarSurface', rect(0, 0, width, height), {
            background: 'toolBar',
            radius: 0
        })
    ];
    const action = (id, x, title, icon, type, enabled, extra) =>
        nodes.push(
            button(
                id,
                rect(x, y, size, size),
                tr(title),
                icon,
                { type },
                enabled,
                Object.assign(
                    { iconOnly: true, iconAction: true, iconSize: 17 },
                    extra || {}
                )
            )
        );
    let right = width - 7;
    right -= 38;
    nodes.push(
        button(
            'taskWorkspaceRefreshButton',
            rect(right, (height - 38) / 2, 38, 38),
            tr('Refresh'),
            'refresh',
            { type: 'refresh' },
            model.canRefresh !== false,
            { iconOnly: true, iconAction: true, iconSize: 17 }
        )
    );
    if (!phone) {
        right -= gap + 108;
        nodes.push(
            node(
                'View',
                'taskWorkspaceSurfaceSwitcher',
                rect(right, y, 108, size),
                { view: 'surfaces' }
            )
        );
    }
    right -= gap + size;
    action(
        'taskWorkspaceOverflowButton',
        right,
        'Task view options',
        'more',
        'options',
        true,
        {
            pressAction: { type: 'options-press' },
            iconColor:
                condensed && model.filtersActive ? 'green' : 'primaryText'
        }
    );
    let x = 10;
    action(
        'taskWorkspaceCreateButton',
        x,
        'Create task',
        'add',
        'create',
        model.canCreate !== false,
        {
            highlighted: true,
            filledAction: true,
            iconAction: false,
            iconSize: 18
        }
    );
    x += size + gap;
    if (scopeButton && compact) {
        action(
            'compactScopeButton',
            x,
            'Choose task scope',
            model.scopeIcon || 'inventory-2',
            'scope',
            !model.blocked,
            { pressAction: { type: 'scope-press' } }
        );
        x += size + gap;
    }
    if (!phone && !compact) {
        action(
            'taskMilestoneManagerButton',
            x,
            'Project milestones',
            'milestone',
            'milestones',
            !model.busy,
            { iconColor: 'action' }
        );
        x += size + gap;
    }
    let remaining = right - gap;
    if (directGroup) remaining -= 148 + gap;
    if (directSort) remaining -= 132 + gap;
    if (scopeSegments) remaining -= 560 + gap;
    else if (scopeButton && !compact) remaining -= scopeWidth + gap;
    if (!phone && !condensed) remaining -= (size + gap) * 2;
    const searchWidth = Math.max(0, remaining - x);
    if (!phone || model.searchOpen) {
        nodes.push(
            node(
                'View',
                'taskWorkspaceSearchField',
                rect(x, y, searchWidth, size),
                { view: 'search' }
            )
        );
        x += searchWidth + gap;
    } else {
        action(
            'taskWorkspaceSearchToggle',
            Math.max(x, remaining - size),
            'Open search',
            'search',
            'search-toggle',
            true
        );
        x = remaining + gap;
    }
    if (!phone && !condensed) {
        nodes.push(
            node(
                'Box',
                'taskFilterSurface',
                rect(x + 2, y + 2, size - 4, size - 4),
                {
                    radiusRole: 'iconButtonRadius',
                    background: model.filtersActive
                        ? { mix: ['surfaceContainerHigh', 'green', 0.18] }
                        : 'surfaceContainerHigh'
                }
            )
        );
        action(
            'taskWorkspaceQuickFilterButton',
            x,
            'Task filters',
            'filter',
            'filters',
            !model.busy,
            {
                iconColor: model.filtersActive ? 'green' : 'primaryText',
                pressAction: { type: 'filters-press' }
            }
        );
        x += size + gap;
        action(
            'taskWorkspaceClearFiltersButton',
            x,
            'Clear filters',
            'filter-off',
            'clear-filters',
            !model.busy && model.filtersActive
        );
        x += size + gap;
    }
    if (scopeSegments) {
        nodes.push(
            node('Segmented', 'embeddedScopeSwitcher', rect(x, y, 560, size), {
                label: tr('Task scope'),
                value: model.scope,
                enabled: !model.blocked,
                options: scopeActions(model, language).map((row) => ({
                    value: row.value,
                    label: row.title,
                    icon: row.icon,
                    disabled: !row.enabled,
                    reselectable: row.value === 'team'
                })),
                action: { type: 'scope-choice' }
            })
        );
        x += 564;
    } else if (scopeButton && !compact) {
        nodes.push(
            button(
                'embeddedScopeButton',
                rect(x, y, scopeWidth, size),
                model.scopeLabel || '',
                model.scopeIcon || 'inventory-2',
                { type: 'scope' },
                !model.blocked,
                {
                    label: tr('Choose task scope'),
                    pressAction: { type: 'scope-press' },
                    tonal: true,
                    fontRole: 'body'
                }
            )
        );
        x += scopeWidth + gap;
    }
    for (const [shown, name, extent, title] of [
        [directSort, 'sort', 132, 'Sort'],
        [directGroup, 'group', 148, 'Group']
    ]) {
        if (!shown) continue;
        nodes.push(
            node(
                'Choice',
                name === 'sort' ? 'taskSortModeCombo' : 'taskGroupModeCombo',
                rect(x, y, extent, size),
                {
                    label: tr(title),
                    displayPrefix: name === 'sort' ? tr('Sort') + ': ' : '',
                    value: model[name],
                    enabled: !model.busy,
                    options: (model[name + 'Options'] || []).map((row) =>
                        Object.assign({}, row, { label: tr(row.label) })
                    ),
                    action: { type: name }
                }
            )
        );
        x += extent + gap;
    }
    return {
        nodes,
        height,
        compact,
        condensed,
        directSort,
        directGroup,
        createBounds: { x: 10, y, width: size, height: size }
    };
}

export function processToolbar(model, width, language) {
    const tr = (text) => translate(text, language),
        height = model.phone ? 40 : 58,
        controlHeight = model.controlHeight || 36;
    const nodes = [
        node('Box', 'quickTaskToolbar', rect(0, 0, width, height), {
            background: 'toolBar',
            radius: 0
        }),
        node('Icon', 'quickTaskIcon', rect(10, (height - 17) / 2, 17, 17), {
            icon: 'task-alt',
            color: 'action'
        }),
        label(
            'quickTaskTarget',
            rect(31, (height - 20) / 2, Math.max(0, width - 256), 20),
            model.title || tr('Select an sObject'),
            {
                fontRole: 'bodyLarge',
                weight: 600
            }
        ),
        button(
            'quickTaskSaveAll',
            rect(width - 221, (height - 28) / 2, 28, 28),
            tr('Save all process changes'),
            'save',
            { type: 'save-all' },
            !model.busy && model.dirty,
            {
                iconOnly: true,
                iconAction: true,
                iconSize: 17,
                iconColor: 'action'
            }
        ),
        button(
            'quickTaskDiscardAll',
            rect(width - 189, (height - 28) / 2, 28, 28),
            tr('Discard all process changes'),
            'undo',
            { type: 'discard-all' },
            !model.busy && model.dirty,
            { iconOnly: true, iconAction: true, iconSize: 17 }
        ),
        node(
            'View',
            'quickTaskWorkspaceSurfaceSwitcher',
            rect(width - 157, (height - controlHeight) / 2, 108, controlHeight),
            { view: 'surfaces' }
        ),
        button(
            'quickTaskRefreshButton',
            rect(width - 45, (height - 38) / 2, 38, 38),
            tr('Refresh'),
            'refresh',
            { type: 'refresh' },
            !model.busy && model.hasTarget,
            { iconOnly: true, iconAction: true, iconSize: 17 }
        )
    ];
    return { nodes, height };
}

export function modes(model, width, language) {
    const tr = (text) => translate(text, language),
        h = model.controlHeight || 36;
    return {
        width: modeWidth,
        height: h,
        nodes: [
            node('Segmented', 'taskBrowserViewSwitcher', rect(0, 0, 74, h), {
                label: tr('Task view'),
                iconOnly: true,
                value: model.view,
                enabled: !model.busy,
                options: [
                    { value: 'table', label: tr('Table'), icon: 'table-view' },
                    { value: 'gantt', label: tr('Gantt'), icon: 'gantt' }
                ],
                action: { type: 'mode' }
            }),
            button(
                'taskCalendarButton',
                rect(78, (h - 28) / 2, 28, 28),
                tr('Calendar'),
                'calendar-month',
                { type: 'calendar' },
                !model.busy && model.calendar !== false,
                { iconOnly: true, iconAction: true, iconSize: 17 }
            )
        ]
    };
}
export function footer(model, width, language) {
    const tr = (text, values) => translate(text, language, values),
        nodes = [],
        height = 58;
    let right = width - 8;
    if (model.quick) {
        nodes.push(
            node('Icon', 'taskFooterIcon', rect(12, 21, 16, 16), {
                icon: 'task-alt',
                color: 'secondaryText'
            })
        );
        nodes.push(
            label(
                'taskFooterCount',
                rect(36, 19, Math.max(0, width - 180), 20),
                tr(
                    model.processes === 1
                        ? '{count} process'
                        : '{count} processes',
                    { count: model.processes }
                ),
                { fontRole: 'body', weight: 500, color: 'secondaryText' }
            )
        );
        if (model.busy) {
            right -= 22;
            nodes.push(
                node('View', 'taskFooterBusy', rect(right, 18, 22, 22), {
                    view: 'busy'
                })
            );
            right -= 8;
        }
        if (model.dirty)
            nodes.push(
                label(
                    'taskFooterDirty',
                    rect(
                        Math.max(36, right - 130),
                        20,
                        Math.min(130, right - 36),
                        18
                    ),
                    tr('{count} unsaved', { count: model.dirty }),
                    {
                        align: 'right',
                        fontRole: 'secondary',
                        weight: 600,
                        color: 'action'
                    }
                )
            );
    } else {
        if (model.showModes && width >= 380) {
            right -= modeWidth;
            for (const item of modes(model, modeWidth, language).nodes)
                nodes.push(
                    Object.assign({}, item, {
                        x: item.x + right,
                        y: item.y + (height - (model.controlHeight || 36)) / 2
                    })
                );
            right -= 12;
        } else if (model.reserveModes && width >= 380) right -= modeWidth + 12;
        if (model.more) {
            const w = width < 520 ? 32 : 136;
            right -= w;
            nodes.push(
                button(
                    'taskFooterLoadMore',
                    rect(right, 13, w, 32),
                    tr('Load more tasks'),
                    'add',
                    { type: 'more' },
                    !model.busy,
                    { iconOnly: width < 520 }
                )
            );
            right -= 8;
        }
        if (model.checked && right > 200) {
            right -= 28;
            nodes.push(
                button(
                    'taskFooterClear',
                    rect(right, 15, 28, 28),
                    tr('Clear checked tasks'),
                    'close',
                    { type: 'clear' },
                    !model.busy,
                    { iconOnly: true, iconAction: true, iconSize: 17 }
                )
            );
            right -= 8;
        }
        let text = model.filtered
            ? tr('{visible} of {loaded} tasks', {
                  visible: model.visible,
                  loaded: model.loaded
              })
            : tr(model.loaded === 1 ? '{count} task' : '{count} tasks', {
                  count: model.loaded
              });
        if (width >= 720 && model.processes)
            text +=
                '   ' +
                tr(
                    model.processes === 1
                        ? '{count} process'
                        : '{count} processes',
                    { count: model.processes }
                );
        if (width >= 900 && model.checked)
            text += '   ' + tr('{count} checked', { count: model.checked });
        if (model.total > model.loaded)
            text +=
                '   ' +
                tr('{loaded} of {total} loaded', {
                    loaded: model.loaded,
                    total: model.total
                });
        nodes.push(
            label(
                'taskFooterCount',
                rect(10, 21, Math.max(0, right - 10), 16),
                text,
                { fontRole: 'caption', color: 'secondaryText' }
            )
        );
    }
    return { nodes, height };
}

export function options(model, width, language) {
    const tr = (text) => translate(text, language),
        nodes = [];
    let y = 0;
    const choice = (id, title, value, records, type) => {
        nodes.push(
            label(id + 'Title', rect(0, y, width, 16), tr(title), {
                fontRole: 'caption',
                color: 'secondaryText'
            })
        );
        nodes.push(
            node('Choice', id, rect(0, y + 20, width, 32), {
                label: tr(title),
                value,
                options: records.map((row) =>
                    Object.assign({}, row, { label: tr(row.label) })
                ),
                enabled: !model.busy,
                action: { type }
            })
        );
        y += 60;
    };
    choice(
        'taskOptionsView',
        'Task view',
        model.view || 'table',
        [
            { value: 'table', label: 'Table', icon: 'table-view' },
            { value: 'gantt', label: 'Gantt', icon: 'gantt' }
        ],
        'mode'
    );
    if (model.toolbarWidth < 1180)
        choice(
            'taskOptionsSort',
            'Sort',
            model.sort,
            model.sortOptions || [],
            'sort'
        );
    nodes.push(
        node('CheckBox', 'taskOptionsDescending', rect(0, y, width, 32), {
            text: tr('Descending'),
            label: tr('Descending'),
            checked: !!model.descending,
            enabled: !model.busy,
            action: { type: 'descending' }
        })
    );
    y += 40;
    if (model.toolbarWidth < 720)
        choice(
            'taskOptionsGroup',
            'Group',
            model.group,
            model.groupOptions || [],
            'group'
        );
    choice(
        'taskOptionsPageSize',
        'Records per page',
        model.pageSize,
        [20, 50, 100, 500].map((value) => ({ value, label: String(value) })),
        'page-size'
    );
    for (const [type, title, icon, enabled] of [
        [
            'scope',
            'Choose task scope',
            model.scopeIcon || 'inventory-2',
            !model.blocked
        ],
        ['filters', 'Task filters', 'filter', !model.busy],
        [
            'clear-filters',
            'Clear filters',
            'filter-off',
            !model.busy && !!model.filtersActive
        ],
        ['milestones', 'Project milestones', 'milestone', !model.busy],
        ['columns', 'Task columns', 'view-column', !model.busy],
        ['quick', 'Quick task editor', 'view-agenda', !model.busy],
        ['calendar', 'Calendar', 'calendar-month', !model.busy]
    ]) {
        if (type === 'columns' && model.phone) continue;
        nodes.push(
            button(
                'taskOptions_' + type,
                rect(0, y, width, 32),
                tr(title),
                icon,
                { type },
                enabled,
                { align: 'left' }
            )
        );
        y += 36;
    }
    if (model.phone) {
        nodes.push(
            node('CheckBox', 'taskOptionsSelectAll', rect(0, y, width, 32), {
                text: tr('Select all tasks'),
                label: tr('Select all tasks'),
                checked: !!model.allSelected,
                enabled: !model.busy,
                action: { type: 'select-all' }
            })
        );
        y += 40;
        nodes.push(
            node('View', 'taskOptionsSurfaces', rect(0, y, 108, 32), {
                view: 'surfaces'
            })
        );
        y += 40;
    }
    return { nodes, height: y };
}

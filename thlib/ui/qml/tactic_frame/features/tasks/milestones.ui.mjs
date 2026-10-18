import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import { parse, monthLabel } from '../../controls/forms/calendar.mjs';

export function layout(width, height, controlHeight = 36) {
    const margin = 12,
        gap = 10,
        inner = Math.max(0, width - margin * 2),
        searchY = margin + 76 + gap,
        listY = searchY + controlHeight + gap;
    return {
        margin,
        gap,
        inner,
        searchY,
        listY,
        listHeight: Math.max(0, height - listY - margin)
    };
}

export function header(model, width, language) {
    const tr = (text) => translate(text, language),
        compact = width < 600,
        createWidth = compact ? 36 : 146;
    const createX = width - 12 - createWidth,
        refreshX = createX - 39,
        countWidth = width >= 700 ? 86 : 0;
    const textRight = refreshX - (countWidth ? countWidth + 11 : 8),
        radius = model.radius || 8;
    const nodes = [
        node('Box', 'milestoneHeaderSurface', rect(0, 0, width, 76), {
            background: 'surfaceContainerLow',
            border: 'outlineVariant',
            borderWidth: 1,
            radius
        }),
        node('Box', 'milestoneHeaderIconSurface', rect(12, 15, 46, 46), {
            background: 'secondaryContainer',
            radius
        }),
        node('Icon', 'milestoneHeaderIcon', rect(24, 27, 22, 22), {
            icon: 'milestone',
            color: 'action'
        }),
        label(
            'milestoneHeaderTitle',
            rect(69, 21, textRight - 77, 20),
            tr('Project milestones'),
            { fontRole: 'section', weight: 600 }
        ),
        label(
            'milestoneHeaderProject',
            rect(69, 43, textRight - 77, 16),
            translate(
                'Schedule reusable task deadlines for {project}',
                language,
                { project: model.project || tr('current project') }
            ),
            { fontRole: 'secondary', color: 'secondaryText' }
        ),
        button(
            'milestoneRefresh',
            rect(refreshX, 24, 28, 28),
            '',
            'refresh',
            { type: 'refresh' },
            !model.busy,
            {
                label: tr('Refresh milestones'),
                iconOnly: true,
                iconAction: true,
                iconSize: 16
            }
        ),
        button(
            'milestoneCreate',
            rect(createX, 22, createWidth, 32),
            compact ? '' : tr('New milestone'),
            'add',
            { type: 'create' },
            !model.busy && model.canCreate !== false,
            {
                label: tr('New milestone'),
                iconOnly: compact,
                highlighted: true,
                filledAction: true,
                fontRole: 'secondary'
            }
        )
    ];
    if (countWidth)
        nodes.push(
            label(
                'milestoneHeaderCount',
                rect(refreshX - countWidth - 11, 30, countWidth, 16),
                String(model.count || 0) + ' ' + tr('milestones'),
                {
                    fontRole: 'secondary',
                    color: 'secondaryText',
                    align: 'right'
                }
            )
        );
    return { nodes, height: 76 };
}

export function search(model, width, language) {
    const height = model.controlHeight || 36;
    return {
        height,
        nodes: [
            node('Field', 'milestoneSearch', rect(0, 0, width, height), {
                text: model.query || '',
                inputType: 'search',
                paddingLeft: 39,
                label: translate('Search milestones', language),
                placeholder: translate('Search milestones', language),
                enabled: !model.busy,
                action: { type: 'query' }
            }),
            node(
                'Icon',
                'milestoneSearchIcon',
                rect(12, (height - 16) / 2, 16, 16),
                {
                    icon: 'search',
                    color: 'secondaryText',
                    pointerTransparent: true
                }
            )
        ]
    };
}

export function empty(model, width, language) {
    const tr = (text) => translate(text, language),
        nodes = [];
    nodes.push(
        node('Icon', 'milestoneEmptyIcon', rect(width / 2 - 18, 0, 36, 36), {
            icon: 'milestone',
            color: 'disabledText'
        })
    );
    nodes.push(
        label(
            'milestoneEmptyTitle',
            rect(0, 44, width, 18),
            tr(model.query ? 'No matching milestones' : 'No milestones yet'),
            { fontRole: 'body', weight: 600, align: 'center' }
        )
    );
    nodes.push(
        label(
            'milestoneEmptyHint',
            rect(0, 70, width, 32),
            tr(
                model.query
                    ? 'Try another search'
                    : 'Create a reusable deadline for project tasks'
            ),
            {
                fontRole: 'secondary',
                color: 'secondaryText',
                align: 'center',
                wrap: true
            }
        )
    );
    if (!model.query)
        nodes.push(
            button(
                'milestoneEmptyCreate',
                rect(width / 2 - 80, 110, 160, 32),
                tr('New milestone'),
                'add',
                { type: 'create' },
                !model.busy && model.canCreate !== false,
                { filledAction: true, highlighted: true }
            )
        );
    return { nodes, height: model.query ? 102 : 150 };
}

export function row(model, width, language) {
    const tr = (text) => translate(text, language),
        nodes = [],
        compact = width < 640;
    const radius = model.radius || 8,
        control = model.controlHeight || 36,
        blocked = model.busy || model.saving || !!model.uncertain;
    const discard = !!(model.dirty || model.uncertain),
        actionCount = discard ? 3 : 2,
        actionsWidth = actionCount * 28 + (actionCount - 1) * 4;
    const nameX = 68,
        actionsX = width - 9 - actionsWidth;
    const available = Math.max(0, actionsX - nameX - 18),
        nameWidth = compact ? Math.max(0, width - nameX - 9) : available * 0.41;
    const dueX = compact ? nameX : nameX + nameWidth + 9,
        dueWidth = compact ? nameWidth : available - nameWidth;
    const dueTitleY = compact ? 82 : 14,
        planY = compact ? 148 : 76,
        planHeight = compact ? 86 : 43;
    const errorY = planY + planHeight + 7,
        height = errorY + (model.error ? (model.canReview ? 72 : 36) : 0);
    nodes.push(
        node('Box', 'milestoneRowSurface', rect(0, 0, width, height), {
            background: model.dirty
                ? 'surfaceContainerHigh'
                : 'surfaceContainerLow',
            radius,
            border: model.error
                ? 'error'
                : model.selected || model.dirty
                  ? 'action'
                  : undefined,
            borderWidth: model.dirty || model.selected || model.error ? 1 : 0
        })
    );
    nodes.push(
        node('Box', 'milestoneDateSurface', rect(9, 17, 50, 50), {
            background: model.isNew
                ? 'secondaryContainer'
                : 'surfaceContainerHighest',
            radius
        })
    );
    const parsed = parse(model.dueDate, false);
    nodes.push(
        label(
            'milestoneDateDay',
            rect(9, 24, 50, 22),
            parsed ? String(parsed.getDate()) : '—',
            { fontRole: 'title', weight: 600, align: 'center' }
        )
    );
    nodes.push(
        label(
            'milestoneDateMonth',
            rect(9, 48, 50, 15),
            parsed
                ? monthLabel(parsed, language)
                      .split(' ')[0]
                      .slice(0, 3)
                      .toUpperCase()
                : '',
            {
                fontRole: 'caption',
                weight: 700,
                align: 'center',
                color: 'action'
            }
        )
    );
    nodes.push(
        label(
            'milestoneRowState',
            rect(
                nameX,
                14,
                compact ? Math.max(0, actionsX - nameX - 8) : nameWidth,
                12
            ),
            tr(model.isNew ? 'New milestone' : 'Milestone').toUpperCase() +
                (model.dirty
                    ? ' · ' + tr(model.saving ? 'Saving…' : 'Unsaved changes')
                    : ''),
            {
                fontRole: 'caption',
                weight: 700,
                color: model.dirty ? 'yellow' : 'secondaryText'
            }
        )
    );
    const actions = discard
        ? [['milestoneDiscard', 'Discard changes', 'undo', 'discard', true]]
        : [];
    actions.push([
        'milestoneSave',
        'Save milestone',
        'save',
        'save',
        model.dirty && !model.uncertain
    ]);
    actions.push([
        'milestoneDelete',
        'Delete milestone',
        'delete',
        'delete',
        model.canDelete !== false && !model.uncertain
    ]);
    actions.forEach(([id, title, icon, type, enabled], index) =>
        nodes.push(
            button(
                id,
                rect(actionsX + index * 32, compact ? 2 : 31, 28, 28),
                '',
                icon,
                { type, code: model.code },
                !model.busy && !model.saving && !!enabled,
                {
                    label: tr(title),
                    iconOnly: true,
                    iconAction: true,
                    iconSize: 16,
                    iconColor:
                        type === 'delete'
                            ? 'error'
                            : type === 'save' && model.dirty
                              ? 'action'
                              : 'secondaryText'
                }
            )
        )
    );
    nodes.push(
        node('Field', 'milestoneName', rect(nameX, 28, nameWidth, control), {
            text: model.description || '',
            label: tr('Milestone name'),
            maxLength: 4096,
            enabled: !blocked && model.nameEditable !== false,
            action: { type: 'change', code: model.code, field: 'description' }
        })
    );
    nodes.push(
        label(
            'milestoneDueTitle',
            rect(dueX, dueTitleY, dueWidth, 12),
            tr('Due date').toUpperCase(),
            { fontRole: 'caption', weight: 700, color: 'secondaryText' }
        )
    );
    nodes.push(
        node(
            'DateChoice',
            'milestoneDueDate',
            rect(dueX, dueTitleY + 14, dueWidth, control),
            {
                text: model.dueDate || '',
                label: tr('Due date'),
                includeTime: false,
                allowClear: false,
                enabled: !blocked && model.dateEditable !== false,
                action: { type: 'change', code: model.code, field: 'dueDate' }
            }
        )
    );
    nodes.push(
        node(
            'Box',
            'milestonePlanSurface',
            rect(69, planY, width - 79, planHeight),
            { background: 'surfaceContainerHighest', radius: 6 }
        )
    );
    nodes.push(
        node('Box', 'milestonePlanIconSurface', rect(78, planY + 7.5, 28, 28), {
            background: 'secondaryContainer',
            radius: 6
        })
    );
    nodes.push(
        node('Icon', 'milestonePlanIcon', rect(84.5, planY + 14, 15, 15), {
            icon: 'milestone',
            color: 'action'
        })
    );
    const overdueWidth = model.overdueCount ? 68 : 0,
        progressWidth = compact
            ? Math.max(0, width - 100 - overdueWidth)
            : Math.min(226, width * 0.28);
    const progressX = compact
        ? 78
        : width - 19 - overdueWidth - progressWidth - (overdueWidth ? 9 : 0);
    const titleWidth = compact ? width - 127 : Math.max(0, progressX - 124);
    nodes.push(
        label(
            'milestonePlanTitle',
            rect(115, planY + 6, titleWidth, 16),
            tr('Linked task plan').toUpperCase() +
                ' · ' +
                (model.taskCount
                    ? String(
                          model.completedCount == null
                              ? '—'
                              : model.completedCount
                      ) +
                      ' / ' +
                      model.taskCount +
                      ' ' +
                      tr('tasks')
                    : tr('No tasks')),
            { fontRole: 'secondary', weight: 600 }
        )
    );
    nodes.push(
        label(
            'milestonePlanSummary',
            rect(
                compact ? 78 : 115,
                planY + (compact ? 34 : 25),
                compact ? width - 98 : titleWidth,
                15
            ),
            model.taskCount
                ? (model.planStartDate || tr('Start not set')) +
                      ' → ' +
                      (model.dueDate || '—') +
                      (model.processSummary
                          ? ' · ' + model.processSummary
                          : '') +
                      (model.plannedHours > 0
                          ? ' · ' + model.plannedHours + ' h'
                          : '')
                : tr('Assign tasks to build the milestone plan'),
            { fontRole: 'caption', color: 'secondaryText' }
        )
    );
    const completion = Math.max(
            0,
            Math.min(100, Number(model.completion) || 0)
        ),
        progressY = planY + (compact ? 58 : 11);
    nodes.push(
        label(
            'milestoneCompletionTitle',
            rect(progressX, progressY, Math.max(0, progressWidth - 40), 15),
            tr('Completion').toUpperCase(),
            { fontRole: 'caption', weight: 700, color: 'secondaryText' }
        )
    );
    nodes.push(
        label(
            'milestoneCompletion',
            rect(
                progressX + Math.max(0, progressWidth - 40),
                progressY,
                40,
                15
            ),
            model.taskCount ? completion + '%' : '—',
            { fontRole: 'caption', weight: 600, align: 'right' }
        )
    );
    nodes.push(
        node(
            'Box',
            'milestoneCompletionTrack',
            rect(progressX, progressY + 18, progressWidth, 5),
            { background: 'surfaceContainerLow', radius: 2.5 }
        )
    );
    nodes.push(
        node(
            'Box',
            'milestoneCompletionValue',
            rect(
                progressX,
                progressY + 18,
                (progressWidth * completion) / 100,
                5
            ),
            { background: 'action', radius: 2.5 }
        )
    );
    if (model.overdueCount)
        nodes.push(
            label(
                'milestoneOverdue',
                rect(
                    width - 19 - overdueWidth,
                    progressY + 4,
                    overdueWidth,
                    15
                ),
                String(model.overdueCount) + ' ' + tr('overdue'),
                {
                    fontRole: 'caption',
                    weight: 600,
                    color: 'error',
                    align: 'right'
                }
            )
        );
    if (model.error) {
        nodes.push(
            label(
                'milestoneRowError',
                rect(12, errorY, width - 24, 30),
                tr(model.error),
                { fontRole: 'caption', color: 'error', wrap: true }
            )
        );
        if (model.canReview)
            nodes.push(
                button(
                    'milestoneReview',
                    rect(12, errorY + 36, width - 24, 28),
                    tr('Review current milestone revision'),
                    'refresh',
                    { type: 'review', code: model.code },
                    !model.busy
                )
            );
    }
    return { nodes, height };
}

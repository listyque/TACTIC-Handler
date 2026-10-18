import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export function layout(width, height) {
    const compact = width < 500 || height < 430;
    const margin = compact ? 6 : 10,
        gap = compact ? 5 : 8,
        cellGap = compact ? 2 : 4;
    const inner = Math.max(0, width - 2 * margin);
    const gridY = margin + 34 + gap + 22 + gap;
    const gridHeight = Math.max(0, height - gridY - gap - 28 - margin);
    return {
        compact,
        margin,
        gap,
        cellGap,
        inner,
        gridY,
        gridHeight,
        cellWidth: Math.max(0, (inner - 6 * cellGap) / 7),
        cellHeight: Math.max(0, (gridHeight - 5 * cellGap) / 6),
        footerY: height - margin - 28
    };
}

export function navigation(model, width, language) {
    const tr = (text) => translate(text, language),
        nodes = [];
    const icon = (id, x, text, name, type) =>
        nodes.push(
            button(id, rect(x, 3, 28, 28), '', name, { type }, !model.busy, {
                label: tr(text),
                iconOnly: true,
                iconAction: true,
                iconSize: 16
            })
        );
    icon('calendarPrevious', 0, 'Previous month', 'chevron_left', 'previous');
    const trailing = model.selectedDay ? 128 : 96;
    nodes.push(
        node(
            'DateChoice',
            'calendarMonth',
            rect(32, 1, Math.max(0, width - 36 - trailing), 32),
            {
                label: tr('Calendar month'),
                text: model.monthDate,
                includeTime: false,
                monthOnly: true,
                allowClear: false,
                enabled: !model.busy,
                action: { type: 'month-value' }
            }
        )
    );
    let x = width - trailing;
    icon('calendarNext', x, 'Next month', 'chevron_right', 'next');
    x += 32;
    icon('calendarToday', x, 'Today', 'calendar_today', 'today');
    x += 32;
    if (model.selectedDay) {
        icon(
            'calendarClearDay',
            x,
            'Clear selected day',
            'filter_alt_off',
            'clear'
        );
        x += 32;
    }
    icon('calendarAgenda', x, 'Agenda', 'format-list-bulleted', 'agenda');
    return { nodes };
}

export function weekday(index, width, language) {
    const en = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'];
    const ru = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС'];
    return {
        nodes: [
            label(
                'calendarWeekday' + index,
                rect(0, 3, width, 16),
                (language === 'ru' ? ru : en)[index],
                {
                    fontRole: 'caption',
                    color: 'secondaryText',
                    weight: 600,
                    align: 'center'
                }
            )
        ]
    };
}

export function taskLimit(height, compact, milestones) {
    return compact
        ? 0
        : Math.max(
              1,
              Math.min(3, Math.floor((height - (milestones ? 54 : 30)) / 22))
          );
}

export function day(model, width, height, language) {
    const nodes = [],
        today = !!model.today,
        weekend = model.index % 7 >= 5;
    const tr = (text) => translate(text, language);
    const limit = taskLimit(
        height,
        model.compact,
        (model.milestones || []).length
    );
    const radius = model.radius || 8;
    const color = model.selected
        ? 'secondaryContainer'
        : model.hovered
          ? 'surfaceContainerHighest'
          : weekend
            ? 'surfaceContainerLow'
            : 'surfaceContainer';
    nodes.push(
        node('Box', 'calendarDaySurface', rect(0, 0, width, height), {
            background: color,
            radius
        })
    );
    nodes.push(
        node('Action', 'calendarDayAction', rect(0, 0, width, height), {
            text: model.date,
            selected: !!model.selected,
            enabled: !model.busy,
            action: { type: 'day', value: model.date },
            radius
        })
    );
    if (today)
        nodes.push(
            node('Box', 'calendarTodayCircle', rect(5, 5, 23, 23), {
                background: 'action',
                radius: 11.5
            })
        );
    nodes.push(
        label('calendarDayNumber', rect(5, 8.5, 23, 16), String(model.day), {
            fontRole: 'secondary',
            align: 'center',
            color: today ? 'selectedText' : 'primaryText',
            weight: today ? 600 : 400
        })
    );
    if (model.taskCount)
        nodes.push(
            label(
                'calendarTaskCount',
                rect(width - 34, 7, 27, 15),
                String(model.taskCount),
                {
                    fontRole: 'caption',
                    align: 'right',
                    weight: 600,
                    color: model.overdueCount ? 'error' : 'secondaryText'
                }
            )
        );
    const milestone = (model.milestones || [])[0];
    if (milestone) {
        const bandHeight = model.compact ? 8 : 20;
        nodes.push(
            node(
                'Box',
                'calendarMilestoneBand',
                rect(5, 31, width - 10, bandHeight),
                {
                    background: 'tertiaryContainer',
                    border: 'tertiary',
                    borderWidth: 1,
                    radius: 6
                }
            )
        );
        if (!model.compact) {
            nodes.push(
                node('Icon', 'calendarMilestoneIcon', rect(10, 35.5, 11, 11), {
                    icon: 'milestone',
                    color: 'tertiary'
                })
            );
            nodes.push(
                label(
                    'calendarMilestoneLabel',
                    rect(25, 33.5, width - 32, 15),
                    milestone.label,
                    { fontRole: 'caption', weight: 600 }
                )
            );
        }
        nodes.push(
            node(
                'Action',
                'calendarMilestoneAction',
                rect(5, 31, width - 10, bandHeight),
                {
                    text: milestone.label,
                    enabled: !model.busy,
                    action: { type: 'milestone', value: milestone.code }
                }
            )
        );
    }
    let y = milestone ? 55 : 31;
    for (const task of (model.tasks || []).slice(0, limit)) {
        nodes.push(
            node(
                'Box',
                'calendarTaskSurface' + task.taskCode,
                rect(5, y, width - 10, 19),
                {
                    background: task.selected ? 'secondaryContainer' : 'row',
                    radius: 6
                }
            )
        );
        nodes.push(
            node(
                'Box',
                'calendarTaskDot' + task.taskCode,
                rect(10, y + 6.5, 6, 6),
                {
                    background: task.statusColor || 'action',
                    radius: 3
                }
            )
        );
        nodes.push(
            label(
                'calendarTaskText' + task.taskCode,
                rect(20, y + 2, width - 30, 15),
                task.parentTitle + ' · ' + task.processLabel,
                { fontRole: 'caption' }
            )
        );
        nodes.push(
            node(
                'Action',
                'calendarTaskOpen' + task.taskCode,
                rect(5, y, width - 10, 19),
                {
                    text: task.parentTitle + ' · ' + task.processLabel,
                    enabled: !model.busy,
                    action: {
                        type: 'inspect',
                        value: task.taskCode,
                        parentKey: task.parentKey,
                        process: task.process
                    }
                }
            )
        );
        y += 22;
    }
    if (limit && model.taskCount > limit)
        nodes.push(
            label(
                'calendarMoreTasks',
                rect(5, y, width - 10, 14),
                translate('{count} more tasks', language, {
                    count: model.taskCount - limit
                }),
                { fontRole: 'caption', color: 'secondaryText', align: 'right' }
            )
        );
    if (!limit)
        (model.tasks || []).slice(0, 5).forEach((task, index) =>
            nodes.push(
                node(
                    'Box',
                    'calendarStatusDot' + index,
                    rect(6 + index * 9, height - 12, 6, 6),
                    {
                        background: task.statusColor || 'action',
                        radius: 3
                    }
                )
            )
        );
    return { nodes };
}

export function footer(model, width, language) {
    const tr = (text) => translate(text, language),
        nodes = [];
    nodes.push(
        node('Icon', 'calendarFooterIcon', rect(0, 7.5, 13, 13), {
            icon: 'calendar_month',
            color: 'secondaryText'
        })
    );
    nodes.push(
        label(
            'calendarFooterText',
            rect(19, 6, width - 54 - (model.hasMore ? 32 : 0), 16),
            model.selectedDay
                ? translate('Task Browser filtered by {date}', language, {
                      date: model.selectedDay
                  })
                : tr('Select a day to filter Task Browser'),
            { fontRole: 'caption', color: 'secondaryText' }
        )
    );
    if (model.hasMore)
        nodes.push(
            button(
                'calendarLoadMore',
                rect(width - 60, 0, 28, 28),
                '',
                'add',
                { type: 'load-more' },
                !model.busy,
                {
                    label: tr('Load more tasks'),
                    iconOnly: true,
                    iconAction: true,
                    iconSize: 16
                }
            )
        );
    nodes.push(
        button(
            'calendarTasks',
            rect(width - 28, 0, 28, 28),
            '',
            'tasks',
            { type: 'tasks' },
            true,
            {
                label: tr('Task Manager'),
                iconOnly: true,
                iconAction: true,
                iconSize: 16
            }
        )
    );
    return { nodes };
}

export function agendaRows(days, selected) {
    const rows = [];
    for (const day of days) {
        if (selected ? day.date !== selected : !day.inMonth) continue;
        if (!(day.tasks || []).length && !(day.milestones || []).length)
            continue;
        rows.push({ kind: 'date', key: day.date, text: day.date });
        for (const marker of day.milestones || [])
            rows.push({
                kind: 'milestone',
                key: day.date + marker.code,
                text: marker.label,
                action: { type: 'milestone', value: marker.code }
            });
        for (const task of day.tasks || [])
            rows.push({
                kind: 'task',
                key: day.date + task.taskCode,
                text:
                    task.parentTitle +
                    ' · ' +
                    task.processLabel +
                    ' · ' +
                    task.status,
                action: {
                    type: 'inspect',
                    value: task.taskCode,
                    parentKey: task.parentKey,
                    process: task.process
                }
            });
    }
    return rows;
}

export function agendaRow(row, width) {
    return {
        nodes:
            row.kind === 'date'
                ? [
                      label(
                          'calendarAgendaDate',
                          rect(0, 8, width, 18),
                          row.text,
                          { fontRole: 'body', weight: 600 }
                      )
                  ]
                : [
                      button(
                          'calendarAgendaAction',
                          rect(0, 2, width, 30),
                          row.text,
                          row.kind === 'milestone' ? 'milestone' : '',
                          row.action,
                          true,
                          { align: 'left' }
                      )
                  ]
    };
}

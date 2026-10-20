import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

const day = 86400000;
export function date(value) {
    return value ? Date.parse(String(value).slice(0, 10) + 'T00:00:00Z') : NaN;
}

export function timeline(cell, width, height, language) {
    const model = cell.timeline,
        nodes = [],
        start = date(model.start),
        end = date(model.end) + day;
    const extent = Math.max(1, end - start),
        inner = Math.max(0, width - 20);
    const top = model.showTitle ? 18 : 0,
        bars = model.bars.filter((bar) => !bar.hidden);
    const stride = model.overlap ? 0 : Math.max(12, model.barHeight + 4);
    const contentHeight =
        top + Math.max(model.barHeight + 4, bars.length * stride) + 4;
    if (model.showTitle)
        nodes.push(
            label(
                'tableScheduleRange',
                rect(4, 0, inner, 16),
                (model.year === false ? model.start.slice(5) : model.start) +
                    ' — ' +
                    (model.year === false ? model.end.slice(5) : model.end),
                { fontRole: 'caption', color: 'secondaryText' }
            )
        );
    const tick = Math.max(1, Math.ceil(extent / day / 50));
    for (let index = 0; index < extent / day; index += tick) {
        const current = new Date(start + index * day);
        if (model.week && (current.getUTCDay() + 6) % 7 === model.weekStart)
            nodes.push(
                node(
                    'Box',
                    'scheduleWeek_' + index,
                    rect(
                        4 + ((index * day) / extent) * inner,
                        top,
                        1,
                        contentHeight - top
                    ),
                    { background: 'separator' }
                )
            );
    }
    bars.forEach((bar, index) => {
        const from = date(bar.start),
            until = date(bar.end) + day;
        const left = Number.isFinite(from)
            ? Math.max(0, ((from - start) / extent) * inner)
            : 0;
        const right = Number.isFinite(until)
            ? Math.min(inner, ((until - start) / extent) * inner)
            : left;
        if (right < 0 || left > inner || until <= start || from >= end) return;
        const y = top + index * stride;
        nodes.push(
            node(
                'Box',
                'tableScheduleBar_' + index,
                rect(4 + left, y, Math.max(2, right - left), model.barHeight),
                { background: bar.color, radius: 3 }
            )
        );
        if (model.dateMode === 'visible')
            nodes.push(
                label(
                    'tableScheduleDates_' + index,
                    rect(6, y, inner, model.barHeight),
                    (bar.start || '—') + ' — ' + (bar.end || '—'),
                    { fontRole: 'caption' }
                )
            );
        nodes.push(
            node(
                'Action',
                'tableScheduleOpen_' + index,
                rect(4, y, inner, Math.max(12, model.barHeight)),
                {
                    label:
                        bar.label +
                        ': ' +
                        (bar.start || '—') +
                        ' — ' +
                        (bar.end || '—'),
                    role: 'button',
                    action: {
                        type: 'service',
                        name: 'table-schedule',
                        taskKey: bar.searchKey,
                        scheduleIndex: bar.index
                    },
                    enabled: true
                }
            )
        );
    });
    return {
        nodes: [
            node('Scroll', 'tableScheduleScroll', rect(0, 0, width, height), {
                contentHeight,
                scrollbarId: 'tableScheduleBar',
                children: nodes
            })
        ]
    };
}

export function hours(cell, width, height, language) {
    const days = cell.timeDays || [],
        nodes = [],
        t = (value) => translate(value, language);
    const extent = Math.max(35, cell.dayWidth || 35),
        available = Math.max(1, width - 20);
    const columnWidth = Math.max(extent, available / Math.max(1, days.length));
    days.forEach((value, index) => {
        const left = index * columnWidth;
        nodes.push(
            label(
                'tableDay_' + index,
                rect(left, 0, columnWidth - 4, 16),
                t(value.label),
                { fontRole: 'caption', color: 'secondaryText', align: 'center' }
            )
        );
        nodes.push(
            label(
                'tableHours_' + index,
                rect(left, 18, columnWidth - 4, 18),
                value.start || value.end
                    ? (value.start || '—') + ' — ' + (value.end || '—')
                    : value.value || '—',
                { align: 'center' }
            )
        );
        if (value.overtime)
            nodes.push(
                label(
                    'tableOvertime_' + index,
                    rect(left, 36, columnWidth - 4, 16),
                    value.overtime,
                    {
                        fontRole: 'caption',
                        color: 'secondaryText',
                        align: 'center'
                    }
                )
            );
        if (cell.actions?.length)
            nodes.push(
                node(
                    'Action',
                    'tableHoursEdit_' + index,
                    rect(left, 0, columnWidth - 4, 52),
                    {
                        label: t('Work Hours') + ': ' + value.day,
                        role: 'button',
                        action: {
                            type: 'service',
                            name: 'work-hours',
                            day: value.day,
                            taskKey: cell.taskKey
                        }
                    }
                )
            );
    });
    return {
        nodes: [
            node('Scroll', 'tableHoursScroll', rect(0, 0, width, height), {
                contentWidth: columnWidth * days.length,
                contentHeight: days.some((value) => value.overtime) ? 52 : 36,
                scrollbarId: 'tableHoursBar',
                children: nodes
            })
        ]
    };
}

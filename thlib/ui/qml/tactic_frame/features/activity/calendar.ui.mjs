import { node, rect, label, button } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';
import {
    localDate,
    parse,
    monthLabel
} from '../../controls/forms/calendar.mjs';

export function dateKey(date) {
    return (
        String(date.getFullYear()).padStart(4, '0') +
        '-' +
        String(date.getMonth() + 1).padStart(2, '0') +
        '-' +
        String(date.getDate()).padStart(2, '0')
    );
}
export function initialMonth(selected, counts, now = new Date()) {
    const newest = Object.keys(counts || {})
        .filter((key) => Number(counts[key]) > 0 && parse(key, false))
        .sort()
        .pop();
    return parse(selected || newest, false) || now;
}
export function moveMonth(date, delta) {
    return localDate(date.getFullYear(), date.getMonth() + delta, 1, 12);
}
export function cells(month, counts, language, now = new Date()) {
    const first = localDate(month.getFullYear(), month.getMonth(), 1, 12),
        start = language === 'ru' ? 1 : 0,
        offset = (first.getDay() - start + 7) % 7,
        today = dateKey(now);
    return Array.from({ length: 42 }, (_, index) => {
        const value = localDate(
                first.getFullYear(),
                first.getMonth(),
                index - offset + 1,
                12
            ),
            key = dateKey(value);
        return {
            key,
            day: value.getDate(),
            inMonth: value.getMonth() === month.getMonth(),
            today: key === today,
            count: Math.max(0, Number((counts || {})[key]) || 0)
        };
    });
}
export function describe(model, width, language) {
    const tr = (text, values) => translate(text, language, values),
        nodes = [],
        gap = 3,
        cellWidth = Math.max(0, (width - gap * 6) / 7),
        gridTop = 64,
        cellHeight = 38,
        days =
            language === 'ru'
                ? ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
                : ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    nodes.push(
        button(
            'activityCalendarPreviousMonth',
            rect(0, 0, 26, 26),
            '',
            'chevron_left',
            { type: 'previous' },
            true,
            { label: tr('Previous month'), iconOnly: true, iconAction: true }
        )
    );
    nodes.push(
        label(
            'activityCalendarMonthLabel',
            rect(30, 4, Math.max(0, width - 60), 19),
            monthLabel(model.month, language),
            { fontRole: 'bodyLarge', weight: 600, align: 'center' }
        )
    );
    nodes.push(
        button(
            'activityCalendarNextMonth',
            rect(Math.max(0, width - 26), 0, 26, 26),
            '',
            'chevron_right',
            { type: 'next' },
            true,
            { label: tr('Next month'), iconOnly: true, iconAction: true }
        )
    );
    for (let i = 0; i < 7; i++)
        nodes.push(
            label(
                'activityCalendarWeekday_' + i,
                rect(i * (cellWidth + gap), 34, cellWidth, 22),
                days[i],
                { fontRole: 'caption', align: 'center', color: 'secondaryText' }
            )
        );
    const list = cells(model.month, model.counts, language, model.now);
    for (let i = 0; i < list.length; i++) {
        const cell = list[i],
            selected = cell.key === model.selected,
            ink = selected
                ? 'selectedText'
                : !cell.inMonth
                  ? 'disabledText'
                  : 'primaryText',
            x = (i % 7) * (cellWidth + gap),
            y = gridTop + Math.floor(i / 7) * (cellHeight + gap);
        const children = [
            label(
                'activityCalendarNumber_' + cell.key,
                rect(0, 10, cellWidth, 18),
                String(cell.day),
                {
                    fontRole: 'body',
                    align: 'center',
                    color: ink,
                    weight: cell.today ? 700 : 400
                }
            )
        ];
        if (cell.count) {
            const text = cell.count > 99 ? '99+' : String(cell.count),
                w = Math.max(16, text.length * 5 + 6);
            children.push(
                node(
                    'Box',
                    'activityCalendarCount_' + cell.key,
                    rect(Math.max(0, cellWidth - w), 0, w, 16),
                    {
                        background: selected ? 'selectedText' : 'action',
                        radius: 8,
                        children: [
                            label(
                                'activityCalendarCountText_' + cell.key,
                                rect(0, 1, w, 14),
                                text,
                                {
                                    fontRole: 'menuHeading',
                                    weight: 700,
                                    align: 'center',
                                    color: selected
                                        ? 'selected'
                                        : 'selectedText'
                                }
                            )
                        ]
                    }
                )
            );
        }
        nodes.push(
            node(
                'Action',
                'activityCalendarDay_' + cell.key,
                rect(x, y, cellWidth, cellHeight),
                {
                    text:
                        cell.key +
                        ' · ' +
                        tr('{count} events', { count: cell.count }),
                    selected,
                    enabled: cell.count > 0,
                    normalColor: cell.today
                        ? 'surfaceContainerHigh'
                        : 'transparent',
                    selectedColor: 'selected',
                    radius: 9,
                    action: { type: 'day', value: cell.key },
                    children
                }
            )
        );
    }
    const footer = gridTop + 6 * (cellHeight + gap) + 8;
    nodes.push(
        node(
            'Box',
            'activityCalendarSeparator',
            rect(0, footer - 5, width, 1),
            { background: 'separator' }
        )
    );
    nodes.push(
        button(
            'activityCalendarAll',
            rect(0, footer, 128, 38),
            tr('All history'),
            '',
            { type: 'day', value: '' },
            true
        )
    );
    nodes.push(
        button(
            'activityCalendarClose',
            rect(Math.max(0, width - 92), footer, 92, 38),
            tr('Close'),
            '',
            { type: 'close' },
            true
        )
    );
    if (model.busy)
        nodes.push(
            node(
                'View',
                'activityCalendarLoading',
                rect(Math.max(128, (width - 18) / 2), footer + 10, 18, 18),
                { view: 'busy' }
            )
        );
    return { height: footer + 38, nodes };
}

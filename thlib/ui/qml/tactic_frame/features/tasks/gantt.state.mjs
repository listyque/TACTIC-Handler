// Production presentation state. Drafts, revisions, history and writes stay with
// the task owner; both native hosts translate their input into these operations.
import { layout as frameLayout } from '../../core/foundation.mjs';
export const clamp = (value, minimum, maximum) =>
    Math.max(minimum, Math.min(maximum, value));

export const metrics = {
    heading: 54,
    headingGap: 3,
    overview: 30,
    footer: frameLayout.dockWorkspaceFooterHeight,
    section: 28,
    group: 27,
    row: 50,
    bar: 27,
    barInset: 4,
    minBar: 7,
    gripWidth: 12,
    gripHeight: 22,
    gripOutside: 8,
    progressWidth: 18,
    progressHeight: 22,
    overscan: 100,
    autoScrollEdge: 28,
    autoScrollStep: 10,
    autoScrollInterval: 20,
    dragThreshold: 3
};

export function layout(width, height, days, zoom = 1, gutter = 0) {
    const labels = Math.min(310, Math.max(220, width * 0.3));
    const viewport = Math.max(1, width - labels - gutter);
    const count = Math.max(1, days || 1);
    const baseDay = clamp(viewport / count, 10, 28);
    const day = clamp(baseDay * zoom, 2, 80);
    const bodyTop = metrics.heading + metrics.headingGap;
    const bodyHeight = Math.max(
        0,
        height - bodyTop - metrics.overview - metrics.footer
    );
    return {
        labels,
        viewport,
        baseDay,
        day,
        timeline: Math.max(viewport, count * day),
        heading: { x: 0, y: 0, width, height: metrics.heading },
        body: { x: 0, y: bodyTop, width, height: bodyHeight },
        overview: {
            x: 0,
            y: bodyTop + bodyHeight,
            width,
            height: metrics.overview
        },
        footer: {
            x: 0,
            y: Math.max(0, height - metrics.footer),
            width,
            height: metrics.footer
        }
    };
}

export function rows(records, collapsed = []) {
    const result = [];
    let top = 0;
    function add(kind, key, record, height) {
        result.push({ kind, key, record, height, top });
        top += height;
    }
    for (const record of records) {
        if (record.ganttSectionFirst)
            add(
                'section',
                'section:' + record.ganttSection,
                record,
                metrics.section
            );
        if (record.groupFirst && record.groupKey)
            add(
                'group',
                record.ganttSection + ':' + record.groupKey,
                record,
                metrics.group
            );
        if (collapsed.indexOf(record.groupKey) < 0)
            add('task', record.taskCode, record, metrics.row);
    }
    return { items: result, height: top };
}

export function dateForDay(rangeStart, offset) {
    const value = new Date(
        (rangeStart || '2000-01-01').slice(0, 10) + 'T12:00:00Z'
    );
    value.setUTCDate(value.getUTCDate() + Number(offset || 0));
    return value.toISOString().slice(0, 10);
}

export function boundary(rangeStart, offset) {
    const date = new Date(dateForDay(rangeStart, offset) + 'T12:00:00Z');
    return date.getUTCDate() === 1 ? 2 : date.getUTCDay() === 1 ? 1 : 0;
}

export function tickMode(day) {
    return day >= 22
        ? 'days'
        : day >= 7
          ? 'weeks'
          : day >= 2.8
            ? 'months'
            : 'quarters';
}

export function ticks(range, day, x, width) {
    return ((range.tickSets || {})[tickMode(day)] || []).filter(
        (tick) =>
            tick.offsetDay * day >= x - metrics.overscan &&
            tick.offsetDay * day <= x + width + metrics.overscan
    );
}

export function bar(start, duration, day, x = 0) {
    return {
        x: start * day - x,
        y: (metrics.row - metrics.bar) / 2,
        width: Math.max(metrics.minBar, duration * day - metrics.barInset),
        height: metrics.bar
    };
}

export function progressAt(pointer, width) {
    return clamp(Math.round((pointer / Math.max(1, width)) * 100), 0, 100);
}

export function progressKey(progress, key) {
    if (key === 'Home') return 0;
    if (key === 'End') return 100;
    if (key === 'ArrowLeft') return clamp(progress - 1, 0, 100);
    if (key === 'ArrowRight') return clamp(progress + 1, 0, 100);
    return null;
}

export function progressLeft(width, progress) {
    return (
        clamp((width * progress) / 100, 18, width - 18) -
        metrics.progressWidth / 2
    );
}

export function begin(record, mode, contentX, day, fromIssue = false) {
    const start =
        mode === 'create' ? Math.round(contentX / day) : record.ganttStartDay;
    const duration =
        mode === 'create' ? 1 : Math.max(1, record.ganttDurationDays);
    return {
        key: record.taskCode,
        mode,
        fromIssue,
        distance: 0,
        press: contentX,
        baseStart: start,
        baseDuration: duration,
        start,
        duration,
        baseProgress: record.progress,
        progress: record.progress
    };
}

export function pointer(drag, contentX, day) {
    const next = Object.assign({}, drag);
    next.distance = Math.max(
        drag.distance || 0,
        Math.abs(contentX - drag.press)
    );
    if (drag.mode === 'progress') {
        next.progress = progressAt(
            contentX - drag.baseStart * day,
            bar(drag.baseStart, drag.baseDuration, day).width
        );
        return next;
    }
    const delta = Math.round((contentX - drag.press) / day);
    if (drag.mode === 'move')
        next.start = clamp(drag.baseStart + delta, -3650, 36600);
    else if (drag.mode === 'start' || drag.mode === 'resize-start') {
        next.start = clamp(
            drag.baseStart + delta,
            -3650,
            drag.baseStart + drag.baseDuration - 1
        );
        next.duration = Math.min(
            3650,
            drag.baseDuration + drag.baseStart - next.start
        );
    } else if (drag.mode === 'create') {
        next.start = drag.baseStart + Math.min(0, delta);
        next.duration = Math.min(3650, Math.abs(delta) + 1);
    } else if (drag.mode === 'end' || drag.mode === 'resize-end')
        next.duration = clamp(drag.baseDuration + delta, 1, 3650);
    else throw Error('Unknown schedule gesture: ' + drag.mode);
    return next;
}

export function moved(drag) {
    return drag.distance >= metrics.dragThreshold;
}

export function changed(drag) {
    return (
        (drag.mode === 'create' && (!drag.fromIssue || moved(drag))) ||
        drag.start !== drag.baseStart ||
        drag.duration !== drag.baseDuration ||
        drag.progress !== drag.baseProgress
    );
}

export function zoomAt(geometry, x, value, anchor) {
    const zoom = clamp(value, 2 / geometry.baseDay, 5);
    const day = clamp(geometry.baseDay * zoom, 2, 80);
    const anchoredDay =
        (x + clamp(anchor, 0, geometry.viewport)) / geometry.day;
    return {
        zoom,
        day,
        x: anchoredDay * day - clamp(anchor, 0, geometry.viewport)
    };
}

export function scaleZoom(mode, baseDay) {
    const widths = {
        days: 28,
        weeks: 12,
        months: 5,
        quarters: 2,
        auto: baseDay
    };
    if (!(mode in widths)) throw Error('Unknown timeline scale: ' + mode);
    return widths[mode] / baseDay;
}

export function overviewPosition(position, viewport, timeline, offset) {
    const thumb = Math.min(
        viewport,
        Math.max(28, (viewport * viewport) / timeline)
    );
    const travel = Math.max(0, viewport - thumb);
    return travel
        ? (clamp(
              position - (offset === undefined ? thumb / 2 : offset),
              0,
              travel
          ) /
              travel) *
              Math.max(0, timeline - viewport)
        : 0;
}

export function autoScroll(x, width, scroll, maximum) {
    const delta =
        x < metrics.autoScrollEdge
            ? -metrics.autoScrollStep
            : x > width - metrics.autoScrollEdge
              ? metrics.autoScrollStep
              : 0;
    return clamp(scroll + delta, 0, maximum);
}

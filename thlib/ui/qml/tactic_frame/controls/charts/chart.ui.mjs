import { node, rect, label } from '../../core/frame.mjs';
import { translate } from '../../core/strings.mjs';

export const palette = ['action', 'cyan', 'violet', 'green', 'yellow', 'red'];

export function number(value, language) {
    if (typeof value !== 'number' || !Number.isFinite(value)) return '—';
    const rounded = Number(value.toFixed(2));
    return String(rounded)
        .replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
        .replace('.', language === 'ru' ? ',' : '.');
}

export function axisLabel(text, language) {
    const date = /^(\d{4})-(\d{2})(?:-(\d{2}))?$/.exec(text);
    if (!date) return text;
    const months =
        language === 'ru'
            ? [
                  'янв',
                  'фев',
                  'мар',
                  'апр',
                  'май',
                  'июн',
                  'июл',
                  'авг',
                  'сен',
                  'окт',
                  'ноя',
                  'дек'
              ]
            : [
                  'Jan',
                  'Feb',
                  'Mar',
                  'Apr',
                  'May',
                  'Jun',
                  'Jul',
                  'Aug',
                  'Sep',
                  'Oct',
                  'Nov',
                  'Dec'
              ];
    const month = months[Number(date[2]) - 1];
    return month
        ? date[3]
            ? Number(date[3]) + ' ' + month
            : month + ' ' + date[1]
        : text;
}

// Geometry and paint are shared; the engines only supply Canvas and theme colors.
export function geometry(data, width, height) {
    const values = data.values.map((value) =>
        typeof value === 'number' && Number.isFinite(value) ? value : null
    );
    const type = data.type || 'bar';
    if (type === 'donut') {
        const side = width >= 380;
        const size = Math.max(
            0,
            Math.min(side ? width * 0.48 : width, side ? height : height * 0.6)
        );
        const cx = side ? size / 2 : width / 2,
            cy = size / 2;
        const radius = Math.max(0, size / 2 - 10),
            inner = radius * 0.74;
        const valid = values.every((value) => value == null || value >= 0);
        const total = valid
            ? values.reduce((sum, value) => sum + (value || 0), 0)
            : 0;
        let angle = -Math.PI / 2;
        const marks = values.map((value, index) => {
            const start = angle;
            angle += total ? ((value || 0) / total) * Math.PI * 2 : 0;
            return { index, value, start, end: angle };
        });
        return {
            type,
            width,
            height,
            values,
            valid,
            total,
            cx,
            cy,
            radius,
            inner,
            marks,
            legend: side
                ? rect(size + 18, 8, width - size - 18, height - 16)
                : rect(0, size + 12, width, height - size - 12)
        };
    }
    const finite = values.filter((value) => value != null);
    const low = Math.min(0, ...finite),
        high = Math.max(0, ...finite);
    const span = high - low || 1;
    const magnitude = Math.pow(10, Math.floor(Math.log(span / 4) / Math.LN10));
    const fraction = span / 4 / magnitude;
    const step =
        (fraction <= 1 ? 1 : fraction <= 2 ? 2 : fraction <= 5 ? 5 : 10) *
        magnitude;
    const minimum = Math.floor(low / step) * step;
    const maximum =
        high === low ? minimum + step * 4 : Math.ceil(high / step) * step;
    const plot = rect(
        width < 220 ? 36 : 48,
        12,
        width - (width < 220 ? 44 : 56),
        height - 46
    );
    const y = (value) =>
        plot.y +
        plot.height -
        ((value - minimum) / (maximum - minimum)) * plot.height;
    const stride = plot.width / Math.max(1, values.length);
    const marks = values.map((value, index) => ({
        index,
        value,
        x: plot.x + stride * (index + 0.5),
        y: value == null ? null : y(value),
        width: Math.max(1, Math.min(42, stride * 0.62)),
        zero: y(0)
    }));
    const ticks = [];
    for (let value = minimum; value <= maximum + step / 2; value += step)
        ticks.push({
            value: Math.abs(value) < step / 100 ? 0 : value,
            y: y(value)
        });
    return { type, width, height, values, marks, plot, ticks, stride };
}

export function describe(data, id, width, height, language) {
    const tr = (text) => translate(text, language);
    const g = geometry(data, width, height);
    const nodes = [
        node('Chart', id + '_plot', rect(0, 0, width, height), {
            chart: g,
            language,
            labels: data.labels,
            text: data.labels
                .map(
                    (text, i) => text + ': ' + number(data.values[i], language)
                )
                .join('; ')
        })
    ];
    if (g.type === 'donut') {
        nodes.push(
            label(
                id + '_total',
                rect(g.cx - g.inner, g.cy - 26, g.inner * 2, 44),
                g.valid ? number(g.total, language) : '—',
                { fontRole: 'headline', weight: 600, align: 'center' }
            )
        );
        nodes.push(
            label(
                id + '_totalLabel',
                rect(g.cx - g.inner, g.cy + 20, g.inner * 2, 22),
                tr('Total'),
                { color: 'secondaryText', fontRole: 'caption', align: 'center' }
            )
        );
        const children = [];
        data.labels.forEach((text, index) => {
            const y = index * 34;
            children.push(
                node('Box', id + '_key_' + index, rect(0, y + 11, 8, 8), {
                    background: palette[index % palette.length],
                    radius: 4
                })
            );
            children.push(
                label(
                    id + '_legend_' + index,
                    rect(18, y, Math.max(0, g.legend.width - 82), 30),
                    text,
                    { maxLines: 1, fontRole: 'secondary' }
                )
            );
            children.push(
                label(
                    id + '_legendValue_' + index,
                    rect(Math.max(18, g.legend.width - 60), y, 60, 30),
                    number(data.values[index], language),
                    { align: 'right', weight: 600, fontRole: 'secondary' }
                )
            );
        });
        nodes.push(
            node('Scroll', id + '_legend', g.legend, {
                contentHeight: data.labels.length * 34,
                children
            })
        );
        if (!g.valid)
            nodes.push(
                label(
                    id + '_invalid',
                    rect(0, 0, width, 28),
                    tr('Donut charts require non-negative values'),
                    { color: 'error', maxLines: 1 }
                )
            );
    } else {
        for (const [index, tick] of g.ticks.entries())
            nodes.push(
                label(
                    id + '_tick_' + index,
                    rect(0, tick.y - 9, g.plot.x - 9, 18),
                    number(tick.value, language),
                    {
                        fontRole: 'caption',
                        color: 'secondaryText',
                        align: 'right'
                    }
                )
            );
        const every = Math.max(
            1,
            Math.ceil(
                data.labels.length / Math.max(1, Math.floor(g.plot.width / 84))
            )
        );
        for (const mark of g.marks)
            if (mark.index % every === 0 || mark.index === g.marks.length - 1) {
                const w = Math.min(82, g.plot.width);
                const x = Math.max(
                    g.plot.x,
                    Math.min(g.plot.x + g.plot.width - w, mark.x - w / 2)
                );
                if (
                    mark.index === g.marks.length - 1 &&
                    mark.index % every &&
                    mark.index % every < every / 2
                )
                    continue;
                nodes.push(
                    label(
                        id + '_axisLabel_' + mark.index,
                        rect(x, height - 28, w, 24),
                        axisLabel(data.labels[mark.index], language),
                        {
                            fontRole: 'caption',
                            color: 'secondaryText',
                            maxLines: 1,
                            align: 'center'
                        }
                    )
                );
            }
    }
    return { nodes };
}

export function hit(g, x, y) {
    if (g.type === 'donut') {
        const radius = Math.hypot(x - g.cx, y - g.cy);
        if (radius < g.inner || radius > g.radius || !g.total) return -1;
        let angle = Math.atan2(y - g.cy, x - g.cx);
        if (angle < -Math.PI / 2) angle += Math.PI * 2;
        return g.marks.findIndex(
            (mark) => mark.end > angle && mark.start <= angle
        );
    }
    if (
        x < g.plot.x ||
        x > g.plot.x + g.plot.width ||
        y < g.plot.y ||
        y > g.plot.y + g.plot.height
    )
        return -1;
    return Math.min(g.marks.length - 1, Math.floor((x - g.plot.x) / g.stride));
}

export function paint(c, g, color, hovered = -1) {
    c.clearRect(0, 0, g.width, g.height);
    c.lineJoin = 'round';
    c.lineCap = 'round';
    if (g.type === 'donut') {
        if (!g.radius) return;
        c.lineCap = 'butt';
        c.lineWidth = g.radius - g.inner;
        c.strokeStyle = color('outlineVariant');
        c.beginPath();
        c.arc(g.cx, g.cy, (g.radius + g.inner) / 2, 0, Math.PI * 2);
        c.stroke();
        for (const mark of g.marks)
            if (mark.value > 0 && g.valid) {
                const gap = Math.min(0.025, (mark.end - mark.start) / 4);
                c.strokeStyle =
                    mark.color || color(palette[mark.index % palette.length]);
                c.lineWidth =
                    g.radius - g.inner + (hovered === mark.index ? 3 : 0);
                c.beginPath();
                c.arc(
                    g.cx,
                    g.cy,
                    (g.radius + g.inner) / 2,
                    mark.start + gap,
                    mark.end - gap
                );
                c.stroke();
            }
        return;
    }
    c.strokeStyle = color('outlineVariant');
    c.lineWidth = 1;
    for (const tick of g.ticks) {
        c.globalAlpha = tick.value === 0 ? 0.8 : 0.4;
        c.beginPath();
        c.moveTo(g.plot.x, tick.y);
        c.lineTo(g.plot.x + g.plot.width, tick.y);
        c.stroke();
    }
    c.globalAlpha = 1;
    if (g.type === 'bar') {
        for (const mark of g.marks)
            if (mark.value != null) {
                c.fillStyle = color(
                    hovered === mark.index ? 'contentAccent' : 'action'
                );
                c.globalAlpha =
                    hovered < 0 || hovered === mark.index ? 0.9 : 0.55;
                c.fillRect(
                    mark.x - mark.width / 2,
                    Math.min(mark.y, mark.zero),
                    mark.width,
                    Math.max(1, Math.abs(mark.y - mark.zero))
                );
            }
    } else if (g.type === 'line') {
        let run = [];
        const draw = () => {
            if (!run.length) return;
            c.beginPath();
            c.moveTo(run[0].x, run[0].zero);
            for (const point of run) c.lineTo(point.x, point.y);
            c.lineTo(run[run.length - 1].x, run[0].zero);
            c.closePath();
            c.fillStyle = color('action');
            c.globalAlpha = 0.12;
            c.fill();
            c.globalAlpha = 1;
            c.beginPath();
            c.moveTo(run[0].x, run[0].y);
            for (const point of run.slice(1)) c.lineTo(point.x, point.y);
            c.strokeStyle = color('action');
            c.lineWidth = 2.5;
            c.stroke();
            for (const point of run)
                if (g.marks.length <= 28 || point.index === hovered) {
                    c.beginPath();
                    c.arc(
                        point.x,
                        point.y,
                        point.index === hovered ? 5 : 3,
                        0,
                        Math.PI * 2
                    );
                    c.fillStyle = color('action');
                    c.fill();
                    c.strokeStyle = color('panel');
                    c.lineWidth = 2;
                    c.stroke();
                }
            run = [];
        };
        for (const mark of g.marks) {
            if (mark.value == null) draw();
            else run.push(mark);
        }
        draw();
    }
    c.globalAlpha = 1;
}

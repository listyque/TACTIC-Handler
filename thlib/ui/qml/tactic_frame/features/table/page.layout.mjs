import { textStyles } from '../../core/foundation.mjs';
import { buttonWidth } from '../../controls/buttons/metrics.mjs';

export function preferredWidth(item, measure) {
    const size = textStyles[item.textRole || 'body'];
    const text = String(item.text || '');
    const padding = item.padding || [0, 0, 0, 0],
        margin = item.margin || [0, 0, 0, 0];
    const inset = padding[1] + padding[3] + margin[1] + margin[3];
    if (item.kind === 'icon') return (item.iconSize || 32) + inset;
    if (item.kind === 'image') return 160 + inset;
    if (item.kind === 'button' || item.kind === 'link')
        return buttonWidth(measure(text, 13, 600), true) + inset;
    if (item.children) {
        const widths = item.children.map(
            (child) => parseFloat(child.width) || preferredWidth(child, measure)
        );
        return (
            (item.kind === 'row'
                ? widths.reduce((a, b) => a + b, 0) +
                  (item.gap ?? 8) * Math.max(0, widths.length - 1)
                : Math.max(40, ...widths)) + inset
        );
    }
    if (item.kind === 'text')
        return Math.max(
            40,
            inset +
                Math.ceil(
                    Math.max(
                        ...text
                            .split('\n')
                            .map((line) =>
                                measure(line, size, item.textWeight || 400)
                            )
                    )
                ) +
                2
        );
    return 240;
}
export function width(item, space, measure) {
    const sizing = item.sizing || {};
    const mode = sizing.width_mode || 'auto';
    const fixed = /^\d+(?:px)?$/.test(item.width || '')
        ? parseFloat(item.width)
        : null;
    const requested =
        mode === 'content'
            ? preferredWidth(item, measure)
            : mode === 'fill'
              ? space
              : fixed === null
                ? space
                : fixed;
    // A narrow host wins over preferred minimums, so the page never forces shell overflow.
    return Math.max(
        0,
        Math.min(
            space,
            Math.max(
                sizing.min_width || 0,
                Math.min(sizing.max_width ?? Infinity, requested)
            )
        )
    );
}
export function rowWidths(items, budget, measure) {
    const flexible = [],
        widths = items.map((item, index) => {
            const sizing = item.sizing || {},
                mode = sizing.width_mode || 'auto';
            const fixed = /%$/.test(item.width || '')
                ? (parseFloat(item.width) / 100) * budget
                : parseFloat(item.width) || 0;
            const content =
                mode === 'content' ? preferredWidth(item, measure) : 0;
            if (mode === 'fill' || (!content && !fixed)) flexible.push(index);
            return Math.max(
                sizing.min_width || 0,
                Math.min(
                    sizing.max_width ?? Infinity,
                    mode === 'fill' ? 0 : content || fixed
                )
            );
        });
    const minimum = widths.reduce((sum, value) => sum + value, 0);
    if (minimum > budget)
        return widths.map((value) => (value * budget) / minimum);
    let remaining = budget - minimum,
        active = flexible;
    while (remaining > 0.01 && active.length) {
        const weight = active.reduce(
            (sum, index) => sum + (items[index].weight || 1),
            0
        );
        let used = 0;
        for (const index of active) {
            const add = Math.max(
                0,
                Math.min(
                    (remaining * (items[index].weight || 1)) / weight,
                    (items[index].sizing?.max_width ?? Infinity) - widths[index]
                )
            );
            widths[index] += add;
            used += add;
        }
        if (used < 0.01) break;
        remaining -= used;
        active = active.filter(
            (index) =>
                widths[index] + 0.01 <
                (items[index].sizing?.max_width ?? Infinity)
        );
    }
    return widths;
}
export function height(item, natural, slot) {
    const sizing = item.sizing || {},
        mode = sizing.height_mode || 'auto';
    const requested =
        mode === 'content'
            ? natural
            : mode === 'fill' && slot !== null
              ? slot
              : Number.isFinite(item.height)
                ? item.height
                : mode === 'auto' && slot !== null
                  ? slot
                  : natural;
    return Math.min(
        slot ?? Infinity,
        Math.max(
            sizing.min_height || 0,
            Math.min(sizing.max_height ?? Infinity, requested)
        )
    );
}
export function textHeight(text, width, size, weight, measure) {
    const available = Math.max(1, width),
        space = measure(' ', size, weight);
    let lines = 0;
    for (const paragraph of String(text).split('\n')) {
        lines++;
        let used = 0;
        for (const word of paragraph.split(/\s+/).filter(Boolean)) {
            const advance = measure(word, size, weight);
            if (used && used + space + advance > available) {
                lines++;
                used = 0;
            }
            const wraps = Math.max(1, Math.ceil(advance / available));
            lines += wraps - 1;
            used =
                (used ? used + space : 0) + advance - (wraps - 1) * available;
        }
    }
    return Math.max(24, lines * Math.ceil(size * 1.33));
}
export function grid(items, width, settings, gap) {
    const count = Math.max(
        1,
        Math.min(
            settings.columns || 3,
            Math.floor((width + gap) / ((settings.min_cell_width || 200) + gap))
        )
    );
    const unit = Math.max(0, (width - gap * (count - 1)) / count),
        rowHeight = settings.row_height || 120;
    const occupied = [],
        placements = [];
    for (const [index, item] of items.entries()) {
        const columns = Math.min(count, item.columnSpan || 1),
            rows = item.rowSpan || 1;
        let row = 0,
            column = 0;
        for (;;) {
            const fits =
                column + columns <= count &&
                Array.from({ length: rows }, (_, dy) => dy).every((dy) =>
                    Array.from({ length: columns }, (_, dx) => dx).every(
                        (dx) => !occupied[row + dy]?.[column + dx]
                    )
                );
            if (fits) break;
            if (++column >= count) {
                column = 0;
                row++;
            }
        }
        for (let dy = 0; dy < rows; dy++) {
            if (!occupied[row + dy]) occupied[row + dy] = [];
            for (let dx = 0; dx < columns; dx++)
                occupied[row + dy][column + dx] = true;
        }
        placements.push({
            index,
            x: column * (unit + gap),
            y: row * (rowHeight + gap),
            width: unit * columns + gap * (columns - 1),
            height: rowHeight * rows + gap * (rows - 1)
        });
    }
    return {
        columns: count,
        placements,
        height: occupied.length ? occupied.length * (rowHeight + gap) - gap : 0
    };
}

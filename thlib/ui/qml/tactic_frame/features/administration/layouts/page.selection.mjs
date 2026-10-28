import { transform } from './canvas.mjs';

export const alignments = [
    'left',
    'centerX',
    'right',
    'top',
    'centerY',
    'bottom'
];
export function roots(keys) {
    const unique = Array.from(new Set(keys));
    return unique.filter(
        (key) => !unique.some((parent) => key.startsWith(parent + '.'))
    );
}
export function toggle(keys, key) {
    if (keys.includes(key)) return keys.filter((value) => value !== key);
    return roots(
        keys.filter((value) => !key.startsWith(value + '.')).concat(key)
    );
}
export function selected(boxes, keys) {
    const names = roots(keys);
    return boxes.filter((box) => names.includes(box.key));
}
export function bounds(boxes) {
    if (!boxes.length) return null;
    const x = Math.min(...boxes.map((box) => box.x));
    const y = Math.min(...boxes.map((box) => box.y));
    return {
        x,
        y,
        width: Math.max(...boxes.map((box) => box.x + box.width)) - x,
        height: Math.max(...boxes.map((box) => box.y + box.height)) - y
    };
}
export function marquee(boxes, start, end) {
    const area = bounds([
        { x: start.x, y: start.y, width: 0, height: 0 },
        { x: end.x, y: end.y, width: 0, height: 0 }
    ]);
    return roots(
        boxes
            .filter((box) => {
                const hit = box.hit || box;
                return (
                    hit.x >= area.x &&
                    hit.y >= area.y &&
                    hit.x + hit.width <= area.x + area.width &&
                    hit.y + hit.height <= area.y + area.height
                );
            })
            .map((box) => box.key)
    );
}
export function alignment(boxes, mode) {
    if (!alignments.includes(mode) || boxes.length < 2) return [];
    const group = bounds(boxes);
    return boxes.map((box) => {
        const after = Object.assign({}, box);
        if (mode === 'left') after.x = group.x;
        if (mode === 'centerX')
            after.x = group.x + (group.width - box.width) / 2;
        if (mode === 'right') after.x = group.x + group.width - box.width;
        if (mode === 'top') after.y = group.y;
        if (mode === 'centerY')
            after.y = group.y + (group.height - box.height) / 2;
        if (mode === 'bottom') after.y = group.y + group.height - box.height;
        after.x = Math.round(after.x);
        after.y = Math.round(after.y);
        return {
            key: box.key,
            handle: 'move',
            position: true,
            before: box,
            after
        };
    });
}
export function drag(boxes, handle, dx, dy, candidates, scale, snap) {
    const group = bounds(boxes);
    const moving = transform(group, handle, dx, dy);
    const guides = [];
    const others = candidates.filter(
        (box) =>
            !boxes.some(
                (chosen) =>
                    box.key === chosen.key ||
                    box.key.startsWith(chosen.key + '.') ||
                    chosen.key.startsWith(box.key + '.')
            )
    );
    if (snap)
        for (const axis of ['x', 'y']) {
            const size = axis === 'x' ? 'width' : 'height';
            const relevant =
                handle === 'move' || handle.includes(axis === 'x' ? 'e' : 's');
            if (!relevant) continue;
            const anchors = handle === 'move' ? [0, 0.5, 1] : [1];
            let best = null;
            for (const other of others)
                for (const target of [0, 0.5, 1])
                    for (const anchor of anchors) {
                        const value = other[axis] + other[size] * target;
                        const delta =
                            value - moving[axis] - moving[size] * anchor;
                        if (
                            Math.abs(delta) <= 6 / scale &&
                            (!best || Math.abs(delta) < Math.abs(best.delta))
                        )
                            best = { axis, value, delta, other };
                    }
            if (best) {
                if (handle === 'move') moving[axis] += best.delta;
                else
                    moving[size] = Math.max(
                        axis === 'x' ? 40 : 24,
                        moving[size] + best.delta
                    );
                const cross = axis === 'x' ? 'y' : 'x',
                    extent = axis === 'x' ? 'height' : 'width';
                guides.push({
                    axis,
                    value: best.value,
                    start: Math.min(moving[cross], best.other[cross]),
                    end: Math.max(
                        moving[cross] + moving[extent],
                        best.other[cross] + best.other[extent]
                    )
                });
            }
        }
    const changes = boxes.map((box) => ({
        key: box.key,
        handle,
        position: true,
        before: box,
        after:
            handle === 'move'
                ? transform(box, handle, moving.x - group.x, moving.y - group.y)
                : Object.assign({}, box, {
                      width: moving.width,
                      height: moving.height
                  })
    }));
    return { changes, guides };
}

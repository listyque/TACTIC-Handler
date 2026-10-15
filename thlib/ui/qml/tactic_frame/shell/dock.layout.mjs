// Structural projection from Handler's docks_tree.py, EPL-1.0.
// Owners retain their tree, visibility and persistence; projection never writes them.
import { dockMinimumWidth, dockMinimumHeight } from './window.sizing.mjs';

export function minimum(kind) {
    return [dockMinimumWidth(kind), dockMinimumHeight(kind)];
}

export function panelIds(node) {
    if (!node) return [];
    return node.type === 'stack'
        ? node.panels
        : panelIds(node.first).concat(panelIds(node.second));
}

export function minimumSize(node, available, sizes) {
    if (!node) return [0, 0];
    if (node.type === 'stack') {
        const result = [0, 0];
        for (const id of node.panels) {
            if (available.indexOf(id) < 0) continue;
            const size = sizes[id] || [0, 0];
            result[0] = Math.max(result[0], size[0]);
            result[1] = Math.max(result[1], size[1]);
        }
        return result;
    }
    const first = minimumSize(node.first, available, sizes);
    const second = minimumSize(node.second, available, sizes);
    return node.orientation === 'horizontal'
        ? [first[0] + second[0], Math.max(first[1], second[1])]
        : [Math.max(first[0], second[0]), first[1] + second[1]];
}

function present(node, available) {
    return panelIds(node).some((id) => available.indexOf(id) >= 0);
}

function ratioLimits(node, rect, available, sizes) {
    const axis = node.orientation === 'horizontal' ? 0 : 1;
    const extent = rect[axis + 2];
    if (extent <= 0) return [node.ratio, node.ratio];
    const first = minimumSize(node.first, available, sizes)[axis];
    const second = minimumSize(node.second, available, sizes)[axis];
    const lower = first / extent,
        upper = 1 - second / extent;
    if (lower <= upper) return [lower, upper];
    const proportional = first + second > 0 ? first / (first + second) : 0.5;
    return [proportional, proportional];
}

function childRects(node, rect, ratio) {
    const x = rect[0],
        y = rect[1],
        w = rect[2],
        h = rect[3];
    return node.orientation === 'horizontal'
        ? [
              [x, y, w * ratio, h],
              [x + w * ratio, y, w * (1 - ratio), h]
          ]
        : [
              [x, y, w, h * ratio],
              [x, y + h * ratio, w, h * (1 - ratio)]
          ];
}

export function normalizedSizes(kinds, width, height) {
    const sizes = {};
    for (const id of Object.keys(kinds)) {
        const size = minimum(kinds[id]);
        sizes[id] = [
            Math.min(1, size[0] / Math.max(1, width)),
            Math.min(1, size[1] / Math.max(1, height))
        ];
    }
    return sizes;
}

export function project(node, available, sizes) {
    const stacks = [],
        dividers = [],
        rectangles = {};
    function visit(current, rect, path) {
        if (!current || !present(current, available)) return current;
        if (current.type === 'stack') {
            const panels = current.panels.filter(
                (id) => available.indexOf(id) >= 0
            );
            stacks.push({
                panels,
                active:
                    panels.indexOf(current.active) >= 0
                        ? current.active
                        : panels[0],
                rect
            });
            for (const id of panels) rectangles[id] = rect;
            return current;
        }
        if (!present(current.first, available))
            return Object.assign({}, current, {
                second: visit(current.second, rect, path + '1')
            });
        if (!present(current.second, available))
            return Object.assign({}, current, {
                first: visit(current.first, rect, path + '0')
            });
        const limits = ratioLimits(current, rect, available, sizes);
        const ratio = Math.max(limits[0], Math.min(limits[1], current.ratio));
        const children = childRects(current, rect, ratio);
        const axis = current.orientation === 'horizontal' ? 0 : 1;
        dividers.push({
            path,
            orientation: current.orientation,
            ratio,
            rect,
            boundary: rect[axis] + rect[axis + 2] * ratio,
            minimum: limits[0],
            maximum: limits[1]
        });
        return Object.assign({}, current, {
            ratio,
            first: visit(current.first, children[0], path + '0'),
            second: visit(current.second, children[1], path + '1')
        });
    }
    const tree = visit(node, [0, 0, 1, 1], '');
    return { tree, stacks, dividers, rectangles };
}

export function resize(node, path, ratio, available, sizes) {
    function replace(current, depth) {
        if (depth === path.length) return Object.assign({}, current, { ratio });
        const key = path[depth] === '0' ? 'first' : 'second';
        const result = Object.assign({}, current);
        result[key] = replace(current[key], depth + 1);
        return result;
    }
    // Start at the actual projected geometry, then clamp every affected descendant.
    return project(
        replace(project(node, available, sizes).tree, 0),
        available,
        sizes
    ).tree;
}

export function resizeEdge(node, id, edge, boundary, available, sizes) {
    const projected = project(node, available, sizes);
    const candidates = projected.dividers.filter((divider) => {
        let current = projected.tree;
        for (const step of divider.path)
            current = step === '0' ? current.first : current.second;
        const horizontal = current.orientation === 'horizontal';
        return (
            (horizontal ? ['left', 'right'] : ['top', 'bottom']).indexOf(
                edge
            ) >= 0 &&
            panelIds(
                edge === 'left' || edge === 'top'
                    ? current.second
                    : current.first
            ).indexOf(id) >= 0
        );
    });
    candidates.sort((a, b) => b.path.length - a.path.length);
    if (!candidates.length) return { tree: node, found: false };
    const divider = candidates[0],
        axis = divider.orientation === 'horizontal' ? 0 : 1;
    const ratio = (boundary - divider.rect[axis]) / divider.rect[axis + 2];
    return {
        tree: resize(projected.tree, divider.path, ratio, available, sizes),
        found: true
    };
}

export function reorder(node, id, order) {
    if (!node) return node;
    if (node.type === 'stack') {
        if (node.panels.indexOf(id) < 0) return node;
        if (
            !order.length ||
            order.some(
                (value, index) =>
                    node.panels.indexOf(value) < 0 ||
                    order.indexOf(value) !== index
            )
        )
            return node;
        let index = 0;
        return Object.assign({}, node, {
            panels: node.panels.map((value) =>
                order.indexOf(value) >= 0 ? order[index++] : value
            )
        });
    }
    return Object.assign({}, node, {
        first: reorder(node.first, id, order),
        second: reorder(node.second, id, order)
    });
}

export function normalizeActive(node, available) {
    if (!node) return node;
    if (node.type === 'stack') {
        const visible = node.panels.filter((id) => available.indexOf(id) >= 0);
        return visible.length && visible.indexOf(node.active) < 0
            ? Object.assign({}, node, { active: visible[0] })
            : node;
    }
    return Object.assign({}, node, {
        first: normalizeActive(node.first, available),
        second: normalizeActive(node.second, available)
    });
}

export function floatingResize(rect, edge, dx, dy, kind, width, height) {
    const x = rect[0],
        y = rect[1],
        w = rect[2],
        h = rect[3];
    const size = minimum(kind),
        minW = Math.min(width, size[0]),
        minH = Math.min(height, size[1]);
    const left =
        edge.indexOf('left') >= 0
            ? Math.max(0, Math.min(x + w - minW, x + dx))
            : x;
    const top =
        edge.indexOf('top') >= 0
            ? Math.max(0, Math.min(y + h - minH, y + dy))
            : y;
    const right =
        edge.indexOf('right') >= 0
            ? x + Math.max(minW, Math.min(width - x, w + dx))
            : x + w;
    const bottom =
        edge.indexOf('bottom') >= 0
            ? y + Math.max(minH, Math.min(height - y, h + dy))
            : y + h;
    return [left, top, right - left, bottom - top];
}

export function tabTarget(centers, source, translation) {
    const center = centers[source] + translation;
    let target = source;
    if (translation > 0) {
        while (target + 1 < centers.length && center > centers[target + 1])
            target++;
    } else {
        while (target > 0 && center < centers[target - 1]) target--;
    }
    return target;
}

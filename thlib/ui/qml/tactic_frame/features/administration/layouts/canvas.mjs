import { node, rect } from '../../../core/frame.mjs';
import { translate } from '../../../core/strings.mjs';

export const handles = ['e', 's', 'se'];
function intersect(a, b) {
    if (!a) return b;
    const x = Math.max(a.x, b.x),
        y = Math.max(a.y, b.y);
    return rect(
        x,
        y,
        Math.max(0, Math.min(a.x + a.width, b.x + b.width) - x),
        Math.max(0, Math.min(a.y + a.height, b.y + b.height) - y)
    );
}
export function boxes(nodes, field, x = 0, y = 0, depth = 0, clip = null) {
    let result = [];
    for (const item of nodes || []) {
        const left = x + item.x,
            top = y + item.y;
        const bounds = rect(left, top, item.width, item.height),
            hit = intersect(clip, bounds);
        if (item[field] !== undefined && hit.width > 0 && hit.height > 0)
            result.push({
                id: item.id,
                key:
                    field === 'editorPath'
                        ? Array.from(item[field]).join('.')
                        : String(item[field]),
                x: left,
                y: top,
                width: item.width,
                height: item.height,
                depth,
                hit,
                grid: item.canvasGrid
            });
        result = result.concat(
            boxes(
                item.children,
                field,
                left,
                top,
                depth + 1,
                item.clip ? hit : clip
            )
        );
    }
    return result;
}
export function transform(box, handle, dx, dy) {
    const next = Object.assign({}, box);
    dx = Math.round(dx);
    dy = Math.round(dy);
    if (handle === 'move') {
        next.x += dx;
        next.y += dy;
    } else {
        if (handle.includes('e'))
            next.width = Math.max(40, Math.min(2400, next.width + dx));
        if (handle.includes('s'))
            next.height = Math.max(24, Math.min(1600, next.height + dy));
    }
    return next;
}
export function decorate(
    scene,
    field,
    view = 'canvasOverlay',
    accept = () => true
) {
    const result = Object.assign({}, scene, {
        nodes: (scene.nodes || []).slice()
    });
    const index = result.nodes.findIndex((n) => n.id === 'customLayoutScroll');
    const scroll =
        index < 0
            ? null
            : Object.assign({}, result.nodes[index], {
                  children: result.nodes[index].children.slice()
              });
    if (scroll) result.nodes[index] = scroll;
    const children = scroll ? scroll.children : result.nodes;
    const targets = boxes(children, field).filter(accept);
    if (!targets.length) return scene;
    children.push(
        node(
            'View',
            'canvasOverlay',
            rect(
                0,
                0,
                Math.max(...targets.map((b) => b.x + b.width)),
                Math.max(...targets.map((b) => b.y + b.height))
            ),
            { view, layer: 1000 }
        )
    );
    return Object.assign(result, { canvasBoxes: targets });
}

export function spacingField(
    id,
    title,
    value,
    text,
    action,
    language,
    enabled,
    width
) {
    const sides = ['Top', 'Right', 'Bottom', 'Left'];
    const size = Math.max(1, (width - 18) / 4);
    const children = [];
    for (let side = 0; side < 4; side++) {
        const key = id + ':' + side;
        children.push(
            node(
                'Label',
                id + 'Label' + side,
                rect(side * (size + 6), 0, size, 18),
                {
                    text: translate(sides[side], language),
                    fontRole: 'caption',
                    color: 'secondaryText'
                }
            ),
            node('Field', id + side, rect(side * (size + 6), 22, size, 34), {
                label: title + ': ' + translate(sides[side], language),
                text: Object.prototype.hasOwnProperty.call(text, key)
                    ? text[key]
                    : String(value[side]),
                enabled,
                inputMode: 'numeric',
                action: { type: 'buffer', key },
                commitAction: Object.assign({}, action, { side, key })
            })
        );
    }
    return {
        kind: 'Box',
        id,
        title,
        fullWidth: true,
        height: 80,
        props: {
            children: [
                node('Label', id + 'Heading', rect(0, 0, width, 18), {
                    text: title,
                    weight: 600
                }),
                node('Box', id + 'Fields', rect(0, 24, width, 56), { children })
            ]
        }
    };
}

export function itemScene(scene, layout, prefix = 'itemComposition') {
    if (layout.flow === 'contents' || layout.collection === 'table')
        return scene;
    return decorate(scene, 'layoutElement', 'canvasOverlay', (box) => {
        const item = layout.elements.find((row) => row.name === box.key);
        const parent =
            item && layout.elements.find((row) => row.name === item.parent);
        return (
            !!item &&
            box.id === prefix + '_' + item.name &&
            (parent ? parent.flow : layout.flow) === 'grid'
        );
    });
}

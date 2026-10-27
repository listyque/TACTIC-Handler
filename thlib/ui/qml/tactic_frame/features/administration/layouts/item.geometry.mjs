import * as Layout from './layout.document.mjs';

// Keep the saved grid; pointer movement changes its cells, not the runtime CSS.
export function apply(model, change) {
    const item = model.layout.elements.find((row) => row.name === change.key);
    if (!item) throw Error('The selected element no longer exists');
    const parent = model.layout.elements.find(
        (row) => row.name === item.parent
    );
    if ((parent ? parent.flow : model.layout.flow) !== 'grid')
        throw Error('Choose Grid in the parent container to position elements');
    const columns = parent ? parent.columns : model.layout.columns;
    const gap = (parent ? parent.gap : model.layout.gap) ?? 6;
    const margin = item.margin || [0, 0, 0, 0],
        pitch = (change.before.width + margin[1] + margin[3] + gap) / item.span;
    const grid = change.before.grid;
    const nearest = (values, target) =>
        values.reduce(
            (best, value, index) =>
                Math.abs(value - target) < Math.abs(values[best] - target)
                    ? index
                    : best,
            0
        );
    const values = {};
    if (change.handle === 'move') {
        values.column = Math.max(
            1,
            Math.min(
                columns - item.span + 1,
                item.column +
                    Math.round((change.after.x - change.before.x) / pitch)
            )
        );
        values.row = Math.max(
            1,
            Math.min(
                100,
                item.row +
                    Math.round(
                        (change.after.y - change.before.y) /
                            ((change.before.height + gap) / item.rows)
                    )
            )
        );
        if (grid) {
            const start =
                grid.columns[item.column - 1] +
                change.after.x -
                change.before.x;
            values.column = Math.min(
                columns - item.span + 1,
                nearest(grid.columns, start) + 1
            );
            const y =
                grid.rows[item.row - 1] + change.after.y - change.before.y;
            if (y <= grid.rows[grid.rows.length - 1])
                values.row = nearest(grid.rows, y) + 1;
        }
    } else {
        if (change.handle.includes('e'))
            values.span = Math.max(
                1,
                Math.min(
                    columns - item.column + 1,
                    Math.round((change.after.width + gap) / pitch)
                )
            );
        if (grid && change.handle.includes('e')) {
            const ends = grid.ends.slice(item.column - 1);
            values.span =
                nearest(
                    ends,
                    grid.columns[item.column - 1] +
                        change.after.width +
                        margin[1] +
                        margin[3]
                ) + 1;
        }
        if (change.handle.includes('s')) {
            values.align = 'start';
            values.height = Math.max(
                1,
                Math.min(
                    1200,
                    Math.round(
                        item.height + change.after.height - change.before.height
                    )
                )
            );
        }
    }
    if (change.keyboard && change.handle === 'move') {
        values.column = Math.max(
            1,
            Math.min(
                columns - item.span + 1,
                item.column + change.after.x - change.before.x
            )
        );
        values.row = Math.max(
            1,
            Math.min(100, item.row + change.after.y - change.before.y)
        );
    }
    let tree = model.tree;
    for (const field of Object.keys(values))
        tree = Layout.edit(tree, model.view, item.name, field, values[field]);
    return Layout.serialize(tree);
}

import { node, rect, label, button } from '../../core/frame.mjs';
import { listAction } from '../../controls/lists/tree.ui.mjs';
import { translate } from '../../core/strings.mjs';

export function initial(tree, serial = 0) {
    return {
        tree,
        serial,
        nodes: {
            root: {
                id: 'root',
                kind: 'branch',
                depth: -1,
                path: [],
                parentKey: '',
                children: [],
                expanded: true
            }
        }
    };
}
function definition(model, path) {
    return path.reduce((value, index) => value.branches[index], model.tree);
}
function branches(model, target) {
    target.children = definition(model, target.path).branches.map(
        (branch, index) => {
            const id = target.id + '/branch:' + index;
            model.nodes[id] = {
                id,
                kind: 'branch',
                title: branch.title || branch.search_type,
                depth: target.depth + 1,
                path: [...target.path, index],
                parentKey: target.key,
                children: [],
                expanded: false
            };
            return id;
        }
    );
    target.loaded = true;
}
export function change(source, action) {
    let model = JSON.parse(JSON.stringify(source));
    if (action.type === 'refresh') {
        model = initial(model.tree, model.serial);
        action = { type: 'load', id: 'root' };
    }
    const target = model.nodes[action.id];
    if (!target) return { model };
    if (action.type === 'toggle') {
        target.expanded = !target.expanded;
        if (!target.expanded) return { model };
        if (target.kind === 'record' && !target.loaded) {
            branches(model, target);
        }
        if (target.kind !== 'branch' || target.loaded) return { model };
    }
    if (!['toggle', 'load', 'more'].includes(action.type) || target.busy)
        return { model };
    target.busy = true;
    target.error = '';
    target.pending = ++model.serial;
    return {
        model,
        request: {
            id: target.id,
            serial: target.pending,
            tree: model.tree,
            branch_path: target.path,
            parent_key: target.parentKey,
            offset: action.type === 'more' ? target.nextOffset : 0,
            limit: 50
        }
    };
}
export function accept(source, request, result, error = '') {
    const model = JSON.parse(JSON.stringify(source)),
        target = model.nodes[request.id];
    if (!target || target.pending !== request.serial) return model;
    target.busy = false;
    target.error = error;
    if (error) return model;
    if (Object.keys(model.nodes).length + result.items.length > 4000) {
        target.error = 'Too many results. Narrow the search.';
        return model;
    }
    const ids = result.items.map((item) => {
        const id = target.id + '/' + encodeURIComponent(item.key);
        if (!model.nodes[id])
            model.nodes[id] = Object.assign({}, item, {
                id,
                kind: 'record',
                path: target.path,
                depth: target.depth + 1,
                expanded: false,
                expandable: !!definition(model, target.path).branches.length,
                children: []
            });
        if (
            request.id === 'root' &&
            model.nodes[id].expandable &&
            !model.nodes[id].loaded
        ) {
            model.nodes[id].expanded = true;
            branches(model, model.nodes[id]);
        }
        return id;
    });
    target.children = request.offset
        ? [...new Set([...target.children, ...ids])]
        : ids;
    target.loaded = true;
    target.hasNext = result.has_next;
    target.nextOffset = result.offset + result.items.length;
    return model;
}
export function rows(model) {
    const result = [];
    function visit(id) {
        const item = model.nodes[id];
        if (id !== 'root') result.push(item);
        if (!item.expanded) return;
        for (const child of item.children) visit(child);
        if (item.error)
            result.push({
                id: id + '/error',
                kind: 'error',
                title: item.error,
                target: id,
                depth: item.depth + 1
            });
        else if (item.busy)
            result.push({
                id: id + '/busy',
                kind: 'busy',
                title: 'Loading data…',
                depth: item.depth + 1
            });
        else if (item.loaded && !item.children.length)
            result.push({
                id: id + '/empty',
                kind: 'empty',
                title: 'No results',
                depth: item.depth + 1
            });
        if (item.hasNext)
            result.push({
                id: id + '/more',
                kind: 'more',
                title: 'Load more',
                target: id,
                depth: item.depth + 1
            });
    }
    visit('root');
    return result;
}
export function describe(model, width, height, language) {
    const tr = (text) => translate(text, language);
    return {
        nodes: [
            button(
                'dashboardTreeRefresh',
                rect(Math.max(0, width - 40), 0, 32, 32),
                tr('Refresh'),
                'refresh',
                { type: 'refresh' },
                !model.nodes.root.busy,
                { iconOnly: true }
            ),
            node(
                'List',
                'dashboardTreeRows',
                rect(0, 40, width, Math.max(0, height - 40)),
                {
                    source: 'rows',
                    keyField: 'id',
                    rowHeight: 32,
                    rowGap: 0,
                    scrollbarId: 'dashboardTreeScrollBar'
                }
            )
        ]
    };
}
export function row(model, item, width, language) {
    const tr = (text) => translate(text, language),
        nodes = [],
        left = Math.min(96, Math.max(0, item.depth) * 16);
    if (item.kind === 'branch' || item.expandable)
        nodes.push(
            button(
                'dashboardTreeExpand',
                rect(left, 4, 24, 24),
                tr(item.expanded ? 'Collapse' : 'Expand'),
                item.expanded ? 'chevron-down' : 'chevron-right',
                { type: 'toggle', id: item.id },
                true,
                { iconOnly: true }
            )
        );
    const action =
        item.kind === 'record'
            ? { type: 'inspect', key: item.key }
            : item.kind === 'branch'
              ? { type: 'toggle', id: item.id }
              : {
                    type: item.kind === 'more' ? 'more' : 'load',
                    id: item.target
                };
    const enabled = ['record', 'branch', 'more', 'error'].includes(item.kind);
    const detail = item.detail || '';
    nodes.push(
        listAction(
            'dashboardTreeTitle',
            rect(left + 26, 0, Math.max(0, width - left - 42), 32),
            ['empty', 'busy', 'more'].includes(item.kind)
                ? tr(item.title)
                : item.title,
            item.kind === 'record' ? item.icon : '',
            action,
            enabled,
            {
                radius: 2,
                weight: item.kind === 'branch' ? 600 : 400,
                endInset: detail ? Math.min(180, width / 4) : 0,
                color: item.kind === 'error' ? 'error' : undefined
            }
        )
    );
    if (detail)
        nodes.push(
            label(
                'dashboardTreeDetail',
                rect(
                    Math.max(left + 64, width - Math.min(180, width / 4)),
                    0,
                    Math.min(170, width / 4),
                    32
                ),
                detail,
                { color: 'secondaryText' }
            )
        );
    return { nodes };
}

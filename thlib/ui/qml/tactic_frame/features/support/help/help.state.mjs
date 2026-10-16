// Help presentation only. Article loading and file operations belong to adapters.
import { revealListOffset } from '../../../core/frame.mjs';
export function initial() {
    return {
        selected: 'overview',
        query: '',
        topicsVisible: false,
        positions: {}
    };
}

export function filtered(articles, query) {
    const needle = String(query || '')
        .replace(/[`#>*_|\[\]()]/g, ' ')
        .replace(/\s+/g, ' ')
        .trim()
        .toLowerCase();
    return articles.filter((article) =>
        [article.title, article.group, article.searchText]
            .join(' ')
            .toLowerCase()
            .includes(needle)
    );
}

export function offset(model, id) {
    const value = model.positions[id];
    return Number.isFinite(value) ? Math.max(0, value) : 0;
}

export function revealOffset(offset, index, height, count) {
    return revealListOffset(offset, index, height, count, 61);
}

export function topicFromLink(link) {
    const match = /(?:^|\/)([a-z][a-z0-9_.-]*)\.(?:en|ru)\.md(?:#.*)?$/i.exec(
        String(link)
    );
    return match ? match[1] : '';
}

export function transition(model, articles, action) {
    const next = Object.assign({}, model);
    const commands = [];
    const known = (id) => articles.some((article) => article.id === id);
    if (action.type === 'query') {
        next.query = String(action.value || '');
    } else if (action.type === 'topics') {
        next.topicsVisible =
            action.value === undefined ? !model.topicsVisible : !!action.value;
    } else if (action.type === 'scroll') {
        if (action.id === model.selected && Number.isFinite(action.value))
            next.positions = Object.assign({}, model.positions, {
                [action.id]: Math.max(0, action.value)
            });
    } else if (['open', 'select', 'loaded'].indexOf(action.type) >= 0) {
        const requested = action.id || model.selected;
        next.selected = known(requested)
            ? requested
            : known(model.selected)
              ? model.selected
              : known('overview')
                ? 'overview'
                : articles[0]?.id || '';
        if (action.type !== 'loaded') next.topicsVisible = false;
        if (action.type === 'select' || (action.id && action.type === 'open')) {
            if (
                !filtered(articles, next.query).some(
                    (row) => row.id === next.selected
                )
            )
                next.query = '';
            commands.push({ type: 'reveal', id: next.selected });
        }
        if (action.type === 'loaded') {
            next.positions = {};
            for (const id of Object.keys(model.positions))
                if (known(id)) next.positions[id] = model.positions[id];
        }
        if (next.selected)
            commands.push({ type: 'selectArticle', id: next.selected });
        if (
            action.keyboard ||
            (action.type === 'select' && model.topicsVisible)
        )
            commands.push({ type: 'focusArticle' });
    } else if (action.type === 'topicKey') {
        const rows = filtered(articles, model.query);
        const index = rows.findIndex((row) => row.id === action.id);
        let target = index;
        if (action.key === 'Home') target = 0;
        else if (action.key === 'End') target = rows.length - 1;
        else if (action.key === 'ArrowDown') target = (index + 1) % rows.length;
        else if (action.key === 'ArrowUp')
            target = (index - 1 + rows.length) % rows.length;
        if (rows[target])
            commands.push({ type: 'focusTopic', id: rows[target].id });
    } else if (
        ['reload', 'openFile', 'download', 'close'].indexOf(action.type) >= 0
    ) {
        commands.push({ type: action.type });
    } else {
        throw Error('Unknown Help action: ' + action.type);
    }
    return { model: next, commands };
}

// Input decisions only; hosts own focus, panel visibility and persistence.
export function neighbor(tabs, id) {
    const index = tabs.findIndex((tab) => tab.id === id);
    return tabs[index + 1]?.id || tabs[index - 1]?.id || '';
}

export function action(tabs, id, key, reorder) {
    const index = tabs.findIndex((tab) => tab.id === id);
    if (index < 0 || !tabs.length) return null;
    let target = index;
    if (key === 'ArrowLeft') target = (index + tabs.length - 1) % tabs.length;
    else if (key === 'ArrowRight') target = (index + 1) % tabs.length;
    else if (key === 'Home') target = 0;
    else if (key === 'End') target = tabs.length - 1;
    else if (key === 'Delete')
        return tabs[index].closable
            ? { type: 'close', id, next: neighbor(tabs, id) }
            : null;
    else if (key !== 'Enter' && key !== ' ') return null;
    return reorder && ['ArrowLeft', 'ArrowRight'].indexOf(key) >= 0
        ? { type: 'reorder', id, source: index, target }
        : { type: 'select', id: tabs[target].id };
}

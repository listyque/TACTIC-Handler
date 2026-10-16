// Presentation drafts stay local; existing controllers own authorization and writes.
export function begin(document) {
    return Object.assign({}, document, {
        password: '',
        groups: (document.groups || []).slice(),
        accessLevels: Object.assign({}, document.accessLevels || {})
    });
}

export function edit(draft, action) {
    if (!draft) return draft;
    if (action.type === 'field') {
        if (!Object.prototype.hasOwnProperty.call(draft, action.key))
            throw Error('Unknown profile field: ' + action.key);
        const next = Object.assign({}, draft);
        next[action.key] = action.value;
        return next;
    }
    if (action.type === 'group') {
        const groups = (draft.groups || []).filter(
            (code) => code !== action.code
        );
        if (action.value) groups.push(action.code);
        return Object.assign({}, draft, { groups });
    }
    if (action.type === 'access') {
        const accessLevels = Object.assign({}, draft.accessLevels);
        accessLevels[action.code] = action.value;
        return Object.assign({}, draft, { accessLevels });
    }
    return draft;
}

export function dirty(draft, original, avatar) {
    return (
        !!draft &&
        (!!avatar || JSON.stringify(draft) !== JSON.stringify(original))
    );
}

export function closeDecision(model, force) {
    if (model.saving) return 'busy';
    return !force && (model.dirty || model.uncertain) ? 'confirm' : 'close';
}

export function page(model, value) {
    if (model.saving) return model.mode;
    return value === 'groups' && model.canManage && !model.restricted
        ? 'groups'
        : 'profile';
}

export function submitted(draft) {
    return Object.assign({}, draft, { password: '' });
}

// The hosts own requests and popup lifetime; this module owns the entire draft.
function responseArray(value) {
    // QVariantList is an array-like sequence in Qt, rather than a JavaScript Array.
    return value &&
        typeof value === 'object' &&
        Number.isInteger(value.length) &&
        value.length >= 0
        ? Array.from(value)
        : null;
}

export function create(seed) {
    return {
        seed: Object.assign({}, seed),
        ready: false,
        rows: [],
        parentTypes: [],
        parentType: '',
        query: '',
        draftQuery: '',
        currentParentKey: '',
        currentParent: null,
        selectedParent: null,
        expectedRevision: '',
        busy: '',
        error: '',
        uncertain: false,
        confirmAction: ''
    };
}

export function dropParentKey(value) {
    if (
        !value ||
        !Array.isArray(value.searchKeys) ||
        value.searchKeys.length !== 1 ||
        typeof value.searchKeys[0] !== 'string' ||
        !value.searchKeys[0] ||
        typeof value.searchType !== 'string' ||
        value.searchKeys[0].split('?')[0] !== value.searchType.split('?')[0]
    )
        throw new Error('Drop one parent object');
    return value.searchKeys[0];
}

export function dirty(state) {
    return (
        !!state.selectedParent &&
        state.selectedParent.searchKey !== state.currentParentKey
    );
}

export function canSave(state) {
    return (
        state.ready &&
        dirty(state) &&
        !state.busy &&
        !state.uncertain &&
        !state.selectedParent.retired &&
        !!state.selectedParent.revision &&
        !!state.expectedRevision
    );
}

export function rows(state) {
    return state.rows.map((row) =>
        Object.assign({}, row, {
            selected: row.searchKey === state.selectedParent?.searchKey,
            enabled: !state.busy && !state.uncertain
        })
    );
}

export function begin(state, operation, more = false) {
    if (
        state.busy ||
        (operation === 'save' && !canSave(state)) ||
        (operation === 'check' && !state.uncertain) ||
        (operation === 'candidates' &&
            (!state.parentType || (more && !state.hasNext)))
    )
        return { state };
    const request = {
        search_key: state.seed.targetSearchKey,
        view: state.seed.tableView,
        column: state.seed.columnName,
        projectCode: state.seed.projectCode,
        action: operation,
        expected_revision: state.expectedRevision
    };
    if (state.seed.sourceId != null) request.source_id = state.seed.sourceId;
    if (operation === 'prepare') {
        request.source_revision = state.seed.sourceRevision || '';
        request.parent_key = state.seed.dropParentKey || '';
    } else if (operation === 'candidates') {
        request.parent_type = state.parentType;
        request.query = state.query;
        request.offset = more ? state.rows.length : 0;
    } else {
        request.parent_key = state.selectedParent?.searchKey || '';
        request.parent_revision = state.selectedParent?.revision || '';
    }
    return {
        state: Object.assign({}, state, {
            busy: operation,
            error: '',
            append: more
        }),
        request
    };
}

function refresh(state) {
    return begin(
        create(
            Object.assign({}, state.seed, {
                sourceRevision: '',
                dropParentKey: ''
            })
        ),
        'prepare'
    );
}

export function dispatch(state, action) {
    const value = action.value;
    if (state.confirmAction) {
        if (action.type === 'accept')
            return state.confirmAction === 'refresh'
                ? refresh(state)
                : { state, close: true };
        if (['reject', 'cancel'].includes(action.type))
            return { state: Object.assign({}, state, { confirmAction: '' }) };
        return { state };
    }
    if (action.type === 'cancel') {
        if (state.busy === 'save') return { state };
        return dirty(state) || state.uncertain
            ? { state: Object.assign({}, state, { confirmAction: 'close' }) }
            : { state, close: true };
    }
    if (action.type === 'query-text')
        return {
            state: Object.assign({}, state, { draftQuery: String(value ?? '') })
        };
    if (state.busy) return { state };
    if (action.type === 'check') return begin(state, 'check');
    if (state.uncertain) return { state };
    if (action.type === 'refresh')
        return dirty(state)
            ? { state: Object.assign({}, state, { confirmAction: 'refresh' }) }
            : refresh(state);
    if (action.type === 'type') {
        if (!state.parentTypes.some((row) => row.value === value))
            return { state };
        return begin(
            Object.assign({}, state, {
                parentType: value,
                query: '',
                draftQuery: '',
                rows: [],
                hasNext: false,
                selectedParent: null
            }),
            'candidates'
        );
    }
    if (action.type === 'query')
        return begin(
            Object.assign({}, state, { query: state.draftQuery }),
            'candidates'
        );
    if (action.type === 'more') return begin(state, 'candidates', true);
    if (action.type === 'select') {
        const selectedParent = state.rows.find(
            (row) => row.searchKey === action.searchKey
        );
        return selectedParent
            ? { state: Object.assign({}, state, { selectedParent }) }
            : { state };
    }
    if (action.type === 'save') return begin(state, 'save');
    return { state };
}

export function accept(
    state,
    operation,
    result,
    error = '',
    uncertain = false
) {
    if (state.busy !== operation) return { state };
    let next = Object.assign({}, state, { busy: '', error });
    if (error)
        return {
            state: Object.assign(next, {
                uncertain: state.uncertain || uncertain
            })
        };
    if (operation === 'prepare') {
        const parentTypes = responseArray(result?.parentTypes);
        if (
            !result?.expectedRevision ||
            typeof result.sourceId !== 'string' ||
            !result.sourceId ||
            !parentTypes ||
            parentTypes.some((row) => typeof row?.value !== 'string')
        )
            return {
                state: Object.assign(next, { error: 'Invalid parent response' })
            };
        next = Object.assign(next, result, {
            ready: true,
            parentTypes,
            seed: Object.assign({}, state.seed, {
                sourceId: result.sourceId ?? state.seed.sourceId,
                sourceTitle: result.sourceTitle || state.seed.sourceTitle || ''
            }),
            selectedParent:
                result.selectedParent || result.currentParent || null,
            parentType: result.parentType || parentTypes[0]?.value || ''
        });
        return next.parentType ? begin(next, 'candidates') : { state: next };
    }
    if (operation === 'candidates') {
        const page =
            result?.rows?.length <= 50 ? responseArray(result.rows) : null;
        if (
            !page ||
            page.some(
                (row) =>
                    typeof row?.searchKey !== 'string' ||
                    typeof row.revision !== 'string'
            )
        )
            return {
                state: Object.assign(next, { error: 'Invalid parent response' })
            };
        return {
            state: Object.assign(next, {
                rows: state.append ? state.rows.concat(page) : page,
                hasNext: !!result.hasNext
            })
        };
    }
    if (result?.state === 'saved')
        return { state: next, saved: true, close: true };
    if (
        operation === 'check' &&
        ['unchanged', 'conflict'].includes(result?.state)
    )
        return {
            state: Object.assign(next, {
                uncertain: false,
                error:
                    result.state === 'conflict'
                        ? 'Parent changed. Reload before saving.'
                        : ''
            })
        };
    return {
        state: Object.assign(next, {
            uncertain: true,
            error: 'Unable to verify the parent change'
        })
    };
}

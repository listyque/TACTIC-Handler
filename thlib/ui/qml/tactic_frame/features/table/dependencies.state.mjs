// A page belongs to one concrete snapshot (or one file range inside it).
export function create(searchKey, projectCode) {
    return {
        pages: {
            root: {
                searchKey,
                projectCode,
                rows: [],
                open: true,
                loaded: false
            }
        }
    };
}

export function begin(state, path, more = false) {
    const page = state.pages[path];
    if (!page || page.busy || (more && !page.hasNext)) return { state };
    const request = {
        path,
        search_key: page.searchKey,
        projectCode: page.projectCode,
        expected_revision: page.revision || '',
        offset: more ? page.rows.length : 0,
        limit: 50
    };
    if (page.fileIndex !== undefined) request.file_index = page.fileIndex;
    return {
        state: Object.assign({}, state, {
            pages: Object.assign({}, state.pages, {
                [path]: Object.assign({}, page, {
                    busy: true,
                    error: '',
                    append: more
                })
            })
        }),
        request
    };
}

export function accept(state, path, result, error = '') {
    const page = state.pages[path];
    if (!page?.busy) return state;
    const next = Object.assign({}, page, { busy: false, error });
    if (!error) {
        Object.assign(next, result, {
            searchKey: result.snapshotKey || page.searchKey,
            loaded: true,
            rows: page.append ? [...page.rows, ...result.rows] : result.rows
        });
    }
    return Object.assign({}, state, {
        pages: Object.assign({}, state.pages, { [path]: next })
    });
}

export function toggle(state, record) {
    if (!record.expandable) return { state };
    const path = record.path,
        old = state.pages[path];
    const page = old
        ? Object.assign({}, old, { open: !old.open })
        : Object.assign(
              {
                  searchKey: record.snapshotKey,
                  projectCode: record.projectCode,
                  revision: record.revision,
                  rows: [],
                  open: true,
                  loaded: false
              },
              record.fileRange ? { fileIndex: record.fileIndex } : {}
          );
    const next = Object.assign({}, state, {
        pages: Object.assign({}, state.pages, { [path]: page })
    });
    return page.open && !page.loaded && !page.busy
        ? begin(next, path)
        : { state: next };
}

export function rows(state) {
    const output = [],
        ancestors = new Set(),
        stack = [{ path: 'root', depth: 0, index: 0 }];
    while (stack.length) {
        const frame = stack[stack.length - 1],
            path = frame.path,
            depth = frame.depth,
            page = state.pages[path];
        if (!page?.open) {
            stack.pop();
            continue;
        }
        if (!frame.entered) {
            frame.entered = true;
            // File pages share their parent's snapshot, rather than entering it again.
            if (page.fileIndex === undefined) {
                frame.identity = page.searchKey;
                ancestors.add(frame.identity);
            }
        }
        if (frame.index < page.rows.length) {
            const record = page.rows[frame.index++];
            const childPath = path + '/' + record.key,
                child = state.pages[childPath],
                cycle =
                    record.kind === 'reference' &&
                    ancestors.has(record.snapshotKey),
                expandable =
                    !cycle &&
                    (record.kind === 'reference' || !!record.fileRange);
            output.push(
                Object.assign({}, record, {
                    path: childPath,
                    depth,
                    cycle,
                    expandable,
                    open: !!child?.open,
                    busy: !!child?.busy,
                    revision: record.revision || page.revision
                })
            );
            if (expandable && child?.open)
                stack.push({ path: childPath, depth: depth + 1, index: 0 });
            continue;
        }
        if (page.error || page.message || (page.loaded && !page.rows.length))
            output.push({
                path: path + '/status',
                pagePath: path,
                depth,
                kind: 'status',
                error: page.error,
                more: !!page.append,
                title: page.error || page.message || 'No dependencies',
                busy: page.busy
            });
        if (page.hasNext)
            output.push({
                path: path + '/more',
                pagePath: path,
                depth,
                kind: 'more',
                busy: page.busy
            });
        if (frame.identity !== undefined) ancestors.delete(frame.identity);
        stack.pop();
    }
    return output;
}
